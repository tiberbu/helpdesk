<template>
  <div
    class="flex items-center gap-3 px-4 py-3 hover:bg-gray-50"
    :class="{ 'bg-red-50': variant === 'overdue' }"
  >
    <!-- Article info -->
    <div class="min-w-0 flex-1">
      <a
        :href="`/helpdesk/kb/articles/${article.name}`"
        class="block truncate text-sm font-medium text-blue-700 hover:underline"
        :aria-label="__('View article: {0}', [article.title])"
      >
        {{ article.title }}
      </a>
      <div class="mt-0.5 flex items-center gap-2 text-xs text-gray-500">
        <span>{{ article.author }}</span>
        <span aria-hidden="true">·</span>
        <span :class="variant === 'overdue' ? 'text-red-600 font-medium' : 'text-yellow-600'">
          {{ daysLabel }}
        </span>
      </div>
    </div>

    <!-- Action buttons -->
    <div class="flex shrink-0 items-center gap-1">
      <!-- Mark Reviewed -->
      <button
        class="rounded px-2 py-1 text-xs font-medium text-green-700 hover:bg-green-50 focus:outline-none focus-visible:ring-2 focus-visible:ring-green-500"
        :aria-label="__('Mark article reviewed: {0}', [article.title])"
        :disabled="markingReviewed"
        @click="handleMarkReviewed"
      >
        {{ __("Reviewed") }}
      </button>

      <!-- Edit -->
      <a
        :href="`/helpdesk/kb/articles/${article.name}`"
        class="rounded px-2 py-1 text-xs font-medium text-gray-600 hover:bg-gray-100 focus:outline-none focus-visible:ring-2 focus-visible:ring-gray-400"
        :aria-label="__('Edit article: {0}', [article.title])"
      >
        {{ __("Edit") }}
      </a>

      <!-- Archive -->
      <button
        class="rounded px-2 py-1 text-xs font-medium text-red-600 hover:bg-red-50 focus:outline-none focus-visible:ring-2 focus-visible:ring-red-400"
        :aria-label="__('Archive article: {0}', [article.title])"
        :disabled="archiving"
        @click="handleArchive"
      >
        {{ __("Archive") }}
      </button>
    </div>
  </div>
</template>

<script setup lang="ts">
import { computed, ref } from "vue";
import { createResource, toast } from "frappe-ui";
import { __ } from "@/translation";

interface ArticleRow {
  name: string;
  title: string;
  review_date: string;
  author: string;
  reviewed_by: string | null;
  days_overdue: number;
}

const props = defineProps<{
  article: ArticleRow;
  variant: "overdue" | "upcoming";
}>();

const emit = defineEmits<{
  reviewed: [articleName: string];
  archived: [articleName: string];
}>();

const markingReviewed = ref(false);
const archiving = ref(false);

const daysLabel = computed(() => {
  const d = props.article.days_overdue;
  if (d > 0) {
    return __("{0} day(s) overdue", [d]);
  }
  if (d === 0) {
    return __("Due today");
  }
  return __("Due in {0} day(s)", [Math.abs(d)]);
});

const markReviewedApi = createResource({
  url: "helpdesk.api.kb_review.mark_article_reviewed",
  onSuccess: () => {
    markingReviewed.value = false;
    emit("reviewed", props.article.name);
  },
  onError: (err: any) => {
    markingReviewed.value = false;
    toast({ title: __("Failed to mark reviewed"), variant: "error" });
  },
});

const archiveApi = createResource({
  url: "helpdesk.api.kb_review.archive_article_from_widget",
  onSuccess: () => {
    archiving.value = false;
    emit("archived", props.article.name);
  },
  onError: (err: any) => {
    archiving.value = false;
    toast({ title: __("Failed to archive article"), variant: "error" });
  },
});

function handleMarkReviewed() {
  markingReviewed.value = true;
  markReviewedApi.submit({ article_name: props.article.name });
}

function handleArchive() {
  if (!confirm(__("Archive this article?"))) return;
  archiving.value = true;
  archiveApi.submit({ article_name: props.article.name });
}
</script>
