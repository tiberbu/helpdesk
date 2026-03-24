<template>
  <div class="w-full flex flex-col gap-2">
    <!-- Granularity selector -->
    <div class="flex justify-end gap-1">
      <button
        v-for="g in granularities"
        :key="g.value"
        class="px-2 py-1 text-xs rounded transition-colors"
        :class="
          granularity === g.value
            ? 'bg-blue-100 text-blue-700 font-medium'
            : 'text-ink-gray-5 hover:bg-surface-gray-2'
        "
        @click="granularity = g.value"
      >
        {{ g.label }}
      </button>
    </div>

    <!-- Loading -->
    <div v-if="resource.loading" class="flex justify-center py-8">
      <LoadingIndicator :scale="6" />
    </div>

    <!-- Chart -->
    <div v-else-if="hasData" class="w-full" style="height: 220px">
      <ECharts :options="chartOptions" class="w-full h-full" />
    </div>

    <!-- Empty -->
    <div v-else class="flex justify-center py-8 text-ink-gray-4 text-sm">
      {{ __("No trend data for selected filters") }}
    </div>
  </div>
</template>

<script setup lang="ts">
import { computed, ref, watch } from "vue";
import { createResource, ECharts, LoadingIndicator } from "frappe-ui";
import { type EChartsOption } from "echarts";
import { __ } from "@/translation";

const props = defineProps<{
  dateFrom: string;
  dateTo: string;
  team?: string;
  agent?: string;
  priority?: string;
  category?: string;
}>();

const granularities = [
  { value: "daily", label: __("D") },
  { value: "weekly", label: __("W") },
  { value: "monthly", label: __("M") },
];

const granularity = ref("daily");

const resource = createResource({
  url: "helpdesk.api.sla.get_compliance_trend",
  makeParams: () => ({
    date_from: props.dateFrom,
    date_to: props.dateTo,
    granularity: granularity.value,
    team: props.team || null,
    agent: props.agent || null,
    priority: props.priority || null,
    category: props.category || null,
  }),
  auto: true,
});

const hasData = computed(
  () => (resource.data?.current?.length || 0) > 0
);

const chartOptions = computed<EChartsOption>(() => {
  const current = resource.data?.current || [];
  const prior = resource.data?.prior || [];

  const labels = current.map((r: any) => String(r.period_label));
  const currentRes = current.map((r: any) => r.resolution_compliance_pct);
  const currentResp = current.map((r: any) => r.response_compliance_pct);
  const priorRes = prior.map((r: any) => r.resolution_compliance_pct);
  const priorResp = prior.map((r: any) => r.response_compliance_pct);

  return {
    tooltip: {
      trigger: "axis",
      formatter: (params: any) => {
        let html = `<div class="text-xs font-medium">${params[0]?.axisValue}</div>`;
        params.forEach((p: any) => {
          html += `<div>${p.marker}${p.seriesName}: <b>${p.value}%</b></div>`;
        });
        return html;
      },
    },
    legend: {
      bottom: 0,
      textStyle: { fontSize: 11 },
    },
    grid: { left: 40, right: 10, top: 10, bottom: 50 },
    xAxis: {
      type: "category",
      data: labels,
      axisLabel: { fontSize: 10, rotate: labels.length > 14 ? 30 : 0 },
    },
    yAxis: {
      type: "value",
      min: 0,
      max: 100,
      axisLabel: { formatter: "{value}%", fontSize: 10 },
    },
    series: [
      {
        name: __("Resolution (current)"),
        type: "line",
        data: currentRes,
        symbol: "none",
        lineStyle: { width: 2 },
        color: "#3B82F6",
      },
      {
        name: __("Response (current)"),
        type: "line",
        data: currentResp,
        symbol: "none",
        lineStyle: { width: 2 },
        color: "#10B981",
      },
      {
        name: __("Resolution (prior)"),
        type: "line",
        data: priorRes,
        symbol: "none",
        lineStyle: { width: 1.5, type: "dashed" },
        color: "#93C5FD",
      },
      {
        name: __("Response (prior)"),
        type: "line",
        data: priorResp,
        symbol: "none",
        lineStyle: { width: 1.5, type: "dashed" },
        color: "#6EE7B7",
      },
    ],
  };
});

watch(
  () => [granularity.value, props.dateFrom, props.dateTo, props.team, props.agent, props.priority, props.category],
  () => {
    resource.reload();
  }
);
</script>
