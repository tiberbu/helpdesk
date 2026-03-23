# Story 1.7: Per-Ticket Time Tracking

Status: ready-for-dev

## Story

As a support agent,
I want to log time spent on a ticket with both manual entry and timer mode,
so that effort is tracked for reporting and billing.

## Acceptance Criteria

1. **[Timer — Start]** Given an agent is viewing a ticket, when they click the "Start Timer" button in the `TimeTracker.vue` sidebar component, then:
   - A timer begins counting elapsed time visible in the UI (format `HH:MM:SS`, monospace font, updates every second)
   - The timer start timestamp and ticket ID are persisted in `localStorage` under key `hd_timer_{ticketId}` so the timer survives page navigation and browser refresh
   - The "Start Timer" button changes to a "Stop Timer" button (disabled state: start; enabled state: stop)
   - The timer is scoped to one ticket at a time — if a timer is already active on another ticket, the user is warned ("A timer is already running for ticket {X}. Stop it first.")

2. **[Timer — Stop and Create Entry]** Given a timer is running, when the agent clicks "Stop Timer", then:
   - The elapsed duration is calculated in minutes: `Math.ceil((stopTimestamp - startTimestamp) / 60000)`
   - The `stop_timer` API endpoint is called with `ticket`, `started_at`, and calculated `duration_minutes`
   - An HD Time Entry is created on the server with: `ticket`, `agent` (current user), `duration_minutes`, `billable` (default: unchecked), `description` (empty), `timestamp` (stop time)
   - A description prompt modal appears immediately after stop so the agent can optionally add a description and toggle the billable checkbox before finalizing
   - The `localStorage` timer entry `hd_timer_{ticketId}` is cleared
   - The timer display resets to `00:00:00` and the UI reverts to the "Start Timer" state
   - The time summary in the sidebar refreshes to include the new entry

3. **[Manual Entry — Form]** Given an agent wants to log time without using the timer, when they click "Add Time Entry" in the sidebar, then:
   - A modal dialog opens with fields:
     - **Duration** (hours input + minutes input, both numeric, both required, combined value must be > 0 minutes)
     - **Description** (text area, optional, max 500 chars)
     - **Billable** (checkbox, default: unchecked)
   - The "Save" button is disabled until duration is valid (> 0 total minutes)
   - On "Save", the `add_entry` API endpoint is called with `ticket`, `duration_minutes`, `description`, `billable`
   - An HD Time Entry is created linked to the current ticket and current agent
   - The modal closes and the sidebar time summary refreshes

4. **[Manual Entry — Validation]** Given an agent submits the manual entry form, when the total minutes is 0 or the hours/minutes fields contain non-numeric input, then:
   - A form-level validation error is shown inline ("Duration must be greater than 0")
   - The API is NOT called
   - The modal remains open for correction

5. **[HD Time Entry DocType — Schema]** Given the HD Time Entry DocType is created, when inspected, then it has these fields:
   - `ticket` (Link → HD Ticket, required): the parent ticket
   - `agent` (Link → User, required, default: `__user`): the agent who logged the time
   - `duration_minutes` (Int, required, minimum 1): duration in minutes
   - `billable` (Check, default 0): whether the time is billable
   - `description` (Text, optional): note about what was done
   - `timestamp` (Datetime, required, default: Now): when the time was logged
   - `started_at` (Datetime, optional): timer start time (populated for timer-mode entries)
   - The DocType follows the HD prefix naming convention (AR-02) with module "Helpdesk"
   - The DocType is accessible via the standard Frappe REST API (`/api/resource/HD Time Entry`) per NFR-M-02

6. **[Time Summary — Sidebar Display]** Given a ticket has one or more HD Time Entry records, when an agent views the ticket sidebar, then:
   - The TimeTracker sidebar section shows a summary header with:
     - **Total time**: sum of all `duration_minutes` formatted as `Xh Ym` (e.g., "1h 30m")
     - **Billable time**: sum of `duration_minutes` where `billable = 1`, formatted as `Xh Ym`
   - Below the summary, an entry list shows each HD Time Entry as a row with: agent name (first name + last initial), date (`DD MMM`), duration (`Xh Ym`), description preview (truncated to 60 chars), and billable badge (shown only if `billable = 1`)
   - The entry list is ordered by `timestamp` descending (newest first)
   - If no time entries exist, an empty state is shown: "No time logged yet" with the "Add Time Entry" button

7. **[Time Summary — Entry Delete]** Given a time entry is shown in the sidebar list, when an agent clicks the delete (trash) icon on their own entry, then:
   - A confirmation dialog appears: "Delete this time entry? This cannot be undone."
   - On confirmation, the HD Time Entry is deleted via `frappe.client.delete`
   - Agents may only delete their own entries; HD Admin / System Manager may delete any entry
   - The sidebar refreshes to reflect the updated totals

8. **[API — `get_summary`]** Given the `get_summary(ticket)` endpoint is called, when there are multiple time entries, then:
   - It returns: `{ total_minutes, billable_minutes, entries: [{ name, agent, agent_name, duration_minutes, billable, description, timestamp }] }`
   - The function is decorated with `@frappe.whitelist()` and requires Agent role (read permission on HD Time Entry)
   - Entries are sorted by `timestamp` descending

