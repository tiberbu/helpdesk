# Story: Fix: P1 issues from QA task-71 — tz-aware crash, REST delete bypass, backend maxlength

Status: in-progress
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

- [ ] Implementation matches task description
- [ ] No regressions introduced
- [ ] Code compiles/builds without errors

## Tasks / Subtasks

- [ ] Implement changes
- [ ] Verify build passes

## Dev Notes



### References

- Task source: Claude Code Studio task #74

## Dev Agent Record

### Agent Model Used

sonnet

### Completion Notes List

_(Updated by agent on completion)_

### Change Log

_(Updated by agent during implementation)_

### File List

_(Updated by agent — list all files created or modified)_
