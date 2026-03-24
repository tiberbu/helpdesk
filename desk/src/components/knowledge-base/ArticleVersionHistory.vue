<template>
  <!-- Version History Drawer -->
  <div
    class="fixed inset-y-0 right-0 z-50 flex"
    role="dialog"
    aria-label="Version History"
    aria-modal="true"
  >
    <!-- Backdrop -->
    <div
      class="fixed inset-0 bg-black/20"
      @click="emit('close')"
    />

    <!-- Drawer panel -->
    <div
      class="relative ml-auto flex h-full w-96 flex-col bg-white shadow-xl"
      @keydown.escape="emit('close')"
      tabindex="-1"
      ref="drawerRef"
    >
      <!-- Header -->
      <div class="flex items-center justify-between border-b px-4 py-3">
        <h2 class="text-base font-semibold text-gray-800">
          {{ __("Version History") }}
        </h2>
        <button
          class="rounded p-1 text-gray-500 hover:bg-gray-100"
          :aria-label="__('Close version history')"
          @click="emit('close')"
        >
          <svg xmlns="http://www.w3.org/2000/svg" class="h-4 w-4" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2"><line x1="18" y1="6" x2="6" y2="18"/><line x1="6" y1="6" x2="18" y2="18"/></svg>
        </button>
      </div>

      <!-- Compare toolbar (shown when 2 are selected) -->
      <div
        v-if="selectedVersions.length === 2"
        class="flex items-center justify-between bg-blue-50 px-4 py-2 text-sm"
      >
        <span class="text-blue-700">
          {{ __("{0} versions selected", [selectedVersions.length]) }}
        </span>
        <Button
          :label="__('Compare')"
          size="sm"
          variant="solid"
          @click="openDiff"
        />
      </div>

      <!-- Loading -->
      <div v-if="versions.loading" class="flex flex-1 items-center justify-center">
        <div class="h-5 w-5 animate-spin rounded-full border-2 border-gray-300 border-t-blue-500" />
      </div>

      <!-- Empty state -->
      <div
        v-else-if="!versions.loading && (!versions.data || versions.data.length === 0)"
        class="flex flex-1 flex-col items-center justify-center gap-2 px-6 text-center text-sm text-gray-500"
      >
        <svg xmlns="http://www.w3.org/2000/svg" class="h-10 w-10 text-gray-300" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="1.5"><path d="M12 8v4l3 3"/><circle cx="12" cy="12" r="10"/></svg>
        <p class="font-medium text-gray-700">{{ __("No version history yet") }}</p>
        <p>{{ __("Versions are created each time the article content is updated.") }}</p>
      </div>

      <!-- Version list -->
      <div v-else class="flex-1 overflow-y-auto divide-y">
        <div
          v-for="v in versions.data"
          :key="v.name"
          class="flex cursor-pointer items-start gap-3 px-4 py-3 hover:bg-gray-50"
          :class="{ 'bg-blue-50': previewVersion?.name === v.name }"
          @click="openPreview(v)"
        >
          <!-- Checkbox for comparison (max 2) -->
          <input
            type="checkbox"
            class="mt-1 h-4 w-4 cursor-pointer rounded border-gray-300 text-blue-600"
            :checked="selectedVersions.includes(v.name)"
            @click.stop
            @change="toggleSelect(v.name)"
            :disabled="selectedVersions.length >= 2 && !selectedVersions.includes(v.name)"
            :aria-label="__('Select version {0} for comparison', [v.version_number])"
          />
          <!-- Version info -->
          <div class="flex-1 min-w-0">
            <div class="flex items-center gap-2">
              <span class="inline-flex items-center rounded bg-gray-100 px-1.5 py-0.5 text-xs font-medium text-gray-700">
                v{{ v.version_number }}
              </span>
              <span class="truncate text-sm font-medium text-gray-800">
                {{ v.author_full_name || v.author }}
              </span>
            </div>
            <div class="mt-0.5 text-xs text-gray-500">
              {{ relativeTime(v.timestamp) }}
            </div>
            <div
              v-if="v.change_summary"
              class="mt-0.5 truncate text-xs text-gray-500"
              :title="v.change_summary"
            >
              {{ truncate(v.change_summary, 80) }}
            </div>
          </div>
        </div>
      </div>
    </div>
  </div>

  <!-- Version Preview Panel (replaces main content area when open) -->
  <Teleport to="body">
    <div
      v-if="previewVersion"
      class="fixed inset-y-0 right-96 z-40 w-[calc(100%-24rem)] bg-white shadow-lg flex flex-col"
      role="region"
      :aria-label="__('Version preview')"
    >
      <!-- Preview header -->
      <div class="flex items-center justify-between border-b px-6 py-3 bg-gray-50">
        <div class="flex items-center gap-3">
          <span class="inline-flex items-center rounded bg-gray-200 px-2 py-0.5 text-sm font-medium text-gray-700">
            v{{ previewVersion.version_number }}
          </span>
          <span class="text-sm text-gray-700">
            {{ __("by {0}", [previewVersion.author_full_name || previewVersion.author]) }}
          </span>
          <span class="text-xs text-gray-400">·</span>
          <span class="text-xs text-gray-500">{{ relativeTime(previewVersion.timestamp) }}</span>
          <span v-if="previewVersion.change_summary" class="text-xs text-gray-400">·</span>
          <span v-if="previewVersion.change_summary" class="text-xs italic text-gray-500">
            {{ previewVersion.change_summary }}
          </span>
        </div>
        <div class="flex items-center gap-2">
          <Button
            :label="__('Revert to This Version')"
            size="sm"
            @click="confirmRevert"
          />
          <button
            class="rounded p-1 text-gray-500 hover:bg-gray-100"
            :aria-label="__('Close preview')"
            @click="previewVersion = null"
          >
            <svg xmlns="http://www.w3.org/2000/svg" class="h-4 w-4" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2"><line x1="18" y1="6" x2="6" y2="18"/><line x1="6" y1="6" x2="18" y2="18"/></svg>
          </button>
        </div>
      </div>
      <!-- Preview content -->
      <div
        class="flex-1 overflow-y-auto px-6 py-4 prose prose-sm max-w-none"
        v-html="previewVersion.content"
      />
    </div>
  </Teleport>

  <!-- Diff Modal -->
  <Teleport to="body">
    <div
      v-if="showDiff && diffVersions.length === 2"
      class="fixed inset-0 z-50 flex flex-col bg-white"
      role="dialog"
      :aria-label="__('Version diff')"
    >
      <!-- Diff header -->
      <div class="flex items-center justify-between border-b px-6 py-3 bg-gray-50">
        <h2 class="text-sm font-semibold text-gray-800">
          {{
            __("Compare v{0} ({1}) vs v{2} ({3})", [
              diffVersions[0].version_number,
              formatTs(diffVersions[0].timestamp),
              diffVersions[1].version_number,
              formatTs(diffVersions[1].timestamp),
            ])
          }}
        </h2>
        <button
          class="rounded p-1 text-gray-500 hover:bg-gray-100"
          :aria-label="__('Close diff view')"
          @click="closeDiff"
        >
          <svg xmlns="http://www.w3.org/2000/svg" class="h-5 w-5" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2"><line x1="18" y1="6" x2="6" y2="18"/><line x1="6" y1="6" x2="18" y2="18"/></svg>
        </button>
      </div>
      <!-- Diff columns -->
      <div class="flex flex-1 overflow-hidden">
        <!-- Left: older version (removed lines) -->
        <div class="flex-1 overflow-y-auto border-r px-4 py-2">
          <div class="mb-2 text-xs font-medium text-gray-500 uppercase tracking-wide">
            v{{ diffVersions[0].version_number }} — {{ diffVersions[0].author_full_name || diffVersions[0].author }}
          </div>
          <div class="font-mono text-sm whitespace-pre-wrap">
            <div
              v-for="(line, idx) in diffLines"
              :key="'left-' + idx"
              :class="{
                'bg-red-100 text-red-800': line.type === 'removed',
                'bg-gray-50 text-gray-300': line.type === 'added',
                'text-gray-700': line.type === 'unchanged',
              }"
              class="px-1 leading-6"
            >
              <span v-if="line.type !== 'added'">{{ line.content || ' ' }}</span>
              <span v-else class="select-none opacity-0">{{ line.content || ' ' }}</span>
            </div>
          </div>
        </div>
        <!-- Right: newer version (added lines) -->
        <div class="flex-1 overflow-y-auto px-4 py-2">
          <div class="mb-2 text-xs font-medium text-gray-500 uppercase tracking-wide">
            v{{ diffVersions[1].version_number }} — {{ diffVersions[1].author_full_name || diffVersions[1].author }}
          </div>
          <div class="font-mono text-sm whitespace-pre-wrap">
            <div
              v-for="(line, idx) in diffLines"
              :key="'right-' + idx"
              :class="{
                'bg-green-100 text-green-800': line.type === 'added',
                'bg-gray-50 text-gray-300': line.type === 'removed',
                'text-gray-700': line.type === 'unchanged',
              }"
              class="px-1 leading-6"
            >
              <span v-if="line.type !== 'removed'">{{ line.content || ' ' }}</span>
              <span v-else class="select-none opacity-0">{{ line.content || ' ' }}</span>
            </div>
          </div>
        </div>
      </div>
    </div>
  </Teleport>
