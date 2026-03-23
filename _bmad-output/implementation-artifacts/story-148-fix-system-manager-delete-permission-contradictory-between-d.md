# Story: Fix: System Manager delete permission contradictory between delete_entry API and REST DELETE

Status: done
Task ID: mn3dwquf2ogb4j
Task Number: #148
Workflow: quick-dev
Model: sonnet
Created: 2026-03-23T16:12:45.160Z

## Description

P1 from adversarial review docs/qa-report-task-142.md Finding 1.

System Manager permission is contradictory:
- delete_entry() blocks bare System Manager at is_agent() pre-gate (PermissionError)
- Direct REST DELETE /api/resource/HD Time Entry/{name} ALLOWS System Manager (DocType JSON has delete:1, on_trash uses PRIVILEGED_ROLES which includes System Manager)

This is a half-applied permission change. Either:
1. Fully remove System Manager from delete permission surface: remove from PRIVILEGED_ROLES, remove delete:1 from DocType JSON
2. OR add System Manager to is_agent() role set (probably wrong)

Option 1 is recommended. Also update _check_delete_permission docstring (Finding 11) and fix test_delete_entry_system_manager_blocked_at_pre_gate frappe.db.commit() test isolation issue (Finding 5).

## Acceptance Criteria

- [x] Fully remove System Manager from delete permission surface: remove from PRIVILEGED_ROLES, remove delete:1 from DocType JSON
- [x] Update _check_delete_permission docstring (Finding 11)
- [x] Fix test_delete_entry_system_manager_blocked_at_pre_gate frappe.db.commit() test isolation issue (Finding 5)

## Tasks / Subtasks

- [x] Remove "System Manager" from PRIVILEGED_ROLES in hd_time_entry.py
- [x] Remove delete:1 from System Manager in hd_time_entry.json
- [x] Update _check_delete_permission docstring to reflect removal
- [x] Invert test_on_trash_allows_system_manager_to_delete_any_entry → test_on_trash_blocks_system_manager_delete
- [x] Fix frappe.db.commit() isolation issue in test_delete_entry_system_manager_blocked_at_pre_gate
- [x] Sync all changes to bench copy
- [x] Run full test suite — 71 tests pass

## Dev Notes



### References

- Task source: Claude Code Studio task #148

## Dev Agent Record

### Agent Model Used

sonnet

### Completion Notes List

- Chose Option 1 (fully remove System Manager from delete surface) as recommended by task spec
- PRIVILEGED_ROLES now only contains HD Admin and Agent Manager — matches delete:1 grants in DocType JSON
- All 3 deletion paths now consistent: delete_entry() API, on_trash() hook, REST DELETE — all block bare System Manager
- test_on_trash_allows_system_manager_to_delete_any_entry renamed to test_on_trash_blocks_system_manager_delete with inverted assertion
- Removed frappe.db.commit() from test_delete_entry_system_manager_blocked_at_pre_gate finally block; tearDown rollback handles cleanup
- 71 tests pass (added 0 new tests — existing test renamed/updated; no net count change)

### Change Log

- `hd_time_entry.py`: Removed "System Manager" from PRIVILEGED_ROLES frozenset; expanded _check_delete_permission docstring to note System Manager exclusion is intentional and callers are responsible for pre-gate enforcement
- `hd_time_entry.json`: Removed `"delete": 1` from System Manager permission block
- `test_hd_time_entry.py`: Renamed `test_on_trash_allows_system_manager_to_delete_any_entry` → `test_on_trash_blocks_system_manager_delete`, inverted assertion to expect PermissionError; removed `frappe.db.commit()` from `test_delete_entry_system_manager_blocked_at_pre_gate` finally block
- All three files synced to bench copy at `/home/ubuntu/frappe-bench/apps/helpdesk/`

### File List

- `helpdesk/helpdesk/doctype/hd_time_entry/hd_time_entry.py` (modified)
- `helpdesk/helpdesk/doctype/hd_time_entry/hd_time_entry.json` (modified)
- `helpdesk/helpdesk/doctype/hd_time_entry/test_hd_time_entry.py` (modified)
- `/home/ubuntu/frappe-bench/apps/helpdesk/helpdesk/helpdesk/doctype/hd_time_entry/hd_time_entry.py` (synced)
- `/home/ubuntu/frappe-bench/apps/helpdesk/helpdesk/helpdesk/doctype/hd_time_entry/hd_time_entry.json` (synced)
- `/home/ubuntu/frappe-bench/apps/helpdesk/helpdesk/helpdesk/doctype/hd_time_entry/test_hd_time_entry.py` (synced)
