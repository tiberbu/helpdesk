# Story: Fix: P1 hd_ticket.py production code not updated — savepoint CM + exception simplification never applied

Status: done
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

- [x] Implement changes
- [x] Verify build passes

## Dev Notes



### References

- Task source: Claude Code Studio task #185

## Dev Agent Record

### Agent Model Used

sonnet

### Completion Notes List

CORRECTION (story-197): This story was "born fabricated" — it was created with Status: in-progress but its described implementation was ALREADY COMMITTED in the same commit (4bff11be6eee6d53514931c3f84950e513195635) that created this story file. The task-184 agent bundled story-185's work into task-184's commit. See QA report docs/qa-report-task-184.md Finding #3 and Finding #1.

The following changes were delivered in commit 4bff11be6 (task-184's commit, NOT a dedicated story-185 commit):
- P1-a fixed: `_autoclose_savepoint` context manager added to `hd_ticket.py`. Manual `frappe.db.savepoint()` / `frappe.db.release_savepoint()` / `frappe.db.rollback(save_point=...)` calls inside the loop are gone; loop body is now `with _autoclose_savepoint(ticket):`.
- P1-b fixed: `except Exception as exc` + `isinstance(exc, frappe.ValidationError)` replaced with proper `except frappe.ValidationError as exc` / `except Exception` hierarchy inside the CM.
- P2 fixed: `test_checklist_validation_blocks_auto_close` now asserts `mock_logger.warning.assert_called_once()` and checks message contains ticket name. `test_stale_ticket_does_not_exist_is_skipped` now asserts warning was logged with ticket name + "validation" in the message.
- P3 fixed: New `test_unexpected_error_is_logged` test covers the `except Exception` branch (OperationalError/deadlock), asserting `frappe.log_error` is called with the ticket name in the title.
- All 6 tests pass (1.683s). Both files synced to bench.

This story has no independent commit of its own. Its work is attributable to commit 4bff11be6.

### Change Log

- `hd_ticket.py`: Added `from contextlib import contextmanager` import; added `_autoclose_savepoint(ticket)` CM before `close_tickets_after_n_days`; replaced 16-line manual savepoint/try/except/isinstance block with `with _autoclose_savepoint(ticket):` (3 lines).
- `test_close_tickets.py`: Added `mock_logger` assertions to `test_checklist_validation_blocks_auto_close` and `test_stale_ticket_does_not_exist_is_skipped`; added new `test_unexpected_error_is_logged` test (section f).

### File List

- `helpdesk/helpdesk/doctype/hd_ticket/hd_ticket.py` (modified + synced to bench)
- `helpdesk/helpdesk/doctype/hd_ticket/test_close_tickets.py` (modified + synced to bench)
