<template>
  <div class="border-t pt-3 px-5 pb-3">
    <!-- Header -->
    <div class="flex items-center justify-between mb-3">
      <h3 class="text-sm font-semibold text-gray-700">
        {{ __("Time Tracking") }}
      </h3>
      <Button size="sm" variant="ghost" @click="openManualEntry">
        <template #prefix><LucidePlus class="w-3 h-3" /></template>
        {{ __("Add Entry") }}
      </Button>
    </div>

    <!-- Active Timer Display -->
    <div
      v-if="isTimerRunning"
      class="mb-3 rounded-md bg-blue-50 border border-blue-200 px-3 py-2 flex items-center justify-between"
    >
      <div>
        <p class="text-xs text-blue-600 font-medium">{{ __("Timer running") }}</p>
        <p
          class="font-mono text-lg text-blue-800 tabular-nums"
          role="timer"
          aria-live="polite"
        >
          {{ formattedElapsed }}
        </p>
      </div>
      <Button
        size="sm"
        variant="solid"
        theme="red"
        :label="__('Stop')"
        @click="stopTimer"
      />
    </div>

    <!-- Cross-ticket timer warning -->
    <div
      v-else-if="foreignTimerTicket"
      class="mb-3 rounded-md bg-yellow-50 border border-yellow-200 px-3 py-2 text-xs text-yellow-700"
    >
      {{ __("Timer running on ticket") }}
      <router-link
        :to="`/tickets/${foreignTimerTicket}`"
        class="font-medium underline"
      >{{ foreignTimerTicket }}</router-link>.
      {{ __("Stop it before starting a new timer.") }}
    </div>

    <!-- Start Timer Button (when no timer active) -->
    <Button
      v-else
      size="sm"
      variant="outline"
      class="w-full mb-3"
      @click="startTimer"
      :loading="startResource.loading"
    >
      <template #prefix><LucideTimer class="w-3 h-3" /></template>
      {{ __("Start Timer") }}
    </Button>

    <!-- Totals Summary -->
    <div
      v-if="summary.total_minutes > 0"
      class="mb-3 flex gap-4 text-xs text-gray-600"
    >
      <div>
        <span class="font-medium text-gray-800">{{
          formatMinutes(summary.total_minutes)
        }}</span>
        <span class="ml-1">{{ __("total") }}</span>
      </div>
      <div v-if="summary.billable_minutes > 0">
        <span class="font-medium text-gray-800">{{
          formatMinutes(summary.billable_minutes)
        }}</span>
        <span class="ml-1">{{ __("billable") }}</span>
      </div>
    </div>

    <!-- Entry List -->
    <ul
      v-if="summary.entries?.length"
      class="space-y-1"
      role="list"
    >
      <li
        v-for="entry in summary.entries"
        :key="entry.name"
        class="flex items-start justify-between gap-2 rounded border border-gray-100 bg-gray-50 px-2 py-1.5 text-xs"
      >
        <div class="min-w-0 flex-1">
          <div class="flex items-center gap-1 flex-wrap">
            <span class="font-medium text-gray-800">{{
              formatMinutes(entry.duration_minutes)
            }}</span>
            <Badge v-if="entry.billable" label="Billable" theme="green" size="sm" />
            <span class="text-gray-400 ml-auto">{{ formatDate(entry.timestamp) }}</span>
          </div>
          <p
            class="text-gray-500 mt-0.5 truncate"
            :title="entry.description || ''"
          >
            {{ entry.agent_name
            }}<span v-if="entry.description"> — {{ entry.description }}</span>
          </p>
        </div>
        <button
          v-if="canDelete(entry)"
          class="text-gray-400 hover:text-red-500 transition-colors flex-shrink-0 mt-0.5"
          :aria-label="__('Delete time entry')"
          @click="confirmDelete(entry)"
        >
          <LucideTrash2 class="w-3 h-3" />
        </button>
      </li>
    </ul>

    <!-- Empty State -->
    <div
      v-else-if="!isTimerRunning"
      class="text-center py-4 text-gray-400 text-xs"
    >
      <LucideClock class="w-5 h-5 mx-auto mb-1 opacity-50" />
      <p>{{ __("No time logged yet") }}</p>
    </div>

    <!-- Manual Entry Dialog -->
    <TimeEntryDialog
      v-if="showManualEntry"
      :ticket-id="ticketId"
      mode="manual"
      @saved="onEntrySaved"
      @close="showManualEntry = false"
    />

    <!-- Stop Timer: description/billable prompt -->
    <TimeEntryDialog
      v-if="showStopPrompt"
      :ticket-id="ticketId"
      :prefill-duration-minutes="pendingDurationMinutes"
      :started-at="pendingStartedAt"
      mode="stop-timer"
      @saved="onStopSaved"
      @close="cancelStopPrompt"
    />

    <!-- Delete Confirmation -->
    <Dialog
      v-if="deleteTarget"
      :options="{
        title: __('Delete Time Entry'),
        message: __('Delete this time entry? This cannot be undone.'),
        actions: [
          {
            label: __('Cancel'),
            variant: 'subtle',
            onClick: () => (deleteTarget = null),
          },
          {
            label: __('Delete'),
            variant: 'solid',
            theme: 'red',
            onClick: doDelete,
          },
        ],
      }"
      @close="deleteTarget = null"
    />
  </div>
</template>

<script setup lang="ts">
import { ref, computed, onMounted, onUnmounted } from "vue";
import { createResource, Button, Badge, Dialog } from "frappe-ui";
import LucidePlus from "~icons/lucide/plus";
import LucideTimer from "~icons/lucide/timer";
import LucideClock from "~icons/lucide/clock";
import LucideTrash2 from "~icons/lucide/trash-2";
import TimeEntryDialog from "./TimeEntryDialog.vue";

