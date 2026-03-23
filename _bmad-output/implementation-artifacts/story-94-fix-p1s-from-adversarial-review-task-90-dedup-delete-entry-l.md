# Story: Fix: P1s from adversarial review task-90 — dedup delete_entry logic, auto-close crash guard, frozenset PRIVILEGED_ROLES, bench sync

Status: done
Task ID: mn3bw03oesh6ec
Task Number: #94
Workflow: quick-dev
Model: sonnet
Created: 2026-03-23T15:16:26.867Z

## Description

## P1 Fixes from Adversarial Review (docs/qa-report-task-87.md)

### P1 #1: delete_entry() still duplicates permission logic
`delete_entry()` in `time_tracking.py` builds its own `user_roles`/`is_privileged` check AND calls `_check_delete_permission()` which does the same thing. Fix: remove the inline privilege check from `delete_entry()`, keep only the `is_agent()` pre-gate and delegate everything else to `_check_delete_permission()`.

### P1 #7: close_tickets_after_n_days() crashes entire cron on single ticket with incomplete checklist
The auto-close loop has no try/except. A single ticket with incomplete mandatory checklist items raises ValidationError, crashing the entire cron job and preventing all subsequent tickets from being auto-closed. Fix: wrap the per-ticket save in try/except with logging.

### P2 #12: PRIVILEGED_ROLES is a mutable set
Change from `set` to `frozenset` to prevent accidental mutation.

### P2 #3: Bench frontend not synced
Sync TimeTracker.vue to bench and rebuild frontend.

### Files to modify
- `helpdesk/api/time_tracking.py` — remove duplicate privilege check from delete_entry
- `helpdesk/helpdesk/doctype/hd_time_entry/hd_time_entry.py` — frozenset
- `helpdesk/helpdesk/doctype/hd_ticket/hd_ticket.py` — try/except in auto-close
- `desk/src/components/ticket/TimeTracker.vue` — sync to bench

## Acceptance Criteria

- [x] Implementation matches task description
- [x] No regressions introduced
- [x] Code compiles/builds without errors

## Tasks / Subtasks

- [x] Implement changes
- [x] Verify build passes

## Dev Notes



### References

- Task source: Claude Code Studio task #94

## Dev Agent Record

### Agent Model Used

sonnet

### Completion Notes List

- P1 #1: Removed inline `is_privileged`/`PRIVILEGED_ROLES` check from `delete_entry()` in `time_tracking.py`. Now only `is_agent()` pre-gates the function; all ownership/role logic is delegated entirely to `_check_delete_permission()`. Also removed now-unused `PRIVILEGED_ROLES` import.
- P1 #7: Wrapped per-ticket `doc.save()` in `close_tickets_after_n_days()` with `try/except Exception`. Failed tickets are logged via `frappe.log_error` and rolled back; the loop continues with remaining tickets.
- P2 #12: Changed `PRIVILEGED_ROLES` from `set` to `frozenset` in `hd_time_entry.py`.
- P2 #3: Verified `TimeTracker.vue` is identical between dev and bench (diff clean). Bench built assets (15:16) are newer than source (15:12) — no rebuild required.
- All Python files synced to bench; gunicorn reloaded.

### Change Log

- `helpdesk/api/time_tracking.py`: Removed `PRIVILEGED_ROLES` from import; simplified `delete_entry()` to only `is_agent()` pre-gate + `_check_delete_permission()`.
- `helpdesk/helpdesk/doctype/hd_time_entry/hd_time_entry.py`: `PRIVILEGED_ROLES` changed from `set` to `frozenset`.
- `helpdesk/helpdesk/doctype/hd_ticket/hd_ticket.py`: Auto-close loop wrapped in `try/except` with `frappe.log_error` + `frappe.db.rollback()`.

### File List

- `helpdesk/api/time_tracking.py` (modified)
- `helpdesk/helpdesk/doctype/hd_time_entry/hd_time_entry.py` (modified)
- `helpdesk/helpdesk/doctype/hd_ticket/hd_ticket.py` (modified)
