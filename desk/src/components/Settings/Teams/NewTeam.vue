<template>
  <SettingsLayoutBase>
    <template #title>
      <div class="flex items-center gap-2">
        <Button
          variant="ghost"
          icon-left="chevron-left"
          :label="teamData.name || __('New Team')"
          size="md"
          @click="goBack()"
          class="cursor-pointer -ml-4 hover:bg-transparent focus:bg-transparent focus:outline-none focus:ring-0 focus:ring-offset-0 focus-visible:none active:bg-transparent active:outline-none active:ring-0 active:ring-offset-0 active:text-ink-gray-5 font-semibold text-ink-gray-7 text-lg hover:opacity-70 !pr-0"
        />
        <Badge
          variant="subtle"
          theme="orange"
          size="sm"
          :label="__('Unsaved')"
          v-if="isDirty"
        />
      </div>
    </template>
    <template #header-actions>
      <Button
        :label="__('Save')"
        variant="solid"
        @click="saveTeam()"
        :disabled="!isDirty"
        :loading="teamsList.insert.loading"
      />
    </template>
    <template #content>
      <div class="flex flex-col gap-4">
        <!-- Team Name -->
        <div class="space-y-1.5">
          <FormControl
            v-model="teamData.name"
            :label="__('Team Name')"
            :placeholder="__('Product Experts')"
            maxlength="50"
            required
            @change="validateData('name')"
          />
          <ErrorMessage :message="errors.name" />
        </div>

        <!-- Support Level -->
        <div class="space-y-1.5">
          <FormLabel :label="__('Support Level')" />
          <Autocomplete
            :value="getSupportLevelOption(teamData.support_level)"
            :options="supportLevelOptions"
            :placeholder="__('Select support level…')"
            @change="(opt) => onSupportLevelChange(opt)"
          />
        </div>

        <!-- Parent Team -->
        <div class="space-y-1.5">
          <FormLabel :label="__('Parent Team')" />
          <Autocomplete
            :value="getTeamOption(teamData.parent_team)"
            :options="parentTeamOptions"
            :placeholder="__('Select parent team…')"
            @change="(opt) => { teamData.parent_team = opt?.value || '' }"
          />
        </div>

        <!-- Territory -->
        <div class="space-y-1.5">
          <FormControl
            v-model="teamData.territory"
            :label="__('Territory')"
            :placeholder="__('e.g. Nairobi County')"
            type="text"
          />
        </div>

        <!-- Members -->
        <div class="flex flex-col gap-1.5">
          <FormLabel :label="__('Members')" required />
          <div class="flex">
            <AgentSelector
              v-model="teamData.agents"
              @change="validateData('agents')"
            />
          </div>
          <ErrorMessage :message="errors.agents" />
        </div>
      </div>
    </template>
  </SettingsLayoutBase>
  <ConfirmDialog
    v-model="showConfirmDialog.show"
    :title="showConfirmDialog.title"
    :message="showConfirmDialog.message"
    :onConfirm="showConfirmDialog.onConfirm"
  />
</template>

<script setup lang="ts">
import { computed, inject, onMounted, ref } from "vue";
import SettingsLayoutBase from "@/components/layouts/SettingsLayoutBase.vue";
import { Badge, ErrorMessage, FormControl, FormLabel, toast } from "frappe-ui";
import { __ } from "@/translation";
import AgentSelector from "./components/AgentSelector.vue";
import Autocomplete from "@/components/Autocomplete.vue";
import { useAgentStore } from "@/stores/agent";
import { TeamListResourceSymbol } from "@/types";
import ConfirmDialog from "../../ConfirmDialog.vue";

interface E {
  (event: "update:step", step: string, team?: string): void;
}

const emit = defineEmits<E>();

const teamsList = inject(TeamListResourceSymbol);
const supportLevels = inject<any>("supportLevels");
const allTeamsForLinks = inject<any>("allTeamsForLinks");
const { agents } = useAgentStore();

const isDirty = computed(() => {
  return (
    teamData.value.name ||
    teamData.value.agents.length ||
    teamData.value.support_level ||
    teamData.value.parent_team ||
    teamData.value.territory
  );
});

