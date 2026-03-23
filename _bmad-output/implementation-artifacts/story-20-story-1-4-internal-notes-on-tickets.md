# Story: Story 1.4: Internal Notes on Tickets

Status: done
Task ID: mn2g9twet3iyeq
Task Number: #20
Workflow: dev-story
Model: sonnet
Created: 2026-03-23T11:54:18.071Z

## Description

## Story 1.4: Internal Notes on Tickets

As a support agent, I want to add private notes on a ticket visible only to other agents, so that I can collaborate internally without exposing information to customers.

### Acceptance Criteria

- Given an agent views a ticket, when they click Add Internal Note, then a visually distinct editor opens (amber-50 background, amber-400 left border, Internal Note badge, lock icon) with rich text and file attachments
- Given an internal note exists, when a customer views the ticket in portal, then the note is NOT visible and NOT included in customer emails
- Given an internal note exists, when ticket data is fetched via API without Agent role, then internal notes are excluded (server-side permission check)

### Tasks
- Add internal note communication type to HD Ticket
- Create InternalNote.vue component with distinct styling (amber-50 bg, amber-400 border, lock icon)
- Implement server-side permission check to exclude internal notes from customer APIs
- Ensure internal notes excluded from customer portal and email notifications
- Add rich text editor support with file attachments for notes
- Write unit tests for permission boundary (NFR-SE-01)
- Ensure keyboard shortcut for adding internal notes

## Acceptance Criteria

- [x] Given an agent views a ticket, when they click Add Internal Note, then a visually distinct editor opens (amber-50 background, amber-400 left border, Internal Note badge, lock icon) with rich text and file attachments
- [x] Given an internal note exists, when a customer views the ticket in portal, then the note is NOT visible and NOT included in customer emails
- [x] Given an internal note exists, when ticket data is fetched via API without Agent role, then internal notes are excluded (server-side permission check)

## Tasks / Subtasks

- [x] Add internal note communication type to HD Ticket
- [x] Create InternalNote.vue component with distinct styling (amber-50 bg, amber-400 border, lock icon)
- [x] Implement server-side permission check to exclude internal notes from customer APIs
- [x] Ensure internal notes excluded from customer portal and email notifications
- [x] Add rich text editor support with file attachments for notes
- [x] Write unit tests for permission boundary (NFR-SE-01)
- [x] Ensure keyboard shortcut for adding internal notes

## Dev Notes



### References

- Task source: Claude Code Studio task #20

## Dev Agent Record

### Agent Model Used

sonnet

### Completion Notes List

- All 7 tasks and 3 acceptance criteria fully implemented and verified.
- Backend: `is_internal` field already existed in `hd_ticket_comment.json`. Added `new_internal_note()` method to `hd_ticket.py`. Server-side filter in `get_comments()` in `api.py` excludes internal notes for non-agents (NFR-SE-01).
- Frontend: New `InternalNote.vue` (amber-50 bg, amber-400 left border, lock icon badge), `InternalNoteTextEditor.vue` (calls `new_internal_note`), `InternalNoteIcon.vue` (SVG lock icon).
- `CommunicationArea.vue`: Added "Internal Note" button, editor section, `toggleInternalNoteBox` wiring, keyboard shortcut `n`.
- `TicketActivityPanel.vue`: Added "Internal Notes" tab; `is_internal` comments mapped to `internal_note` activity type; internal notes excluded from general Activity tab.
- `TicketAgentActivities.vue`: Renders `InternalNote` component for `internal_note` type; amber lock icon in timeline; empty state with "Add Internal Note" button.
- `types.ts`: Added `internal_note` to `TicketTab` union; added `InternalNoteActivity` interface.
- 10 unit tests all passing (permission boundary, creation guards, flag integrity, API filtering).
- Database migration patch copied to bench and registered in `patches.txt`.

### Change Log

- 2026-03-23: Implemented Story 1.4 — Internal Notes on Tickets (all tasks complete, all tests passing)

### File List

**Created:**
- `desk/src/components/InternalNote.vue` — Display component with amber styling, lock icon badge, edit/delete support
- `desk/src/components/InternalNoteTextEditor.vue` — Rich text editor for creating internal notes (calls `new_internal_note`)
- `desk/src/components/icons/InternalNoteIcon.vue` — SVG lock icon for internal notes
- `helpdesk/helpdesk/doctype/hd_ticket/test_internal_notes.py` — 10 unit tests for permission boundary (NFR-SE-01)
- `helpdesk/patches/v1_phase1/add_is_internal_to_hd_ticket_comment.py` — (pre-existing) DB migration patch

**Modified:**
- `desk/src/types.ts` — Added `internal_note` to `TicketTab`; added `InternalNoteActivity` interface; added to `TicketActivity` union
- `desk/src/components/icons/index.ts` — Exported `InternalNoteIcon`
- `desk/src/components/CommunicationArea.vue` — Added Internal Note button, `InternalNoteTextEditor`, shortcut `n`, focus watcher, click-outside handler
- `desk/src/components/ticket-agent/TicketActivityPanel.vue` — Added "Internal Notes" tab; mapped `is_internal` comments to `internal_note` type; filtered from Activity tab
- `desk/src/components/ticket/TicketAgentActivities.vue` — Renders `InternalNote` component; added `InternalNoteIcon` in timeline; empty state button
- `desk/src/pages/ticket/modalStates.ts` — (pre-existing) Already had `showInternalNoteBox` / `toggleInternalNoteBox`
- `helpdesk/helpdesk/doctype/hd_ticket/hd_ticket.py` — Added `new_internal_note()` method; set `is_internal=False` explicitly in `new_comment()`
- `helpdesk/helpdesk/doctype/hd_ticket/api.py` — `get_comments()` now selects `is_internal`, filters internal notes for non-agents
- `helpdesk/helpdesk/doctype/hd_ticket_comment/hd_ticket_comment.json` — (pre-existing) Already had `is_internal` field
- `helpdesk/patches.txt` — Registered `add_is_internal_to_hd_ticket_comment` patch
