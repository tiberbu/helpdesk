<template>
  <SupportLevelsList
    v-if="step === 'list'"
    @update:step="updateStep"
  />
  <SupportLevelForm
    v-else-if="step === 'form'"
    :levelName="editingLevelName"
    @update:step="updateStep"
  />
</template>

<script setup lang="ts">
import { onUnmounted, provide, ref, Ref } from "vue";
import { createListResource } from "frappe-ui";
import SupportLevelsList from "./SupportLevelsList.vue";
import SupportLevelForm from "./SupportLevelForm.vue";
import { SupportLevelListResourceSymbol } from "./types";

type SupportLevelStep = "list" | "form";

const step: Ref<SupportLevelStep> = ref("list");
const editingLevelName: Ref<string> = ref("");

function updateStep(newStep: SupportLevelStep, levelName?: string): void {
  step.value = newStep;
  editingLevelName.value = levelName || "";
}

const supportLevels = createListResource({
  doctype: "HD Support Level",
  cache: ["SupportLevels"],
  fields: [
    "name",
    "level_name",
    "level_order",
    "display_name",
    "allow_escalation_to_next",
    "auto_escalate_on_breach",
    "auto_escalate_minutes",
    "color",
  ],
  orderBy: "level_order asc",
  pageLength: 99,
  auto: true,
});

provide(SupportLevelListResourceSymbol, supportLevels);

onUnmounted(() => {
  supportLevels.filters = {};
});
</script>
