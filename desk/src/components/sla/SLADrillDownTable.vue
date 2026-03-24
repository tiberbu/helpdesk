<template>
  <div class="w-full">
    <!-- Dimension tabs -->
    <div class="flex gap-1 mb-3 border-b border-outline-gray-1">
      <button
        v-for="dim in dimensions"
        :key="dim.value"
        class="px-3 py-1.5 text-sm font-medium transition-colors"
        :class="
          selectedDimension === dim.value
            ? 'border-b-2 border-blue-500 text-blue-600'
            : 'text-ink-gray-5 hover:text-ink-gray-7'
        "
        @click="selectedDimension = dim.value"
      >
        {{ dim.label }}
      </button>
    </div>

    <!-- Loading -->
    <div v-if="resource.loading" class="flex justify-center py-8">
      <LoadingIndicator :scale="6" />
    </div>

    <!-- Table -->
    <div v-else-if="rows.length" class="overflow-x-auto">
      <table class="w-full text-sm">
        <thead>
          <tr class="text-ink-gray-5 border-b border-outline-gray-1">
            <th class="text-left py-2 px-2 font-medium">{{ currentDimension.label }}</th>
            <th class="text-right py-2 px-2 font-medium">{{ __("Tickets") }}</th>
            <th class="text-right py-2 px-2 font-medium">{{ __("Resp %") }}</th>
            <th class="text-right py-2 px-2 font-medium">{{ __("Resol %") }}</th>
            <th class="text-right py-2 px-2 font-medium">{{ __("Breaches") }}</th>
            <th class="text-right py-2 px-2 font-medium">{{ __("Avg Resp (min)") }}</th>
          </tr>
        </thead>
        <tbody>
          <tr
            v-for="row in rows"
            :key="row.dimension_value"
            class="border-b border-outline-gray-1 hover:bg-surface-gray-1 transition-colors"
          >
            <td class="py-2 px-2 text-ink-gray-8 truncate max-w-[180px]">
              {{ row.dimension_value || __("None") }}
            </td>
            <td class="py-2 px-2 text-right text-ink-gray-6">{{ row.total_tickets }}</td>
            <td class="py-2 px-2 text-right font-medium" :class="pctColor(row.response_compliance_pct)">
              {{ row.response_compliance_pct }}%
            </td>
            <td class="py-2 px-2 text-right font-medium" :class="pctColor(row.resolution_compliance_pct)">
              {{ row.resolution_compliance_pct }}%
            </td>
            <td class="py-2 px-2 text-right text-red-600 font-medium">{{ row.breach_count }}</td>
            <td class="py-2 px-2 text-right text-ink-gray-6">
              {{ row.avg_response_minutes != null ? row.avg_response_minutes : "—" }}
            </td>
          </tr>
        </tbody>
      </table>
    </div>

    <!-- Empty -->
    <div v-else class="flex justify-center py-8 text-ink-gray-4 text-sm">
      {{ __("No data for selected filters") }}
    </div>
  </div>
</template>

<script setup lang="ts">
import { computed, ref, watch } from "vue";
import { createResource, LoadingIndicator } from "frappe-ui";
import { __ } from "@/translation";

const props = defineProps<{
  dateFrom: string;
  dateTo: string;
  team?: string;
  agent?: string;
  priority?: string;
  category?: string;
}>();

const dimensions = [
  { value: "team", label: __("Team") },
  { value: "agent", label: __("Agent") },
  { value: "priority", label: __("Priority") },
  { value: "category", label: __("Category") },
];

const selectedDimension = ref("team");

const currentDimension = computed(
  () => dimensions.find((d) => d.value === selectedDimension.value) || dimensions[0]
);

const resource = createResource({
  url: "helpdesk.api.sla.get_compliance_by_dimension",
  makeParams: () => ({
    dimension: selectedDimension.value,
    date_from: props.dateFrom,
    date_to: props.dateTo,
    team: props.team || null,
    agent: props.agent || null,
    priority: props.priority || null,
    category: props.category || null,
  }),
  auto: true,
});

const rows = computed(() => resource.data || []);

function pctColor(pct: number) {
  if (pct >= 90) return "text-green-600";
  if (pct >= 70) return "text-yellow-600";
  return "text-red-600";
}

watch(
  () => [selectedDimension.value, props.dateFrom, props.dateTo, props.team, props.agent, props.priority, props.category],
  () => {
    resource.reload();
  }
);
</script>