const showConfirmDialog = ref({
  show: false,
  title: "",
  message: "",
  onConfirm: () => {},
});

const teamData = ref({
  name: "",
  agents: [] as string[],
  support_level: "",
  parent_team: "",
  territory: "",
});

const errors = ref({
  name: "",
  agents: "",
});

// ── Options computed ──────────────────────────────────────────────────────────

const supportLevelOptions = computed(() => {
  const levels: any[] = supportLevels?.data || [];
  return levels.map((l) => ({
    label: l.display_name || l.level_name || l.name,
    value: l.name,
    level_order: l.level_order ?? 0,
  }));
});

const parentTeamOptions = computed(() => {
  const teams: any[] = allTeamsForLinks?.data || [];
  const selOpt = supportLevelOptions.value.find(
    (o) => o.value === teamData.value.support_level
  );
  const selOrder: number = selOpt?.level_order ?? -1;

  return teams
    .filter((t) => {
      if (selOrder >= 0 && teamData.value.support_level) {
        const teamSLOpt = supportLevelOptions.value.find(
          (o) => o.value === t.support_level
        );
        return (teamSLOpt?.level_order ?? -1) > selOrder;
      }
      return true;
    })
    .map((t) => ({ label: t.name, value: t.name }));
});

// ── Helpers ───────────────────────────────────────────────────────────────────

function getSupportLevelOption(val: string) {
  if (!val) return null;
  return supportLevelOptions.value.find((o) => o.value === val) || null;
}

function getTeamOption(val: string) {
  if (!val) return null;
  return parentTeamOptions.value.find((o) => o.value === val) || null;
}

function onSupportLevelChange(opt: any) {
  teamData.value.support_level = opt?.value || "";
  // Clear parent team if it no longer matches the level filter
  if (teamData.value.parent_team && opt) {
    const stillValid = parentTeamOptions.value.some(
      (o) => o.value === teamData.value.parent_team
    );
    if (!stillValid) {
      teamData.value.parent_team = "";
    }
  }
}

// ── Navigation ────────────────────────────────────────────────────────────────

const goBack = () => {
  const confirmDialogInfo = {
    show: true,
    title: __("Unsaved changes"),
    message: __(
      "Are you sure you want to go back? Unsaved changes will be lost."
    ),
    onConfirm: goBack,
  };
  if (isDirty.value && !showConfirmDialog.value.show) {
    showConfirmDialog.value = confirmDialogInfo;
    return;
  }

  // Workaround fix for settings modal not closing after going back
  setTimeout(() => {
    emit("update:step", "team-list");
  }, 250);
  showConfirmDialog.value.show = false;
};

// ── Save ──────────────────────────────────────────────────────────────────────

const saveTeam = () => {
  validateData();
  if (Object.values(errors.value).some((error) => error)) {
    toast.error(__("Please fill all required fields"));
    return;
  }
  teamsList.insert.submit(
    {
      team_name: teamData.value.name,
      users: teamData.value.agents.map((agent) => ({ user: agent })),
      support_level: teamData.value.support_level || null,
      parent_team: teamData.value.parent_team || null,
      territory: teamData.value.territory || null,
    },
    {
      onSuccess: (data) => {
        toast.success(__("Team created"));
        emit("update:step", "team-edit", data.name);
      },
    }
  );
};

// ── Validation ────────────────────────────────────────────────────────────────

const validateData = (key?: string) => {
  const validateField = (field: string) => {
    if (key && field !== key) return;

    switch (field) {
      case "name":
        teamData.value.name?.length == 0
          ? (errors.value.name = "Name is required")
          : (errors.value.name = "");
        break;
      case "agents":
        teamData.value.agents.length == 0
          ? (errors.value.agents = "At least one team member is required")
          : (errors.value.agents = "");
        break;
    }
  };

  if (key) {
    validateField(key);
  } else {
    (Object.keys(errors.value) as string[]).forEach(validateField);
  }

  return errors.value;
};

onMounted(() => {
  if (agents.loading || agents.data?.length || agents.list.promise) {
    return;
  }
  agents.fetch();
});
</script>
