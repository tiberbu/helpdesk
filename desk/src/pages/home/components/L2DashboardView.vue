<template>
  <div class="flex flex-col gap-4">
    <!-- Header -->
    <div class="flex items-center justify-between px-1">
      <div>
        <div class="text-xl font-semibold text-ink-gray-8">
          {{ __("National Dashboard") }}
        </div>
        <div class="text-sm text-ink-gray-5 mt-0.5">
          {{ __("Kenya-wide support overview across all 47 counties") }}
        </div>
      </div>
      <Button variant="subtle" icon-left="refresh-ccw" :label="__('Refresh')" @click="$emit('refresh')" />
    </div>

    <!-- KPI Cards -->
    <div class="grid grid-cols-2 md:grid-cols-3 gap-3">
      <StatCard
        :label="__('Open Tickets')"
        :value="data.open_tickets ?? 0"
        icon="inbox"
        color="blue"
      />
      <StatCard
        :label="__('SLA Compliance')"
        :value="(data.sla_compliance_pct ?? 0) + '%'"
        icon="shield"
        :color="slaColor(data.sla_compliance_pct)"
      />
      <StatCard
        :label="__('Engineering Tickets')"
        :value="data.engineering_tickets ?? 0"
        icon="tool"
        color="purple"
      />
    </div>

    <!-- Two columns: leaderboard + trends -->
    <div class="grid grid-cols-1 md:grid-cols-2 gap-4">
      <!-- County leaderboard -->
      <div class="rounded border border-outline-gray-1 bg-surface-white">
        <div class="px-4 py-3 border-b border-outline-gray-1 flex items-center justify-between">
          <div class="text-sm font-semibold text-ink-gray-8">
            {{ __("County Leaderboard") }}
          </div>
          <div class="text-xs text-ink-gray-5">{{ __("SLA compliance ranking") }}</div>
        </div>
        <div v-if="!data.county_leaderboard?.length" class="text-sm text-ink-gray-4 py-6 text-center">
          {{ __("No county data available") }}
        </div>
        <div v-else class="overflow-y-auto max-h-80">
          <table class="w-full text-sm">
            <thead class="bg-surface-gray-1 text-ink-gray-5 uppercase text-xs sticky top-0">
              <tr>
                <th class="px-4 py-2 text-left">#</th>
                <th class="px-4 py-2 text-left">{{ __("County") }}</th>
                <th class="px-4 py-2 text-right">{{ __("Tickets") }}</th>
                <th class="px-4 py-2 text-right">{{ __("SLA %") }}</th>
                <th class="px-4 py-2 text-right">{{ __("Esc. Rate") }}</th>
              </tr>
            </thead>
            <tbody>
              <tr
                v-for="(county, idx) in data.county_leaderboard"
                :key="county.county"
                class="border-t border-outline-gray-1 hover:bg-surface-gray-1 transition"
              >
                <td class="px-4 py-2 text-ink-gray-5 text-xs">{{ idx + 1 }}</td>
                <td class="px-4 py-2 font-medium text-ink-gray-8">{{ county.county }}</td>
                <td class="px-4 py-2 text-right text-ink-gray-7">{{ county.total_tickets }}</td>
                <td class="px-4 py-2 text-right">
                  <SLABadge :pct="county.sla_compliance_pct" />
                </td>
                <td class="px-4 py-2 text-right">
                  <span
                    class="text-xs rounded px-1.5 py-0.5"
                    :class="
                      county.escalation_rate_pct > 10
                        ? 'bg-red-100 text-red-700'
                        : county.escalation_rate_pct > 5
                        ? 'bg-orange-100 text-orange-700'
                        : 'bg-green-100 text-green-700'
                    "
                  >
                    {{ county.escalation_rate_pct }}%
                  </span>
                </td>
              </tr>
            </tbody>
          </table>
        </div>
      </div>

      <!-- National trends (7-day) -->
      <div class="rounded border border-outline-gray-1 bg-surface-white p-4">
        <div class="text-sm font-semibold text-ink-gray-8 mb-3">
          {{ __("National Trends — Last 7 Days") }}
        </div>
        <div v-if="!trendsRows.length" class="text-sm text-ink-gray-4 py-4 text-center">
          {{ __("No trend data available") }}
        </div>
        <div v-else class="flex flex-col gap-2">
          <div
            v-for="row in trendsRows"
            :key="row.date"
            class="flex items-center gap-3"
          >
            <div class="text-xs text-ink-gray-5 w-24 shrink-0">{{ row.date }}</div>
            <div class="flex-1 h-4 bg-surface-gray-2 rounded-full overflow-hidden">
              <div
                class="h-full rounded-full bg-blue-500 transition-all"
                :style="{ width: maxTrend ? (row.count / maxTrend) * 100 + '%' : '0%' }"
              />
            </div>
            <div class="text-xs font-medium text-ink-gray-8 w-8 text-right shrink-0">{{ row.count }}</div>
          </div>
        </div>
      </div>
    </div>

    <!-- Bottom: worst counties highlight -->
    <div v-if="worstCounties.length" class="rounded border border-red-200 bg-red-50 p-4">
      <div class="text-sm font-semibold text-red-700 mb-2 flex items-center gap-1.5">
        <FeatherIcon name="alert-circle" class="size-4" />
        {{ __("Counties Needing Attention — Lowest SLA Compliance") }}
      </div>
      <div class="flex flex-wrap gap-2">
        <span
          v-for="c in worstCounties"
          :key="c.county"
          class="text-xs bg-red-100 text-red-700 rounded px-2 py-1"
        >
          {{ c.county }} — {{ c.sla_compliance_pct }}%
        </span>
      </div>
    </div>
  </div>
</template>

<script setup lang="ts">
import { computed } from "vue";
import { Button, FeatherIcon } from "frappe-ui";
import { __ } from "@/translation";
import StatCard from "./DashStatCard.vue";
import SLABadge from "./SLABadge.vue";

const props = defineProps<{
  data: Record<string, any>;
}>();
defineEmits(["refresh"]);

// Trend rows from {dates: [...], open_tickets: [...]}
const trendsRows = computed(() => {
  const trends = props.data.national_trends;
  if (!trends?.dates?.length) return [];
  return trends.dates.map((d: string, i: number) => ({
    date: d,
    count: trends.open_tickets[i] ?? 0,
  }));
});

const maxTrend = computed(() => {
  const counts = trendsRows.value.map((r) => r.count);
  return counts.length ? Math.max(...counts, 1) : 1;
});

// Bottom 5 counties by SLA (from leaderboard which is sorted desc, so take last 5)
const worstCounties = computed(() => {
  const lb: Array<Record<string, any>> = props.data.county_leaderboard ?? [];
  if (lb.length <= 5) return [];
  return [...lb].sort((a, b) => a.sla_compliance_pct - b.sla_compliance_pct).slice(0, 5);
});

function slaColor(pct: number): string {
  if (pct >= 90) return "green";
  if (pct >= 70) return "orange";
  return "red";
}
</script>
