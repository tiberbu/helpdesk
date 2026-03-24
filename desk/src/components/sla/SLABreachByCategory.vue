<template>
  <div class="w-full">
    <div v-if="resource.loading" class="flex justify-center py-8">
      <LoadingIndicator :scale="6" />
    </div>
    <div v-else-if="rows.length" style="height: 220px">
      <ECharts :options="chartOptions" class="w-full h-full" />
    </div>
    <div v-else class="flex justify-center py-8 text-ink-gray-4 text-sm">
      {{ __("No breach data") }}
    </div>
  </div>
</template>

<script setup lang="ts">
import { computed, watch } from "vue";
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

const resource = createResource({
  url: "helpdesk.api.sla.get_breach_analysis",
  makeParams: () => ({
    date_from: props.dateFrom,
    date_to: props.dateTo,
    team: props.team || null,
    agent: props.agent || null,
    priority: props.priority || null,
    category: props.category || null,
  }),
  auto: true,
});

const rows = computed<{ category: string; breach_count: number }[]>(
  () => resource.data?.by_category || []
);

const chartOptions = computed<EChartsOption>(() => {
  const labels = rows.value.map((r) => r.category);
  const values = rows.value.map((r) => r.breach_count);

  return {
    tooltip: {
      trigger: "axis",
      axisPointer: { type: "shadow" },
    },
    grid: { left: 100, right: 10, top: 10, bottom: 30 },
    xAxis: {
      type: "value",
      axisLabel: { fontSize: 10 },
    },
    yAxis: {
      type: "category",
      data: labels.slice().reverse(),
      axisLabel: {
        fontSize: 10,
        width: 90,
        overflow: "truncate",
      },
    },
    series: [
      {
        type: "bar",
        data: values.slice().reverse(),
        itemStyle: { color: "#F87171" },
        label: {
          show: true,
          position: "right",
          fontSize: 10,
        },
      },
    ],
  };
});

watch(
  () => [props.dateFrom, props.dateTo, props.team, props.agent, props.priority, props.category],
  () => { resource.reload(); }
);
</script>
