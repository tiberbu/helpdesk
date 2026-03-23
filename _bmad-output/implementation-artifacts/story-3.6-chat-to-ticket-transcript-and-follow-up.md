# Story 3.6: Chat-to-Ticket Transcript and Follow-up

Status: ready-for-dev

<!-- Note: Validation is optional. Run validate-create-story for quality check before dev-story. -->

## Story

As a support agent,
I want every chat to have a complete HD Ticket with full transcript,
so that all interactions are tracked, reportable, and can be followed up via email.

## Acceptance Criteria

1. **Each chat message stored as a ticket communication via the channel adapter** — When a customer or agent sends a message in an active `HD Chat Session`, `chat_adapter.py` converts the `HD Chat Message` into a `ChannelMessage` (source="chat"), which `normalizer.py` persists as an HD Ticket Communication linked to the session's associated HD Ticket. Every message (customer and agent) is stored in real time so the transcript on the HD Ticket is always current. Server-side XSS sanitization is applied to message content before storage (FR-LC-03, NFR-SE-06).

2. **Chat session ends without resolution: ticket remains open for email follow-up** — When a chat session's `status` transitions to `"ended"` (whether by agent calling `end_session`, customer leaving, or the 30-minute inactivity timeout from Story 3.2), the associated HD Ticket status is NOT changed to Resolved or Closed. The ticket remains in its current open/in-progress state so the agent or system can follow up via email. A system communication is added to the HD Ticket timeline: `"Chat session ended. Follow up via email."` with `sender_type="system"` (FR-LC-03).

3. **Agent reply to associated ticket sends response via email (standard ticket flow)** — After a chat-originated ticket (source="Chat") is open for follow-up, when an agent adds a reply via the standard HD Ticket reply interface, Frappe's existing email notification pipeline handles delivery to the customer's email (the same email captured in the pre-chat form and stored in `HD Chat Session.customer_email` / `HD Ticket.raised_by`). No custom email logic is required for this story — the standard HD Ticket reply-to-email flow must work seamlessly for chat-originated tickets (FR-LC-03).

4. **Chat-originated tickets are identifiable by `source` field** — HD Tickets created from chat sessions have `source="Chat"` (set during session creation in Story 3.2). Agents can filter/sort by this field in the ticket list. The ticket detail view shows the source badge indicating "Chat" origin (FR-LC-03).

5. **Full transcript accessible on the HD Ticket** — The HD Ticket's communication thread contains all chat messages as individual communication entries in chronological order, each showing: sender name, sender type (customer/agent), message content, and timestamp. An agent viewing the ticket after the session ends can read the complete conversation without accessing the HD Chat Session directly (FR-LC-03).

6. **`store_chat_message_as_communication` hook called on every `HD Chat Message` save** — In `helpdesk/helpdesk/doctype/hd_chat_message/hd_chat_message.py`, the `after_insert` controller method calls `store_chat_message_as_communication(doc)` which: constructs a `ChannelMessage` from the `HD Chat Message` doc, then calls `normalizer.create_ticket_communication(channel_message)` to persist the communication. If the chat_message has no linked ticket (edge case), the function logs a warning and returns without error (NFR-A-01).

7. **`mark_session_ended_on_ticket` called when session status transitions to `"ended"`** — In `helpdesk/helpdesk/doctype/hd_chat_session/hd_chat_session.py`, the `on_update` controller method detects when `status` changes to `"ended"` and calls `mark_session_ended_on_ticket(doc)`. This function: verifies the ticket is not already closed; adds a system communication to the ticket; does NOT change ticket status; does NOT trigger email notifications for this system message (FR-LC-03, NFR-A-01).

8. **Integration test: full chat-to-ticket flow** — A backend integration test `helpdesk/tests/test_chat_to_ticket_flow.py` covers: create chat session → send customer message → assert HD Ticket communication created with correct content and sender → send agent message → assert second communication created → end session → assert ticket remains open and system communication added → agent adds ticket reply → assert email notification would be sent (mock `frappe.sendmail`). ≥80% line coverage on all new/modified backend code in this story (NFR-M-01).

## Tasks / Subtasks

