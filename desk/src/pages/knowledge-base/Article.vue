<template>
  <div>
    <LayoutHeader>
      <template #left-header>
        <div class="flex gap-1 items-center crumbs truncate">
          <Breadcrumbs :items="breadcrumbs" class="-ml-0.5" />
        </div>
      </template>
      <template #right-header v-if="!isCustomerPortal">
        <!-- Version History button -->
        <Button
          v-if="!editable && !isCustomerPortal"
          :label="__('Version History')"
          iconLeft="history"
          @click="showVersionHistory = !showVersionHistory"
          class="mr-1"
        />
        <!-- Workflow action buttons (non-edit mode) -->
        <div class="flex gap-2" v-if="!editable">
          <!-- Draft: agent can submit for review -->
          <Button
            v-if="article.data?.status === 'Draft'"
            :label="__('Submit for Review')"
            iconLeft="send"
            @click="handleSubmitForReview()"
          />
          <!-- In Review: reviewer can approve, request changes, or reject -->
          <template v-if="article.data?.status === 'In Review' && isAdmin">
            <Button
              :label="__('Approve')"
              iconLeft="check"
              variant="solid"
              theme="green"
              @click="handleApprove()"
            />
            <Button
              :label="__('Request Changes')"
              iconLeft="edit"
              @click="requestChangesVisible = true"
            />
            <Button
              :label="__('Reject')"
              iconLeft="x"
              theme="red"
              @click="handleReject()"
            />
          </template>
          <!-- Published: reviewer can archive -->
          <Button
            v-if="article.data?.status === 'Published' && isAdmin"
            :label="__('Archive')"
            iconLeft="archive"
            @click="handleArchive()"
          />
        </div>
      </template>
    </LayoutHeader>

    <div
      class="py-4 mx-auto w-full max-w-3xl px-5 flex flex-col"
      v-if="!article.loading"
    >
      <!-- article Info -->
      <div
        class="flex flex-col gap-3 p-4 w-full"
        :class="editable && 'border rounded-lg overflow-hidden'"
      >
        <!-- Top Element -->
        <div class="flex flex-col gap-3">
          <div class="flex gap-1 items-center justify-between">
            <div class="flex gap-1 items-center">
              <!-- Avatar -->
              <div class="flex gap-1 items-center justify-center">
                <Avatar
                  :image="article.data.author.image"
                  :label="article.data.author.name"
                />
                <span
                  class="truncate capitalize text-base text-ink-gray-9 font-medium"
                >
                  {{ article.data.author.name }}
                </span>
              </div>
              <IconDot class="h-4 w-4 text-gray-600" />
              <div class="text-xs text-gray-500">
                {{ dayjsLocal(article.data.modified).format("MMM D, h:mm A") }}
              </div>
            </div>
            <Dropdown
              :options="articleActions"
              v-if="!editable && !isCustomerPortal"
            >
              <Button variant="ghost">
                <template #icon>
                  <IconMoreHorizontal class="h-4 w-4" />
                </template>
              </Button>
            </Dropdown>
            <div class="flex gap-2" v-if="editable">
              <DiscardButton
                :hide-dialog="!isDirty"
                :title="__('Discard changes?')"
                :message="__('Are you sure you want to discard changes?')"
                @discard="handleDiscard"
              />

              <Button :label="__('Save')" @click="handleSave" variant="solid" />
            </div>
          </div>
          <!-- Internal badge (agents only) -->
          <div
            v-if="!isCustomerPortal && article.data?.internal_only"
            class="inline-flex items-center gap-1 rounded-full px-2 py-0.5 text-xs font-medium bg-gray-100 text-gray-700 w-fit"
          >
            <IconLock class="h-3 w-3" />
            {{ __("Internal") }}
          </div>
          <!-- Title -->
          <textarea
            ref="titleRef"
            class="w-full resize-none border-0 text-3xl font-bold placeholder-ink-gray-3 p-0 pb-3 border-b border-gray-200 focus:ring-0 focus:border-gray-200 overflow-hidden"
            v-model="title"
            :placeholder="__('Title')"
            rows="1"
            wrap="soft"
            maxlength="140"
            autofocus
            :disabled="!editable"
          />
        </div>
        <!-- Article Content -->
        <TextEditor
          ref="editorRef"
          :editor-class="editorClass"
          :content="textEditorContentWithIDs"
          :extensions="[ComponentUtils]"
          :editable="editable"
          @change="(event:string) => {
			      content = event;
		      }"
          :placeholder="__('Write your article here...')"
        >
          <template #bottom v-if="editable">
            <TextEditorFixedMenu
              class="-ml-1 overflow-x-auto w-full"
              :buttons="textEditorMenuButtons"
            />
          </template>
        </TextEditor>
      </div>
      <!-- Reviewer comment (shown in Draft status when feedback was left) -->
      <div
        v-if="article.data?.reviewer_comment && article.data?.status === 'Draft'"
        class="mx-4 mb-2 p-3 rounded-lg border border-amber-300 bg-amber-50 text-sm text-amber-800"
      >
        <div class="font-medium mb-1">{{ __("Reviewer Feedback") }}</div>
        <div class="whitespace-pre-line">{{ article.data.reviewer_comment }}</div>
      </div>
      <!-- Request Changes inline form -->
      <div
        v-if="requestChangesVisible"
        class="mx-4 mb-2 p-3 rounded-lg border border-gray-200 flex flex-col gap-2"
      >
        <div class="text-sm font-medium text-gray-700">{{ __("Reviewer Comment") }}</div>
        <textarea
          v-model="requestChangesComment"
          class="w-full border border-gray-300 rounded p-2 text-sm focus:outline-none focus:ring-1 focus:ring-gray-400"
          rows="3"
          :placeholder="__('Describe the changes needed...')"
        />
        <div class="flex gap-2 justify-end">
          <Button :label="__('Cancel')" @click="requestChangesVisible = false; requestChangesComment = ''" />
          <Button :label="__('Submit')" variant="solid" @click="handleRequestChanges()" />
        </div>
      </div>
      <!-- Linked Tickets section (agents only) -->
      <LinkedTickets
        v-if="!isCustomerPortal && article.data?.name"
        :article-id="article.data.name"
        class="px-4"
      />
      <div class="p-4" v-if="isCustomerPortal">
        <ArticleFeedback :feedback="feedback" :article-id="articleId" />
      </div>
    </div>
    <MoveToCategoryModal v-model="moveToModal" @move="handleMoveToCategory" />
    <!-- Version History Drawer -->
    <ArticleVersionHistory
      v-if="showVersionHistory && article.data?.name"
      :article-name="article.data.name"
      @close="showVersionHistory = false"
      @reverted="article.reload()"
    />
  </div>
