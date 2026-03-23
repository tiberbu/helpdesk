# Story: Fix: P1 findings from QA task-69 — status_category None regression, missing bypass test, migration hardening

Status: done
Task ID: mn3ata28e6ihmx
Task Number: #73
Workflow: quick-dev
Model: sonnet
Created: 2026-03-23T14:46:16.827Z

## Description

## P1 Findings from Adversarial Review (docs/qa-report-task-68.md)

### F-01 [P1] — set_status_category() now sets None for invalid/empty statuses

The fix removed the `or` short-circuit but introduced a regression: when self.status is None, empty, or references a deleted HD Ticket Status record, frappe.get_value() returns None, and status_category is silently wiped. The correct fix should check `self.has_value_changed("status") or not self.status_category` before re-deriving, or fall back to existing value when frappe.get_value returns None.

### F-02 [P1] — No test for the exact stale status_category bypass scenario

The core P1 fix has zero automated regression protection. Need a test that: (1) saves a ticket as Replied (category Paused), (2) changes status to Resolved, (3) verifies status_category updates to Resolved (not stale Paused).

### Also fix (P2):
- F-03: Add frappe.db.commit() to migration patch
- F-04: Add try/except for tabHD Ticket Priority table existence in migration
- F-05: Reload HD Incident Checklist Item child doctype in migration
- F-06: Clean up test user in permission test tearDown
- F-07: Add permission test for complete_checklist_item (not just apply_incident_model)

### Files to modify:
- helpdesk/helpdesk/doctype/hd_ticket/hd_ticket.py (set_status_category defensive fix)
- helpdesk/patches/v1_phase1/reload_incident_model_for_link_field.py (hardening)
- helpdesk/helpdesk/doctype/hd_ticket/test_incident_model.py (add bypass test + complete_checklist_item tests)

## Acceptance Criteria

- [x] Implementation matches task description
- [x] No regressions introduced
- [x] Code compiles/builds without errors

## Tasks / Subtasks

- [x] Implement changes
- [x] Verify build passes

## Dev Notes



### References

- Task source: Claude Code Studio task #73

## Dev Agent Record

### Agent Model Used

sonnet

### Completion Notes List

- F-01: `set_status_category()` now only re-derives when status has changed OR status_category is unset. Falls back gracefully when `frappe.get_value()` returns None (deleted/invalid status). Prevents silent wipe of status_category.
- F-02: Added `test_status_category_updates_when_status_changes` — saves ticket as Replied (Paused), changes to Resolved, asserts status_category is Resolved.
- F-03: Migration patch now calls `frappe.db.commit()` at end of `execute()`.
- F-04: Migration patch wraps the `tabHD Ticket Priority` SQL query in try/except to handle missing table on clean install.
- F-05: Migration patch now also calls `frappe.reload_doctype("HD Incident Checklist Item", force=True)`.
- F-06: tearDown explicitly deletes `im_customer_noagent@example.com` before rollback.
- F-07: Added `test_complete_checklist_item_raises_permission_error_for_non_agent`.
- Bonus: Added `category_required_on_resolution=0` to setUp to fix 2 pre-existing test failures that were masked.
- All 15 tests in test_incident_model.py pass.

### Change Log

- 2026-03-23: F-01 `hd_ticket.py` set_status_category defensive fix (already committed via story-75 Time Tracking fix)
- 2026-03-23: F-02/F-06/F-07 added 3 new tests to test_incident_model.py + tearDown cleanup + setUp category fix
- 2026-03-23: F-03/F-04/F-05 hardened reload_incident_model_for_link_field.py migration patch

### File List

- `helpdesk/helpdesk/doctype/hd_ticket/hd_ticket.py` — F-01 set_status_category defensive fix
- `helpdesk/helpdesk/doctype/hd_ticket/test_incident_model.py` — F-02/F-06/F-07 new tests + setUp/tearDown hardening
- `helpdesk/patches/v1_phase1/reload_incident_model_for_link_field.py` — F-03/F-04/F-05 migration hardening
