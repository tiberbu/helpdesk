# Story: Fix: delete_entry reimplements is_agent inline - consolidate permission logic

Status: done
Task ID: mn3dmb3p9s2suj
Task Number: #142
Workflow: quick-dev
Model: sonnet
Created: 2026-03-23T16:04:56.014Z

## Description

P1 from adversarial review docs/qa-report-task-136.md Finding 1. delete_entry in time_tracking.py reimplements is_agent logic inline instead of calling is_agent. This creates wider permission surface than other endpoints, DRY violation, and double frappe.get_roles call. Fix: simplify delete_entry pre-gate to use is_agent, sync to bench.

## Acceptance Criteria

- [x] Implementation matches task description
- [x] No regressions introduced
- [x] Code compiles/builds without errors

## Tasks / Subtasks

- [x] Implement changes
- [x] Verify build passes

## Dev Notes



### References

- Task source: Claude Code Studio task #142

## Dev Agent Record

### Agent Model Used

sonnet

### Completion Notes List

- Replaced inline `user_roles = frappe.get_roles()` + `PRIVILEGED_ROLES` intersection check in `delete_entry` pre-gate with a single `is_agent()` call, matching all other endpoints in the file.
- Removed `PRIVILEGED_ROLES` from the `time_tracking.py` import — it is no longer used there.
- Updated stale comments/docstring in `delete_entry` that still referenced System Manager / PRIVILEGED_ROLES.
- Updated `test_delete_entry_system_manager_can_delete_any_entry` → `test_delete_entry_system_manager_blocked_at_pre_gate` to assert the correct behavior: a bare System Manager user (no Agent/HD Admin role) is now blocked by the `is_agent()` pre-gate. The old test was asserting the unintended wider permission surface.
- All 69 tests pass. Synced both files to bench.

### Change Log

- `helpdesk/api/time_tracking.py`: removed `PRIVILEGED_ROLES` import; replaced inline role check with `is_agent()` in `delete_entry`; updated docstring and inline comments.
- `helpdesk/helpdesk/doctype/hd_time_entry/test_hd_time_entry.py`: renamed and rewrote `test_delete_entry_system_manager_can_delete_any_entry` to assert PermissionError for bare System Manager.

### File List

- `helpdesk/api/time_tracking.py` (modified)
- `helpdesk/helpdesk/doctype/hd_time_entry/test_hd_time_entry.py` (modified)
