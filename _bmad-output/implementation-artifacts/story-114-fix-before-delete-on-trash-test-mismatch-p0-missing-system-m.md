# Story: Fix: before_delete→on_trash test mismatch (P0) + missing System Manager/stop_timer tests (P1)

Status: in-progress
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

- [ ] Add `test_delete_entry_system_manager_can_delete_any_entry` — creates a bare System Manager user (no Agent/HD Admin role) and verifies they can delete another agent's entry via `delete_entry()`.
- [ ] Add `test_stop_timer_rejects_non_numeric_duration` — mirrors the existing `test_add_entry_rejects_non_numeric_duration` but for `stop_timer()`.

## Tasks / Subtasks

- [ ] Add `test_delete_entry_system_manager_can_delete_any_entry` — creates a bare System Manager user (no Agent/HD Admin role) and verifies they can delete another agent's entry via `delete_entry()`.
- [ ] Add `test_stop_timer_rejects_non_numeric_duration` — mirrors the existing `test_add_entry_rejects_non_numeric_duration` but for `stop_timer()`.

## Dev Notes



### References

- Task source: Claude Code Studio task #114

## Dev Agent Record

### Agent Model Used

sonnet

### Completion Notes List

_(Updated by agent on completion)_

### Change Log

_(Updated by agent during implementation)_

### File List

_(Updated by agent — list all files created or modified)_
