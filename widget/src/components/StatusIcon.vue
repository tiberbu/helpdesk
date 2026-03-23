<script setup>
/**
 * StatusIcon.vue — Message delivery/read status icon (AC #2, Story 3.4).
 *
 * Displays one of three states:
 *   sent      — single grey checkmark ✓
 *   delivered — double grey checkmarks ✓✓
 *   read      — double blue checkmarks ✓✓
 *
 * Only rendered for messages sent by the current user ('customer' side).
 * The parent passes the status prop; this component is purely presentational.
 */
defineProps({
  /**
   * Delivery status.
   * @values 'sent' | 'delivered' | 'read'
   */
  status: {
    type: String,
    default: 'sent',
    validator: (v) => ['sent', 'delivered', 'read'].includes(v),
  },
})
</script>

<template>
  <!-- Single grey check: sent to server -->
  <span
    v-if="status === 'sent'"
    class="hd-status-icon hd-status-icon--sent"
    aria-label="Sent"
    title="Sent"
  >
    <svg viewBox="0 0 16 16" aria-hidden="true">
      <polyline points="2,8 6,12 14,4" />
    </svg>
  </span>

  <!-- Double grey checks: delivered to recipient's device -->
  <span
    v-else-if="status === 'delivered'"
    class="hd-status-icon hd-status-icon--delivered"
    aria-label="Delivered"
    title="Delivered"
  >
    <svg viewBox="0 0 20 16" aria-hidden="true">
      <polyline points="1,8 5,12 13,4" />
      <polyline points="7,8 11,12 19,4" />
    </svg>
  </span>

  <!-- Double blue checks: read by recipient -->
  <span
    v-else-if="status === 'read'"
    class="hd-status-icon hd-status-icon--read"
    aria-label="Read"
    title="Read"
  >
    <svg viewBox="0 0 20 16" aria-hidden="true">
      <polyline points="1,8 5,12 13,4" />
      <polyline points="7,8 11,12 19,4" />
    </svg>
  </span>
</template>
