# Story: Fix: Story 3.5 Agent Chat Interface — agent send_message JWT bypass + queue visibility

Status: done
Task ID: mn3soi7c9kk1ck
Task Number: #233
Workflow: quick-dev
Model: sonnet
Created: 2026-03-23T23:06:14.954Z

## Description

## Fix Task (from QA report docs/qa-report-task-34.md)

### SCOPE LOCK
You MUST only modify the files listed below. Any change outside this scope = failure.

### Issues to fix

#### Issue 1 (P0): Agent cannot send messages — send_message always validates JWT
- File: `helpdesk/api/chat.py`
- Line: 142 (inside `send_message` function)
- Current: `validate_chat_token(token, session_id)` is called unconditionally
- Expected: If the caller is an authenticated agent (`_is_agent()` returns True), skip JWT validation and use `frappe.session.user` as sender_email with `sender_type="agent"`
- Before:
```python
    _check_chat_enabled()

    # Authenticate customer
    validate_chat_token(token, session_id)

    session_doc = frappe.get_doc("HD Chat Session", session_id)
```
- After:
```python
    _check_chat_enabled()

    is_agent_sender = _is_agent()
    if not is_agent_sender:
        # Authenticate customer via JWT
        validate_chat_token(token, session_id)

    session_doc = frappe.get_doc("HD Chat Session", session_id)
```
- Also update sender_type/sender_email logic (around line 151-157):
- Before:
```python
    msg = frappe.get_doc(
        {
            "doctype": "HD Chat Message",
            "session": session_id,
            "sender_type": "customer",
            "sender_email": session_doc.customer_email,
```
- After:
```python
    msg = frappe.get_doc(
        {
            "doctype": "HD Chat Message",
            "session": session_id,
            "sender_type": "agent" if is_agent_sender else "customer",
            "sender_email": frappe.session.user if is_agent_sender else session_doc.customer_email,
```
- And update the realtime event sender_type (around line 175):
- Before: `"sender_type": "customer",`
- After: `"sender_type": "agent" if is_agent_sender else "customer",`
- Verify: `cd /home/ubuntu/frappe-bench && bench --site helpdesk.localhost run-tests --app helpdesk --module helpdesk.tests.test_agent_chat_interface`

#### Issue 2 (P1): Chat queue 

## Acceptance Criteria

- [x] Implementation matches task description
- [x] No regressions introduced
- [x] Code compiles/builds without errors

## Tasks / Subtasks

- [x] Implement changes
- [x] Verify build passes

## Dev Notes



### References

- Task source: Claude Code Studio task #233

## Dev Agent Record

### Agent Model Used

sonnet

### Completion Notes List

- Fixed Issue 1 (P0): `send_message` now checks `_is_agent()` before calling `validate_chat_token`. Agents bypass JWT, use `frappe.session.user` as `sender_email` and `"agent"` as `sender_type`. Realtime event `sender_type` also updated.
- Fixed Issue 2 (P1): `get_agent_sessions` now returns agent's own active sessions PLUS all unassigned waiting sessions (the queue), enabling agents to see and accept new chats on page load without relying solely on realtime events.
- Added `TestAgentSendMessage` test class (2 new tests) and 2 new tests to `TestGetAgentSessions`. All 20 tests pass.

### Change Log

- 2026-03-23: `helpdesk/api/chat.py` — Issue 1: agent JWT bypass in `send_message` (3 locations); Issue 2: `get_agent_sessions` restructured to include unassigned waiting sessions.
- 2026-03-23: `helpdesk/tests/test_agent_chat_interface.py` — Added `TestAgentSendMessage` class + 2 new queue-visibility tests.

### File List

- `helpdesk/api/chat.py` (modified)
- `helpdesk/tests/test_agent_chat_interface.py` (modified)
