<template>
  <div class="flex flex-col gap-3">
    <!-- AND/OR toggle -->
    <div v-if="conditions.length > 1" class="flex items-center gap-2">
      <span class="text-xs text-gray-500">{{ __("Match") }}</span>
      <button
        class="rounded px-2 py-0.5 text-xs font-medium transition-colors"
        :class="
          logicOperator === 'AND'
            ? 'bg-orange-100 text-orange-700 border border-orange-300'
            : 'bg-gray-100 text-gray-500 border border-gray-200 hover:bg-gray-200'
        "
        @click="logicOperator = 'AND'"
      >
        ALL
      </button>
      <button
        class="rounded px-2 py-0.5 text-xs font-medium transition-colors"
        :class="
          logicOperator === 'OR'
            ? 'bg-orange-100 text-orange-700 border border-orange-300'
            : 'bg-gray-100 text-gray-500 border border-gray-200 hover:bg-gray-200'
        "
        @click="logicOperator = 'OR'"
      >
        ANY
      </button>
      <span class="text-xs text-gray-500">{{ __("of the following conditions") }}</span>
    </div>

    <!-- Condition rows -->
    <div
      v-for="(condition, index) in conditions"
      :key="index"
      class="flex items-center gap-2"
    >
      <!-- AND/OR label for rows after the first -->
      <span
        v-if="index > 0"
        class="w-8 shrink-0 text-right text-xs font-medium text-orange-600 uppercase"
      >
        {{ logicOperator === "AND" ? __("AND") : __("OR") }}
      </span>
      <span v-else class="w-8 shrink-0 text-right text-xs text-gray-400">{{ __("IF") }}</span>

      <!-- Field select -->
      <div class="flex-1 min-w-0">
        <FormControl
          type="select"
          :placeholder="__('Select field')"
          :options="fieldOptions"
          :value="condition.field"
          @change="(e) => updateCondition(index, 'field', e.target.value)"
          class="w-full"
        />
      </div>

      <!-- Operator select -->
      <div class="w-36 shrink-0">
        <FormControl
          type="select"
          :options="OPERATOR_OPTIONS"
          :value="condition.operator"
          @change="(e) => updateCondition(index, 'operator', e.target.value)"
          class="w-full"
        />
      </div>

      <!-- Value input (hidden for is_set / is_not_set) -->
      <div class="flex-1 min-w-0">
        <FormControl
          v-if="!['is_set', 'is_not_set'].includes(condition.operator)"
          type="text"
          :placeholder="__('Value')"
          :value="condition.value"
          @change="(e) => updateCondition(index, 'value', e.target.value)"
          class="w-full"
        />
        <div v-else class="h-7 rounded border border-gray-200 bg-gray-50 flex items-center px-2">
          <span class="text-xs text-gray-400 italic">{{ __("(no value needed)") }}</span>
        </div>
      </div>

      <!-- Remove button -->
      <button
        class="shrink-0 rounded p-1 text-gray-400 hover:bg-red-50 hover:text-red-500 transition-colors"
        :title="__('Remove condition')"
        @click="removeCondition(index)"
      >
        <LucideX class="h-3.5 w-3.5" />
      </button>
    </div>

    <!-- Empty state -->
    <div
      v-if="conditions.length === 0"
      class="rounded-md border border-dashed border-gray-200 px-4 py-3 text-center"
    >
      <p class="text-sm text-gray-400">
        {{ __("No conditions — rule will always fire for selected trigger.") }}
      </p>
    </div>

    <!-- Add condition button -->
    <div>
      <Button
        variant="ghost"
        size="sm"
        :label="__('Add Condition')"
        @click="addCondition"
      >
        <template #prefix>
          <LucidePlus class="h-3.5 w-3.5" />
        </template>
      </Button>
    </div>
  </div>
</template>

<script setup lang="ts">
import { ref, computed, watch } from "vue"
import { Button, FormControl } from "frappe-ui"
import { __ } from "@/translation"
import LucideX from "~icons/lucide/x"
import LucidePlus from "~icons/lucide/plus"

interface Condition {
  field: string
  operator: string
  value: string
}

interface ConditionsState {
  logic: string
  conditions: Condition[]
}

const props = defineProps<{
  modelValue: ConditionsState
}>()

const emit = defineEmits<{
  (e: "update:modelValue", value: ConditionsState): void
}>()

const logicOperator = ref<string>(props.modelValue?.logic || "AND")
const conditions = ref<Condition[]>(props.modelValue?.conditions || [])

watch([logicOperator, conditions], () => {
  emit("update:modelValue", {
    logic: logicOperator.value,
    conditions: conditions.value,
  })
}, { deep: true })

watch(() => props.modelValue, (val) => {
  if (val) {
    logicOperator.value = val.logic || "AND"
    conditions.value = val.conditions || []
  }
}, { deep: true })

const TICKET_FIELDS = [
  { label: "Priority", value: "priority" },
  { label: "Status", value: "status" },
  { label: "Team", value: "agent_group" },
  { label: "Assigned To", value: "assigned_to" },
  { label: "Category", value: "category" },
  { label: "Sub Category", value: "sub_category" },
  { label: "Source", value: "source" },
  { label: "Subject", value: "subject" },
  { label: "Customer", value: "customer" },
  { label: "Raised By", value: "raised_by" },
]

const fieldOptions = computed(() => [
  { label: "— Select field —", value: "" },
  ...TICKET_FIELDS,
])

const OPERATOR_OPTIONS = [
  { label: "equals", value: "equals" },
  { label: "not equals", value: "not_equals" },
  { label: "contains", value: "contains" },
  { label: "greater than", value: "greater_than" },
  { label: "less than", value: "less_than" },
  { label: "is set", value: "is_set" },
  { label: "is not set", value: "is_not_set" },
]

function addCondition() {
  conditions.value = [
    ...conditions.value,
    { field: "", operator: "equals", value: "" },
  ]
}

function removeCondition(index: number) {
  conditions.value = conditions.value.filter((_, i) => i !== index)
}

function updateCondition(index: number, key: keyof Condition, value: string) {
  const updated = [...conditions.value]
  updated[index] = { ...updated[index], [key]: value }
  // Clear value when operator changes to is_set / is_not_set
  if (key === "operator" && ["is_set", "is_not_set"].includes(value)) {
    updated[index].value = ""
  }
  conditions.value = updated
}
</script>
