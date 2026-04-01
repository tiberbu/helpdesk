<template>
  <div class="rounded border border-outline-gray-1 bg-surface-white p-4 flex flex-col gap-1.5">
    <div class="flex items-center justify-between">
      <div class="text-xs font-medium text-ink-gray-5 uppercase tracking-wide">{{ label }}</div>
      <div
        v-if="icon"
        class="rounded-full p-1.5"
        :class="iconBgClass"
      >
        <FeatherIcon :name="icon" class="size-3.5" :class="iconColorClass" />
      </div>
    </div>
    <div class="text-2xl font-bold" :class="valueColorClass">{{ value }}</div>
  </div>
</template>

<script setup lang="ts">
import { computed } from "vue";
import { FeatherIcon } from "frappe-ui";

const props = defineProps<{
  label: string;
  value: string | number;
  icon?: string;
  color?: "blue" | "orange" | "green" | "red" | "purple";
}>();

const iconBgClass = computed(() => ({
  "bg-blue-100": props.color === "blue",
  "bg-orange-100": props.color === "orange",
  "bg-green-100": props.color === "green",
  "bg-red-100": props.color === "red",
  "bg-purple-100": props.color === "purple",
}));

const iconColorClass = computed(() => ({
  "text-blue-600": props.color === "blue",
  "text-orange-600": props.color === "orange",
  "text-green-600": props.color === "green",
  "text-red-600": props.color === "red",
  "text-purple-600": props.color === "purple",
}));

const valueColorClass = computed(() => ({
  "text-ink-gray-8": !props.color,
  "text-blue-700": props.color === "blue",
  "text-orange-700": props.color === "orange",
  "text-green-700": props.color === "green",
  "text-red-700": props.color === "red",
  "text-purple-700": props.color === "purple",
}));
</script>
