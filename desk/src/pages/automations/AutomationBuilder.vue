<template>
  <div class="flex flex-col min-h-0 h-full max-h-[calc(100vh-3rem)] overflow-hidden">
    <!-- Header / breadcrumb -->
    <div class="flex items-center justify-between px-6 py-3 border-b border-outline-gray-2 shrink-0">
      <div class="flex items-center gap-2 text-sm">
        <button
          class="text-gray-500 hover:text-gray-800 font-medium"
          @click="navigateBack"
        >
          {{ __("Automation Rules") }}
        </button>
        <span class="text-gray-300">/</span>
        <span class="text-gray-700 font-medium">
          {{ isNew ? __("New Rule") : (formState.rule_name || id) }}
        </span>
      </div>
      <div class="flex items-center gap-2">
        <Button
          variant="ghost"
          size="sm"
          :label="__('Cancel')"
          @click="navigateBack"
        />
        <Button
          v-if="!isNew"
          variant="subtle"
          size="sm"
          :label="__('Test Rule')"
          :loading="testLoading"
          @click="openTestModal"
        >
          <template #prefix>
            <LucideFlaskConical class="h-3.5 w-3.5" />
          </template>
        </Button>
        <Button
          variant="solid"
          size="sm"
          :label="__('Save')"
          :loading="saving"
          @click="saveRule"
        >
          <template #prefix>
            <LucideSave class="h-3.5 w-3.5" />
          </template>
        </Button>
      </div>
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
      v-else-if="loading"
      class="flex items-center justify-center flex-1"
    >
      <LoadingIndicator :scale="6" />
    </div>

    <!-- Builder layout -->
    <div v-else class="flex flex-1 overflow-hidden">
      <!-- Left sidebar: metadata -->
      <div class="w-72 shrink-0 border-r border-gray-200 flex flex-col gap-5 p-5 overflow-y-auto bg-gray-50">
        <div class="flex flex-col gap-1.5">
          <label class="text-xs font-semibold text-gray-500 uppercase tracking-wider">{{ __("Rule Name") }}</label>
          <FormControl
            type="text"
            v-model="formState.rule_name"
            :placeholder="__('e.g. Escalate Urgent Tickets')"
            required
          />
        </div>

        <div class="flex flex-col gap-1.5">
          <label class="text-xs font-semibold text-gray-500 uppercase tracking-wider">{{ __("Description") }}</label>
          <FormControl
            type="textarea"
            v-model="formState.description"
            :placeholder="__('What does this rule do?')"
            :rows="3"
          />
        </div>

        <div class="flex flex-col gap-1.5">
          <label class="text-xs font-semibold text-gray-500 uppercase tracking-wider">{{ __("Priority Order") }}</label>
          <FormControl
            type="number"
            v-model="formState.priority_order"
            :placeholder="__('10')"
          />
          <p class="text-xs text-gray-400">{{ __("Lower number = higher priority. Rules with same trigger fire in this order.") }}</p>
        </div>

        <div class="flex items-center justify-between">
          <label class="text-xs font-semibold text-gray-500 uppercase tracking-wider">{{ __("Enabled") }}</label>
          <input
            type="checkbox"
            :checked="formState.enabled"
            @change="formState.enabled = !formState.enabled"
            class="h-4 w-4 rounded border-gray-300 text-blue-600 cursor-pointer"
          />
        </div>

        <!-- Failure warning -->
        <div
          v-if="formState.failure_count && formState.failure_count >= 5"
          class="rounded-md bg-yellow-50 border border-yellow-200 p-3 text-xs text-yellow-700"
        >
          <p class="font-semibold">{{ __("High failure count") }}</p>
          <p>{{ __("{0} consecutive failures. Rule may be auto-disabled at 10.").replace("{0}", String(formState.failure_count)) }}</p>
        </div>
      </div>

      <!-- Main: WHEN / IF / THEN -->
      <div class="flex-1 overflow-y-auto p-6 flex flex-col gap-6">

        <!-- WHEN -->
        <div class="rounded-xl border border-gray-200 bg-white overflow-hidden">
          <div class="flex items-center gap-2 px-5 py-3 border-b border-gray-100 bg-blue-50">
            <Badge label="WHEN" theme="blue" variant="solid" size="sm" />
            <span class="text-sm font-semibold text-blue-800">{{ __("Trigger") }}</span>
            <span class="text-xs text-blue-500 ml-1">{{ __("— select when this rule fires") }}</span>
          </div>
          <div class="p-5">
            <RuleTriggerSelect v-model="formState.trigger_type" />
            <p v-if="showErrors && !formState.trigger_type" class="mt-2 text-xs text-red-500">
              {{ __("Please select a trigger.") }}
            </p>
          </div>
        </div>

        <!-- IF -->
        <div class="rounded-xl border border-gray-200 bg-white overflow-hidden">
          <div class="flex items-center gap-2 px-5 py-3 border-b border-gray-100 bg-orange-50">
            <Badge label="IF" theme="orange" variant="solid" size="sm" />
            <span class="text-sm font-semibold text-orange-800">{{ __("Conditions") }}</span>
            <span class="text-xs text-orange-500 ml-1">{{ __("— optional: only fire when these match") }}</span>
          </div>
          <div class="p-5">
            <RuleConditionBuilder v-model="conditionsState" />
          </div>
        </div>

        <!-- THEN -->
        <div class="rounded-xl border border-gray-200 bg-white overflow-hidden">
          <div class="flex items-center gap-2 px-5 py-3 border-b border-gray-100 bg-green-50">
            <Badge label="THEN" theme="green" variant="solid" size="sm" />
            <span class="text-sm font-semibold text-green-800">{{ __("Actions") }}</span>
            <span class="text-xs text-green-500 ml-1">{{ __("— what to do when rule fires") }}</span>
          </div>
          <div class="p-5">
            <RuleActionList v-model="actionsState" />
            <p v-if="showErrors && actionsState.length === 0" class="mt-2 text-xs text-red-500">
              {{ __("Add at least one action.") }}
            </p>
          </div>
        </div>

      </div>
    </div>

    <!-- Test Rule Modal -->
    <Dialog
      v-model="showTestModal"
      :options="{ title: __('Test Rule'), size: 'lg' }"
    >
      <template #body-content>
        <div class="flex flex-col gap-4">
          <p class="text-sm text-gray-600">
            {{ __("Select a ticket to evaluate this rule against. No actions will be executed.") }}
          </p>

          <div class="flex flex-col gap-1.5">
            <label class="text-xs font-semibold text-gray-500">{{ __("Ticket") }}</label>
            <FormControl
              type="text"
              v-model="testTicketId"
              :placeholder="__('Enter ticket ID or name')"
            />
          </div>

          <Button
            variant="solid"
            :label="__('Run Test')"
            :loading="testLoading"
            :disabled="!testTicketId"
            @click="runTest"
          />

          <!-- Test results -->
          <div v-if="testResult" class="flex flex-col gap-3 pt-2 border-t border-gray-100">
            <!-- Overall -->
            <div
              class="flex items-center gap-2 rounded-md px-3 py-2 text-sm font-semibold"
              :class="testResult.would_fire ? 'bg-green-50 text-green-700' : 'bg-gray-50 text-gray-500'"
            >
              <LucideCheckCircle v-if="testResult.would_fire" class="h-4 w-4 text-green-500" />
              <LucideXCircle v-else class="h-4 w-4 text-gray-400" />
              {{ testResult.would_fire ? __("Rule WOULD fire") : __("Rule would NOT fire") }}
            </div>

            <!-- Conditions -->
            <div v-if="testResult.conditions?.length">
              <p class="text-xs font-semibold text-gray-500 mb-1.5">{{ __("Conditions") }}</p>
              <div class="flex flex-col gap-1">
                <div
                  v-for="(cond, i) in testResult.conditions"
                  :key="i"
                  class="flex items-center gap-2 rounded px-2 py-1 text-xs"
                  :class="cond.matched ? 'bg-green-50 text-green-700' : 'bg-red-50 text-red-600'"
                >
                  <LucideCheck v-if="cond.matched" class="h-3 w-3 shrink-0" />
                  <LucideX v-else class="h-3 w-3 shrink-0" />
                  <span class="font-mono">{{ cond.field }} {{ cond.operator }} {{ cond.value ?? '' }}</span>
                </div>
              </div>
            </div>
            <div v-else class="text-xs text-gray-400 italic">{{ __("No conditions — rule always fires for trigger.") }}</div>

            <!-- Actions -->
            <div v-if="testResult.actions?.length">
              <p class="text-xs font-semibold text-gray-500 mb-1.5">{{ __("Actions") }}</p>
              <div class="flex flex-col gap-1">
                <div
                  v-for="(action, i) in testResult.actions"
                  :key="i"
                  class="flex items-center gap-2 rounded px-2 py-1 text-xs"
                  :class="action.would_execute ? 'bg-blue-50 text-blue-700' : 'bg-gray-50 text-gray-400'"
                >
                  <LucidePlay v-if="action.would_execute" class="h-3 w-3 shrink-0" />
                  <LucideMinus v-else class="h-3 w-3 shrink-0" />
                  <span class="font-mono">{{ action.type }}<span v-if="action.value">: {{ action.value }}</span></span>
                </div>
              </div>
            </div>
          </div>
        </div>
      </template>
    </Dialog>
  </div>
