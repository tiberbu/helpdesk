# Adversarial QA Report: Task #62 — Fix: Story 1.9 QA Findings

**Reviewer:** Adversarial Review (Opus model)
**Date:** 2026-03-23
**Artifact:** Git diff 6ff6d32e0..98c070a8c (task #62 fix commit)
**Verdict:** 13 findings. 2 P1, 5 P2, 6 P3.

---

## Findings

### F-01 [P1] — `set_status_category()` runs AFTER `set_default_status()` but BEFORE `validate()` — race on new tickets

**Description:** In `hd_ticket.py`, `before_validate` calls `set_status_category()` which sets `self.status_category` from the DB lookup of `self.status`. However, `set_status_category()` uses `self.status_category = self.status_category or frappe.get_value(...)` — it only sets the category if it's currently falsy. This means if a ticket already has a stale `status_category` value cached (e.g. from a previous save), and the status is changed, `status_category` won't be re-derived. The client-side guard in `TicketDetailsTab.vue` uses `ticketStatusStore.getStatus(value).category` which IS correct, but the server-side `validate_checklist_before_resolution()` relies on `self.status_category` which may be stale if the status was just changed. The `or` short-circuit in `set_status_category` is a latent bug: it should always re-derive from the current `self.status` when `self.has_value_changed("status")`.

**Impact:** A ticket could bypass the mandatory checklist guard on the server side if `status_category` was previously set to something non-falsy (which it always is after the first save). When changing from "Replied" (category "Paused") to "Resolved" (category "Resolved"), `status_category` would remain "Paused" because the `or` short-circuit preserves the existing value.

**Evidence:** `hd_ticket.py` line 1042-1047: `self.status_category = self.status_category or frappe.get_value(...)`. The `or` means it never updates once set.

**Severity:** P1 — server-side resolution guard bypass.

---

### F-02 [P1] — No migration patch for `default_priority` field type change (Select -> Link)

**Description:** The fix changed `default_priority` on `HD Incident Model` from `Select` (with hardcoded "\nLow\nMedium\nHigh\nUrgent") to `Link` (to "HD Ticket Priority"). This is a schema-altering change. The existing patch `add_incident_model_doctypes.py` just does `frappe.reload_doctype(...)` which creates the doctype fresh if it doesn't exist, but does NOT alter an existing column from VARCHAR (Select) to VARCHAR (Link). More critically, existing data in the `default_priority` column contains literal strings like "Low", "Medium" etc. — if the Link target `HD Ticket Priority` uses different naming (e.g. the `name` field might not match these exact strings), all existing fixture data and any user-created models become broken references.

**Impact:** On an existing deployment that already ran the original patch, `bench migrate` will either fail or leave the column in an inconsistent state. The fixture data uses "Low", "Medium", "High", "Urgent" but there's no validation these are actual `HD Ticket Priority` document names.

**Evidence:** `hd_incident_model.json` diff shows the field type change. No new patch in `patches.txt`. Fixture still references literal priority names without verifying they exist as Link targets.

---

### F-03 [P2] — Client-side resolution guard depends on async store data that may not be loaded

**Description:** `ticketStatusStore.getStatus(value)` looks up status data from `statuses.data`, which is populated by `createListResource` with `auto: true`. If the store hasn't finished loading yet (race condition on initial page load), `getStatus()` returns `undefined`, and `undefined?.category` is `undefined`, which is `!== "Resolved"`, so the guard silently passes. The resolution would go through without any checklist validation on the client side.

**Impact:** On slow connections or first page load, the client guard is ineffective. The server guard (F-01 notwithstanding) is the real authority, but the UX will be confusing — user sees no warning, then gets a server error.

**Evidence:** `ticketStatus.ts` line 33-38: `getStatus` does a `.find()` on `statuses.data` which is `undefined` until the list resource resolves.

---

### F-04 [P2] — No test coverage for the `is_agent()` permission guard

**Description:** The fix added `is_agent()` checks to both `apply_incident_model()` and `complete_checklist_item()`, but there are zero tests verifying that a non-agent (customer) user is rejected. The test suite only runs as an agent user (`im_agent@example.com`). A regression that removes the `is_agent()` check would pass all tests.

**Impact:** The permission fix (AC #3) is unverified. A future refactor could silently remove the guard.

**Evidence:** `test_incident_model.py` — grep for `test_.*customer`, `test_.*non_agent`, `test_.*permission`, `test_.*itil.*disabled` returns zero matches.

---

### F-05 [P2] — No test coverage for ITIL mode disabled path

**Description:** The fix added ITIL mode checks to both API functions, but the test setUp always enables ITIL mode and tearDown disables it. There is no test that calls `apply_incident_model()` or `complete_checklist_item()` with ITIL mode OFF to verify the `ValidationError` is raised.

**Impact:** The ITIL gating fix (AC #5) is unverified by automated tests.

**Evidence:** `test_incident_model.py` — setUp line 43 enables, tearDown line 57 disables. No test toggles the flag.

---

### F-06 [P2] — `depends_on` using `frappe.db.get_single_value()` in DocType JSON is a DB call per field render

**Description:** The `depends_on` expression `eval:frappe.db.get_single_value('HD Settings', 'itil_mode_enabled')` on `incident_model` and `ticket_checklist` fields in `hd_ticket.json` is evaluated on every form render. In the standard Frappe form view, this triggers a synchronous DB call per field per render. This is acceptable for the standard desk form, but it's unusual and could cause N+1 performance issues if the form is rendered in a list context.

**Impact:** Performance degradation on ticket list views if these fields are evaluated. Not a functional bug, but a code smell. The established pattern uses the config store on the frontend side, but the backend DocType JSON has no choice.

**Evidence:** `hd_ticket.json` lines 554 and 561.

---

### F-07 [P2] — Frontend TicketChecklist and IncidentModel panel have no ITIL mode gating

**Description:** The `TicketChecklist` component and the incident model auto-populate logic in `TicketDetailsTab.vue` have zero frontend ITIL mode gating. While the backend API will reject calls when ITIL mode is off, the UI still shows the checklist panel (`v-if="ticket?.doc?.name && ticket.doc.ticket_checklist?.length"`) and the incident_model field (controlled only by `depends_on` in doctype JSON). If a ticket was created while ITIL was ON and later ITIL is turned OFF, the checklist panel still renders with stale data, and the toggle checkboxes will produce confusing API errors.

**Impact:** Poor UX — users see ITIL-only UI elements when ITIL is off, get API errors on interaction.

**Evidence:** `TicketDetailsTab.vue` line 68-73 — no `itilModeEnabled` check. `TicketChecklist.vue` — no ITIL gating at all.

---

### F-08 [P3] — `_make_model` helper creates test data that leaks if test fails mid-execution

**Description:** The test helper `_make_model()` calls `doc.insert(ignore_permissions=True)` but the tearDown only does `frappe.db.rollback()`. Since `apply_incident_model` calls `ticket_doc.save()` (which may auto-commit depending on Frappe version/context), and the fix removed `frappe.db.commit()`, the test data might or might not persist depending on whether Frappe auto-commits the whitelist call boundary. The original QA report (issue #4) specifically called out that removing `frappe.db.commit()` was the fix, but the test tearDown still relies on `rollback()` — if Frappe's test runner auto-commits between test methods, data leaks again.

**Impact:** Potential test pollution across test runs, same issue the fix was supposed to address.

**Evidence:** `test_incident_model.py` tearDown uses `frappe.db.rollback()` without explicit cleanup of created docs.

---

### F-09 [P3] — Fixture priority values may not match Link targets

**Description:** The fixture `hd_incident_model.json` uses priority strings "Low", "Medium", "High", "Urgent" for `default_priority`. After the field type change to `Link -> HD Ticket Priority`, these must exactly match `HD Ticket Priority` document names. If the helpdesk installation uses different priority names (e.g. "Critical" instead of "Urgent"), fixture import will fail with a LinkValidationError, or worse, silently set an invalid link value.

**Impact:** Fixture installation fails on non-standard priority configurations.

**Evidence:** `hd_incident_model.json` — "Urgent" is used as priority. Standard Frappe helpdesk may not have an "Urgent" priority out of the box.

---

### F-10 [P3] — `getStatus()` lookup by label is fragile when `different_view` is enabled

**Description:** In `ticketStatus.ts`, `getStatus(label)` matches on `s.label_agent === label || s.label_customer === label`. When `different_view` is false, `label_customer` is set equal to `label_agent` in the transform. But when `different_view` is true, they differ. The resolution guard passes `value` (which comes from the dropdown selection — presumably the agent label). If a status has `different_view: true` and the lookup matches on `label_customer` instead of `label_agent`, it could return the wrong status or a false positive. More critically, if two statuses share the same `label_customer`, the `.find()` returns the first match, which may have a different category.

**Impact:** Edge case: resolution guard could match wrong status when `different_view` is enabled.

**Evidence:** `ticketStatus.ts` lines 33-37.

---

### F-11 [P3] — No error handling when `ticketStatusStore.getStatus()` returns undefined

**Description:** In `TicketDetailsTab.vue` line 232: `const newStatusCategory = ticketStatusStore.getStatus(value as string)?.category`. If `getStatus` returns undefined (status not found, store not loaded, or value is not a valid status), `newStatusCategory` is `undefined`. The guard `fieldname === "status" && newStatusCategory === "Resolved"` evaluates to `false`, so the resolution proceeds without checklist validation. There should be defensive handling: if `getStatus` returns undefined for a status change, either block the update or log a warning.

**Impact:** Silent bypass of client-side guard when status is unknown.

**Evidence:** `TicketDetailsTab.vue` line 232-233.

---

### F-12 [P3] — "Closed" status also has category "Resolved" but original code explicitly checked for it

**Description:** The original code checked `value === "Resolved" || value === "Closed"`. The fix replaced this with `newStatusCategory === "Resolved"`. Looking at the actual HD Ticket Status data, "Closed" has `category: "Resolved"`, so the fix is functionally equivalent plus it catches "Duplicate". However, the comment in the code says "Check status_category so 'Duplicate' (also Resolved category) is caught as well" — it doesn't mention "Closed" at all, which suggests the developer didn't verify that "Closed" is also category "Resolved". This is a documentation/reasoning gap, not a bug, but it indicates incomplete analysis.

**Evidence:** Bench query shows Closed has `category: "Resolved"`. Code comment only mentions Duplicate.

---

### F-13 [P3] — PostIncidentReview import remains but the component was deleted in a concurrent fix

**Description:** `TicketDetailsTab.vue` line 104 imports `PostIncidentReview` from `"../ticket/PostIncidentReview.vue"`. The git diff for the concurrent fix commit (a054d39ba) shows `PostIncidentReview.vue` was deleted (193 lines removed). However, the file still exists on disk currently. If these commits are cherry-picked or reordered, the import will break. The concurrent story-60 fix and this story-62 fix both modify `TicketDetailsTab.vue` — they're touching overlapping files and there may be merge conflicts or build failures if not carefully sequenced.

**Impact:** Potential build failure if commits are reordered or applied independently.

**Evidence:** Git log shows `a054d39ba` (story 60 fix) deleted PostIncidentReview.vue, but `98c070a8c` (story 62 fix) still imports it. File currently exists because story 62's commit is older.

---

## Summary

| ID | Severity | Title |
|------|----------|-------|
| F-01 | P1 | `set_status_category()` short-circuit allows server-side resolution guard bypass |
| F-02 | P1 | No migration patch for Select->Link field type change on HD Incident Model |
| F-03 | P2 | Client-side guard depends on async store data that may not be loaded |
| F-04 | P2 | No test for `is_agent()` permission guard |
| F-05 | P2 | No test for ITIL-mode-disabled rejection path |
| F-06 | P2 | `depends_on` with `frappe.db.get_single_value()` is a DB call per render |
| F-07 | P2 | No frontend ITIL gating on TicketChecklist/IncidentModel panels |
| F-08 | P3 | Test data may still leak despite removing `frappe.db.commit()` |
| F-09 | P3 | Fixture priority values may not match HD Ticket Priority document names |
| F-10 | P3 | `getStatus()` label lookup fragile with `different_view` enabled |
| F-11 | P3 | No error handling when `getStatus()` returns undefined |
| F-12 | P3 | Code comment incomplete — doesn't mention "Closed" is also Resolved category |
| F-13 | P3 | PostIncidentReview import may conflict with concurrent deletion |

---

## Recommendation

F-01 and F-02 are real risks. F-01 means the server-side checklist guard is bypassable on any status change (because `status_category` is never re-derived once set). F-02 means the field type change has no migration path for existing deployments. Both need immediate attention before this code ships to production.
