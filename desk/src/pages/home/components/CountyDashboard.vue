<template>
  <div class="flex flex-col gap-4">
    <!-- Filters -->
    <div class="flex items-center gap-4 overflow-x-auto">
      <Dropdown
        v-if="!showDatePicker"
        :options="options"
        class="!form-control !w-48"
        v-model="preset"
        :placeholder="__('Select Range')"
      >
        <template #default>
          <div
            class="flex justify-between !w-48 items-center border border-outline-gray-2 rounded text-ink-gray-8 px-2 py-1.5 hover:border-outline-gray-3 hover:shadow-sm transition-colors h-7 cursor-pointer"
          >
            <div class="flex items-center">
              <LucideCalendar class="size-4 text-ink-gray-5 mr-2" />
              <span class="text-base">{{ preset }}</span>
            </div>
            <LucideChevronDown class="size-4 text-ink-gray-5" />
          </div>
        </template>
      </Dropdown>
      <DateRangePicker
        v-else
        class="!w-48"
        ref="datePickerRef"
        v-model="filters.period"
        variant="outline"
        :placeholder="__('Period')"
        @update:model-value="
          (e: string) => {
            showDatePicker = false;
            preset = formatter(e);
          }
        "
        :formatter="formatRange"
      >
        <template #prefix>
          <LucideCalendar class="size-4 text-ink-gray-5 mr-2" />
        </template>
      </DateRangePicker>
      <Link
        class="form-control w-48"
        doctype="HD County"
        :placeholder="__('County')"
        v-model="filters.county"
        :page-length="20"
        :hide-me="true"
      />
      <Link
        class="form-control w-48"
        doctype="HD Support Level"
        :placeholder="__('Support Level')"
        v-model="filters.support_level"
        :page-length="10"
        :hide-me="true"
      />
    </div>

    <!-- Loading -->
    <div
      v-if="dashboardData.loading"
      class="flex items-center justify-center h-[200px]"
    >
      <Button :loading="true" size="2xl" variant="ghost" />
    </div>

    <div v-else-if="dashboardData.data" class="flex flex-col gap-4">
      <!-- Number Cards -->
      <div class="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-5 gap-4">
        <Tooltip
          v-for="(config, index) in dashboardData.data.number_cards"
          :key="index"
          :text="config.tooltip"
        >
          <NumberChart class="border rounded-md" :config="config" />
        </Tooltip>
      </div>

      <!-- Charts -->
      <div class="grid grid-cols-1 md:grid-cols-2 gap-4">
        <div class="border rounded-md">
          <component :is="getChartType(dashboardData.data.county_chart)" />
        </div>
        <div class="border rounded-md">
          <component :is="getChartType(dashboardData.data.support_level_chart)" />
        </div>
        <div class="border rounded-md">
          <component :is="getChartType(dashboardData.data.priority_chart)" />
        </div>
        <div class="border rounded-md">
          <component :is="getChartType(dashboardData.data.type_chart)" />
        </div>
        <div class="border rounded-md">
          <component :is="getChartType(dashboardData.data.channel_chart)" />
        </div>
      </div>

      <!-- Implementers by County -->
      <div class="border rounded-md p-4">
        <div class="text-base font-medium text-ink-gray-8 mb-3">
          {{ __("Implementers by County") }}
        </div>
        <div
          v-if="!dashboardData.data.implementers?.length"
          class="text-sm text-ink-gray-5"
        >
          {{ __("No county-team mappings found.") }}
        </div>
        <div v-else class="flex flex-col divide-y divide-outline-gray-1">
          <div
            v-for="row in dashboardData.data.implementers"
            :key="row.county"
            class="py-2 flex flex-col gap-1"
          >
            <div class="flex items-center gap-2">
              <span class="font-medium text-ink-gray-8">{{ row.county }}</span>
              <span class="text-xs text-ink-gray-5">
                ({{ row.teams.join(", ") }})
              </span>
            </div>
            <div class="flex flex-wrap gap-2">
              <span
                v-for="agent in row.implementers"
                :key="agent.user"
                class="text-xs px-2 py-0.5 rounded-full"
                :class="
                  agent.is_active
                    ? 'bg-surface-green-2 text-ink-green-3'
                    : 'bg-surface-gray-2 text-ink-gray-5'
                "
              >
                {{ agent.agent_name || agent.user }}
              </span>
              <span
                v-if="!row.implementers.length"
                class="text-xs text-ink-gray-5"
              >
                {{ __("No implementers assigned") }}
              </span>
            </div>
          </div>
        </div>
      </div>
    </div>
  </div>
