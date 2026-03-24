<script setup>
/**
 * BrandingHeader.vue — Fetches and displays brand config (AC #7).
 *
 * Applies primary_color as --hd-primary CSS custom property to the widget.
 * Falls back gracefully to defaults when brand config is unavailable.
 */
import { ref, onMounted } from 'vue'

const props = defineProps({
  brand: { type: String, default: 'default' },
  siteUrl: { type: String, default: '' },
})

const emit = defineEmits(['close'])

// ── Brand config state ─────────────────────────────────────────────────────
const brandName = ref('Support')
const greeting = ref('Hi! How can we help you today?')
const logo = ref(null)
const primaryColor = ref('#4f46e5')

// ── Lifecycle ──────────────────────────────────────────────────────────────
onMounted(async () => {
  await fetchConfig()
})

// ── Methods ────────────────────────────────────────────────────────────────
async function fetchConfig() {
  try {
    const url = `${props.siteUrl}/api/method/helpdesk.api.chat.get_widget_config?brand=${encodeURIComponent(props.brand)}`
    const res = await fetch(url, { credentials: 'omit', headers: { Accept: 'application/json' } })
    if (!res.ok) return
    const data = await res.json()
    const payload = data.message !== undefined ? data.message : data

    if (payload.name) brandName.value = payload.name
    if (payload.greeting) greeting.value = payload.greeting
    if (payload.logo) logo.value = payload.logo
    if (payload.primary_color) {
      primaryColor.value = payload.primary_color
      // Apply to shadow root host element via the container style (AC #7)
      applyPrimaryColor(payload.primary_color)
    }
  } catch {
    // Use defaults silently (AC #7 — handle fetch errors silently)
  }
}

function applyPrimaryColor(color) {
  // Walk up to the shadow host and set the CSS variable
  try {
    // The component is mounted inside the shadow root.
    // We can set the variable on the closest parent that is the shadow container.
    const el = document.querySelector('#hd-widget-root')
    if (el) {
      el.style.setProperty('--hd-primary', color)
    }
  } catch {
    // DOM traversal unavailable in test env — ignore
  }
}
</script>

<template>
  <div class="hd-header" :style="{ background: primaryColor }">
    <!-- Logo or text fallback (AC #7) -->
    <img
      v-if="logo"
      :src="logo"
      :alt="brandName"
      class="hd-header__logo"
    />
    <span
      v-else
      class="hd-header__logo"
      style="display:flex;align-items:center;justify-content:center;font-weight:700;font-size:18px;color:#fff;"
      aria-hidden="true"
    >
      {{ brandName.charAt(0).toUpperCase() }}
    </span>

    <div class="hd-header__text">
      <div class="hd-header__name">{{ brandName }}</div>
      <div class="hd-header__greeting">{{ greeting }}</div>
    </div>

    <button
      class="hd-header__close"
      @click="$emit('close')"
      aria-label="Close chat"
    >
      ×
    </button>
  </div>
</template>
