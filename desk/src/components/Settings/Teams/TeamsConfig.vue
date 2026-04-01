<template>
  <TeamsList v-if="step === 'team-list'" @update:step="updateStep" />
  <NewTeam v-else-if="step === 'new-team'" @update:step="updateStep" />
  <TeamEdit
    v-else-if="step === 'team-edit'"
    @update:step="updateStep"
    :team-name="teamName"
  />
</template>

<script setup lang="ts">
import { onUnmounted, provide, Ref, ref } from "vue";
import TeamEdit from "./TeamEdit.vue";
import TeamsList from "./TeamsList.vue";
import { createListResource } from "frappe-ui";
import NewTeam from "./NewTeam.vue";
import { TeamListResourceSymbol } from "@/types";

type TeamStep = "team-list" | "team-edit" | "new-team";

const step: Ref<TeamStep> = ref("team-list");
const teamName: Ref<string> = ref("");
function updateStep(newStep: TeamStep, team?: string): void {
  step.value = newStep;
  teamName.value = team;
}
const teamsSearchQuery = ref("");

const teams = createListResource({
  doctype: "HD Team",
  cache: ["Teams"],
  fields: ["name", "support_level", "parent_team"],
  auto: true,
  orderBy: "modified desc",
  start: 0,
  pageLength: 20,
});

// Shared support-levels resource for dropdowns
const supportLevels = createListResource({
  doctype: "HD Support Level",
  fields: ["name", "level_name", "level_order", "display_name"],
  orderBy: "level_order asc",
  auto: true,
});

// Full teams list for parent-team dropdown (unfiltered/unpaginated up to 100)
const allTeamsForLinks = createListResource({
  doctype: "HD Team",
  fields: ["name", "support_level", "parent_team"],
  pageLength: 100,
  auto: true,
});

provide("teamsSearchQuery", teamsSearchQuery);
provide(TeamListResourceSymbol, teams);
provide("supportLevels", supportLevels);
provide("allTeamsForLinks", allTeamsForLinks);

onUnmounted(() => {
  teamsSearchQuery.value = "";
  teams.filters = {};
});
</script>

<style scoped></style>
