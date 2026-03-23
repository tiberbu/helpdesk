# QA Report: Story 1.6 — Related Ticket Linking (Task #22)

**Date:** 2026-03-23
**Reviewer:** Claude Opus (adversarial review)
**Task ID:** mn37v5auja11q9
**Story File:** `_bmad-output/implementation-artifacts/story-22-story-1-6-related-ticket-linking.md`

---

## Acceptance Criteria Results

### AC-1: Bidirectional "Related to" Linking
> Given an agent views Ticket A, when they click Link Ticket and select Ticket B with type "Related to", then Ticket B appears in A sidebar and A appears in B sidebar (bidirectional)

**Result: PASS**

- API `link_tickets(244, 245, "Related to")` returned `{"success": true}`
- `get_related_tickets(244)` returned ticket 245 with `link_type: "Related to"`
- `get_related_tickets(245)` returned ticket 244 with `link_type: "Related to"` (reverse)
- 13/13 unit tests pass including `test_related_to_creates_bidirectional_links`
- Frontend `RelatedTickets.vue` correctly renders in `TicketDetailsTab.vue`

### AC-2: "Duplicate of" Auto-Close
> Given an agent links Ticket A to Ticket B with type "Duplicate of", when saved, then Ticket A is auto-closed with status "Duplicate" and comment added

**Result: PASS (with caveats — see findings F-02, F-03, F-04)**

- API `link_tickets(246, 245, "Duplicate of")` returned `{"success": true}`
- Ticket 246 status confirmed changed to `"Duplicate"` (category `"Resolved"`)
- Comment added with `is_internal=0` mentioning ticket 245
- Unit tests confirm: `test_duplicate_of_auto_closes_ticket_a`, `test_duplicate_of_adds_system_comment_on_ticket_a`, `test_duplicate_of_does_not_close_ticket_b`

### AC-3: Link Types Available
> Link types available: Related to, Caused by, Duplicate of

**Result: PASS (with caveat — see finding F-01)**

- Frontend `LinkTicketDialog.vue` offers exactly 3 options: Related to, Caused by, Duplicate of
- Backend `INVERSE_LINK_TYPE` correctly maps all inverse types
- Unit test `test_invalid_link_type_raises_validation_error` passes

---

## Adversarial Findings

### F-01 — API Accepts 5 Link Types Instead of 3 (P2)

**Severity:** P2 — Medium
**Category:** Security / Input Validation

**Description:** The `link_tickets` API validates `link_type` against `INVERSE_LINK_TYPE.keys()`, which contains 5 values: `Related to, Caused by, Causes, Duplicate of, Duplicated by`. The frontend only offers 3 types, but a direct API call can submit `"Causes"` or `"Duplicated by"` and they will be accepted.

**Steps to Reproduce:**
```bash
curl -X POST /api/method/helpdesk.api.incident.link_tickets \
  -d '{"ticket_a":"244","ticket_b":"245","link_type":"Causes"}'
# Returns: {"success": true}
```

**Expected:** API should reject `Causes` and `Duplicated by` as direct input — these are system-generated inverse types only.

**Actual:** API accepts them, creating potentially confusing link semantics. The error message misleadingly says "Must be one of: Related to, Caused by, Duplicate of" but the validation doesn't match.

**Impact:** A "Duplicated by" link does NOT trigger auto-close on either ticket, bypassing the duplicate workflow. Semantically, if A is "Duplicated by" B, B should be auto-closed, but nothing happens.

---

### F-02 — Unlink Does Not Revert Duplicate Auto-Close (P2)

**Severity:** P2 — Medium
**Category:** Missing Feature / Data Integrity

**Description:** When a "Duplicate of" link is created, ticket A is auto-closed with status "Duplicate". If the link is subsequently removed via `unlink_tickets`, ticket A remains in "Duplicate" status with no way to programmatically revert it.

**Steps to Reproduce:**
1. Link ticket 246 to 245 as "Duplicate of" — ticket 246 becomes status "Duplicate"
2. Unlink ticket 246 from 245 — returns `{"success": true}`
3. Check ticket 246 status — still "Duplicate"

