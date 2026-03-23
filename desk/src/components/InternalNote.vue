<template>
  <div class="flex-col text-base flex-1" ref="internalNoteRef">
    <div class="mb-1 ml-0.5 flex items-center justify-between">
      <div class="text-gray-600 flex items-center gap-2">
        <Avatar
          size="md"
          :label="commenter"
          :image="getUser(commentedBy).user_image"
        />
        <p>
          <span class="font-medium text-gray-800">
            {{ commenter }}
          </span>
          <span> added an</span>
          <span class="max-w-xs truncate font-medium text-amber-700">
            internal note
          </span>
        </p>
      </div>
      <div class="flex items-center gap-1">
        <Tooltip :text="dateFormat(creation, dateTooltipFormat)">
          <span class="pl-0.5 text-sm text-gray-600">
            {{ timeAgo(creation) }}
          </span>
        </Tooltip>
        <div v-if="authStore.userId === commentedBy && !editable">
          <Dropdown
            :placement="'right'"
            :options="[
              {
                label: 'Edit',
                onClick: () => handleEditMode(),
                icon: 'edit-2',
              },
              {
                label: 'Delete',
                onClick: () => (showDialog = true),
                icon: 'trash-2',
              },
            ]"
          >
            <Button
              icon="more-horizontal"
              class="text-gray-600"
              variant="ghost"
            />
          </Dropdown>
        </div>
      </div>
    </div>
    <!-- Visually distinct amber container: amber-50 bg, amber-400 left border -->
    <div
      :id="`comment-${name}`"
      class="rounded bg-amber-50 border-l-4 border-amber-400 transition-colors px-4 py-3"
    >
      <!-- Internal Note badge with lock icon -->
      <div class="flex items-center gap-1.5 mb-2">
        <InternalNoteIcon class="h-3.5 w-3.5 text-amber-600" />
        <span
          class="text-xs font-semibold text-amber-700 bg-amber-100 px-2 py-0.5 rounded-full"
        >
          Internal Note
        </span>
      </div>
      <TextEditor
        ref="editorRef"
        :editor-class="[
          'prose-f shrink text-p-sm transition-all duration-300 ease-in-out block w-full content',
          getFontFamily(_content),
        ]"
        :content="_content"
        :editable="editable"
        :bubble-menu="textEditorMenuButtons"
        :mentions="userMentions"
        @change="(event:string) => {_content = event}"
        @keydown.ctrl.enter.capture.stop="handleSaveNote"
        @keydown.meta.enter.capture.stop="handleSaveNote"
      >
        <template #bottom v-if="editable">
          <div class="flex flex-row-reverse gap-2">
            <div>
              <Button
                :label="
                  isMobileView
                    ? 'Save'
                    : isMac
                    ? 'Save (⌘ + ⏎)'
                    : 'Save (Ctrl + ⏎)'
                "
                @click="handleSaveNote"
                variant="solid"
                class="!bg-amber-500 hover:!bg-amber-600 !text-white"
              />
            </div>
            <Button label="Discard" @click="handleDiscard" />
          </div>
        </template>
      </TextEditor>
      <div
        class="flex flex-wrap gap-2"
        v-if="!editable && Boolean(attachments.length)"
      >
        <AttachmentItem
          v-for="a in attachments"
          :key="a.file_url"
          :label="a.file_name"
          :url="a.file_url"
        />
      </div>
    </div>
  </div>
  <Dialog
    v-model="showDialog"
    :options="{
      title: 'Delete Internal Note',
      message: 'Are you sure you want to delete this internal note?',
      actions: [
        { label: 'Cancel', onClick: () => (showDialog = false) },
        {
          label: 'Delete',
          onClick: () => deleteNote.submit(),
          variant: 'solid',
        },
      ],
    }"
  />
</template>

<script setup lang="ts">
import { AttachmentItem } from "@/components";
import { InternalNoteIcon } from "@/components/icons";
import { useAgentStore } from "@/stores/agent";
import { useAuthStore } from "@/stores/auth";
import { updateRes as updateComment } from "@/stores/knowledgeBase";
import { useUserStore } from "@/stores/user";
import { InternalNoteActivity } from "@/types";
import { useDevice } from "@/composables";
import { useScreenSize } from "@/composables/screen";
import {
  dateFormat,
  dateTooltipFormat,
  getFontFamily,
  isContentEmpty,
  textEditorMenuButtons,
  timeAgo,
} from "@/utils";
import {
  Avatar,
  Dialog,
  Dropdown,
  TextEditor,
  Tooltip,
  createResource,
  toast,
} from "frappe-ui";
import { PropType, computed, onMounted, ref } from "vue";

const authStore = useAuthStore();
const props = defineProps({
  activity: {
    type: Object as PropType<InternalNoteActivity>,
    required: true,
  },
});
const { getUser } = useUserStore();

const { name, creation, content, commenter, commentedBy, attachments } =
  props.activity;

const { isMac } = useDevice();
const { isMobileView } = useScreenSize();

const agentStore = useAgentStore();
const userMentions = computed(() => agentStore.dropdown ?? []);

const emit = defineEmits(["update"]);
const showDialog = ref(false);
const editable = ref(false);
const _content = ref(content);

const internalNoteRef = ref(null);
const editorRef = ref(null);
const lastSavedContent = ref(content);
const noteBoxState = ref(content);

function handleEditMode() {
  editable.value = true;
  noteBoxState.value = _content.value;
  editorRef.value.editor.chain().focus("start");
}

function handleDiscard() {
  _content.value = noteBoxState.value;
  editable.value = false;
}

const deleteNote = createResource({
  url: "frappe.client.delete",
  makeParams: () => ({
    doctype: "HD Ticket Comment",
    name: name,
  }),
  onSuccess() {
    emit("update");
    showDialog.value = false;
    toast.success("Internal note deleted");
  },
});

function handleSaveNote() {
  if (lastSavedContent.value === _content.value) {
    editable.value = false;
    return;
  }
  if (isContentEmpty(_content.value)) {
    toast.error("Internal note cannot be empty");
    return;
  }

  updateComment.submit(
    {
      doctype: "HD Ticket Comment",
      name: name,
      fieldname: "content",
      value: _content.value,
    },
    {
      onSuccess: () => {
        editable.value = false;
        lastSavedContent.value = _content.value;
        emit("update");
        toast.success("Internal note updated");
      },
    }
  );
}

onMounted(() => {
  internalNoteRef.value.style.width = "0px";
});
</script>
