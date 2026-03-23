# Story 3.1: Channel Abstraction Layer

Status: ready-for-dev

<!-- Note: Validation is optional. Run validate-create-story for quality check before dev-story. -->

## Story

As a developer,
I want a channel abstraction layer that normalizes messages from all channels into a unified format,
so that adding new channels (WhatsApp, SMS) in Phase 2 requires minimal core changes.

## Acceptance Criteria

1. **Channel module exists** — The `helpdesk/helpdesk/channels/` Python package is created with `__init__.py`, `base.py`, `normalizer.py`, `registry.py`, `email_adapter.py`, and `chat_adapter.py` files.

2. **ChannelMessage dataclass defined** — `ChannelMessage` is a Python dataclass (or class) in `base.py` with all required fields: `source` (str), `sender_email` (str), `sender_name` (str), `subject` (str), `content` (str), `content_type` (str, default `"text/html"`), `attachments` (list), `metadata` (dict), `ticket_id` (str, optional), `is_internal` (bool, default `False`), `timestamp` (datetime).

3. **Abstract base adapter** — `base.py` defines an abstract `ChannelAdapter` base class with abstract methods: `normalize(raw_message) -> ChannelMessage` and `can_handle(source: str) -> bool`.

4. **Registry supports registration and dispatch** — `registry.py` provides a `ChannelRegistry` class with:
   - `register(adapter: ChannelAdapter)` — registers an adapter
   - `get_adapter(source: str) -> ChannelAdapter` — returns the adapter matching the source
   - A module-level default registry instance with email and chat adapters pre-registered

5. **Normalizer processes ChannelMessage into HD Ticket communication** — `normalizer.py` provides a `ChannelNormalizer` class with a `process(msg: ChannelMessage)` method that:
   - Creates a new HD Ticket if `msg.ticket_id` is `None` (using `msg.subject`, `msg.sender_email`, `msg.sender_name`, `msg.source` as ticket `via_customer_portal` if source is "portal")
   - Creates a ticket communication (reply) if `msg.ticket_id` is set
   - Handles `is_internal=True` to create internal communications

6. **Email adapter wraps existing email processing** — `email_adapter.py` provides an `EmailAdapter(ChannelAdapter)` class that:
   - Sets `source = "email"` in the produced `ChannelMessage`
   - Wraps the existing `HdEmailAccount.get_inbound_mails()` / ticket creation flow (no duplicate logic — delegates to existing code)
   - Passes all existing email functionality through unchanged (regression-safe)

7. **Chat adapter normalizes chat messages** — `chat_adapter.py` provides a `ChatAdapter(ChannelAdapter)` class that:
   - Sets `source = "chat"` in the produced `ChannelMessage`
   - Accepts a `chat_session_id` in the raw message dict and stores it in `metadata`
   - Auto-generates `subject` as `"Chat session {chat_session_id}"` when no subject is provided

8. **Regression safety** — All existing email-to-ticket flows continue to work identically after the refactor. No existing test suite failures are introduced.

9. **Unit tests for normalizer and registry** — Test file at `helpdesk/helpdesk/channels/tests/test_channels.py` (or `tests/test_channel_normalizer.py`) with:
   - Tests for `ChannelMessage` dataclass instantiation and defaults
   - Tests for `ChannelRegistry.register()` and `get_adapter()`
   - Tests for `ChannelNormalizer.process()` with both new-ticket and reply scenarios
   - Tests for `ChatAdapter.normalize()` with a mock chat message dict

10. **Regression tests for email flow** — Tests at `helpdesk/helpdesk/channels/tests/test_email_adapter.py` (or alongside existing email tests) confirming that calling `EmailAdapter` still produces identical ticket communications to the original code path.

## Tasks / Subtasks

