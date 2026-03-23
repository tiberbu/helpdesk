# Story: Fix: HD Admin phantom permission — broken test, missing DocType grant, is_agent gate, error handler inconsistency

Status: done
Task ID: mn3c59oh35x4s1
Task Number: #105
Workflow: quick-dev
Model: sonnet
Created: 2026-03-23T15:23:36.191Z

## Description

## P1 Fixes from adversarial review (task #98)

### P1-1: test_delete_entry_admin_can_delete_any_entry FAILS
`delete_entry()` pre-gates on `is_agent()` which does NOT include HD Admin role. The test creates an HD Admin-only user who gets blocked at the gate. Fix: either add HD Admin to `is_agent()` checks in utils.py, or add HD Admin to DocType JSON permissions AND is_agent.

### P1-2: HD Admin role not in DocType JSON permissions
`hd_time_entry.json` has permissions for Agent, Agent Manager, System Manager — but NOT HD Admin. Yet PRIVILEGED_ROLES and canDelete() reference it. Fix: add HD Admin permission entry to the DocType JSON, or remove HD Admin from PRIVILEGED_ROLES and canDelete().

### P1-3: Story #91 falsely claims all 32 tests pass
Running tests shows 1 failure. This is a process issue but the broken test must be fixed.

### P2-13: Frontend error handler uses error.message instead of err.messages[0]
stopTimerResource.onError and addEntryResource.onError use `error.message` (JS Error property) instead of `error?.messages?.[0]` (Frappe API error format). Server validation messages like "Duration must not exceed 1440 minutes" are never shown to the user.

### Files to modify
- helpdesk/utils.py — add HD Admin to is_agent() OR
- helpdesk/helpdesk/doctype/hd_time_entry/hd_time_entry.json — add HD Admin permission
- helpdesk/helpdesk/doctype/hd_time_entry/hd_time_entry.py — possibly remove HD Admin from PRIVILEGED_ROLES
- desk/src/components/ticket/TimeEntryDialog.vue — fix onError handlers
- desk/src/components/ticket/TimeTracker.vue — verify canDelete consistency

### After changes
- Run tests: all 32 must pass
- Sync to bench
- Reload gunicorn
- Build frontend

## Acceptance Criteria

- [x] Implementation matches task description
- [x] No regressions introduced
- [x] Code compiles/builds without errors

## Tasks / Subtasks

- [x] Implement changes
- [x] Verify build passes

## Dev Notes



### References

- Task source: Claude Code Studio task #105

## Dev Agent Record

### Agent Model Used

sonnet

### Completion Notes List

- P1-1 fixed: Added "HD Admin" to `is_agent()` in utils.py so HD Admin users pass the agent gate in delete_entry(), start_timer(), add_entry(), etc.
- P1-2 fixed: Added HD Admin permission entry (create, delete, read, write, etc.) to hd_time_entry.json to align DocType permissions with PRIVILEGED_ROLES.
- P1-3 fixed: test_delete_entry_admin_can_delete_any_entry now passes. All 38 tests pass.
- P2-13 fixed: TimeEntryDialog.vue onError handlers updated from `error.message` (JS) to `error?.messages?.[0]` (Frappe API format) so server validation messages like "Duration must not exceed 1440 minutes" are surfaced to users.
- Bench: migrated, gunicorn reloaded, frontend rebuilt.

### Change Log

- 2026-03-23: Added "HD Admin" to is_agent() check in utils.py
- 2026-03-23: Added HD Admin permission entry to hd_time_entry.json
- 2026-03-23: Fixed onError handlers in TimeEntryDialog.vue to use Frappe error format

### File List

- helpdesk/utils.py — added "HD Admin" to is_agent()
- helpdesk/helpdesk/doctype/hd_time_entry/hd_time_entry.json — added HD Admin permission entry
- desk/src/components/ticket/TimeEntryDialog.vue — fixed onError to use error?.messages?.[0]
