# Story: Fix: P0 bench test sync broken + P1 divergent delete_entry logic + misleading nan comment

Status: done
Task ID: mn3ddahhtbxkjm
Task Number: #136
Workflow: quick-dev
Model: sonnet
Created: 2026-03-23T15:58:06.351Z

## Description

## P0/P1 findings from adversarial review (docs/qa-report-task-131.md)

### P0: Bench test file fatally out of sync
The dev copy of test_hd_time_entry.py imports ensure_agent_manager_user, ensure_hd_admin_user, ensure_system_manager_user from helpdesk.test_utils. The bench copy still uses inline helpers and does NOT import these shared functions. Running bench run-tests produces ImportError. ALL tests fail to discover on bench.

**Fix:** rsync the dev test file to bench: `cp helpdesk/helpdesk/doctype/hd_time_entry/test_hd_time_entry.py /home/ubuntu/frappe-bench/apps/helpdesk/helpdesk/helpdesk/doctype/hd_time_entry/test_hd_time_entry.py`
Also ensure test_utils.py is synced to bench.

### P1: Bench delete_entry has divergent security logic
Dev uses `if not is_agent() and not is_privileged` but bench uses a completely different pattern with is_admin(), _any_allowed_roles, and HD Agent table lookup. These are functionally different authorization checks.

**Fix:** Sync dev time_tracking.py to bench.

### P1: Comment incorrectly states int(float(nan)) raises OverflowError
Line 42 of time_tracking.py groups nan with inf under OverflowError. This is wrong — int(float(nan)) raises ValueError, not OverflowError. Fix the comment.

### P2: Missing billable=inf test for add_entry, missing nan test via stop_timer
Add test_add_entry_rejects_inf_billable and test_stop_timer_rejects_nan_duration.

### Files to modify
- helpdesk/api/time_tracking.py (fix comment, sync to bench)
- helpdesk/helpdesk/doctype/hd_time_entry/test_hd_time_entry.py (add missing tests, sync to bench)
- helpdesk/test_utils.py (verify bench sync)

## Acceptance Criteria

- [x] Implementation matches task description
- [x] No regressions introduced
- [x] Code compiles/builds without errors

## Tasks / Subtasks

- [x] Implement changes
- [x] Verify build passes

## Dev Notes



### References

- Task source: Claude Code Studio task #136

## Dev Agent Record

### Agent Model Used

sonnet

### Completion Notes List

- P0/P1 bench sync: Both bench files were already identical to dev (a prior task had synced them). No re-sync was needed for those.
- P1 comment fix: Corrected the misleading comment in `_require_int_str` — `int(float("nan"))` raises `ValueError`, NOT `OverflowError`. Updated comment to accurately distinguish the two exception types.
- P2 tests: Added `test_add_entry_rejects_inf_billable` and `test_stop_timer_rejects_nan_duration` to the test file.
- All 66 tests pass on bench (up from 64).

### Change Log

- Fixed misleading comment in `helpdesk/api/time_tracking.py` lines 40-43: `int(float("nan"))` raises ValueError, not OverflowError.
- Added 2 new P2 tests to `test_hd_time_entry.py`: `test_add_entry_rejects_inf_billable`, `test_stop_timer_rejects_nan_duration`.
- Synced both files to bench.

### File List

- `helpdesk/api/time_tracking.py` — fixed nan comment
- `helpdesk/helpdesk/doctype/hd_time_entry/test_hd_time_entry.py` — added 2 P2 tests
- `/home/ubuntu/frappe-bench/apps/helpdesk/helpdesk/api/time_tracking.py` — synced
- `/home/ubuntu/frappe-bench/apps/helpdesk/helpdesk/helpdesk/doctype/hd_time_entry/test_hd_time_entry.py` — synced
