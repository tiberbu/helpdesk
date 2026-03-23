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
import { h } from "vue"
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

defineProps<{
  modelValue: string
}>()

defineEmits<{
  (e: "update:modelValue", value: string): void
}>()

export const TRIGGER_OPTIONS = [
  {
    value: "ticket_created",
    label: "Ticket Created",
    description: "Fires when a new ticket is submitted",
    icon: LucideTicket,
  },
  {
    value: "ticket_updated",
    label: "Ticket Updated",
    description: "Fires on every save of an existing ticket",
    icon: LucideRefreshCw,
  },
  {
    value: "ticket_assigned",
    label: "Ticket Assigned",
    description: "Fires when a ticket is assigned to an agent",
    icon: LucideUserCheck,
  },
  {
    value: "ticket_resolved",
    label: "Ticket Resolved",
    description: "Fires when ticket status changes to Resolved or Closed",
    icon: LucideCheckCircle,
  },
  {
    value: "ticket_reopened",
    label: "Ticket Reopened",
    description: "Fires when a resolved ticket is reopened",
    icon: LucideRotateCcw,
  },
  {
    value: "sla_warning",
    label: "SLA Warning",
    description: "Fires when a ticket approaches its SLA breach threshold",
    icon: LucideAlertTriangle,
  },
  {
    value: "sla_breached",
    label: "SLA Breached",
    description: "Fires when a ticket exceeds its SLA resolution time",
    icon: LucideAlertOctagon,
  },
  {
    value: "csat_received",
    label: "CSAT Response Received",
    description: "Fires when a customer submits a satisfaction rating",
    icon: LucideStar,
  },
  {
    value: "chat_started",
    label: "Chat Started",
    description: "Fires when a new live chat session begins",
    icon: LucideMessageSquare,
  },
  {
    value: "chat_ended",
    label: "Chat Ended",
    description: "Fires when a live chat session ends",
    icon: LucideMessageSquareOff,
  },
]
</script>
