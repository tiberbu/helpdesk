<template>
  <div class="px-5 py-3 border-t">
    <!-- Header -->
    <div class="flex items-center justify-between mb-2">
      <span class="text-sm font-medium text-ink-gray-7">
        {{ __("Linked Articles") }}
        <span v-if="linkedArticles.data?.length" class="text-ink-gray-4 font-normal">
          ({{ linkedArticles.data.length }})
        </span>
      </span>
      <div class="flex items-center gap-1">
        <Button
          size="sm"
          variant="ghost"
          :label="__('Create Article')"
          :title="__('Create new article pre-filled from this ticket')"
          @click="createFromTicket"
        >
          <template #prefix>
            <LucideFilePlus class="h-3 w-3" />
          </template>
        </Button>
        <Button
          size="sm"
          variant="ghost"
          :label="__('Link')"
          @click="showLinkDialog = true"
        >
          <template #prefix>
            <LucidePlus class="h-3 w-3" />
          </template>
        </Button>
      </div>
    </div>

    <!-- Loading -->
    <div v-if="linkedArticles.loading" class="text-sm text-ink-gray-4 py-1">
      {{ __("Loading…") }}
    </div>

    <!-- Empty state -->
    <div
      v-else-if="!linkedArticles.data?.length"
      class="text-sm text-ink-gray-4 py-1"
    >
      {{ __("No linked articles") }}
    </div>

    <!-- Article rows -->
    <ul v-else class="space-y-1.5" role="list">
      <li
        v-for="link in linkedArticles.data"
        :key="link.name"
        class="flex items-start gap-2 rounded border border-outline-gray-2 bg-surface-gray-1 px-2.5 py-2 text-sm hover:bg-surface-gray-2 transition-colors"
      >
        <div class="min-w-0 flex-1">
          <a
            class="font-medium text-blue-600 hover:underline text-xs"
            @click.prevent="router.push(`/articles/${link.article}`)"
          >
            {{ link.article_title || link.article }}
          </a>
        </div>
        <button
          class="flex-shrink-0 mt-0.5 text-ink-gray-3 hover:text-red-500 transition-colors"
          :title="__('Remove link')"
          :aria-label="__('Remove article link')"
          @click="confirmRemove(link)"
        >
          <LucideX class="h-3.5 w-3.5" />
        </button>
      </li>
    </ul>

    <!-- Article Link Dialog -->
    <ArticleLinkDialog
      v-if="showLinkDialog"
      :ticket-id="ticketId"
      @linked="onLinked"
      @close="showLinkDialog = false"
    />

    <!-- Remove Confirmation -->
    <Dialog
      v-if="removeTarget"
      v-model="showRemoveDialog"
      :options="{
        title: __('Remove Article Link'),
        size: 'sm',
      }"
    >
      <template #body-content>
        <p class="text-p-sm text-ink-gray-7">
          {{
            __(
              "Remove link to article \"{0}\"?",
              [removeTarget.article_title || removeTarget.article]
            )
          }}
        </p>
      </template>
      <template #actions>
        <div class="flex gap-2 justify-end">
          <Button
            variant="subtle"
            :label="__('Cancel')"
            @click="cancelRemove"
          />
          <Button
            variant="solid"
            theme="red"
            :label="__('Remove')"
            :loading="removeResource.loading"
            @click="doRemove"
          />
        </div>
      </template>
    </Dialog>
  </div>
</template>

<script setup lang="ts">
import { Button, Dialog, createResource, toast } from "frappe-ui";
import { ref, watch } from "vue";
import { useRouter } from "vue-router";
import LucidePlus from "~icons/lucide/plus";
import LucideX from "~icons/lucide/x";
import LucideFilePlus from "~icons/lucide/file-plus";
import ArticleLinkDialog from "@/components/knowledge-base/ArticleLinkDialog.vue";

interface LinkedArticleRow {
  name: string;
  article: string;
  article_title: string;
}

const props = defineProps<{ ticketId: string }>();
const router = useRouter();

const showLinkDialog = ref(false);
const removeTarget = ref<LinkedArticleRow | null>(null);
const showRemoveDialog = ref(false);

const linkedArticles = createResource({
  url: "frappe.client.get",
  params: {
    doctype: "HD Ticket",
    name: props.ticketId,
  },
  auto: true,
  transform(data: any) {
    return (data?.linked_articles || []) as LinkedArticleRow[];
  },
});

watch(
  () => props.ticketId,
  (id) => {
    if (id) {
      linkedArticles.update({
        params: {
          doctype: "HD Ticket",
          name: id,
        },
      });
      linkedArticles.reload();
    }
  }
);

function onLinked() {
  showLinkDialog.value = false;
  linkedArticles.reload();
}

function confirmRemove(link: LinkedArticleRow) {
  removeTarget.value = link;
  showRemoveDialog.value = true;
}

function cancelRemove() {
  removeTarget.value = null;
  showRemoveDialog.value = false;
}

const removeResource = createResource({
  url: "helpdesk.api.knowledge_base.remove_article_link",
  onSuccess() {
    removeTarget.value = null;
    showRemoveDialog.value = false;
    linkedArticles.reload();
  },
  onError(err: any) {
    const msg = err?.messages?.[0] || __("Failed to remove link.");
    toast.error(msg);
  },
});

function doRemove() {
  if (!removeTarget.value) return;
  removeResource.submit({
    ticket: props.ticketId,
    article: removeTarget.value.article,
  });
}

const prefillResource = createResource({
  url: "helpdesk.api.knowledge_base.prefill_article_from_ticket",
  onSuccess(data: { title: string; content: string; category: string; source_ticket: string }) {
    sessionStorage.setItem(
      "hd_article_prefill",
      JSON.stringify(data)
    );
    // Navigate to new article page under the returned category (param is optional)
    router.push({ name: "NewArticle", params: data.category ? { id: data.category } : {} });
  },
  onError(err: any) {
    const msg = err?.messages?.[0] || __("Failed to prefill article.");
    toast.error(msg);
  },
});

function createFromTicket() {
  prefillResource.submit({ ticket: props.ticketId });
}
</script>
