<template>
  <Dialog
    v-model="model"
    :options="{ title: __('Create Ticket from Template'), size: 'md' }"
  >
    <template #body-content>
      <div class="space-y-4">
        <div class="space-y-1">
          <label class="block text-sm text-gray-700">
            {{ __("Select Template") }}
          </label>
          <FormControl
            type="select"
            :options="templateOptions"
            v-model="selectedTemplate"
            :placeholder="__('Choose a template')"
          />
        </div>

        <div v-if="selectedTemplate && templatePreview.data" class="space-y-2 border rounded-lg p-4 bg-gray-50">
          <h4 class="font-medium text-sm text-gray-900">{{ __("Template Preview") }}</h4>
          <div class="text-xs text-gray-600 space-y-1">
            <div v-if="templatePreview.data.default_values?.priority">
              <span class="font-medium">{{ __("Priority") }}:</span> {{ templatePreview.data.default_values.priority }}
            </div>
            <div v-if="templatePreview.data.default_values?.ticket_type">
              <span class="font-medium">{{ __("Type") }}:</span> {{ templatePreview.data.default_values.ticket_type }}
            </div>
            <div v-if="templatePreview.data.default_values?.category">
              <span class="font-medium">{{ __("Category") }}:</span> {{ templatePreview.data.default_values.category }}
            </div>
            <div v-if="templatePreview.data.default_values?.agent_group">
              <span class="font-medium">{{ __("Team") }}:</span> {{ templatePreview.data.default_values.agent_group }}
            </div>
          </div>
        </div>

        <div class="float-right flex space-x-2">
          <Button
            :label="__('Cancel')"
            theme="gray"
            variant="outline"
            @click="model = false"
          />
          <Button
            :label="__('Continue')"
            theme="gray"
            variant="solid"
            :disabled="!selectedTemplate"
            @click="createFromTemplate"
          />
        </div>
      </div>
    </template>
  </Dialog>
</template>

<script setup lang="ts">
import { __ } from "@/translation";
import { Dialog, FormControl, Button, createListResource, createResource } from "frappe-ui";
import { computed, ref, watch } from "vue";
import { useRouter } from "vue-router";

const model = defineModel<boolean>();
const router = useRouter();

const selectedTemplate = ref("");

// Fetch all available templates
const templatesResource = createListResource({
  doctype: "HD Ticket Template",
  fields: ["name", "template_name"],
  auto: true,
  cache: "ticketTemplates",
});

const templateOptions = computed(() => {
  const templates = templatesResource.data || [];
  return templates.map((t) => ({
    label: t.template_name || t.name,
    value: t.name,
  }));
});

// Fetch template details for preview
const templatePreview = createResource({
  url: "helpdesk.helpdesk.doctype.hd_ticket_template.api.get_one",
  makeParams: () => ({
    name: selectedTemplate.value,
  }),
});

watch(selectedTemplate, (newVal) => {
  if (newVal) {
    templatePreview.fetch();
  }
});

function createFromTemplate() {
  if (!selectedTemplate.value) return;

  model.value = false;
  router.push({
    name: "TicketAgentNew",
    params: { templateId: selectedTemplate.value },
  });
}
</script>
