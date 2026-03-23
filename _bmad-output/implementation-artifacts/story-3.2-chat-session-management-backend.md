# Story 3.2: Chat Session Management Backend

Status: ready-for-dev

<!-- Note: Validation is optional. Run validate-create-story for quality check before dev-story. -->

## Story

As a developer,
I want chat session lifecycle management,
so that chat conversations are properly tracked and cleaned up.

## Acceptance Criteria

1. **HD Chat Session DocType exists** — The `HD Chat Session` DocType is created with fields: `session_id` (Data, unique), `customer_email` (Data, mandatory), `customer_name` (Data), `status` (Select: waiting/active/ended, default "waiting"), `started_at` (Datetime, auto-set on create), `ended_at` (Datetime, optional), `agent` (Link → HD Agent, nullable until assigned), `brand` (Link → HD Brand, optional), `ticket` (Link → HD Ticket, set after first message), `inactivity_timeout_minutes` (Int, default 30), and `jwt_token_hash` (Data, for server-side token validation).

2. **HD Chat Message DocType exists** — The `HD Chat Message` DocType is created as a child table of `HD Chat Session` with fields: `message_id` (Data, unique), `session` (Link → HD Chat Session, mandatory), `sender_type` (Select: customer/agent/system), `sender_email` (Data), `content` (Long Text, sanitized), `sent_at` (Datetime, auto-set), `is_read` (Check, default 0), and `attachment` (Attach, optional).

3. **`create_session` API endpoint** — `POST /api/method/helpdesk.api.chat.create_session` accepts `{email, name, subject, brand}` and:
   - Creates an `HD Chat Session` record with `status="waiting"`, `customer_email`, `customer_name`, `started_at`
   - Generates a short-lived JWT token (24h expiry, signed with site secret, subject = customer email hash)
   - Returns `{session_id, token, status}` to the caller
   - Validates the email format before creating the session

4. **`send_message` API endpoint** — `POST /api/method/helpdesk.api.chat.send_message` accepts `{session_id, content, attachment}` (requires valid JWT in Authorization header or `token` param):
   - Validates session ownership via JWT
   - Appends an `HD Chat Message` child record to the session
   - Sanitizes `content` via `frappe.utils.html_sanitize()` before storage
   - On the **first customer message** for a session, creates an `HD Ticket` with `source="Chat"` via the `ChatAdapter` channel normalizer (from Story 3.1) and stores the `ticket` link on the session
   - Publishes a real-time Socket.IO event `{type: "new_message", session_id, message}` to room `chat:{session_id}`
   - Returns `{message_id, sent_at}`

5. **`end_session` API endpoint** — `POST /api/method/helpdesk.api.chat.end_session` accepts `{session_id}`:
   - Sets session `status="ended"` and `ended_at=now()`
   - Publishes a system message `"This chat has ended"` to the session
   - Publishes a Socket.IO event to room `chat:{session_id}` with `{type: "session_ended"}`
   - Accessible by the owning customer (JWT) or any agent with HD Agent role

6. **`get_sessions` API endpoint** — `GET /api/method/helpdesk.api.chat.get_sessions` (agent-only, requires HD Agent role):
   - Returns a list of active/waiting sessions with fields: `session_id`, `customer_email`, `customer_name`, `status`, `started_at`, `agent`, `ticket`, `message_count`
   - Supports `?status=waiting` filter
   - Results ordered by `started_at` ascending (oldest first)

7. **`transfer_session` API endpoint** — `POST /api/method/helpdesk.api.chat.transfer_session` accepts `{session_id, target_agent_email}` (agent-only, HD Agent role):
   - Updates session's `agent` field to `target_agent_email`
   - Publishes Socket.IO event `{type: "session_transferred", new_agent}` to room `chat:{session_id}` and `agent:{target_agent_email}`
   - Adds a system message to the session log

