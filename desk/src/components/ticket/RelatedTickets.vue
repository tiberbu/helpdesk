<template>
  <div class="px-5 py-3 border-t">
    <!-- Header -->
    <div class="flex items-center justify-between mb-2">
      <span class="text-sm font-medium text-ink-gray-7">
        {{ __("Related Tickets") }}
        <span v-if="relatedTickets.data?.length" class="text-ink-gray-4 font-normal">
          ({{ relatedTickets.data.length }})
        </span>
      </span>
      <Button
        size="sm"
        variant="ghost"
        :label="__('Link')"
        @click="showLinkDialog = true"
      >
        <template #prefix>
          <LucidePlus class="h-3 w-3" />
        </template>
      </Button>
    </div>

    <!-- Loading -->
    <div v-if="relatedTickets.loading" class="text-sm text-ink-gray-4 py-1">
      {{ __("Loading…") }}
    </div>

    <!-- Empty state -->
    <div
      v-else-if="!relatedTickets.data?.length"
      class="text-sm text-ink-gray-4 py-1"
    >
      {{ __("No related tickets") }}
    </div>

    <!-- Ticket rows -->
    <ul v-else class="space-y-1.5" role="list">
      <li
        v-for="link in relatedTickets.data"
        :key="link.name"
        class="flex items-start gap-2 rounded border border-outline-gray-2 bg-surface-gray-1 px-2.5 py-2 text-sm hover:bg-surface-gray-2 transition-colors"
      >
        <div class="min-w-0 flex-1">
          <a
            :href="`/helpdesk/tickets/${link.ticket}`"
            class="font-medium text-blue-600 hover:underline text-xs"
            @click.prevent="router.push(`/tickets/${link.ticket}`)"
          >
            #{{ link.ticket }}
          </a>
          <p class="text-xs text-ink-gray-6 truncate mt-0.5" :title="link.ticket_subject">
            {{ link.ticket_subject || __("(No subject)") }}
          </p>
          <div class="flex flex-wrap gap-1 mt-1">
            <Badge
              :label="link.link_type"
              variant="subtle"
              theme="blue"
              size="sm"
            />
            <Badge
              v-if="link.ticket_status"
              :label="link.ticket_status"
              variant="subtle"
              :theme="statusTheme(link.ticket_status)"
              size="sm"
            />
          </div>
        </div>
        <button
          class="flex-shrink-0 mt-0.5 text-ink-gray-3 hover:text-red-500 transition-colors"
          :title="__('Remove link')"
          :aria-label="__('Remove link to #{0}', [link.ticket])"
          @click="confirmUnlink(link)"
        >
          <LucideX class="h-3.5 w-3.5" />
        </button>
      </li>
    </ul>

    <!-- Link Ticket Dialog -->
    <LinkTicketDialog
      v-if="showLinkDialog"
      :ticket-id="ticketId"
      @linked="onLinked"
      @close="showLinkDialog = false"
    />

    <!-- Unlink Confirmation -->
    <Dialog
      v-if="unlinkTarget"
      v-model="showUnlinkDialog"
      :options="{
        title: __('Remove Link'),
        size: 'sm',
      }"
    >
      <template #body-content>
        <p class="text-p-sm text-ink-gray-7">
          {{
            __(
              'Remove link to #{0}? This will also remove the reverse link.',
              [unlinkTarget.ticket]
            )
          }}
        </p>
      </template>
      <template #actions>
        <div class="flex gap-2 justify-end">
          <Button
            variant="subtle"
            :label="__('Cancel')"
            @click="cancelUnlink"
          />
          <Button
            variant="solid"
            theme="red"
            :label="__('Remove')"
            :loading="unlinkResource.loading"
            @click="doUnlink"
          />
        </div>
      </template>
    </Dialog>
  </div>
</template>

<script setup lang="ts">
import { Badge, Button, Dialog, createResource } from "frappe-ui";
import { ref, watch } from "vue";
import { useRouter } from "vue-router";
import LucidePlus from "~icons/lucide/plus";
import LucideX from "~icons/lucide/x";
import LinkTicketDialog from "./LinkTicketDialog.vue";

interface RelatedTicketRow {
  name: string;
  ticket: string;
  link_type: string;
  ticket_subject: string;
  ticket_status: string;
}

const props = defineProps<{ ticketId: string }>();
const router = useRouter();

const showLinkDialog = ref(false);
const unlinkTarget = ref<RelatedTicketRow | null>(null);
const showUnlinkDialog = ref(false);

const relatedTickets = createResource({
  url: "helpdesk.api.incident.get_related_tickets",
  params: { ticket: props.ticketId },
  auto: true,
});

watch(
  () => props.ticketId,
  (id) => {
    if (id) {
      relatedTickets.update({ params: { ticket: id } });
      relatedTickets.reload();
    }
  }
);

function statusTheme(status: string): string {
  const map: Record<string, string> = {
    Open: "green",
    Replied: "blue",
    Resolved: "gray",
    Closed: "gray",
    Duplicate: "orange",
    "On Hold": "yellow",
  };
  return map[status] ?? "gray";
}

function onLinked() {
  showLinkDialog.value = false;
  relatedTickets.reload();
}

function confirmUnlink(link: RelatedTicketRow) {
  unlinkTarget.value = link;
  showUnlinkDialog.value = true;
}

function cancelUnlink() {
  unlinkTarget.value = null;
  showUnlinkDialog.value = false;
}

const unlinkResource = createResource({
  url: "helpdesk.api.incident.unlink_tickets",
  onSuccess() {
    unlinkTarget.value = null;
    showUnlinkDialog.value = false;
    relatedTickets.reload();
  },
  onError(err: any) {
    const msg = err?.messages?.[0] || __("Failed to remove link.");
    console.error(msg);
  },
});

function doUnlink() {
  if (!unlinkTarget.value) return;
  unlinkResource.submit({
    ticket_a: props.ticketId,
    ticket_b: unlinkTarget.value.ticket,
  });
}
</script>
