# Story: Fix: P1 unguarded commit() in autoclose loop + asymmetric ValidationError handler + dropped F-06

Status: in-progress
Task ID: mn3ftudcbouiy6
Task Number: #207
Workflow: quick-dev
Model: sonnet
Created: 2026-03-23T17:06:52.746Z

## Description

## QA Findings from adversarial review (task-200) of task-198

### F-01 [P1]: Unguarded frappe.db.commit() at line 1611 defeats defensive architecture
The _autoclose_savepoint CM meticulously guards rollback and log_error calls, but the frappe.db.commit() at line 1611 (OUTSIDE the CM) has no try/except. If the DB connection dies between CM exit and commit, the exception propagates uncaught, killing the entire cron batch. This is the exact scenario F-01 was designed to prevent. Wrap in try/except with frappe.logger().error() fallback.

### F-02 [P1]: ValidationError handler frappe.logger().warning() is not defensively wrapped
Lines 1541-1543: the except ValidationError handler calls frappe.logger().warning() without a try/except guard, unlike the except Exception handler which guards everything. Asymmetric treatment. If connection is dead when a ValidationError fires, warning() could fail.

### F-03 [P1]: Silent rollback failure — inner except Exception: pass swallows rollback error with no logging
Lines 1539-1540 and 1548-1549: if frappe.db.rollback() fails, the error is silently swallowed. No indication anywhere that the rollback failed. Add frappe.logger().warning() in the inner except to at least record that rollback failed.

### F-04 [P2]: F-06 from task description silently dropped
Task-198 description explicitly included F-06: Update story-165 completion notes to remove false claims about db_savepoint CM. This was never done and not mentioned in Completion Notes.

### F-05 [P2]: No test for frappe.log_error() failure fallback path
The _pending_log block has a fallback to frappe.logger().error() when frappe.log_error() raises. This path has zero test coverage. Add a test where frappe.log_error is mocked to raise and verify frappe.logger().error is called.

### F-06 [P2]: None concatenation risk in fallback logger
Line 1566: frappe.logger().error(_pending_log[0] + chr(10) + _pending_log[1]) — if frappe.get_traceback() returns None, this raises TypeError. Add str

## Acceptance Criteria

- [ ] Implementation matches task description
- [ ] No regressions introduced
- [ ] Code compiles/builds without errors

## Tasks / Subtasks

- [ ] Implement changes
- [ ] Verify build passes

## Dev Notes



### References

- Task source: Claude Code Studio task #207

## Dev Agent Record

### Agent Model Used

sonnet

### Completion Notes List

_(Updated by agent on completion)_

### Change Log

_(Updated by agent during implementation)_

### File List

_(Updated by agent — list all files created or modified)_
