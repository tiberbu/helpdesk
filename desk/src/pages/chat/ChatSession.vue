<template>
  <div class="flex h-full flex-col">
    <!-- Header -->
    <div class="flex items-center justify-between border-b px-4 py-3">
      <div class="flex items-center gap-3">
        <Avatar :label="session?.customer_name || '?'" size="md" />
        <div>
          <p class="font-semibold text-gray-800">
            {{ session?.customer_name || session?.customer_email }}
          </p>
          <p class="text-xs text-gray-500">{{ session?.customer_email }}</p>
        </div>
      </div>
      <div class="flex items-center gap-2">
        <span
          class="inline-flex items-center rounded-full px-2 py-0.5 text-xs font-medium"
          :class="statusBadgeClass"
        >
          {{ session?.status }}
        </span>
        <Button
          v-if="session?.ticket"
          size="sm"
          :label="__('View Ticket')"
          @click="openTicket"
        />
        <Button
          v-if="session?.status === 'active'"
          size="sm"
          :label="__('Transfer')"
          @click="showTransfer = true"
        />
        <Button
          v-if="session?.status === 'active'"
          size="sm"
          theme="red"
          :label="__('End Chat')"
          @click="handleEnd"
        />
      </div>
    </div>

    <!-- Messages -->
    <div ref="scrollEl" class="flex-1 overflow-y-auto px-4 py-3 space-y-3">
      <div v-if="messages.length === 0" class="text-center text-sm text-gray-400 mt-8">
        {{ __("No messages yet.") }}
      </div>
      <div
        v-for="msg in messages"
        :key="msg.message_id"
        class="flex"
        :class="msg.sender_type === 'agent' ? 'justify-end' : 'justify-start'"
      >
        <!-- System message -->
        <div
          v-if="msg.sender_type === 'system'"
          class="w-full text-center text-xs text-gray-400 italic py-1"
        >
          {{ msg.content }}
        </div>
        <!-- Chat bubble -->
        <div
          v-else
          class="max-w-[70%] rounded-2xl px-4 py-2 text-sm"
          :class="
            msg.sender_type === 'agent'
              ? 'bg-blue-600 text-white'
              : 'bg-gray-100 text-gray-900'
          "
        >
          <!-- eslint-disable-next-line vue/no-v-html -->
          <span v-html="msg.content" />
          <p
            class="mt-1 text-xs"
            :class="msg.sender_type === 'agent' ? 'text-blue-200' : 'text-gray-400'"
          >
            {{ formatTime(msg.sent_at) }}
          </p>
        </div>
      </div>
      <div v-if="isCustomerTyping" class="flex justify-start">
        <div class="bg-gray-100 rounded-2xl px-4 py-2 text-sm text-gray-500 italic">
          {{ __("Typing…") }}
        </div>
      </div>
    </div>

    <!-- Input -->
    <div
      v-if="session?.status === 'active'"
      class="border-t px-4 py-3 flex gap-2 items-end"
    >
      <textarea
        v-model="draft"
        class="flex-1 resize-none rounded-lg border border-gray-300 px-3 py-2 text-sm focus:outline-none focus:ring-2 focus:ring-blue-500"
        rows="2"
        :placeholder="__('Type a message…')"
        @keydown.enter.prevent="sendMessage"
      />
      <Button
        variant="solid"
        :label="__('Send')"
        :disabled="!draft.trim()"
        @click="sendMessage"
      />
    </div>
    <div
      v-else-if="session?.status === 'waiting'"
      class="border-t px-4 py-4 flex items-center justify-center"
    >
      <Button
        variant="solid"
        :label="__('Accept Chat')"
        @click="chatStore.acceptSession(sessionId)"
      />
    </div>

    <TransferDialog
      v-model="showTransfer"
      :session-id="sessionId"
    />
  </div>
</template>

<script setup lang="ts">
import { computed, nextTick, ref, watch } from "vue";
import { Avatar, Button, createResource, toast } from "frappe-ui";
import { useRouter } from "vue-router";
import { useChatStore } from "@/stores/chat";
import TransferDialog from "@/components/chat/TransferDialog.vue";
import { __ } from "@/translation";
import { useAuthStore } from "@/stores/auth";

const props = defineProps<{ sessionId: string }>();

const chatStore = useChatStore();
const authStore = useAuthStore();
const router = useRouter();
const showTransfer = ref(false);
const draft = ref("");
const scrollEl = ref<HTMLElement | null>(null);

const session = computed(() =>
  chatStore.sessions.find((s) => s.session_id === props.sessionId) ?? null
);
const messages = computed(
  () => chatStore.messagesBySession[props.sessionId] ?? []
);
const isCustomerTyping = computed(
  () => chatStore.typingBySessions[props.sessionId] ?? false
);

const statusBadgeClass = computed(() => {
  const map: Record<string, string> = {
    waiting: "bg-yellow-100 text-yellow-800",
    active: "bg-green-100 text-green-800",
    ended: "bg-gray-100 text-gray-700",
  };
  return map[session.value?.status ?? ""] ?? "bg-gray-100 text-gray-700";
});

// Scroll to bottom on new messages
watch(
  () => messages.value.length,
  async () => {
    await nextTick();
    if (scrollEl.value) {
      scrollEl.value.scrollTop = scrollEl.value.scrollHeight;
    }
  }
);

const sendResource = createResource({
  url: "helpdesk.api.chat.send_message",
  auto: false,
  onSuccess(data: { message_id: string; sent_at: string }) {
    chatStore.addMessage(props.sessionId, {
      message_id: data.message_id,
      sender_type: "agent",
      sender_email: authStore.userId,
      content: draft.value,
      sent_at: data.sent_at,
      is_read: true,
    });
    draft.value = "";
  },
  onError(err: { message?: string }) {
    toast.create({ message: err?.message ?? "Failed to send message." });
  },
});

function sendMessage() {
  const content = draft.value.trim();
  if (!content) return;
  // Agents call send_message — they are authenticated via session, token ignored
  sendResource.submit({
    session_id: props.sessionId,
    content,
    token: "__agent__",
  });
}

function handleEnd() {
  chatStore.endSession(props.sessionId);
  router.push({ name: "ChatDashboard" });
}

function openTicket() {
  if (session.value?.ticket) {
    router.push({
      name: "TicketAgent",
      params: { ticketId: session.value.ticket },
    });
  }
}

function formatTime(dt: string) {
  try {
    return new Date(dt).toLocaleTimeString([], {
      hour: "2-digit",
      minute: "2-digit",
    });
  } catch {
    return dt;
  }
}
</script>