</template>

<script setup lang="ts">
import DiscardButton from "@/components/DiscardButton.vue";
import LayoutHeader from "@/components/LayoutHeader.vue";
import ArticleFeedback from "@/components/knowledge-base/ArticleFeedback.vue";
import ArticleVersionHistory from "@/components/knowledge-base/ArticleVersionHistory.vue";
import LinkedTickets from "@/components/knowledge-base/LinkedTickets.vue";
import MoveToCategoryModal from "@/components/knowledge-base/MoveToCategoryModal.vue";
import { dayjs } from "@/dayjs";
import { useAuthStore } from "@/stores/auth";
import { globalStore } from "@/stores/globalStore";
import {
  deleteRes as deleteArticle,
  incrementView,
  moveToCategory,
  updateRes as updateArticle,
} from "@/stores/knowledgeBase";
import { capture } from "@/telemetry";
import { ComponentUtils } from "@/tiptap-extensions";
import { Article, Breadcrumb, Error, FeedbackAction, Resource } from "@/types";
import {
  copyToClipboard,
  isCustomerPortal,
  textEditorMenuButtons,
} from "@/utils";
import {
  Avatar,
  Breadcrumbs,
  Button,
  createResource,
  Dropdown,
  TextEditor,
  TextEditorFixedMenu,
  toast,
  dayjsLocal,
} from "frappe-ui";
import { computed, h, onMounted, ref, watch } from "vue";
import { useRoute, useRouter } from "vue-router";
import IconDot from "~icons/lucide/dot";
import IconLock from "~icons/lucide/lock";
import IconMoreHorizontal from "~icons/lucide/more-horizontal";
import { __ } from "@/translation";
const props = defineProps({
  articleId: {
    type: String,
    required: true,
  },
});

const { $dialog } = globalStore();

const router = useRouter();
const route = useRoute();
const authStore = useAuthStore();
const { isAdmin } = authStore;

const editorRef = ref(null);
const editable = ref(route.query.isEdit ?? false);

const content = ref("");
const title = ref("");
const feedback = ref<FeedbackAction>();

const titleRef = ref(null);
watch(
  () => titleRef.value,
  (newVal) => {
    if (!newVal) return;

    if (newVal.scrollHeight > newVal.clientHeight) {
      newVal.style.height = newVal.scrollHeight + "px";
    }
  }
);

