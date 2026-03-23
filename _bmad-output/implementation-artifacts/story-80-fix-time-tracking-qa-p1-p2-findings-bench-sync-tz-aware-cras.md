# Story: Fix: Time Tracking QA P1/P2 findings (bench sync, tz-aware crash, toast API, is_agent gaps)

Status: done
Task ID: mn3b6738n0yeh6
Task Number: #80
Workflow: quick-dev
Model: sonnet
Created: 2026-03-23T14:56:16.841Z

## Description

## Fix P1 and P2 issues from QA report task #75 (docs/qa-report-task-72.md)

### P1 Fixes
1. **Sync frontend files to bench** — TimeEntryDialog.vue and TicketDetailsTab.vue have changes in dev but NOT in bench. Run rsync to sync both files.
2. **Fix tz-aware started_at MySQL crash** — In stop_timer(), normalize started_at to naive datetime string before passing to frappe.get_doc(). Use started_at_dt.replace(tzinfo=None) for storage, not just comparison. Test test_stop_timer_handles_tz_aware_started_at currently ERRORS.
3. **Fix before_delete hook / test** — test_before_delete_hook_blocks_other_agent_from_direct_delete FAILS. Investigate why is_hd_admin returns truthy for agent3. May need to add is_agent() check to hook.

### P2 Fixes
4. **Fix toast API syntax in TimeEntryDialog.vue** — Change toast({title, text, type}) to toast.error(msg) to match codebase convention.
5. **Add is_agent() gate to stop_timer() and add_entry()** — These endpoints lack is_agent() unlike start_timer/delete_entry/get_summary.
6. **Add upper bound for duration_minutes** — Currently accepts 999999999 minutes. Add max 1440 (24h) or similar.

### Files to modify
- helpdesk/api/time_tracking.py
- desk/src/components/ticket/TimeEntryDialog.vue
- helpdesk/helpdesk/doctype/hd_time_entry/hd_time_entry.py
- helpdesk/helpdesk/doctype/hd_time_entry/test_hd_time_entry.py
- Sync all to bench

### QA Report
See docs/qa-report-task-72.md for full findings with evidence.

## Acceptance Criteria

- [x] **Sync frontend files to bench** — TimeEntryDialog.vue synced to bench; TicketDetailsTab.vue already in sync.
- [x] **Fix tz-aware started_at MySQL crash** — Already fixed using convert_utc_to_system_timezone(); 32 tests pass including test_stop_timer_handles_tz_aware_started_at and test_stop_timer_ist_offset_not_rejected_as_future.
- [x] **Fix before_delete hook / test** — Already fixed using frappe.get_roles() + _check_delete_permission() shared helper; test_before_delete_hook_blocks_other_agent_from_direct_delete passes.
- [x] **Fix toast API syntax in TimeEntryDialog.vue** — Changed toast({title, text, type}) to toast.error(msg) in dev + synced to bench + rebuilt.
- [x] **Add is_agent() gate to stop_timer() and add_entry()** — Already present in both dev and bench time_tracking.py; test_customer_cannot_stop_timer passes.
- [x] **Add upper bound for duration_minutes** — MAX_DURATION_MINUTES=1440 enforced in HDTimeEntry.validate(); tests pass.

## Tasks / Subtasks

- [x] **Sync frontend files to bench** — TimeEntryDialog.vue synced to bench; TicketDetailsTab.vue already in sync.
- [x] **Fix tz-aware started_at MySQL crash** — Already fixed using convert_utc_to_system_timezone(); 32 tests pass including test_stop_timer_handles_tz_aware_started_at and test_stop_timer_ist_offset_not_rejected_as_future.
- [x] **Fix before_delete hook / test** — Already fixed using frappe.get_roles() + _check_delete_permission() shared helper; test_before_delete_hook_blocks_other_agent_from_direct_delete passes.
- [x] **Fix toast API syntax in TimeEntryDialog.vue** — Changed toast({title, text, type}) to toast.error(msg) in dev + synced to bench + rebuilt.
- [x] **Add is_agent() gate to stop_timer() and add_entry()** — Already present in both dev and bench time_tracking.py; test_customer_cannot_stop_timer passes.
- [x] **Add upper bound for duration_minutes** — MAX_DURATION_MINUTES=1440 enforced in HDTimeEntry.validate(); tests pass.

## Dev Notes



### References

- Task source: Claude Code Studio task #80

## Dev Agent Record

### Agent Model Used

sonnet

### Completion Notes List

- All 6 acceptance criteria already implemented in dev/bench Python before this task ran; Python code was already in sync between dev and bench.
- The only actual change required was fixing the toast API syntax in TimeEntryDialog.vue (dev had wrong `toast({title, text, type})`, bench had no toast at all).
- Fixed: `toast({...})` → `toast.error(msg)` in both stopTimerResource and addEntryResource onError handlers.
- Synced updated TimeEntryDialog.vue to bench, rebuilt frontend (yarn build), reloaded gunicorn.
- All 32 tests pass (stale pyc cache caused 3 tests to be skipped on first run; cleared cache to confirm all pass).

### Change Log

- `desk/src/components/ticket/TimeEntryDialog.vue`: Fixed toast API syntax from `toast({title, text, type: "error"})` to `toast.error(msg)` to match codebase convention.
- Bench frontend rebuilt and gunicorn reloaded.

### File List

- `desk/src/components/ticket/TimeEntryDialog.vue` (fixed toast syntax, synced to bench)
