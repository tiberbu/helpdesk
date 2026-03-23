# QA Report: Story 1.9 -- Incident Models / Templates (Task #25)

**Reviewer:** Adversarial QA (Opus)
**Date:** 2026-03-23
**Task ID:** mn39hzqiuq25qf (QA task #61 reviewing dev task #25)
**Story:** Story 1.9 -- Incident Models / Templates
**Verdict:** MIXED -- Core logic works, but multiple design/security issues found

---

## Acceptance Criteria Results

### AC-1: HD Incident Model DocType with configurable fields
**Result: PASS**
- HD Incident Model DocType exists with fields: model_name, description, default_category, default_sub_category, default_priority, default_team, checklist_items (Table of HD Incident Checklist Item).
- Permissions: HD Admin has full CRUD, Agent has read-only. Correct.
- Evidence: `GET /api/resource/HD%20Incident%20Model/System%20Outage` returns all fields populated.

### AC-2: Auto-populate ticket fields on model selection
**Result: PASS (with caveats -- see P1-1, P2-2)**
- `apply_incident_model` API correctly sets priority, category, sub_category, team, and incident_model reference on the ticket.
- Frontend `TicketDetailsTab.vue` triggers `applyIncidentModel()` when `incident_model` field changes.
- Evidence: API call `apply_incident_model(ticket=363, model="System Outage")` returned `{success: true, fields_applied: {priority: "Urgent", incident_model: "System Outage"}, checklist_items_count: 4}`.

### AC-3: Checklist items displayed and mandatory items block resolution
**Result: PASS (with caveats -- see P1-2, P2-4)**
- Server-side `validate_checklist_before_resolution()` correctly blocks resolution when mandatory items are incomplete.
- Evidence: PUT to set status="Resolved" on ticket 363 with incomplete checklist returned `ValidationError`.
- After completing all 4 mandatory items, resolution succeeded (status changed to "Resolved").
- Frontend `TicketChecklist.vue` component renders items with checkboxes, progress bar, mandatory badges, and completion tracking.

### AC-4: At least 5 default models available
**Result: PASS**
- All 5 fixtures present: Password Reset (Low), System Outage (Urgent), Access Request (Medium), Hardware Failure (High), Software Bug (Medium).
- Evidence: `GET /api/resource/HD%20Incident%20Model` returns all 5 named models.

### Unit Tests
**Result: PASS**
- 11/11 tests pass in 1.619s.
- Existing tests (major incident, internal notes) not regressed.

---

## Issues Found

### P1-1: Missing `__` translation import in TicketDetailsTab.vue
**Severity: P1 (High)**
**Description:** `TicketDetailsTab.vue` uses `__()` translation function on lines 198, 202, and 227 but never imports it. The `__` function is exported from `@/translation` and is NOT a global. Other components in the same directory (e.g., `TicketHeader.vue`) explicitly import it.
**Impact:** Any code path that reaches `toast.success(__("Incident model applied"))`, the error toast, or the checklist resolution guard will throw `ReferenceError: __ is not defined`, causing a silent failure with no user feedback. The model may apply successfully but the user sees no confirmation toast. The client-side resolution guard will crash instead of warning the user.
**Steps to Reproduce:**
1. Open a ticket in agent view
2. Select an incident model from the field
3. Observe browser console for `ReferenceError: __ is not defined`
**Expected:** Toast notification "Incident model applied"
**Actual:** JavaScript error, no toast shown

### P1-2: Client-side resolution guard misses "Duplicate" status
**Severity: P1 (High)**
**Description:** The frontend resolution guard in `handleFieldUpdate()` (line 218-219) only checks for `value === "Resolved" || value === "Closed"`. However, the "Duplicate" status also has `category: "Resolved"` and would trigger the server-side validation. The frontend guard is bypassed when setting status to "Duplicate" with incomplete mandatory checklist items.
**Impact:** User can attempt to set status to "Duplicate" without completing mandatory items. The server will reject it, but the user gets no client-side warning -- just an unexpected server error.
**Steps to Reproduce:**
1. Apply a model with mandatory checklist items
2. Don't complete any items
3. Try to set status to "Duplicate"
4. Frontend allows it, server rejects with ValidationError

### P2-1: No ITIL feature flag gating on Incident Models
**Severity: P2 (Medium)**
**Description:** Story 1.1 established `itil_mode_enabled` as a feature flag in HD Settings. Other ITIL features (Impact/Urgency, Major Incident) check this flag. Incident Models are an ITIL-specific feature but have zero checks for `itil_mode_enabled` -- neither in the API, nor in the frontend, nor on the DocType field visibility.
**Impact:** The `incident_model` and `ticket_checklist` fields are always visible on HD Ticket regardless of whether ITIL mode is enabled. Non-ITIL deployments will see irrelevant fields.

### P2-2: Priority field type mismatch -- Select vs Link
**Severity: P2 (Medium)**
**Description:** HD Ticket's `priority` field is `Link` to `HD Ticket Priority` DocType. HD Incident Model's `default_priority` is a `Select` field with hardcoded options `Low|Medium|High|Urgent`. If an admin renames or adds priority levels in HD Ticket Priority, the incident model form won't reflect those changes. The `apply_incident_model` API will set a string value from the Select into a Link field, which works only as long as the names happen to match.
**Impact:** Data integrity risk. If priorities are customized (e.g., "Critical" added, "Urgent" renamed), models will set invalid priority values silently.

### P2-3: No `is_agent()` check in API -- customers can toggle checklist items
**Severity: P2 (Medium)**
**Description:** Both `apply_incident_model()` and `complete_checklist_item()` use `frappe.has_permission("HD Ticket", "write", doc=ticket, throw=True)` but do NOT check `is_agent()`. Customers who raise tickets via the portal have write permission on their own tickets (per `has_permission()` in hd_ticket.py, which grants access to `owner`, `raised_by`, `contact`). This means a customer could theoretically call these APIs on their own tickets.
**Impact:** Customers could mark checklist items as complete without agent verification, undermining the operational checklist's purpose.

### P2-4: `close_tickets_after_n_days()` bypasses checklist validation
**Severity: P2 (Medium)**
**Description:** The auto-close scheduler job (line 1468-1471) sets `doc.flags.ignore_validate = True` before saving with status "Closed". This bypasses `validate_checklist_before_resolution()`, meaning tickets can be auto-closed even when mandatory checklist items are incomplete.
**Impact:** Tickets with incomplete operational checklists (e.g., "Verify service restoration") can silently auto-close, violating ITIL compliance.

### P2-5: Test data leaks into production database
**Severity: P2 (Medium)**
**Description:** Running unit tests leaves 20+ "Test Model XXXX" records in the HD Incident Model table. The `tearDown` calls `frappe.db.rollback()` which should clean up, but apparently the `frappe.db.commit()` calls in the API methods (lines 61, 115 of `incident_model.py`) commit the test data before rollback can undo it.
**Impact:** Production/staging databases get polluted with test artifacts. The 20 leftover "Test Model" records visible via API confirm this.

### P2-6: Fixture child table entries missing `doctype` key
**Severity: P2 (Medium)**
**Description:** In `helpdesk/fixtures/hd_incident_model.json`, the `checklist_items` child table entries don't include a `"doctype": "HD Incident Checklist Item"` key. While Frappe may infer the doctype from the parent's field definition, this is fragile and may fail in certain fixture import scenarios (e.g., `bench import-fixtures` with older Frappe versions).
**Impact:** Fixture import may fail silently or skip checklist items on some Frappe versions.

### P3-1: Sub-category not filtered by parent category in Incident Model form
**Severity: P3 (Low)**
**Description:** The `default_sub_category` field has `depends_on: "eval:doc.default_category"` for visibility, but no `get_query` or `link_filters` to restrict sub-categories to those belonging to the selected category. An admin can select any category as a sub-category regardless of parent relationship.
**Impact:** Admin UX issue -- can create models with mismatched category/sub-category, which will then fail HD Ticket's `validate_category()` when applied.

### P3-2: No guard against applying models to resolved/closed tickets
**Severity: P3 (Low)**
**Description:** `apply_incident_model()` does not check the ticket's current status. A model can be applied to a resolved or closed ticket, potentially overwriting priority, team, and adding checklist items to an already-closed ticket.
**Impact:** Minor data integrity concern. Unlikely to happen in normal workflows but no guardrail exists.

### P3-3: No HD Incident Model DocType test file
**Severity: P3 (Low)**
**Description:** There is no `test_hd_incident_model.py` for the HD Incident Model DocType itself. All tests are in `test_incident_model.py` under HD Ticket. There are no tests for model creation validation, uniqueness enforcement, or permission boundary testing (e.g., can a customer read incident models?).

### P3-4: `frappe.db.commit()` anti-pattern in API methods
**Severity: P3 (Low)**
**Description:** Both `apply_incident_model` and `complete_checklist_item` call `frappe.db.commit()` explicitly (with `# nosemgrep` to suppress the linter). In Frappe, whitelisted API methods auto-commit on success. Explicit commits can cause partial data persistence in error scenarios and break transaction isolation.
**Impact:** If an error occurs after `ticket_doc.save()` but before the function returns, the data is already committed and cannot be rolled back. This is also the root cause of P2-5 (test data leaks).

---

## Regression Check

| Area | Status |
|------|--------|
| Story 1.8 (Major Incident) tests | PASS (12/12) |
| Story 1.4 (Internal Notes) tests | PASS (10/10) |
| Ticket list/detail loading | OK (HTTP 200) |
| Login flow | OK |

---

## Summary

| Severity | Count |
|----------|-------|
| P0 (Critical) | 0 |
| P1 (High) | 2 |
| P2 (Medium) | 6 |
| P3 (Low) | 4 |
| **Total** | **12** |

The core backend logic is solid -- model application, checklist toggling, and resolution validation all work correctly via API. However, there are significant frontend issues (missing `__` import causes runtime errors), security gaps (no `is_agent` check, no ITIL flag gating), and design fragility (hardcoded Select vs Link for priority). The explicit `frappe.db.commit()` calls cause test data to leak into the database and are a transaction safety hazard.

**Recommendation:** Create a fix task addressing at minimum the two P1 issues and the P2-3 security issue before considering this story complete.