**Expected:** Either (a) revert to previous status on unlink, or (b) add a comment noting the link was removed so the agent knows to manually update status.

**Actual:** Status remains "Duplicate" silently. Agent may not realize the ticket needs manual status update.

---

### F-03 — Auto-Close Comment Is Public, Not Internal (P3)

**Severity:** P3 — Low
**Category:** Information Disclosure

**Description:** The system comment added when a ticket is marked as duplicate has `is_internal=0`, meaning it's visible to customers via the portal. The comment reads: "This ticket has been closed as a duplicate of [Ticket B]." This reveals internal ticket management decisions and linked ticket IDs to the customer.

**Location:** `helpdesk/api/incident.py`, line 214: `"is_internal": 0`

**Expected:** The auto-close comment should be an internal note (`is_internal=1`) since duplicate detection is an internal workflow decision.

---

### F-04 — Redundant doc_a.save() in Duplicate Flow (P3)

**Severity:** P3 — Low (Performance)
**Category:** Performance / Code Quality

**Description:** In the `link_tickets` function, when `link_type == "Duplicate of"`, `doc_a.save()` is called twice:
1. Line 78: saves the new child table row
2. Line 198 (via `_auto_close_duplicate`): saves the status change

Each `.save()` triggers Frappe hooks, SLA recalculations, and DB writes. The status change could be combined with the first save.

---

### F-05 — Unlink Error Handler Silent to User (P2)

**Severity:** P2 — Medium
**Category:** UX / Error Handling

**Description:** In `RelatedTickets.vue`, the `unlinkResource.onError` handler only logs to `console.error`. There is no user-visible toast, alert, or error message shown. If the unlink fails (e.g., network error, permission issue), the user clicks "Remove", the dialog closes (or hangs), and there is no feedback.

**Location:** `desk/src/components/ticket/RelatedTickets.vue`, lines 201-204

**Expected:** Show a toast notification or inline error message on unlink failure.

**Actual:** Error is silently logged to browser console only.

---

### F-06 — No Guard Against Linking Closed/Resolved Tickets (P3)

**Severity:** P3 — Low
**Category:** Missing Validation

**Description:** There is no validation to prevent linking a ticket that is already in "Duplicate", "Closed", or "Resolved" status to another ticket. An agent can create new "Duplicate of" links on an already-closed ticket, potentially changing its status redundantly or creating confusing link chains.

**Expected:** At minimum, warn if the source ticket is already closed. Consider blocking "Duplicate of" on already-duplicate tickets.

---

### F-07 — No Audit Trail for Link/Unlink Operations (P2)

**Severity:** P2 — Medium
**Category:** Observability / Compliance

**Description:** Neither `link_tickets` nor `unlink_tickets` creates any audit trail beyond the auto-close comment for duplicates. There is:
- No `HD Ticket Comment` when a "Related to" or "Caused by" link is created
- No comment or log when any link is removed
- No `frappe.log_error` or custom log entry
- No Frappe Version/Activity record for the linking action itself

**Impact:** If an agent links/unlinks tickets, there is no visible history of this action. Other agents reviewing the ticket later have no way to know links were added or removed.

---

### F-08 — Race Condition in Duplicate Link Detection (P3)

**Severity:** P3 — Low
**Category:** Concurrency / Data Integrity

**Description:** The `_assert_no_existing_link` check and the subsequent `doc_a.append()/save()` are not atomic. If two agents simultaneously try to link the same two tickets, both could pass the existence check and create duplicate rows. The `frappe.db.commit()` at the end of the function doesn't address this TOCTOU (time-of-check-time-of-use) issue.

**Mitigation:** In practice, this is low-risk since concurrent identical linking is rare, but a database unique constraint on `(parent, parenttype, ticket)` would be the proper fix.

---

### F-09 — No Realtime Update When Links Change (P3)

**Severity:** P3 — Low
**Category:** UX / Realtime