- [ ] **Task 1: Create `helpdesk/helpdesk/channels/` Python package** (AC: #1)
  - [ ] Create `helpdesk/helpdesk/channels/__init__.py` (exports key symbols: `ChannelMessage`, `ChannelAdapter`, `ChannelNormalizer`, `ChannelRegistry`, `default_registry`)
  - [ ] Verify package is importable from `helpdesk.helpdesk.channels`

- [ ] **Task 2: Define `ChannelMessage` dataclass and `ChannelAdapter` ABC in `base.py`** (AC: #2, #3)
  - [ ] Create `helpdesk/helpdesk/channels/base.py`
  - [ ] Implement `ChannelMessage` as a `@dataclass` with all required fields and typed annotations
  - [ ] Implement abstract `ChannelAdapter` base class with `normalize()` and `can_handle()` abstract methods
  - [ ] Add docstrings to both classes explaining extension patterns

- [ ] **Task 3: Implement `ChannelRegistry` in `registry.py`** (AC: #4)
  - [ ] Create `helpdesk/helpdesk/channels/registry.py`
  - [ ] Implement `ChannelRegistry` class with `register()`, `get_adapter()`, and `list_adapters()` methods
  - [ ] Create module-level `default_registry` instance
  - [ ] `get_adapter()` raises `ValueError` with informative message for unknown source

- [ ] **Task 4: Implement `ChannelNormalizer` in `normalizer.py`** (AC: #5)
  - [ ] Create `helpdesk/helpdesk/channels/normalizer.py`
  - [ ] Implement `ChannelNormalizer.process(msg: ChannelMessage)` method
  - [ ] Handle `ticket_id=None` → create new HD Ticket via `frappe.get_doc("HD Ticket", {...}).insert()`
  - [ ] Handle `ticket_id` set → fetch ticket and call `create_communication_via_contact()` or equivalent
  - [ ] Handle `is_internal=True` → mark communication as internal

- [ ] **Task 5: Implement `EmailAdapter` in `email_adapter.py`** (AC: #6, #8)
  - [ ] Create `helpdesk/helpdesk/channels/email_adapter.py`
  - [ ] Implement `EmailAdapter(ChannelAdapter)` with `source = "email"` and `can_handle("email") -> True`
  - [ ] `normalize()` method maps `InboundMail` / raw email dict fields to `ChannelMessage` (delegates to existing `HdEmailAccount` override logic, no code duplication)
  - [ ] Ensure backward-compatible: existing `hooks.py` email processing path still works via adapter

- [ ] **Task 6: Implement `ChatAdapter` in `chat_adapter.py`** (AC: #7)
  - [ ] Create `helpdesk/helpdesk/channels/chat_adapter.py`
  - [ ] Implement `ChatAdapter(ChannelAdapter)` with `source = "chat"` and `can_handle("chat") -> True`
  - [ ] `normalize()` accepts a dict with: `sender_email`, `sender_name`, `content`, `chat_session_id`, optional `ticket_id`
  - [ ] Auto-generates `subject` if not provided: `f"Chat session {chat_session_id}"`
  - [ ] Stores `chat_session_id` and any extra fields in `metadata`

- [ ] **Task 7: Register adapters in `__init__.py` and wire to `default_registry`** (AC: #4)
  - [ ] Import and register `EmailAdapter` and `ChatAdapter` into `default_registry` on module import
  - [ ] Ensure lazy import pattern to avoid circular imports with Frappe app structure

- [ ] **Task 8: Write unit tests for normalizer and registry** (AC: #9)
  - [ ] Create `helpdesk/helpdesk/channels/tests/__init__.py`
  - [ ] Create `helpdesk/helpdesk/channels/tests/test_channels.py`
  - [ ] Test `ChannelMessage` default field values
  - [ ] Test `ChannelRegistry.register()` and `get_adapter()` for known/unknown sources
  - [ ] Test `ChatAdapter.normalize()` with a mock chat message dict
  - [ ] Test `ChannelNormalizer.process()` with mocked `frappe.get_doc` (new ticket path)
  - [ ] Test `ChannelNormalizer.process()` with `ticket_id` set (reply path)

- [ ] **Task 9: Write regression tests for email adapter** (AC: #10)
  - [ ] Create `helpdesk/helpdesk/channels/tests/test_email_adapter.py`
  - [ ] Test that `EmailAdapter.normalize()` produces a valid `ChannelMessage` from a mock `InboundMail`
  - [ ] Test that `can_handle("email") == True` and `can_handle("chat") == False`
  - [ ] Run existing HD Ticket email tests to confirm no regressions

- [ ] **Task 10: Ensure 80% unit test coverage on new backend code** (AC: #9, #10 — NFR-M-01)
  - [ ] Run `pytest helpdesk/helpdesk/channels/` with coverage report
  - [ ] Fix any gaps to reach ≥80% coverage on channels module

## Dev Notes

### Architecture Patterns

This story implements ADR-07 (Channel Abstraction Layer) from the architecture document. The design uses:

- **Abstract Base Class pattern** — `ChannelAdapter` in `base.py` uses Python's `abc.ABC` and `abc.abstractmethod`. Concrete adapters must implement `normalize()` and `can_handle()`.
- **Registry pattern** — `ChannelRegistry` acts as a service locator/dispatcher. The module-level `default_registry` is the application's singleton registry.
- **Dataclass for value objects** — `ChannelMessage` is a `@dataclass` for immutable(ish) value transport between adapters and the normalizer.
- **Frappe doc_events for email** — The existing email processing is triggered via `hooks.py` `doc_events` on `Email Account`. The `EmailAdapter` wraps `helpdesk/overrides/email_account.py` (`HdEmailAccount.get_inbound_mails()`). **Do not replace existing hooks** — the adapter wraps/delegates, it does not replace.

### Key Files to Touch / Create

**New files (create):**
```
helpdesk/helpdesk/channels/__init__.py
helpdesk/helpdesk/channels/base.py
helpdesk/helpdesk/channels/normalizer.py
helpdesk/helpdesk/channels/registry.py
helpdesk/helpdesk/channels/email_adapter.py
helpdesk/helpdesk/channels/chat_adapter.py
helpdesk/helpdesk/channels/tests/__init__.py
helpdesk/helpdesk/channels/tests/test_channels.py
helpdesk/helpdesk/channels/tests/test_email_adapter.py
```

**Existing files to understand (read, possibly modify minimally):**
```
helpdesk/helpdesk/overrides/email_account.py   # HdEmailAccount — source of email logic
helpdesk/helpdesk/helpdesk/doctype/hd_ticket/hd_ticket.py
  → create_communication_via_contact()         # Used by normalizer for replies
  → Line ~181: ticket creation from email      # Understand for email_adapter
helpdesk/hooks.py                              # doc_events for email processing
```

### Frappe Patterns in Use

```python
# Creating a new HD Ticket from normalizer
ticket = frappe.get_doc({
    "doctype": "HD Ticket",
    "subject": msg.subject,
    "raised_by": msg.sender_email,
    "raised_by_contact": msg.sender_name,
    "via_customer_portal": msg.source == "portal",
    "channel": msg.source,   # new field to add if needed
    "description": msg.content,
})
ticket.insert(ignore_permissions=True)

# Creating a reply communication on an existing ticket
ticket = frappe.get_doc("HD Ticket", msg.ticket_id)
ticket.create_communication_via_contact(
    message=msg.content,
    attachments=msg.attachments,
)
```

### ChannelMessage Interface (from ADR-07)

```python
@dataclass
class ChannelMessage:
    source: str               # "email", "chat", "whatsapp", "portal"
    sender_email: str
    sender_name: str
    subject: str              # For email; auto-generated for chat
    content: str              # HTML content, sanitized
    content_type: str = "text/html"
    attachments: list = field(default_factory=list)
    metadata: dict = field(default_factory=dict)
    ticket_id: str = None     # Existing ticket ID if this is a reply
    is_internal: bool = False
    timestamp: datetime = field(default_factory=datetime.utcnow)
```

### Testing Standards

- Use `frappe.tests.utils.FrappeTestCase` or `unittest.TestCase` with mocking via `unittest.mock.patch`
- Mock `frappe.get_doc`, `frappe.db.get_value` to avoid DB dependency in unit tests
- Integration tests for email regression can use `FrappeTestCase` with real Frappe context
- Target ≥80% coverage (NFR-M-01)
- Test file naming: `test_*.py` per Frappe convention

### Security Considerations

- `content` field in `ChannelMessage` must be HTML-sanitized before storage. The normalizer should call `frappe.utils.html_sanitize()` or Frappe's built-in sanitizer on `msg.content`.
- Internal notes (`is_internal=True`) must never be exposed via customer portal APIs — this is a server-side check in `hd_ticket.py`, not in the channel layer (but note it in tests).

### Feature Flag

The channel abstraction layer itself does not require a feature flag. The `chat_enabled` flag (from `HD Settings`) gates whether chat messages are routed; the channel layer is infrastructure only.

### Project Structure Notes

- **Module location**: `helpdesk/helpdesk/channels/` — follows existing module structure pattern (e.g., `helpdesk/helpdesk/api/`, `helpdesk/helpdesk/overrides/`)
- **Import path**: `from helpdesk.helpdesk.channels import ChannelMessage, default_registry`
- **Naming convention**: Snake_case modules, PascalCase classes — consistent with existing codebase
- **No Frappe DocTypes created** in this story — channel abstraction is a pure Python module, not a DocType
- **Tests location**: `helpdesk/helpdesk/channels/tests/` — mirrors `helpdesk/helpdesk/api/agent_home/` test pattern

### Dependencies / Story Prerequisites

- This story has **no dependencies** on other Phase 1 stories — it is foundational for Epic 3
- Story 3.2 (Chat Session Management Backend) depends on the `ChatAdapter` from this story
- Story 3.6 (Chat-to-Ticket Transcript) uses the normalizer directly

### References

- Architecture ADR-07: Channel Abstraction Layer [Source: `_bmad-output/planning-artifacts/architecture.md#ADR-07: Channel Abstraction Layer`]
- Architecture diagram and `ChannelMessage` interface definition [Source: `_bmad-output/planning-artifacts/architecture.md#ADR-07`]
- Epic 3 Story 3.1 acceptance criteria [Source: `_bmad-output/planning-artifacts/epics.md#Story 3.1: Channel Abstraction Layer`]
- Additional Requirement AR-01: Channel abstraction layer must be implemented before live chat [Source: `_bmad-output/planning-artifacts/epics.md#Additional Requirements`]
- NFR-M-01: 80% unit test coverage on all new backend code [Source: `_bmad-output/planning-artifacts/epics.md#Non-Functional Requirements`]
- NFR-M-03: Chat uses abstract channel interface for future extensibility [Source: `_bmad-output/planning-artifacts/epics.md#Non-Functional Requirements`]
- NFR-A-01: Core ticketing unaffected by chat failures [Source: `_bmad-output/planning-artifacts/epics.md#Non-Functional Requirements`]
- Existing email override: `helpdesk/helpdesk/overrides/email_account.py`
- Existing ticket creation: `helpdesk/helpdesk/helpdesk/doctype/hd_ticket/hd_ticket.py` line ~686 `create_communication_via_contact()`
- Implementation module location: `helpdesk/helpdesk/channels/` [Source: `_bmad-output/planning-artifacts/architecture.md#ADR-07`]

## Dev Agent Record

### Agent Model Used

claude-opus-4-5

### Debug Log References

### Completion Notes List

### File List
