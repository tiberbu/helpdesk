# Story: Fix: Time Tracking adversarial review P1/P2 findings (canDelete Agent Manager, __ import, frontend validation)

Status: in-progress
Task ID: mn3bneu2wt63yw
Task Number: #91
Workflow: quick-dev
Model: sonnet
Created: 2026-03-23T15:09:31.869Z

## Description

## Fix P1/P2 findings from adversarial review (task #88)

### P1 — canDelete() missing Agent Manager role
`TimeTracker.vue` `canDelete()` checks HD Admin and System Manager but NOT Agent Manager. Backend includes Agent Manager in privileged_roles. Add Agent Manager to the frontend check.

### P2 — Missing __ import in script setup
Both `TimeEntryDialog.vue` and `TimeTracker.vue` use `__()` in `<script setup>` without importing from `@/translation`. Add explicit import.

### P2 — No frontend upper-bound validation
`TimeEntryDialog.vue` has no max on hours input. Add client-side validation matching backend MAX_DURATION_MINUTES=1440.

### P2 — Duplicated permission logic in delete_entry
`delete_entry()` in `time_tracking.py` duplicates the privileged_roles check that `_check_delete_permission()` already handles. Remove the duplication.

### P2 — MAX_DURATION not checked at API layer
`stop_timer()` and `add_entry()` check min but not max duration. Add the check for consistency with description length validation pattern.

### Files to modify
- `desk/src/components/ticket/TimeTracker.vue`
- `desk/src/components/ticket/TimeEntryDialog.vue`
- `helpdesk/api/time_tracking.py`

### After changes
- Sync all modified files to bench
- Run tests: `cd /home/ubuntu/frappe-bench && bench --site helpdesk.localhost run-tests --app helpdesk --module helpdesk.helpdesk.doctype.hd_time_entry.test_hd_time_entry`
- Reload gunicorn

## Acceptance Criteria

- [ ] Implementation matches task description
- [ ] No regressions introduced
- [ ] Code compiles/builds without errors

## Tasks / Subtasks

- [ ] Implement changes
- [ ] Verify build passes

## Dev Notes



### References

- Task source: Claude Code Studio task #91

## Dev Agent Record

### Agent Model Used

sonnet

### Completion Notes List

_(Updated by agent on completion)_

### Change Log

_(Updated by agent during implementation)_

### File List

_(Updated by agent — list all files created or modified)_
