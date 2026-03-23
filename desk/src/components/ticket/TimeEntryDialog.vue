<template>
  <Dialog
    :options="{ title: dialogTitle, size: 'sm' }"
    v-model="show"
    @close="emit('close')"
  >
    <template #body-content>
      <div class="space-y-4">
        <!-- Duration -->
        <div>
          <label class="block text-sm font-medium text-gray-700 mb-1">
            {{ __("Duration") }} *
          </label>
          <div class="flex gap-2">
            <FormControl
              type="number"
              :placeholder="__('Hours')"
              v-model="hours"
              :min="0"
              class="w-24"
            />
            <FormControl
              type="number"
              :placeholder="__('Minutes')"
              v-model="minutes"
              :min="0"
              :max="59"
              class="w-24"
            />
          </div>
          <p v-if="showDurationError" class="mt-1 text-xs text-red-600">
            {{ __("Duration must be greater than 0") }}
          </p>
        </div>

        <!-- Description -->
        <FormControl
          type="textarea"
          :label="__('Description')"
          :placeholder="__('What did you work on? (optional)')"
          v-model="description"
        />

        <!-- Billable -->
        <FormControl
          type="checkbox"
          :label="__('Billable')"
          v-model="billable"
        />
      </div>
    </template>
    <template #actions>
      <Button variant="subtle" @click="emit('close')">
        {{ __("Cancel") }}
      </Button>
      <Button
        variant="solid"
        :disabled="!isValid || saveResource.loading"
        :loading="saveResource.loading"
        @click="save"
      >
        {{ __("Save") }}
      </Button>
    </template>
  </Dialog>
</template>

<script setup lang="ts">
import { ref, computed, watch } from "vue";
import { createResource, Button, Dialog, FormControl } from "frappe-ui";

const props = defineProps<{
  ticketId: string;
  prefillDurationMinutes?: number;
  mode?: "manual" | "stop-timer";
  startedAt?: string;
}>();

const emit = defineEmits<{ saved: []; close: [] }>();

const show = ref(true);
const description = ref("");
const billable = ref(false);
const hours = ref<number>(0);
const minutes = ref<number>(0);
const touched = ref(false);

// Pre-fill duration from timer if provided
watch(
  () => props.prefillDurationMinutes,
  (val) => {
    if (val && val > 0) {
      hours.value = Math.floor(val / 60);
      minutes.value = val % 60;
    }
  },
  { immediate: true }
);

const dialogTitle = computed(() =>
  props.mode === "stop-timer" ? __("Log Timer Entry") : __("Add Time Entry")
);

const totalMinutes = computed(
  () => Number(hours.value) * 60 + Number(minutes.value)
);

const showDurationError = computed(() => touched.value && totalMinutes.value < 1);
const isValid = computed(() => totalMinutes.value >= 1);

const saveUrl = computed(() =>
  props.mode === "stop-timer"
    ? "helpdesk.api.time_tracking.stop_timer"
    : "helpdesk.api.time_tracking.add_entry"
);

const saveResource = createResource({
  url: saveUrl.value,
  onSuccess() {
    emit("saved");
  },
});

function save() {
  touched.value = true;
  if (!isValid.value) return;

  const params: Record<string, any> = {
    ticket: props.ticketId,
    duration_minutes: totalMinutes.value,
    description: description.value,
    billable: billable.value ? 1 : 0,
  };

  if (props.mode === "stop-timer" && props.startedAt) {
    params.started_at = props.startedAt;
  }

  saveResource.submit(params);
}
</script>
