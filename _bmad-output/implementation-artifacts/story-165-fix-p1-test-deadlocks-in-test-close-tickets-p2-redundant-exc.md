# Story: Fix: P1 test deadlocks in test_close_tickets + P2 redundant exception hierarchy + destructive setUp

Status: in-progress
Task ID: mn3ei12wkl7kag
Task Number: #165
Workflow: quick-dev
Model: sonnet
Created: 2026-03-23T16:29:34.315Z

## Description

## QA Findings from task-157 (adversarial review of task-125)

### P1: Tests deadlock with QueryDeadlockError
Running `bench run-tests --module helpdesk.helpdesk.doctype.hd_ticket.test_close_tickets` fails with deadlock errors in 2 of 4 tests. The `frappe.db.commit()` inside `close_tickets_after_n_days` conflicts with tearDown cleanup of HD Settings singles. Fix the test to handle commit-based functions properly (per MEMORY.md pattern: explicit delete+commit in tearDown, avoid relying on rollback).

### P2: Exception tuple is redundant
`except (frappe.ValidationError, frappe.LinkValidationError, frappe.DoesNotExistError)` — both LinkValidationError and DoesNotExistError are subclasses of ValidationError. Either simplify to just `except frappe.ValidationError:` or narrow further to specific non-overlapping exceptions.

### P2: setUp does destructive frappe.db.delete("HD Ticket")
Nukes ALL tickets, not just test-created ones. Use per-record cleanup tracking instead.

### P2: No test for DoesNotExistError path
Add a test where ticket is deleted between query and close attempt.

### P2: Use frappe.database.database.savepoint context manager
Replace manual savepoint/release/rollback with the built-in context manager for cleaner code.

### Files to modify
- helpdesk/helpdesk/doctype/hd_ticket/hd_ticket.py (lines 1515-1542)
- helpdesk/helpdesk/doctype/hd_ticket/test_close_tickets.py (full rewrite of setUp/tearDown + add test)
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

- Task source: Claude Code Studio task #165

## Dev Agent Record

### Agent Model Used

sonnet

### Completion Notes List

_(Updated by agent on completion)_

### Change Log

_(Updated by agent during implementation)_

### File List

_(Updated by agent — list all files created or modified)_
