<template>
  <div class="flex flex-col h-full overflow-auto">
    <!-- Header -->
    <div class="flex items-center justify-between px-6 py-4 border-b border-outline-gray-2">
      <div class="flex items-center gap-2">
        <LucideAlertTriangle class="h-5 w-5 text-red-600" />
        <h1 class="text-lg font-semibold text-ink-gray-9">
          {{ __("Major Incidents") }}
        </h1>
        <Badge
          v-if="!incidents.loading && incidents.data?.length"
          :label="String(incidents.data.length)"
          theme="red"
          variant="subtle"
        />
      </div>
      <Button
        size="sm"
        variant="ghost"
        :label="__('Refresh')"
        :loading="incidents.loading"
        @click="incidents.reload()"
      >
        <template #prefix>
          <LucideRefreshCw class="h-3.5 w-3.5" />
        </template>
      </Button>
    </div>

    <!-- Loading -->
    <div
      v-if="incidents.loading"
      class="flex items-center justify-center flex-1 text-ink-gray-4"
    >
      <LoadingIndicator :scale="6" />
    </div>

    <!-- Empty state -->
    <div
      v-else-if="!incidents.data?.length"
      class="flex flex-col items-center justify-center flex-1 gap-3 text-ink-gray-4"
    >
      <LucideCheckCircle class="h-12 w-12 text-green-500" />
      <p class="text-base font-medium">{{ __("No active major incidents") }}</p>
      <p class="text-sm">{{ __("All clear — no tickets are currently flagged as major incidents.") }}</p>
    </div>

    <!-- Incident cards -->
    <div
      v-else
      class="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-3 gap-4 p-6"
    >
      <MajorIncidentCard
        v-for="incident in incidents.data"
        :key="incident.name"
        :incident="incident"
      />
    </div>
  </div>
</template>

<script setup lang="ts">
import MajorIncidentCard from "./MajorIncidentCard.vue";
import { Badge, Button, LoadingIndicator, createResource, usePageMeta } from "frappe-ui";
import LucideAlertTriangle from "~icons/lucide/alert-triangle";
import LucideCheckCircle from "~icons/lucide/check-circle";
import LucideRefreshCw from "~icons/lucide/refresh-cw";

usePageMeta(() => ({ title: "Major Incidents" }));

const incidents = createResource({
  url: "helpdesk.api.incident.get_major_incident_summary",
  auto: true,
});
</script>
