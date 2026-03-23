# Story: Fix: P1 unguarded fallback logger + commit failure cascade in _autoclose_savepoint

Status: done
Task ID: mn3ng9g5wg6rrm
Task Number: #215
Workflow: quick-dev
Model: sonnet
Created: 2026-03-23T20:39:52.280Z

## Description

## P1 Findings from adversarial review (task-213) of task-207

### F-01 [P1]: Unguarded fallback logger at line 1583
The last-resort fallback `frappe.logger().error(...)` at line 1583 of hd_ticket.py has NO try/except guard. If `frappe.log_error()` fails AND `frappe.logger().error()` also fails, the exception propagates and kills the cron batch. This is the exact class of bug task-207 was supposed to fix.

**File:** `helpdesk/helpdesk/doctype/hd_ticket/hd_ticket.py`, line 1583
**Fix:** Wrap in `try: ... except Exception: pass`

### F-02 [P1]: Commit failure guard creates silent failure cascade
Lines 1628-1638: when `frappe.db.commit()` fails, the code logs and continues to the next ticket. But with a dead connection, every subsequent iteration will also fail. No `frappe.db.rollback()` or connection health check before continuing. Add a break or connection check after commit failure.

**File:** `helpdesk/helpdesk/doctype/hd_ticket/hd_ticket.py`, lines 1628-1638
**Fix:** After commit failure, attempt rollback and break the loop (or at minimum, attempt reconnect).

### Additional P2 items (fix if time permits)
- F-04: Add tests for F-01 commit guard, F-02 warning guard, F-03 rollback failure logging
- F-05: Change `str(_pending_log[1] or "")` to `str(_pending_log[1]) if _pending_log[1] is not None else ""`
- F-10: Extract `_safe_log(level, msg)` helper to reduce nested try/except depth

### Done Checklist
- [x] Line 1583 fallback logger wrapped in try/except
- [x] Commit failure at line 1628 triggers loop break or reconnect attempt
- [x] Both fixes synced to /home/ubuntu/frappe-bench/apps/helpdesk/
- [x] All close_tickets tests pass (8/8 ✔)
- [x] Story file updated with completion notes

## Acceptance Criteria

- [ ] Implementation matches task description
- [ ] No regressions introduced
- [ ] Code compiles/builds without errors

## Tasks / Subtasks

- [ ] Implement changes
- [ ] Verify build passes

## Dev Notes



### References

- Task source: Claude Code Studio task #215

## Dev Agent Record

### Agent Model Used

sonnet

### Completion Notes List

- F-01 fixed: Wrapped the fallback `frappe.logger().error(...)` call at the old line 1583 in its own `try/except Exception: pass` block so it can never propagate if the logger itself raises. Also applied the P2 F-05 fix (None-safe string coercion) in the same change.
- F-02 fixed: After a `frappe.db.commit()` failure in `close_tickets_after_n_days`, the code now attempts `frappe.db.rollback()` (guarded) and then `break`s out of the ticket loop, preventing the silent failure cascade that would occur if iteration continued on a dead connection.
- Both fixes synced to `/home/ubuntu/frappe-bench/apps/helpdesk/`.
- All 8 `test_close_tickets` integration tests pass.

### Change Log

- 2026-03-23: F-01 — wrapped fallback logger in inner try/except; F-05 — None-safe string coercion; F-02 — rollback + break on commit failure.

### File List

- `helpdesk/helpdesk/doctype/hd_ticket/hd_ticket.py` (modified — F-01, F-02, F-05 fixes)
