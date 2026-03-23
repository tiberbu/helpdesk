# Story: Fix: _require_int_str inf/nan 500 error (P1) + empty commit audit trail (P1) from QA #129

Status: done
Task ID: mn3d60wtrw41w4
Task Number: #132
Workflow: quick-dev
Model: sonnet
Created: 2026-03-23T15:52:12.045Z

## Description

## P1 Findings from QA Report task-126.md

### P1-1: _require_int_str does not handle inf/infinity/nan strings
`int(float("inf"))` raises OverflowError (not ValueError), so the except ValueError clause misses it. Passing `duration_minutes="inf"` to add_entry() or stop_timer() produces an unhandled 500 Internal Server Error. This has been flagged in TWO consecutive QA reports (qa-report-task-114.md Finding 6, qa-report-task-126.md Finding 5) without being fixed.

**Fix:** Change `except ValueError` to `except (ValueError, OverflowError)` in _require_int_str. Add tests for "inf", "infinity", "nan", "-inf" inputs.

### P1-2: Process — task #126 commit contains zero code changes
Commit aafbe478a only modified markdown files. Actual code changes landed in commit d1a9de058 under a different task. This breaks git audit trail. Document this as a process note — no code fix needed, but future tasks should ensure code changes are in the correct commit.

### Files to change
- helpdesk/api/time_tracking.py (_require_int_str except clause)
- helpdesk/helpdesk/doctype/hd_time_entry/test_hd_time_entry.py (add inf/nan tests)
- Copy both to bench after changes

### Verification
- ALL tests must pass
- Manually verify: add_entry with duration_minutes="inf" returns 417 not 500

## Acceptance Criteria

- [x] Implementation matches task description
- [x] No regressions introduced
- [x] Code compiles/builds without errors

## Tasks / Subtasks

- [x] Implement changes
- [x] Verify build passes

## Dev Notes



### References

- Task source: Claude Code Studio task #132

## Dev Agent Record

### Agent Model Used

sonnet

### Completion Notes List

- P1-1: `_require_int_str` in `time_tracking.py` already had `except (ValueError, OverflowError)` applied in a prior session. No code change was needed — the fix was already correct.
- Added 3 new tests to `test_hd_time_entry.py` covering "inf", "-inf", and "nan" as `duration_minutes` via `add_entry()`. Combined with the pre-existing "inf" (billable) and "Infinity" (duration via stop_timer) tests, all specified inf/nan inputs are now exercised.
- P1-2: Process note — commit aafbe478a (task #126) contained only markdown changes; code landed in d1a9de058. No code fix required; documented here.
- All 66 tests pass (Ran 66 tests in 24.235s — OK).

### Change Log

- 2026-03-23: Added 3 tests to `test_hd_time_entry.py` for inf/nan/negative-inf edge cases in `_require_int_str`.
- 2026-03-23: Copied updated `test_hd_time_entry.py` to bench. Verified `time_tracking.py` already has `except (ValueError, OverflowError)` — no change needed.

### File List

- `helpdesk/helpdesk/doctype/hd_time_entry/test_hd_time_entry.py` — added 3 new inf/nan/negative-inf tests
- Bench copy: `/home/ubuntu/frappe-bench/apps/helpdesk/helpdesk/helpdesk/doctype/hd_time_entry/test_hd_time_entry.py`
