<template>
  <div
    class="rounded-lg border-2 border-red-200 bg-red-50 p-4 flex flex-col gap-3 hover:shadow-sm transition-shadow"
  >
    <!-- Ticket link & subject -->
    <div class="flex items-start gap-2">
      <LucideAlertTriangle class="h-4 w-4 text-red-600 flex-shrink-0 mt-0.5" />
      <div class="min-w-0 flex-1">
        <a
          :href="`/helpdesk/tickets/${incident.name}`"
          class="font-semibold text-red-700 hover:underline text-sm"
          @click.prevent="router.push(`/tickets/${incident.name}`)"
        >
          #{{ incident.name }} — {{ incident.subject }}
        </a>
      </div>
    </div>

    <!-- Meta row -->
    <div class="flex flex-wrap gap-2 text-xs text-ink-gray-5">
      <Badge :label="incident.status || 'Unknown'" theme="red" variant="subtle" />
      <Badge
        v-if="incident.priority"
        :label="incident.priority"
        theme="orange"
        variant="subtle"
      />
    </div>

    <!-- Elapsed time & linked tickets -->
    <div class="flex items-center gap-4 text-xs text-ink-gray-5">
      <span>
        <LucideClock class="inline h-3 w-3 mr-0.5" />
        {{ __("Open for {0}", [elapsedText]) }}
      </span>
      <span v-if="incident.linked_ticket_count">
        <LucideLink class="inline h-3 w-3 mr-0.5" />
        {{ __("{0} linked ticket(s)", [incident.linked_ticket_count]) }}
      </span>
    </div>
  </div>
</template>

<script setup lang="ts">
import { Badge } from "frappe-ui";
import { computed } from "vue";
import { useRouter } from "vue-router";
import LucideAlertTriangle from "~icons/lucide/alert-triangle";
import LucideClock from "~icons/lucide/clock";
import LucideLink from "~icons/lucide/link";

interface MajorIncident {
  name: string;
  subject: string;
  status: string;
  priority: string;
  major_incident_flagged_at: string;
  linked_ticket_count: number;
  elapsed_minutes: number;
}

const props = defineProps<{ incident: MajorIncident }>();
const router = useRouter();

const elapsedText = computed(() => {
  const mins = props.incident.elapsed_minutes || 0;
  if (mins < 60) return `${mins}m`;
  if (mins < 1440) return `${Math.floor(mins / 60)}h ${mins % 60}m`;
  return `${Math.floor(mins / 1440)}d`;
});
</script>
