# Story 3.5: Agent Chat Interface

Status: ready-for-dev

<!-- Note: Validation is optional. Run validate-create-story for quality check before dev-story. -->

## Story

As a support agent,
I want to handle multiple simultaneous chat conversations from my workspace,
so that I can efficiently serve chat customers alongside ticket work.

## Acceptance Criteria

1. **New chat request visible in queue with desktop notification and unread badge; agent can accept** — When a chat session transitions to `status="waiting"` and the agent is `Online`, the session appears in `ChatDashboard.vue`'s queue panel without page refresh (via Socket.IO event `agent_chat_request` published to room `agent:{agent_email}`). The browser shows a desktop notification (Web Notifications API, `Notification.requestPermission()`) with the customer name and first message preview. The unread badge on the chat queue nav item increments. The agent can click "Accept" to claim the session, which calls `POST /api/method/helpdesk.api.chat.accept_session` and transitions the `HD Chat Session.status` to `"active"` with `agent` set to the accepting agent's email (FR-LC-04, AR-07).

2. **Up to 5 concurrent active chats with unread count badges and quick-switch** — The Pinia `chat.ts` store tracks `activeSessions: ChatSession[]` (max 5, configurable via `HD Settings.max_concurrent_chats`, default `5`). Each session tab in `ChatDashboard.vue` displays an unread count badge that increments when a `chat_message` event arrives for a non-visible session. The agent can switch between sessions by clicking a tab — the `activeSessionId` ref in the store updates and `ChatSession.vue` renders the corresponding conversation. When a session is already at max concurrency, new incoming chats are shown in the queue but the agent cannot accept until a slot is freed (FR-LC-04, UX-DR-12).

3. **Chat transfer to another agent or team with full context preserved** — From `ChatSession.vue`, the agent clicks "Transfer" which opens a `TransferDialog.vue` modal. The agent selects a target agent (online/away status shown) or team from a dropdown populated via `GET /api/method/helpdesk.api.chat.get_transfer_targets`. On confirm, `POST /api/method/helpdesk.api.chat.transfer_session` is called with `{session_id, target_type: "agent"|"team", target}`. The server: updates `HD Chat Session.agent` (or assigns to team queue), adds a system message `"Chat transferred to {target_name}"` visible to both parties, and publishes a `chat_transferred` Socket.IO event to room `chat:{session_id}` so the widget informs the customer. The receiving agent gets a `agent_chat_request` event (FR-LC-04).

4. **Availability toggle: Online/Away/Offline; Away/Offline agents not routed new chats** — `AgentAvailability.vue` renders a dropdown (green dot = Online, yellow dot = Away, red dot = Offline). Selecting a status calls `POST /api/method/helpdesk.api.chat.set_availability` which sets `HD Agent.chat_availability` on the agent's record and publishes availability change to room `agent:{agent_email}`. The session assignment logic in `accept_session` and the chat routing in `HD Chat Session` creation checks `HD Agent.chat_availability != "Offline"` and `!= "Away"` before routing new sessions to an agent. Away/Offline agents are hidden from the transfer target list (FR-LC-04).

5. **Chat store state management** — `desk/src/stores/chat.ts` exposes: `activeSessions`, `queuedSessions`, `availability`, `unreadCounts: Record<sessionId, number>`, `activeSessionId`. Actions: `acceptSession`, `transferSession`, `setAvailability`, `markRead`, `addMessage`. The store subscribes to Socket.IO events on `agent:{agent_email}` room and per `chat:{session_id}` rooms for active sessions. All state is reactive via Pinia (ADR-11).

6. **`ChatDashboard.vue` page with queue and session tabs** — The page at `/helpdesk/chat` renders: a left sidebar listing queued sessions (awaiting agent) and active session tabs with unread badges; a main panel rendering the active `ChatSession.vue`; the `AgentAvailability.vue` toggle in the top bar. If `chat_enabled` feature flag in HD Settings is `false`, the page redirects to `/helpdesk` with a toast: "Chat is not enabled" (FR-LC-04, AR-06).

7. **`ChatSession.vue` page for individual conversations** — Accessible at `/helpdesk/chat/:sessionId`. Renders: `ChatMessageList.vue` (message history), `ChatInput.vue` (message input with attachment support), Transfer button, End Chat button. End Chat calls `POST /api/method/helpdesk.api.chat.end_session` which sets `status="ended"`, publishes `session_ended` to room `chat:{session_id}`, and the associated HD Ticket remains open for email follow-up (Story 3.6 dependency).

