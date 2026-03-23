# Story: Fix: P1s from adversarial review task-90 — dedup delete_entry logic, auto-close crash guard, frozenset PRIVILEGED_ROLES, bench sync

Status: in-progress
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

- [ ] Implementation matches task description
- [ ] No regressions introduced
- [ ] Code compiles/builds without errors

## Tasks / Subtasks

- [ ] Implement changes
- [ ] Verify build passes

## Dev Notes



### References

- Task source: Claude Code Studio task #94

## Dev Agent Record

### Agent Model Used

sonnet

### Completion Notes List

_(Updated by agent on completion)_

### Change Log

_(Updated by agent during implementation)_

### File List

_(Updated by agent — list all files created or modified)_
