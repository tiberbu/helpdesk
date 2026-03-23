# Story 3.4: Real-Time Chat Communication

Status: ready-for-dev

<!-- Note: Validation is optional. Run validate-create-story for quality check before dev-story. -->

## Story

As a customer chatting live,
I want real-time message delivery with typing indicators,
so that the experience feels like a modern messaging app.

## Acceptance Criteria

1. **Message delivery <200ms end-to-end (95th percentile)** — When either the customer (in the widget) or the agent (in the agent chat interface) sends a message, the message appears on the other party's screen within 200ms end-to-end under normal load (NFR-P-03, FR-LC-02). This is achieved via Socket.IO WebSocket transport (not long-polling). The server-side `chat_message` event handler must publish the event to room `chat:{session_id}` via `frappe.realtime.publish` immediately after saving to DB. Latency tests must confirm the 95th-percentile round-trip is <200ms in a local benchmark.

2. **Message status: sent / delivered / read** — Each message in the chat view displays a status indicator:
   - **Sent** (single grey check ✓): the message has been saved server-side and `sent_at` is set on `HD Chat Message`.
   - **Delivered** (double grey check ✓✓): the recipient's Socket.IO client has acknowledged receipt via a `message_delivered` event emitted back to the room.
   - **Read** (double blue check ✓✓): the recipient has viewed the message (chat panel is open and message is visible), confirmed via a `message_read` event. The `is_read` field on `HD Chat Message` is set to `1` server-side when this event is received (FR-LC-02).

3. **Typing indicator with 10-second auto-clear** — When either party presses a key in the message input:
   - A `typing_start` Socket.IO event is emitted to room `chat:{session_id}` with `{session_id, sender_type}`.
   - The other party's chat view shows a typing indicator: three animated dots with the text "{Name} is typing…".
   - If no additional `typing_start` events arrive within **10 seconds**, the indicator auto-clears (a `clearTimeout` or equivalent cancels the display timer).
   - When the sender submits their message or clears the input, a `typing_stop` event is emitted immediately and the indicator clears on the receiver side (FR-LC-02, AR-07).

4. **Chat session persists across page navigation via localStorage** — The widget stores `{session_id, token, status}` under the key `hd_chat_session` in `localStorage`. On each page load the widget reads this key and, if `status !== "ended"`, skips the pre-chat form and reconnects to the Socket.IO room `chat:{session_id}`, fetching and displaying the full message history. This is consistent with the localStorage mechanism introduced in Story 3.3 (FR-LC-02).

5. **Agent response timeout: auto-message after 2 minutes** — If the session's `status` is `"waiting"` (no agent has joined) and no agent message has been sent within **2 minutes** (configurable via `HD Settings.chat_response_timeout_seconds`, default `120`), the server sends an automated system message: `"We're experiencing high volume. You can wait or leave a message and we'll email you."` This system message is:
   - Stored as an `HD Chat Message` with `sender_type="system"`.
   - Published via `frappe.realtime.publish` to room `chat:{session_id}` as a `chat_message` event.
   - A background job `helpdesk.helpdesk.chat.response_timeout.check_unanswered_sessions()` runs every 60 seconds (via the `short` Redis queue) to detect and trigger the auto-message (FR-LC-02).

6. **Socket.IO room management for `chat:{session_id}`** — All real-time events for a chat session are scoped to the room `chat:{session_id}` (AR-07). Server-side event handlers in `helpdesk/helpdesk/realtime/chat_handlers.py` handle:
   - `join_room`: validate JWT, join the Socket.IO room.
   - `chat_message`: validate JWT, save message to DB, publish to room.
   - `typing_start` / `typing_stop`: validate JWT, broadcast to room (do NOT save to DB).
   - `message_delivered` / `message_read`: validate JWT, update `HD Chat Message.is_read`, publish status update to sender.
   - `leave_room`: clean up room membership on disconnect.

7. **Latency and integration tests** — A test suite at `helpdesk/tests/test_chat_realtime.py` (Python) and `widget/src/__tests__/ChatRealtime.test.js` (Vitest) verifies:
   - Socket.IO event handler unit tests (Python): `chat_message` saves to DB and publishes; `typing_start`/`typing_stop` broadcast without saving; `message_read` updates `is_read` field.
   - Widget tests (Vitest): typing indicator appears on `typing_start` event, auto-clears after 10s, clears on `typing_stop`; message status icon updates on `message_delivered` / `message_read` events; `localStorage` session restored on re-mount.
   - Latency benchmark script `scripts/benchmark_chat_latency.py` sends 100 messages via Socket.IO and asserts p95 round-trip < 200ms.