8. **JWT token generation and validation** — A dedicated helper in `helpdesk/helpdesk/chat/jwt_helper.py`:
   - `generate_chat_token(session_id, customer_email) -> str` — uses `PyJWT` (or `frappe`'s HMAC utilities) to create a signed token with payload `{session_id, email_hash, exp}`
   - `validate_chat_token(token, session_id) -> bool` — validates signature, expiry, and that `session_id` matches token payload; raises `frappe.AuthenticationError` on failure
   - Token signed with `frappe.utils.get_site_secret()` (never hardcoded)

9. **Session cleanup background job** — A function `helpdesk.helpdesk.chat.session_cleanup.cleanup_inactive_sessions()`:
   - Queries for `HD Chat Session` records where `status IN ("waiting", "active")` AND `started_at < now() - inactivity_timeout_minutes` (using the per-session timeout, defaulting to 30 minutes)
   - For each inactive session: calls `end_session` logic (sets status="ended", ended_at, publishes system message)
   - Runs in the `short` Redis queue for high priority
   - Logs cleaned sessions count via `frappe.logger()`

10. **Scheduler event in `hooks.py`** — The cleanup job is registered as a scheduled event running every 5 minutes:
    ```python
    scheduler_events = {
        "cron": {
            "*/5 * * * *": [
                "helpdesk.helpdesk.chat.session_cleanup.cleanup_inactive_sessions"
            ]
        }
    }
    ```
    Added alongside existing scheduler events without removing them.

11. **Unit tests for session lifecycle** — Test file `helpdesk/helpdesk/chat/tests/test_chat_session.py` with:
    - Test `create_session` creates HD Chat Session with correct fields and returns JWT token
    - Test `send_message` creates HD Chat Message, sanitizes content, and creates HD Ticket on first message
    - Test `end_session` sets status="ended" and ended_at
    - Test `cleanup_inactive_sessions` ends sessions past the timeout threshold and skips recent/already-ended ones
    - Test `generate_chat_token` and `validate_chat_token` (valid token, expired token, wrong session_id)
    - Mocks `frappe.get_doc`, `frappe.db`, and `frappe.realtime.publish` to avoid DB dependency in unit tests
    - Achieves ≥80% coverage on the `helpdesk/helpdesk/chat/` module (NFR-M-01)

12. **Security: input sanitization and token enforcement** — All API endpoints that write messages apply `frappe.utils.html_sanitize()` on `content`. All customer-facing endpoints (`send_message`) validate the JWT token. Agent endpoints (`get_sessions`, `transfer_session`) use `frappe.only_for` or a role check for `HD Agent` / `System Manager`. No cross-customer session data access is possible (NFR-SE-02).

## Tasks / Subtasks

- [ ] **Task 1: Create `HD Chat Session` DocType** (AC: #1)
  - [ ] Create DocType JSON at `helpdesk/helpdesk/helpdesk/doctype/hd_chat_session/hd_chat_session.json`
  - [ ] Fields: `session_id` (Data, unique, read-only after creation), `customer_email` (Data, mandatory), `customer_name` (Data), `status` (Select: waiting/active/ended, default "waiting"), `started_at` (Datetime), `ended_at` (Datetime, optional), `agent` (Link → HD Agent), `brand` (Link → HD Brand), `ticket` (Link → HD Ticket), `inactivity_timeout_minutes` (Int, default 30), `jwt_token_hash` (Data, hidden)
  - [ ] Add Python controller `hd_chat_session.py` with `autoname` (UUID) and `before_insert` hook to set `started_at`
  - [ ] Add permission rules: Agent/Admin can read all; customers read via token only
  - [ ] Create DB migration patch at `helpdesk/patches/v1_phase1/create_hd_chat_session.py`

- [ ] **Task 2: Create `HD Chat Message` DocType** (AC: #2)
  - [ ] Create DocType JSON at `helpdesk/helpdesk/helpdesk/doctype/hd_chat_message/hd_chat_message.json`
  - [ ] Set `istable = 1` (child table) and `parenttype = "HD Chat Session"`
  - [ ] Fields: `message_id` (Data, unique, auto-UUID), `sender_type` (Select: customer/agent/system), `sender_email` (Data), `content` (Long Text), `sent_at` (Datetime, auto-set), `is_read` (Check, default 0), `attachment` (Attach)
  - [ ] Python controller sets `sent_at = frappe.utils.now()` and auto-generates `message_id` on before_insert
  - [ ] Create DB migration patch at `helpdesk/patches/v1_phase1/create_hd_chat_message.py`

- [ ] **Task 3: Create `helpdesk/helpdesk/chat/` Python package** (AC: #8, #9)
  - [ ] Create `helpdesk/helpdesk/chat/__init__.py`
  - [ ] Create `helpdesk/helpdesk/chat/jwt_helper.py` with `generate_chat_token()` and `validate_chat_token()`
  - [ ] Create `helpdesk/helpdesk/chat/session_cleanup.py` with `cleanup_inactive_sessions()`
  - [ ] Create `helpdesk/helpdesk/chat/tests/__init__.py`

- [ ] **Task 4: Implement JWT helpers** (AC: #8)
  - [ ] Implement `generate_chat_token(session_id, customer_email) -> str`
    - Payload: `{sub: sha256(customer_email), session_id: session_id, exp: now + 24h}`
    - Sign with `frappe.utils.get_site_secret()` using HMAC-SHA256 (PyJWT or manual)
  - [ ] Implement `validate_chat_token(token, session_id) -> bool`
    - Decode and verify signature
    - Check `exp` not past
    - Verify `payload["session_id"] == session_id`
    - Raise `frappe.AuthenticationError` on any failure

- [ ] **Task 5: Implement `helpdesk/api/chat.py`** (AC: #3, #4, #5, #6, #7, #12)
  - [ ] Create `helpdesk/helpdesk/api/chat.py` (or `helpdesk/api/chat.py` per existing structure)
  - [ ] Implement `create_session(email, name, subject=None, brand=None)` — `@frappe.whitelist(allow_guest=True)`
    - Validate email format
    - Create HD Chat Session (status="waiting", customer_email, customer_name, started_at=now())
    - Call `generate_chat_token(session.name, email)`
    - Return `{session_id, token, status}`
  - [ ] Implement `send_message(session_id, content, token, attachment=None)` — `@frappe.whitelist(allow_guest=True)`
    - Call `validate_chat_token(token, session_id)` → raises AuthenticationError if invalid
    - `frappe.utils.html_sanitize(content)` before storage
    - Append HD Chat Message to session
    - If this is the first customer message and session.ticket is None: call `ChatAdapter` / `ChannelNormalizer` to create HD Ticket with source="Chat", link ticket back to session
    - Publish `frappe.publish_realtime("chat_message", {...}, room=f"chat:{session_id}")`
    - Return `{message_id, sent_at}`
  - [ ] Implement `end_session(session_id, token=None)` — `@frappe.whitelist(allow_guest=True)`
    - Allow customer (valid JWT) or agent (role check) to end session
    - Set status="ended", ended_at=now()
    - Append a system message "This chat has ended"
    - Publish `frappe.publish_realtime("session_ended", {session_id}, room=f"chat:{session_id}")`
  - [ ] Implement `get_sessions(status=None)` — `@frappe.whitelist()` (agent role required)
    - `frappe.only_for(["HD Agent", "System Manager", "Administrator"])`
    - Query HD Chat Session with optional status filter
    - Return list with `session_id`, `customer_email`, `customer_name`, `status`, `started_at`, `agent`, `ticket`
  - [ ] Implement `transfer_session(session_id, target_agent_email)` — `@frappe.whitelist()` (agent role required)
    - Validate target agent exists
    - Update session.agent = target_agent_email
    - Append system message to session
    - Publish Socket.IO event to `chat:{session_id}` and `agent:{target_agent_email}`

- [ ] **Task 6: Implement session cleanup job** (AC: #9)
  - [ ] In `session_cleanup.py`, implement `cleanup_inactive_sessions()`:
    - Query: `SELECT name, inactivity_timeout_minutes FROM "HD Chat Session" WHERE status IN ('waiting', 'active')`
    - For each session: check if `started_at < now() - inactivity_timeout_minutes minutes`
    - If inactive: set status="ended", ended_at=now(), append system message, publish realtime event
    - Log count via `frappe.logger().info(f"Cleaned {n} inactive chat sessions")`

- [ ] **Task 7: Register scheduler event in `hooks.py`** (AC: #10)
  - [ ] Open `helpdesk/hooks.py`
  - [ ] Add to `scheduler_events["cron"]` dict: `"*/5 * * * *"` → `"helpdesk.helpdesk.chat.session_cleanup.cleanup_inactive_sessions"`
  - [ ] Verify it does not overwrite existing `*/5 * * * *` entries (merge into list if needed)

- [ ] **Task 8: Write unit tests** (AC: #11)
  - [ ] Create `helpdesk/helpdesk/chat/tests/test_chat_session.py`
  - [ ] Test `create_session`: mock `frappe.get_doc().insert()`, assert session fields and token returned
  - [ ] Test `send_message` first message: mock channel normalizer, assert HD Ticket created and linked
  - [ ] Test `send_message` subsequent messages: assert no duplicate ticket created
  - [ ] Test `end_session`: assert status="ended", ended_at set, realtime published
  - [ ] Test `cleanup_inactive_sessions`: mock DB query, assert end_session called for stale sessions only
  - [ ] Test `generate_chat_token` and `validate_chat_token`:
    - Valid token passes validation
    - Expired token raises `frappe.AuthenticationError`
    - Wrong session_id raises `frappe.AuthenticationError`
    - Tampered signature raises `frappe.AuthenticationError`
  - [ ] Run coverage to confirm ≥80% on `helpdesk/helpdesk/chat/`

- [ ] **Task 9: Add DB patches to `patches.txt`** (AC: #1, #2)
  - [ ] Append `helpdesk.patches.v1_phase1.create_hd_chat_session` to `helpdesk/patches.txt`
  - [ ] Append `helpdesk.patches.v1_phase1.create_hd_chat_message` to `helpdesk/patches.txt`

## Dev Notes

### Architecture Patterns

This story implements the **HD Chat Session** and **HD Chat Message** DocTypes (ADR-02) along with the chat API layer (ADR-08) and JWT security model (ADR-05) from the architecture document.

**Key patterns:**
- **JWT via site secret** — Never hardcode secrets. Always use `frappe.utils.get_site_secret()`. Use `PyJWT` library (already available in Frappe's Python environment) or implement manual HMAC-SHA256 signing as a fallback.
- **Guest-accessible endpoints** — `create_session` and `send_message` use `@frappe.whitelist(allow_guest=True)`. Security is enforced through the JWT token parameter.
- **Channel normalizer integration** — When the first customer message arrives, delegate ticket creation to `helpdesk.helpdesk.channels.normalizer.ChannelNormalizer` using a `ChannelMessage` with `source="chat"`. This ensures Story 3.1's abstraction layer is used (as required by AR-01 and NFR-M-03).
- **Socket.IO rooms** — Per ADR architecture (AR-07), room naming convention is `chat:{session_id}`. Use `frappe.publish_realtime(event, data, room=f"chat:{session_id}")`.
- **Background jobs** — The session cleanup job uses the `short` queue (ADR-12) for high priority. Schedule via `frappe.enqueue()` if triggered manually, or via `scheduler_events` for the cron trigger.
- **Frappe DocType child tables** — `HD Chat Message` has `istable = 1` and `parenttype = "HD Chat Session"`. Messages are stored as child rows and accessed via `session.get("messages")`. Alternatively, use `HD Chat Message` as an independent DocType with a `session` Link field for easier querying — this is preferred for scalability (avoids loading all messages when fetching session metadata).

### HD Chat Session Schema (detailed)

```python
# hd_chat_session.json (key fields)
{
    "name": "HD Chat Session",
    "module": "Helpdesk",
    "naming_rule": "By \"Autoname\" field",
    "autoname": "field:session_id",
    "fields": [
        {"fieldname": "session_id", "fieldtype": "Data", "label": "Session ID", "unique": 1, "read_only": 1},
        {"fieldname": "customer_email", "fieldtype": "Data", "label": "Customer Email", "reqd": 1},
        {"fieldname": "customer_name", "fieldtype": "Data", "label": "Customer Name"},
        {"fieldname": "status", "fieldtype": "Select", "label": "Status",
         "options": "waiting\nactive\nended", "default": "waiting"},
        {"fieldname": "started_at", "fieldtype": "Datetime", "label": "Started At"},
        {"fieldname": "ended_at", "fieldtype": "Datetime", "label": "Ended At"},
        {"fieldname": "agent", "fieldtype": "Link", "options": "HD Agent", "label": "Agent"},
        {"fieldname": "brand", "fieldtype": "Link", "options": "HD Brand", "label": "Brand"},
        {"fieldname": "ticket", "fieldtype": "Link", "options": "HD Ticket", "label": "Ticket"},
        {"fieldname": "inactivity_timeout_minutes", "fieldtype": "Int", "label": "Inactivity Timeout (min)", "default": 30},
        {"fieldname": "jwt_token_hash", "fieldtype": "Data", "label": "JWT Token Hash", "hidden": 1}
    ]
}
```

### HD Chat Message Schema (detailed)

```python
# hd_chat_message.json (key fields) — standalone DocType (not child table) for scalability
{
    "name": "HD Chat Message",
    "module": "Helpdesk",
    "naming_rule": "By \"Autoname\" field",
    "autoname": "field:message_id",
    "fields": [
        {"fieldname": "message_id", "fieldtype": "Data", "label": "Message ID", "unique": 1},
        {"fieldname": "session", "fieldtype": "Link", "options": "HD Chat Session", "label": "Session", "reqd": 1},
        {"fieldname": "sender_type", "fieldtype": "Select", "options": "customer\nagent\nsystem", "label": "Sender Type"},
        {"fieldname": "sender_email", "fieldtype": "Data", "label": "Sender Email"},
        {"fieldname": "content", "fieldtype": "Long Text", "label": "Content"},
        {"fieldname": "sent_at", "fieldtype": "Datetime", "label": "Sent At"},
        {"fieldname": "is_read", "fieldtype": "Check", "label": "Is Read", "default": 0},
        {"fieldname": "attachment", "fieldtype": "Attach", "label": "Attachment"}
    ]
}
```

> **Design note:** `HD Chat Message` is implemented as a standalone DocType (not a child table) to allow efficient queries like "messages for session X since timestamp Y" without loading the entire session document. This is the preferred pattern for high-volume child data.

### JWT Token Flow (from ADR-05)

```
Customer fills pre-chat form
    → POST /api/method/helpdesk.api.chat.create_session
    → Server validates email, creates HD Chat Session
    → generate_chat_token(session_id, email) → JWT
    → JWT returned to widget → stored in localStorage
    → All subsequent send_message calls include token param
    → Server calls validate_chat_token(token, session_id) on each call
```

```python
# jwt_helper.py implementation pattern
import jwt  # PyJWT
import hashlib
import frappe
from datetime import datetime, timedelta

def generate_chat_token(session_id: str, customer_email: str) -> str:
    secret = frappe.utils.get_site_secret()
    email_hash = hashlib.sha256(customer_email.encode()).hexdigest()
    payload = {
        "sub": email_hash,
        "session_id": session_id,
        "exp": datetime.utcnow() + timedelta(hours=24),
        "iat": datetime.utcnow(),
    }
    return jwt.encode(payload, secret, algorithm="HS256")

def validate_chat_token(token: str, session_id: str) -> bool:
    secret = frappe.utils.get_site_secret()
    try:
        payload = jwt.decode(token, secret, algorithms=["HS256"])
        if payload.get("session_id") != session_id:
            raise frappe.AuthenticationError("Token session mismatch")
        return True
    except jwt.ExpiredSignatureError:
        raise frappe.AuthenticationError("Chat token expired")
    except jwt.InvalidTokenError as e:
        raise frappe.AuthenticationError(f"Invalid chat token: {e}")
```

### Session Cleanup Pattern

```python
# session_cleanup.py
import frappe

def cleanup_inactive_sessions():
    """End chat sessions that have been inactive beyond their timeout."""
    sessions = frappe.db.get_all(
        "HD Chat Session",
        filters={"status": ["in", ["waiting", "active"]]},
        fields=["name", "session_id", "started_at", "inactivity_timeout_minutes"]
    )
    ended_count = 0
    for session in sessions:
        timeout = session.inactivity_timeout_minutes or 30
        cutoff = frappe.utils.add_to_date(frappe.utils.now_datetime(), minutes=-timeout)
        if session.started_at < cutoff:
            _end_session_internal(session.session_id)
            ended_count += 1
    if ended_count:
        frappe.logger().info(f"[ChatCleanup] Ended {ended_count} inactive chat sessions")
```

### Key Files to Create / Modify

**New files (create):**
```
helpdesk/helpdesk/helpdesk/doctype/hd_chat_session/
    hd_chat_session.json
    hd_chat_session.py
    __init__.py

helpdesk/helpdesk/helpdesk/doctype/hd_chat_message/
    hd_chat_message.json
    hd_chat_message.py
    __init__.py

helpdesk/helpdesk/chat/
    __init__.py
    jwt_helper.py
    session_cleanup.py
    tests/
        __init__.py
        test_chat_session.py

helpdesk/helpdesk/api/chat.py   (or helpdesk/api/chat.py — check existing api/ location)

helpdesk/patches/v1_phase1/
    create_hd_chat_session.py
    create_hd_chat_message.py
```

**Existing files to modify:**
```
helpdesk/hooks.py
    → Add scheduler_events["cron"]["*/5 * * * *"] entry for cleanup job
    → Merge with existing cron entries if the key already exists

helpdesk/patches.txt
    → Append two new patch module paths
```

**Existing files to understand (read):**
```
helpdesk/helpdesk/channels/chat_adapter.py    # Story 3.1 output — used for ticket creation
helpdesk/helpdesk/channels/normalizer.py      # Story 3.1 output — ChannelNormalizer.process()
helpdesk/hooks.py                             # Existing scheduler_events — merge carefully
helpdesk/helpdesk/helpdesk/doctype/hd_ticket/hd_ticket.py
    → Understand existing ticket creation pattern for source="Chat"
```

### Frappe API Patterns

```python
# Creating an HD Chat Session
session = frappe.get_doc({
    "doctype": "HD Chat Session",
    "session_id": frappe.generate_hash(length=20),
    "customer_email": email,
    "customer_name": name,
    "status": "waiting",
    "started_at": frappe.utils.now(),
    "inactivity_timeout_minutes": 30,
})
session.insert(ignore_permissions=True)

# Creating an HD Chat Message
msg = frappe.get_doc({
    "doctype": "HD Chat Message",
    "message_id": frappe.generate_hash(length=20),
    "session": session_id,
    "sender_type": "customer",
    "sender_email": customer_email,
    "content": frappe.utils.html_sanitize(content),
    "sent_at": frappe.utils.now(),
})
msg.insert(ignore_permissions=True)

# Publishing realtime event
frappe.publish_realtime(
    event="chat_message",
    message={"session_id": session_id, "message_id": msg.name, "content": content},
    room=f"chat:{session_id}"
)
```

### Channel Normalizer Integration (First Message)

```python
# In send_message(), when session.ticket is None and sender_type == "customer":
from helpdesk.helpdesk.channels.base import ChannelMessage
from helpdesk.helpdesk.channels.normalizer import ChannelNormalizer

channel_msg = ChannelMessage(
    source="chat",
    sender_email=customer_email,
    sender_name=session.customer_name or customer_email,
    subject=f"Chat session {session_id}",
    content=sanitized_content,
    metadata={"chat_session_id": session_id},
)
normalizer = ChannelNormalizer()
ticket = normalizer.process(channel_msg)   # Creates HD Ticket, returns doc
frappe.db.set_value("HD Chat Session", session_id, "ticket", ticket.name)
```

### Testing Patterns

```python
# Example test structure using unittest.mock
import unittest
from unittest.mock import patch, MagicMock
import frappe

class TestChatSession(unittest.TestCase):

    @patch("helpdesk.helpdesk.api.chat.frappe.get_doc")
    @patch("helpdesk.helpdesk.chat.jwt_helper.frappe.utils.get_site_secret")
    def test_create_session_returns_token(self, mock_secret, mock_get_doc):
        mock_secret.return_value = "test-secret-key"
        mock_session = MagicMock()
        mock_get_doc.return_value = mock_session

        from helpdesk.helpdesk.api.chat import create_session
        result = create_session(email="test@example.com", name="Test User")

        self.assertIn("session_id", result)
        self.assertIn("token", result)
        self.assertEqual(result["status"], "waiting")
```

### Feature Flag / Prerequisites

- The `chat_enabled` feature flag in `HD Settings` gates chat functionality at the UI level. The backend DocTypes and API functions in this story are created unconditionally, but should check `frappe.db.get_single_value("HD Settings", "chat_enabled")` before processing requests — return a clear error if chat is disabled.
- **Story 3.1 (Channel Abstraction Layer)** must be complete before implementing the "first message creates ticket" functionality in Task 5. If 3.1 is not yet deployed, the dev can stub the ticket creation call and wire it properly once 3.1 lands.

### Security Notes (NFR-SE-02, NFR-SE-06)

- All customer message content MUST be sanitized via `frappe.utils.html_sanitize()` before storage (prevents XSS).
- JWT tokens are validated on every `send_message` call — no session modification is possible without a valid token.
- `get_sessions` and `transfer_session` require Agent role — never expose session list to unauthenticated callers.
- `jwt_token_hash` field on `HD Chat Session` stores only a hash of the token (not the token itself) for server-side revocation if needed. The actual JWT is stored in the customer's `localStorage`.

### Project Structure Notes

- **Module location**: `helpdesk/helpdesk/chat/` follows existing module structure (e.g., `helpdesk/helpdesk/channels/`, `helpdesk/helpdesk/api/`)
- **DocType location**: `helpdesk/helpdesk/helpdesk/doctype/hd_chat_session/` and `.../hd_chat_message/` — follows the `HD prefix` naming convention (AR-02)
- **API module location**: Check whether existing API files live at `helpdesk/helpdesk/api/` or `helpdesk/api/` — match the existing pattern exactly
- **Patches**: All schema changes require patches in `helpdesk/patches/v1_phase1/` per AR-05 and must be listed in `helpdesk/patches.txt`
- **Naming**: All DocTypes use `HD` prefix per AR-02 (`HD Chat Session`, `HD Chat Message`)

### References

- Architecture ADR-02: New DocType Schema — HD Chat Session and HD Chat Message [Source: `_bmad-output/planning-artifacts/architecture.md#ADR-02`]
- Architecture ADR-05: Chat Widget Security — JWT token flow [Source: `_bmad-output/planning-artifacts/architecture.md#ADR-05`]
- Architecture ADR-07: Channel Abstraction Layer — ChatAdapter and ChannelNormalizer [Source: `_bmad-output/planning-artifacts/architecture.md#ADR-07`]
- Architecture ADR-08: API Design — `helpdesk/api/chat.py` endpoints [Source: `_bmad-output/planning-artifacts/architecture.md#ADR-08`]
- Architecture ADR-12: Background Job Architecture — `short` queue for chat cleanup [Source: `_bmad-output/planning-artifacts/architecture.md#ADR-12`]
- Epic 3 Story 3.2 acceptance criteria [Source: `_bmad-output/planning-artifacts/epics.md#Story 3.2: Chat Session Management Backend`]
- Additional Requirement AR-01: Channel abstraction before live chat [Source: `_bmad-output/planning-artifacts/epics.md#Additional Requirements`]
- Additional Requirement AR-02: HD prefix naming convention [Source: `_bmad-output/planning-artifacts/epics.md#Additional Requirements`]
- Additional Requirement AR-03: Redis Queue via `frappe.enqueue` [Source: `_bmad-output/planning-artifacts/epics.md#Additional Requirements`]
- Additional Requirement AR-05: Migration patches in `helpdesk/patches/v1_phase1/` [Source: `_bmad-output/planning-artifacts/epics.md#Additional Requirements`]
- Additional Requirement AR-07: Socket.IO room naming `chat:{session_id}` [Source: `_bmad-output/planning-artifacts/epics.md#Additional Requirements`]
- NFR-M-01: 80% unit test coverage [Source: `_bmad-output/planning-artifacts/epics.md#Non-Functional Requirements`]
- NFR-SE-02: Chat sessions authenticated via token; no cross-customer data access [Source: `_bmad-output/planning-artifacts/epics.md#Non-Functional Requirements`]
- NFR-SE-06: All chat messages sanitized server-side before storage [Source: `_bmad-output/planning-artifacts/epics.md#Non-Functional Requirements`]
- Story 3.1 (prerequisite): Channel Abstraction Layer [Source: `_bmad-output/implementation-artifacts/story-3.1-channel-abstraction-layer.md`]
- Frappe hooks.py scheduler_events pattern [Source: `_bmad-output/planning-artifacts/architecture.md#ADR-12`]

## Dev Agent Record

### Agent Model Used

claude-opus-4-5

### Debug Log References

### Completion Notes List

### File List
