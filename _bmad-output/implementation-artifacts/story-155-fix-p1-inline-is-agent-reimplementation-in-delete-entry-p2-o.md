# Story: Fix: P1 inline is_agent() reimplementation in delete_entry + P2 on_trash missing pre-gate + P2 SM create/write inconsistency

Status: in-progress
Task ID: mn3e4hzar67uwy
Task Number: #155
Workflow: quick-dev
Model: sonnet
Created: 2026-03-23T16:18:59.816Z

## Description

## QA Findings from task-149 adversarial review (docs/qa-report-task-149.md)

### P1: delete_entry() re-implements is_agent() inline
- `delete_entry()` in `time_tracking.py` has a hand-rolled `is_agent()` check instead of calling the canonical `is_agent()` from `utils.py`
- The hardcoded role set {"HD Admin", "Agent Manager", "Agent"} appears in TWO places now
- Fix: refactor `is_agent()` to accept optional `user_roles` param, or extract `AGENT_ROLES` constant shared by both

### P2: on_trash() has no pre-gate
- `_check_delete_permission` docstring says callers must enforce pre-gate, but `on_trash()` delegates directly without one
- A bare SM who is also `entry.agent` would pass the ownership check silently
- Fix: add is_agent check in on_trash or in _check_delete_permission itself

### P2: SM still has create:1/write:1 in DocType JSON
- Contradicts stated policy that bare SM users are not agents
- Consider whether SM should have any permissions on HD Time Entry at all

### P2: No test for Administrator path in _check_delete_permission
- Add test_check_delete_permission_administrator_always_allowed

### P2: Hardcoded role sets should be constants
- Extract AGENT_ROLES constant to utils.py, used by is_agent() and delete_entry()

### Files to modify
- helpdesk/utils.py (add AGENT_ROLES constant, refactor is_agent)
- helpdesk/api/time_tracking.py (use is_agent or AGENT_ROLES constant)
- helpdesk/helpdesk/doctype/hd_time_entry/hd_time_entry.py (add pre-gate to on_trash or _check_delete_permission)
- helpdesk/helpdesk/doctype/hd_time_entry/test_hd_time_entry.py (add Administrator test, dual-role SM+Agent test)

## Acceptance Criteria

- [ ] Implementation matches task description
- [ ] No regressions introduced
- [ ] Code compiles/builds without errors

## Tasks / Subtasks

- [ ] Implement changes
- [ ] Verify build passes

## Dev Notes



### References

- Task source: Claude Code Studio task #155

## Dev Agent Record

### Agent Model Used

sonnet

### Completion Notes List

_(Updated by agent on completion)_

### Change Log

_(Updated by agent during implementation)_

### File List

_(Updated by agent — list all files created or modified)_
