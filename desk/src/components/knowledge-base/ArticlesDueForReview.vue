<template>
  <div class="rounded-md border bg-white">
    <!-- Header -->
    <div class="flex items-center justify-between border-b px-4 py-3">
      <h2 class="text-sm font-semibold text-gray-800">
        {{ __("Articles Due for Review") }}
      </h2>
      <button
        class="rounded p-1 text-gray-400 hover:bg-gray-100 hover:text-gray-600"
        :aria-label="__('Refresh articles due for review')"
        @click="reviewData.reload()"
      >
        <LucideRefreshCw class="size-4" :class="{ 'animate-spin': reviewData.loading }" />
      </button>
    </div>

    <!-- Loading skeleton -->
    <div v-if="reviewData.loading" class="space-y-2 p-4">
      <div
        v-for="i in 3"
        :key="i"
        class="h-10 animate-pulse rounded bg-gray-100"
      />
    </div>

    <!-- Error state -->
    <div
      v-else-if="reviewData.error"
      class="flex flex-col items-center gap-2 p-6 text-center text-sm text-gray-500"
    >
      <LucideAlertCircle class="size-5 text-red-400" />
      <span>{{ __("Failed to load articles") }}</span>
      <button
        class="text-blue-600 hover:underline"
        @click="reviewData.reload()"
      >
        {{ __("Retry") }}
      </button>
    </div>

    <!-- Empty state -->
    <div
      v-else-if="!hasArticles"
      class="flex flex-col items-center gap-2 p-6 text-center text-sm text-gray-500"
    >
      <LucideCheckCircle2 class="size-6 text-green-500" />
      <span>{{ __("All articles are up to date") }}</span>
    </div>

    <!-- Article list -->
    <div v-else class="divide-y">
      <!-- Overdue section -->
      <template v-if="overdue.length">
        <div class="px-4 py-2">
          <span class="text-xs font-semibold uppercase tracking-wide text-red-600">
            {{ __("Overdue") }} ({{ overdue.length }})
          </span>
        </div>
        <ArticleReviewRow
          v-for="article in overdue"
          :key="article.name"
          :article="article"
          variant="overdue"
          @reviewed="onReviewed"
          @archived="onArchived"
        />
      </template>

      <!-- Upcoming section -->
      <template v-if="upcoming.length">
        <div class="px-4 py-2" :class="{ 'border-t': overdue.length }">
          <span class="text-xs font-semibold uppercase tracking-wide text-yellow-600">
            {{ __("Due Within 7 Days") }} ({{ upcoming.length }})
          </span>
        </div>
        <ArticleReviewRow
          v-for="article in upcoming"
          :key="article.name"
          :article="article"
          variant="upcoming"
          @reviewed="onReviewed"
          @archived="onArchived"
        />
      </template>
    </div>
  </div>
</template>

<script setup lang="ts">
import { computed, ref } from "vue";
import { createResource, toast } from "frappe-ui";
import { useRouter } from "vue-router";
import { __ } from "@/translation";
import ArticleReviewRow from "./ArticleReviewRow.vue";

const router = useRouter();

const reviewData = createResource({
  url: "helpdesk.api.kb_review.get_articles_due_for_review",
  auto: true,
});

const overdue = computed<any[]>(() => reviewData.data?.overdue ?? []);
const upcoming = computed<any[]>(() => reviewData.data?.upcoming ?? []);
const hasArticles = computed(() => overdue.value.length + upcoming.value.length > 0);

function onReviewed(articleName: string) {
  // Optimistically remove from both lists
  if (reviewData.data) {
    reviewData.data.overdue = reviewData.data.overdue.filter(
      (a: any) => a.name !== articleName
    );
    reviewData.data.upcoming = reviewData.data.upcoming.filter(
      (a: any) => a.name !== articleName
    );
  }
  toast.create({ message: __("Article marked as reviewed"), type: "info" });
}

function onArchived(articleName: string) {
  if (reviewData.data) {
    reviewData.data.overdue = reviewData.data.overdue.filter(
      (a: any) => a.name !== articleName
    );
    reviewData.data.upcoming = reviewData.data.upcoming.filter(
      (a: any) => a.name !== articleName
    );
  }
  toast.create({ message: __("Article archived"), type: "info" });
}
</script>
