<template>
  <div class="flex flex-col h-full">
    <LayoutHeader>
      <template #left-header>
        <div class="flex items-center gap-2 text-lg font-medium text-gray-900">
          <span>{{ __("SLA Compliance") }}</span>
        </div>
      </template>
      <template #right-header>
        <Button
          variant="subtle"
          icon-left="refresh-ccw"
          :label="__('Refresh')"
          :loading="isLoading"
          @click="refresh"
        />
      </template>
    </LayoutHeader>

    <div class="p-5 w-full flex-1 overflow-y-auto">
      <!-- Filters row -->
      <div class="mb-5 flex flex-wrap items-center gap-3">
        <!-- Date range preset -->
        <Dropdown
          v-if="!showDatePicker"
          :options="presetOptions"
          class="!form-control !w-44"
        >
          <template #default>
            <div
              class="flex justify-between !w-44 items-center border border-outline-gray-2 rounded text-ink-gray-8 px-2 py-1.5 hover:border-outline-gray-3 cursor-pointer h-7"
            >
              <div class="flex items-center">
                <LucideCalendar class="size-4 text-ink-gray-5 mr-2" />
                <span class="text-sm">{{ presetLabel }}</span>
              </div>
              <LucideChevronDown class="size-4 text-ink-gray-5" />
            </div>
          </template>
        </Dropdown>
        <DateRangePicker
          v-else
          class="!w-44"
          ref="datePickerRef"
          v-model="customPeriod"
          variant="outline"
          :placeholder="__('Period')"
          @update:model-value="onCustomDateApply"
        >
          <template #prefix>
            <LucideCalendar class="size-4 text-ink-gray-5 mr-2" />
          </template>
        </DateRangePicker>

        <!-- Team filter -->
        <Link
          class="form-control w-40"
          doctype="HD Team"
          :placeholder="__('Team')"
          v-model="filters.team"
          :page-length="10"
        >
          <template #prefix>
            <LucideUsers class="size-4 text-ink-gray-5 mr-2" />
          </template>
        </Link>

        <!-- Priority filter -->
        <Link
          class="form-control w-36"
          doctype="HD Ticket Priority"
          :placeholder="__('Priority')"
          v-model="filters.priority"
          :page-length="10"
        />

        <!-- Category filter -->
        <Link
          class="form-control w-40"
          doctype="HD Ticket Category"
          :placeholder="__('Category')"
          v-model="filters.category"
          :page-length="10"
        />

        <!-- Clear filters -->
        <Button
          v-if="hasFilters"
          variant="ghost"
          :label="__('Clear')"
          @click="clearFilters"
        />
      </div>

      <!-- Compliance KPI cards -->
      <div class="grid grid-cols-1 sm:grid-cols-2 gap-4 mb-5">
        <!-- Response compliance -->
        <div class="border rounded-lg p-4 bg-surface-white">
          <div class="text-sm text-ink-gray-5 mb-1">{{ __("Response SLA Compliance") }}</div>
          <div v-if="overview.loading" class="h-10 flex items-center">
            <LoadingIndicator :scale="4" />
          </div>
          <template v-else>
            <div class="flex items-end gap-2">
              <span
                class="text-3xl font-bold"
                :class="pctColor(overview.data?.response_compliance_pct)"
              >
                {{ overview.data?.response_compliance_pct ?? "—" }}%
              </span>
              <span class="text-sm text-ink-gray-5 pb-1">
                {{ overview.data?.response_met }}/{{ overview.data?.response_total }} {{ __("tickets") }}
              </span>
            </div>
            <div class="mt-2 h-2 rounded-full bg-surface-gray-3 overflow-hidden">
              <div
                class="h-full rounded-full transition-all"
                :class="pctBarColor(overview.data?.response_compliance_pct)"
                :style="{ width: `${overview.data?.response_compliance_pct ?? 0}%` }"
              />
            </div>
          </template>
        </div>

        <!-- Resolution compliance -->
        <div class="border rounded-lg p-4 bg-surface-white">
          <div class="text-sm text-ink-gray-5 mb-1">{{ __("Resolution SLA Compliance") }}</div>
          <div v-if="overview.loading" class="h-10 flex items-center">
            <LoadingIndicator :scale="4" />
          </div>
          <template v-else>
            <div class="flex items-end gap-2">
              <span
                class="text-3xl font-bold"
                :class="pctColor(overview.data?.resolution_compliance_pct)"
              >
                {{ overview.data?.resolution_compliance_pct ?? "—" }}%
              </span>
              <span class="text-sm text-ink-gray-5 pb-1">
                {{ overview.data?.resolution_met }}/{{ overview.data?.resolution_total }} {{ __("tickets") }}
              </span>
            </div>
            <div class="mt-2 h-2 rounded-full bg-surface-gray-3 overflow-hidden">
              <div
                class="h-full rounded-full transition-all"
                :class="pctBarColor(overview.data?.resolution_compliance_pct)"
                :style="{ width: `${overview.data?.resolution_compliance_pct ?? 0}%` }"
              />
            </div>
          </template>
        </div>
      </div>

      <!-- Trend chart -->
      <div class="border rounded-lg p-4 mb-5 bg-surface-white">
        <div class="text-sm font-medium text-ink-gray-7 mb-3">{{ __("Compliance Trend") }}</div>
        <SLATrendChart
          :date-from="dateFrom"
          :date-to="dateTo"
          :team="filters.team"
          :priority="filters.priority"
          :category="filters.category"
        />
      </div>

      <!-- Drill-down table -->
      <div class="border rounded-lg p-4 mb-5 bg-surface-white">
        <div class="text-sm font-medium text-ink-gray-7 mb-3">{{ __("Compliance by Dimension") }}</div>
        <SLADrillDownTable
          :date-from="dateFrom"
          :date-to="dateTo"
          :team="filters.team"
          :priority="filters.priority"
          :category="filters.category"
        />
      </div>

      <!-- Breach analysis -->
      <div class="grid grid-cols-1 lg:grid-cols-2 gap-4">
        <div class="border rounded-lg p-4 bg-surface-white">
          <div class="text-sm font-medium text-ink-gray-7 mb-3">{{ __("Top Breach Categories") }}</div>
          <SLABreachByCategory
            :date-from="dateFrom"
            :date-to="dateTo"
            :team="filters.team"
            :priority="filters.priority"
            :category="filters.category"
          />
        </div>
        <div class="border rounded-lg p-4 bg-surface-white">
          <div class="text-sm font-medium text-ink-gray-7 mb-3">{{ __("Breaches by Hour of Day") }}</div>
          <SLABreachByHour
            :date-from="dateFrom"
            :date-to="dateTo"
            :team="filters.team"
            :priority="filters.priority"
            :category="filters.category"
          />
        </div>
      </div>
    </div>
  </div>
