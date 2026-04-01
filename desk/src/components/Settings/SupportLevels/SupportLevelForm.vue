<template>
  <SettingsLayoutBase>
    <template #title>
      <div class="flex items-center gap-2">
        <Button
          variant="ghost"
          icon-left="chevron-left"
          :label="isEditMode ? (formData.level_name || levelName) : __('New Support Level')"
          size="md"
          @click="goBack()"
          class="cursor-pointer -ml-4 hover:bg-transparent focus:bg-transparent focus:outline-none focus:ring-0 focus:ring-offset-0 active:bg-transparent active:text-ink-gray-5 font-semibold text-ink-gray-7 text-lg hover:opacity-70 !pr-0"
        />
        <Badge
          v-if="isDirty"
          variant="subtle"
          theme="orange"
          size="sm"
          :label="__('Unsaved')"
        />
      </div>
    </template>
    <template #header-actions>
      <div class="flex gap-2">
        <Button
          v-if="isEditMode"
          :label="__('Delete')"
          variant="outline"
          theme="red"
          @click="confirmDelete()"
          :loading="levels.delete?.loading"
        />
        <Button
          :label="__('Save')"
          variant="solid"
          :disabled="!isDirty"
          :loading="saving"
          @click="saveLevel()"
        />
      </div>
    </template>
    <template #content>
      <div class="flex flex-col gap-6 max-w-lg">
        <!-- Level Name -->
        <div class="space-y-1.5">
          <FormControl
            v-model="formData.level_name"
            :label="__('Level Name')"
            :placeholder="__('e.g. Sub-County Support')"
            required
            @change="markDirty"
          />
          <ErrorMessage :message="errors.level_name" />
        </div>

        <!-- Level Order -->
        <div class="space-y-1.5">
          <FormControl
            v-model.number="formData.level_order"
            :label="__('Level Order')"
            type="number"
            :placeholder="__('0')"
            :description="__('Lower numbers = lower tiers (e.g. 0 = L0 / frontline, 3 = L3 / specialist)')"
            required
            @change="markDirty"
          />
          <ErrorMessage :message="errors.level_order" />
        </div>

        <!-- Display Name -->
        <FormControl
          v-model="formData.display_name"
          :label="__('Display Name')"
          :placeholder="__('e.g. L0 - Sub-County Support')"
          :description="__('Optional label shown in ticket views')"
          @change="markDirty"
        />

        <!-- Color -->
        <div class="space-y-1.5">
          <label class="block text-sm font-medium text-ink-gray-7">
            {{ __("Color") }}
          </label>
          <div class="flex items-center gap-3">
            <input
              type="color"
              v-model="formData.color"
              @input="markDirty"
              class="h-9 w-14 cursor-pointer rounded border border-gray-300 p-0.5"
            />
            <span class="text-sm text-gray-500">{{ formData.color || __("None") }}</span>
            <Button
              v-if="formData.color"
              variant="ghost"
              icon="x"
              size="sm"
              @click="formData.color = ''; markDirty()"
            />
          </div>
        </div>

        <hr />

        <!-- Allow Escalation -->
        <div class="flex items-start gap-3">
          <input
            type="checkbox"
            id="allow_escalation"
            v-model="formData.allow_escalation_to_next"
            class="mt-0.5 h-4 w-4 rounded border-gray-300 text-blue-600"
            @change="markDirty"
          />
          <div>
            <label for="allow_escalation" class="text-sm font-medium text-ink-gray-7 cursor-pointer">
              {{ __("Allow Escalation to Next Level") }}
            </label>
            <p class="text-p-sm text-gray-500 mt-0.5">
              {{ __("Tickets at this level can be escalated to the next higher support tier.") }}
            </p>
          </div>
        </div>

        <!-- Auto-Escalate on Breach -->
        <div
          v-if="formData.allow_escalation_to_next"
          class="flex items-start gap-3"
        >
          <input
            type="checkbox"
            id="auto_escalate"
            v-model="formData.auto_escalate_on_breach"
            class="mt-0.5 h-4 w-4 rounded border-gray-300 text-blue-600"
            @change="markDirty"
          />
          <div>
            <label for="auto_escalate" class="text-sm font-medium text-ink-gray-7 cursor-pointer">
              {{ __("Auto-Escalate on SLA Breach") }}
            </label>
            <p class="text-p-sm text-gray-500 mt-0.5">
              {{ __("Automatically escalate tickets when the SLA response window is breached.") }}
            </p>
          </div>
        </div>

        <!-- Auto-Escalate Minutes -->
        <div
          v-if="formData.allow_escalation_to_next && formData.auto_escalate_on_breach"
          class="space-y-1.5"
        >
          <FormControl
            v-model.number="formData.auto_escalate_minutes"
            :label="__('Auto-Escalate After (Minutes)')"
            type="number"
            :placeholder="__('60')"
            :description="__('If no response within this many minutes, auto-escalate the ticket.')"
            @change="markDirty"
          />
        </div>
      </div>
    </template>
  </SettingsLayoutBase>

  <ConfirmDialog
    v-model="showConfirmBack.show"
    :title="__('Unsaved changes')"
    :message="__('Are you sure you want to go back? Unsaved changes will be lost.')"
    :onConfirm="() => { showConfirmBack.show = false; doGoBack(); }"
    :onCancel="() => { showConfirmBack.show = false; }"
  />

  <ConfirmDialog
    v-model="showConfirmDelete"
    :title="__('Delete Support Level')"
    :message="__('Are you sure you want to delete this support level? This action cannot be undone.')"
    :onConfirm="doDelete"
    :onCancel="() => { showConfirmDelete = false; }"
  />
