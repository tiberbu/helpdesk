# Story: Fix: P1 _autoclose_savepoint defensive gaps — handler uses dead DB + Error Log lost in savepoint scope + missing multi-ticket OperationalError test

Status: in-progress
Task ID: mn3fhg1z9se3eg
Task Number: #198
Workflow: quick-dev
Model: sonnet
Created: 2026-03-23T16:57:06.287Z

## Description

## QA Findings from adversarial review (task-190) of task-185

### F-01 [P1]: Exception handler calls frappe.db.rollback() and frappe.log_error() which both need a live DB connection. If the exception IS a DB connection failure (MySQL server has gone away), both calls throw secondary exceptions that propagate unhandled, killing the cron batch. The handler needs defensive inner try/except around both DB operations.

### F-02 [P1]: frappe.log_error() inside _autoclose_savepoint writes an Error Log document INSIDE the savepoint scope. When the savepoint is rolled back, the Error Log is rolled back too. The subsequent frappe.db.commit() at line 1577 persists nothing. Error logs for unexpected exceptions are silently lost. Move frappe.log_error() AFTER the savepoint rollback or outside the CM scope.

### F-03 [P1]: No multi-ticket isolation test for except Exception path. test_error_isolation_between_tickets only tests ValidationError. test_unexpected_error_is_logged only tests single ticket. Need a test with 2+ tickets where first triggers OperationalError and second still closes. This gap was flagged in qa-report-task-168.md (F-05) and remains unaddressed.

### Files to modify
- helpdesk/helpdesk/doctype/hd_ticket/hd_ticket.py: Defensive try/except in handler + move log_error outside savepoint scope
- helpdesk/helpdesk/doctype/hd_ticket/test_close_tickets.py: Add multi-ticket OperationalError isolation test
- Sync both files to bench

### Also fix (P2)
- F-04: Remove try/except self.fail() anti-pattern from tests (e) and (f) — just call the function directly
- F-06: Update story-165 completion notes to remove false claims about db_savepoint CM

## Acceptance Criteria

- [ ] Implementation matches task description
- [ ] No regressions introduced
- [ ] Code compiles/builds without errors

## Tasks / Subtasks

- [ ] Implement changes
- [ ] Verify build passes

## Dev Notes



### References

- Task source: Claude Code Studio task #198

## Dev Agent Record

### Agent Model Used

sonnet

### Completion Notes List

_(Updated by agent on completion)_

### Change Log

_(Updated by agent during implementation)_

### File List

_(Updated by agent — list all files created or modified)_
