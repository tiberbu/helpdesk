# Story: Fix: P1 findings from QA task-78 — regression test gaps, migration error handling, status_category trust boundary

Status: done
Task ID: mn3b6qvd2n8gyc
Task Number: #81
Workflow: quick-dev
Model: sonnet
Created: 2026-03-23T14:56:40.286Z

## Description

## P1 Findings from Adversarial Review (docs/qa-report-task-73.md)

### F-01 [P1] — set_status_category() trusts pre-populated status_category without validating it matches status
The has_value_changed guard + truthiness check means pre-populated tickets skip re-derivation. If status_category is set via API/import and doesnt match status, it persists unchecked.

### F-02 [P1] — Regression test uses ignore_permissions=True, doesnt exercise real user workflow
test_status_category_updates_when_status_changes uses save(ignore_permissions=True), bypassing check_update_perms() and other before_validate hooks. Doesnt prove the fix works in production path.

### F-03 [P1] — Regression test verifies status_category update but NOT the original bug: checklist guard bypass
The original P1 was that stale status_category allowed bypassing mandatory checklist resolution guard. The test only asserts status_category value, never tests that validate_checklist_before_resolution() actually fires on Replied->Resolved transition with incomplete checklist.

### Also fix (P2):
- F-04: Migration exception handler catches ALL exceptions, should only catch table-not-found
- F-05: Migration commits on exception path (dangerous)
- F-06: No test for complete_checklist_item when ITIL mode disabled (original F-08 still unaddressed)

### Files to modify:
- helpdesk/helpdesk/doctype/hd_ticket/hd_ticket.py (F-01: add cross-validation of status vs status_category)
- helpdesk/helpdesk/doctype/hd_ticket/test_incident_model.py (F-02/F-03: fix regression test + add end-to-end checklist bypass test + F-06: ITIL-disabled test for complete_checklist_item)
- helpdesk/patches/v1_phase1/reload_incident_model_for_link_field.py (F-04/F-05: precise exception handling)

## Acceptance Criteria

- [x] Implementation matches task description
- [x] No regressions introduced
- [x] Code compiles/builds without errors

## Tasks / Subtasks

- [x] Implement changes
- [x] Verify build passes

## Dev Notes



### References

- Task source: Claude Code Studio task #81

## Dev Agent Record

### Agent Model Used

sonnet

### Completion Notes List

- F-01: Removed `has_value_changed("status") and self.status_category` guard from `set_status_category()`. Now always re-derives from current status when status is non-empty, preventing stale status_category from persisting via API/import.
- F-02: Removed `ignore_permissions=True` from `test_status_category_updates_when_status_changes` — test now exercises real agent save path including all before_validate hooks.
- F-03: Added `test_replied_to_resolved_blocked_by_incomplete_checklist` — proves the original P1 bug is fixed end-to-end: Replied→Resolved transition with incomplete mandatory checklist raises ValidationError.
- F-04: Migration exception handler now only suppresses table-not-found errors (checks for "doesn't exist" or "1146" in error string); re-raises all other exceptions.
- F-05: Removed `frappe.db.commit()` from exception path in migration — no commit when nothing was changed.
- F-06: Added `test_complete_checklist_item_raises_when_itil_disabled` — proves the ITIL-disabled guard on complete_checklist_item fires.
- All 17 tests pass (bench run-tests).

### Change Log

- `helpdesk/helpdesk/doctype/hd_ticket/hd_ticket.py`: Removed `has_value_changed` guard in `set_status_category()` — always re-derives from status.
- `helpdesk/helpdesk/doctype/hd_ticket/test_incident_model.py`: Fixed F-02 test (removed ignore_permissions), added F-03 e2e test, added F-06 ITIL-disabled test.
- `helpdesk/patches/v1_phase1/reload_incident_model_for_link_field.py`: Precise exception handling (F-04), no commit on exception path (F-05).

### File List

- `helpdesk/helpdesk/doctype/hd_ticket/hd_ticket.py` (modified)
- `helpdesk/helpdesk/doctype/hd_ticket/test_incident_model.py` (modified)
- `helpdesk/patches/v1_phase1/reload_incident_model_for_link_field.py` (modified)
