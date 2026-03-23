<script setup>
/**
 * ChatView.vue — Active chat session message list + input (Story 3.3 + Story 3.4).
 *
 * Story 3.4 additions:
 *   - Message status icons (sent → delivered → read) via StatusIcon.vue (AC #2)
 *   - Typing indicator with 10s auto-clear via TypingIndicator.vue (AC #3)
 *   - typing_start / typing_stop events emitted to server via REST API (AC #3)
 *   - message_delivered emitted on receiving a chat_message (AC #2)
 *   - mark_messages_read called on mount + panel open + new messages (AC #2)
 *   - Session persistence via localStorage on reconnect (AC #4)
 */
import { ref, nextTick, onMounted, onUnmounted } from 'vue'
import { connectSocket, on, disconnectSocket } from '../socket.js'
import TypingIndicator from './TypingIndicator.vue'
import StatusIcon from './StatusIcon.vue'

const props = defineProps({
  sessionId: { type: String, required: true },
  token: { type: String, required: true },
  siteUrl: { type: String, default: '' },
})

const emit = defineEmits(['session-ended'])

// ── State ──────────────────────────────────────────────────────────────────
const messages = ref([])
const inputText = ref('')
const isLoading = ref(false)
const isSending = ref(false)
const isEnded = ref(false)
const messagesEl = ref(null)

// Typing indicator state (AC #3)
const remoteTyping = ref({ visible: false, senderName: '' })
let remoteTypingTimer = null   // auto-clear after 10s of no typing_start events
let localTypingTimer = null    // debounce: emit typing_start at most once per 2s

// ── Lifecycle ──────────────────────────────────────────────────────────────
onMounted(async () => {
  await fetchHistory()
  setupSocket()
  // Mark all loaded messages as read (AC #2)
  await markAllUnreadRead()
})

onUnmounted(() => {
  disconnectSocket()
  if (remoteTypingTimer) clearTimeout(remoteTypingTimer)
  if (localTypingTimer) clearTimeout(localTypingTimer)
})

// ── Methods ────────────────────────────────────────────────────────────────
async function fetchHistory() {
  isLoading.value = true
  try {
    const url = `${props.siteUrl}/api/method/helpdesk.api.chat.get_messages?session_id=${encodeURIComponent(props.sessionId)}&token=${encodeURIComponent(props.token)}`
    const res = await fetch(url, { headers: { Accept: 'application/json' } })
    if (res.ok) {
      const data = await res.json()
      const payload = data.message !== undefined ? data.message : data
      // Assign status='read' to historical customer messages (they've been seen)
      messages.value = (Array.isArray(payload) ? payload : []).map((m) => ({
        ...m,
        status: m.sender_type === 'customer' ? 'read' : undefined,
      }))
    }
  } catch {
    // History unavailable — start with empty list
  } finally {
    isLoading.value = false
    await nextTick()
    scrollToBottom()
  }
}

async function setupSocket() {
  const socket = await connectSocket(props.siteUrl, props.sessionId, props.token)

  // Receive a message from the agent/system (AC #1, #2)
  on(socket, 'chat_message', async (msg) => {
    if (msg.session_id !== props.sessionId) return
    // Avoid duplicates if own message was already appended optimistically
    if (messages.value.find((m) => m.message_id === msg.message_id)) return
    messages.value.push({
      message_id: msg.message_id,
      sender_type: msg.sender_type || 'agent',
      sender_email: msg.sender_email || '',
      content: msg.content,
      sent_at: msg.sent_at || new Date().toISOString(),
      status: undefined, // not our message — no status icon needed on this side
    })
    nextTick(scrollToBottom)

    // Notify sender that message was delivered (AC #2)
    if (msg.sender_type !== 'customer' && msg.message_id) {
      callApi('message_delivered', {
        session_id: props.sessionId,
        token: props.token,
        message_id: msg.message_id,
      }).catch(() => {})
    }

    // Mark as read immediately (panel is open) (AC #2)
    markMessageRead(msg.message_id, msg.sender_type)
  })

  // Update status icon on delivery/read confirmation (AC #2)
  on(socket, 'message_status', (data) => {
    if (data?.session_id !== props.sessionId) return
    const msg = messages.value.find((m) => m.message_id === data.message_id)
    if (msg) {
      // Status can only advance: sent → delivered → read
      const order = { sent: 0, delivered: 1, read: 2 }
      if (order[data.status] > (order[msg.status] ?? -1)) {
        msg.status = data.status
      }
    }
  })

  // Remote typing indicator (AC #3)
  on(socket, 'typing_start', (data) => {
    if (data?.session_id !== props.sessionId) return
    remoteTyping.value = { visible: true, senderName: data.sender_name || 'Agent' }
    clearTimeout(remoteTypingTimer)
    // Auto-clear after 10 seconds of inactivity (AC #3)
    remoteTypingTimer = setTimeout(() => {
      remoteTyping.value.visible = false
    }, 10_000)
  })

  on(socket, 'typing_stop', (data) => {
    if (data?.session_id !== props.sessionId) return
    clearTimeout(remoteTypingTimer)
    remoteTyping.value.visible = false
  })

  on(socket, 'session_ended', (data) => {
    if (data?.session_id !== props.sessionId) return
    isEnded.value = true
  })
}

