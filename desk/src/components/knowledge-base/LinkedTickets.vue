<template>
  <div class="mt-6 border-t pt-4">
    <div class="flex items-center justify-between mb-3">
      <h3 class="text-sm font-semibold text-ink-gray-7">
        {{ __("Linked Tickets") }}
        <span v-if="linkedTickets.data?.count" class="text-ink-gray-4 font-normal">
          ({{ linkedTickets.data.count }})
        </span>
      </h3>
    </div>

    <!-- Loading -->
    <div v-if="linkedTickets.loading" class="text-sm text-ink-gray-4 py-1">
      {{ __("Loading…") }}
    </div>

    <!-- Empty state -->
    <div
      v-else-if="!linkedTickets.data?.count"
      class="text-sm text-ink-gray-4 py-1"
    >
      {{ __("No tickets have linked this article yet.") }}
    </div>

    <!-- Ticket rows -->
    <ul v-else class="space-y-2" role="list">
      <li
        v-for="t in linkedTickets.data.tickets"
        :key="t.name"
        class="flex items-start gap-2 rounded border border-outline-gray-2 bg-surface-gray-1 px-3 py-2 text-sm hover:bg-surface-gray-2 transition-colors"
      >
        <div class="min-w-0 flex-1">
          <a
            class="font-medium text-blue-600 hover:underline text-xs cursor-pointer"
            @click.prevent="router.push(`/tickets/${t.name}`)"
          >
            #{{ t.name }}
          </a>
          <p class="text-xs text-ink-gray-6 truncate mt-0.5" :title="t.subject">
            {{ t.subject || __("(No subject)") }}
          </p>
        </div>
        <Badge
          v-if="t.status"
          :label="t.status"
          variant="subtle"
          :theme="statusTheme(t.status)"
          size="sm"
          class="mt-0.5 flex-shrink-0"
        />
      </li>
    </ul>

    <!-- Show "and N more" if count > 10 -->
    <p
      v-if="linkedTickets.data?.count > linkedTickets.data?.tickets?.length"
      class="mt-2 text-xs text-ink-gray-4"
    >
      {{
        __(
          "…and {0} more ticket(s)",
          [linkedTickets.data.count - linkedTickets.data.tickets.length]
        )
      }}
    </p>
  </div>
</template>

<script setup lang="ts">
import { Badge, createResource } from "frappe-ui";
import { watch } from "vue";
import { useRouter } from "vue-router";

const props = defineProps<{ articleId: string }>();
const router = useRouter();

const linkedTickets = createResource({
  url: "helpdesk.api.knowledge_base.get_linked_tickets",
  params: { article: props.articleId },
  auto: true,
});

watch(
  () => props.articleId,
  (id) => {
    if (id) {
      linkedTickets.update({ params: { article: id } });
      linkedTickets.reload();
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
</script>
