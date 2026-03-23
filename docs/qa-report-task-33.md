# QA Report: Story 3.4 — Real-Time Chat Communication

**Task**: #33 (QA task #230)
**Date**: 2026-03-23
**Tester**: Claude QA Agent (Opus)
**Status**: FAIL (1 P0 issue found)

---

## Acceptance Criteria Results

### AC #1: Message delivery <200ms end-to-end (95th percentile)
**Result: PASS**

- Backend API `send_message` responds in <200ms (tested via curl).
- `frappe.publish_realtime` broadcasts to Socket.IO room `chat:{session_id}` with ~1-5ms local overhead.
- Benchmark script provided at `scripts/benchmark_chat_latency.py`.
- **Note**: The frontend `ChatView.vue` calls the wrong API path (see P0 below), so while the backend meets the latency target, messages cannot actually be sent from the widget.

### AC #2: Message status: sent (single check), delivered (double check), read (blue double check)
**Result: FAIL (blocked by P0)**

- `StatusIcon.vue` correctly renders three states with SVG icons and proper aria labels.
- One-way state machine in `ChatView.vue` lines 113-117 prevents status regression (`sent→delivered→read`).
- Backend `handle_message_delivered` and `handle_message_read` properly broadcast `message_status` events.
- **BLOCKED**: `ChatView.vue` uses wrong API path `helpdesk.helpdesk.api.chat.*` — all status-related API calls (`message_delivered`, `mark_messages_read`) fail with `No module named 'helpdesk.helpdesk.api'`.

### AC #3: Typing indicator (three animated dots) auto-clears after 10s inactivity
**Result: FAIL (blocked by P0)**

- `TypingIndicator.vue` component is well-implemented with accessibility (`role="status"`, `aria-live="polite"`).
- Auto-clear timer in `ChatView.vue` lines 127-129 correctly set to 10,000ms.
- Debounce on local typing events (2s) prevents excessive API calls.
- Backend `handle_typing_start`/`handle_typing_stop` correctly broadcast without DB writes.
- **BLOCKED**: `callApi('typing_start', ...)` and `callApi('typing_stop', ...)` use wrong path via `callApi()` at line 256.

### AC #4: Chat session persists across page navigation via localStorage
**Result: PASS**

- `Widget.vue` reads/writes `hd_chat_session` key in localStorage (lines 65, 98, 103).
- Session restored on mount if `status !== 'ended'`.
- Session cleared when session ends.
- 4 Vitest tests verify localStorage persistence (ChatRealtime.test.js + Widget.test.js).

### AC #5: No agent response within 2min timeout: auto-message shown
**Result: PASS**

- `response_timeout.py` implements `check_unanswered_sessions()` cron job.
- Registered in hooks.py at `*/1 * * * *` schedule.
- Correctly skips already-notified sessions and sessions with agent messages.
- `timeout_notified_at` field verified present on HD Chat Session.
- `chat_response_timeout_seconds` defaults to 120 in HD Settings.
- 4 backend tests pass for this feature.

---

## P0 Issue: Wrong API Path in ChatView.vue

**Severity: P0 — All real-time chat features are broken**

`ChatView.vue` uses `helpdesk.helpdesk.api.chat.*` (double `helpdesk`) instead of the correct `helpdesk.api.chat.*`. This affects three locations:

| Line | Function | API Method | Impact |
|------|----------|-----------|--------|
| 57 | `fetchHistory()` | `get_messages` | Chat history won't load |
| 166 | `sendMessage()` | `send_message` | Customer can't send messages |
| 256 | `callApi()` | All others | typing_start, typing_stop, message_delivered, mark_messages_read all broken |

**Evidence**:
```
$ curl -s -X POST http://helpdesk.localhost:8004/api/method/helpdesk.helpdesk.api.chat.send_message ...
→ {"exc_type":"ValidationError","_server_messages":"[\"Failed to get method ... No module named 'helpdesk.helpdesk.api'\"]"}

$ curl -s -X POST http://helpdesk.localhost:8004/api/method/helpdesk.api.chat.send_message ...
→ {"message":{"message_id":"61dc5366199616c427f9","sent_at":"2026-03-24 04:15:14.188877","status":"sent"}}
```

Other components (`PreChatForm.vue`, `OfflineForm.vue`, `BrandingHeader.vue`, `Widget.vue`) correctly use `helpdesk.api.chat.*`.

---

## P3 Issues (informational, no fix task needed)

1. **Deprecation warning**: Tests use `frappe.db.set_value("HD Settings", None, ...)` which is deprecated for single doctypes. Should use `frappe.db.set_single_value()`. (7 occurrences in `test_chat_realtime.py`)

---

## Test Results

| Suite | Tests | Result |
|-------|-------|--------|
| Backend: `test_chat_realtime.py` | 16 | All PASS |
| Frontend: `ChatRealtime.test.js` | 20 | All PASS |
| Frontend: `Widget.test.js` | (existing) | Not re-run (no changes) |

---

## API Endpoint Verification

| Endpoint | Path | Status |
|----------|------|--------|
| `create_session` | `helpdesk.api.chat.create_session` | PASS (returns session_id + JWT) |
| `send_message` | `helpdesk.api.chat.send_message` | PASS (returns message_id + status) |
| `get_sessions` | `helpdesk.api.chat.get_sessions` | PASS (agent-only, returns list) |
| `typing_start` | `helpdesk.api.chat.typing_start` | PASS (returns {ok: true}) |
| `typing_stop` | `helpdesk.api.chat.typing_stop` | PASS (returns {ok: true}) |
| `message_delivered` | `helpdesk.api.chat.message_delivered` | PASS (returns {ok: true}) |
| `mark_messages_read` | `helpdesk.api.chat.mark_messages_read` | PASS (returns {ok: true}) |

---

## Code Quality Notes

- **Security**: JWT validation on every handler (NFR-SE-02). Cross-session injection blocked in `handle_message_read`. Content sanitized before storage.
- **Architecture**: Clean separation between REST endpoints (`api/chat.py`) and realtime handlers (`realtime/chat_handlers.py`).
- **Accessibility**: TypingIndicator has `role="status"` + `aria-live="polite"`. StatusIcon has `aria-label` and `title` attributes.
- **Error handling**: Real-time broadcast failures wrapped in try/except with pass (NFR-A-01 — broadcast failure must not block delivery).

---

## Summary

| Category | Count |
|----------|-------|
| P0 (Critical) | 1 |
| P1 (Major) | 0 |
| P2 (Minor) | 0 |
| P3 (Info) | 1 |

**Verdict**: FAIL — P0 bug blocks all ChatView.vue functionality. Fix required.
