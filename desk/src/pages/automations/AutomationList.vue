<template>
  <div class="flex flex-col h-full overflow-auto">
    <!-- Header -->
    <div class="flex items-center justify-between px-6 py-4 border-b border-outline-gray-2">
      <div class="flex items-center gap-2">
        <LucideZap class="h-5 w-5 text-gray-600" />
        <h1 class="text-lg font-semibold text-ink-gray-9">{{ __("Automation Rules") }}</h1>
        <Badge
          v-if="!rules.loading && rules.data?.length"
          :label="String(rules.data.length)"
          theme="gray"
          variant="subtle"
        />
      </div>
      <Button
        variant="solid"
        :label="__('New Rule')"
        @click="router.push({ name: 'AutomationBuilder', params: { id: 'new' } })"
      >
        <template #prefix>
          <LucidePlus class="h-3.5 w-3.5" />
        </template>
      </Button>
    </div>

    <!-- Access denied -->
    <div
      v-if="!authStore.isAdmin"
      class="flex flex-col items-center justify-center flex-1 gap-3 text-ink-gray-4"
    >
      <LucideLock class="h-10 w-10 text-gray-400" />
      <p class="text-base font-medium text-gray-600">{{ __("Access Restricted") }}</p>
      <p class="text-sm text-gray-400">{{ __("Only administrators can manage automation rules.") }}</p>
    </div>

    <!-- Loading -->
    <div
      v-else-if="rules.loading"
      class="flex items-center justify-center flex-1"
    >
      <LoadingIndicator :scale="6" />
    </div>

    <!-- Empty state -->
    <div
      v-else-if="!rules.data?.length"
      class="flex flex-col items-center justify-center flex-1 gap-3 text-ink-gray-4"
    >
      <LucideZap class="h-10 w-10 text-gray-300" />
      <p class="text-base font-medium text-gray-500">{{ __("No automation rules yet") }}</p>
      <p class="text-sm text-gray-400">{{ __("Create rules to automate repetitive ticket operations.") }}</p>
      <Button
        variant="subtle"
        :label="__('Create your first rule')"
        @click="router.push({ name: 'AutomationBuilder', params: { id: 'new' } })"
      />
    </div>

    <!-- Rules table -->
    <div v-else class="overflow-auto flex-1">
      <table class="w-full text-sm">
        <thead class="border-b border-gray-200 bg-gray-50">
          <tr>
            <th class="px-6 py-3 text-left text-xs font-semibold text-gray-500 uppercase tracking-wider">{{ __("Rule Name") }}</th>
            <th class="px-4 py-3 text-left text-xs font-semibold text-gray-500 uppercase tracking-wider">{{ __("Trigger") }}</th>
            <th class="px-4 py-3 text-left text-xs font-semibold text-gray-500 uppercase tracking-wider">{{ __("Priority") }}</th>
            <th class="px-4 py-3 text-right text-xs font-semibold text-gray-500 uppercase tracking-wider">{{ __("Executions") }}</th>
            <th class="px-4 py-3 text-left text-xs font-semibold text-gray-500 uppercase tracking-wider">{{ __("Last Fired") }}</th>
            <th class="px-4 py-3 text-right text-xs font-semibold text-gray-500 uppercase tracking-wider">{{ __("Failure Rate") }}</th>
            <th class="px-4 py-3 text-center text-xs font-semibold text-gray-500 uppercase tracking-wider">{{ __("Enabled") }}</th>
            <th class="px-4 py-3 text-right text-xs font-semibold text-gray-500 uppercase tracking-wider">{{ __("Actions") }}</th>
          </tr>
        </thead>
        <tbody class="divide-y divide-gray-100">
          <tr
            v-for="rule in rulesWithStats"
            :key="rule.name"
            class="hover:bg-gray-50 cursor-pointer"
            @click="router.push({ name: 'AutomationBuilder', params: { id: rule.name } })"
          >
            <td class="px-6 py-3 font-medium text-gray-900">{{ rule.rule_name || rule.name }}</td>
            <td class="px-4 py-3">
              <Badge
                :label="formatTrigger(rule.trigger_type)"
                :theme="getTriggerTheme(rule.trigger_type)"
                variant="subtle"
              />
            </td>
            <td class="px-4 py-3 text-gray-500">{{ rule.priority_order }}</td>
            <td class="px-4 py-3 text-right text-gray-600 tabular-nums">
              <span v-if="stats.loading" class="text-gray-300">—</span>
              <span v-else>{{ rule.execution_count ?? 0 }}</span>
            </td>
            <td class="px-4 py-3 text-gray-500 text-xs">
              <span v-if="stats.loading" class="text-gray-300">—</span>
              <span v-else-if="rule.last_fired">{{ formatRelativeTime(rule.last_fired) }}</span>
              <span v-else class="text-gray-300">{{ __("Never") }}</span>
            </td>
            <td class="px-4 py-3 text-right">
              <span v-if="stats.loading" class="text-gray-300">—</span>
              <Badge
                v-else
                :label="(rule.failure_rate ?? 0) + '%'"
                :theme="getFailureRateTheme(rule.failure_rate ?? 0)"
                variant="subtle"
              />
            </td>
            <td class="px-4 py-3 text-center" @click.stop>
              <input
                type="checkbox"
                :checked="!!rule.enabled"
                class="h-4 w-4 rounded border-gray-300 text-blue-600 cursor-pointer"
                @change="toggleEnabled(rule)"
              />
            </td>
            <td class="px-4 py-3 text-right" @click.stop>
              <div class="flex items-center justify-end gap-1">
                <Button
                  variant="ghost"
                  size="sm"
                  :title="__('Edit')"
                  @click="router.push({ name: 'AutomationBuilder', params: { id: rule.name } })"
                >
                  <template #icon>
                    <LucidePencil class="h-3.5 w-3.5" />
                  </template>
                </Button>
                <Button
                  variant="ghost"
                  size="sm"
                  :title="__('Delete')"
                  @click="deleteRule(rule)"
                >
                  <template #icon>
                    <LucideTrash2 class="h-3.5 w-3.5 text-red-400" />
                  </template>
                </Button>
              </div>
            </td>
          </tr>
        </tbody>
      </table>
    </div>
  </div>

  <!-- Delete confirmation dialog -->
  <Dialog
    v-model="deleteConfirm.show"
    :options="{
      title: __('Delete Rule'),
      message: deleteConfirm.rule ? __('Are you sure you want to delete \'{0}\'? This action cannot be undone.').replace('{0}', deleteConfirm.rule.rule_name || deleteConfirm.rule.name) : '',
      actions: [
        { label: __('Delete'), variant: 'solid', theme: 'red', onClick: confirmDelete },
        { label: __('Cancel'), onClick: () => (deleteConfirm.show = false) },
      ],
    }"
  />
