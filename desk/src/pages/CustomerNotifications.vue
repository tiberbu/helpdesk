<template>
  <LayoutHeader>
    <template #left-header>
      <Breadcrumbs
        :items="[
          { label: __('Notifications'), route: { name: 'CustomerNotifications' } },
        ]"
      />
    </template>
    <template #right-header>
      <Button
        v-if="notificationStore.data.length"
        :label="__('Mark all as read')"
        @click="() => notificationStore.clear.submit()"
      >
        <template #prefix>
          <LucideCheckCheck class="h-4 w-4" />
        </template>
      </Button>
    </template>
  </LayoutHeader>

  <div v-if="notificationStore.data.length" class="divide-y text-base">
    <RouterLink
      v-for="n in notificationStore.data"
      :key="n.name"
      class="flex cursor-pointer items-start gap-3.5 px-5 py-3 hover:bg-gray-50"
      :to="getRoute(n)"
      @click="() => notificationStore.read(n.reference_ticket)"
    >
      <UserAvatar :name="n.user_from" size="lg" class="mt-0.5 shrink-0" />
      <div class="flex-1 min-w-0">
        <div class="flex items-start justify-between gap-2">
          <div class="leading-5">
            <span class="font-medium text-gray-900">{{ n.user_from }}</span>
            <span class="text-gray-600 ml-1" v-if="n.notification_type === 'Ticket Reply'">
              {{ __("replied on ticket") }}
              <span class="font-medium text-gray-800">#{{ n.reference_ticket }}</span>
            </span>
            <span class="text-gray-600 ml-1" v-else-if="n.notification_type === 'Ticket Status Change'">
              {{ n.message || __("updated your ticket") }}
              <span class="font-medium text-gray-800">#{{ n.reference_ticket }}</span>
            </span>
            <span class="text-gray-600 ml-1" v-else>
              {{ n.message }}
            </span>
          </div>
          <div v-if="!n.read" class="mt-1.5 h-2 w-2 rounded-full bg-blue-500 shrink-0" />
        </div>

        <!-- Reply preview -->
        <p
          v-if="n.notification_type === 'Ticket Reply' && n.message"
          class="mt-1 text-sm text-gray-500 line-clamp-2 leading-relaxed"
        >
          {{ n.message }}
        </p>

        <div class="mt-1 text-xs text-gray-400">
          {{ dayjs.tz(n.creation).fromNow() }}
        </div>
      </div>
    </RouterLink>
  </div>

  <div v-else class="flex flex-1 flex-col items-center justify-center gap-3 mt-24 text-center px-6">
    <LucideBell class="h-12 w-12 text-gray-300" />
    <p class="text-base font-medium text-gray-500">{{ __("You're all caught up!") }}</p>
    <p class="text-sm text-gray-400">{{ __("Notifications will appear here when your tickets are updated.") }}</p>
  </div>
</template>

<script setup lang="ts">
import { LayoutHeader } from "@/components";
import { UserAvatar } from "@/components";
import { dayjs } from "@/dayjs";
import { useNotificationStore } from "@/stores/notification";
import { Notification } from "@/types";
import { __ } from "@/translation";
import { Breadcrumbs, Button } from "frappe-ui";
import LucideBell from "~icons/lucide/bell";
import LucideCheckCheck from "~icons/lucide/check-check";

const notificationStore = useNotificationStore();

function getRoute(n: Notification) {
  if (n.reference_ticket) {
    return {
      name: "TicketCustomer",
      params: { ticketId: n.reference_ticket },
      hash: n.reference_comment ? `#${n.reference_comment}` : undefined,
    };
  }
  return { name: "TicketsCustomer" };
}
</script>

<style scoped>
.line-clamp-2 {
  display: -webkit-box;
  -webkit-line-clamp: 2;
  -webkit-box-orient: vertical;
  overflow: hidden;
}
</style>