**Description:** The `RelatedTickets.vue` component fetches data on mount and only reloads after the current user performs a link/unlink action. There is no `frappe.realtime` or WebSocket subscription. If Agent A adds a link while Agent B has the same ticket open, Agent B won't see the change until they manually reload.

**Location:** `desk/src/components/ticket/RelatedTickets.vue` — no `socket.on()` or `realtime` subscription.

---

### F-10 — No Test Coverage for get_related_tickets API (P2)

**Severity:** P2 — Medium
**Category:** Test Coverage

**Description:** The unit test file (`test_hd_related_ticket.py`) tests `link_tickets` and `unlink_tickets` but has no test for the `get_related_tickets` API. This function contains enrichment logic (subject/status lookup, `str()` key normalization) that was previously buggy (per completion notes) but is not covered by any test.

**Expected:** At minimum, test that `get_related_tickets` returns correct enriched data after linking, returns empty list for unlinked tickets, and blocks non-agent callers.

---

### F-11 — `frappe.db.commit()` in API Functions (P3)

**Severity:** P3 — Low
**Category:** Code Quality / Frappe Best Practices

**Description:** Both `link_tickets` and `unlink_tickets` call `frappe.db.commit()` explicitly (with `# nosemgrep` suppression). In Frappe's standard request lifecycle, the framework auto-commits on successful request completion. Explicit commits inside whitelisted methods can cause partial data visibility in error scenarios and interfere with Frappe's transaction management.

**Location:** `helpdesk/api/incident.py`, lines 98 and 124.

---

### F-12 — Migration Patch Commits Inside execute() (P3)

**Severity:** P3 — Low
**Category:** Frappe Best Practices

**Description:** The migration patch `add_related_ticket_linking.py` calls `frappe.db.commit()` on line 34. Frappe's migrate framework already handles commits after each patch runs. The explicit commit could cause issues if a subsequent patch in the same migrate run fails and needs to rollback.

**Location:** `helpdesk/patches/v1_phase1/add_related_ticket_linking.py`, line 34.

---

### F-13 — Unlink Comparison Uses String Equality but Child Row ticket Field May Be Int (P3)

**Severity:** P3 — Low (currently mitigated)
**Category:** Fragility / Type Safety

**Description:** In `unlink_tickets`, the filter `r.ticket != ticket_b` compares the child row's `ticket` field (Link type, stored as string in DB) with the API parameter `ticket_b` (typed as `str`). While this works today because Link fields store strings, there is no explicit `str()` coercion like was added to `get_related_tickets` (line 157-160) after a previous bug. If the comparison ever fails due to type mismatch, links would silently fail to be removed.

---

## Regression Check

| Area | Status | Notes |
|------|--------|-------|
| Ticket list page loads | PASS | HTTP 200, no errors |
| Ticket detail page loads | PASS | HTTP 200 for `/helpdesk/tickets/244` |
| Existing ticket fields | PASS | Core fields (status, priority, etc.) unaffected |
| SLA agreement handling | PASS | SLA fields populated correctly on test tickets |
| Permission model | PASS | Unauthenticated users get PermissionError on API |
| Unit tests | PASS | All 13 tests pass (`Ran 13 tests in 2.515s OK`) |

## Console Errors

No console errors detected via API-level testing. JavaScript console verification would require Playwright browser session.

---

## Summary

| Severity | Count | IDs |
|----------|-------|-----|
| P0 (Critical) | 0 | — |
| P1 (High) | 0 | — |
| P2 (Medium) | 4 | F-01, F-02, F-05, F-07, F-10 |
| P3 (Low) | 8 | F-03, F-04, F-06, F-08, F-09, F-11, F-12, F-13 |

**Overall Assessment:** The implementation meets all stated acceptance criteria. The bidirectional linking, auto-close on duplicate, and frontend UI are functional and tested. However, there are 13 findings — primarily around missing edge-case handling, incomplete validation (API accepting inverse types), missing audit trail, and silent error handling. The P2 items (F-01, F-02, F-05, F-07, F-10) should be addressed before the feature is considered production-ready.