</template>

<script setup lang="ts">
import { Button, createResource, toast } from "frappe-ui";
import { computed, onMounted, ref } from "vue";
import { __ } from "@/translation";
import { globalStore } from "@/stores/globalStore";
import { computeDiff } from "./articleVersionDiff";
import { dayjs } from "@/dayjs";

const props = defineProps({
  articleName: {
    type: String,
    required: true,
  },
});

const emit = defineEmits<{
  (e: "close"): void;
  (e: "reverted"): void;
}>();

const { $dialog } = globalStore();
const drawerRef = ref<HTMLElement | null>(null);

// Focus the drawer on mount for accessibility
onMounted(() => {
  drawerRef.value?.focus();
});

// ── Versions list ────────────────────────────────────────────────
const versions = createResource({
  url: "helpdesk.api.knowledge_base.get_article_versions",
  params: { article: props.articleName },
  auto: true,
});

// ── Selection for comparison (max 2) ────────────────────────────
const selectedVersions = ref<string[]>([]);

function toggleSelect(versionName: string) {
  const idx = selectedVersions.value.indexOf(versionName);
  if (idx === -1) {
    if (selectedVersions.value.length < 2) {
      selectedVersions.value = [...selectedVersions.value, versionName];
    }
  } else {
    selectedVersions.value = selectedVersions.value.filter((n) => n !== versionName);
  }
}

