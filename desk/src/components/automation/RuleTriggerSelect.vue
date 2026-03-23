<template>
  <div class="flex flex-col gap-1.5">
    <div
      v-for="trigger in TRIGGER_OPTIONS"
      :key="trigger.value"
      class="flex items-center gap-3 rounded-lg border px-4 py-3 cursor-pointer transition-colors"
      :class="
        modelValue === trigger.value
          ? 'border-blue-500 bg-blue-50 text-blue-900'
          : 'border-gray-200 bg-white hover:border-gray-300 hover:bg-gray-50'
      "
      @click="$emit('update:modelValue', trigger.value)"
    >
      <component
        :is="trigger.icon"
        class="h-4 w-4 shrink-0"
        :class="modelValue === trigger.value ? 'text-blue-600' : 'text-gray-400'"
      />
      <div class="flex flex-col min-w-0">
        <span class="text-sm font-medium leading-tight">{{ __(trigger.label) }}</span>
        <span class="text-xs text-gray-500 leading-tight mt-0.5">{{ __(trigger.description) }}</span>
      </div>
      <div class="ml-auto shrink-0">
        <div
          v-if="modelValue === trigger.value"
          class="h-2 w-2 rounded-full bg-blue-500"
        />
      </div>
    </div>
  </div>
</template>

<script setup lang="ts">
import { __ } from "@/translation"
import LucideTicket from "~icons/lucide/ticket"
import LucideRefreshCw from "~icons/lucide/refresh-cw"
import LucideUserCheck from "~icons/lucide/user-check"
import LucideCheckCircle from "~icons/lucide/check-circle"
import LucideRotateCcw from "~icons/lucide/rotate-ccw"
import LucideAlertTriangle from "~icons/lucide/alert-triangle"
import LucideAlertOctagon from "~icons/lucide/alert-octagon"
import LucideStar from "~icons/lucide/star"
import LucideMessageSquare from "~icons/lucide/message-square"
import LucideMessageSquareOff from "~icons/lucide/message-square-off"
import { TRIGGER_OPTIONS as _OPTIONS } from "./triggerOptions"

defineProps<{
  modelValue: string
}>()

defineEmits<{
  (e: "update:modelValue", value: string): void
}>()

const TRIGGER_OPTIONS = _OPTIONS.map((t, i) => ({
  ...t,
  icon: [LucideTicket, LucideRefreshCw, LucideUserCheck, LucideCheckCircle, LucideRotateCcw,
         LucideAlertTriangle, LucideAlertOctagon, LucideStar, LucideMessageSquare, LucideMessageSquareOff][i],
}))
</script>
