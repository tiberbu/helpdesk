<template>
  <div
    v-if="ticket?.doc?.is_major_incident"
    class="border-t px-5 py-4"
  >
    <div class="flex items-center gap-2 mb-3">
      <LucideClipboardCheck class="h-4 w-4 text-red-600" />
      <span class="text-sm font-semibold text-ink-gray-9">
        {{ __("Post-Incident Review") }}
      </span>
    </div>

    <!-- Root Cause Summary -->
    <div class="mb-3">
      <label class="block text-xs font-medium text-ink-gray-6 mb-1">
        {{ __("Root Cause Summary") }}
      </label>
      <div v-if="!editingField.root_cause_summary">
        <p
          v-if="ticket.doc.root_cause_summary"
          class="text-sm text-ink-gray-8 whitespace-pre-wrap cursor-pointer hover:bg-surface-gray-1 rounded p-1 -ml-1"
          @click="startEdit('root_cause_summary')"
        >{{ ticket.doc.root_cause_summary }}</p>
        <button
          v-else
          class="text-xs text-ink-gray-4 hover:text-ink-gray-6 italic"
          @click="startEdit('root_cause_summary')"
        >{{ __("Click to add root cause...") }}</button>
      </div>
      <div v-else>
        <textarea
          v-model="fieldValues.root_cause_summary"
          class="w-full text-sm border border-outline-gray-2 rounded p-2 resize-none focus:outline-none focus:border-outline-gray-4"
          rows="3"
          :placeholder="__('Describe the root cause...')"
        />
        <div class="flex gap-2 mt-1">
          <button
            class="text-xs text-blue-600 hover:underline"
            :disabled="saving"
            @click="saveField('root_cause_summary')"
          >{{ __("Save") }}</button>
          <button
            class="text-xs text-ink-gray-4 hover:underline"
            @click="cancelEdit('root_cause_summary')"
          >{{ __("Cancel") }}</button>
        </div>
      </div>
    </div>

    <!-- Corrective Actions -->
    <div class="mb-3">
      <label class="block text-xs font-medium text-ink-gray-6 mb-1">
        {{ __("Corrective Actions") }}
      </label>
      <div v-if="!editingField.corrective_actions">
        <p
          v-if="ticket.doc.corrective_actions"
          class="text-sm text-ink-gray-8 whitespace-pre-wrap cursor-pointer hover:bg-surface-gray-1 rounded p-1 -ml-1"
          @click="startEdit('corrective_actions')"
        >{{ ticket.doc.corrective_actions }}</p>
        <button
          v-else
          class="text-xs text-ink-gray-4 hover:text-ink-gray-6 italic"
          @click="startEdit('corrective_actions')"
        >{{ __("Click to add corrective actions...") }}</button>
      </div>
      <div v-else>
        <textarea
          v-model="fieldValues.corrective_actions"
          class="w-full text-sm border border-outline-gray-2 rounded p-2 resize-none focus:outline-none focus:border-outline-gray-4"
          rows="3"
          :placeholder="__('List corrective actions taken...')"
        />
        <div class="flex gap-2 mt-1">
          <button
            class="text-xs text-blue-600 hover:underline"
            :disabled="saving"
            @click="saveField('corrective_actions')"
          >{{ __("Save") }}</button>
          <button
            class="text-xs text-ink-gray-4 hover:underline"
            @click="cancelEdit('corrective_actions')"
          >{{ __("Cancel") }}</button>
        </div>
      </div>
    </div>

    <!-- Prevention Measures -->
    <div>
      <label class="block text-xs font-medium text-ink-gray-6 mb-1">
        {{ __("Prevention Measures") }}
      </label>
      <div v-if="!editingField.prevention_measures">
        <p
          v-if="ticket.doc.prevention_measures"
          class="text-sm text-ink-gray-8 whitespace-pre-wrap cursor-pointer hover:bg-surface-gray-1 rounded p-1 -ml-1"
          @click="startEdit('prevention_measures')"
        >{{ ticket.doc.prevention_measures }}</p>
        <button
          v-else
          class="text-xs text-ink-gray-4 hover:text-ink-gray-6 italic"
          @click="startEdit('prevention_measures')"
        >{{ __("Click to add prevention measures...") }}</button>
      </div>
      <div v-else>
        <textarea
          v-model="fieldValues.prevention_measures"
          class="w-full text-sm border border-outline-gray-2 rounded p-2 resize-none focus:outline-none focus:border-outline-gray-4"
          rows="3"
          :placeholder="__('List measures to prevent recurrence...')"
        />
        <div class="flex gap-2 mt-1">
          <button
            class="text-xs text-blue-600 hover:underline"
            :disabled="saving"
            @click="saveField('prevention_measures')"
          >{{ __("Save") }}</button>
          <button
            class="text-xs text-ink-gray-4 hover:underline"
            @click="cancelEdit('prevention_measures')"
          >{{ __("Cancel") }}</button>
        </div>
      </div>
    </div>
  </div>
</template>

<script setup lang="ts">
import { TicketSymbol } from "@/types";
import { toast } from "frappe-ui";
import { inject, reactive, ref, watch } from "vue";
import LucideClipboardCheck from "~icons/lucide/clipboard-check";

type ReviewField = "root_cause_summary" | "corrective_actions" | "prevention_measures";

const ticket = inject(TicketSymbol);

const saving = ref(false);

const editingField = reactive<Record<ReviewField, boolean>>({
  root_cause_summary: false,
  corrective_actions: false,
  prevention_measures: false,
});

const fieldValues = reactive<Record<ReviewField, string>>({
  root_cause_summary: "",
  corrective_actions: "",
  prevention_measures: "",
});

// Keep fieldValues in sync when doc loads/changes
watch(
  () => ticket?.value?.doc,
  (doc) => {
    if (!doc) return;
    fieldValues.root_cause_summary = doc.root_cause_summary || "";
    fieldValues.corrective_actions = doc.corrective_actions || "";
    fieldValues.prevention_measures = doc.prevention_measures || "";
  },
  { immediate: true, deep: false }
);

function startEdit(field: ReviewField) {
  // Reset to current doc value before editing
  fieldValues[field] = ticket?.value?.doc?.[field] || "";
  editingField[field] = true;
}

function cancelEdit(field: ReviewField) {
  editingField[field] = false;
  fieldValues[field] = ticket?.value?.doc?.[field] || "";
}

function saveField(field: ReviewField) {
  saving.value = true;
  ticket?.value?.setValue.submit(
    { [field]: fieldValues[field] },
    {
      onSuccess() {
        editingField[field] = false;
        saving.value = false;
      },
      onError(err: any) {
        saving.value = false;
        const msg = err?.messages?.[0] || __("Failed to save.");
        toast.error(msg);
      },
    }
  );
}
</script>