9. **[API — `start_timer` / `stop_timer`]** Given the server-side timer support API exists in `helpdesk/api/time_tracking.py`, then:
   - `start_timer(ticket)`: validates the agent has write permission on the HD Ticket, returns `{ started_at: <ISO datetime> }` for the client to store in localStorage
   - `stop_timer(ticket, started_at, duration_minutes, description, billable)`: creates an HD Time Entry with the provided values; returns the created entry's `name`
   - Both endpoints use `@frappe.whitelist()` and internally call `frappe.has_permission("HD Ticket", "write", doc=ticket, throw=True)`

10. **[API — `add_entry`]** Given the `add_entry(ticket, duration_minutes, description, billable)` endpoint is called, then:
    - It validates `duration_minutes >= 1` and raises `frappe.ValidationError` if not
    - It creates an HD Time Entry with `agent = frappe.session.user` and `timestamp = frappe.utils.now_datetime()`
    - Returns `{ name: <entry_name>, success: True }`
    - The endpoint uses `@frappe.whitelist()` and requires write permission on HD Ticket

11. **[Timer Persistence — localStorage]** Given a timer is running and the agent navigates away from the ticket, when they return to any ticket detail page, then:
    - The `TimeTracker.vue` component checks `localStorage` for `hd_timer_{ticketId}` on mount
    - If a timer entry exists for the current ticket, the timer resumes counting from the stored start time
    - If a timer entry exists for a DIFFERENT ticket, the component shows a passive warning banner: "Timer running on ticket {X}" with a link to navigate there
    - The localStorage key format is: `{ started_at: "<ISO string>", ticket: "<ticket_name>" }`

12. **[Unit Tests — Backend]** Given the implementation is complete, when the test suite runs, then unit tests exist covering:
    - `add_entry` creates an HD Time Entry with correct fields (ticket, agent, duration, billable, description)
    - `add_entry` raises `frappe.ValidationError` when `duration_minutes < 1`
    - `stop_timer` creates an HD Time Entry with `started_at` populated
    - `get_summary` returns correct `total_minutes`, `billable_minutes`, and `entries` count for a ticket with mixed billable/non-billable entries
    - `get_summary` returns zeroes and empty list for a ticket with no entries
    - Permission check: non-Agent caller to `add_entry` raises `frappe.PermissionError`
    - Minimum 80% line coverage on all new backend Python code (NFR-M-01)

## Tasks / Subtasks