// ── Preview ──────────────────────────────────────────────────────
const previewVersion = ref<Record<string, any> | null>(null);

function openPreview(v: Record<string, any>) {
  previewVersion.value = v;
  showDiff.value = false;
}

// ── Diff view ────────────────────────────────────────────────────
const showDiff = ref(false);

const diffVersions = computed<Record<string, any>[]>(() => {
  if (selectedVersions.value.length !== 2 || !versions.data) return [];
  const all: Record<string, any>[] = versions.data;
  // Sort so lower version_number is "left" (older)
  const selected = all.filter((v) => selectedVersions.value.includes(v.name));
  return selected.sort((a, b) => a.version_number - b.version_number);
});

const diffLines = computed(() => {
  if (diffVersions.value.length !== 2) return [];
  return computeDiff(
    diffVersions.value[0].content || "",
    diffVersions.value[1].content || ""
  );
});

function openDiff() {
  if (selectedVersions.value.length === 2) {
    showDiff.value = true;
    previewVersion.value = null;
  }
}

function closeDiff() {
  showDiff.value = false;
}

// ── Revert ───────────────────────────────────────────────────────
const revertResource = createResource({
  url: "helpdesk.api.knowledge_base.revert_article_to_version",
});

function confirmRevert() {
  if (!previewVersion.value) return;
  const v = previewVersion.value;
  $dialog({
    title: __("Revert Article?"),
    message: __(
      "This will restore the article content from version #{0} ({1}) and create a new version record. The article status will not change.",
      [v.version_number, formatTs(v.timestamp)]
    ),
    actions: [
      {
        label: __("Revert"),
        variant: "solid",
        onClick({ close }: { close: () => void }) {
          revertResource.submit(
            {
              article: props.articleName,
              version_name: v.name,
            },
            {
              onSuccess: () => {
                toast.success(
                  __("Article reverted to version #{0}", [v.version_number])
                );
                previewVersion.value = null;
                versions.reload();
                emit("reverted");
              },
              onError: (err: any) => {
                toast.error(err?.messages?.[0] || err.message || __("Revert failed"));
              },
            }
          );
          close();
        },
      },
    ],
  });
}

// ── Helpers ──────────────────────────────────────────────────────
function relativeTime(ts: string) {
  return dayjs(ts).fromNow();
}

function formatTs(ts: string) {
  return dayjs(ts).format("MMM D, YYYY h:mm A");
}

function truncate(str: string, len: number) {
  return str.length > len ? str.slice(0, len) + "…" : str;
}
</script>