</template>

<script setup lang="ts">
import { Badge, createDocumentResource, ErrorMessage, FormControl, toast } from "frappe-ui";
import { computed, inject, onMounted, ref } from "vue";
import SettingsLayoutBase from "@/components/layouts/SettingsLayoutBase.vue";
import ConfirmDialog from "@/components/ConfirmDialog.vue";
import { __ } from "@/translation";
import { SupportLevelListResourceSymbol } from "./types";

interface Props {
  levelName?: string;
}

interface E {
  (event: "update:step", step: string, levelName?: string): void;
}

const props = withDefaults(defineProps<Props>(), { levelName: "" });
const emit = defineEmits<E>();

const levels = inject(SupportLevelListResourceSymbol) as any;
const isEditMode = computed(() => Boolean(props.levelName));

const formData = ref({
  level_name: "",
  level_order: 0,
  display_name: "",
  color: "",
  allow_escalation_to_next: true,
  auto_escalate_on_breach: false,
  auto_escalate_minutes: 60,
});

const errors = ref({
  level_name: "",
  level_order: "",
});

const isDirty = ref(false);
const saving = ref(false);
const showConfirmBack = ref({ show: false });
const showConfirmDelete = ref(false);

// Document resource for edit mode
const docResource = isEditMode.value
  ? createDocumentResource({
      doctype: "HD Support Level",
      name: props.levelName,
      auto: true,
      onSuccess: (doc: any) => {
        formData.value = {
          level_name: doc.level_name || "",
          level_order: doc.level_order ?? 0,
          display_name: doc.display_name || "",
          color: doc.color || "",
          allow_escalation_to_next: Boolean(doc.allow_escalation_to_next),
          auto_escalate_on_breach: Boolean(doc.auto_escalate_on_breach),
          auto_escalate_minutes: doc.auto_escalate_minutes ?? 60,
        };
        isDirty.value = false;
      },
    })
  : null;

function markDirty() {
  isDirty.value = true;
}

function validate(): boolean {
  errors.value.level_name = "";
  errors.value.level_order = "";

  let valid = true;
  if (!formData.value.level_name?.trim()) {
    errors.value.level_name = __("Level Name is required");
    valid = false;
  }
  if (formData.value.level_order === null || formData.value.level_order === undefined || String(formData.value.level_order) === "") {
    errors.value.level_order = __("Level Order is required");
    valid = false;
  }
  return valid;
}

async function saveLevel() {
  if (!validate()) {
    toast.error(__("Please fill all required fields"));
    return;
  }

  saving.value = true;

  const payload = {
    level_name: formData.value.level_name.trim(),
    level_order: Number(formData.value.level_order),
    display_name: formData.value.display_name || "",
    color: formData.value.color || "",
    allow_escalation_to_next: formData.value.allow_escalation_to_next ? 1 : 0,
    auto_escalate_on_breach: formData.value.auto_escalate_on_breach ? 1 : 0,
    auto_escalate_minutes: formData.value.auto_escalate_on_breach
      ? Number(formData.value.auto_escalate_minutes)
      : 0,
  };

  if (isEditMode.value && docResource) {
    docResource.setValue.submit(payload, {
      onSuccess: () => {
        docResource.save.submit(
          {},
          {
            onSuccess: () => {
              toast.success(__("Support level updated"));
              isDirty.value = false;
              saving.value = false;
              levels.reload();
            },
            onError: (err: any) => {
              toast.error(err?.message || __("Failed to save"));
              saving.value = false;
            },
          }
        );
      },
      onError: (err: any) => {
        toast.error(err?.message || __("Failed to save"));
        saving.value = false;
      },
    });
  } else {
    levels.insert.submit(payload, {
      onSuccess: () => {
        toast.success(__("Support level created"));
        isDirty.value = false;
        saving.value = false;
        emit("update:step", "list");
      },
      onError: (err: any) => {
        toast.error(err?.message || __("Failed to create support level"));
        saving.value = false;
      },
    });
  }
}

function goBack() {
  if (isDirty.value) {
    showConfirmBack.value = { show: true };
    return;
  }
  doGoBack();
}

function doGoBack() {
  setTimeout(() => {
    emit("update:step", "list");
  }, 100);
}

function confirmDelete() {
  showConfirmDelete.value = true;
}

function doDelete() {
  showConfirmDelete.value = false;
  levels.delete.submit(props.levelName, {
    onSuccess: () => {
      toast.success(__("Support level deleted"));
      emit("update:step", "list");
    },
    onError: (err: any) => {
      toast.error(err?.message || __("Failed to delete"));
    },
  });
}

onMounted(() => {
  if (!isEditMode.value) {
    // Set sensible default for new levels based on existing count
    const existing = levels.data || [];
    const maxOrder = existing.reduce((max: number, l: any) => Math.max(max, l.level_order || 0), -1);
    formData.value.level_order = maxOrder + 1;
  }
});
</script>
