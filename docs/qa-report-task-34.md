# QA Report: Task #34 — Story 3.5: Agent Chat Interface

**QA Date**: 2026-03-23
**QA Depth**: 1/1 (max depth)
**Tester**: QA Agent (Claude)
**Method**: API testing (curl), code review, backend unit tests

---

## Test Environment

- Backend: Frappe bench at `/home/ubuntu/frappe-bench`, site `helpdesk.localhost:8004`
- Frontend: Vue 3 SPA (no dist build in dev repo; served via bench assets)
- Login: Administrator / admin123
- Backend tests: 16/16 pass (`test_agent_chat_interface.py`)

---

## Acceptance Criteria Results

### AC1: New chat request visible in chat queue with desktop notification and unread badge, agent can accept

**FAIL (P1)** — Queue is always empty for agents.

**Evidence**: The Pinia chat store (`desk/src/stores/chat.ts:70`) fetches sessions via `helpdesk.api.chat.get_agent_sessions`. This API (`chat.py:715-719`) filters by `{"agent": agent_name, "status": ["in", ["waiting", "active"]]}`. Waiting sessions have `agent=null` (no agent assigned yet), so they **never** appear in the agent's session list.

- `curl get_sessions` returns 14 waiting sessions (correct, no agent filter)
- `curl get_agent_sessions` returns `[]` (empty — waiting sessions excluded by agent filter)
- Desktop notification logic and unread badge code are correctly implemented in the store (`_showDesktopNotification`, `_bindSocketEvents` for `chat_queue_new`)
- Accept button exists in ChatSession.vue (line 114) and calls `accept_session` API correctly
- `accept_session` API works correctly (enforces max_concurrent_chats, sets accepted_at, publishes realtime event)

**Partial PASS**: Socket-based `chat_queue_new` event would add sessions to the local list, but the initial page load fetches nothing. Agent must rely solely on realtime events to see queue items, which is fragile and breaks on page refresh.

### AC2: Up to 5 concurrent chats (configurable) with unread count badges and quick-switch

**PASS** (with caveat from AC1)

**Evidence**:
- `max_concurrent_chats` field added to HD Settings with default 5, verified in DB
- `accept_session` API (chat.py:614-623) correctly enforces the limit — test `test_max_concurrent_chats_enforced` passes
- Unread count badges shown in ChatDashboard.vue (line 63-68) with blue circle, "9+" cap
- Quick-switch: clicking sessions in sidebar calls `selectSession()` which updates `currentSessionId`
- Active sessions panel with count badge (line 43)

### AC3: Chat transfer to another agent/team with context preserved

**PASS**

**Evidence**:
- `transfer_session` API (chat.py:284-337) correctly updates agent, appends system message, publishes realtime events to both session room and new agent's room
- TransferDialog.vue fetches `get_transfer_targets` (excludes self, excludes offline agents) — API returns online agents correctly
- Transfer button visible for active sessions (ChatSession.vue line 30-32)
- `test_excludes_offline_agents`, `test_excludes_self`, `test_includes_online_agents` all pass
- Context preserved: session document retains all messages and ticket link

### AC4: Availability toggle: Online/Away/Offline; Away/Offline agents not routed new chats

**PASS**

**Evidence**:
- AgentAvailability.vue provides dropdown with Online/Away/Offline options
- `set_availability` API correctly validates input and updates HD Agent record
- `get_availability` (chat.py:359) filters by `chat_availability="Online"` — verified returns `{"available": true}` when online agents exist
- `get_transfer_targets` (chat.py:768-775) filters by `chat_availability="Online"` — offline/away agents excluded
- Tests pass: `test_set_online`, `test_set_away`, `test_set_offline`, `test_invalid_availability_raises`, `test_not_available_when_all_away`

### CRITICAL: Agent cannot send messages (P0)

**FAIL (P0)**

**Evidence**: ChatSession.vue (line 196-199) sends messages via `send_message` API with `token: "__agent__"`. The `send_message` function (chat.py:142) **always** calls `validate_chat_token(token, session_id)` which rejects `"__agent__"` as invalid JWT.

Verified directly:
```
$ python3: validate_chat_token('__agent__', 'test123')
ERROR: Invalid chat session token: Not enough segments
```

The `send_message` API has no agent bypass — it treats all callers as customers requiring JWT authentication. This means agents cannot send any messages through the chat interface, making the entire feature non-functional for two-way communication.

---

## Backend Test Results

```
Ran 16 tests in 2.421s — OK

TestAcceptSession: 3/3 pass
TestSetAvailability: 5/5 pass
TestGetAgentSessions: 2/2 pass
TestGetTransferTargets: 3/3 pass
TestGetAvailabilityUpdated: 2/2 pass
```

Note: Backend tests for `accept_session` create sessions with agent pre-assigned, so they don't catch the queue visibility bug. The `send_message` tests use customer JWT tokens, not agent tokens, so they don't catch the agent send bug.

---

## Code Review Notes

### Files Reviewed
- `helpdesk/api/chat.py` — all new endpoints (accept_session, set_availability, get_agent_sessions, get_transfer_targets)
- `desk/src/stores/chat.ts` — Pinia store with socket bindings
- `desk/src/pages/chat/ChatDashboard.vue` — main dashboard layout
- `desk/src/pages/chat/ChatSession.vue` — individual session view
- `desk/src/components/chat/AgentAvailability.vue` — availability dropdown
- `desk/src/components/chat/TransferDialog.vue` — transfer dialog
- `desk/src/router/index.ts` — chat routes
- `desk/src/components/layouts/layoutSettings.ts` — sidebar entry
- `helpdesk/patches/v1_phase1/add_chat_availability_to_agent.py` — migration

### Positive Observations
- Clean component architecture with proper separation of concerns
- Socket event bindings well-structured (chat_queue_new, chat_assigned, chat_message, session_ended, typing indicators, availability_changed)
- Desktop notification permission requested on init
- Proper error handling with toast notifications
- Transfer dialog correctly excludes self and offline agents
- Schema changes properly registered in patches.txt with migration

### Security Note
- `v-html` used for message content (ChatSession.vue:72) — acceptable because `_sanitize()` in chat.py uses `frappe.utils.html_utils.clean_html()` (NFR-SE-06)

---

## Issues Summary

| # | Severity | Description | File | Line |
|---|----------|-------------|------|------|
| 1 | **P0** | Agent cannot send messages — `send_message` always validates JWT, no agent bypass | `helpdesk/api/chat.py` | 142 |
| 2 | **P1** | Queue always empty — `get_agent_sessions` filters by agent, excludes unassigned waiting sessions | `helpdesk/api/chat.py` | 715-719 |

---

## Verdict

**FAIL** — 2 critical issues found (1x P0, 1x P1). Fix task created.