const article: Resource<Article> = createResource({
  url: "helpdesk.api.knowledge_base.get_article",
  params: {
    name: props.articleId,
  },
  auto: true,
  onSuccess: (data: Article) => {
    content.value = data.content;
    title.value = data.title;
    feedback.value = data.feedback;
    if (isCustomerPortal.value) {
      capture("article_viewed", {
        data: {
          user: authStore.userId,
          article: data.name,
          title: data.title,
        },
      });
      incrementArticleViews(data.name);
    }
  },
  onError: (err: Error) => {
    if (err.exc_type === "PermissionError") {
      router.replace({
        name: "CustomerKnowledgeBase",
      });
    }
  },
});

function incrementArticleViews(articleId: string) {
  incrementView.submit(
    {
      article: articleId,
    },
    {
      onError: (err: Error) => {
        if (err.exc_type === "RateLimitExceededError") {
          return;
        }
      },
    }
  );
}

const isDirty = ref(false);

const moveToModal = ref(false);
const requestChangesVisible = ref(false);
const requestChangesComment = ref("");
const showVersionHistory = ref(false);

const workflowSubmitForReview = createResource({
  url: "helpdesk.api.knowledge_base.submit_for_review",
});
const workflowApprove = createResource({
  url: "helpdesk.api.knowledge_base.approve_article",
});
const workflowRequestChanges = createResource({
  url: "helpdesk.api.knowledge_base.request_changes",
});
const workflowReject = createResource({
  url: "helpdesk.api.knowledge_base.reject_article",
});
const workflowArchive = createResource({
  url: "helpdesk.api.knowledge_base.archive_article",
});

function handleSubmitForReview() {
  workflowSubmitForReview.submit(
    { article: article.data.name },
    {
      onSuccess: () => {
        toast.success(__("Article submitted for review"));
        article.reload();
      },
      onError: (err: Error) => {
        toast.error(err?.messages?.[0] || err.message);
      },
    }
  );
}

function handleApprove() {
  workflowApprove.submit(
    { article: article.data.name },
    {
      onSuccess: () => {
        toast.success(__("Article approved and published"));
        article.reload();
      },
      onError: (err: Error) => {
        toast.error(err?.messages?.[0] || err.message);
      },
    }
  );
}

function handleRequestChanges() {
  if (!requestChangesComment.value.trim()) {
    toast.error(__("Please provide a reviewer comment."));
    return;
  }
  workflowRequestChanges.submit(
    { article: article.data.name, comment: requestChangesComment.value },
    {
      onSuccess: () => {
        toast.success(__("Changes requested"));
        requestChangesVisible.value = false;
        requestChangesComment.value = "";
        article.reload();
      },
      onError: (err: Error) => {
        toast.error(err?.messages?.[0] || err.message);
      },
    }
  );
}

function handleReject() {
  $dialog({
    title: __("Reject Article"),
    message: __("Are you sure you want to reject and archive this article?"),
    actions: [
      {
        label: __("Confirm"),
        variant: "solid",
        theme: "red",
        onClick({ close }) {
          workflowReject.submit(
            { article: article.data.name },
            {
              onSuccess: () => {
                toast.success(__("Article rejected"));
                article.reload();
              },
              onError: (err: Error) => {
                toast.error(err?.messages?.[0] || err.message);
              },
            }
          );
          close();
        },
      },
    ],
  });
}

function handleArchive() {
  $dialog({
    title: __("Archive Article"),
    message: __("Are you sure you want to archive this article?"),
    actions: [
      {
        label: __("Confirm"),
        variant: "solid",
        onClick({ close }) {
          workflowArchive.submit(
            { article: article.data.name },
            {
              onSuccess: () => {
                toast.success(__("Article archived"));
                article.reload();
              },
              onError: (err: Error) => {
                toast.error(err?.messages?.[0] || err.message);
              },
            }
          );
          close();
        },
      },
    ],
  });
}

function handleMoveToCategory(category: string) {
  moveToCategory.submit(
    {
      category,
      articles: [props.articleId],
    },
    {
      onSuccess: () => {
        article.reload();
        moveToModal.value = false;
        toast.success(__("Article moved"));
      },
      onError: (error: Error) => {
        let msg = error?.messages?.[0] || error.message;
        toast.error(msg);
        moveToModal.value = false;
      },
    }
  );
}

function handleEditMode() {
  editable.value = true;
  editorRef.value.editor.chain().focus("start");
}