## Tasks / Subtasks

- [ ] **Task 1: Implement server-side Socket.IO event handlers** (AC: #1, #2, #3, #6)
  - [ ] Create `helpdesk/helpdesk/realtime/` directory with `__init__.py` and `chat_handlers.py`
  - [ ] Implement `handle_join_room(data)` — validates JWT via `validate_chat_token`, joins room `chat:{session_id}` via `frappe.realtime` room join; raises `frappe.AuthenticationError` on invalid token
  - [ ] Implement `handle_chat_message(data)` — validates JWT, sanitizes content via `frappe.utils.html_sanitize()`, creates `HD Chat Message` record (`sender_type`, `content`, `sent_at`, `session`), then calls `frappe.publish_realtime(event="chat_message", message=payload, room=f"chat:{session_id}")` with `{message_id, content, sender_type, sender_email, sent_at, status="sent"}`
  - [ ] Implement `handle_typing_start(data)` and `handle_typing_stop(data)` — validate JWT, publish `typing_start`/`typing_stop` event to room with `{sender_type, sender_name}`; do NOT persist to DB
  - [ ] Implement `handle_message_delivered(data)` — validate JWT; publish `message_status` event to room with `{message_id, status="delivered"}`
  - [ ] Implement `handle_message_read(data)` — validate JWT; set `frappe.db.set_value("HD Chat Message", message_id, "is_read", 1)`; publish `message_status` event with `{message_id, status="read"}` to room
  - [ ] Implement `handle_leave_room(data)` — leave room on disconnect
  - [ ] Register handlers in `hooks.py` under `socketio_handlers` (or the appropriate Frappe hook for Socket.IO)

- [ ] **Task 2: Extend `send_message` API for delivery confirmation** (AC: #2)
  - [ ] In `helpdesk/helpdesk/api/chat.py`, modify `send_message` response to include `{message_id, sent_at, status: "sent"}`
  - [ ] On the widget side (Task 5), use the returned `message_id` to track per-message status state
  - [ ] When the server publishes `chat_message` to the room, include `message_id` in the payload so recipients can emit `message_delivered` immediately upon receipt

- [ ] **Task 3: Implement agent response timeout background job** (AC: #5)
  - [ ] Create `helpdesk/helpdesk/chat/response_timeout.py`
  - [ ] Implement `check_unanswered_sessions()`:
    - Query `HD Chat Session` where `status="waiting"` and `started_at < now() - chat_response_timeout_seconds`
    - For each session with no agent message (check `HD Chat Message` for `sender_type="agent"`):
      - Insert `HD Chat Message` with `sender_type="system"`, `content="We're experiencing high volume. You can wait or leave a message and we'll email you."`
      - Publish `frappe.publish_realtime(event="chat_message", message=system_msg_payload, room=f"chat:{session.name}")`
      - Update session to add a `timeout_notified_at` timestamp to avoid duplicate messages
  - [ ] Read timeout from `frappe.db.get_single_value("HD Settings", "chat_response_timeout_seconds")` with fallback to `120`
  - [ ] Register in `hooks.py` scheduler as `"*/1 * * * *"` (every 1 minute) on the `short` queue

- [ ] **Task 4: Add `chat_response_timeout_seconds` to HD Settings** (AC: #5)
  - [ ] Add `chat_response_timeout_seconds` (Int, default 120) to `HD Settings` DocType JSON at `helpdesk/helpdesk/doctype/hd_settings/hd_settings.json`
  - [ ] Add a migration patch at `helpdesk/patches/v1_phase1/add_chat_response_timeout_to_settings.py` that sets the default value via `frappe.db.set_value("HD Settings", None, "chat_response_timeout_seconds", 120)`
  - [ ] Register patch in `patches.txt`

- [ ] **Task 5: Extend `ChatView.vue` in the widget for full real-time features** (AC: #1, #2, #3, #4)
  - [ ] In `widget/src/components/ChatView.vue` (created in Story 3.3), add:
    - On receipt of `chat_message` event: append message to list; emit `message_delivered` back to server with `{session_id, message_id, token}`
    - On receipt of `message_status` event: update the corresponding message's status icon (sent → delivered → read)
    - On receipt of `typing_start` event: show `TypingIndicator` component; start a 10-second `clearTimeout` timer — if no new `typing_start` arrives within 10s, hide the indicator
    - On receipt of `typing_stop` event: immediately clear the typing indicator and cancel the auto-clear timer
    - On input keydown: emit `typing_start` to server (debounced — emit at most once per 2s to avoid flooding); emit `typing_stop` on blur or after message send
    - On scroll: if message is visible (Intersection Observer or scroll position check), emit `message_read` for each unread message from the other party
  - [ ] When panel becomes visible (`isOpen` transitions to `true`): emit `message_read` for all unread messages in the current view
  - [ ] Message status icon component: `<StatusIcon :status="msg.status" />` with three states rendered as inline SVG checkmarks

- [ ] **Task 6: Implement `TypingIndicator.vue` in the widget** (AC: #3)
  - [ ] Create `widget/src/components/TypingIndicator.vue`
  - [ ] Renders three animated dots using CSS keyframe animation (bounce or fade) — self-contained CSS, no Tailwind
  - [ ] Shows `"{senderName} is typing…"` text alongside the dots
  - [ ] Accepts `senderName` prop (string); hidden by default, shown when `visible` prop is `true`
  - [ ] Accessible: `role="status"` and `aria-live="polite"` on the container (NFR-U-04, WCAG 2.1 AA)

- [ ] **Task 7: Extend `ChatMessageList.vue` (agent interface) for real-time features** (AC: #1, #2, #3)
  - [ ] In `desk/src/components/chat/ChatMessageList.vue` (created in Story 3.3 or 3.5), add the same real-time event handling as Task 5:
    - `chat_message` event → append message, emit `message_delivered`
    - `message_status` event → update status icon on sent messages
    - `typing_start` / `typing_stop` → show/hide typing indicator
    - Scroll-based `message_read` emission
  - [ ] Use Frappe's existing Socket.IO client (NOT the widget's bundled `socket.io-client`) — access via `import { socket } from "@/socket"` or the existing Frappe realtime mechanism
  - [ ] Agent chat joins room `chat:{session_id}` using `socket.emit("join_room", { room: "chat:"+sessionId })` after agent accepts the session

- [ ] **Task 8: Session persistence in widget on page reload** (AC: #4)
  - [ ] In `widget/src/Widget.vue`, on mount:
    - Read `localStorage.getItem("hd_chat_session")`; parse JSON to get `{session_id, token, status}`
    - If `status !== "ended"`: call `GET /api/method/helpdesk.api.chat.get_messages?session_id={session_id}&token={token}` to load message history; set `activeSession` ref and render `ChatView` directly (skip `PreChatForm`)
    - Call `connectSocket(siteUrl, session_id, token)` and rejoin room `chat:{session_id}`
  - [ ] Ensure `localStorage` is updated when session `status` changes to `"ended"` (so subsequent page loads show `PreChatForm`)
  - [ ] Add `get_messages` endpoint to `helpdesk/helpdesk/api/chat.py` if not already present from Story 3.2: accepts `{session_id, token}`, validates JWT, returns list of `HD Chat Message` records ordered by `sent_at`

- [ ] **Task 9: Write backend unit tests** (AC: #7)
  - [ ] Create `helpdesk/tests/test_chat_realtime.py`
  - [ ] Test `handle_chat_message`: assert `HD Chat Message` is created with sanitized content; assert `frappe.publish_realtime` is called with correct room and payload (mock `frappe.publish_realtime`)
  - [ ] Test `handle_typing_start`: assert `frappe.publish_realtime` is called with `typing_start` event; assert NO DB record is created
  - [ ] Test `handle_message_read`: assert `HD Chat Message.is_read` is set to `1`; assert `message_status` event is published with `status="read"`
  - [ ] Test `check_unanswered_sessions`: with a session in `waiting` state older than 120s with no agent message — assert system message is inserted and published; with a recent session — assert no message is inserted
  - [ ] Achieve ≥80% line coverage on `chat_handlers.py` and `response_timeout.py` (NFR-M-01)

- [ ] **Task 10: Write widget Vitest tests** (AC: #7)
  - [ ] Create `widget/src/__tests__/ChatRealtime.test.js`
  - [ ] Test: typing indicator shows when `typing_start` event received; auto-clears after 10s (use `vi.useFakeTimers()`); clears immediately on `typing_stop`
  - [ ] Test: message status icon cycles from `"sent"` → `"delivered"` → `"read"` as corresponding `message_status` events arrive
  - [ ] Test: `message_delivered` emitted when `chat_message` is received from the other party
  - [ ] Test: `message_read` emitted when panel becomes visible with unread messages
  - [ ] Test: localStorage session restored — mount `Widget.vue` with mocked `localStorage` containing `{session_id: "abc", token: "tok", status: "active"}`; assert `ChatView` is rendered (not `PreChatForm`); assert `connectSocket` is called with `"abc"` and `"tok"`
  - [ ] Add to existing `test:widget` Vitest run

- [ ] **Task 11: Latency benchmark script** (AC: #1, #7)
  - [ ] Create `scripts/benchmark_chat_latency.py`
  - [ ] Script sends 100 `chat_message` events over Socket.IO (using `python-socketio` client), measures round-trip time (time from emit to receipt of `chat_message` event back on the same socket), prints p50/p95/p99 statistics
  - [ ] Add a CI assertion: `assert p95 < 200` (print PASS/FAIL)
  - [ ] Document required setup (`pip install python-socketio`, running dev server) in a docstring

## Dev Notes

### Architecture Patterns

This story implements the real-time communication layer described in **FR-LC-02** and **NFR-P-03**. It builds directly on the session management infrastructure from Story 3.2 and the widget foundation from Story 3.3.

**Key architectural constraints:**

- **Socket.IO rooms** — All events are published to room `chat:{session_id}` per AR-07. The room naming convention is enforced: never use session numeric IDs directly — always the prefixed form.
- **Frappe realtime** — Server-side publishing uses `frappe.publish_realtime(event, message, room)`. Do not use `frappe.publish_realtime(user=...)` for chat events — always use `room=` to scope to the session.
- **JWT validation on every event** — Every server-side Socket.IO handler must call `validate_chat_token(token, session_id)` before processing. Never trust the socket's session state alone.
- **No DB writes for typing events** — `typing_start` and `typing_stop` are ephemeral signals. They MUST NOT be persisted to `HD Chat Message`. Only `chat_message`, `message_delivered`, and `message_read` result in DB operations.
- **Widget vs. agent Socket.IO client** — The widget bundles its own `socket.io-client` (from Story 3.3's `widget/src/socket.js`). The agent interface uses Frappe's globally available Socket.IO instance. Do not merge these or import `socket.io-client` in `desk/`.

### Socket.IO Event Schema

```python
# helpdesk/helpdesk/realtime/chat_handlers.py

# Events received from clients:
# join_room:        {session_id: str, token: str}
# chat_message:     {session_id: str, token: str, content: str, attachment: str|None}
# typing_start:     {session_id: str, token: str, sender_name: str}
# typing_stop:      {session_id: str, token: str}
# message_delivered:{session_id: str, token: str, message_id: str}
# message_read:     {session_id: str, token: str, message_ids: list[str]}
# leave_room:       {session_id: str}

# Events published to room chat:{session_id}:
# chat_message:     {message_id: str, content: str, sender_type: str, sender_email: str,
#                    sender_name: str, sent_at: str, status: "sent"}
# typing_start:     {sender_type: str, sender_name: str}
# typing_stop:      {sender_type: str}
# message_status:   {message_id: str, status: "delivered"|"read"}
# session_ended:    {reason: str}  (from Story 3.2)
```

### Backend Handler Pattern

```python
# helpdesk/helpdesk/realtime/chat_handlers.py
import frappe
from helpdesk.helpdesk.chat.jwt_helper import validate_chat_token


def handle_chat_message(data):
    """Receive, validate, persist, and broadcast a chat message."""
    session_id = data.get("session_id")
    token = data.get("token")
    content = data.get("content", "")

    # 1. Authenticate
    if not validate_chat_token(token, session_id):
        raise frappe.AuthenticationError("Invalid chat token")

    # 2. Sanitize and persist
    safe_content = frappe.utils.html_sanitize(content)
    session = frappe.get_doc("HD Chat Session", session_id)
    sender_type = _get_sender_type(token, session)

    msg = frappe.get_doc({
        "doctype": "HD Chat Message",
        "session": session_id,
        "sender_type": sender_type,
        "sender_email": _get_sender_email(token),
        "content": safe_content,
    })
    msg.insert(ignore_permissions=True)

    # 3. Broadcast to room
    frappe.publish_realtime(
        event="chat_message",
        message={
            "message_id": msg.name,
            "content": safe_content,
            "sender_type": sender_type,
            "sender_email": msg.sender_email,
            "sent_at": str(msg.sent_at),
            "status": "sent",
        },
        room=f"chat:{session_id}",
    )
    return {"message_id": msg.name, "sent_at": str(msg.sent_at), "status": "sent"}


def handle_typing_start(data):
    """Broadcast typing indicator — no DB persistence."""
    session_id = data.get("session_id")
    token = data.get("token")
    if not validate_chat_token(token, session_id):
        raise frappe.AuthenticationError("Invalid chat token")

    frappe.publish_realtime(
        event="typing_start",
        message={"sender_name": data.get("sender_name", ""), "sender_type": _get_sender_type(token, None)},
        room=f"chat:{session_id}",
    )


def handle_message_read(data):
    """Mark messages as read and notify the original sender."""
    session_id = data.get("session_id")
    token = data.get("token")
    message_ids = data.get("message_ids", [])

    if not validate_chat_token(token, session_id):
        raise frappe.AuthenticationError("Invalid chat token")

    for message_id in message_ids:
        frappe.db.set_value("HD Chat Message", message_id, "is_read", 1)
        frappe.publish_realtime(
            event="message_status",
            message={"message_id": message_id, "status": "read"},
            room=f"chat:{session_id}",
        )
    frappe.db.commit()
```

### Typing Indicator Vue Pattern

```javascript
// widget/src/components/TypingIndicator.vue
<template>
  <div
    v-if="visible"
    class="hd-typing"
    role="status"
    aria-live="polite"
    :aria-label="`${senderName} is typing`"
  >
    <span class="hd-dot" />
    <span class="hd-dot" />
    <span class="hd-dot" />
    <span class="hd-typing-label">{{ senderName }} is typing…</span>
  </div>
</template>

<style scoped>
/* Bounce animation — no Tailwind dependency */
.hd-dot {
  display: inline-block;
  width: 6px; height: 6px;
  border-radius: 50%;
  background: #94a3b8;
  animation: hd-bounce 1.2s infinite ease-in-out;
}
.hd-dot:nth-child(2) { animation-delay: 0.2s; }
.hd-dot:nth-child(3) { animation-delay: 0.4s; }
@keyframes hd-bounce {
  0%, 80%, 100% { transform: scale(0.8); opacity: 0.5; }
  40%            { transform: scale(1.2); opacity: 1;   }
}
</style>
```

### ChatView Typing Event Pattern

```javascript
// widget/src/components/ChatView.vue (additions)

// In setup():
const typingTimeout = ref(null)
const remoteTyping = ref({ visible: false, senderName: '' })

// On socket event:
socket.on('typing_start', ({ sender_name }) => {
  remoteTyping.value = { visible: true, senderName: sender_name }
  clearTimeout(typingTimeout.value)
  typingTimeout.value = setTimeout(() => {
    remoteTyping.value.visible = false
  }, 10_000)
})

socket.on('typing_stop', () => {
  clearTimeout(typingTimeout.value)
  remoteTyping.value.visible = false
})

// On input keydown (debounced):
let localTypingTimer = null
function onInputKeydown() {
  if (!localTypingTimer) {
    socket.emit('typing_start', { session_id: props.sessionId, token: props.token, sender_name: customerName.value })
    localTypingTimer = setTimeout(() => { localTypingTimer = null }, 2000)
  }
}

// On message send:
function sendMessage() {
  clearTimeout(localTypingTimer)
  localTypingTimer = null
  socket.emit('typing_stop', { session_id: props.sessionId, token: props.token })
  // ... send message logic
}
```

### Message Status Icon Pattern

```javascript
// widget/src/components/StatusIcon.vue (inline SVG)
// status: 'sending' | 'sent' | 'delivered' | 'read'
// - 'sending': spinner
// - 'sent':    single grey checkmark ✓
// - 'delivered': double grey checkmarks ✓✓
// - 'read':   double blue checkmarks ✓✓ (color: #3B82F6)
```

### Response Timeout Background Job

```python
# helpdesk/helpdesk/chat/response_timeout.py
import frappe
from frappe.utils import now_datetime, add_to_date


def check_unanswered_sessions():
    """Send auto-message to sessions with no agent response within timeout."""
    timeout_seconds = frappe.db.get_single_value(
        "HD Settings", "chat_response_timeout_seconds"
    ) or 120

    cutoff = add_to_date(now_datetime(), seconds=-timeout_seconds)

    # Find waiting sessions created before the cutoff, not yet notified
    sessions = frappe.db.get_all(
        "HD Chat Session",
        filters={
            "status": "waiting",
            "started_at": ["<", cutoff],
            "timeout_notified_at": ["is", "not set"],
        },
        fields=["name", "customer_name"],
    )

    for session in sessions:
        # Verify no agent message exists
        agent_msg_count = frappe.db.count(
            "HD Chat Message",
            {"session": session.name, "sender_type": "agent"},
        )
        if agent_msg_count > 0:
            continue  # Agent already responded, skip

        # Insert system message
        msg = frappe.get_doc({
            "doctype": "HD Chat Message",
            "session": session.name,
            "sender_type": "system",
            "content": (
                "We're experiencing high volume. "
                "You can wait or leave a message and we'll email you."
            ),
        })
        msg.insert(ignore_permissions=True)

        # Publish to widget
        frappe.publish_realtime(
            event="chat_message",
            message={
                "message_id": msg.name,
                "content": msg.content,
                "sender_type": "system",
                "sent_at": str(msg.sent_at),
                "status": "sent",
            },
            room=f"chat:{session.name}",
        )

        # Mark as notified to prevent duplicate messages
        frappe.db.set_value(
            "HD Chat Session", session.name, "timeout_notified_at", now_datetime()
        )

    frappe.db.commit()
    frappe.logger().info(f"[Chat Timeout] Processed {len(sessions)} session(s)")
```

### hooks.py Additions

```python
# helpdesk/hooks.py additions

# Socket.IO event handlers
socketio_handlers = {
    "join_room":          "helpdesk.helpdesk.realtime.chat_handlers.handle_join_room",
    "chat_message":       "helpdesk.helpdesk.realtime.chat_handlers.handle_chat_message",
    "typing_start":       "helpdesk.helpdesk.realtime.chat_handlers.handle_typing_start",
    "typing_stop":        "helpdesk.helpdesk.realtime.chat_handlers.handle_typing_stop",
    "message_delivered":  "helpdesk.helpdesk.realtime.chat_handlers.handle_message_delivered",
    "message_read":       "helpdesk.helpdesk.realtime.chat_handlers.handle_message_read",
    "leave_room":         "helpdesk.helpdesk.realtime.chat_handlers.handle_leave_room",
}

# Scheduler additions (in existing scheduler_events dict)
scheduler_events = {
    # ... existing entries ...
    "cron": {
        # ... existing cron entries ...
        "*/1 * * * *": [
            "helpdesk.helpdesk.chat.response_timeout.check_unanswered_sessions"
        ],
    },
}
```

### Prerequisites and Dependencies

- **Story 3.1** (Channel Abstraction Layer) — `ChatAdapter` and `ChannelNormalizer` used by `handle_chat_message` for first-message ticket creation.
- **Story 3.2** (Chat Session Management Backend) — `HD Chat Session`, `HD Chat Message` DocTypes; `validate_chat_token()` from `helpdesk/helpdesk/chat/jwt_helper.py`; `send_message` API endpoint. The `timeout_notified_at` field must be added to `HD Chat Session` in this story's migration patch.
- **Story 3.3** (Embeddable Chat Widget) — `ChatView.vue`, `socket.js` in `widget/src/` are extended (not replaced) by Tasks 5 and 6.
- **`chat_enabled` feature flag** — All Socket.IO handlers must check `frappe.db.get_single_value("HD Settings", "chat_enabled")` and return early if disabled.

### Project Structure Notes

**New files created by this story:**
```
helpdesk/
├── helpdesk/
│   ├── realtime/
│   │   ├── __init__.py
│   │   └── chat_handlers.py          # Socket.IO event handlers (Task 1)
│   ├── chat/
│   │   └── response_timeout.py       # Timeout background job (Task 3)
│   └── doctype/
│       └── hd_settings/
│           └── hd_settings.json      # Add chat_response_timeout_seconds field (Task 4)
├── patches/
│   └── v1_phase1/
│       └── add_chat_response_timeout_to_settings.py  # Migration patch (Task 4)
└── tests/
    └── test_chat_realtime.py          # Backend unit tests (Task 9)

widget/
└── src/
    ├── components/
    │   ├── ChatView.vue               # Extended with real-time features (Task 5)
    │   ├── TypingIndicator.vue        # New component (Task 6)
    │   └── StatusIcon.vue             # New message status icon (Task 5)
    └── __tests__/
        └── ChatRealtime.test.js       # Widget Vitest tests (Task 10)

desk/
└── src/
    └── components/
        └── chat/
            └── ChatMessageList.vue    # Extended for agent interface (Task 7)

scripts/
└── benchmark_chat_latency.py          # Latency benchmark (Task 11)
```

**Modified files:**
```
helpdesk/hooks.py                      # socketio_handlers + scheduler_events (Tasks 1, 3)
helpdesk/patches.txt                   # Register migration patch (Task 4)
helpdesk/helpdesk/api/chat.py          # get_messages endpoint if not from 3.2 (Task 8)
```

**Naming conventions followed:**
- DocType fields: `snake_case` (e.g., `chat_response_timeout_seconds`, `timeout_notified_at`)
- Vue components: PascalCase (`TypingIndicator.vue`, `StatusIcon.vue`)
- Socket.IO events: `snake_case` (`chat_message`, `typing_start`, `message_read`) per architecture naming rules
- API module: `helpdesk/api/chat.py` (existing module, additive changes only)
- Test file: `test_chat_realtime.py` in `helpdesk/tests/` following existing test structure

### Security Notes

- **NFR-SE-02**: All Socket.IO handlers validate JWT before processing. Token is never logged.
- **NFR-SE-06**: `handle_chat_message` always calls `frappe.utils.html_sanitize()` on content before DB insert. Raw content is never stored.
- Typing events carry the sender's token for authentication but are not persisted — there is no typing history in the DB.
- The `get_messages` endpoint enforces JWT ownership — a customer cannot fetch messages from another customer's session.

### References

- Architecture ADR-07: Channel Abstraction Layer [Source: `_bmad-output/planning-artifacts/architecture.md#ADR-07`]
- Architecture ADR-08: API Design — `helpdesk/api/chat.py` endpoints [Source: `_bmad-output/planning-artifacts/architecture.md#ADR-08`]
- Architecture ADR-11: State Management — Pinia `chat.ts` store [Source: `_bmad-output/planning-artifacts/architecture.md#ADR-11`]
- Architecture ADR-12: Background Job Architecture — `short` queue for real-time jobs [Source: `_bmad-output/planning-artifacts/architecture.md#ADR-12`]
- Architecture Naming Patterns: Socket.IO events snake_case [Source: `_bmad-output/planning-artifacts/architecture.md#Naming Patterns`]
- FR-LC-02: Real-time chat with <200ms latency, typing indicators, message status, session persistence, timeout handling [Source: `_bmad-output/planning-artifacts/epics.md#Functional Requirements`]
- NFR-P-03: Live chat message delivery <200ms end-to-end (95th percentile) [Source: `_bmad-output/planning-artifacts/epics.md#Non-Functional Requirements`]
- NFR-SE-02: Chat sessions authenticated via token [Source: `_bmad-output/planning-artifacts/epics.md#Non-Functional Requirements`]
- NFR-SE-06: All chat messages sanitized server-side before storage [Source: `_bmad-output/planning-artifacts/epics.md#Non-Functional Requirements`]
- NFR-M-01: Minimum 80% unit test coverage on all new backend code [Source: `_bmad-output/planning-artifacts/epics.md#Non-Functional Requirements`]
- NFR-U-04: WCAG 2.1 AA compliance for all new UI components [Source: `_bmad-output/planning-artifacts/epics.md#Non-Functional Requirements`]
- AR-07: Socket.IO room naming convention: `chat:{session_id}` [Source: `_bmad-output/planning-artifacts/epics.md#Additional Requirements`]
- Epic 3 Story 3.4 acceptance criteria [Source: `_bmad-output/planning-artifacts/epics.md#Story 3.4: Real-Time Chat Communication`]
- Story 3.2 (prerequisite): Chat Session Management Backend [Source: `_bmad-output/implementation-artifacts/story-3.2-chat-session-management-backend.md`]
- Story 3.3 (prerequisite): Embeddable Chat Widget [Source: `_bmad-output/implementation-artifacts/story-3.3-embeddable-chat-widget.md`]

## Dev Agent Record

### Agent Model Used

claude-opus-4-5

### Debug Log References

### Completion Notes List

### File List
