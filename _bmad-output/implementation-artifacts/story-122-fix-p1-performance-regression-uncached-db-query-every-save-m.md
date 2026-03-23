# Story: Fix: P1 performance regression (uncached DB query every save) + misleading error for empty category field + test split reality in _resolve_ticket

Status: in-progress
Task ID: mn3csloyxbktc8
Task Number: #122
Workflow: quick-dev
Model: sonnet
Created: 2026-03-23T15:41:47.867Z

## Description

## P1 Findings from Adversarial Review (docs/qa-report-task-99.md)

### F-01 [P1] — Performance regression: unconditional DB query on every save
set_status_category() uses frappe.get_value() (uncached) on every save. Should use frappe.get_cached_value("HD Ticket Status", self.status, "category") to avoid DB round-trip on the hot path while still re-deriving instead of trusting stale values.

### F-02 [P1] — frappe.get_value returns None for BOTH missing record AND empty category field
The error message claims "record no longer exists" but frappe.get_value returns None in two cases: (1) record missing, (2) category field empty. Add frappe.db.exists check to disambiguate. Different error messages for each case.

### F-03 [P1] — _resolve_ticket() in test_hd_ticket.py manually sets status_category
Line 978 sets ticket.status_category = "Resolved" which is now dead code for save() paths but still used by direct validate_category() calls. Tests that call validate_category() directly bypass set_status_category() entirely, creating split reality between test and production paths. Fix: remove the manual status_category assignment and have tests that call validate_category() also call set_status_category() first, or refactor to go through save().

### Also fix (P2):
- F-05: No test for F-02 fix (deleted HD Ticket Status causing ValidationError)
- F-08: close_tickets_after_n_days error logging rolled back by subsequent frappe.db.rollback()

### Files to modify:
- helpdesk/helpdesk/doctype/hd_ticket/hd_ticket.py (F-01: use get_cached_value; F-02: disambiguate missing record vs empty category)
- helpdesk/helpdesk/doctype/hd_ticket/test_incident_model.py (F-05: add test for deleted status record)
- helpdesk/helpdesk/doctype/hd_ticket/test_hd_ticket.py (F-03: fix _resolve_ticket split reality)

## Acceptance Criteria

- [ ] Implementation matches task description
- [ ] No regressions introduced
- [ ] Code compiles/builds without errors

## Tasks / Subtasks

- [ ] Implement changes
- [ ] Verify build passes

## Dev Notes



### References

- Task source: Claude Code Studio task #122

## Dev Agent Record

### Agent Model Used

sonnet

### Completion Notes List

_(Updated by agent on completion)_

### Change Log

_(Updated by agent during implementation)_

### File List

_(Updated by agent — list all files created or modified)_
