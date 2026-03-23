# Story: Story 1.5: @Mention Notifications in Internal Notes

Status: review
Task ID: mn2g9tyj48o8aw
Task Number: #21
Workflow: dev-story
Model: sonnet
Created: 2026-03-23T12:20:45.577Z

## Description

## Story 1.5: @Mention Notifications in Internal Notes

As a support agent, I want to @mention other agents in internal notes, so that they are notified and can quickly find the relevant ticket.

### Acceptance Criteria

- Given an agent is typing an internal note, when they type @ followed by characters, then an autocomplete dropdown shows matching agent names
- Given an agent submits a note mentioning @Rajesh, when the note is saved, then Rajesh receives an in-app notification with link to the ticket and note content preview

### Tasks
- Implement @mention autocomplete in internal note editor
- Create notification handler for @mentions via frappe notification system
- Add in-app notification with ticket link and note preview
- Write unit tests for mention detection and notification delivery

## Acceptance Criteria

- [x] Given an agent is typing an internal note, when they type @ followed by characters, then an autocomplete dropdown shows matching agent names
- [x] Given an agent submits a note mentioning @Rajesh, when the note is saved, then Rajesh receives an in-app notification with link to the ticket and note content preview

## Tasks / Subtasks

- [x] Implement @mention autocomplete in internal note editor
- [x] Create notification handler for @mentions via frappe notification system
- [x] Add in-app notification with ticket link and note preview
- [x] Write unit tests for mention detection and notification delivery

## Dev Notes

### Implementation Summary

Most of the core infrastructure was already in place from Story 1.4:

1. **@mention autocomplete** — `InternalNoteTextEditor.vue` already passes `:mentions="dropdown"` from `useAgentStore`, which provides `{label: agent_name, value: email}` objects. The Tiptap editor renders autocomplete automatically.

2. **Notification handler** — `HDTicketComment` already inherits `HasMentions` mixin (`helpdesk/mixins/mentions.py`), which fires `notify_mentions()` on `after_insert` and `on_update` (with dedup for edits). This creates `HD Notification` docs with `notification_type="Mention"`.

3. **Real-time bell update** — Added `frappe.publish_realtime("helpdesk:new-notification", ...)` in `HDNotification.after_insert()` so the mentioned agent's bell badge updates without a page refresh.

4. **Frontend store update** — Added `$socket.on("helpdesk:new-notification", ...)` in `notification.ts` to trigger list reload on the real-time event.

### References

- Task source: Claude Code Studio task #21

## Dev Agent Record

### Agent Model Used

sonnet

### Completion Notes List

- Story 1.4 had already implemented `is_internal` field, `HasMentions` mixin integration, and the Tiptap `:mentions` prop — so the @mention autocomplete and notification creation were already functional.
- The only gap was the real-time notification bell update. Fixed by adding `frappe.publish_realtime("helpdesk:new-notification", ...)` in `HDNotification.after_insert()` and a corresponding socket listener in the frontend `notification.ts` store.
- All 12 unit tests pass (ran via `bench run-tests` against the deployed site).

### Change Log

- `helpdesk/helpdesk/doctype/hd_notification/hd_notification.py` — Added `after_insert()` method with `frappe.publish_realtime("helpdesk:new-notification", ...)` for real-time bell update + optional email via `skip_email_workflow` flag.
- `desk/src/stores/notification.ts` — Added `$socket.on("helpdesk:new-notification", ...)` listener to reload notification list on real-time event.
- `helpdesk/helpdesk/doctype/hd_ticket/test_mention_notifications.py` — New test file with 12 tests covering all ACs.

### File List

**Modified:**
- `helpdesk/helpdesk/doctype/hd_notification/hd_notification.py`
- `desk/src/stores/notification.ts`

**Created:**
- `helpdesk/helpdesk/doctype/hd_ticket/test_mention_notifications.py`