</template>

<script setup lang="ts">
import { ref, computed } from "vue"
import { Badge, Button, Dialog, LoadingIndicator, createListResource, createResource, usePageMeta, call } from "frappe-ui"
import { useRouter } from "vue-router"
import { useAuthStore } from "@/stores/auth"
import { __ } from "@/translation"
import LucideZap from "~icons/lucide/zap"
import LucidePlus from "~icons/lucide/plus"
import LucideLock from "~icons/lucide/lock"
import LucidePencil from "~icons/lucide/pencil"
import LucideTrash2 from "~icons/lucide/trash-2"

usePageMeta(() => ({ title: "Automation Rules" }))

const router = useRouter()
const authStore = useAuthStore()

const deleteConfirm = ref<{ show: boolean; rule: any }>({ show: false, rule: null })

const rules = createListResource({
  doctype: "HD Automation Rule",
  fields: ["name", "rule_name", "trigger_type", "enabled", "priority_order", "failure_count"],
  orderBy: "priority_order asc",
  auto: true,
})

// Batch-fetch execution stats for all rules from HD Automation Log
const stats = createResource({
  url: "helpdesk.api.automation.get_execution_stats",
  auto: true,
})

// Merge stats into rules list for display
const rulesWithStats = computed(() => {
  if (!rules.data) return []
  const statsList: any[] = stats.data || []
  const statsMap = Object.fromEntries(statsList.map((s: any) => [s.name, s]))
  return rules.data.map((rule: any) => {
    const stat = statsMap[rule.name] || {}
    return {
      ...rule,
      execution_count: stat.execution_count ?? 0,
      last_fired: stat.last_fired ?? null,
      failure_rate: stat.failure_rate ?? 0.0,
    }
  })
})

function formatTrigger(trigger: string): string {
  const labels: Record<string, string> = {
    ticket_created: "Ticket Created",
    ticket_updated: "Ticket Updated",
    ticket_assigned: "Ticket Assigned",
    ticket_resolved: "Ticket Resolved",
    ticket_reopened: "Ticket Reopened",
    sla_warning: "SLA Warning",
    sla_breached: "SLA Breached",
    csat_received: "CSAT Received",
    chat_started: "Chat Started",
    chat_ended: "Chat Ended",
  }
  return labels[trigger] || trigger
}

function getTriggerTheme(trigger: string): string {
  if (trigger.startsWith("sla")) return "red"
  if (trigger.startsWith("chat")) return "blue"
  if (trigger === "csat_received") return "yellow"
  return "gray"
}

function getFailureRateTheme(rate: number): string {
  if (rate === 0) return "green"
  if (rate <= 25) return "yellow"
  return "red"
}

function formatRelativeTime(timestamp: string): string {
  if (!timestamp) return ""
  const date = new Date(timestamp)
  const now = new Date()
  const diffMs = now.getTime() - date.getTime()
  const diffMins = Math.floor(diffMs / 60000)
  if (diffMins < 1) return __("just now")
  if (diffMins < 60) return __("{0}m ago").replace("{0}", String(diffMins))
  const diffHours = Math.floor(diffMins / 60)
  if (diffHours < 24) return __("{0}h ago").replace("{0}", String(diffHours))
  const diffDays = Math.floor(diffHours / 24)
  return __("{0}d ago").replace("{0}", String(diffDays))
}

async function toggleEnabled(rule: any) {
  const newEnabled = rule.enabled ? 0 : 1
  await call("helpdesk.api.automation.toggle_rule", {
    rule_name: rule.name,
    enabled: newEnabled,
  })
  await rules.reload()
  await stats.reload()
}

function deleteRule(rule: any) {
  deleteConfirm.value = { show: true, rule }
}

async function confirmDelete() {
  const rule = deleteConfirm.value.rule
  deleteConfirm.value = { show: false, rule: null }
  if (!rule) return
  await call("frappe.client.delete", { doctype: "HD Automation Rule", name: rule.name })
  await rules.reload()
  await stats.reload()
}
</script>
