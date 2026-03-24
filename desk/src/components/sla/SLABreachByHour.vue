<template>
  <div class="w-full">
    <div v-if="resource.loading" class="flex justify-center py-8">
      <LoadingIndicator :scale="6" />
    </div>
    <div v-else-if="hasData" style="height: 200px">
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

const hourRows = computed<{ hour: number; breach_count: number }[]>(
  () => resource.data?.by_hour || []
);

const hasData = computed(() =>
  hourRows.value.some((r) => r.breach_count > 0)
);

const chartOptions = computed<EChartsOption>(() => {
  const labels = hourRows.value.map((r) => `${r.hour}h`);
  const values = hourRows.value.map((r) => r.breach_count);

  return {
    tooltip: {
      trigger: "axis",
      axisPointer: { type: "shadow" },
      formatter: (params: any) =>
        `${params[0]?.axisValue}: <b>${params[0]?.value}</b> ${__("breaches")}`,
    },
    grid: { left: 35, right: 10, top: 10, bottom: 30 },
    xAxis: {
      type: "category",
      data: labels,
      axisLabel: { fontSize: 9 },
    },
    yAxis: {
      type: "value",
      axisLabel: { fontSize: 10 },
    },
    series: [
      {
        type: "bar",
        data: values,
        itemStyle: {
          color: (params: any) => {
            const v = params.value as number;
            if (v === 0) return "#E5E7EB";
            if (v < 3) return "#FCA5A5";
            return "#EF4444";
          },
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
