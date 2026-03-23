# Story: Fix: Story 3.3 Embeddable Chat Widget — wrong API paths + offline ticket Guest permission

Status: done
Task ID: mn3rdfo2dehyfe
Task Number: #229
Workflow: quick-dev
Model: sonnet
Created: 2026-03-23T22:29:38.836Z

## Description

## Fix Task (from QA report docs/qa-report-task-32.md)

### SCOPE LOCK
You MUST only modify the files listed below. Any change outside this scope = failure.

### Issues to fix

#### Issue 1: All widget API calls use wrong module path
- **Files**: `widget/src/Widget.vue`, `widget/src/components/BrandingHeader.vue`, `widget/src/components/PreChatForm.vue`, `widget/src/components/OfflineForm.vue`, `widget/src/components/ChatView.vue`
- **Problem**: All API URLs use `helpdesk.helpdesk.api.chat.*` but the correct Frappe module path is `helpdesk.api.chat.*`. The directory `helpdesk/helpdesk/api/` does not exist. Every widget API call fails with "No module named 'helpdesk.helpdesk.api'".
- **Current (6 occurrences)**:
  - `widget/src/Widget.vue:78`: `helpdesk.helpdesk.api.chat.get_availability`
  - `widget/src/components/BrandingHeader.vue:31`: `helpdesk.helpdesk.api.chat.get_widget_config`
  - `widget/src/components/PreChatForm.vue:48`: `helpdesk.helpdesk.api.chat.create_session`
  - `widget/src/components/OfflineForm.vue:50`: `helpdesk.helpdesk.api.chat.create_offline_ticket`
  - `widget/src/components/ChatView.vue:46`: `helpdesk.helpdesk.api.chat.get_messages`
  - `widget/src/components/ChatView.vue:112`: `helpdesk.helpdesk.api.chat.send_message`
- **Fix**: In each file, replace `helpdesk.helpdesk.api.chat.` with `helpdesk.api.chat.`
- **Verify**: `grep -r 'helpdesk.helpdesk.api.chat' widget/src/` should return NO results after fix

#### Issue 2: create_offline_ticket fails for Guest users — missing permission elevation
- **File**: `helpdesk/api/chat.py` (and bench copy at `/home/ubuntu/frappe-bench/apps/helpdesk/helpdesk/api/chat.py`)
- **Line**: ~438-452 (the try block inside `create_offline_ticket`)
- **Problem**: The channel normalizer and fallback ticket creation run as Guest user, causing PermissionError. Compare with `_create_ticket_for_session` (line ~511) which correctly does `frappe.set_user('Administrator')` before creating the ticket.
- **Current** (around l

## Acceptance Criteria

- [x] Implementation matches task description
- [x] No regressions introduced
- [x] Code compiles/builds without errors

## Tasks / Subtasks

- [x] Implement changes
- [x] Verify build passes

## Dev Notes



### References

- Task source: Claude Code Studio task #229

## Dev Agent Record

### Agent Model Used

sonnet

### Completion Notes List

- Fixed all 6 wrong API paths in widget frontend (replaced `helpdesk.helpdesk.api.chat.` → `helpdesk.api.chat.`)
- Added `frappe.set_user('Administrator')` elevation in `create_offline_ticket` with `finally` block to restore original user, matching the pattern in `_create_ticket_for_session`
- Synced backend fix to bench copy and reloaded Gunicorn

### Change Log

- `widget/src/Widget.vue`: Fixed get_availability API path
- `widget/src/components/BrandingHeader.vue`: Fixed get_widget_config API path
- `widget/src/components/PreChatForm.vue`: Fixed create_session API path
- `widget/src/components/OfflineForm.vue`: Fixed create_offline_ticket API path
- `widget/src/components/ChatView.vue`: Fixed get_messages and send_message API paths
- `helpdesk/api/chat.py`: Added Administrator elevation in `create_offline_ticket` with proper restore in `finally`

### File List

- `widget/src/Widget.vue`
- `widget/src/components/BrandingHeader.vue`
- `widget/src/components/PreChatForm.vue`
- `widget/src/components/OfflineForm.vue`
- `widget/src/components/ChatView.vue`
- `helpdesk/api/chat.py` (dev + bench copy)
