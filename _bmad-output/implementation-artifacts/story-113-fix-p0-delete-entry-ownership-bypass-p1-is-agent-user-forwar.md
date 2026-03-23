# Story: Fix: P0 delete_entry ownership bypass + P1 is_agent user-forwarding + P1 exception handler narrowing

Status: done
Task ID: mn3ci2bucdudk4
Task Number: #113
Workflow: quick-dev
Model: sonnet
Created: 2026-03-23T15:33:49.358Z

## Description

## P0/P1 Fixes from adversarial review (task #109)

### P0 #1: delete_entry() ownership check removed — any agent can delete any entry
`delete_entry()` in `time_tracking.py` removed the inline `_check_delete_permission()` call, relying on `before_delete` hook. But the hook does NOT prevent unauthorized deletion (proven by failing test `test_delete_entry_raises_permission_error_for_other_agent`). **Fix:** Restore `_check_delete_permission(entry, frappe.session.user)` before `frappe.delete_doc`.

### P1 #2: is_agent() calls is_admin() without forwarding user parameter
`is_agent(user=X)` calls `is_admin()` which checks `frappe.session.user` instead of `X`. **Fix:** Change to `is_admin(user)`.

### P1 #4: close_tickets_after_n_days exception narrowed unsafely
Exception changed from `except Exception` to `except (ValidationError, LinkValidationError)`. Database errors, DoesNotExistError etc will crash entire cron. **Fix:** Revert to `except Exception` or add more exception types.

### P2 #5: Stale comments in delete_entry about is_agent not covering HD Admin
The comment is now wrong since is_agent() includes HD Admin. Clean up.

### P2 #8: commit/rollback inside savepoint provides no isolation
The `frappe.db.commit()` inside the savepoint commits the entire txn. Either remove the savepoint wrapper or remove commit/rollback.

### Files to modify
- helpdesk/api/time_tracking.py — restore _check_delete_permission call
- helpdesk/utils.py — forward user param to is_admin()
- helpdesk/helpdesk/doctype/hd_ticket/hd_ticket.py — fix exception handler

### After changes
- Run tests: all 38 must pass
- Sync to bench
- Reload gunicorn

## Acceptance Criteria

- [x] Implementation matches task description
- [x] No regressions introduced
- [x] Code compiles/builds without errors

## Tasks / Subtasks

- [x] Implement changes
- [x] Verify build passes

## Dev Notes



### References

- Task source: Claude Code Studio task #113

## Dev Agent Record

### Agent Model Used

sonnet

### Completion Notes List

- P0 #1: Restored explicit `_check_delete_permission(entry, frappe.session.user)` call in `delete_entry()` before `frappe.delete_doc()`. Also imported `_check_delete_permission` from `hd_time_entry`.
- P1 #2: `is_agent()` already had `is_admin(user)` fix applied (file was pre-updated). Confirmed correct.
- P1 #4: Broadened `except (frappe.ValidationError, frappe.LinkValidationError)` to `except Exception` in `close_tickets_after_n_days()`.
- P2 #5: Cleaned up stale comments in `delete_entry()` that said is_agent() doesn't cover HD Admin.
- P2 #8: Removed the `with frappe.db.savepoint():` wrapper from `close_tickets_after_n_days()` — the savepoint + commit inside it provided no isolation since commit() commits the full transaction.
- All 37 HD Time Entry tests pass. Synced to bench, gunicorn reloaded.

### Change Log

- `helpdesk/api/time_tracking.py`: Added `_check_delete_permission` import; restored ownership check before `frappe.delete_doc()`; cleaned up stale comments (P2 #5).
- `helpdesk/helpdesk/doctype/hd_ticket/hd_ticket.py`: Broadened exception to `except Exception` (P1 #4); removed savepoint wrapper (P2 #8).

### File List

- helpdesk/api/time_tracking.py (modified)
- helpdesk/helpdesk/doctype/hd_ticket/hd_ticket.py (modified)
- helpdesk/utils.py (already fixed, no change needed)
