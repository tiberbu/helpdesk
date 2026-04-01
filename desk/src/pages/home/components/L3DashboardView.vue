<template>
  <div class="flex flex-col gap-4">
    <!-- Header -->
    <div class="flex items-center justify-between px-1">
      <div>
        <div class="text-xl font-semibold text-ink-gray-8">
          {{ __("Engineering Dashboard") }}
          <span v-if="data.territory" class="text-ink-gray-5 font-normal text-base ml-2">
            — {{ data.territory }}
          </span>
        </div>
        <div class="text-sm text-ink-gray-5 mt-0.5">
          {{ __("Escalated tickets awaiting engineering resolution") }}
        </div>
      </div>
      <Button variant="subtle" icon-left="refresh-ccw" :label="__('Refresh')" @click="$emit('refresh')" />
    </div>

    <!-- KPI Cards -->
    <div class="grid grid-cols-2 gap-3">
      <StatCard
        :label="__('Open Tickets')"
        :value="data.open_tickets ?? 0"
        icon="inbox"
        color="blue"
      />
      <StatCard
        :label="__('Avg Resolution')"
        :value="formatMinutes(data.avg_resolution_time_minutes)"
        icon="clock"
        color="orange"
      />
    </div>

    <!-- Two columns: category breakdown + recent escalated tickets -->
    <div class="grid grid-cols-1 md:grid-cols-2 gap-4">
      <!-- Tickets by Category -->
      <div class="rounded border border-outline-gray-1 p-4 bg-surface-white">
        <div class="text-sm font-semibold text-ink-gray-8 mb-3">
          {{ __("Tickets by Product / Category") }}
        </div>
        <div v-if="!data.tickets_by_category?.length" class="text-sm text-ink-gray-4 py-4 text-center">
          {{ __("No open tickets") }}
        </div>
        <div v-else class="flex flex-col gap-2">
          <div
            v-for="cat in data.tickets_by_category"
            :key="cat.category"
            class="flex items-center justify-between gap-2"
          >
            <div class="flex-1 min-w-0">
              <div class="text-sm text-ink-gray-7 truncate">{{ cat.category }}</div>
              <div class="mt-1 h-1.5 rounded-full bg-surface-gray-2 overflow-hidden">
                <div
                  class="h-full rounded-full bg-purple-500"
                  :style="{
                    width: maxCategoryCount
                      ? (cat.count / maxCategoryCount) * 100 + '%'
                      : '0%',
                  }"
                />
              </div>
            </div>
            <div class="text-sm font-medium text-ink-gray-8 shrink-0">{{ cat.count }}</div>
          </div>
        </div>
      </div>

      <!-- Recent escalated tickets -->
      <div class="rounded border border-outline-gray-1 bg-surface-white">
        <div class="px-4 py-3 border-b border-outline-gray-1 flex items-center gap-1.5">
          <FeatherIcon name="arrow-up-circle" class="size-4 text-purple-600" />
          <div class="text-sm font-semibold text-ink-gray-8">
            {{ __("Recent Escalated Tickets") }}
          </div>
        </div>
        <div
          v-if="!data.escalated_tickets?.length"
          class="text-sm text-ink-gray-4 py-6 text-center"
        >
          {{ __("No escalated tickets") }}
        </div>
        <div v-else class="flex flex-col divide-y divide-outline-gray-1 overflow-y-auto max-h-72">
          <a
            v-for="ticket in data.escalated_tickets"
            :key="ticket.name"
            :href="`/helpdesk/tickets/${ticket.name}`"
            class="flex items-start justify-between gap-2 px-4 py-2.5 hover:bg-surface-gray-1 transition"
          >
            <div class="flex-1 min-w-0">
              <div class="text-sm font-medium text-ink-gray-8 truncate">
                #{{ ticket.name }} — {{ ticket.subject }}
              </div>
              <div class="text-xs text-ink-gray-5 mt-0.5 flex items-center gap-2">
                <span>{{ ticket.category || __("No category") }}</span>
                <span v-if="ticket.escalation_count" class="text-purple-600">
                  ↑{{ ticket.escalation_count }}x escalated
                </span>
              </div>
            </div>
            <div class="shrink-0 text-xs text-ink-gray-5 mt-0.5">
              {{ ticket.days_open }}d
            </div>
          </a>
        </div>
      </div>
    </div>
  </div>
</template>

<script setup lang="ts">
import { computed } from "vue";
import { Button, FeatherIcon } from "frappe-ui";
import { __ } from "@/translation";
import StatCard from "./DashStatCard.vue";

const props = defineProps<{
  data: Record<string, any>;
}>();
defineEmits(["refresh"]);

const maxCategoryCount = computed(() => {
  const cats: Array<{ count: number }> = props.data.tickets_by_category ?? [];
  return cats.length ? Math.max(...cats.map((c) => c.count)) : 1;
});

function formatMinutes(mins: number): string {
  if (!mins) return "—";
  if (mins < 60) return `${mins}m`;
  const h = Math.floor(mins / 60);
  const m = Math.round(mins % 60);
  return m ? `${h}h ${m}m` : `${h}h`;
}
</script>
