# Story: Fix: Story 2.3 SLA-Based Automation Triggers — dead notification channel, untested cron entry point, dead dedup reset

Status: in-progress
Task ID: mn3pce5hti9sqh
Task Number: #221
Workflow: quick-dev
Model: sonnet
Created: 2026-03-23T21:32:50.983Z

## Description

## Fix Task (from QA report docs/qa-report-task-28.md)

### SCOPE LOCK
You MUST only modify the files listed below. Any change outside this scope = failure.

### Issues to fix

#### Issue 1: P1 — Notification publishes to non-existent Socket.IO room with no frontend listener
- File: `helpdesk/helpdesk/automation/notifications.py` (line 55-58)
- Current: `frappe.publish_realtime(event="sla_warning", message=payload, room=f"agent:{agent_email}")`
- Problem: The `agent:{email}` room is never joined by any frontend code. Frappe uses `user:{email}` rooms. No frontend handler exists for `sla_warning` event.
- Fix approach (TWO parts):
  - **Part A (backend)**: Change room to standard Frappe pattern: `room=f"user:{agent_email}"` and also create an `HD Notification` record so the notification persists even if the agent is offline.
  - **Part B (frontend)**: Add a Socket.IO listener in `desk/src/stores/notification.ts` (or a new composable) that listens for `sla_warning` events and displays a toast notification using `frappe-ui`'s toast system.
- Files to modify:
  - `helpdesk/helpdesk/automation/notifications.py` (change room name, add HD Notification creation)
  - `desk/src/stores/notification.ts` or new `desk/src/composables/slaWarning.ts` (add socket listener + toast)
- Verify backend: `grep -n 'user:' helpdesk/helpdesk/automation/notifications.py` should show `user:{agent_email}`
- Verify frontend: `grep -rn 'sla_warning' desk/src/` should show at least one `.on("sla_warning"` handler

#### Issue 2: P1 — `check_sla_breaches` cron entry point has zero end-to-end test coverage
- File: `helpdesk/helpdesk/doctype/hd_service_level_agreement/test_sla_monitor_automation.py`
- Current: All tests call `_fire_warning`/`_fire_breached` directly; `check_sla_breaches` is imported but never invoked
- Expected: Add at least 2 integration tests that call `check_sla_breaches()` directly:
  - Test 1: Create a ticket with `resolution_by` 10 min from now, call `check_sla_breaches()`, verif

## Acceptance Criteria

- [ ] Implementation matches task description
- [ ] No regressions introduced
- [ ] Code compiles/builds without errors

## Tasks / Subtasks

- [ ] Implement changes
- [ ] Verify build passes

## Dev Notes



### References

- Task source: Claude Code Studio task #221

## Dev Agent Record

### Agent Model Used

sonnet

### Completion Notes List

_(Updated by agent on completion)_

### Change Log

_(Updated by agent during implementation)_

### File List

_(Updated by agent — list all files created or modified)_