</template>

<script setup lang="ts">
import { ref, computed, onMounted, watch } from "vue"
import { useRoute, useRouter } from "vue-router"
import { Badge, Button, Dialog, FormControl, LoadingIndicator, call, toast, usePageMeta } from "frappe-ui"
import { useAuthStore } from "@/stores/auth"
import { __ } from "@/translation"
import RuleTriggerSelect from "@/components/automation/RuleTriggerSelect.vue"
import RuleConditionBuilder from "@/components/automation/RuleConditionBuilder.vue"
import RuleActionList from "@/components/automation/RuleActionList.vue"
import LucideSave from "~icons/lucide/save"
import LucideFlaskConical from "~icons/lucide/flask-conical"
import LucideCheckCircle from "~icons/lucide/check-circle"
import LucideXCircle from "~icons/lucide/x-circle"
import LucideCheck from "~icons/lucide/check"
import LucideX from "~icons/lucide/x"
import LucidePlay from "~icons/lucide/play"
import LucideMinus from "~icons/lucide/minus"
import LucideLock from "~icons/lucide/lock"

const route = useRoute()
const router = useRouter()
const authStore = useAuthStore()

const id = computed(() => route.params.id as string)
const isNew = computed(() => id.value === "new")

usePageMeta(() => ({
  title: isNew.value ? "New Automation Rule" : (formState.value.rule_name || "Edit Rule"),
}))

