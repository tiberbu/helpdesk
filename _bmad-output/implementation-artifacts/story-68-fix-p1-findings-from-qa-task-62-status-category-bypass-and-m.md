# Story: Fix: P1 findings from QA task-62 — status_category bypass and missing migration patch

Status: done
Task ID: mn3agaq2jw9da7
Task Number: #68
Workflow: quick-dev
Model: sonnet
Created: 2026-03-23T14:36:01.810Z

## Description

## P1 Findings from Adversarial Review (docs/qa-report-task-62.md)

### F-01 [P1] — set_status_category() short-circuit allows server-side resolution guard bypass

In hd_ticket.py, `set_status_category()` uses `self.status_category = self.status_category or frappe.get_value(...)` which means once status_category is set, it never re-derives from the current status. When a ticket status changes from Replied (Paused) to Resolved (Resolved), the status_category remains Paused because the `or` short-circuit preserves the old value. This means `validate_checklist_before_resolution()` never fires.

**Fix:** Change `set_status_category()` to always re-derive: `self.status_category = frappe.get_value("HD Ticket Status", self.status, "category")` (remove the `or` short-circuit).

### F-02 [P1] — No migration patch for Select->Link field type change on HD Incident Model

The default_priority field was changed from Select to Link (HD Ticket Priority). Existing deployments that already ran the original patch will not get the column type updated. Need a new migration patch.

**Fix:** Add a new patch to patches.txt that does `frappe.reload_doctype("HD Incident Model", force=True)` and validates existing default_priority values exist as HD Ticket Priority docs.

### Also fix (P2):
- F-04: Add test for is_agent() permission guard (customer user should get PermissionError)
- F-05: Add test for ITIL-mode-disabled rejection path

## Acceptance Criteria

- [x] Implementation matches task description
- [x] No regressions introduced
- [x] Code compiles/builds without errors

## Tasks / Subtasks

- [x] Implement changes
- [x] Verify build passes

## Dev Notes



### References

- Task source: Claude Code Studio task #68

## Dev Agent Record

### Agent Model Used

sonnet

### Completion Notes List

- F-01 fixed: `set_status_category()` now always re-derives from current status (removed `or` short-circuit). This ensures `validate_checklist_before_resolution()` fires correctly when transitioning to Resolved.
- F-02 fixed: New patch `reload_incident_model_for_link_field.py` added to `patches.txt`. It calls `frappe.reload_doctype("HD Incident Model", force=True)` and clears any `default_priority` values that no longer exist as HD Ticket Priority docs.
- F-04 fixed: New test `test_apply_model_raises_permission_error_for_non_agent` — verifies customer (non-agent) user gets PermissionError.
- F-05 fixed: New test `test_apply_model_raises_validation_error_when_itil_disabled` — verifies ValidationError when ITIL mode is off.
- All 13 incident model tests pass.

### Change Log

- `helpdesk/helpdesk/doctype/hd_ticket/hd_ticket.py`: Fixed `set_status_category()` — removed `or` short-circuit, always re-derives from current status.
- `helpdesk/patches/v1_phase1/reload_incident_model_for_link_field.py`: New migration patch for HD Incident Model default_priority Select→Link field change.
- `helpdesk/patches.txt`: Added new patch entry.
- `helpdesk/helpdesk/doctype/hd_ticket/test_incident_model.py`: Added 2 new tests (F-04, F-05).

### File List

- `helpdesk/helpdesk/doctype/hd_ticket/hd_ticket.py` (modified)
- `helpdesk/patches/v1_phase1/reload_incident_model_for_link_field.py` (created)
- `helpdesk/patches.txt` (modified)
- `helpdesk/helpdesk/doctype/hd_ticket/test_incident_model.py` (modified)
