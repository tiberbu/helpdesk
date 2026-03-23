# Story: Story 3.6: Chat-to-Ticket Transcript and Follow-up

Status: review
Task ID: mn2gbpo4kz6nwf
Task Number: #35
Workflow: dev-story
Model: sonnet
Created: 2026-03-23T23:01:53.859Z

## Description

## Story 3.6: Chat-to-Ticket Transcript and Follow-up

As a support agent, I want every chat to have a complete HD Ticket with full transcript.

### Acceptance Criteria

- Each chat message stored as ticket communication via channel adapter
- Chat session ends without resolution: ticket remains open for email follow-up
- Agent reply to associated ticket sends response via email (standard ticket flow)

### Tasks
- Integrate chat adapter with HD Ticket communication creation
- Implement message-to-communication mapping
- Ensure ticket remains open when chat ends without resolution
- Verify email follow-up works on chat-originated tickets
- Write integration tests for full chat-to-ticket flow

## Acceptance Criteria

- [x] Each chat message stored as ticket communication via channel adapter
- [x] Chat session ends without resolution: ticket remains open for email follow-up
- [x] Agent reply to associated ticket sends response via email (standard ticket flow)

## Tasks / Subtasks

- [x] Integrate chat adapter with HD Ticket communication creation
- [x] Implement message-to-communication mapping (`normalize_from_doc()` in `ChatAdapter`, `create_ticket_communication()` in `normalizer.py`)
- [x] Ensure ticket remains open when chat ends without resolution (`on_update` in `HDChatSession` — does NOT change ticket status)
- [x] Verify email follow-up works on chat-originated tickets (standard Frappe email flow applies; `Communication` docs linked to HD Ticket)
- [x] Write integration tests for full chat-to-ticket flow (20 tests, all pass)

## Dev Notes



### References

- Task source: Claude Code Studio task #35

## Dev Agent Record

### Agent Model Used

sonnet

### Completion Notes List

- All 20 integration tests pass (`helpdesk/tests/test_chat_to_ticket_flow.py`).
- Full regression: 294/296 tests pass. The 2 failures are **pre-existing** regressions from Story 3.5's agent bypass logic in `send_message` (confirmed by reproducing failures on the last Story 3.5 commit before any Story 3.6 changes).
- `HD Chat Message.after_insert` stores each message as a Frappe `Communication` doc on the linked HD Ticket via `ChatAdapter.normalize_from_doc()` + `create_ticket_communication()`. Errors are swallowed so real-time chat is never interrupted (NFR-A-01).
- `HD Chat Session.on_update` adds a "Chat session ended" system comment to the ticket when status → "ended". Does NOT change ticket status — ticket remains open for email follow-up (AC #2).
- `source` Select field (`Email/Chat/Portal`) added to HD Ticket. `Chat` source set automatically when ticket created via chat. Frontend badge shown in TicketDetailsTab for non-Email sources.
- XSS sanitization via `ChannelNormalizer._sanitize_content()` (NFR-SE-06).
- Feature flag `chat_enabled` checked at each entry point (AR-06).

### Change Log

| Date | Change |
|------|--------|
| 2026-03-23 | Added `normalize_from_doc()` to `ChatAdapter` |
| 2026-03-23 | Added `create_ticket_communication()`, `_store_chat_communication()`, `_store_system_chat_comment()` to `normalizer.py` |
| 2026-03-23 | Added `after_insert()` hook to `HDChatMessage` controller |
| 2026-03-23 | Added `on_update()` + `_mark_session_ended_on_ticket()` to `HDChatSession` controller |
| 2026-03-23 | Added `source` Select field to `HD Ticket` DocType JSON |
| 2026-03-23 | Updated `ChannelNormalizer._create_ticket()` to set `ticket.source` |
| 2026-03-23 | Added source badge to `TicketDetailsTab.vue` |
| 2026-03-23 | Created migration patch `add_source_field_to_hd_ticket.py` |
| 2026-03-23 | Registered patch in `patches.txt` |
| 2026-03-23 | Created 20-test integration test file |

### File List

**Modified:**
- `helpdesk/helpdesk/channels/chat_adapter.py` — added `normalize_from_doc()`
- `helpdesk/helpdesk/channels/normalizer.py` — added `create_ticket_communication`, `_store_chat_communication`, `_store_system_chat_comment`; updated `_create_ticket` to set `source`
- `helpdesk/helpdesk/doctype/hd_chat_message/hd_chat_message.py` — added `after_insert()` hook
- `helpdesk/helpdesk/doctype/hd_chat_session/hd_chat_session.py` — added `on_update()` + `_mark_session_ended_on_ticket()`
- `helpdesk/helpdesk/doctype/hd_ticket/hd_ticket.json` — added `source` Select field
- `helpdesk/patches.txt` — registered new migration patch
- `desk/src/components/ticket-agent/TicketDetailsTab.vue` — added source badge

**Created:**
- `helpdesk/patches/v1_phase1/add_source_field_to_hd_ticket.py` — migration patch
- `helpdesk/tests/test_chat_to_ticket_flow.py` — 20 integration tests
