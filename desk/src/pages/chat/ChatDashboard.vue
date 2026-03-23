<template>
  <div class="flex h-full overflow-hidden">
    <!-- Sidebar: queue + active sessions -->
    <div class="w-72 flex-shrink-0 border-r flex flex-col bg-white">
      <!-- Header -->
      <div class="px-4 py-4 border-b space-y-2">
        <div class="flex items-center justify-between">
          <h2 class="text-base font-semibold text-gray-800">{{ __("Live Chat") }}</h2>
          <AgentAvailability />
        </div>
      </div>

      <!-- Waiting queue -->
      <div v-if="chatStore.waitingSessions.length > 0" class="border-b">
        <p class="px-4 pt-3 pb-1 text-xs font-semibold uppercase text-gray-500 tracking-wider">
          {{ __("Queue") }}
          <Badge :label="String(chatStore.waitingSessions.length)" theme="orange" class="ml-1" />
        </p>
        <ul>
          <li
            v-for="s in chatStore.waitingSessions"
            :key="s.session_id"
            class="flex items-center gap-3 px-4 py-3 cursor-pointer hover:bg-orange-50 border-l-4 border-l-transparent"
            :class="{ 'border-l-orange-400 bg-orange-50': selectedId === s.session_id }"
            @click="select(s.session_id)"
          >
            <Avatar :label="s.customer_name || '?'" size="sm" />
            <div class="flex-1 min-w-0">
              <p class="text-sm font-medium truncate">
                {{ s.customer_name || s.customer_email }}
              </p>
              <p class="text-xs text-gray-500">{{ __("Waiting") }}</p>
            </div>
            <span class="inline-block h-2 w-2 rounded-full bg-yellow-400 flex-shrink-0" />
          </li>
        </ul>
      </div>

      <!-- Active sessions -->
      <div class="flex-1 overflow-y-auto">
        <p class="px-4 pt-3 pb-1 text-xs font-semibold uppercase text-gray-500 tracking-wider">
          {{ __("Active") }}
          <Badge :label="String(chatStore.activeSessions.length)" theme="green" class="ml-1" />
        </p>
        <p v-if="chatStore.activeSessions.length === 0" class="px-4 text-sm text-gray-400">
          {{ __("No active chats.") }}
        </p>
        <ul>
          <li
            v-for="s in chatStore.activeSessions"
            :key="s.session_id"
            class="flex items-center gap-3 px-4 py-3 cursor-pointer hover:bg-blue-50 border-l-4 border-l-transparent"
            :class="{ 'border-l-blue-500 bg-blue-50': selectedId === s.session_id }"
            @click="select(s.session_id)"
          >
            <Avatar :label="s.customer_name || '?'" size="sm" />
            <div class="flex-1 min-w-0">
              <p class="text-sm font-medium truncate">
                {{ s.customer_name || s.customer_email }}
              </p>
              <p class="text-xs text-gray-500 truncate">{{ s.customer_email }}</p>
            </div>
            <span
              v-if="s.unread_count > 0"
              class="flex-shrink-0 inline-flex items-center justify-center h-5 w-5 rounded-full bg-blue-600 text-white text-xs font-bold"
            >
              {{ s.unread_count > 9 ? "9+" : s.unread_count }}
            </span>
          </li>
        </ul>
      </div>
    </div>

    <!-- Main pane -->
    <div class="flex-1 overflow-hidden flex flex-col">
      <div v-if="selectedId" class="h-full overflow-hidden">
        <ChatSession :session-id="selectedId" />
      </div>
      <div
        v-else
        class="flex h-full items-center justify-center flex-col gap-3 text-gray-400"
      >
        <LucideMessageCircle class="h-12 w-12 opacity-30" />
        <p class="text-sm">{{ __("Select a chat to get started.") }}</p>
        <p v-if="chatStore.waitingSessions.length > 0" class="text-sm font-medium text-orange-500">
          {{ chatStore.waitingSessions.length }} {{ __("chat(s) waiting in queue") }}
        </p>
      </div>
    </div>
  </div>
</template>

<script setup lang="ts">
import { computed, onMounted } from "vue";
import { Avatar, Badge } from "frappe-ui";
import LucideMessageCircle from "~icons/lucide/message-circle";
import { useChatStore } from "@/stores/chat";
import AgentAvailability from "@/components/chat/AgentAvailability.vue";
import ChatSession from "./ChatSession.vue";
import { __ } from "@/translation";
import { useRoute, useRouter } from "vue-router";

const chatStore = useChatStore();
const route = useRoute();
const router = useRouter();

const selectedId = computed(() => chatStore.currentSessionId);

onMounted(() => {
  chatStore.init();
  // If navigated to /chat/:sessionId, select that session
  if (route.params.sessionId) {
    chatStore.selectSession(route.params.sessionId as string);
  }
});

function select(sessionId: string) {
  chatStore.selectSession(sessionId);
  router.push({ name: "ChatSession", params: { sessionId } });
}
</script>