const props = defineProps<{ ticketId: string }>();

// ---- Timer state ----
const storageKey = computed(() => `hd_timer_${props.ticketId}`);
const isTimerRunning = ref(false);
const timerStartedAt = ref<number | null>(null);
const pendingStartedAt = ref<string>("");
const elapsed = ref(0); // seconds
const foreignTimerTicket = ref<string | null>(null);
let timerInterval: ReturnType<typeof setInterval> | null = null;

const showManualEntry = ref(false);
const showStopPrompt = ref(false);
const pendingDurationMinutes = ref(0);
const deleteTarget = ref<any | null>(null);

const summary = ref<{
  total_minutes: number;
  billable_minutes: number;
  entries: any[];
}>({ total_minutes: 0, billable_minutes: 0, entries: [] });

// ---- Computed ----
const formattedElapsed = computed(() => {
  const h = Math.floor(elapsed.value / 3600);
  const m = Math.floor((elapsed.value % 3600) / 60);
  const s = elapsed.value % 60;
  return [h, m, s].map((v) => String(v).padStart(2, "0")).join(":");
});

// ---- Lifecycle ----
onMounted(() => {
  loadTimer();
  loadSummary();
});

onUnmounted(() => {
  if (timerInterval) clearInterval(timerInterval);
});

// ---- Timer helpers ----
function loadTimer() {
  const stored = localStorage.getItem(storageKey.value);
  if (stored) {
    try {
      const data = JSON.parse(stored);
      timerStartedAt.value = new Date(data.started_at).getTime();
      pendingStartedAt.value = data.started_at;
      elapsed.value = Math.floor((Date.now() - timerStartedAt.value) / 1000);
      isTimerRunning.value = true;
      timerInterval = setInterval(tick, 1000);
      return;
    } catch {
      localStorage.removeItem(storageKey.value);
    }
  }
  // Check for a timer running on a different ticket
  for (let i = 0; i < localStorage.length; i++) {
    const key = localStorage.key(i);
    if (key && key.startsWith("hd_timer_") && key !== storageKey.value) {
      try {
        const data = JSON.parse(localStorage.getItem(key)!);
        if (data.ticket) {
          foreignTimerTicket.value = data.ticket;
        }
      } catch {
        // ignore corrupt entries
      }
      break;
    }
  }
}

function tick() {
  elapsed.value = Math.floor(
    (Date.now() - (timerStartedAt.value ?? Date.now())) / 1000
  );
}

const startResource = createResource({
  url: "helpdesk.api.time_tracking.start_timer",
  onSuccess(data: { started_at: string }) {
    timerStartedAt.value = new Date(data.started_at).getTime();
    pendingStartedAt.value = data.started_at;
    elapsed.value = 0;
    isTimerRunning.value = true;
    foreignTimerTicket.value = null;
    localStorage.setItem(
      storageKey.value,
      JSON.stringify({ started_at: data.started_at, ticket: props.ticketId })
    );
    timerInterval = setInterval(tick, 1000);
  },
});

function startTimer() {
  if (foreignTimerTicket.value) return;
  startResource.submit({ ticket: props.ticketId });
}

function stopTimer() {
  if (timerInterval) {
    clearInterval(timerInterval);
    timerInterval = null;
  }
  isTimerRunning.value = false;
  pendingDurationMinutes.value = Math.max(
    1,
    Math.ceil(elapsed.value / 60)
  );
  showStopPrompt.value = true;
}

function cancelStopPrompt() {
  // Resume timer if user cancels the stop prompt
  showStopPrompt.value = false;
  if (timerStartedAt.value) {
    isTimerRunning.value = true;
    timerInterval = setInterval(tick, 1000);
  }
}

function onStopSaved() {
  localStorage.removeItem(storageKey.value);
  elapsed.value = 0;
  timerStartedAt.value = null;
  pendingStartedAt.value = "";
  showStopPrompt.value = false;
  loadSummary();
}

// ---- Manual entry ----
function openManualEntry() {
  showManualEntry.value = true;
}

function onEntrySaved() {
  showManualEntry.value = false;
  loadSummary();
}

// ---- Summary ----
const summaryResource = createResource({
  url: "helpdesk.api.time_tracking.get_summary",
  onSuccess(data: any) {
    summary.value = data;
  },
});

function loadSummary() {
  summaryResource.submit({ ticket: props.ticketId });
}

// ---- Delete ----
function canDelete(entry: any): boolean {
  const frappeUser = (window as any).frappe?.session?.user;
  const hasAdminRole =
    (window as any).frappe?.user?.has_role?.("HD Admin") ||
    (window as any).frappe?.user?.has_role?.("System Manager");
  return entry.agent === frappeUser || hasAdminRole;
}

function confirmDelete(entry: any) {
  deleteTarget.value = entry;
}

const deleteResource = createResource({
  url: "helpdesk.api.time_tracking.delete_entry",
  onSuccess() {
    deleteTarget.value = null;
    loadSummary();
  },
});

function doDelete() {
  if (!deleteTarget.value) return;
  deleteResource.submit({ name: deleteTarget.value.name });
}

// ---- Formatting ----
function formatMinutes(mins: number): string {
  const h = Math.floor(mins / 60);
  const m = mins % 60;
  if (h === 0) return `${m}m`;
  if (m === 0) return `${h}h`;
  return `${h}h ${m}m`;
}

function formatDate(ts: string): string {
  return new Date(ts).toLocaleDateString(undefined, {
    day: "2-digit",
    month: "short",
  });
}
</script>