</template>

<script setup lang="ts">
import { Link } from "@/components";
import { __ } from "@/translation";
import {
  AxisChart,
  DateRangePicker,
  DonutChart,
  Dropdown,
  NumberChart,
  Button,
  Tooltip,
  createResource,
  dayjs,
} from "frappe-ui";
import { computed, h, reactive, ref, watch, onMounted } from "vue";

const colors = [
  "#318AD8",
  "#F683AE",
  "#48BB74",
  "#F56B6B",
  "#FACF7A",
  "#44427B",
  "#5FD8C4",
  "#F8814F",
  "#15CCEF",
  "#A6B1B9",
];

const filters = reactive({
  period: getLastXDays(),
  county: null,
  support_level: null,
});

const dashboardData = createResource({
  url: "helpdesk.api.dashboard.get_county_dashboard_data",
  cache: ["Analytics", "CountyDashboard"],
  params: buildParams(),
  auto: true,
});

function buildParams() {
  const [from_date, to_date] = (filters.period || "").split(",");
  return {
    from_date: from_date || null,
    to_date: to_date || null,
    county: filters.county || null,
    support_level: filters.support_level || null,
  };
}

watch(
  () => filters,
  () => {
    if (showDatePicker.value) return;
    dashboardData.update({ params: buildParams() });
    dashboardData.reload();
  },
  { deep: true }
);

function getChartType(chart: any) {
  if (!chart) return;
  chart.colors = colors;
  if (chart["type"] === "axis") {
    return h(AxisChart, { config: chart });
  }
  if (chart["type"] === "pie") {
    return h(DonutChart, { config: chart });
  }
}

function getLastXDays(range: number = 30): string {
  const today = new Date();
  const lastXDate = new Date(today);
  lastXDate.setDate(today.getDate() - range);
  return `${dayjs(lastXDate).format("YYYY-MM-DD")},${dayjs(today).format("YYYY-MM-DD")}`;
}

const showDatePicker = ref(false);
const datePickerRef = ref(null);
const preset = ref(__("Last 30 Days"));

const options = computed(() => [
  {
    group: __("Presets"),
    hideLabel: true,
    items: [
      { label: __("Today"), onClick: () => { preset.value = __("Today"); filters.period = getLastXDays(0); } },
      { label: __("Last 7 Days"), onClick: () => { preset.value = __("Last 7 Days"); filters.period = getLastXDays(7); } },
      { label: __("Last 30 Days"), onClick: () => { preset.value = __("Last 30 Days"); filters.period = getLastXDays(30); } },
      { label: __("Last 60 Days"), onClick: () => { preset.value = __("Last 60 Days"); filters.period = getLastXDays(60); } },
      { label: __("Last 90 Days"), onClick: () => { preset.value = __("Last 90 Days"); filters.period = getLastXDays(90); } },
    ],
  },
  {
    label: __("Custom Range"),
    onClick: () => {
      showDatePicker.value = true;
      setTimeout(() => { datePickerRef.value?.open(); }, 0);
      preset.value = __("Custom Range");
      filters.period = null;
    },
  },
]);

function formatter(range: string) {
  if (!range) {
    filters.period = getLastXDays();
    preset.value = __("Last 30 Days");
    return preset.value;
  }
  const [from, to] = range.split(",");
  return `${formatRange(from)} to ${formatRange(to)}`;
}

function formatRange(date: string) {
  const dateObj = new Date(date);
  return dateObj.toLocaleDateString("en-US", {
    month: "short",
    day: "numeric",
    year: dateObj.getFullYear() === new Date().getFullYear() ? undefined : "numeric",
  });
}

defineExpose({});
</script>
