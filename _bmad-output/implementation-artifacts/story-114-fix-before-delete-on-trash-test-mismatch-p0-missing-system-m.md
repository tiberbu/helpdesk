# Story: Fix: before_delete→on_trash test mismatch (P0) + missing System Manager/stop_timer tests (P1)

Status: done
Task ID: mn3cll4uxc9ous
Task Number: #114
Workflow: quick-dev
Model: sonnet
Created: 2026-03-23T15:36:20.250Z

## Description

## Fix QA findings from adversarial review (Story #111)

### P0 — 2 tests actively failing
- `test_before_delete_hook_blocks_other_agent_from_direct_delete` (line 304) calls `entry_doc.before_delete()` but the model defines `on_trash()`. Fix: change to `entry_doc.on_trash()`.
- `test_before_delete_hook_allows_agent_manager_to_delete_any_entry` (line 440) same issue.
- After fix, all 37 tests must pass.

### P1 — Missing test coverage
1. Add `test_delete_entry_system_manager_can_delete_any_entry` — creates a bare System Manager user (no Agent/HD Admin role) and verifies they can delete another agent's entry via `delete_entry()`.
2. Add `test_stop_timer_rejects_non_numeric_duration` — mirrors the existing `test_add_entry_rejects_non_numeric_duration` but for `stop_timer()`.

### Files to change
- `helpdesk/helpdesk/doctype/hd_time_entry/test_hd_time_entry.py`
- Copy to bench: `cp helpdesk/helpdesk/doctype/hd_time_entry/test_hd_time_entry.py /home/ubuntu/frappe-bench/apps/helpdesk/helpdesk/helpdesk/doctype/hd_time_entry/test_hd_time_entry.py`

### Verification
- ALL tests must pass: `cd /home/ubuntu/frappe-bench && bench --site helpdesk.localhost run-tests --app helpdesk --module helpdesk.helpdesk.doctype.hd_time_entry.test_hd_time_entry`

## Acceptance Criteria

- [x] Add `test_delete_entry_system_manager_can_delete_any_entry` — creates a bare System Manager user (no Agent/HD Admin role) and verifies they can delete another agent's entry via `delete_entry()`.
- [x] Add `test_stop_timer_rejects_non_numeric_duration` — mirrors the existing `test_add_entry_rejects_non_numeric_duration` but for `stop_timer()`.

## Tasks / Subtasks

- [x] Add `test_delete_entry_system_manager_can_delete_any_entry` — creates a bare System Manager user (no Agent/HD Admin role) and verifies they can delete another agent's entry via `delete_entry()`.
- [x] Add `test_stop_timer_rejects_non_numeric_duration` — mirrors the existing `test_add_entry_rejects_non_numeric_duration` but for `stop_timer()`.

## Dev Notes



### References

- Task source: Claude Code Studio task #114

## Dev Agent Record

### Agent Model Used

sonnet

### Completion Notes List

- P0 fixes were already applied in the file (`on_trash()` at lines 341 and 477); no change needed.
- Added `_ensure_system_manager_user()` helper and `test_delete_entry_system_manager_can_delete_any_entry` test (P1 #1).
- Added `test_stop_timer_rejects_non_numeric_duration` test (P1 #2).
- All 41 tests pass (Ran 41 tests in 12.520s OK).

### Change Log

- Added `_ensure_system_manager_user`, `test_delete_entry_system_manager_can_delete_any_entry`, and `test_stop_timer_rejects_non_numeric_duration` to test file.
- Copied test file to bench: `frappe-bench/apps/helpdesk/...`.

### File List

- `helpdesk/helpdesk/doctype/hd_time_entry/test_hd_time_entry.py` (modified)
- `/home/ubuntu/frappe-bench/apps/helpdesk/helpdesk/helpdesk/doctype/hd_time_entry/test_hd_time_entry.py` (synced)
