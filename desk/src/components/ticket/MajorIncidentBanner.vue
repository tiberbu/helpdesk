<template>
  <div
    v-if="ticket.doc?.is_major_incident"
    class="flex items-start gap-3 bg-red-50 border-l-4 border-red-600 px-4 py-3 text-sm"
    role="alert"
  >
    <!-- Icon -->
    <LucideAlertTriangle class="h-5 w-5 text-red-600 flex-shrink-0 mt-0.5" />

    <div class="flex-1 min-w-0">
      <div class="flex items-center gap-2 flex-wrap">
        <span class="font-semibold text-red-700">{{ __("Major Incident") }}</span>
        <span class="text-red-500 text-xs">
          {{ __("Declared {0} ago", [elapsedText]) }}
        </span>
        <span v-if="linkedCount > 0" class="text-red-500 text-xs">
          &bull; {{ __("{0} linked ticket(s)", [linkedCount]) }}
        </span>
      </div>
    </div>

    <!-- Actions -->
    <div class="flex items-center gap-2 flex-shrink-0">
      <Button
        size="sm"
        variant="solid"
        theme="red"
        :label="__('Propagate Update')"
        @click="showPropagateDialog = true"
      >
        <template #prefix>
          <LucideMegaphone class="h-3.5 w-3.5" />
        </template>
      </Button>
    </div>
  </div>

  <!-- Propagate Update Dialog -->
  <Dialog
    v-model="showPropagateDialog"
    :options="{
      title: __('Propagate Update to Linked Tickets'),
      size: 'md',
    }"
  >
    <template #body-content>
      <p class="text-sm text-ink-gray-6 mb-3">
        {{
          __(
            'Post an update comment on this ticket and all {0} linked ticket(s). Customers and agents on those tickets will see this message.',
            [linkedCount]
          )
        }}
      </p>
      <FormControl
        type="textarea"
        :label="__('Update Message')"
        v-model="propagateMessage"
        :rows="4"
        :placeholder="__('Describe the current status or next steps...')"
      />
    </template>
    <template #actions>
      <Button
        variant="subtle"
        :label="__('Cancel')"
        @click="showPropagateDialog = false"
      />
      <Button
        variant="solid"
        theme="red"
        :label="__('Post Update')"
        :disabled="!propagateMessage.trim()"
        :loading="propagateResource.loading"
        @click="doPropagateUpdate"
      />
    </template>
  </Dialog>
</template>

<script setup lang="ts">
import { TicketSymbol } from "@/types";
import { Button, Dialog, FormControl, createResource, toast } from "frappe-ui";
import { computed, inject, ref } from "vue";
import LucideAlertTriangle from "~icons/lucide/alert-triangle";
import LucideMegaphone from "~icons/lucide/megaphone";

const ticket = inject(TicketSymbol);

const showPropagateDialog = ref(false);
const propagateMessage = ref("");

const linkedCount = computed(
  () => (ticket?.value?.doc?.related_tickets || []).length
);

const elapsedText = computed(() => {
  const flaggedAt = ticket?.value?.doc?.major_incident_flagged_at;
  if (!flaggedAt) return "—";
  const diff = Math.floor(
    (Date.now() - new Date(flaggedAt).getTime()) / 1000
  );
  if (diff < 60) return `${diff}s`;
  if (diff < 3600) return `${Math.floor(diff / 60)}m`;
  if (diff < 86400) return `${Math.floor(diff / 3600)}h ${Math.floor((diff % 3600) / 60)}m`;
  return `${Math.floor(diff / 86400)}d`;
});

const propagateResource = createResource({
  url: "helpdesk.api.incident.propagate_update",
  onSuccess(data: { count: number }) {
    toast.success(
      __("Update posted to {0} ticket(s).", [data.count])
    );
    showPropagateDialog.value = false;
    propagateMessage.value = "";
  },
  onError(err: any) {
    const msg = err?.messages?.[0] || __("Failed to post update.");
    toast.error(msg);
  },
});

function doPropagateUpdate() {
  if (!propagateMessage.value.trim()) return;
  propagateResource.submit({
    ticket: ticket?.value?.doc?.name,
    message: propagateMessage.value,
  });
}
</script>