</template>

<script setup lang="ts">
import { LayoutHeader } from "@/components";
import { Link } from "@/components";
import { __ } from "@/translation";
import {
  Button,
  DateRangePicker,
  Dropdown,
  LoadingIndicator,
  createResource,
  dayjs,
  usePageMeta,
} from "frappe-ui";
import { computed, reactive, ref, watch } from "vue";
import SLATrendChart from "@/components/sla/SLATrendChart.vue";
import SLADrillDownTable from "@/components/sla/SLADrillDownTable.vue";
import SLABreachByCategory from "@/components/sla/SLABreachByCategory.vue";
import SLABreachByHour from "@/components/sla/SLABreachByHour.vue";

usePageMeta(() => ({ title: __("SLA Compliance") }));

// ---- Date range ----
function lastXDays(n: number) {
  const to = dayjs().format("YYYY-MM-DD");
  const from = dayjs().subtract(n, "day").format("YYYY-MM-DD");
  return { from, to, label: `${__("Last")} ${n} ${__("days")}` };
}

const presetLabel = ref(__("Last 30 days"));
const showDatePicker = ref(false);
const datePickerRef = ref(null);
const customPeriod = ref<string | null>(null);
const dateFrom = ref(lastXDays(30).from);
const dateTo = ref(lastXDays(30).to);

const presetOptions = computed(() => [
  {
    group: __("Presets"),
    hideLabel: true,
    items: [7, 30, 60, 90].map((n) => ({
      label: `${__("Last")} ${n} ${__("days")}`,
      onClick: () => {
        const r = lastXDays(n);
        dateFrom.value = r.from;
        dateTo.value = r.to;
        presetLabel.value = r.label;
        showDatePicker.value = false;
      },
    })),
  },
  {
    label: __("Custom Range"),
    onClick: () => {
      showDatePicker.value = true;
      setTimeout(() => (datePickerRef.value as any)?.open(), 0);
    },
  },
]);

function onCustomDateApply(val: string) {
  showDatePicker.value = false;
  if (!val) return;
  const [from, to] = val.split(",");
  dateFrom.value = from;
  dateTo.value = to;
  presetLabel.value = `${from} → ${to}`;
}

// ---- Filters ----
const filters = reactive<{
  team: string | null;
  priority: string | null;
  category: string | null;
}>({ team: null, priority: null, category: null });

const hasFilters = computed(
  () => filters.team || filters.priority || filters.category
);

function clearFilters() {
  filters.team = null;
  filters.priority = null;
  filters.category = null;
}

// ---- Overview resource ----
const overview = createResource({
  url: "helpdesk.api.sla.get_compliance_overview",
  makeParams: () => ({
    date_from: dateFrom.value,
    date_to: dateTo.value,
    team: filters.team || null,
    priority: filters.priority || null,
    category: filters.category || null,
  }),
  auto: true,
});

const isLoading = computed(() => overview.loading);

function refresh() {
  overview.reload();
}

watch([dateFrom, dateTo, () => filters.team, () => filters.priority, () => filters.category], () => {
  overview.reload();
});

// ---- Helpers ----
function pctColor(pct?: number) {
  if (pct === undefined || pct === null) return "text-ink-gray-5";
  if (pct >= 90) return "text-green-600";
  if (pct >= 70) return "text-yellow-600";
  return "text-red-600";
}

function pctBarColor(pct?: number) {
  if (!pct) return "bg-surface-gray-4";
  if (pct >= 90) return "bg-green-500";
  if (pct >= 70) return "bg-yellow-500";
  return "bg-red-500";
}
</script>

<style scoped>
:deep(.form-control button) {
  @apply text-sm rounded h-7 py-1.5 border border-outline-gray-2 bg-surface-white placeholder-ink-gray-4 hover:border-outline-gray-3 hover:shadow-sm focus:bg-surface-white focus:border-outline-gray-4 focus:shadow-sm focus:ring-0 focus-visible:ring-0 text-ink-gray-8 transition-colors w-full;
}
:deep(.form-control button > div) {
  overflow: hidden;
  text-overflow: ellipsis;
  white-space: nowrap;
}
:deep(.form-control div) {
  width: 100%;
  display: flex;
}
</style>
