<template>
  <!-- Amber-50 background wrapper to visually distinguish the note editor -->
  <div
    v-if="agentsList.data"
    class="bg-amber-50 border-l-4 border-amber-400 mx-6 md:ml-10 md:mr-9 rounded-r"
  >
    <!-- Internal Note header badge -->
    <div class="flex items-center gap-1.5 px-3 pt-2.5">
      <InternalNoteIcon class="h-3.5 w-3.5 text-amber-600" />
      <span
        class="text-xs font-semibold text-amber-700 bg-amber-100 px-2 py-0.5 rounded-full"
      >
        Internal Note
      </span>
      <span class="text-xs text-amber-600 ml-1">
        — visible to agents only
      </span>
    </div>
    <TextEditor
      ref="editorRef"
      :editor-class="[
        'prose-sm max-w-none',
        editable && 'min-h-[7rem] max-h-[50vh] overflow-y-auto py-3 px-3',
        getFontFamily(noteContent),
      ]"
      :content="noteContent"
      :starterkit-options="{ heading: { levels: [2, 3, 4, 5, 6] } }"
      :placeholder="placeholder"
      :editable="editable"
      :mentions="dropdown"
      @change="editable ? (noteContent = $event) : null"
      :extensions="[ComponentUtils, HandleExcelPaste]"
      :uploadFunction="(file:any)=>uploadFunction(file, doctype, ticketId)"
    >
      <template #bottom>
        <div v-if="editable" class="flex flex-col gap-2 px-3 pb-2.5">
          <!-- Attachments -->
          <div class="flex flex-wrap gap-2">
            <AttachmentItem
              v-for="a in attachments"
              :key="a.file_url"
              :label="a.file_name"
              :url="!['MOV', 'MP4'].includes(a.file_type) ? a.file_url : null"
            >
              <template #suffix>
                <FeatherIcon
                  class="h-3.5"
                  name="x"
                  @click.stop="removeAttachment(a)"
                />
              </template>
            </AttachmentItem>
          </div>
          <!-- Fixed Menu -->
          <div class="flex justify-between overflow-hidden border-t border-amber-200 py-2.5">
            <div class="flex items-center overflow-x-auto w-[60%]">
              <FileUploader
                :upload-args="{
                  doctype: doctype,
                  docname: ticketId,
                  private: true,
                }"
                @success="(f) => attachments.push(f)"
              >
                <template #default="{ openFileSelector, uploading }">
                  {{ void (loading = uploading) }}
                  <Button
                    theme="gray"
                    variant="ghost"
                    @click="openFileSelector()"
                  >
                    <template #icon>
                      <AttachmentIcon
                        class="h-4"
                        style="color: #000000; stroke-width: 1.5 !important"
                      />
                    </template>
                  </Button>
                </template>
              </FileUploader>
              <TextEditorFixedMenu
                class="-ml-0.5"
                :buttons="textEditorMenuButtons"
              />
            </div>
            <div class="flex items-center justify-end space-x-2 w-[40%]">
              <Button
                label="Discard"
                @click="
                  () => {
                    noteContent = '';
                    attachments = [];
                    emit('discard');
                  }
                "
              />
              <Button
                variant="solid"
                :label="label"
                :disabled="isDisabled"
                :loading="loading"
                class="!bg-amber-500 hover:!bg-amber-600 !text-white"
                @click="
                  () => {
                    loading = true;
                    submitNote();
                    noteContent = '';
                  }
                "
              />
            </div>
          </div>
        </div>
      </template>
    </TextEditor>
  </div>
</template>
<script setup lang="ts">
import {
  FileUploader,
  TextEditor,
  TextEditorFixedMenu,
  createResource,
  FeatherIcon,
} from "frappe-ui";
import { computed, onBeforeUnmount, onMounted, ref, watch } from "vue";

import { AttachmentItem } from "@/components/";
import { AttachmentIcon, InternalNoteIcon } from "@/components/icons/";
import { useTyping } from "@/composables/realtime";
import { useAgentStore } from "@/stores/agent";
import { ComponentUtils, HandleExcelPaste } from "@/tiptap-extensions";
import {
  getFontFamily,
  isContentEmpty,
  removeAttachmentFromServer,
  textEditorMenuButtons,
  uploadFunction,
} from "@/utils";
import { useStorage } from "@vueuse/core";
import { storeToRefs } from "pinia";

const { agents: agentsList, dropdown } = storeToRefs(useAgentStore());

const props = defineProps({
  ticketId: {
    type: String,
    default: null,
  },
  placeholder: {
    type: String,
    default: "Add a private internal note visible only to agents...",
  },
  label: {
    type: String,
    default: "Add Note",
  },
  editable: {
    type: Boolean,
    default: true,
  },
  doctype: {
    type: String,
    default: "HD Ticket",
  },
});

const emit = defineEmits(["submit", "discard"]);

const noteContent = useStorage("internalNoteBoxContent" + props.ticketId, null);

// Initialize typing composable
const { onUserType, cleanup } = useTyping(props.ticketId);

const attachments = ref([]);
const isDisabled = computed(() => {
  return isContentEmpty(noteContent.value) || loading.value;
});
const loading = ref(false);

// Watch for changes in note content to trigger typing events
watch(noteContent, (newValue, oldValue) => {
  if (newValue !== oldValue && newValue) {
    onUserType();
  }
});

onBeforeUnmount(() => {
  cleanup();
});

const label = computed(() => {
  return loading.value ? "Saving..." : props.label;
});

function removeAttachment(attachment) {
  attachments.value = attachments.value.filter((a) => a !== attachment);
  removeAttachmentFromServer(attachment.name);
}

async function submitNote() {
  if (isContentEmpty(noteContent.value)) {
    return false;
  }
  const note = createResource({
    url: "run_doc_method",
    makeParams: () => ({
      dt: props.doctype,
      dn: props.ticketId,
      method: "new_internal_note",
      args: {
        content: noteContent.value,
        attachments: attachments.value,
      },
    }),
    onSuccess: () => {
      emit("submit");
      loading.value = false;
      attachments.value = [];
      noteContent.value = null;
    },
    onError: () => {
      loading.value = false;
    },
  });

  note.submit();
}

const editorRef = ref(null);
const editor = computed(() => editorRef.value?.editor);

onMounted(() => {
  if (
    agentsList.value.loading ||
    agentsList.value.data?.length ||
    agentsList.value.list.promise
  ) {
    return;
  }
  agentsList.value.fetch();
});

defineExpose({
  submitNote,
  editor,
});
</script>
