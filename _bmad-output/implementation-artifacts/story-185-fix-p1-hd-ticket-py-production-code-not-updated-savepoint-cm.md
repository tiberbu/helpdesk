# Story: Fix: P1 hd_ticket.py production code not updated — savepoint CM + exception simplification never applied

Status: in-progress
Task ID: mn3f2xhivbgs5l
Task Number: #185
Workflow: quick-dev
Model: sonnet
Created: 2026-03-23T16:45:43.223Z

## Description

## QA Findings from adversarial review (task-174) of task-165

### P1: Production code NOT changed — savepoint context manager claim is false
Story-165 completion notes claim manual savepoint/release/rollback was replaced with `db_savepoint` context manager. This never happened. `hd_ticket.py:1542-1554` still uses manual `frappe.db.savepoint(_sp)`, `frappe.db.release_savepoint(_sp)`, and `frappe.db.rollback(save_point=_sp)`. Commit cfe1f482b has zero changes to hd_ticket.py.

### P1: Production code NOT changed — exception hierarchy not simplified
Story-165 claims `except Exception + isinstance` was replaced with `except frappe.ValidationError`. Code still reads `except Exception as exc` at line 1552 with isinstance check at 1555.

### P2: Tests for DoesNotExist and checklist paths only assert no-crash, not logging behavior
test_stale_ticket_does_not_exist_is_skipped only checks function doesnt raise. No assertion that warning was logged. test_checklist_validation_blocks_auto_close lost its Error Log assertion from prior version.

### P3: No test for OperationalError path
The else branch (lines 1561-1569) with frappe.log_error() for unexpected exceptions has zero test coverage.

### Files to modify
- helpdesk/helpdesk/doctype/hd_ticket/hd_ticket.py (lines 1536-1571): Replace manual savepoint with CM, simplify exception handling
- helpdesk/helpdesk/doctype/hd_ticket/test_close_tickets.py: Add logging assertions, add OperationalError test
- Sync both files to bench after changes
- Correct story-165 completion notes to match reality

## Acceptance Criteria

- [ ] Implementation matches task description
- [ ] No regressions introduced
- [ ] Code compiles/builds without errors

## Tasks / Subtasks

- [ ] Implement changes
- [ ] Verify build passes

## Dev Notes



### References

- Task source: Claude Code Studio task #185

## Dev Agent Record

### Agent Model Used

sonnet

### Completion Notes List

_(Updated by agent on completion)_

### Change Log

_(Updated by agent during implementation)_

### File List

_(Updated by agent — list all files created or modified)_