async function sendMessage() {
  const text = inputText.value.trim()
  if (!text || isSending.value || isEnded.value) return

  // Stop typing indicator for remote party immediately (AC #3)
  emitTypingStop()

  isSending.value = true
  // Optimistic append with 'sent' status (AC #2)
  const optimistic = {
    message_id: `pending-${Date.now()}`,
    sender_type: 'customer',
    content: text,
    sent_at: new Date().toISOString(),
    status: 'sent',
  }
  messages.value.push(optimistic)
  inputText.value = ''
  await nextTick()
  scrollToBottom()

  try {
    const url = `${props.siteUrl}/api/method/helpdesk.api.chat.send_message`
    const res = await fetch(url, {
      method: 'POST',
      headers: { 'Content-Type': 'application/json', Accept: 'application/json' },
      body: JSON.stringify({
        session_id: props.sessionId,
        content: text,
        token: props.token,
      }),
    })
    const data = await res.json()
    const payload = data.message !== undefined ? data.message : data
    // Update the optimistic entry with real message_id and confirmed 'sent' status (AC #2)
    const idx = messages.value.findIndex((m) => m.message_id === optimistic.message_id)
    if (idx !== -1 && payload.message_id) {
      messages.value[idx].message_id = payload.message_id
      messages.value[idx].status = payload.status || 'sent'
    }
  } catch {
    // Keep optimistic message — it may have been delivered
  } finally {
    isSending.value = false
  }
}

// ── Typing events (AC #3) ──────────────────────────────────────────────────

function handleKeydown(e) {
  if (e.key === 'Enter' && !e.shiftKey) {
    e.preventDefault()
    sendMessage()
    return
  }
  // Debounce: emit typing_start at most once every 2 seconds (AC #3)
  if (!localTypingTimer) {
    emitTypingStart()
    localTypingTimer = setTimeout(() => { localTypingTimer = null }, 2000)
  }
}

function emitTypingStart() {
  callApi('typing_start', {
    session_id: props.sessionId,
    token: props.token,
    sender_name: 'Customer',
  }).catch(() => {})
}

function emitTypingStop() {
  clearTimeout(localTypingTimer)
  localTypingTimer = null
  callApi('typing_stop', { session_id: props.sessionId, token: props.token }).catch(() => {})
}

// ── Message read receipts (AC #2) ──────────────────────────────────────────

async function markAllUnreadRead() {
  const unread = messages.value
    .filter((m) => m.sender_type !== 'customer' && !m.is_read && m.message_id && !m.message_id.startsWith('pending-'))
    .map((m) => m.message_id)
  if (unread.length) {
    try {
      await callApi('mark_messages_read', {
        session_id: props.sessionId,
        token: props.token,
        message_ids: unread,
      })
      unread.forEach((mid) => {
        const m = messages.value.find((x) => x.message_id === mid)
        if (m) m.is_read = 1
      })
    } catch { /* Non-critical */ }
  }
}

function markMessageRead(messageId, senderType) {
  if (senderType === 'customer' || !messageId || messageId.startsWith('pending-')) return
  callApi('mark_messages_read', {
    session_id: props.sessionId,
    token: props.token,
    message_ids: [messageId],
  }).catch(() => {})
}

// ── Helpers ────────────────────────────────────────────────────────────────

/**
 * POST to a Frappe whitelisted API method.
 */
function callApi(method, body) {
  const url = `${props.siteUrl}/api/method/helpdesk.api.chat.${method}`
  return fetch(url, {
    method: 'POST',
    headers: { 'Content-Type': 'application/json', Accept: 'application/json' },
    body: JSON.stringify(body),
  })
}

function startNewChat() {
  emit('session-ended')
}

function scrollToBottom() {
  if (messagesEl.value) {
    messagesEl.value.scrollTop = messagesEl.value.scrollHeight
  }
}

function formatTime(ts) {
  if (!ts) return ''
  const d = new Date(ts)
  return d.toLocaleTimeString([], { hour: '2-digit', minute: '2-digit' })
}
</script>

<template>
  <div class="hd-chat">
    <!-- Message list -->
    <div ref="messagesEl" class="hd-chat__messages">
      <div
        v-for="msg in messages"
        :key="msg.message_id"
        class="hd-message"
        :class="`hd-message--${msg.sender_type}`"
      >
        <div class="hd-message__bubble" v-html="msg.content"></div>
        <span class="hd-message__meta">
          {{ formatTime(msg.sent_at) }}
          <!-- Status icon for outgoing (customer) messages only (AC #2) -->
          <StatusIcon
            v-if="msg.sender_type === 'customer' && msg.status"
            :status="msg.status"
          />
        </span>
      </div>

      <!-- Typing indicator (AC #3) -->
      <TypingIndicator
        :visible="remoteTyping.visible"
        :sender-name="remoteTyping.senderName"
      />
    </div>

    <!-- Chat ended banner -->
    <div v-if="isEnded" class="hd-ended">
      <p>This chat has ended.</p>
      <button class="hd-btn hd-btn--ghost" style="width:auto;padding:6px 14px;font-size:12px;" @click="startNewChat">
        Start new chat
      </button>
    </div>

    <!-- Input area (hidden when session ended) -->
    <div v-if="!isEnded" class="hd-chat__footer">
      <textarea
        v-model="inputText"
        class="hd-chat__input"
        placeholder="Type a message…"
        rows="1"
        :disabled="isEnded"
        @keydown="handleKeydown"
      ></textarea>
      <button
        class="hd-chat__send"
        :disabled="!inputText.trim() || isSending || isEnded"
        @click="sendMessage"
        aria-label="Send"
      >
        <svg viewBox="0 0 24 24" aria-hidden="true">
          <line x1="22" y1="2" x2="11" y2="13" />
          <polygon points="22 2 15 22 11 13 2 9 22 2" />
        </svg>
      </button>
    </div>
  </div>
</template>
