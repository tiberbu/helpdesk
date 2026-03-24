<template>
  <Dialog
    v-model="show"
    :options="{ title: __('Link a Knowledge Base Article'), size: 'sm' }"
    @close="emit('close')"
  >
    <template #body-content>
      <div class="flex flex-col gap-3">
        <!-- Article search -->
        <div>
          <label class="block text-xs font-medium text-ink-gray-6 mb-1">
            {{ __("Search Articles") }}
          </label>
          <Autocomplete
            :options="searchOptions"
            :placeholder="__('Search by title…')"
            v-model="selectedArticle"
            :filter-results="false"
            @update:query="onSearchQuery"
          />
        </div>

        <!-- Error -->
        <p v-if="errorMessage" class="text-sm text-red-600">
          {{ errorMessage }}
        </p>
      </div>
    </template>
    <template #actions>
      <div class="flex gap-2 justify-end">
        <Button variant="subtle" :label="__('Cancel')" @click="emit('close')" />
        <Button
          variant="solid"
          :label="__('Link Article')"
          :disabled="!selectedArticle?.value || linkResource.loading"
          :loading="linkResource.loading"
          @click="doLink"
        />
      </div>
    </template>
  </Dialog>
</template>

<script setup lang="ts">
import { Autocomplete, Button, Dialog, createResource } from "frappe-ui";
import { ref } from "vue";

const props = defineProps<{ ticketId: string }>();
const emit = defineEmits<{ linked: []; close: [] }>();

const show = ref(true);
const selectedArticle = ref<{ value: string; label: string; description?: string } | null>(null);
const errorMessage = ref("");
const searchOptions = ref<{ value: string; label: string; description?: string }[]>([]);

let searchTimer: ReturnType<typeof setTimeout> | null = null;

const searchResource = createResource({
  url: "helpdesk.api.knowledge_base.search_articles",
  onSuccess(data: { name: string; title: string; category_name: string }[]) {
    searchOptions.value = data.map((a) => ({
      value: a.name,
      label: a.title,
      description: a.category_name || "",
    }));
  },
});

function onSearchQuery(query: string) {
  if (searchTimer) clearTimeout(searchTimer);
  searchTimer = setTimeout(() => {
    searchResource.submit({ query: query || "" });
  }, 200);
}

const linkResource = createResource({
  url: "helpdesk.api.knowledge_base.link_article_to_ticket",
  onSuccess() {
    emit("linked");
  },
  onError(err: any) {
    const msgs = err?.messages || [];
    errorMessage.value = msgs[0] || __("Failed to link article.");
  },
});

function doLink() {
  errorMessage.value = "";
  if (!selectedArticle.value?.value) return;
  linkResource.submit({
    ticket: props.ticketId,
    article: selectedArticle.value.value,
  });
}
</script>