const loading = ref(false)
const saving = ref(false)
const showErrors = ref(false)
const showTestModal = ref(false)
const testLoading = ref(false)
const testTicketId = ref("")
const testResult = ref<any>(null)

const formState = ref({
  rule_name: "",
  description: "",
  trigger_type: "",
  priority_order: 10,
  enabled: true,
  failure_count: 0,
})

const conditionsState = ref({ logic: "AND", conditions: [] as any[] })
const actionsState = ref([] as any[])

// Load existing rule
async function loadRule() {
  if (isNew.value) return
  loading.value = true
  try {
    const data = await call("frappe.client.get", {
      doctype: "HD Automation Rule",
      name: id.value,
    })
    formState.value = {
      rule_name: data.rule_name || "",
      description: data.description || "",
      trigger_type: data.trigger_type || "",
      priority_order: data.priority_order ?? 10,
      enabled: !!data.enabled,
      failure_count: data.failure_count || 0,
    }
    // Parse conditions
    let rawConditions = data.conditions
    if (typeof rawConditions === "string") {
      try { rawConditions = JSON.parse(rawConditions) } catch { rawConditions = [] }
    }
    if (Array.isArray(rawConditions)) {
      // Handle nested group format: [{"logic":"OR","conditions":[...]}]
      if (rawConditions.length === 1 && rawConditions[0].logic && Array.isArray(rawConditions[0].conditions)) {
        conditionsState.value = {
          logic: rawConditions[0].logic,
          conditions: rawConditions[0].conditions,
        }
      } else {
        conditionsState.value = { logic: "AND", conditions: rawConditions }
      }
    } else if (rawConditions && typeof rawConditions === "object") {
      // Legacy dict wrapper format
      conditionsState.value = {
        logic: rawConditions.logic || "AND",
        conditions: rawConditions.conditions || [],
      }
    }
    // Parse actions
    let rawActions = data.actions
    if (typeof rawActions === "string") {
      try { rawActions = JSON.parse(rawActions) } catch { rawActions = [] }
    }
    actionsState.value = Array.isArray(rawActions) ? rawActions : []
  } finally {
    loading.value = false
  }
}

async function saveRule() {
  showErrors.value = true

  if (!formState.value.rule_name?.trim()) {
    toast.warning(__("Rule name is required."))
    return
  }
  if (!formState.value.trigger_type) {
    toast.warning(__("Please select a trigger."))
    return
  }
  if (actionsState.value.length === 0) {
    toast.warning(__("Add at least one action."))
    return
  }

  saving.value = true
  try {
    const payload = {
      doctype: "HD Automation Rule",
      rule_name: formState.value.rule_name.trim(),
      description: formState.value.description || "",
      trigger_type: formState.value.trigger_type,
      priority_order: Number(formState.value.priority_order) || 10,
      enabled: formState.value.enabled ? 1 : 0,
      conditions: JSON.stringify(
        conditionsState.value.logic === "OR" && conditionsState.value.conditions?.length
          ? [{ logic: "OR", conditions: conditionsState.value.conditions }]
          : conditionsState.value.conditions || []
      ),
      actions: JSON.stringify(actionsState.value),
    }

    if (isNew.value) {
      await call("frappe.client.insert", { doc: payload })
    } else {
      await call("frappe.client.set_value", {
        doctype: "HD Automation Rule",
        name: id.value,
        fieldname: payload,
      })
    }
    showErrors.value = false
    toast.success(__("Automation rule saved."))
    router.push({ name: "AutomationList" })
  } catch (e: any) {
    toast.error(e?.messages?.[0] || e?.message || __("Failed to save rule."))
  } finally {
    saving.value = false
  }
}

function navigateBack() {
  router.push({ name: "AutomationList" })
}

function openTestModal() {
  testResult.value = null
  testTicketId.value = ""
  showTestModal.value = true
}

async function runTest() {
  if (!testTicketId.value?.trim()) return
  testLoading.value = true
  try {
    const result = await call("helpdesk.api.automation.test_rule", {
      rule_name: id.value,
      ticket_name: testTicketId.value.trim(),
    })
    testResult.value = result
  } catch (e: any) {
    toast.error(e?.messages?.[0] || e?.message || __("Error running test."))
  } finally {
    testLoading.value = false
  }
}

onMounted(loadRule)
</script>
