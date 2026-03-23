<script setup>
/**
 * TypingIndicator.vue — Animated three-dot typing indicator (AC #3, Story 3.4).
 *
 * Shows "{senderName} is typing…" with bouncing dots when visible.
 * Auto-clear logic is managed by the parent (ChatView.vue) via the
 * visible prop — see AC #3 for the 10-second inactivity rule.
 *
 * Accessibility: role="status" + aria-live="polite" so screen readers
 * announce the typing state (NFR-U-04, WCAG 2.1 AA).
 */
defineProps({
  /** Display name of the party who is typing. */
  senderName: { type: String, default: 'Agent' },
  /** Whether the indicator is currently visible. */
  visible: { type: Boolean, default: false },
})
</script>

<template>
  <div
    v-if="visible"
    class="hd-typing-indicator"
    role="status"
    aria-live="polite"
    :aria-label="`${senderName} is typing`"
  >
    <span class="hd-typing-indicator__dot" aria-hidden="true"></span>
    <span class="hd-typing-indicator__dot" aria-hidden="true"></span>
    <span class="hd-typing-indicator__dot" aria-hidden="true"></span>
    <span class="hd-typing-indicator__label">{{ senderName }} is typing…</span>
  </div>
</template>
