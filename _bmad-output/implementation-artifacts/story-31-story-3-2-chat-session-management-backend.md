# Story: Story 3.2: Chat Session Management Backend

Status: review
Task ID: mn2gb2yp8l8mwp
Task Number: #31
Workflow: dev-story
Model: sonnet
Created: 2026-03-23T21:56:35.753Z

## Description

## Story 3.2: Chat Session Management Backend

As a developer, I want chat session lifecycle management, so that chat conversations are properly tracked and cleaned up.

### Acceptance Criteria

- HD Chat Session and HD Chat Message DocTypes exist
- Pre-chat form submission creates session with customer email, status (waiting/active/ended), started_at, agent (null until assigned), and returns JWT session token
- First customer message creates HD Ticket with source=Chat via channel normalizer
- Inactive sessions (configurable timeout, default 30min) automatically ended by background job

### Tasks
- Create HD Chat Session DocType
- Create HD Chat Message DocType (child of session)
- Implement helpdesk/api/chat.py with create_session, send_message, end_session, get_sessions, transfer_session
- Implement JWT token generation for chat authentication
- Implement session cleanup background job
- Add scheduler event in hooks.py for session cleanup
- Write unit tests for session lifecycle

## Acceptance Criteria

- [x] HD Chat Session and HD Chat Message DocTypes exist
- [x] Pre-chat form submission creates session with customer email, status (waiting/active/ended), started_at, agent (null until assigned), and returns JWT session token
- [x] First customer message creates HD Ticket with source=Chat via channel normalizer
- [x] Inactive sessions (configurable timeout, default 30min) automatically ended by background job

## Tasks / Subtasks

- [x] Create HD Chat Session DocType
- [x] Create HD Chat Message DocType (standalone DocType linked to session)
- [x] Implement helpdesk/api/chat.py with create_session, send_message, end_session, get_sessions, transfer_session
- [x] Implement JWT token generation for chat authentication
- [x] Implement session cleanup background job
- [x] Add scheduler event in hooks.py for session cleanup
- [x] Write unit tests for session lifecycle

## Dev Notes



### References

- Task source: Claude Code Studio task #31

## Dev Agent Record

### Agent Model Used

sonnet

### Completion Notes List

- Implemented HD Chat Session DocType (standalone, not child table) with session_id autoname, status select (waiting/active/ended), started_at auto-set, agent Link, ticket Link, inactivity_timeout_minutes (default 30), jwt_token_hash hidden field.
- Implemented HD Chat Message DocType (standalone, linked to session via Link field) for scalable per-session queries.
- Created `helpdesk/helpdesk/chat/` package with `jwt_helper.py` (PyJWT + Frappe encryption key for signing) and `session_cleanup.py` (cleans stale sessions, appends system message, publishes realtime event).
- Created `helpdesk/api/chat.py` with all 5 endpoints: create_session (allow_guest), send_message (JWT auth + content sanitize + first-message ticket creation via ChannelNormalizer), end_session (JWT or agent role), get_sessions (agent-only), transfer_session (agent-only).
- Added `*/5 * * * *` cron entry to `hooks.py` for session cleanup alongside existing SLA monitor.
- Created patches in `patches/v1_phase1/` and added to `patches.txt`.
- 29 unit tests covering all ACs: DocType existence, field structure, create_session, send_message (sanitize, first ticket, no-duplicate, invalid token, ended session), session cleanup (stale/recent/already-ended/return-count), JWT (valid/expired/tampered/session-mismatch), end_session idempotency, get_sessions permission.
- All 72 tests pass (29 new + 43 existing, no regressions).

### Change Log

- 2026-03-23: Story 3.2 implemented — HD Chat Session DocType, HD Chat Message DocType, chat API (create_session, send_message, end_session, get_sessions, transfer_session), JWT helper, session cleanup background job, hooks.py scheduler event, patches, 29 unit tests.

### File List

- `helpdesk/helpdesk/helpdesk/doctype/hd_chat_session/__init__.py` (new)
- `helpdesk/helpdesk/helpdesk/doctype/hd_chat_session/hd_chat_session.json` (new)
- `helpdesk/helpdesk/helpdesk/doctype/hd_chat_session/hd_chat_session.py` (new)
- `helpdesk/helpdesk/helpdesk/doctype/hd_chat_message/__init__.py` (new)
- `helpdesk/helpdesk/helpdesk/doctype/hd_chat_message/hd_chat_message.json` (new)
- `helpdesk/helpdesk/helpdesk/doctype/hd_chat_message/hd_chat_message.py` (new)
- `helpdesk/helpdesk/helpdesk/chat/__init__.py` (new)
- `helpdesk/helpdesk/helpdesk/chat/jwt_helper.py` (new)
- `helpdesk/helpdesk/helpdesk/chat/session_cleanup.py` (new)
- `helpdesk/helpdesk/helpdesk/chat/tests/__init__.py` (new)
- `helpdesk/helpdesk/helpdesk/chat/tests/test_chat_session.py` (new)
- `helpdesk/helpdesk/api/chat.py` (new)
- `helpdesk/helpdesk/hooks.py` (modified — added cleanup cron)
- `helpdesk/helpdesk/patches.txt` (modified — added 2 new patches)
- `helpdesk/helpdesk/patches/v1_phase1/create_hd_chat_session.py` (new)
- `helpdesk/helpdesk/patches/v1_phase1/create_hd_chat_message.py` (new)
