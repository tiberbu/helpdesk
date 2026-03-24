<template>
  <div class="w-full h-full flex flex-col p-4 overflow-hidden">
    <div class="flex items-center justify-between mb-3">
      <span class="text-ink-gray-5 text-sm">{{ __("SLA Compliance") }}</span>
      <router-link
        to="/dashboard/sla"
        class="text-xs text-blue-500 hover:underline"
      >
        {{ __("View details") }}
      </router-link>
    </div>

    <div v-if="resource.loading" class="flex flex-1 items-center justify-center">
      <LoadingIndicator :scale="6" />
    </div>

    <template v-else>
      <div class="grid grid-cols-2 gap-3 mb-3">
        <!-- Response compliance -->
        <div class="flex flex-col">
          <span class="text-xs text-ink-gray-5 mb-1">{{ __("Response") }}</span>
          <span
            class="text-2xl font-bold"
            :class="pctColor(resource.data?.response_compliance_pct)"
          >
            {{ resource.data?.response_compliance_pct ?? "—" }}%
          </span>
          <div class="mt-1 h-1.5 rounded-full bg-surface-gray-3 overflow-hidden">
            <div
              class="h-full rounded-full"
              :class="pctBarColor(resource.data?.response_compliance_pct)"
              :style="{ width: `${resource.data?.response_compliance_pct ?? 0}%` }"
            />
          </div>
          <span class="text-xs text-ink-gray-4 mt-1">
            {{ resource.data?.response_met }}/{{ resource.data?.response_total }}
          </span>
        </div>

        <!-- Resolution compliance -->
        <div class="flex flex-col">
          <span class="text-xs text-ink-gray-5 mb-1">{{ __("Resolution") }}</span>
          <span
            class="text-2xl font-bold"
            :class="pctColor(resource.data?.resolution_compliance_pct)"
          >
            {{ resource.data?.resolution_compliance_pct ?? "—" }}%
          </span>
          <div class="mt-1 h-1.5 rounded-full bg-surface-gray-3 overflow-hidden">
            <div
              class="h-full rounded-full"
              :class="pctBarColor(resource.data?.resolution_compliance_pct)"
              :style="{ width: `${resource.data?.resolution_compliance_pct ?? 0}%` }"
            />
          </div>
          <span class="text-xs text-ink-gray-4 mt-1">
            {{ resource.data?.resolution_met }}/{{ resource.data?.resolution_total }}
          </span>
        </div>
      </div>

      <!-- Mini sparkline bars for last 7 days -->
      <div v-if="trendData.length" class="flex flex-1 items-end gap-0.5 pt-2">
        <div
          v-for="(point, i) in trendData"
          :key="i"
          class="flex-1 rounded-t transition-all"
          :class="pctBarColor(point.resolution_compliance_pct)"
          :style="{ height: `${Math.max(4, point.resolution_compliance_pct)}%` }"
          :title="`${point.period_label}: ${point.resolution_compliance_pct}%`"
        />
      </div>
    </template>
  </div>
</template>

<script setup lang="ts">
import { computed, onMounted } from "vue";
import { createResource, LoadingIndicator } from "frappe-ui";
import { __ } from "@/translation";
import { dayjs } from "frappe-ui";

const dateTo = dayjs().format("YYYY-MM-DD");
const dateFrom = dayjs().subtract(30, "day").format("YYYY-MM-DD");
const trendDateFrom = dayjs().subtract(7, "day").format("YYYY-MM-DD");

const resource = createResource({
  url: "helpdesk.api.sla.get_compliance_overview",
  makeParams: () => ({
    date_from: dateFrom,
    date_to: dateTo,
  }),
  auto: true,
});

const trendResource = createResource({
  url: "helpdesk.api.sla.get_compliance_trend",
  makeParams: () => ({
    date_from: trendDateFrom,
    date_to: dateTo,
    granularity: "daily",
  }),
  auto: true,
});

const trendData = computed(
  () => (trendResource.data?.current || []).slice(-14)
);

function pctColor(pct?: number) {
  if (pct === undefined || pct === null) return "text-ink-gray-5";
  if (pct >= 90) return "text-green-600";
  if (pct >= 70) return "text-yellow-600";
  return "text-red-600";
}

function pctBarColor(pct?: number) {
  if (!pct) return "bg-surface-gray-3";
  if (pct >= 90) return "bg-green-500";
  if (pct >= 70) return "bg-yellow-400";
  return "bg-red-400";
}
</script>