- [ ] Task 1 — Create `HD Time Entry` DocType (AC: #5)
  - [ ] 1.1 Create `helpdesk/helpdesk/doctype/hd_time_entry/hd_time_entry.json`:
    ```json
    {
      "name": "HD Time Entry",
      "doctype": "DocType",
      "module": "Helpdesk",
      "is_child_table": 0,
      "istable": 0,
      "fields": [
        {
          "fieldname": "ticket",
          "fieldtype": "Link",
          "label": "Ticket",
          "options": "HD Ticket",
          "reqd": 1,
          "in_list_view": 1,
          "in_standard_filter": 1
        },
        {
          "fieldname": "agent",
          "fieldtype": "Link",
          "label": "Agent",
          "options": "User",
          "reqd": 1,
          "default": "__user",
          "in_list_view": 1
        },
        {
          "fieldname": "duration_minutes",
          "fieldtype": "Int",
          "label": "Duration (Minutes)",
          "reqd": 1,
          "in_list_view": 1
        },
        {
          "fieldname": "billable",
          "fieldtype": "Check",
          "label": "Billable",
          "default": 0,
          "in_list_view": 1
        },
        {
          "fieldname": "description",
          "fieldtype": "Text",
          "label": "Description"
        },
        {
          "fieldname": "timestamp",
          "fieldtype": "Datetime",
          "label": "Logged At",
          "reqd": 1,
          "default": "Now",
          "in_list_view": 1
        },
        {
          "fieldname": "started_at",
          "fieldtype": "Datetime",
          "label": "Timer Started At",
          "read_only": 1
        }
      ],
      "permissions": [
        {"role": "HD Agent", "read": 1, "write": 1, "create": 1, "delete": 1},
        {"role": "HD Admin", "read": 1, "write": 1, "create": 1, "delete": 1},
        {"role": "System Manager", "read": 1, "write": 1, "create": 1, "delete": 1}
      ],
      "sort_field": "timestamp",
      "sort_order": "DESC"
    }
    ```
  - [ ] 1.2 Create `helpdesk/helpdesk/doctype/hd_time_entry/__init__.py` (empty file).
  - [ ] 1.3 Create `helpdesk/helpdesk/doctype/hd_time_entry/hd_time_entry.py`:
    ```python
    # Copyright (c) 2026, Frappe Technologies Pvt. Ltd. and contributors
    # For license information, please see license.txt

    import frappe
    from frappe import _
    from frappe.model.document import Document


    class HDTimeEntry(Document):
        def validate(self):
            if self.duration_minutes < 1:
                frappe.throw(
                    _("Duration must be at least 1 minute."),
                    frappe.ValidationError,
                )
    ```
  - [ ] 1.4 Run `bench migrate` to create the `tabHD Time Entry` database table.

- [ ] Task 2 — Implement `helpdesk/api/time_tracking.py` (AC: #8, #9, #10)
  - [ ] 2.1 Create `helpdesk/api/time_tracking.py`:
    ```python
    # Copyright (c) 2026, Frappe Technologies Pvt. Ltd. and contributors
    # For license information, please see license.txt

    import frappe
    from frappe import _
    from frappe.utils import now_datetime


    @frappe.whitelist()
    def start_timer(ticket: str) -> dict:
        """
        Validate agent has write access to the ticket and return server-side
        start timestamp for the client to store in localStorage.

        Returns: { "started_at": "<ISO datetime string>" }
        """
        frappe.has_permission("HD Ticket", "write", doc=ticket, throw=True)
        started_at = now_datetime()
        return {"started_at": str(started_at)}


    @frappe.whitelist()
    def stop_timer(
        ticket: str,
        started_at: str,
        duration_minutes: int,
        description: str = "",
        billable: int = 0,
    ) -> dict:
        """
        Create an HD Time Entry from a stopped timer session.

        Returns: { "name": "<entry_name>", "success": True }
        """
        frappe.has_permission("HD Ticket", "write", doc=ticket, throw=True)

        duration_minutes = int(duration_minutes)
        if duration_minutes < 1:
            frappe.throw(_("Duration must be at least 1 minute."), frappe.ValidationError)

        entry = frappe.get_doc(
            {
                "doctype": "HD Time Entry",
                "ticket": ticket,
                "agent": frappe.session.user,
                "duration_minutes": duration_minutes,
                "billable": int(billable),
                "description": description or "",
                "timestamp": now_datetime(),
                "started_at": started_at,
            }
        )
        entry.insert(ignore_permissions=True)
        frappe.db.commit()

        return {"name": entry.name, "success": True}


    @frappe.whitelist()
    def add_entry(
        ticket: str,
        duration_minutes: int,
        description: str = "",
        billable: int = 0,
    ) -> dict:
        """
        Create an HD Time Entry via manual entry form.

        Returns: { "name": "<entry_name>", "success": True }
        """
        frappe.has_permission("HD Ticket", "write", doc=ticket, throw=True)

        duration_minutes = int(duration_minutes)
        if duration_minutes < 1:
            frappe.throw(_("Duration must be at least 1 minute."), frappe.ValidationError)

        entry = frappe.get_doc(
            {
                "doctype": "HD Time Entry",
                "ticket": ticket,
                "agent": frappe.session.user,
                "duration_minutes": duration_minutes,
                "billable": int(billable),
                "description": description or "",
                "timestamp": now_datetime(),
            }
        )
        entry.insert(ignore_permissions=True)
        frappe.db.commit()

        return {"name": entry.name, "success": True}


    @frappe.whitelist()
    def get_summary(ticket: str) -> dict:
        """
        Return time summary for a ticket: totals and entry list.

        Returns:
        {
            "total_minutes": int,
            "billable_minutes": int,
            "entries": [
                {
                    "name": str,
                    "agent": str,
                    "agent_name": str,
                    "duration_minutes": int,
                    "billable": int,
                    "description": str,
                    "timestamp": str
                },
                ...
            ]
        }
        """
        frappe.has_permission("HD Ticket", "read", doc=ticket, throw=True)

        entries = frappe.get_all(
            "HD Time Entry",
            filters={"ticket": ticket},
            fields=[
                "name",
                "agent",
                "duration_minutes",
                "billable",
                "description",
                "timestamp",
            ],
            order_by="timestamp desc",
        )

        # Resolve agent full names
        for entry in entries:
            user = frappe.db.get_value(
                "User", entry["agent"], ["first_name", "last_name"], as_dict=True
            )
            if user:
                last_initial = (user.last_name or "")[:1]
                entry["agent_name"] = (
                    f"{user.first_name} {last_initial}." if last_initial else user.first_name
                )
            else:
                entry["agent_name"] = entry["agent"]

        total_minutes = sum(e["duration_minutes"] for e in entries)
        billable_minutes = sum(
            e["duration_minutes"] for e in entries if e["billable"]
        )

        return {
            "total_minutes": total_minutes,
            "billable_minutes": billable_minutes,
            "entries": entries,
        }
    ```
  - [ ] 2.2 Confirm that `helpdesk/api/__init__.py` exists (or the `api/` directory is a flat package); no explicit import registration is needed for `@frappe.whitelist()` functions — they are auto-discoverable.

- [ ] Task 3 — Create `TimeTracker.vue` sidebar component (AC: #1, #2, #3, #4, #6, #7, #11)
  - [ ] 3.1 Create `desk/src/components/ticket/TimeTracker.vue`:
    ```vue
    <template>
      <div class="time-tracker-panel">
        <!-- Summary Header -->
        <div class="flex items-center justify-between mb-3">
          <h3 class="text-sm font-semibold text-gray-700">
            {{ __('Time Tracking') }}
          </h3>
          <Button size="sm" variant="ghost" @click="openManualEntry" :label="__('Add Entry')">
            <template #prefix><LucidePlus class="w-3 h-3" /></template>
          </Button>
        </div>

        <!-- Active Timer Display -->
        <div
          v-if="isTimerRunning"
          class="mb-3 rounded-md bg-blue-50 border border-blue-200 px-3 py-2 flex items-center justify-between"
        >
          <div>
            <p class="text-xs text-blue-600 font-medium">{{ __('Timer running') }}</p>
            <p class="font-mono text-lg text-blue-800 tabular-nums">{{ formattedElapsed }}</p>
          </div>
          <Button
            size="sm"
            variant="solid"
            theme="red"
            :label="__('Stop')"
            @click="stopTimer"
          />
        </div>

        <!-- Cross-ticket timer warning -->
        <div
          v-else-if="foreignTimerTicket"
          class="mb-3 rounded-md bg-yellow-50 border border-yellow-200 px-3 py-2 text-xs text-yellow-700"
        >
          {{ __('Timer running on') }}
          <router-link
            :to="`/tickets/${foreignTimerTicket}`"
            class="font-medium underline"
          >{{ foreignTimerTicket }}</router-link>.
          {{ __('Stop it before starting a new timer.') }}
        </div>

        <!-- Start Timer Button (when no timer active) -->
        <Button
          v-else
          size="sm"
          variant="outline"
          class="w-full mb-3"
          @click="startTimer"
          :loading="startResource.loading"
        >
          <template #prefix><LucideTimer class="w-3 h-3" /></template>
          {{ __('Start Timer') }}
        </Button>

        <!-- Totals -->
        <div v-if="summary.total_minutes > 0" class="mb-3 flex gap-4 text-xs text-gray-600">
          <div>
            <span class="font-medium text-gray-800">{{ formatMinutes(summary.total_minutes) }}</span>
            <span class="ml-1">{{ __('total') }}</span>
          </div>
          <div v-if="summary.billable_minutes > 0">
            <span class="font-medium text-gray-800">{{ formatMinutes(summary.billable_minutes) }}</span>
            <span class="ml-1">{{ __('billable') }}</span>
          </div>
        </div>

        <!-- Entry List -->
        <ul v-if="summary.entries?.length" class="space-y-1" role="list">
          <li
            v-for="entry in summary.entries"
            :key="entry.name"
            class="flex items-start justify-between gap-2 rounded border border-gray-100 bg-gray-50 px-2 py-1.5 text-xs"
          >
            <div class="min-w-0 flex-1">
              <div class="flex items-center gap-1">
                <span class="font-medium text-gray-800">{{ formatMinutes(entry.duration_minutes) }}</span>
                <Badge v-if="entry.billable" label="Billable" theme="green" size="sm" />
                <span class="text-gray-400 ml-auto">{{ formatDate(entry.timestamp) }}</span>
              </div>
              <p class="text-gray-500 mt-0.5 truncate" :title="entry.description">
                {{ entry.agent_name }}<span v-if="entry.description"> — {{ entry.description }}</span>
              </p>
            </div>
            <button
              v-if="canDelete(entry)"
              class="text-gray-400 hover:text-red-500 transition-colors flex-shrink-0"
              :aria-label="__('Delete time entry')"
              @click="confirmDelete(entry)"
            >
              <LucideTrash2 class="w-3 h-3" />
            </button>
          </li>
        </ul>

        <!-- Empty State -->
        <div v-else-if="!isTimerRunning" class="text-center py-4 text-gray-400 text-xs">
          <LucideClock class="w-5 h-5 mx-auto mb-1 opacity-50" />
          <p>{{ __('No time logged yet') }}</p>
        </div>

        <!-- Manual Entry Dialog -->
        <TimeEntryDialog
          v-if="showManualEntry"
          :ticket-id="ticketId"
          @saved="onEntrySaved"
          @close="showManualEntry = false"
        />

        <!-- Stop Timer: description/billable prompt -->
        <TimeEntryDialog
          v-if="showStopPrompt"
          :ticket-id="ticketId"
          :prefill-duration-minutes="pendingDurationMinutes"
          mode="stop-timer"
          @saved="onStopSaved"
          @close="showStopPrompt = false"
        />

        <!-- Delete Confirmation -->
        <Dialog
          v-if="deleteTarget"
          :options="{
            title: __('Delete Time Entry'),
            message: __('Delete this time entry? This cannot be undone.'),
            actions: [
              { label: __('Cancel'), variant: 'subtle', onClick: () => deleteTarget = null },
              { label: __('Delete'), variant: 'solid', theme: 'red', onClick: doDelete },
            ],
          }"
          @close="deleteTarget = null"
        />
      </div>
    </template>

    <script setup lang="ts">
    import { ref, computed, onMounted, onUnmounted } from 'vue'
    import { createResource, Button, Badge, Dialog } from 'frappe-ui'
    import {
      LucidePlus, LucideTimer, LucideClock, LucideTrash2,
    } from 'lucide-vue-next'
    import TimeEntryDialog from './TimeEntryDialog.vue'

    const props = defineProps<{ ticketId: string }>()

    // --- Timer state ---
    const STORAGE_KEY = `hd_timer_${props.ticketId}`
    const isTimerRunning = ref(false)
    const timerStartedAt = ref<number | null>(null)
    const elapsed = ref(0) // seconds
    const foreignTimerTicket = ref<string | null>(null)
    let timerInterval: ReturnType<typeof setInterval> | null = null

    const showManualEntry = ref(false)
    const showStopPrompt = ref(false)
    const pendingDurationMinutes = ref(0)
    const deleteTarget = ref<{ name: string } | null>(null)

    const summary = ref<{
      total_minutes: number
      billable_minutes: number
      entries: any[]
    }>({ total_minutes: 0, billable_minutes: 0, entries: [] })

    // --- Computed ---
    const formattedElapsed = computed(() => {
      const h = Math.floor(elapsed.value / 3600)
      const m = Math.floor((elapsed.value % 3600) / 60)
      const s = elapsed.value % 60
      return [h, m, s].map((v) => String(v).padStart(2, '0')).join(':')
    })

    // --- Lifecycle ---
    onMounted(() => {
      loadTimer()
      loadSummary()
    })

    onUnmounted(() => {
      if (timerInterval) clearInterval(timerInterval)
    })

    // --- Timer helpers ---
    function loadTimer() {
      // Check for timer on this ticket
      const stored = localStorage.getItem(STORAGE_KEY)
      if (stored) {
        const data = JSON.parse(stored)
        timerStartedAt.value = new Date(data.started_at).getTime()
        elapsed.value = Math.floor((Date.now() - timerStartedAt.value) / 1000)
        isTimerRunning.value = true
        timerInterval = setInterval(tick, 1000)
        return
      }
      // Check for timer on a different ticket
      for (let i = 0; i < localStorage.length; i++) {
        const key = localStorage.key(i)
        if (key && key.startsWith('hd_timer_') && key !== STORAGE_KEY) {
          const data = JSON.parse(localStorage.getItem(key)!)
          foreignTimerTicket.value = data.ticket
          break
        }
      }
    }

    function tick() {
      elapsed.value = Math.floor((Date.now() - (timerStartedAt.value ?? Date.now())) / 1000)
    }

    const startResource = createResource({
      url: 'helpdesk.api.time_tracking.start_timer',
      onSuccess(data: { started_at: string }) {
        timerStartedAt.value = new Date(data.started_at).getTime()
        elapsed.value = 0
        isTimerRunning.value = true
        foreignTimerTicket.value = null
        localStorage.setItem(
          STORAGE_KEY,
          JSON.stringify({ started_at: data.started_at, ticket: props.ticketId })
        )
        timerInterval = setInterval(tick, 1000)
      },
    })

    function startTimer() {
      if (foreignTimerTicket.value) return
      startResource.submit({ ticket: props.ticketId })
    }

    function stopTimer() {
      if (timerInterval) { clearInterval(timerInterval); timerInterval = null }
      isTimerRunning.value = false
      pendingDurationMinutes.value = Math.max(1, Math.ceil(elapsed.value / 60))
      showStopPrompt.value = true
    }

    function onStopSaved() {
      localStorage.removeItem(STORAGE_KEY)
      elapsed.value = 0
      timerStartedAt.value = null
      showStopPrompt.value = false
      loadSummary()
    }

    // --- Manual entry ---
    function openManualEntry() { showManualEntry.value = true }

    function onEntrySaved() {
      showManualEntry.value = false
      loadSummary()
    }

    // --- Summary ---
    const summaryResource = createResource({
      url: 'helpdesk.api.time_tracking.get_summary',
      onSuccess(data: any) { summary.value = data },
    })

    function loadSummary() {
      summaryResource.submit({ ticket: props.ticketId })
    }

    // --- Delete ---
    function canDelete(entry: any): boolean {
      return (
        entry.agent === (window as any).frappe?.session?.user ||
        (window as any).frappe?.user?.has_role?.('HD Admin') ||
        (window as any).frappe?.user?.has_role?.('System Manager')
      )
    }

    function confirmDelete(entry: { name: string }) {
      deleteTarget.value = entry
    }

    const deleteResource = createResource({
      url: 'frappe.client.delete',
      onSuccess() {
        deleteTarget.value = null
        loadSummary()
      },
    })

    function doDelete() {
      if (!deleteTarget.value) return
      deleteResource.submit({ doctype: 'HD Time Entry', name: deleteTarget.value.name })
    }

    // --- Formatting ---
    function formatMinutes(mins: number): string {
      const h = Math.floor(mins / 60)
      const m = mins % 60
      if (h === 0) return `${m}m`
      if (m === 0) return `${h}h`
      return `${h}h ${m}m`
    }

    function formatDate(ts: string): string {
      return new Date(ts).toLocaleDateString(undefined, { day: '2-digit', month: 'short' })
    }
    </script>
    ```
  - [ ] 3.2 Create `desk/src/components/ticket/TimeEntryDialog.vue` — shared modal for both manual entry and post-timer-stop entry:
    ```vue
    <template>
      <Dialog
        :options="{ title: dialogTitle, size: 'sm' }"
        v-model="show"
        @close="emit('close')"
      >
        <template #body-content>
          <div class="space-y-4">
            <!-- Duration -->
            <div>
              <label class="text-sm font-medium text-gray-700">{{ __('Duration') }} *</label>
              <div class="flex gap-2 mt-1">
                <FormControl
                  type="number"
                  :placeholder="__('Hours')"
                  v-model="hours"
                  :min="0"
                  class="w-24"
                />
                <FormControl
                  type="number"
                  :placeholder="__('Minutes')"
                  v-model="minutes"
                  :min="0"
                  :max="59"
                  class="w-24"
                />
              </div>
              <p v-if="durationError" class="text-xs text-red-600 mt-1">{{ durationError }}</p>
            </div>

            <!-- Description -->
            <FormControl
              type="textarea"
              :label="__('Description')"
              :placeholder="__('What did you work on? (optional)')"
              v-model="description"
              :max-length="500"
            />

            <!-- Billable -->
            <FormControl
              type="checkbox"
              :label="__('Billable')"
              v-model="billable"
            />
          </div>
        </template>
        <template #actions>
          <Button variant="subtle" @click="emit('close')">{{ __('Cancel') }}</Button>
          <Button
            variant="solid"
            :disabled="!isValid || saveResource.loading"
            :loading="saveResource.loading"
            @click="save"
          >
            {{ __('Save') }}
          </Button>
        </template>
      </Dialog>
    </template>

    <script setup lang="ts">
    import { ref, computed, watch } from 'vue'
    import { createResource, Button, Dialog, FormControl } from 'frappe-ui'

    const props = defineProps<{
      ticketId: string
      prefillDurationMinutes?: number
      mode?: 'manual' | 'stop-timer'
    }>()
    const emit = defineEmits<{ saved: []; close: [] }>()

    const show = ref(true)
    const description = ref('')
    const billable = ref(false)
    const hours = ref(0)
    const minutes = ref(0)

    // Pre-fill from timer if provided
    watch(
      () => props.prefillDurationMinutes,
      (val) => {
        if (val) {
          hours.value = Math.floor(val / 60)
          minutes.value = val % 60
        }
      },
      { immediate: true }
    )

    const dialogTitle = computed(() =>
      props.mode === 'stop-timer' ? __('Log Timer Entry') : __('Add Time Entry')
    )

    const totalMinutes = computed(() => (Number(hours.value) * 60) + Number(minutes.value))

    const durationError = computed(() =>
      totalMinutes.value < 1 ? __('Duration must be greater than 0') : ''
    )

    const isValid = computed(() => totalMinutes.value >= 1)

    const endpoint = computed(() =>
      props.mode === 'stop-timer'
        ? 'helpdesk.api.time_tracking.stop_timer'
        : 'helpdesk.api.time_tracking.add_entry'
    )

    const saveResource = createResource({
      url: endpoint.value,
      onSuccess() { emit('saved') },
    })

    function save() {
      if (!isValid.value) return
      const params: Record<string, any> = {
        ticket: props.ticketId,
        duration_minutes: totalMinutes.value,
        description: description.value,
        billable: billable.value ? 1 : 0,
      }
      saveResource.submit(params)
    }
    </script>
    ```
  - [ ] 3.3 Register `TimeTracker.vue` in the ticket sidebar. Locate the ticket sidebar composition file (likely `desk/src/pages/ticket/TicketSidebar.vue` or `desk/src/pages/ticket/index.vue`) and add:
    ```vue
    import TimeTracker from '@/components/ticket/TimeTracker.vue'
    <!-- in template: -->
    <TimeTracker :ticket-id="ticket.name" />
    ```
  - [ ] 3.4 Verify WCAG 2.1 AA compliance (NFR-U-04): icon-only delete button has `aria-label`, timer display has `role="timer"` and `aria-live="polite"`, entry list uses `role="list"`.

- [ ] Task 4 — Write unit tests (AC: #12)
  - [ ] 4.1 Create `helpdesk/helpdesk/doctype/hd_time_entry/test_hd_time_entry.py`:
    ```python
    import frappe
    from frappe.tests.utils import FrappeTestCase
    from helpdesk.api.time_tracking import add_entry, stop_timer, get_summary


    class TestHDTimeEntry(FrappeTestCase):
        """Unit tests for Story 1.7: Per-Ticket Time Tracking."""

        def setUp(self):
            self.ticket = frappe.get_doc(
                {
                    "doctype": "HD Ticket",
                    "subject": "Time Tracking Test Ticket",
                    "raised_by": "customer.tt@test.com",
                }
            ).insert(ignore_permissions=True)

            if not frappe.db.exists("User", "agent.tt@test.com"):
                frappe.get_doc(
                    {
                        "doctype": "User",
                        "email": "agent.tt@test.com",
                        "full_name": "Time Agent",
                        "first_name": "Time",
                        "last_name": "Agent",
                        "send_welcome_email": 0,
                        "roles": [{"role": "HD Agent"}],
                    }
                ).insert(ignore_permissions=True)

            frappe.set_user("agent.tt@test.com")

        def tearDown(self):
            frappe.set_user("Administrator")
            frappe.db.rollback()

        # --- add_entry tests ---

        def test_add_entry_creates_time_entry(self):
            result = add_entry(
                ticket=self.ticket.name,
                duration_minutes=30,
                description="Investigated the issue",
                billable=1,
            )
            self.assertTrue(result.get("success"))
            entry = frappe.get_doc("HD Time Entry", result["name"])
            self.assertEqual(entry.ticket, self.ticket.name)
            self.assertEqual(entry.agent, "agent.tt@test.com")
            self.assertEqual(entry.duration_minutes, 30)
            self.assertEqual(entry.billable, 1)
            self.assertEqual(entry.description, "Investigated the issue")

        def test_add_entry_with_zero_duration_raises_validation_error(self):
            with self.assertRaises(frappe.ValidationError):
                add_entry(ticket=self.ticket.name, duration_minutes=0)

        def test_add_entry_with_negative_duration_raises_validation_error(self):
            with self.assertRaises(frappe.ValidationError):
                add_entry(ticket=self.ticket.name, duration_minutes=-5)

        # --- stop_timer tests ---

        def test_stop_timer_creates_entry_with_started_at(self):
            started_at = "2026-03-23 10:00:00"
            result = stop_timer(
                ticket=self.ticket.name,
                started_at=started_at,
                duration_minutes=45,
                description="Timer session",
                billable=0,
            )
            self.assertTrue(result.get("success"))
            entry = frappe.get_doc("HD Time Entry", result["name"])
            self.assertEqual(entry.duration_minutes, 45)
            self.assertEqual(str(entry.started_at), started_at)

        # --- get_summary tests ---

        def test_get_summary_returns_correct_totals(self):
            add_entry(ticket=self.ticket.name, duration_minutes=60, billable=1)
            add_entry(ticket=self.ticket.name, duration_minutes=30, billable=0)
            add_entry(ticket=self.ticket.name, duration_minutes=15, billable=1)

            summary = get_summary(ticket=self.ticket.name)
            self.assertEqual(summary["total_minutes"], 105)
            self.assertEqual(summary["billable_minutes"], 75)
            self.assertEqual(len(summary["entries"]), 3)

        def test_get_summary_returns_zeroes_for_empty_ticket(self):
            summary = get_summary(ticket=self.ticket.name)
            self.assertEqual(summary["total_minutes"], 0)
            self.assertEqual(summary["billable_minutes"], 0)
            self.assertEqual(summary["entries"], [])

        def test_get_summary_entries_sorted_descending_by_timestamp(self):
            add_entry(ticket=self.ticket.name, duration_minutes=10, billable=0)
            add_entry(ticket=self.ticket.name, duration_minutes=20, billable=0)
            summary = get_summary(ticket=self.ticket.name)
            timestamps = [e["timestamp"] for e in summary["entries"]]
            self.assertEqual(timestamps, sorted(timestamps, reverse=True),
                             "Entries should be sorted newest first")

        # --- Permission tests ---

        def test_customer_cannot_add_entry(self):
            frappe.set_user("customer.tt@test.com")
            with self.assertRaises(frappe.PermissionError):
                add_entry(ticket=self.ticket.name, duration_minutes=30)
            frappe.set_user("agent.tt@test.com")
    ```
  - [ ] 4.2 Run tests:
    ```bash
    bench --site <site> run-tests --module helpdesk.helpdesk.doctype.hd_time_entry.test_hd_time_entry
    ```
  - [ ] 4.3 Verify ≥80% line coverage on all new backend Python code (NFR-M-01).

- [ ] Task 5 — Add migration patch (AC: #5)
  - [ ] 5.1 Create `helpdesk/patches/v1_phase1/create_hd_time_entry.py`:
    ```python
    """
    Patch: Create HD Time Entry DocType table.
    Story: 1.7 -- Per-Ticket Time Tracking
    """
    import frappe


    def execute():
        frappe.reload_doctype("HD Time Entry", force=True)
    ```
  - [ ] 5.2 Register the patch in `patches.txt`:
    ```
    helpdesk.patches.v1_phase1.create_hd_time_entry
    ```
  - [ ] 5.3 Confirm `helpdesk/patches/v1_phase1/__init__.py` exists (create if absent — Stories 1.1–1.6 may have already created it).

## Dev Notes

### Architecture Patterns

- **HD Time Entry DocType (ADR-02):** The architecture explicitly defines `HD Time Entry` as a new standalone DocType (not a child table) with the relationship `HD Ticket → time_entries → HD Time Entry (via ticket Link)`. This means HD Time Entry has a `ticket` Link field (not `parent`), making it queryable independently. Do NOT implement as a child table. [Source: architecture.md#ADR-02]

- **API Location (ADR-08):** All time tracking endpoints (`start_timer`, `stop_timer`, `add_entry`, `get_summary`) belong in `helpdesk/api/time_tracking.py`. This module is explicitly mapped in the architecture's API design table. [Source: architecture.md#ADR-08]

- **Frontend Component Location (ADR-09):** `TimeTracker.vue` is explicitly listed in the architecture's shared component map at `desk/src/components/ticket/TimeTracker.vue`. Do NOT place it elsewhere. [Source: architecture.md#ADR-09]

- **Timer Persistence via localStorage:** The timer is a client-side concern. The server's `start_timer` endpoint returns a timestamp for client storage; it does NOT create a pending DB record. The HD Time Entry is only created when `stop_timer` is called. The localStorage key is `hd_timer_{ticketId}`. This avoids orphan DB records from abandoned timer sessions.

- **No HD Ticket Schema Change Required:** Unlike Stories 1.2–1.6, this story does NOT require modifying `hd_ticket.json`. The HD Time Entry DocType references HD Ticket via a Link field, not via a child table on HD Ticket. The time summary is loaded on demand via `get_summary`. [Source: architecture.md#ADR-02, relationship diagram]

- **`createResource` for Data Fetching (ADR-09):** Follow the existing codebase pattern of `createResource` from `frappe-ui` for all API calls. Do NOT use raw `fetch` or `axios`. [Source: architecture.md]

- **Frappe DocType CRUD:** The delete action in the sidebar uses `frappe.client.delete` (standard Frappe endpoint) rather than a custom delete endpoint. Permission enforcement is handled by Frappe's built-in RBAC on the HD Time Entry DocType — HD Agent role can only delete its own records if the DocType permissions are configured accordingly. Alternatively, implement a custom `delete_entry(name)` API if fine-grained ownership checks are needed beyond Frappe's standard `owner` field.

- **ERPNext Integration (Out of Scope for 1.7):** Story 6.5 (Time Tracking Reports) includes optional ERPNext Timesheet sync. This is explicitly out of scope for Story 1.7. Do NOT implement ERPNext sync in this story. [Source: epics.md#Story 6.5]

- **Monospace Font for Timer Display:** The UX design specifies a monospace font for the running timer display (`font-mono` in Tailwind CSS). The timer value must use `tabular-nums` to prevent layout shift as digits change. [Source: epics.md#UX-DR-04, Story 1.7 AC]

### Files to Create / Modify

| Action  | Path                                                                  | Notes                                         |
|---------|-----------------------------------------------------------------------|-----------------------------------------------|
| Create  | `helpdesk/helpdesk/doctype/hd_time_entry/hd_time_entry.json`          | New DocType definition                        |
| Create  | `helpdesk/helpdesk/doctype/hd_time_entry/__init__.py`                  | Python package init (empty)                   |
| Create  | `helpdesk/helpdesk/doctype/hd_time_entry/hd_time_entry.py`            | DocType controller with validate hook         |
| Create  | `helpdesk/helpdesk/doctype/hd_time_entry/test_hd_time_entry.py`       | Unit tests                                    |
| Create  | `helpdesk/api/time_tracking.py`                                       | `start_timer`, `stop_timer`, `add_entry`, `get_summary` |
| Create  | `helpdesk/patches/v1_phase1/create_hd_time_entry.py`                  | Migration patch                               |
| Modify  | `patches.txt`                                                         | Register migration patch                      |
| Create  | `desk/src/components/ticket/TimeTracker.vue`                          | Sidebar timer + summary component             |
| Create  | `desk/src/components/ticket/TimeEntryDialog.vue`                      | Shared modal for manual entry & stop-timer    |
| Modify  | `desk/src/pages/ticket/{TicketSidebar or TicketDetail}.vue`           | Register TimeTracker in ticket sidebar        |

### Testing Standards

- Use `frappe.tests.utils.FrappeTestCase` as base class (consistent with Story 1.4–1.6 patterns).
- All test fixtures created in `setUp` must be cleaned up via `frappe.db.rollback()` in `tearDown`.
- Test both zero-duration and negative-duration validation in `add_entry`.
- The `get_summary` tests must create actual HD Time Entry records (not mocks) to test the aggregation logic accurately.
- The permission test must use `frappe.set_user()` to simulate a non-agent caller and restore to a privileged user in `tearDown`.
- Minimum **80% line coverage** on all new backend Python code (NFR-M-01).

### Constraints

- Do NOT implement the timer as a server-side record (no "pending" HD Time Entry). localStorage is the sole persistence mechanism for the running timer. This avoids ghost entries when users abandon timers.
- Do NOT modify `hd_ticket.json` for this story. The time summary is fetched on demand, not stored as a summary field on HD Ticket.
- The `duration_minutes` field must be `>= 1` (not 0) — this is enforced both in the Vue form validation (client-side) and in the HDTimeEntry `validate` hook (server-side).
- All user-facing strings must use `frappe._()` in Python and `__()` in Vue/TypeScript for i18n compatibility.
- Timer display must use `font-mono` CSS class and `tabular-nums` to prevent layout shift.
- Only one timer may be active per browser session (per localStorage). Multiple tickets can have entries, but only one timer runs at a time.

### Project Structure Notes

- **`patches/v1_phase1/__init__.py`:** This file may already exist from Stories 1.1–1.6. Check before creating — do not overwrite if it exists.
- **`helpdesk/api/time_tracking.py`:** This is a new module. Verify `helpdesk/api/` directory exists and follows the flat module pattern used by other API files (e.g., `helpdesk/api/ticket.py`, `helpdesk/api/chat.py`). No registration in `__init__.py` is needed; `@frappe.whitelist()` functions are discovered automatically by Frappe's request routing.
- **Ticket sidebar wiring:** Look for where other story components (`RelatedTickets.vue`, `InternalNote.vue`) were registered in the sidebar (from Stories 1.4–1.6). The `TimeTracker.vue` placement should be consistent with those — typically in the right sidebar section. Inspect `TicketSidebar.vue` or the ticket detail page's composition root.
- **Story 6.5 dependency:** The `HD Time Entry` DocType created in this story is the data source for Story 6.5 (Time Tracking Reports). Ensure all fields specified in this story's schema are stable before Story 6.5 begins.

### References

- FR-TT-01 (Per-ticket time logging — manual, timer, billable/non-billable, summary): [Source: _bmad-output/planning-artifacts/epics.md#FR-TT-01]
- UX-DR-04 (Time tracker with start/stop timer and manual entry in sidebar): [Source: _bmad-output/planning-artifacts/epics.md#UX-DR-04]
- Story 1.7 AC (from Epics): [Source: _bmad-output/planning-artifacts/epics.md#Story 1.7]
- ADR-02 (HD Time Entry in the 10 new DocTypes, standalone with ticket Link): [Source: _bmad-output/planning-artifacts/architecture.md#ADR-02]
- ADR-08 (`helpdesk/api/time_tracking.py` API module mapping): [Source: _bmad-output/planning-artifacts/architecture.md#ADR-08]
- ADR-09 (`desk/src/components/ticket/TimeTracker.vue` component location): [Source: _bmad-output/planning-artifacts/architecture.md#ADR-09]
- AR-02 (HD prefix naming, standard Frappe DocType structure): [Source: _bmad-output/planning-artifacts/epics.md#AR-02]
- AR-04 (New DocTypes via DocType JSON, not Custom Fields): [Source: _bmad-output/planning-artifacts/epics.md#AR-04]
- AR-05 (Migration patches in `helpdesk/patches/v1_phase1/`): [Source: _bmad-output/planning-artifacts/epics.md#AR-05]
- NFR-M-01 (80% unit test coverage on all new backend code): [Source: _bmad-output/planning-artifacts/epics.md#Non-Functional Requirements]
- NFR-M-02 (All new DocTypes accessible via REST API): [Source: _bmad-output/planning-artifacts/epics.md#Non-Functional Requirements]
- NFR-U-04 (WCAG 2.1 AA for all new UI components): [Source: _bmad-output/planning-artifacts/epics.md#Non-Functional Requirements]
- Story 6.5 (Time Tracking Reports — consumes HD Time Entry from this story): [Source: _bmad-output/planning-artifacts/epics.md#Story 6.5]

## Dev Agent Record

### Agent Model Used

Claude Sonnet 4.5 (create-story workflow)

### Debug Log References

_None — story creation phase_

### Completion Notes List

_To be filled by implementing dev agent_

### File List

_To be filled by implementing dev agent upon completion_
