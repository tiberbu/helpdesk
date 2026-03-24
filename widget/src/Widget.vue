<script setup>
/**
 * Widget.vue — Root component for the embeddable chat widget.
 *
 * Responsibilities:
 *  - Render the floating action button (FAB) at the configured position (AC #2)
 *  - Check agent availability on mount (AC #3, #4)
 *  - Restore session from localStorage on mount (AC #8)
 *  - Route to PreChatForm / OfflineForm / ChatView based on state (AC #3, #4, #8)
 *  - Apply mobile (full-screen) or desktop (400px) panel class (AC #6)
 *  - Emit session data to localStorage when a session is created (AC #8)
 */
import { ref, computed, onMounted, onUnmounted } from 'vue'
import BrandingHeader from './components/BrandingHeader.vue'
import PreChatForm from './components/PreChatForm.vue'
import OfflineForm from './components/OfflineForm.vue'
import ChatView from './components/ChatView.vue'

const props = defineProps({
  siteUrl: { type: String, default: '' },
  brand: { type: String, default: 'default' },
  position: { type: String, default: 'bottom-right' },
})

// ── State ──────────────────────────────────────────────────────────────────
const isOpen = ref(false)
const isOnline = ref(false)
const activeSession = ref(null) // { session_id, token } or null
const isMobile = ref(false)

// ── Computed ───────────────────────────────────────────────────────────────
const isLeft = computed(() => props.position === 'bottom-left')

const panelClass = computed(() =>
  isMobile.value ? 'hd-panel hd-panel--mobile' : `hd-panel hd-panel--desktop${isLeft.value ? ' hd-panel--left' : ''}`
)

const fabClass = computed(() =>
  isLeft.value ? 'hd-fab hd-fab--left' : 'hd-fab'
)

// ── Lifecycle ──────────────────────────────────────────────────────────────
onMounted(async () => {
  updateIsMobile()
  window.addEventListener('resize', updateIsMobile)

  // Restore persisted session (AC #8)
  restoreSession()

  // Check agent availability (AC #3, #4)
  await checkAvailability()
})

onUnmounted(() => {
  window.removeEventListener('resize', updateIsMobile)
})

// ── Methods ────────────────────────────────────────────────────────────────
function updateIsMobile() {
  isMobile.value = window.innerWidth < 768
}

function restoreSession() {
  try {
    const raw = localStorage.getItem('hd_chat_session')
    if (!raw) return
    const stored = JSON.parse(raw)
    if (stored && stored.session_id && stored.token && stored.status !== 'ended') {
      activeSession.value = stored
    }
  } catch {
    // Malformed localStorage entry — ignore
  }
}

async function checkAvailability() {
  try {
    const url = `${props.siteUrl}/api/method/helpdesk.api.chat.get_availability?brand=${encodeURIComponent(props.brand)}`
    const res = await fetch(url, { method: 'GET', credentials: 'omit', headers: { Accept: 'application/json' } })
    if (res.ok) {
      const data = await res.json()
      // Frappe wraps responses in { message: ... }
      const payload = data.message !== undefined ? data.message : data
      isOnline.value = !!payload.available
    }
  } catch {
    isOnline.value = false
  }
}

function togglePanel() {
  isOpen.value = !isOpen.value
}

function handleSessionCreated(sessionData) {
  // Persist to localStorage (AC #8)
  const payload = { ...sessionData, status: 'active' }
  localStorage.setItem('hd_chat_session', JSON.stringify(payload))
  activeSession.value = payload
}

function handleSessionEnded() {
  localStorage.removeItem('hd_chat_session')
  activeSession.value = null
  isOnline.value = false // Re-check on next open
  checkAvailability()
}
</script>

<template>
  <!-- FAB button (AC #2) -->
  <button :class="fabClass" @click="togglePanel" aria-label="Open support chat">
    <!-- Chat icon (open state) -->
    <svg v-if="!isOpen" viewBox="0 0 24 24" aria-hidden="true">
      <path d="M21 15a2 2 0 0 1-2 2H7l-4 4V5a2 2 0 0 1 2-2h14a2 2 0 0 1 2 2z" />
    </svg>
    <!-- Close icon (panel open) -->
    <svg v-else viewBox="0 0 24 24" aria-hidden="true">
      <line x1="18" y1="6" x2="6" y2="18" />
      <line x1="6" y1="6" x2="18" y2="18" />
    </svg>
  </button>

  <!-- Chat panel (AC #2, #6) -->
  <div v-if="isOpen" :class="panelClass" role="dialog" aria-label="Support chat">
    <!-- Branding header (AC #7) -->
    <BrandingHeader
      :brand="brand"
      :site-url="siteUrl"
      @close="togglePanel"
    />

    <!-- Active chat session → ChatView (AC #3, #8) -->
    <ChatView
      v-if="activeSession"
      :session-id="activeSession.session_id"
      :token="activeSession.token"
      :site-url="siteUrl"
      @session-ended="handleSessionEnded"
    />

    <!-- Online → PreChatForm (AC #3) -->
    <PreChatForm
      v-else-if="isOnline"
      :brand="brand"
      :site-url="siteUrl"
      @session-created="handleSessionCreated"
    />

    <!-- Offline → OfflineForm (AC #4) -->
    <OfflineForm
      v-else
      :brand="brand"
      :site-url="siteUrl"
    />
  </div>
</template>