function handleDiscard() {
  editable.value = false;
  isDirty.value = false;
  title.value = article.data.title;
  content.value = article.data.content;
}

function handleSave() {
  editable.value = false;
  handleArticleUpdate();
}

function handleArticleUpdate() {
  if (!isDirty.value) return;
  updateArticle.submit(
    {
      doctype: "HD Article",
      name: article.data.name,
      fieldname: {
        content: content.value,
        title: title.value,
      },
    },
    {
      onSuccess: () => {
        capture("article_updated", {
          data: {
            category: props.articleId,
          },
        });
        toast.success(__("Article updated"));
        isDirty.value = false;
        article.reload();
      },
    }
  );
}

function handleDelete() {
  $dialog({
    title: __("Delete Article"),
    message: __("Are you sure you want to delete this article?"),
    actions: [
      {
        label: __("Confirm"),
        variant: "solid",
        onClick({ close }) {
          deleteArticle.submit(
            {
              doctype: "HD Article",
              name: article.data.name,
            },
            {
              onSuccess: () => {
                toast.success(__("Article deleted"));
                router.push({
                  name: "AgentKnowledgeBase",
                });
              },
            }
          );
          close();
        },
      },
    ],
  });
}

const textEditorContentWithIDs = computed(() =>
  article.data?.content ? addLinksToHeadings(article.data?.content) : null
);

function addLinksToHeadings(content: string) {
  const parser = new DOMParser();
  const doc = parser.parseFromString(content, "text/html");
  const headings = doc.querySelectorAll("h2, h3, h4, h5, h6");
  headings.forEach((heading) => {
    const text = heading.textContent.trim();
    const id = text.replace(/[^a-z0-9]+/gi, "-").toLowerCase();
    heading.setAttribute("id", id);
  });
  return doc.body.innerHTML;
}
function scrollToHeading() {
  const articleHeading = window.location.hash;
  if (!articleHeading) return;
  const headingElement = document.querySelector(articleHeading) as HTMLElement;
  if (!headingElement) return;
  headingElement.scrollIntoView({ behavior: "smooth" });
  headingElement.classList.add("transition-all");
  const fontSize = headingElement.style.fontSize;
  setTimeout(() => {
    headingElement.style.fontSize = "1.5rem";
    setTimeout(() => {
      headingElement.style.fontSize = fontSize;
    }, 500);
  }, 500);
}

watch([() => content.value, () => title.value], ([newContent, newTitle]) => {
  isDirty.value =
    newContent !== article.data.content || newTitle !== article.data.title;
});

const editorClass = computed(() => {
  return [
    "rounded-b-lg max-w-[unset] prose-sm",
    editable.value &&
      "overflow-auto h-[calc(100vh-340px)] sm:h-[calc(100vh-250px)]",
  ];
});

const articleActions = computed(() => [
  {
    label: __("Edit"),
    icon: "edit",
    onClick: () => {
      handleEditMode();
    },
  },
  {
    label: __("Move To"),
    icon: "corner-up-right",
    onClick: () => (moveToModal.value = true),
  },
  {
    label: __("Share"),
    icon: "link",
    onClick: () => {
      const url = new URL(window.location.href);
      url.pathname = `/helpdesk/kb-public/articles/${props.articleId}`;
      copyToClipboard(url.toString(), __("Article link copied to clipboard"));
    },
  },
  {
    group: __("Danger"),
    hideLabel: true,
    items: [
      {
        label: __("Delete"),
        component: h(Button, {
          label: __("Delete"),
          variant: "ghost",
          iconLeft: "trash-2",
          theme: "red",
          style: "width: 100%; justify-content: flex-start;",
          onClick: handleDelete,
        }),
      },
    ],
  },
]);

const breadcrumbs = computed(() => {
  const items: Breadcrumb[] = [
    {
      label: __("Knowledge Base"),
      route: {
        name: isCustomerPortal.value
          ? "CustomerKnowledgeBase"
          : "AgentKnowledgeBase",
      },
    },
  ];
  if (article.data?.category_name) {
    let item = {
      label: article.data?.category_name,
    };
    if (isCustomerPortal.value) {
      item["route"] = {
        name: "Articles",
        params: {
          categoryId: article.data?.category_id,
        },
      };
    } else {
      item["route"] = {
        name: "AgentKnowledgeBase",
      };
    }
    items.push(item);
  }
  if (article.data?.title) {
    items.push({
      label: article.data?.title,
      route: { name: "Article" },
    });
  }
  return items;
});

onMounted(() => {
  setTimeout(() => {
    scrollToHeading();
  }, 100);
});
</script>
