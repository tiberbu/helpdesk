# Story: Fix: Missing on_trash tests for System Manager/HD Admin + test naming inconsistency (P1/P2 from QA #118)

Status: done
Task ID: mn3cyy3lub60xr
Task Number: #126
Workflow: quick-dev
Model: sonnet
Created: 2026-03-23T15:46:42.040Z

## Description

## Fix P1/P2 findings from adversarial review (Task #118)

### P1-1: Missing on_trash test for System Manager
Add `test_on_trash_allows_system_manager_to_delete_any_entry` — mirrors `test_before_delete_hook_allows_agent_manager_to_delete_any_entry` but for System Manager role. Creates a bare System Manager user, calls `entry_doc.on_trash()` directly, and verifies no PermissionError is raised.

### P1-2: Missing on_trash test for HD Admin
Add `test_on_trash_allows_hd_admin_to_delete_any_entry` — same pattern but for HD Admin role.

### P2-1: Rename test methods from before_delete to on_trash
Rename these 3 test methods to match the actual hook name:
- `test_before_delete_hook_blocks_other_agent_from_direct_delete` -> `test_on_trash_blocks_other_agent_from_direct_delete`
- `test_before_delete_hook_allows_own_entry_direct_delete` -> `test_on_trash_allows_own_entry_direct_delete`
- `test_before_delete_hook_allows_agent_manager_to_delete_any_entry` -> `test_on_trash_allows_agent_manager_to_delete_any_entry`

### P2-2: Fix try/except anti-pattern in agent manager on_trash test
Remove the try/except block — just call `entry_doc.on_trash()` directly. If it raises, the test framework catches it automatically.

### Files to change
- `helpdesk/helpdesk/doctype/hd_time_entry/test_hd_time_entry.py`
- Copy to bench after changes

### Verification
- ALL tests must pass: `cd /home/ubuntu/frappe-bench && bench --site helpdesk.localhost run-tests --app helpdesk --module helpdesk.helpdesk.doctype.hd_time_entry.test_hd_time_entry`

### QA Report Reference
See `docs/qa-report-task-114.md` for full findings.

## Acceptance Criteria

- [x] Implementation matches task description
- [x] No regressions introduced
- [x] Code compiles/builds without errors

## Tasks / Subtasks

- [x] Implement changes
- [x] Verify build passes

## Dev Notes



### References

- Task source: Claude Code Studio task #126

## Dev Agent Record

### Agent Model Used

sonnet

### Completion Notes List

- All P1 and P2 findings from QA #118 addressed in one pass.
- Added 2 new on_trash tests: `test_on_trash_allows_system_manager_to_delete_any_entry` and `test_on_trash_allows_hd_admin_to_delete_any_entry`.
- Renamed 3 test methods from `before_delete` prefix to `on_trash` prefix to match the actual Frappe hook name.
- Removed try/except anti-pattern in agent manager on_trash test; framework handles unexpected PermissionError automatically.
- All 58 tests pass (58/58 OK).

### Change Log

- `test_before_delete_hook_blocks_other_agent_from_direct_delete` → `test_on_trash_blocks_other_agent_from_direct_delete`
- `test_before_delete_hook_allows_own_entry_direct_delete` → `test_on_trash_allows_own_entry_direct_delete`
- `test_before_delete_hook_allows_agent_manager_to_delete_any_entry` → `test_on_trash_allows_agent_manager_to_delete_any_entry` (+ removed try/except)
- Added `test_on_trash_allows_system_manager_to_delete_any_entry`
- Added `test_on_trash_allows_hd_admin_to_delete_any_entry`

### File List

- `helpdesk/helpdesk/doctype/hd_time_entry/test_hd_time_entry.py` (modified + copied to bench)
