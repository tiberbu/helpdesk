# Story: Fix: P1 issues from QA task-71 — tz-aware crash, REST delete bypass, backend maxlength

Status: done
Task ID: mn3aveh7kcz7jx
Task Number: #74
Workflow: quick-dev
Model: sonnet
Created: 2026-03-23T14:47:46.828Z

## Description

## P1 Fixes from QA Report (docs/qa-report-task-67.md)

### Issue #1 (P1): Timezone-Aware started_at Crashes stop_timer
`stop_timer` compares `started_at_dt > now_datetime()` but `get_datetime()` can return a tz-aware datetime while `now_datetime()` returns naive. This raises `TypeError: cant compare offset-naive and offset-aware datetimes`. Fix: strip timezone info with `.replace(tzinfo=None)` before comparing, or wrap in try/except.

### Issue #2 (P1): REST API Bypass of delete_entry Ownership Check
The HD Time Entry DocType gives `delete: 1` to the Agent role. Any agent can bypass the custom ownership check by calling `DELETE /api/resource/HD Time Entry/{name}` directly. Fix: Remove `delete: 1` from the Agent role in `hd_time_entry.json` (keep only for System Manager/Agent Manager), OR add a `before_delete` hook in `hd_time_entry.py` that enforces ownership.

### Issue #3 (P1): Backend Does Not Enforce maxlength on Description
Frontend has `:maxlength="500"` but backend accepts any length. Fix: Add `if len(description or "") > 500: frappe.throw(...)` in both `add_entry` and `stop_timer`.

### Files to Modify
- `helpdesk/api/time_tracking.py` (tz fix + maxlength)
- `helpdesk/helpdesk/doctype/hd_time_entry/hd_time_entry.json` (remove Agent delete perm)
- `helpdesk/helpdesk/doctype/hd_time_entry/test_hd_time_entry.py` (add tests for tz-aware, maxlength, REST bypass)

## Acceptance Criteria

- [x] Implementation matches task description
- [x] No regressions introduced
- [x] Code compiles/builds without errors

## Tasks / Subtasks

- [x] Implement changes
- [x] Verify build passes

## Dev Notes



### References

- Task source: Claude Code Studio task #74

## Dev Agent Record

### Agent Model Used

sonnet

### Completion Notes List

- Fixed tz-aware crash in `stop_timer`: added `.replace(tzinfo=None)` on parsed datetime before comparing with `now_datetime()`, and store the naive datetime to DB to avoid MariaDB format rejection.
- Fixed REST delete bypass: removed `"delete": 1` from Agent role in `hd_time_entry.json` and added `before_delete` hook in `hd_time_entry.py` enforcing ownership (defense-in-depth).
- Confirmed maxlength validation was already implemented in `time_tracking.py` (no change needed).
- Added 4 new tests: tz-aware happy path, tz-aware future rejection, before_delete blocks other agent, before_delete allows own entry.
- All 25 tests pass.

### Change Log

- `helpdesk/api/time_tracking.py`: Strip tzinfo from `started_at_dt` before future-check comparison; store `started_at_naive` (without tzinfo) in DB to avoid MariaDB rejection of ISO-8601-with-offset strings.
- `helpdesk/helpdesk/doctype/hd_time_entry/hd_time_entry.py`: Added `before_delete` hook enforcing ownership (HD Admin / System Manager exempt).
- `helpdesk/helpdesk/doctype/hd_time_entry/hd_time_entry.json`: Removed `"delete": 1` from Agent role permissions.
- `helpdesk/helpdesk/doctype/hd_time_entry/test_hd_time_entry.py`: Added 4 new tests covering tz-aware and before_delete scenarios.

### File List

- `helpdesk/api/time_tracking.py`
- `helpdesk/helpdesk/doctype/hd_time_entry/hd_time_entry.py`
- `helpdesk/helpdesk/doctype/hd_time_entry/hd_time_entry.json`
- `helpdesk/helpdesk/doctype/hd_time_entry/test_hd_time_entry.py`
