# Story: Fix: Reverted savepoint isolation + broad except in close_tickets_after_n_days (P1s from QA task-116)

Status: in-progress
Task ID: mn3cyabpids6so
Task Number: #125
Workflow: quick-dev
Model: sonnet
Created: 2026-03-23T15:46:10.353Z

## Description

## P1 Fixes Required

### P1 #1: Savepoint isolation was reverted
Story #106 added `frappe.db.savepoint()` per iteration in `close_tickets_after_n_days` but commit a7891185d removed it. The current code uses bare commit/rollback with no savepoint boundary. If a Frappe hook or child document internally calls commit() before the except block, partial state persists across iterations.

**Fix:** Re-add `with frappe.db.savepoint():` around each iteration in the loop.

### P1 #2: Except clause broadened back to except Exception
Story #106 narrowed to `(frappe.ValidationError, frappe.LinkValidationError)` but a7891185d changed it back to `except Exception:`. This swallows OperationalError, SecurityException, etc.

**Fix:** Narrow to `except (frappe.ValidationError, frappe.LinkValidationError, frappe.DoesNotExistError):` — these are the only expected failure modes for auto-close.

### P1 #3: Zero test coverage for close_tickets_after_n_days
Add tests covering: (a) happy path auto-close, (b) error isolation — failing ticket does not prevent subsequent closures, (c) checklist validation blocks auto-close.

### Files to modify
- `helpdesk/helpdesk/doctype/hd_ticket/hd_ticket.py` — lines 1506-1524
- New test file or add to existing hd_ticket tests
- Sync to bench after changes

## Acceptance Criteria

- [ ] Implementation matches task description
- [ ] No regressions introduced
- [ ] Code compiles/builds without errors

## Tasks / Subtasks

- [ ] Implement changes
- [ ] Verify build passes

## Dev Notes



### References

- Task source: Claude Code Studio task #125

## Dev Agent Record

### Agent Model Used

sonnet

### Completion Notes List

_(Updated by agent on completion)_

### Change Log

_(Updated by agent during implementation)_

### File List

_(Updated by agent — list all files created or modified)_
