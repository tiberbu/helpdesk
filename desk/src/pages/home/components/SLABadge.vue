<template>
  <span
    class="text-xs font-semibold rounded px-1.5 py-0.5"
    :class="badgeClass"
  >
    {{ pct }}%
  </span>
</template>

<script setup lang="ts">
import { computed } from "vue";

const props = defineProps<{ pct: number }>();

const badgeClass = computed(() => {
  if (props.pct >= 90) return "bg-green-100 text-green-700";
  if (props.pct >= 70) return "bg-orange-100 text-orange-700";
  return "bg-red-100 text-red-700";
});
</script>
