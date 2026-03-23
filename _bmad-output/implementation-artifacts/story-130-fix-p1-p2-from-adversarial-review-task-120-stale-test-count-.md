# Story: Fix: P1/P2 from adversarial review task-120 — stale test count, misplaced TestIsAgentExplicitUser, missing HD Admin stop_timer/get_summary tests

Status: in-progress
Task ID: mn3d425p5cv7av
Task Number: #130
Workflow: quick-dev
Model: sonnet
Created: 2026-03-23T15:50:43.745Z

## Description

## Fix P1/P2 findings from adversarial review (task #120)

See `docs/qa-report-task-110.md` for full report (14 findings).

### P1 Fixes
1. **Finding #1**: Story-110 completion notes claim 39 tests but actual count is 56. Update story-110 completion notes to reflect correct test count.
2. **Finding #8**: `TestIsAgentExplicitUser` class (tests `is_agent()` from `helpdesk/utils.py`) is placed in `test_hd_time_entry.py`. Move it to a dedicated `helpdesk/tests/test_utils.py` file so tests are co-located with the module they test.

### P2 Fixes
3. **Finding #2**: Add `test_hd_admin_can_stop_timer` test — HD Admin calling `stop_timer()` has zero coverage.
4. **Finding #3**: Add `test_hd_admin_can_get_summary` test — HD Admin calling `get_summary()` has zero coverage.
5. **Finding #4**: `delete_entry()` calls `frappe.get_roles()` separately from `is_agent()`, causing double DB hit. Refactor to avoid redundant `get_roles()` call.
6. **Finding #5**: `_ensure_hd_admin_user()` helper should assert the created user does NOT have Agent/Agent Manager/System Manager roles.
7. **Finding #7**: Extract `_ensure_hd_admin_user()`, `_ensure_agent_manager_user()`, `_ensure_system_manager_user()` to `helpdesk/test_utils.py` as shared utilities.
8. **Finding #11**: `test_hd_admin_can_add_entry` should also assert the description field.

### Files to change
- `helpdesk/helpdesk/doctype/hd_time_entry/test_hd_time_entry.py`
- `helpdesk/tests/test_utils.py` (new)
- `helpdesk/test_utils.py` (add shared helpers)
- `helpdesk/api/time_tracking.py` (refactor delete_entry)
- Story-110 completion notes

## Acceptance Criteria

- [ ] **Finding #1**: Story-110 completion notes claim 39 tests but actual count is 56. Update story-110 completion notes to reflect correct test count.
- [ ] **Finding #8**: `TestIsAgentExplicitUser` class (tests `is_agent()` from `helpdesk/utils.py`) is placed in `test_hd_time_entry.py`. Move it to a dedicated `helpdesk/tests/test_utils.py` file so tests are co-located with the module they test.
- [ ] **Finding #2**: Add `test_hd_admin_can_stop_timer` test — HD Admin calling `stop_timer()` has zero coverage.
- [ ] **Finding #3**: Add `test_hd_admin_can_get_summary` test — HD Admin calling `get_summary()` has zero coverage.
- [ ] **Finding #4**: `delete_entry()` calls `frappe.get_roles()` separately from `is_agent()`, causing double DB hit. Refactor to avoid redundant `get_roles()` call.
- [ ] **Finding #5**: `_ensure_hd_admin_user()` helper should assert the created user does NOT have Agent/Agent Manager/System Manager roles.
- [ ] **Finding #7**: Extract `_ensure_hd_admin_user()`, `_ensure_agent_manager_user()`, `_ensure_system_manager_user()` to `helpdesk/test_utils.py` as shared utilities.
- [ ] **Finding #11**: `test_hd_admin_can_add_entry` should also assert the description field.

## Tasks / Subtasks

- [ ] **Finding #1**: Story-110 completion notes claim 39 tests but actual count is 56. Update story-110 completion notes to reflect correct test count.
- [ ] **Finding #8**: `TestIsAgentExplicitUser` class (tests `is_agent()` from `helpdesk/utils.py`) is placed in `test_hd_time_entry.py`. Move it to a dedicated `helpdesk/tests/test_utils.py` file so tests are co-located with the module they test.
- [ ] **Finding #2**: Add `test_hd_admin_can_stop_timer` test — HD Admin calling `stop_timer()` has zero coverage.
- [ ] **Finding #3**: Add `test_hd_admin_can_get_summary` test — HD Admin calling `get_summary()` has zero coverage.
- [ ] **Finding #4**: `delete_entry()` calls `frappe.get_roles()` separately from `is_agent()`, causing double DB hit. Refactor to avoid redundant `get_roles()` call.
- [ ] **Finding #5**: `_ensure_hd_admin_user()` helper should assert the created user does NOT have Agent/Agent Manager/System Manager roles.
- [ ] **Finding #7**: Extract `_ensure_hd_admin_user()`, `_ensure_agent_manager_user()`, `_ensure_system_manager_user()` to `helpdesk/test_utils.py` as shared utilities.
- [ ] **Finding #11**: `test_hd_admin_can_add_entry` should also assert the description field.

## Dev Notes



### References

- Task source: Claude Code Studio task #130

## Dev Agent Record

### Agent Model Used

sonnet

### Completion Notes List

_(Updated by agent on completion)_

### Change Log

_(Updated by agent during implementation)_

### File List

_(Updated by agent — list all files created or modified)_
