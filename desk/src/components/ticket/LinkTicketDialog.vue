<template>
  <Dialog
    v-model="show"
    :options="{ title: __('Link a Ticket'), size: 'sm' }"
    @close="emit('close')"
  >
    <template #body-content>
      <div class="flex flex-col gap-4">
        <!-- Ticket search -->
        <div>
          <label class="block text-xs font-medium text-ink-gray-6 mb-1">
            {{ __("Search Ticket") }}
          </label>
          <Autocomplete
            :options="searchOptions"
            :placeholder="__('Search by ID or subject…')"
            v-model="selectedTicket"
            :filter-results="false"
            @update:query="onSearchQuery"
          />
        </div>

        <!-- Link type -->
        <FormControl
          type="select"
          :label="__('Link Type')"
          v-model="selectedLinkType"
          :options="linkTypeOptions"
        />

        <!-- Description hint -->
        <p
          v-if="linkTypeDescription"
          class="text-xs text-ink-gray-5 -mt-2"
        >
          {{ linkTypeDescription }}
        </p>

        <!-- Error -->
        <p v-if="errorMessage" class="text-sm text-red-600">
          {{ errorMessage }}
        </p>
      </div>
    </template>
    <template #actions>
      <div class="flex gap-2 justify-end">
        <Button variant="subtle" :label="__('Cancel')" @click="emit('close')" />
        <Button
          variant="solid"
          :label="__('Link Ticket')"
          :disabled="!selectedTicket?.value || !selectedLinkType || linkResource.loading"
          :loading="linkResource.loading"
          @click="doLink"
        />
      </div>
    </template>
  </Dialog>
</template>

<script setup lang="ts">
import { Autocomplete, Button, Dialog, FormControl, createResource } from "frappe-ui";
import { computed, ref } from "vue";

const props = defineProps<{ ticketId: string }>();
const emit = defineEmits<{ linked: []; close: [] }>();

const show = ref(true);
const selectedTicket = ref<{ value: string; label: string } | null>(null);
const selectedLinkType = ref("");
const errorMessage = ref("");
const searchOptions = ref<{ value: string; label: string; description?: string }[]>([]);

const linkTypeOptions = [
  { label: __("Select link type"), value: "" },
  { label: __("Related to"), value: "Related to" },
  { label: __("Caused by"), value: "Caused by" },
  { label: __("Duplicate of"), value: "Duplicate of" },
];

const DESCRIPTIONS: Record<string, string> = {
  "Related to": __("This ticket is related to the selected ticket (no status change)."),
  "Caused by": __("This ticket was caused by the selected ticket."),
  "Duplicate of": __("This ticket is a duplicate — it will be auto-closed when linked."),
};

const linkTypeDescription = computed(
  () => DESCRIPTIONS[selectedLinkType.value] ?? ""
);

// Debounce helper
let searchTimer: ReturnType<typeof setTimeout> | null = null;

const searchResource = createResource({
  url: "frappe.client.get_list",
  onSuccess(data: { name: string; subject: string; status: string }[]) {
    searchOptions.value = data.map((t) => ({
      value: t.name,
      label: `#${t.name}`,
      description: t.subject,
    }));
  },
});

function onSearchQuery(query: string) {
  if (searchTimer) clearTimeout(searchTimer);
  searchTimer = setTimeout(() => {
    if (!query || query.length < 1) {
      searchOptions.value = [];
      return;
    }
    searchResource.submit({
      doctype: "HD Ticket",
      filters: JSON.stringify([["name", "!=", props.ticketId]]),
      or_filters: JSON.stringify([
        ["name", "like", `%${query}%`],
        ["subject", "like", `%${query}%`],
      ]),
      fields: JSON.stringify(["name", "subject", "status"]),
      limit: 10,
    });
  }, 200);
}

const linkResource = createResource({
  url: "helpdesk.api.incident.link_tickets",
  onSuccess() {
    emit("linked");
  },
  onError(err: any) {
    const msgs = err?.messages || [];
    errorMessage.value = msgs[0] || __("Failed to link tickets.");
  },
});

function doLink() {
  errorMessage.value = "";
  if (!selectedTicket.value?.value || !selectedLinkType.value) return;
  linkResource.submit({
    ticket_a: props.ticketId,
    ticket_b: selectedTicket.value.value,
    link_type: selectedLinkType.value,
  });
}
</script>
