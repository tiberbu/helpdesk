<template>
  <div v-if="checklist.length > 0" class="px-5 py-3 border-t">
    <!-- Header -->
    <div class="flex items-center justify-between mb-2">
      <span
        class="text-sm font-medium"
        :class="allMandatoryComplete ? 'text-green-700' : 'text-ink-gray-7'"
      >
        {{ __("Checklist") }}
      </span>
      <span
        class="text-xs font-medium"
        :class="allMandatoryComplete ? 'text-green-600' : 'text-ink-gray-4'"
      >
        {{ completedCount }} / {{ checklist.length }}
      </span>
    </div>

    <!-- Progress bar -->
    <div class="mb-3 h-1.5 w-full rounded-full bg-gray-200">
      <div
        class="h-1.5 rounded-full transition-all duration-300"
        :class="allMandatoryComplete ? 'bg-green-500' : 'bg-blue-500'"
        :style="{ width: progressPercent + '%' }"
      />
    </div>

    <!-- All mandatory complete indicator -->
    <p v-if="allMandatoryComplete" class="mb-2 text-xs text-green-600 font-medium">
      {{ __("All required items completed") }}
    </p>

    <!-- Checklist items -->
    <ul class="space-y-2">
      <li
        v-for="item in checklist"
        :key="item.name"
        class="flex items-start gap-2 rounded-md p-1.5 transition-colors"
        :class="item.is_completed ? 'bg-gray-50' : 'bg-white'"
      >
        <input
          type="checkbox"
          :checked="!!item.is_completed"
          :disabled="toggleLoading === item.name"
          class="mt-0.5 h-4 w-4 cursor-pointer rounded border-gray-300 text-blue-600 focus:ring-blue-500"
          @change="toggleItem(item)"
        />
        <div class="min-w-0 flex-1">
          <span
            class="text-sm"
            :class="
              item.is_completed
                ? 'text-ink-gray-4 line-through'
                : 'text-ink-gray-7'
            "
          >
            {{ item.item }}
          </span>
          <span
            v-if="item.is_mandatory && !item.is_completed"
            class="ml-1 inline-flex items-center rounded-full bg-red-50 px-1.5 py-0.5 text-xs font-medium text-red-600"
          >
            {{ __("Required") }}
          </span>
          <p
            v-if="item.is_completed && item.completed_by"
            class="mt-0.5 text-xs text-ink-gray-4"
          >
            {{ item.completed_by }}<template v-if="item.completed_at"> &middot; {{ item.completed_at }}</template>
          </p>
        </div>
      </li>
    </ul>
  </div>
</template>

<script setup lang="ts">
import { computed, ref } from "vue";
import { createResource, toast } from "frappe-ui";
import { __ } from "@/translation";

interface ChecklistItem {
  name: string;
  item: string;
  is_mandatory: 0 | 1;
  is_completed: 0 | 1;
  completed_by?: string;
  completed_at?: string;
}

const props = defineProps<{
  ticketName: string;
  checklist: ChecklistItem[];
}>();

const emit = defineEmits<{
  itemToggled: [itemName: string, isCompleted: boolean];
}>();

const toggleLoading = ref<string | null>(null);

const completedCount = computed(
  () => props.checklist.filter((i) => i.is_completed).length
);

const progressPercent = computed(() =>
  props.checklist.length === 0
    ? 0
    : Math.round((completedCount.value / props.checklist.length) * 100)
);

const allMandatoryComplete = computed(() =>
  props.checklist
    .filter((i) => i.is_mandatory)
    .every((i) => i.is_completed)
);

const toggleResource = createResource({
  url: "helpdesk.api.incident_model.complete_checklist_item",
});

function toggleItem(item: ChecklistItem) {
  toggleLoading.value = item.name;
  toggleResource.submit(
    {
      ticket: props.ticketName,
      checklist_item_name: item.name,
    },
    {
      onSuccess(data: { is_completed: number }) {
        toggleLoading.value = null;
        emit("itemToggled", item.name, !!data.is_completed);
      },
      onError(err: any) {
        toggleLoading.value = null;
        const msg =
          err?.messages?.[0] || __("Failed to update checklist item.");
        toast.error(msg);
      },
    }
  );
}
</script>
