<template>
  <Dialog v-model="show" :options="{ title: __('Transfer Chat') }">
    <template #body-content>
      <div class="space-y-3">
        <p class="text-sm text-gray-600">
          {{ __("Select an agent to transfer this conversation to:") }}
        </p>
        <div v-if="loadingAgents" class="text-sm text-gray-500">
          {{ __("Loading agents…") }}
        </div>
        <div v-else-if="agents.length === 0" class="text-sm text-gray-500">
          {{ __("No agents are currently available for transfer.") }}
        </div>
        <ul v-else class="space-y-1 max-h-60 overflow-y-auto">
          <li
            v-for="agent in agents"
            :key="agent.name"
            class="flex items-center gap-3 rounded px-2 py-2 cursor-pointer hover:bg-gray-100"
            :class="{ 'bg-blue-50': selected === agent.user }"
            @click="selected = agent.user"
          >
            <Avatar :label="agent.agent_name" :image="agent.user_image" size="sm" />
            <div class="flex-1 min-w-0">
              <p class="text-sm font-medium truncate">{{ agent.agent_name }}</p>
              <p class="text-xs text-gray-500 truncate">{{ agent.user }}</p>
            </div>
            <span class="inline-block h-2 w-2 rounded-full bg-green-500" />
          </li>
        </ul>
      </div>
    </template>
    <template #actions>
      <Button
        variant="solid"
        :label="__('Transfer')"
        :disabled="!selected"
        @click="handleTransfer"
      />
      <Button :label="__('Cancel')" @click="show = false" />
    </template>
  </Dialog>
</template>

<script setup lang="ts">
import { ref, watch } from "vue";
import { Avatar, Button, Dialog, createResource } from "frappe-ui";
import { useChatStore } from "@/stores/chat";
import { __ } from "@/translation";

const props = defineProps<{
  modelValue: boolean;
  sessionId: string;
}>();

const emit = defineEmits<{
  (e: "update:modelValue", v: boolean): void;
}>();

const show = ref(props.modelValue);
watch(
  () => props.modelValue,
  (v) => (show.value = v)
);
watch(show, (v) => emit("update:modelValue", v));

const chatStore = useChatStore();
const selected = ref<string>("");
const agents = ref<
  { name: string; user: string; agent_name: string; user_image: string; chat_availability: string }[]
>([]);
const loadingAgents = ref(false);

const transferTargetsResource = createResource({
  url: "helpdesk.api.chat.get_transfer_targets",
  auto: false,
  onSuccess(data: typeof agents.value) {
    agents.value = data;
    loadingAgents.value = false;
  },
});

watch(
  () => props.modelValue,
  (open) => {
    if (open) {
      selected.value = "";
      loadingAgents.value = true;
      transferTargetsResource.fetch();
    }
  }
);

function handleTransfer() {
  if (!selected.value) return;
  chatStore.transferSession(props.sessionId, selected.value);
  show.value = false;
}
</script>