- [ ] **Task 1: Implement `chat_adapter.py` — HD Chat Message to ChannelMessage conversion** (AC: #1, #5, #6)
  - [ ] In `helpdesk/helpdesk/channels/chat_adapter.py` (created in Story 3.1), implement (or complete if stubbed) `ChatAdapter.normalize(hd_chat_message_doc) -> ChannelMessage`:
    - Map `hd_chat_message_doc.sender` → `sender_email`; `hd_chat_message_doc.sender_name` → `sender_name`
    - Set `source="chat"`, `content=sanitize_html(hd_chat_message_doc.content)` (use `frappe.utils.sanitize_html` or equivalent), `content_type="text/html"`
    - Set `metadata={"chat_session_id": hd_chat_message_doc.session, "message_name": hd_chat_message_doc.name}`
    - Set `ticket_id` from `frappe.db.get_value("HD Chat Session", hd_chat_message_doc.session, "ticket")`
    - Set `is_internal=False` (chat messages are customer-facing communications)
    - Set `timestamp=hd_chat_message_doc.creation`
    - `subject` is auto-generated: `f"Chat: {hd_chat_message_doc.session}"` if no ticket subject available
  - [ ] Register `ChatAdapter` in `helpdesk/helpdesk/channels/registry.py` with key `"chat"` (if not already done in Story 3.1)
  - [ ] Ensure `normalize()` returns a fully-populated `ChannelMessage` dataclass instance

- [ ] **Task 2: Implement (or extend) `normalizer.py` — `create_ticket_communication`** (AC: #1, #5)
  - [ ] In `helpdesk/helpdesk/channels/normalizer.py`, implement `create_ticket_communication(channel_message: ChannelMessage) -> str`:
    - If `channel_message.ticket_id` is falsy: log `frappe.log_error("No ticket_id in ChannelMessage", "ChatNormalizerWarning")` and return `None`
    - Create an `HD Ticket Comment` (or use the existing communication DocType pattern from Story 3.1/3.2):
      ```python
      comm = frappe.get_doc({
          "doctype": "HD Ticket Comment",  # or "Communication" per existing pattern
          "reference_doctype": "HD Ticket",
          "reference_name": channel_message.ticket_id,
          "sender": channel_message.sender_email,
          "sender_full_name": channel_message.sender_name,
          "content": channel_message.content,
          "sent_or_received": "Received" if channel_message.sender_email != frappe.session.user else "Sent",
          "communication_type": "Chat",
          "creation": channel_message.timestamp,
      })
      comm.insert(ignore_permissions=True)
      frappe.db.commit()
      return comm.name
      ```
    - **Note:** Use the actual communication DocType pattern established by Stories 3.1/3.2. If `HD Ticket` uses `Communication` DocType linked via `reference_doctype`/`reference_name`, follow that pattern exactly.
  - [ ] If `normalizer.py` already has a `create_ticket_communication` implementation from Story 3.1, extend it to handle `communication_type="Chat"` distinctly from email communications

- [ ] **Task 3: Wire `HD Chat Message` `after_insert` to store communication** (AC: #1, #6)
  - [ ] In `helpdesk/helpdesk/doctype/hd_chat_message/hd_chat_message.py`, add `after_insert(self)` controller method:
    ```python
    def after_insert(self):
        from helpdesk.helpdesk.channels.chat_adapter import ChatAdapter
        from helpdesk.helpdesk.channels.normalizer import create_ticket_communication
        try:
            adapter = ChatAdapter()
            channel_message = adapter.normalize(self)
            if channel_message.ticket_id:
                create_ticket_communication(channel_message)
        except Exception:
            frappe.log_error(frappe.get_traceback(), "ChatMessageCommunicationError")
            # Swallow error: real-time chat must not fail due to communication storage issues
    ```
  - [ ] Ensure `hd_chat_message.py` exists (created in Story 3.2); add method if not already present
  - [ ] System messages (e.g., "Chat transferred to...") with `sender_type="system"` should also be stored, but marked with `communication_type="Chat System"` to distinguish from agent/customer messages
  - [ ] Verify that storing communication does NOT re-trigger any Socket.IO events (no recursion)

- [ ] **Task 4: Wire `HD Chat Session` `on_update` to mark ticket when session ends** (AC: #2, #7)
  - [ ] In `helpdesk/helpdesk/doctype/hd_chat_session/hd_chat_session.py`, add or extend `on_update(self)`:
    ```python
    def on_update(self):
        if self.has_value_changed("status") and self.status == "ended":
            self._mark_session_ended_on_ticket()

    def _mark_session_ended_on_ticket(self):
        if not self.ticket:
            return
        ticket = frappe.get_doc("HD Ticket", self.ticket)
        # Only act if ticket is not already closed/resolved
        if ticket.status in ("Resolved", "Closed"):
            return
        # Add system communication
        frappe.get_doc({
            "doctype": "HD Ticket Comment",  # or Communication — match existing pattern
            "reference_doctype": "HD Ticket",
            "reference_name": self.ticket,
            "content": "Chat session ended. Follow up via email.",
            "communication_type": "Chat System",
            "sender": "System",
            "sender_full_name": "System",
        }).insert(ignore_permissions=True)
        frappe.db.commit()
        # Do NOT change ticket.status — leave open for email follow-up
    ```
  - [ ] Ensure `has_value_changed()` is available on the DocType (standard Frappe method); if `HD Chat Session` uses `on_change` pattern differently, adapt accordingly

- [ ] **Task 5: Verify standard email follow-up works for chat-originated tickets** (AC: #3, #4)
  - [ ] Confirm `HD Ticket.raised_by` is set to `HD Chat Session.customer_email` during session creation (from Story 3.2); if not, add this assignment in Story 3.2's `create_session` API or `HD Chat Session.after_insert`
  - [ ] Confirm `HD Ticket.source` is set to `"Chat"` during session creation (from Story 3.2)
  - [ ] Test manually (or in integration test Task 8): agent opens chat-originated ticket → clicks "Reply" → sends reply → verify `frappe.sendmail` is called with correct recipient (`HD Ticket.raised_by`)
  - [ ] If source="Chat" causes any issues with the standard reply pipeline (e.g., source-based conditionals in existing code), fix those conditionals to include "Chat" as a valid email-reply source
  - [ ] No new API endpoints or Vue components are required for this task — existing ticket reply UI and backend already handle this

- [ ] **Task 6: Verify ticket list and detail view handle `source="Chat"` correctly** (AC: #4)
  - [ ] In the agent ticket list (`desk/src/pages/tickets/`), confirm the `source` filter/column is either already present or add `source` as a filterable field
  - [ ] In the ticket detail view (`desk/src/pages/ticket/`), confirm the source badge is rendered for `source="Chat"` — if a source badge component already exists for "Email" source, ensure "Chat" shows a distinct label (e.g., a chat-bubble icon or "Chat" badge)
  - [ ] This is primarily a verification task; only add UI changes if `source="Chat"` is not already handled

- [ ] **Task 7: `mark_session_ended_on_ticket` edge case handling** (AC: #2, #7)
  - [ ] Handle the case where `HD Chat Session.ticket` is null/empty (e.g., session created but no first message sent before timeout — ticket may not have been created per Story 3.2 logic)
  - [ ] Handle the case where `HD Ticket` does not exist (deleted or corrupted): catch `frappe.DoesNotExistError`, log warning, and return gracefully
  - [ ] Ensure idempotency: if `on_update` is called multiple times with `status="ended"`, do not insert duplicate system communications (check if one already exists before inserting)

- [ ] **Task 8: Integration tests for full chat-to-ticket flow** (AC: #8)
  - [ ] Create `helpdesk/tests/test_chat_to_ticket_flow.py`:
    ```python
    class TestChatToTicketFlow(unittest.TestCase):
        def setUp(self):
            # Create test HD Team, HD Agent, HD Ticket (simulating Story 3.2 session creation)
            ...

        def test_customer_message_creates_ticket_communication(self):
            # Arrange: HD Chat Session linked to HD Ticket; HD Chat Message (customer)
            # Act: Insert HD Chat Message (triggers after_insert)
            # Assert: HD Ticket Communication exists with correct sender, content, type="Chat"
            ...

        def test_agent_message_creates_ticket_communication(self):
            # Arrange: same session; HD Chat Message (agent sender)
            # Act: Insert HD Chat Message
            # Assert: Communication created, sent_or_received="Sent"
            ...

        def test_session_end_does_not_close_ticket(self):
            # Arrange: active HD Chat Session with linked ticket (status="Open")
            # Act: Set HD Chat Session.status = "ended", save
            # Assert: HD Ticket.status still "Open" (not Resolved/Closed)
            # Assert: System communication added: "Chat session ended. Follow up via email."
            ...

        def test_session_end_skips_already_closed_ticket(self):
            # Arrange: session linked to ticket with status="Resolved"
            # Act: End session
            # Assert: No additional system communication inserted
            ...

        def test_session_end_no_ticket_does_not_error(self):
            # Arrange: HD Chat Session with no ticket linked
            # Act: End session
            # Assert: No exception raised
            ...

        def test_no_duplicate_system_communication_on_repeated_update(self):
            # Arrange: End session once (system comm inserted)
            # Act: Save session again with status="ended"
            # Assert: Still only one system communication present
            ...

        def test_email_reply_on_chat_ticket(self):
            # Arrange: chat-originated HD Ticket with customer email set
            # Act: Call standard ticket reply API (simulate frappe.sendmail)
            # Assert: frappe.sendmail called with correct recipient
            ...
    ```
  - [ ] Run tests: `cd /home/ubuntu/bmad-project/helpdesk && python -m pytest helpdesk/tests/test_chat_to_ticket_flow.py -v`
  - [ ] Achieve ≥80% coverage on all modified/new backend code (NFR-M-01)

## Dev Notes

### Architecture Patterns

This story implements **FR-LC-03** (Chat-to-ticket conversion with full transcript, follow-up via email, SLA tracking). It bridges the chat infrastructure from Stories 3.1–3.5 with the standard HD Ticket communication pipeline.

**Key architectural constraints:**

- **Channel Abstraction Layer is the integration point** — All chat messages MUST flow through `ChatAdapter.normalize()` → `normalizer.create_ticket_communication()`. Do NOT create communications directly from the chat session controller without going through the channel normalizer. This maintains the abstraction that allows future channels (WhatsApp, SMS) to plug in without touching core ticket logic (ADR-07, AR-01).

- **`after_insert` not `validate` or `before_save`** — Wire the communication storage on `after_insert` of `HD Chat Message`, not on `validate`. This ensures the message doc has a name (primary key) before we reference it in metadata, and avoids partial-write scenarios.

- **Swallow errors in `after_insert` hook** — The real-time chat experience must not degrade if communication storage fails (e.g., DB lock, network issue). Always wrap the communication storage call in `try/except` and log to `frappe.log_error`. This implements NFR-A-01 (chat failure must not affect core ticketing).

- **Ticket status is NEVER changed by this story** — The `_mark_session_ended_on_ticket` function is READ-ONLY with respect to ticket status. It only inserts a system communication. Status changes are handled by agents or automation rules. Enforcing this keeps the story scope tight and avoids colliding with SLA or automation rule workflows.

- **No new API endpoints required** — This story is entirely event-driven (DocType controller hooks). The `end_session` API (Story 3.5, Task 5) already exists and sets `HD Chat Session.status = "ended"` — the `on_update` hook in this story reacts to that transition. No new `@frappe.whitelist()` methods are needed.

- **Communication DocType pattern** — The project may use either Frappe's built-in `Communication` DocType or a custom `HD Ticket Comment` DocType for ticket communications. Check the existing implementation from Story 3.1/3.2 and match it exactly. The story template uses `HD Ticket Comment` as a placeholder — replace with the actual DocType used.

- **`chat_enabled` feature flag** — The `after_insert` hook and `on_update` hook should check `frappe.db.get_single_value("HD Settings", "chat_enabled")` before executing. If chat is disabled, skip communication storage (AR-06).

### ChannelMessage Interface (from ADR-07)

```python
# helpdesk/helpdesk/channels/base.py
from dataclasses import dataclass, field
from datetime import datetime
from typing import Optional

@dataclass
class ChannelMessage:
    """Normalized message format for all channels."""
    source: str          # "email", "chat", "whatsapp", "portal"
    sender_email: str
    sender_name: str
    subject: str         # For email; auto-generated for chat: "Chat: {session_id}"
    content: str         # HTML content, sanitized server-side
    content_type: str    # "text/html" or "text/plain"
    attachments: list = field(default_factory=list)
    metadata: dict = field(default_factory=dict)
    ticket_id: Optional[str] = None
    is_internal: bool = False
    timestamp: Optional[datetime] = None
```

### `chat_adapter.py` Implementation Pattern

```python
# helpdesk/helpdesk/channels/chat_adapter.py
import frappe
from helpdesk.helpdesk.channels.base import BaseChannelAdapter, ChannelMessage


class ChatAdapter(BaseChannelAdapter):
    """Normalizes HD Chat Message documents into ChannelMessage format."""

    source = "chat"

    def normalize(self, hd_chat_message) -> ChannelMessage:
        """Convert an HD Chat Message doc to a ChannelMessage."""
        ticket_id = frappe.db.get_value(
            "HD Chat Session", hd_chat_message.session, "ticket"
        )
        content = frappe.utils.sanitize_html(hd_chat_message.content or "")

        return ChannelMessage(
            source=self.source,
            sender_email=hd_chat_message.sender or "",
            sender_name=hd_chat_message.sender_name or hd_chat_message.sender or "",
            subject=f"Chat: {hd_chat_message.session}",
            content=content,
            content_type="text/html",
            attachments=[],
            metadata={
                "chat_session_id": hd_chat_message.session,
                "message_name": hd_chat_message.name,
                "sender_type": hd_chat_message.sender_type,  # "customer" | "agent" | "system"
            },
            ticket_id=ticket_id,
            is_internal=False,
            timestamp=hd_chat_message.creation,
        )
```

### `hd_chat_message.py` After-Insert Hook Pattern

```python
# helpdesk/helpdesk/doctype/hd_chat_message/hd_chat_message.py
import frappe
from frappe import _


class HDChatMessage(Document):

    def after_insert(self):
        """Store chat message as HD Ticket communication via channel normalizer."""
        chat_enabled = frappe.db.get_single_value("HD Settings", "chat_enabled")
        if not chat_enabled:
            return
        try:
            from helpdesk.helpdesk.channels.chat_adapter import ChatAdapter
            from helpdesk.helpdesk.channels.normalizer import create_ticket_communication

            adapter = ChatAdapter()
            channel_message = adapter.normalize(self)
            create_ticket_communication(channel_message)
        except Exception:
            # Log but do not re-raise: real-time chat must not fail due to communication errors
            frappe.log_error(
                frappe.get_traceback(),
                "HDChatMessage: Failed to store communication for message {0}".format(self.name),
            )
```

### `hd_chat_session.py` On-Update Hook Pattern

```python
# helpdesk/helpdesk/doctype/hd_chat_session/hd_chat_session.py
import frappe
from frappe import _


class HDChatSession(Document):

    def on_update(self):
        """React to status transitions."""
        if self.has_value_changed("status") and self.status == "ended":
            self._mark_session_ended_on_ticket()

    def _mark_session_ended_on_ticket(self):
        """Add system communication to ticket; do NOT change ticket status."""
        if not self.ticket:
            return

        try:
            ticket = frappe.get_doc("HD Ticket", self.ticket)
        except frappe.DoesNotExistError:
            frappe.log_error(
                "HD Ticket {0} not found for chat session {1}".format(self.ticket, self.name),
                "ChatSessionEndedWarning",
            )
            return

        # Skip if ticket already closed
        if ticket.status in ("Resolved", "Closed"):
            return

        # Idempotency: skip if system comm already added for this session
        existing = frappe.db.exists(
            "HD Ticket Comment",  # replace with actual DocType if different
            {
                "reference_doctype": "HD Ticket",
                "reference_name": self.ticket,
                "communication_type": "Chat System",
                "content": ["like", "%Chat session ended%"],
            },
        )
        if existing:
            return

        frappe.get_doc({
            "doctype": "HD Ticket Comment",  # replace with actual DocType
            "reference_doctype": "HD Ticket",
            "reference_name": self.ticket,
            "content": _(
                "Chat session ended. Follow up via email."
            ),
            "communication_type": "Chat System",
            "sender": "System",
            "sender_full_name": "System",
        }).insert(ignore_permissions=True)
        frappe.db.commit()
```

### Project Structure Notes

**New files created by this story:**
```
helpdesk/
└── tests/
    └── test_chat_to_ticket_flow.py       # Integration tests (Task 8)
```

**Modified files:**
```
helpdesk/
└── helpdesk/
    ├── channels/
    │   ├── chat_adapter.py               # Complete/implement normalize() (Task 1)
    │   ├── normalizer.py                 # Implement/extend create_ticket_communication() (Task 2)
    │   └── registry.py                   # Ensure ChatAdapter registered (Task 1)
    ├── doctype/
    │   ├── hd_chat_message/
    │   │   └── hd_chat_message.py        # Add after_insert hook (Task 3)
    │   └── hd_chat_session/
    │       └── hd_chat_session.py        # Add on_update hook (Task 4)
    └── api/
        └── chat.py                       # No changes needed — end_session already implemented (Story 3.5)
```

**Files to verify (no changes expected):**
```
desk/src/pages/tickets/                   # Ticket list — verify source="Chat" filter works (Task 6)
desk/src/pages/ticket/                    # Ticket detail — verify source badge for "Chat" (Task 6)
```

**Naming conventions followed:**
- Python controller methods: `snake_case` (`after_insert`, `on_update`, `_mark_session_ended_on_ticket`)
- Communication type string: `"Chat"` for regular messages, `"Chat System"` for system events
- Error log titles: descriptive strings in `frappe.log_error(traceback, "TitleHere")` format
- Patches: not required in this story (no DocType schema changes; all changes are Python controller logic)

### Prerequisites and Dependencies

- **Story 3.1** (Channel Abstraction Layer) — `BaseChannelAdapter`, `ChannelMessage` dataclass, `normalizer.py` skeleton, `registry.py`, `chat_adapter.py` skeleton. This story COMPLETES the chat_adapter and normalizer implementations that Story 3.1 may have left as stubs.
- **Story 3.2** (Chat Session Management Backend) — `HD Chat Session` and `HD Chat Message` DocTypes must exist; `create_session` API sets `HD Chat Session.ticket` and `HD Chat Session.customer_email`; `hd_chat_session.py` controller exists.
- **Story 3.4** (Real-Time Chat Communication) — `HD Chat Message` insert flow already works (messages are saved to DB in Story 3.4); this story adds the `after_insert` side-effect.
- **Story 3.5** (Agent Chat Interface) — `end_session` API sets `HD Chat Session.status = "ended"`; the `on_update` hook in this story reacts to that transition.
- **`chat_enabled` feature flag** — In `HD Settings` (AR-06); checked in both hooks before execution.

### Security Notes

- **NFR-SE-06**: `frappe.utils.sanitize_html()` is applied to chat message content in `ChatAdapter.normalize()` before storage — XSS prevention for chat content entering the ticket communication thread.
- **NFR-SE-02**: `after_insert` uses `ignore_permissions=True` on communication insert because the inserting context may be a Socketio/background process without a full Frappe session. The permission check is effectively done at the message send layer (Stories 3.2/3.4 validate JWT token before accepting messages).
- **No customer data exposure risk**: System communications added by `_mark_session_ended_on_ticket` contain no customer PII — they are generic system messages. The full transcript in the communications thread is visible only to agents (subject to standard HD Ticket role permissions).

### References

- FR-LC-03: Chat-to-ticket conversion with full transcript, follow-up via email, SLA tracking [Source: `_bmad-output/planning-artifacts/epics.md#Functional Requirements`]
- ADR-07: Channel Abstraction Layer — `helpdesk/helpdesk/channels/` implementation [Source: `_bmad-output/planning-artifacts/architecture.md#ADR-07`]
- ADR-08: API Design — `helpdesk/api/chat.py` [Source: `_bmad-output/planning-artifacts/architecture.md#ADR-08`]
- NFR-A-01: Core ticketing unaffected by chat failures [Source: `_bmad-output/planning-artifacts/epics.md#Non-Functional Requirements`]
- NFR-M-01: Minimum 80% unit test coverage on all new backend code [Source: `_bmad-output/planning-artifacts/epics.md#Non-Functional Requirements`]
- NFR-SE-06: All chat messages sanitized server-side before storage [Source: `_bmad-output/planning-artifacts/epics.md#Non-Functional Requirements`]
- AR-01: Channel abstraction layer must be implemented before live chat [Source: `_bmad-output/planning-artifacts/epics.md#Additional Requirements`]
- AR-06: Feature flags in HD Settings [Source: `_bmad-output/planning-artifacts/epics.md#Additional Requirements`]
- Epic 3 Story 3.6 acceptance criteria [Source: `_bmad-output/planning-artifacts/epics.md#Story 3.6: Chat-to-Ticket Transcript and Follow-up`]
- Story 3.1 (prerequisite): Channel Abstraction Layer — `ChannelMessage`, `BaseChannelAdapter`, `normalizer.py` [Source: `_bmad-output/implementation-artifacts/story-3.1-channel-abstraction-layer.md`]
- Story 3.2 (prerequisite): Chat Session Management Backend — `HD Chat Session`, `HD Chat Message` DocTypes [Source: `_bmad-output/implementation-artifacts/story-3.2-chat-session-management-backend.md`]
- Story 3.5 (prerequisite): Agent Chat Interface — `end_session` API sets `status="ended"` [Source: `_bmad-output/implementation-artifacts/story-3.5-agent-chat-interface.md`]
- Architecture: Live Chat DocTypes — `HD Chat Session`, `HD Chat Message` [Source: `_bmad-output/planning-artifacts/architecture.md#DocType Inventory`]
- Architecture: Channel normalizer flow diagram [Source: `_bmad-output/planning-artifacts/architecture.md#ADR-07`]

## Dev Agent Record

### Agent Model Used

claude-sonnet-4-5

### Debug Log References

### Completion Notes List

### File List
