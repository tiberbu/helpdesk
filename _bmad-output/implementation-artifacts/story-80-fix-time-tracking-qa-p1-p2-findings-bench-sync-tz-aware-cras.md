# Story: Fix: Time Tracking QA P1/P2 findings (bench sync, tz-aware crash, toast API, is_agent gaps)

Status: in-progress
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

- [ ] **Sync frontend files to bench** — TimeEntryDialog.vue and TicketDetailsTab.vue have changes in dev but NOT in bench. Run rsync to sync both files.
- [ ] **Fix tz-aware started_at MySQL crash** — In stop_timer(), normalize started_at to naive datetime string before passing to frappe.get_doc(). Use started_at_dt.replace(tzinfo=None) for storage, not just comparison. Test test_stop_timer_handles_tz_aware_started_at currently ERRORS.
- [ ] **Fix before_delete hook / test** — test_before_delete_hook_blocks_other_agent_from_direct_delete FAILS. Investigate why is_hd_admin returns truthy for agent3. May need to add is_agent() check to hook.
- [ ] **Fix toast API syntax in TimeEntryDialog.vue** — Change toast({title, text, type}) to toast.error(msg) to match codebase convention.
- [ ] **Add is_agent() gate to stop_timer() and add_entry()** — These endpoints lack is_agent() unlike start_timer/delete_entry/get_summary.
- [ ] **Add upper bound for duration_minutes** — Currently accepts 999999999 minutes. Add max 1440 (24h) or similar.

## Tasks / Subtasks

- [ ] **Sync frontend files to bench** — TimeEntryDialog.vue and TicketDetailsTab.vue have changes in dev but NOT in bench. Run rsync to sync both files.
- [ ] **Fix tz-aware started_at MySQL crash** — In stop_timer(), normalize started_at to naive datetime string before passing to frappe.get_doc(). Use started_at_dt.replace(tzinfo=None) for storage, not just comparison. Test test_stop_timer_handles_tz_aware_started_at currently ERRORS.
- [ ] **Fix before_delete hook / test** — test_before_delete_hook_blocks_other_agent_from_direct_delete FAILS. Investigate why is_hd_admin returns truthy for agent3. May need to add is_agent() check to hook.
- [ ] **Fix toast API syntax in TimeEntryDialog.vue** — Change toast({title, text, type}) to toast.error(msg) to match codebase convention.
- [ ] **Add is_agent() gate to stop_timer() and add_entry()** — These endpoints lack is_agent() unlike start_timer/delete_entry/get_summary.
- [ ] **Add upper bound for duration_minutes** — Currently accepts 999999999 minutes. Add max 1440 (24h) or similar.

## Dev Notes



### References

- Task source: Claude Code Studio task #80

## Dev Agent Record

### Agent Model Used

sonnet

### Completion Notes List

_(Updated by agent on completion)_

### Change Log

_(Updated by agent during implementation)_

### File List

_(Updated by agent — list all files created or modified)_