8. **Vue routes registered for `/helpdesk/chat` and `/helpdesk/chat/:sessionId`** — Two named routes added to `desk/src/router/index.ts` (or the router module file): `{ path: '/helpdesk/chat', component: ChatDashboard, name: 'ChatDashboard' }` and `{ path: '/helpdesk/chat/:sessionId', component: ChatSession, name: 'ChatSession' }`. Routes use lazy-loading: `component: () => import('@/pages/chat/ChatDashboard.vue')`. Route guard checks `chat_enabled` setting and agent authentication (ADR-09).

9. **Desktop notification permission requested once** — On first visit to `/helpdesk/chat`, if `Notification.permission === "default"`, the app requests permission with a single non-blocking prompt (not a modal — use the browser's native permission dialog). If denied, chat requests still show in the queue UI with visual badge; no error is thrown. Permission state stored in `localStorage` so re-request is not made on subsequent visits (FR-LC-04).

10. **Backend: `accept_session`, `transfer_session`, `set_availability`, `get_transfer_targets` API endpoints** — All four methods in `helpdesk/api/chat.py` are `@frappe.whitelist()`, require Agent role, and validate session ownership before mutation. `accept_session` checks concurrent chat limit against `HD Settings.max_concurrent_chats`. `transfer_session` inserts a system `HD Chat Message` for audit trail. `set_availability` updates `HD Agent.chat_availability` (Select field: Online/Away/Offline). `get_transfer_targets` returns online agents (excluding self) and all teams (ADR-08).

11. **Backend: `HD Agent.chat_availability` field and routing logic** — A `chat_availability` Select field (values: "Online", "Away", "Offline", default "Online") is added to the `HD Agent` DocType JSON. The session creation logic (from Story 3.2) is extended: when routing to an available agent automatically, only agents with `chat_availability="Online"` and current active session count < `max_concurrent_chats` are eligible. A migration patch sets default value for existing agent records (AR-04, AR-05).

12. **Backend and frontend unit tests** — Backend test file `helpdesk/tests/test_agent_chat_interface.py` covers: `accept_session` (happy path, max concurrency exceeded, agent offline), `transfer_session` (to agent, to team), `set_availability`, `get_transfer_targets`. Frontend Vitest tests in `desk/src/pages/chat/__tests__/ChatDashboard.test.ts` cover: unread badge increment, max session enforcement, availability dropdown rendering. ≥80% line coverage on all new backend code (NFR-M-01).

## Tasks / Subtasks

- [ ] **Task 1: Add `chat_availability` field to HD Agent DocType and routing logic** (AC: #4, #10, #11)
  - [ ] Add `chat_availability` Select field (Online/Away/Offline, default "Online") to `helpdesk/helpdesk/doctype/hd_agent/hd_agent.json`
  - [ ] Create migration patch `helpdesk/patches/v1_phase1/add_chat_availability_to_agent.py` that sets `chat_availability="Online"` for all existing HD Agent records; register in `patches.txt`
  - [ ] Extend Story 3.2's session routing logic (in `helpdesk/helpdesk/doctype/hd_chat_session/hd_chat_session.py` or `helpdesk/api/chat.py`) to filter eligible agents by `chat_availability="Online"` and active session count < `max_concurrent_chats`
  - [ ] Add `max_concurrent_chats` Int field (default 5) to `HD Settings` DocType JSON if not already present

- [ ] **Task 2: Implement `accept_session` API endpoint** (AC: #1, #2, #10)
  - [ ] In `helpdesk/helpdesk/api/chat.py`, add `accept_session(session_id: str)`:
    - Validate caller has Agent role: `frappe.has_permission("HD Chat Session", "write", throw=True)`
    - Check agent `chat_availability != "Offline"`
    - Count agent's current active sessions; if >= `max_concurrent_chats`, raise `frappe.ValidationError(_("Maximum concurrent chats reached"))`
    - Set `HD Chat Session.agent = frappe.session.user`, `status = "active"`, `accepted_at = now()`
    - Publish `chat_accepted` event to room `chat:{session_id}` via `frappe.publish_realtime`
    - Return updated session doc

- [ ] **Task 3: Implement `transfer_session` API endpoint** (AC: #3, #10)
  - [ ] In `helpdesk/helpdesk/api/chat.py`, add `transfer_session(session_id: str, target_type: str, target: str)`:
    - Validate caller is the current session agent or HD Admin
    - If `target_type="agent"`: verify target agent exists, is Online, and has capacity
    - If `target_type="team"`: verify HD Team exists
    - Insert `HD Chat Message` with `sender_type="system"`, `content=f"Chat transferred to {target_name}"`
    - Update `HD Chat Session.agent` (for agent transfer) or queue for team
    - Publish `chat_transferred` event to room `chat:{session_id}` with `{target_name, target_type}`
    - Publish `agent_chat_request` to room `agent:{target_email}` (for agent transfers)
    - Return updated session doc

- [ ] **Task 4: Implement `set_availability` and `get_transfer_targets` API endpoints** (AC: #4, #10)
  - [ ] Add `set_availability(availability: str)` to `helpdesk/helpdesk/api/chat.py`:
    - Validate availability in ["Online", "Away", "Offline"]
    - Set `frappe.db.set_value("HD Agent", frappe.session.user, "chat_availability", availability)`
    - Publish `agent_availability_changed` to room `agent:{frappe.session.user}` with `{availability}`
    - Return `{"availability": availability}`
  - [ ] Add `get_transfer_targets()` to `helpdesk/helpdesk/api/chat.py`:
    - Return agents with `chat_availability in ["Online", "Away"]` (excluding `frappe.session.user`) with `{name, full_name, availability, active_chat_count}`
    - Return all HD Teams: `frappe.db.get_all("HD Team", fields=["name"])`

- [ ] **Task 5: Implement `end_session` API endpoint** (AC: #7)
  - [ ] Add `end_session(session_id: str)` to `helpdesk/helpdesk/api/chat.py`:
    - Validate caller is the session agent or HD Admin
    - Set `HD Chat Session.status = "ended"`, `ended_at = now()`
    - Publish `session_ended` to room `chat:{session_id}` with `{reason: "agent_ended"}`
    - Leave the associated HD Ticket open for email follow-up (do NOT close ticket)
    - Return `{"status": "ended"}`

- [ ] **Task 6: Create Pinia `chat.ts` store** (AC: #5)
  - [ ] Create `desk/src/stores/chat.ts` with:
    ```typescript
    interface ChatSession { name: string; customer_name: string; status: string; agent: string; ticket: string }
    state: { activeSessions: ChatSession[]; queuedSessions: ChatSession[]; availability: "Online"|"Away"|"Offline"; unreadCounts: Record<string, number>; activeSessionId: string | null }
    ```
  - [ ] Actions: `acceptSession(sessionId)`, `transferSession(sessionId, targetType, target)`, `setAvailability(availability)`, `markRead(sessionId)`, `addMessage(sessionId, message)`, `removeSession(sessionId)`
  - [ ] On store init (`setup()` or `$onAction`): subscribe to `frappe.realtime` for events on `agent:{currentUser}` room — `agent_chat_request` appends to `queuedSessions`; `chat_transferred` removes from `activeSessions`
  - [ ] Subscribe to per-session rooms on `acceptSession`: on `chat_message` event for non-active session, increment `unreadCounts[sessionId]`

- [ ] **Task 7: Create `ChatDashboard.vue` page** (AC: #6, #2, #9)
  - [ ] Create `desk/src/pages/chat/ChatDashboard.vue`:
    - Check `chat_enabled` from HD Settings via `createResource`; redirect to `/helpdesk` with toast if disabled
    - Request desktop notification permission on first visit (check `localStorage.getItem("hd_notif_requested")`); set key after first request
    - Left sidebar: queued sessions list (customer name, first message preview, accept button); active session tabs with unread badge
    - Main panel: `<RouterView>` or inline `ChatSession` for the `activeSessionId`
    - Show empty state: "No active chats. You're all caught up!" when both lists are empty
    - `AgentAvailability.vue` in top-right corner
  - [ ] On mount: load initial `activeSessions` and `queuedSessions` via `GET /api/method/helpdesk.api.chat.get_agent_sessions`
  - [ ] Add `get_agent_sessions()` endpoint to `helpdesk/helpdesk/api/chat.py` returning agent's active/queued sessions

- [ ] **Task 8: Create `ChatSession.vue` page** (AC: #7)
  - [ ] Create `desk/src/pages/chat/ChatSession.vue`:
    - Props / route param: `sessionId`
    - Renders `ChatMessageList.vue` (existing from Stories 3.3/3.4), `ChatInput.vue`, header with customer info
    - Transfer button → opens `TransferDialog.vue`
    - End Chat button → calls `chatStore.endSession(sessionId)` → confirm dialog first
    - On mount: join Socket.IO room `chat:{sessionId}` and mark messages as read (call `chatStore.markRead(sessionId)` which resets `unreadCounts[sessionId]` to 0)
    - Fetch message history via `GET /api/method/helpdesk.api.chat.get_messages?session_id={sessionId}` (from Story 3.4)

- [ ] **Task 9: Create `AgentAvailability.vue` component** (AC: #4)
  - [ ] Create `desk/src/components/chat/AgentAvailability.vue`:
    - Renders a frappe-ui `Dropdown` with three options: Online (green dot), Away (yellow dot), Offline (red dot)
    - Current status shown as a badge next to agent name in the chat header
    - On selection: calls `chatStore.setAvailability(status)` which calls the `set_availability` API
    - Loading state during API call (disable dropdown until response)
    - Accessible: `aria-label="Set chat availability"`, keyboard navigable (NFR-U-04, NFR-U-05)

- [ ] **Task 10: Create `TransferDialog.vue` component** (AC: #3)
  - [ ] Create `desk/src/components/chat/TransferDialog.vue`:
    - frappe-ui `Dialog` modal with two tabs: "Agent" and "Team"
    - Agent tab: list of agents from `get_transfer_targets` with availability dot, active chat count; filtered by search input
    - Team tab: list of all teams from `get_transfer_targets`
    - Confirm button calls `chatStore.transferSession(sessionId, targetType, target)`
    - On success: close dialog; toast "Chat transferred to {target_name}"; session removed from `activeSessions`
    - Loading state on confirm button; error toast on failure

- [ ] **Task 11: Add Vue routes** (AC: #8)
  - [ ] In `desk/src/router/index.ts` (or equivalent router config file), add:
    ```typescript
    { path: '/helpdesk/chat', name: 'ChatDashboard', component: () => import('@/pages/chat/ChatDashboard.vue') }
    { path: '/helpdesk/chat/:sessionId', name: 'ChatSession', component: () => import('@/pages/chat/ChatSession.vue') }
    ```
  - [ ] Add navigation guard: check `frappe.session.user` is authenticated; if `chat_enabled = false`, redirect to `/helpdesk`
  - [ ] Add chat nav item to the helpdesk sidebar navigation (link to `/helpdesk/chat` with unread count badge from `chatStore`)

- [ ] **Task 12: Handle desktop notification for new chat requests** (AC: #1, #9)
  - [ ] In `ChatDashboard.vue` (or a `useChat.ts` composable), listen for `agent_chat_request` Socket.IO events on `agent:{currentUser}` room
  - [ ] When event arrives:
    - Append to `queuedSessions` in store
    - If `Notification.permission === "granted"`: `new Notification("New chat from {customer_name}", { body: firstMessagePreview, icon: "/assets/helpdesk/images/logo.png" })`
    - Play a soft audio chime (optional, if audio asset available)
    - Increment nav badge unread count

- [ ] **Task 13: Backend unit tests** (AC: #12)
  - [ ] Create `helpdesk/tests/test_agent_chat_interface.py`:
    - Test `accept_session` happy path: session status → "active", agent set, event published (mock `frappe.publish_realtime`)
    - Test `accept_session` max concurrency: create 5 active sessions for agent; assert `frappe.ValidationError` raised on 6th accept
    - Test `accept_session` agent offline: set `chat_availability="Offline"`; assert error raised
    - Test `transfer_session` to agent: assert system message inserted, session agent updated, events published
    - Test `transfer_session` to team: assert queued correctly
    - Test `set_availability`: assert `HD Agent.chat_availability` updated
    - Test `get_transfer_targets`: assert offline agents excluded; self excluded
    - Test `end_session`: assert `status="ended"`, HD Ticket remains open
  - [ ] Achieve ≥80% line coverage on all new `helpdesk/api/chat.py` additions (NFR-M-01)

- [ ] **Task 14: Frontend Vitest tests** (AC: #12)
  - [ ] Create `desk/src/pages/chat/__tests__/ChatDashboard.test.ts`:
    - Test: unread badge shows correct count when `chat_message` event arrives for non-visible session
    - Test: "Accept" button disabled when `activeSessions.length >= max_concurrent_chats`
    - Test: `AgentAvailability` dropdown renders three options; selection triggers `setAvailability` store action
    - Test: desktop notification permission requested on first visit; not re-requested if `hd_notif_requested` in localStorage
    - Test: empty state shown when no queued and no active sessions
  - [ ] Add to existing frontend test suite run

## Dev Notes

### Architecture Patterns

This story implements **FR-LC-04** (Agent Chat Interface) and **UX-DR-12** (concurrent sessions with unread badges and quick-switch). It consumes the backend infrastructure from Stories 3.1–3.4 and builds the agent-facing frontend layer.

**Key architectural constraints:**

- **Feature flag check** — All chat pages and API endpoints must check `frappe.db.get_single_value("HD Settings", "chat_enabled")` and fail gracefully if disabled (AR-06).
- **Socket.IO room strategy** — Agent-level events (new chat request, availability change) go to room `agent:{agent_email}`. Session-level events (messages, transfers, session end) go to room `chat:{session_id}`. Never publish agent-private events to chat rooms (AR-07).
- **Max concurrency enforcement is server-side** — The UI shows the limit visually, but the `accept_session` API enforces it. Never rely solely on frontend enforcement.
- **Pinia store is the single source of truth** — Components read from `chatStore`; they never fetch chat state independently. All Socket.IO event subscriptions are in the store (ADR-11).
- **Lazy-loaded routes** — Both chat pages use dynamic `import()` to avoid increasing the main bundle size (ADR-09).
- **No Frappe session context in widget** — The widget uses JWT tokens. The agent interface uses Frappe session authentication. These must not be conflated (ADR-05).

### API Method Signatures

```python
# helpdesk/helpdesk/api/chat.py (additions to existing module)

@frappe.whitelist()
def accept_session(session_id: str) -> dict:
    """Accept a queued chat session. Raises ValidationError if at max concurrency or offline."""

@frappe.whitelist()
def transfer_session(session_id: str, target_type: str, target: str) -> dict:
    """Transfer session to agent or team. Inserts system message for audit trail."""

@frappe.whitelist()
def set_availability(availability: str) -> dict:
    """Set agent chat availability: Online | Away | Offline."""

@frappe.whitelist()
def get_transfer_targets() -> dict:
    """Return online/away agents (excl. self) and all teams for transfer dialog."""

@frappe.whitelist()
def end_session(session_id: str) -> dict:
    """End an active chat session. Ticket remains open for email follow-up."""

@frappe.whitelist()
def get_agent_sessions() -> dict:
    """Return agent's active and queued chat sessions for dashboard init."""
```

### Pinia Store Structure

```typescript
// desk/src/stores/chat.ts
import { defineStore } from 'pinia'
import { ref, computed } from 'vue'
import type { Ref } from 'vue'

export interface ChatSession {
  name: string
  customer_name: string
  customer_email: string
  status: 'waiting' | 'active' | 'ended'
  agent: string
  ticket: string
  started_at: string
  first_message?: string
}

export const useChatStore = defineStore('chat', () => {
  const activeSessions: Ref<ChatSession[]> = ref([])
  const queuedSessions: Ref<ChatSession[]> = ref([])
  const availability: Ref<'Online' | 'Away' | 'Offline'> = ref('Online')
  const unreadCounts: Ref<Record<string, number>> = ref({})
  const activeSessionId: Ref<string | null> = ref(null)

  const totalUnread = computed(() =>
    Object.values(unreadCounts.value).reduce((sum, n) => sum + n, 0)
  )

  // Actions: acceptSession, transferSession, setAvailability,
  //          markRead, addMessage, removeSession, setActiveSession
  return {
    activeSessions, queuedSessions, availability,
    unreadCounts, activeSessionId, totalUnread,
    // ...actions
  }
})
```

### ChatDashboard.vue Structure

```vue
<!-- desk/src/pages/chat/ChatDashboard.vue -->
<template>
  <div class="flex h-full">
    <!-- Left sidebar -->
    <aside class="w-72 border-r flex flex-col">
      <!-- Agent availability toggle -->
      <AgentAvailability />
      <!-- Queued sessions -->
      <section v-if="chatStore.queuedSessions.length">
        <h3>Waiting ({{ chatStore.queuedSessions.length }})</h3>
        <QueuedSessionCard
          v-for="s in chatStore.queuedSessions"
          :key="s.name"
          :session="s"
          @accept="chatStore.acceptSession(s.name)"
        />
      </section>
      <!-- Active session tabs -->
      <section>
        <h3>Active Chats ({{ chatStore.activeSessions.length }}/{{ maxConcurrent }})</h3>
        <ActiveSessionTab
          v-for="s in chatStore.activeSessions"
          :key="s.name"
          :session="s"
          :unread="chatStore.unreadCounts[s.name] ?? 0"
          :active="chatStore.activeSessionId === s.name"
          @click="chatStore.setActiveSession(s.name)"
        />
      </section>
      <!-- Empty state -->
      <div v-if="isEmpty" class="text-center text-gray-400 mt-8">
        No active chats. You're all caught up!
      </div>
    </aside>
    <!-- Main chat panel -->
    <main class="flex-1">
      <ChatSession v-if="chatStore.activeSessionId" :session-id="chatStore.activeSessionId" />
      <div v-else class="flex items-center justify-center h-full text-gray-400">
        Select a chat to begin
      </div>
    </main>
  </div>
</template>

<script setup lang="ts">
import { onMounted, computed } from 'vue'
import { useChatStore } from '@/stores/chat'
import AgentAvailability from '@/components/chat/AgentAvailability.vue'
import ChatSession from './ChatSession.vue'

const chatStore = useChatStore()
const maxConcurrent = 5 // from HD Settings

const isEmpty = computed(() =>
  chatStore.activeSessions.length === 0 && chatStore.queuedSessions.length === 0
)

onMounted(async () => {
  // Request notification permission once
  if (Notification.permission === 'default' && !localStorage.getItem('hd_notif_requested')) {
    Notification.requestPermission()
    localStorage.setItem('hd_notif_requested', '1')
  }
  await chatStore.loadSessions()
})
</script>
```

### Socket.IO Event Schema (Agent Side)

```python
# Events published TO agent room:  agent:{agent_email}
# agent_chat_request: { session_id, customer_name, customer_email, first_message, started_at }
# agent_availability_changed: { agent_email, availability }

# Events published TO chat room:   chat:{session_id}
# chat_accepted:    { session_id, agent_email, agent_name }
# chat_transferred: { session_id, target_name, target_type }
# session_ended:    { session_id, reason: "agent_ended" }

# Events published FROM agent client:
# (agent joins room chat:{session_id} on accepting session)
# typing_start / typing_stop / chat_message / message_read
# — same as Story 3.4 patterns, reused here for agent side
```

### AgentAvailability Component Pattern

```vue
<!-- desk/src/components/chat/AgentAvailability.vue -->
<template>
  <Dropdown :options="availabilityOptions" @select="handleSelect" :loading="loading">
    <template #trigger>
      <button
        class="flex items-center gap-2 px-3 py-1.5 rounded-md border"
        aria-label="Set chat availability"
      >
        <span :class="dotClass" class="w-2 h-2 rounded-full" />
        {{ chatStore.availability }}
        <ChevronDownIcon class="w-4 h-4" />
      </button>
    </template>
  </Dropdown>
</template>

<script setup lang="ts">
import { ref, computed } from 'vue'
import { useChatStore } from '@/stores/chat'

const chatStore = useChatStore()
const loading = ref(false)

const dotClass = computed(() => ({
  'bg-green-500': chatStore.availability === 'Online',
  'bg-yellow-500': chatStore.availability === 'Away',
  'bg-red-500':   chatStore.availability === 'Offline',
}))

const availabilityOptions = [
  { label: 'Online',  value: 'Online',  icon: '🟢' },
  { label: 'Away',    value: 'Away',    icon: '🟡' },
  { label: 'Offline', value: 'Offline', icon: '🔴' },
]

async function handleSelect(option: { value: string }) {
  loading.value = true
  try {
    await chatStore.setAvailability(option.value as 'Online' | 'Away' | 'Offline')
  } finally {
    loading.value = false
  }
}
</script>
```

### Backend `accept_session` Pattern

```python
# helpdesk/helpdesk/api/chat.py

@frappe.whitelist()
def accept_session(session_id: str) -> dict:
    """Accept a queued chat session."""
    frappe.has_permission("HD Chat Session", "write", throw=True)

    # Check agent availability
    agent_availability = frappe.db.get_value(
        "HD Agent", frappe.session.user, "chat_availability"
    )
    if agent_availability in ("Offline", "Away"):
        frappe.throw(
            _("You cannot accept chats while {0}").format(agent_availability),
            frappe.ValidationError,
        )

    # Check max concurrent chats
    max_concurrent = int(
        frappe.db.get_single_value("HD Settings", "max_concurrent_chats") or 5
    )
    active_count = frappe.db.count(
        "HD Chat Session",
        {"agent": frappe.session.user, "status": "active"},
    )
    if active_count >= max_concurrent:
        frappe.throw(
            _("Maximum concurrent chats ({0}) reached").format(max_concurrent),
            frappe.ValidationError,
        )

    # Accept the session
    session = frappe.get_doc("HD Chat Session", session_id)
    if session.status != "waiting":
        frappe.throw(_("Session is no longer available"), frappe.ValidationError)

    session.agent = frappe.session.user
    session.status = "active"
    session.accepted_at = frappe.utils.now()
    session.save(ignore_permissions=True)
    frappe.db.commit()

    # Notify the widget and other agents
    frappe.publish_realtime(
        event="chat_accepted",
        message={
            "session_id": session_id,
            "agent_email": frappe.session.user,
            "agent_name": frappe.utils.get_fullname(frappe.session.user),
        },
        room=f"chat:{session_id}",
    )

    return session.as_dict()
```

### HD Agent DocType Addition

```json
// Addition to helpdesk/helpdesk/doctype/hd_agent/hd_agent.json (fields array)
{
  "fieldname": "chat_availability",
  "fieldtype": "Select",
  "label": "Chat Availability",
  "options": "Online\nAway\nOffline",
  "default": "Online",
  "in_list_view": 0,
  "in_standard_filter": 1
}
```

### Migration Patch Pattern

```python
# helpdesk/patches/v1_phase1/add_chat_availability_to_agent.py
import frappe


def execute():
    """Set default chat_availability for all existing HD Agent records."""
    frappe.db.sql(
        "UPDATE `tabHD Agent` SET chat_availability = 'Online' WHERE chat_availability IS NULL OR chat_availability = ''"
    )
    frappe.db.commit()
```

### Prerequisites and Dependencies

- **Story 3.1** (Channel Abstraction Layer) — `ChatAdapter` for message normalization.
- **Story 3.2** (Chat Session Management Backend) — `HD Chat Session`, `HD Chat Message` DocTypes; JWT validation; `create_session` API; session cleanup job.
- **Story 3.3** (Embeddable Chat Widget) — `ChatMessageList.vue`, `ChatInput.vue` components reused in `ChatSession.vue`.
- **Story 3.4** (Real-Time Chat Communication) — Socket.IO event handlers; `chat_handlers.py`; `typing_start`/`typing_stop`/`message_read` events; `get_messages` API.
- **`chat_enabled` feature flag** — All API endpoints and Vue pages check this flag (AR-06).
- **frappe-ui components** — `Dropdown`, `Dialog`, `Badge` components used in new Vue files (ADR-09).
- **Pinia** — `chat.ts` store follows existing store pattern in `desk/src/stores/` (ADR-11).

### Project Structure Notes

**New files created by this story:**
```
helpdesk/
├── helpdesk/
│   └── doctype/
│       └── hd_agent/
│           └── hd_agent.json          # Add chat_availability field (Task 1)
└── patches/
    └── v1_phase1/
        └── add_chat_availability_to_agent.py  # Migration patch (Task 1)

helpdesk/
└── tests/
    └── test_agent_chat_interface.py   # Backend unit tests (Task 13)

desk/
└── src/
    ├── pages/
    │   └── chat/
    │       ├── ChatDashboard.vue      # Main chat queue/session dashboard (Task 7)
    │       ├── ChatSession.vue        # Individual session view (Task 8)
    │       └── __tests__/
    │           └── ChatDashboard.test.ts  # Vitest tests (Task 14)
    ├── components/
    │   └── chat/
    │       ├── AgentAvailability.vue  # Availability toggle (Task 9)
    │       └── TransferDialog.vue     # Transfer modal (Task 10)
    └── stores/
        └── chat.ts                    # Pinia chat store (Task 6)
```

**Modified files:**
```
helpdesk/helpdesk/api/chat.py          # accept_session, transfer_session, set_availability,
                                       # get_transfer_targets, end_session, get_agent_sessions (Tasks 2-5,7)
helpdesk/helpdesk/doctype/hd_settings/hd_settings.json  # max_concurrent_chats field (Task 1)
helpdesk/patches.txt                   # Register new patch (Task 1)
desk/src/router/index.ts               # Add /helpdesk/chat routes (Task 11)
desk/src/components/chat/ChatMessageList.vue  # Already extended in Story 3.4; reused here
```

**Naming conventions followed:**
- DocType fields: `snake_case` (`chat_availability`, `max_concurrent_chats`, `accepted_at`)
- Vue components: PascalCase (`ChatDashboard.vue`, `AgentAvailability.vue`, `TransferDialog.vue`)
- Composables/stores: camelCase (`chat.ts`, `useChatStore`)
- Socket.IO events: `snake_case` (`agent_chat_request`, `chat_accepted`, `chat_transferred`) per ADR architecture naming rules
- Routes: kebab-case paths (`/helpdesk/chat`, `/helpdesk/chat/:sessionId`)
- API module: additive changes to existing `helpdesk/api/chat.py`

### Security Notes

- **NFR-SE-02**: `accept_session` and `transfer_session` validate that the caller has the Agent role and owns the session before mutation. Session IDs are not guessable (Frappe auto-name).
- **Availability isolation**: `get_transfer_targets` never exposes Offline agents as targets; routing logic server-side enforces this.
- **Max concurrency server-side**: UI guidance is supplementary; server always enforces `max_concurrent_chats`.
- **Desktop notification content**: Notification body shows only `customer_name` and message preview — no PII beyond what an agent would see in their queue.

### References

- Architecture ADR-08: API Design — `helpdesk/api/chat.py` endpoints [Source: `_bmad-output/planning-artifacts/architecture.md#ADR-08`]
- Architecture ADR-09: Frontend Component Organization — `desk/src/pages/chat/` [Source: `_bmad-output/planning-artifacts/architecture.md#ADR-09`]
- Architecture ADR-11: State Management — Pinia `chat.ts` store [Source: `_bmad-output/planning-artifacts/architecture.md#ADR-11`]
- Architecture Naming Patterns: Vue PascalCase, events snake_case [Source: `_bmad-output/planning-artifacts/architecture.md#Naming Patterns`]
- Architecture Room Strategy: `agent:{email}` for agent events, `chat:{session_id}` for session events [Source: `_bmad-output/planning-artifacts/architecture.md#Communication Patterns`]
- FR-LC-04: Agent chat interface with concurrent sessions (up to 5), transfer, availability toggle, desktop notifications [Source: `_bmad-output/planning-artifacts/epics.md#Functional Requirements`]
- UX-DR-12: Chat agent interface shows concurrent sessions list with unread badges and quick-switch [Source: `_bmad-output/planning-artifacts/epics.md#UX Design Requirements`]
- AR-06: Feature flags in HD Settings [Source: `_bmad-output/planning-artifacts/epics.md#Additional Requirements`]
- AR-07: Socket.IO room naming convention [Source: `_bmad-output/planning-artifacts/epics.md#Additional Requirements`]
- NFR-M-01: Minimum 80% unit test coverage on all new backend code [Source: `_bmad-output/planning-artifacts/epics.md#Non-Functional Requirements`]
- NFR-SE-02: Chat sessions authenticated via token; no cross-customer data access [Source: `_bmad-output/planning-artifacts/epics.md#Non-Functional Requirements`]
- NFR-U-04: WCAG 2.1 AA compliance for all new UI components [Source: `_bmad-output/planning-artifacts/epics.md#Non-Functional Requirements`]
- NFR-U-05: Full keyboard navigation for all new features [Source: `_bmad-output/planning-artifacts/epics.md#Non-Functional Requirements`]
- Epic 3 Story 3.5 acceptance criteria [Source: `_bmad-output/planning-artifacts/epics.md#Story 3.5: Agent Chat Interface`]
- Story 3.2 (prerequisite): Chat Session Management Backend [Source: `_bmad-output/implementation-artifacts/story-3.2-chat-session-management-backend.md`]
- Story 3.3 (prerequisite): Embeddable Chat Widget — `ChatMessageList.vue`, `ChatInput.vue` [Source: `_bmad-output/implementation-artifacts/story-3.3-embeddable-chat-widget.md`]
- Story 3.4 (prerequisite): Real-Time Chat Communication — Socket.IO handlers, `chat_handlers.py` [Source: `_bmad-output/implementation-artifacts/story-3.4-real-time-chat-communication.md`]

## Dev Agent Record

### Agent Model Used

claude-opus-4-5

### Debug Log References

### Completion Notes List

### File List
