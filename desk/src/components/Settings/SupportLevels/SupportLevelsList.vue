<template>
  <SettingsLayoutBase
    :title="__('Support Levels')"
    :description="
      __('Configure escalation tiers for tickets. Levels are ordered from lowest (L0) to highest.')
    "
  >
    <template #header-actions>
      <Button
        :label="__('New')"
        theme="gray"
        variant="solid"
        icon-left="plus"
        @click="emit('update:step', 'form', '')"
      />
    </template>
    <template #content>
      <!-- Visual Hierarchy -->
      <div
        v-if="!levels.loading && levels.data?.length > 1"
        class="mb-6 flex flex-wrap items-center gap-2"
      >
        <template v-for="(level, idx) in sortedLevels" :key="level.name">
          <div
            class="flex items-center gap-1.5 rounded-md px-3 py-1.5 text-sm font-medium border"
            :style="level.color ? { borderColor: level.color, color: level.color } : {}"
            :class="!level.color ? 'border-gray-300 text-gray-700 bg-gray-50' : 'bg-white'"
          >
            <span class="font-semibold text-xs text-gray-500">L{{ level.level_order }}</span>
            <span>{{ level.level_name }}</span>
          </div>
          <div
            v-if="idx < sortedLevels.length - 1"
            class="flex items-center"
          >
            <component
              v-if="level.allow_escalation_to_next"
              :is="LucideArrowRight"
              class="h-4 w-4 text-blue-500"
            />
            <component
              v-else
              :is="LucideArrowRight"
              class="h-4 w-4 text-gray-300"
            />
          </div>
        </template>
        <span
          v-if="sortedLevels.length && !sortedLevels[sortedLevels.length - 1]?.allow_escalation_to_next"
          class="rounded bg-red-50 px-2 py-0.5 text-xs font-medium text-red-600"
        >
          {{ __("Terminal") }}
        </span>
      </div>

      <!-- Column Headers -->
      <div
        v-if="!levels.loading && levels.data?.length"
        class="grid grid-cols-12 gap-2 text-sm text-gray-500 mb-1 px-2"
      >
        <div class="col-span-1">{{ __("Order") }}</div>
        <div class="col-span-4">{{ __("Level Name") }}</div>
        <div class="col-span-3">{{ __("Display Name") }}</div>
        <div class="col-span-2 text-center">{{ __("Escalation") }}</div>
        <div class="col-span-2 text-center">{{ __("Auto-Escalate") }}</div>
      </div>
      <hr v-if="!levels.loading && levels.data?.length" class="mb-2" />

      <!-- List -->
      <div v-if="!levels.loading && levels.data?.length > 0" class="-ml-2">
        <div
          v-for="(level, index) in sortedLevels"
          :key="level.name"
        >
          <div
            class="grid grid-cols-12 gap-2 items-center cursor-pointer hover:bg-gray-50 rounded px-2 py-3"
            @click="() => emit('update:step', 'form', level.name)"
          >
            <!-- Order badge -->
            <div class="col-span-1">
              <span
                class="inline-flex items-center justify-center h-6 w-6 rounded-full text-xs font-bold"
                :style="level.color ? { backgroundColor: level.color + '22', color: level.color } : {}"
                :class="!level.color ? 'bg-gray-100 text-gray-600' : ''"
              >
                {{ level.level_order }}
              </span>
            </div>
            <!-- Level Name -->
            <div class="col-span-4 text-sm font-medium text-ink-gray-7">
              {{ level.level_name }}
            </div>
            <!-- Display Name -->
            <div class="col-span-3 text-sm text-gray-500">
              {{ level.display_name || "—" }}
            </div>
            <!-- Escalation -->
            <div class="col-span-2 flex justify-center">
              <Badge
                v-if="level.allow_escalation_to_next"
                :label="__('Allowed')"
                theme="blue"
                variant="subtle"
                size="sm"
              />
              <Badge
                v-else
                :label="__('Terminal')"
                theme="red"
                variant="subtle"
                size="sm"
              />
            </div>
            <!-- Auto-Escalate -->
            <div class="col-span-2 flex justify-center">
              <span
                v-if="level.auto_escalate_on_breach && level.allow_escalation_to_next"
                class="text-xs text-gray-600"
              >
                {{ level.auto_escalate_minutes }}m
              </span>
              <span v-else class="text-xs text-gray-400">—</span>
            </div>
          </div>
          <!-- Dropdown Actions -->
          <div class="absolute right-10" style="margin-top: -2.5rem;">
            <Dropdown
              placement="right"
              :options="dropdownOptions(level)"
            >
              <Button
                icon="more-horizontal"
                variant="ghost"
                size="sm"
                @click.stop="isConfirmingDelete = false"
              />
            </Dropdown>
          </div>
          <hr v-if="index !== sortedLevels.length - 1" class="mx-2" />
        </div>
      </div>

      <!-- Loading State -->
      <div v-if="levels.loading" class="flex mt-28 justify-center w-full">
        <Button :loading="levels.loading" variant="ghost" class="w-full" size="2xl" />
      </div>

      <!-- Empty State -->
      <div
        v-if="!levels.loading && !levels.data?.length"
        class="flex flex-col items-center justify-center gap-4 h-full min-h-40"
      >
        <div class="p-4 size-14 rounded-full bg-surface-gray-1 flex justify-center items-center">
          <component :is="LucideLayers" class="size-6 text-ink-gray-6" />
        </div>
        <div class="flex flex-col items-center gap-1">
          <div class="text-base font-medium text-ink-gray-6">
            {{ __("No support levels configured") }}
          </div>
          <div class="text-p-sm text-ink-gray-5 text-center max-w-60">
            {{ __("Add support levels to define escalation tiers for your service desk.") }}
          </div>
        </div>
        <Button
          :label="__('New Support Level')"
          variant="outline"
          icon-left="plus"
          @click="emit('update:step', 'form', '')"
        />
      </div>
    </template>
  </SettingsLayoutBase>
</template>

<script setup lang="ts">
import { Badge, Dropdown, toast } from "frappe-ui";
import { computed, inject, markRaw, ref } from "vue";
import SettingsLayoutBase from "@/components/layouts/SettingsLayoutBase.vue";
import { __ } from "@/translation";
import { SupportLevelListResourceSymbol, type SupportLevel } from "./types";
import LucideArrowRight from "~icons/lucide/arrow-right";
import LucideLayers from "~icons/lucide/layers";

interface E {
  (event: "update:step", step: string, levelName: string): void;
}
const emit = defineEmits<E>();

const levels = inject(SupportLevelListResourceSymbol) as any;
const isConfirmingDelete = ref(false);

const sortedLevels = computed<SupportLevel[]>(() => {
  if (!levels.data) return [];
  return [...levels.data].sort((a, b) => a.level_order - b.level_order);
});

const dropdownOptions = (level: SupportLevel) => [
  {
    label: __("Edit"),
    icon: "edit",
    onClick: () => emit("update:step", "form", level.name),
  },
  {
    label: isConfirmingDelete.value ? __("Click again to confirm") : __("Delete"),
    icon: "trash-2",
    onClick: () => deleteLevel(level),
  },
];

const deleteLevel = (level: SupportLevel) => {
  if (!isConfirmingDelete.value) {
    isConfirmingDelete.value = true;
    return;
  }
  levels.delete.submit(level.name, {
    onSuccess: () => {
      toast.success(__("Support level deleted"));
      isConfirmingDelete.value = false;
    },
    onError: () => {
      toast.error(__("Failed to delete support level"));
      isConfirmingDelete.value = false;
    },
  });
};
</script>
