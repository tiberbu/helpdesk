<template>
  <div class="flex items-center gap-2">
    <span class="text-sm text-gray-600">{{ __("Status") }}:</span>
    <Dropdown :options="availabilityOptions">
      <Button :label="currentLabel" size="sm">
        <template #prefix>
          <span
            class="inline-block h-2 w-2 rounded-full"
            :class="statusDotClass"
          />
        </template>
        <template #suffix>
          <LucideChevronDown class="h-3 w-3" />
        </template>
      </Button>
    </Dropdown>
  </div>
</template>

<script setup lang="ts">
import { computed } from "vue";
import { Button, Dropdown } from "frappe-ui";
import LucideChevronDown from "~icons/lucide/chevron-down";
import { useChatStore } from "@/stores/chat";
import { __ } from "@/translation";

const chatStore = useChatStore();

const availabilityOptions = [
  {
    label: __("Online"),
    onClick: () => chatStore.setAvailability("Online"),
  },
  {
    label: __("Away"),
    onClick: () => chatStore.setAvailability("Away"),
  },
  {
    label: __("Offline"),
    onClick: () => chatStore.setAvailability("Offline"),
  },
];

const currentLabel = computed(() => chatStore.availability);

const statusDotClass = computed(() => {
  const map: Record<string, string> = {
    Online: "bg-green-500",
    Away: "bg-yellow-400",
    Offline: "bg-gray-400",
  };
  return map[chatStore.availability] ?? "bg-gray-400";
});
</script>
