# Story 1.8: Major Incident Flag and Workflow

Status: ready-for-dev

## Story

As a support agent,
I want to flag a ticket as a Major Incident to trigger an expedited response process,
so that critical issues affecting multiple customers receive immediate management attention.

## Acceptance Criteria

1. **[Flag — Checkbox and Confirmation Dialog]** Given an agent is viewing a ticket, when they check the `is_major_incident` checkbox, then:
   - A confirmation dialog appears with message: "Flagging this ticket as a Major Incident will immediately notify all escalation contacts via email and in-app notification. Continue?"
   - The dialog has two buttons: "Cancel" (reverts the checkbox to unchecked) and "Confirm — Flag as Major Incident"
   - If the agent clicks "Cancel", the checkbox is NOT checked and no action is taken
   - If the agent clicks "Confirm", the `flag_major_incident` API endpoint is called with the ticket name

2. **[Flag — Server-side State Change]** Given the agent confirms the major incident flag, when `flag_major_incident(ticket)` is called, then:
   - `is_major_incident` is set to `1` on the HD Ticket
   - `major_incident_flagged_at` is set to `frappe.utils.now_datetime()`
   - Both fields are saved to the database
   - The function returns `{ "success": True, "flagged_at": "<ISO datetime>" }`
   - The endpoint uses `@frappe.whitelist()` and requires write permission on HD Ticket

3. **[Flag — Escalation Notifications]** Given a ticket is flagged as major incident, when the `flag_major_incident` endpoint completes, then:
   - All emails listed in `HD Settings.major_incident_contacts` (comma-separated email addresses) receive an email notification using the `major_incident_alert.html` template containing: ticket subject, ticket link, flagged_at datetime, flagging agent name
   - Each contact also receives an in-app notification via `frappe.realtime.publish` to their `agent:{email}` room with event `major_incident_flagged` containing ticket name, subject, and link
   - Notification sending is enqueued as a background job (queue="short") so it does not block the API response
   - If `major_incident_contacts` is empty, the system logs a warning but does NOT raise an error

4. **[Banner — Major Incident Display]** Given a ticket has `is_major_incident = 1`, when an agent opens the ticket detail view, then:
   - A `MajorIncidentBanner.vue` component is displayed prominently at the top of the ticket view (above the conversation thread), with:
     - Red background (`bg-red-50 border border-red-200`)
     - Bold label: "MAJOR INCIDENT" with a red badge
     - Elapsed time display: "Open for Xh Ym" — calculated client-side from `major_incident_flagged_at`, updating every minute
     - Count of linked tickets: "X linked tickets" (from the `related_tickets` child table count)
     - A "Propagate Update" button (visible only to agents with HD Agent or HD Admin role)
   - The banner is NOT shown on tickets where `is_major_incident = 0`

5. **[Banner — Elapsed Time Calculation]** Given the `MajorIncidentBanner.vue` component is mounted, when `major_incident_flagged_at` is provided as a prop, then:
   - The elapsed time is computed as `Math.floor((Date.now() - new Date(flaggedAt).getTime()) / 60000)` minutes
   - Displayed as: `< 1h` if under 60 minutes, `Xh` if exact hours, `Xh Ym` if hours and remaining minutes
   - A `setInterval` of 60 000ms updates the display while the component is mounted
   - The interval is cleared in `onUnmounted` to prevent memory leaks

6. **[Status Update Propagation]** Given a ticket is flagged as major incident and has linked tickets, when an agent clicks "Propagate Update" in the `MajorIncidentBanner`, then:
   - A modal dialog opens with a textarea: "Status Update Message" (required, max 1000 chars) and a preview showing the count of linked tickets that will receive this update
   - On submit, the `propagate_update(ticket, message)` API endpoint is called
   - The endpoint adds the message as a public comment on the major incident ticket AND on every ticket listed in the `related_tickets` child table (regardless of link type)
   - The comment body is prefixed with: `[Major Incident Update] `
   - Returns `{ "success": True, "propagated_to": [list of ticket names] }`
   - The endpoint uses `@frappe.whitelist()` and requires write permission on HD Ticket

7. **[Status Update — Empty Linked Tickets]** Given a ticket is flagged as major incident but has NO linked tickets, when the agent clicks "Propagate Update", then:
   - The modal opens normally but the preview shows: "No linked tickets — update will only be posted on this ticket"
   - On submit, the update is posted only on the major incident ticket itself
   - No error is raised

8. **[Post-Incident Review Fields]** Given a ticket has `is_major_incident = 1` and an agent changes the ticket status to "Resolved" or "Closed", when the ticket form re-renders after status change, then:
   - Three new fields become visible in a "Post-Incident Review" section on the ticket form:
     - `root_cause_summary` (Long Text, label: "Root Cause Summary")
     - `corrective_actions` (Long Text, label: "Corrective Actions")
     - `prevention_measures` (Long Text, label: "Prevention Measures")
   - These fields are hidden (using `depends_on` condition in the DocType JSON) when `is_major_incident = 0` OR when status is not Resolved/Closed
   - The fields are NOT required — agents can save the ticket without filling them
   - A visual hint is displayed: "Completing the post-incident review helps prevent recurrence"

9. **[HD Ticket DocType — Schema Changes]** Given the HD Ticket DocType is modified, when inspected, then it includes these new fields:
   - `is_major_incident` (Check, default 0, label: "Major Incident", in_list_view: 1)
   - `major_incident_flagged_at` (Datetime, label: "Flagged At", read_only: 1)
   - `root_cause_summary` (Long Text, label: "Root Cause Summary", depends_on: `eval:doc.is_major_incident && (doc.status=='Resolved'||doc.status=='Closed')`)
   - `corrective_actions` (Long Text, label: "Corrective Actions", depends_on: `eval:doc.is_major_incident && (doc.status=='Resolved'||doc.status=='Closed')`)
   - `prevention_measures` (Long Text, label: "Prevention Measures", depends_on: `eval:doc.is_major_incident && (doc.status=='Resolved'||doc.status=='Closed')`)
   - All new fields are added via DocType JSON modification (AR-04), NOT via Custom Fields

10. **[HD Settings — `major_incident_contacts` Field]** Given HD Settings is modified, when an admin opens HD Settings, then:
    - A new field `major_incident_contacts` (Small Text, label: "Major Incident Escalation Contacts") is visible
    - Help text reads: "Comma-separated list of email addresses to notify when a major incident is flagged"
    - The field is saved and retrieved correctly via the standard HD Settings document

11. **[Major Incidents Dashboard — Route and Page]** Given a manager navigates to `/helpdesk/major-incidents`, then:
    - A `MajorIncidentDashboard.vue` page component is rendered
    - The page is registered in the Vue Router configuration
    - The page is accessible to users with HD Agent, HD Admin, or System Manager roles
    - The page title is "Major Incidents"

12. **[Major Incidents Dashboard — Cards Display]** Given the major incidents dashboard is open, when the page loads, then:
    - All tickets where `is_major_incident = 1` are fetched via `createListResource` with fields: `name`, `subject`, `status`, `is_major_incident`, `major_incident_flagged_at`, `related_tickets` (count), `raised_by`
    - Active major incidents (status NOT in ["Resolved", "Closed"]) are displayed first, sorted by `major_incident_flagged_at` ascending (oldest first)
    - Resolved/Closed major incidents are shown in a separate "Resolved" section below
    - Each incident is displayed as a card with:
      - Ticket subject (clickable link to ticket detail)
      - Status badge (color-coded)
      - Elapsed time: "Open for Xh Ym" (same calculation as the banner)
      - Linked ticket count: "X linked tickets"
      - Affected customer count: unique count of `raised_by` across all linked tickets plus the major incident ticket itself (fetched via `get_major_incident_summary` API)
    - If no active major incidents exist, an empty state shows: "No active major incidents"

13. **[Major Incidents Dashboard — Summary API]** Given the `get_major_incident_summary(ticket)` API endpoint is called, when there are linked tickets, then:
    - It returns: `{ "linked_ticket_count": int, "affected_customer_count": int, "linked_tickets": [list of ticket names] }`
    - `affected_customer_count` is the count of unique `raised_by` values across the major incident ticket and all its linked tickets
    - The function uses `@frappe.whitelist()` and requires read permission on HD Ticket

14. **[Unit Tests — Backend]** Given the implementation is complete, when the test suite runs, then unit tests exist covering:
    - `flag_major_incident` sets `is_major_incident=1` and `major_incident_flagged_at` on the ticket
    - `flag_major_incident` raises `frappe.PermissionError` when called by a non-agent user
    - `propagate_update` adds a comment to the major incident ticket and all linked tickets
    - `propagate_update` returns the correct list of `propagated_to` ticket names
    - `propagate_update` succeeds (posts only to parent) when there are no linked tickets
    - `get_major_incident_summary` returns correct `linked_ticket_count` and `affected_customer_count`
    - `get_major_incident_summary` returns zeros for a ticket with no linked tickets
    - Minimum 80% line coverage on all new backend Python code (NFR-M-01)

## Tasks / Subtasks

- [ ] Task 1 — Modify HD Ticket DocType JSON to add major incident fields (AC: #9)
  - [ ] 1.1 Open `helpdesk/helpdesk/doctype/hd_ticket/hd_ticket.json` and add the following fields to the `fields` array (place them in a logical section after existing incident management fields):
    ```json
    {
      "fieldname": "is_major_incident",
      "fieldtype": "Check",
      "label": "Major Incident",
      "default": "0",
      "in_list_view": 1,
      "bold": 1
    },
    {
      "fieldname": "major_incident_flagged_at",
      "fieldtype": "Datetime",
      "label": "Flagged At",
      "read_only": 1,
      "no_copy": 1
    },
    {
      "fieldname": "major_incident_section",
      "fieldtype": "Section Break",
      "label": "Post-Incident Review",
      "depends_on": "eval:doc.is_major_incident && (doc.status=='Resolved'||doc.status=='Closed')"
    },
    {
      "fieldname": "root_cause_summary",
      "fieldtype": "Long Text",
      "label": "Root Cause Summary",
      "depends_on": "eval:doc.is_major_incident && (doc.status=='Resolved'||doc.status=='Closed')"
    },
    {
      "fieldname": "corrective_actions",
      "fieldtype": "Long Text",
      "label": "Corrective Actions",
      "depends_on": "eval:doc.is_major_incident && (doc.status=='Resolved'||doc.status=='Closed')"
    },
    {
      "fieldname": "prevention_measures",
      "fieldtype": "Long Text",
      "label": "Prevention Measures",
      "depends_on": "eval:doc.is_major_incident && (doc.status=='Resolved'||doc.status=='Closed')"
    }
    ```
  - [ ] 1.2 Run `bench migrate` to apply schema changes to `tabHD Ticket`.

- [ ] Task 2 — Modify HD Settings DocType JSON to add `major_incident_contacts` field (AC: #10)
  - [ ] 2.1 Open `helpdesk/helpdesk/doctype/hd_settings/hd_settings.json` and add:
    ```json
    {
      "fieldname": "major_incident_contacts",
      "fieldtype": "Small Text",
      "label": "Major Incident Escalation Contacts",
      "description": "Comma-separated list of email addresses to notify when a major incident is flagged"
    }
    ```
  - [ ] 2.2 Place the field in a logical section (e.g., near other notification/escalation settings).
  - [ ] 2.3 Run `bench migrate` to apply the schema change.

- [ ] Task 3 — Create `helpdesk/api/incident.py` with `flag_major_incident`, `propagate_update`, and `get_major_incident_summary` endpoints (AC: #2, #3, #6, #7, #13)
  - [ ] 3.1 Create `helpdesk/api/incident.py`:
    ```python
    # Copyright (c) 2026, Frappe Technologies Pvt. Ltd. and contributors
    # For license information, please see license.txt

    import frappe
    from frappe import _
    from frappe.utils import now_datetime


    @frappe.whitelist()
    def flag_major_incident(ticket: str) -> dict:
        """
        Flag a ticket as a Major Incident.

        Sets is_major_incident=1, records flagged_at timestamp,
        and enqueues escalation notifications.

        Returns: { "success": True, "flagged_at": "<ISO datetime>" }
        """
        frappe.has_permission("HD Ticket", "write", doc=ticket, throw=True)

        doc = frappe.get_doc("HD Ticket", ticket)
        flagged_at = now_datetime()
        doc.is_major_incident = 1
        doc.major_incident_flagged_at = flagged_at
        doc.save(ignore_permissions=True)
        frappe.db.commit()

        # Enqueue notifications as a background job (queue="short")
        frappe.enqueue(
            "helpdesk.api.incident._send_major_incident_notifications",
            queue="short",
            ticket=ticket,
            flagged_at=str(flagged_at),
            flagging_agent=frappe.session.user,
        )

        return {"success": True, "flagged_at": str(flagged_at)}


    def _send_major_incident_notifications(
        ticket: str, flagged_at: str, flagging_agent: str
    ) -> None:
        """
        Background job: send email and in-app notifications to major_incident_contacts.
        Called via frappe.enqueue — NOT a whitelisted endpoint.
        """
        settings = frappe.get_single("HD Settings")
        contacts_raw = getattr(settings, "major_incident_contacts", "") or ""
        contacts = [c.strip() for c in contacts_raw.split(",") if c.strip()]

        if not contacts:
            frappe.log_error(
                title="Major Incident Notification: No contacts configured",
                message=f"Ticket {ticket} was flagged as major incident but no escalation contacts are set in HD Settings.",
            )
            return

        doc = frappe.get_doc("HD Ticket", ticket)
        agent_name = frappe.db.get_value("User", flagging_agent, "full_name") or flagging_agent
        ticket_url = frappe.utils.get_url(f"/helpdesk/tickets/{ticket}")

        for email in contacts:
            # Email notification
            frappe.sendmail(
                recipients=[email],
                subject=_("Major Incident: {0}").format(doc.subject),
                template="major_incident_alert",
                args={
                    "ticket_name": ticket,
                    "ticket_subject": doc.subject,
                    "ticket_url": ticket_url,
                    "flagged_at": flagged_at,
                    "flagging_agent": agent_name,
                },
                now=True,
            )

            # In-app notification via Socket.IO
            frappe.realtime.publish(
                "major_incident_flagged",
                {
                    "ticket": ticket,
                    "subject": doc.subject,
                    "ticket_url": ticket_url,
                    "flagged_at": flagged_at,
                    "flagging_agent": agent_name,
                },
                room=f"agent:{email}",
            )


    @frappe.whitelist()
    def propagate_update(ticket: str, message: str) -> dict:
        """
        Post a status update comment on the major incident ticket and all linked tickets.

        Returns: { "success": True, "propagated_to": [list of ticket names] }
        """
        frappe.has_permission("HD Ticket", "write", doc=ticket, throw=True)

        if not message or not message.strip():
            frappe.throw(_("Update message cannot be empty."), frappe.ValidationError)

        prefixed_message = f"[Major Incident Update] {message.strip()}"

        # Gather all tickets to update: the major incident itself + all linked tickets
        linked_names = frappe.get_all(
            "HD Related Ticket",
            filters={"parent": ticket},
            pluck="related_ticket",
        )
        all_tickets = [ticket] + linked_names

        propagated_to = []
        for t in all_tickets:
            try:
                t_doc = frappe.get_doc("HD Ticket", t)
                t_doc.append(
                    "communications",
                    {
                        "doctype": "HD Ticket Communication",
                        "content": prefixed_message,
                        "sent_or_received": "Sent",
                        "communication_type": "Comment",
                        "sender": frappe.session.user,
                    },
                )
                t_doc.save(ignore_permissions=True)
                propagated_to.append(t)
            except Exception as e:
                frappe.log_error(
                    title=f"propagate_update: failed for ticket {t}",
                    message=str(e),
                )

        frappe.db.commit()
        return {"success": True, "propagated_to": propagated_to}


    @frappe.whitelist()
    def get_major_incident_summary(ticket: str) -> dict:
        """
        Return summary data for a major incident ticket:
        linked ticket count and affected customer count (unique raised_by values).

        Returns:
        {
            "linked_ticket_count": int,
            "affected_customer_count": int,
            "linked_tickets": [list of ticket names]
        }
        """
        frappe.has_permission("HD Ticket", "read", doc=ticket, throw=True)

        linked_names = frappe.get_all(
            "HD Related Ticket",
            filters={"parent": ticket},
            pluck="related_ticket",
        )

        # Collect unique customers across the major incident ticket + linked tickets
        all_ticket_names = [ticket] + linked_names
        raised_by_values = frappe.get_all(
            "HD Ticket",
            filters={"name": ["in", all_ticket_names]},
            pluck="raised_by",
        )
        unique_customers = len(set(v for v in raised_by_values if v))

        return {
            "linked_ticket_count": len(linked_names),
            "affected_customer_count": unique_customers,
            "linked_tickets": linked_names,
        }
    ```
  - [ ] 3.2 Verify that `helpdesk/api/__init__.py` exists (the `api/` directory must be a Python package). No explicit import is needed — `@frappe.whitelist()` functions are auto-discoverable.

- [ ] Task 4 — Create `major_incident_alert.html` email template (AC: #3)
  - [ ] 4.1 Create `helpdesk/templates/major_incident_alert.html`:
    ```html
    <!DOCTYPE html>
    <html>
    <head><meta charset="utf-8" /></head>
    <body style="font-family: sans-serif; color: #333; max-width: 600px; margin: 0 auto;">
      <div style="background: #fee2e2; border-left: 4px solid #ef4444; padding: 16px 20px; margin-bottom: 20px;">
        <h2 style="color: #b91c1c; margin: 0 0 4px;">Major Incident Declared</h2>
        <p style="margin: 0; color: #7f1d1d;">Immediate attention required</p>
      </div>

      <table style="width: 100%; border-collapse: collapse; margin-bottom: 20px;">
        <tr>
          <td style="padding: 8px 0; font-weight: bold; width: 40%;">Ticket:</td>
          <td style="padding: 8px 0;">
            <a href="{{ ticket_url }}" style="color: #2563eb;">{{ ticket_name }} — {{ ticket_subject }}</a>
          </td>
        </tr>
        <tr>
          <td style="padding: 8px 0; font-weight: bold;">Flagged At:</td>
          <td style="padding: 8px 0;">{{ flagged_at }}</td>
        </tr>
        <tr>
          <td style="padding: 8px 0; font-weight: bold;">Flagged By:</td>
          <td style="padding: 8px 0;">{{ flagging_agent }}</td>
        </tr>
      </table>

      <p>
        <a href="{{ ticket_url }}"
           style="background: #ef4444; color: white; padding: 10px 20px; text-decoration: none; border-radius: 4px; display: inline-block;">
          View Major Incident
        </a>
      </p>

      <p style="font-size: 12px; color: #9ca3af; margin-top: 32px;">
        This is an automated notification from Frappe Helpdesk.
        You are receiving this because you are listed as a major incident escalation contact.
      </p>
    </body>
    </html>
    ```

- [ ] Task 5 — Create `MajorIncidentBanner.vue` component (AC: #4, #5, #6, #7)
  - [ ] 5.1 Create `desk/src/components/ticket/MajorIncidentBanner.vue`:
    ```vue
    <template>
      <div
        v-if="isMajorIncident"
        class="mx-4 mt-3 rounded-md border border-red-200 bg-red-50 px-4 py-3"
        role="alert"
        aria-label="Major Incident Banner"
      >
        <div class="flex items-center justify-between gap-4">
          <div class="flex items-center gap-3 min-w-0">
            <!-- Badge -->
            <span
              class="inline-flex items-center rounded-full bg-red-600 px-2.5 py-0.5 text-xs font-semibold text-white uppercase tracking-wide flex-shrink-0"
            >
              Major Incident
            </span>

            <!-- Elapsed time -->
            <span class="text-sm font-medium text-red-800">
              Open for <span class="font-bold">{{ elapsedLabel }}</span>
            </span>

            <!-- Linked ticket count -->
            <span
              v-if="linkedTicketCount > 0"
              class="text-sm text-red-700"
            >
              &middot; {{ linkedTicketCount }} linked ticket{{ linkedTicketCount !== 1 ? 's' : '' }}
            </span>
          </div>

          <!-- Propagate Update button -->
          <Button
            size="sm"
            variant="subtle"
            theme="red"
            :label="__('Propagate Update')"
            @click="showPropagateModal = true"
          />
        </div>
      </div>

      <!-- Propagate Update Modal -->
      <Dialog
        v-if="showPropagateModal"
        :options="{
          title: __('Propagate Status Update'),
          size: 'md',
        }"
        v-model="showPropagateModal"
      >
        <template #body-content>
          <div class="space-y-3">
            <p class="text-sm text-gray-600">
              <template v-if="linkedTicketCount > 0">
                {{ __('This update will be posted on this ticket and') }}
                <strong>{{ linkedTicketCount }}</strong>
                {{ __('linked ticket(s).') }}
              </template>
              <template v-else>
                {{ __('No linked tickets — update will only be posted on this ticket.') }}
              </template>
            </p>
            <FormControl
              type="textarea"
              :label="__('Status Update Message')"
              :placeholder="__('Describe the current status, what has been done, and next steps...')"
              v-model="updateMessage"
              :rows="4"
              :maxlength="1000"
            />
            <p
              v-if="messageError"
              class="text-xs text-red-600"
            >
              {{ messageError }}
            </p>
          </div>
        </template>
        <template #actions>
          <Button variant="subtle" @click="showPropagateModal = false">
            {{ __('Cancel') }}
          </Button>
          <Button
            variant="solid"
            theme="red"
            :disabled="propagateResource.loading"
            :loading="propagateResource.loading"
            @click="submitPropagation"
          >
            {{ __('Post Update') }}
          </Button>
        </template>
      </Dialog>
    </template>

    <script setup lang="ts">
    import { ref, computed, onMounted, onUnmounted } from 'vue'
    import { createResource, Button, Dialog, FormControl } from 'frappe-ui'

    const props = defineProps<{
      ticketName: string
      isMajorIncident: boolean
      flaggedAt: string | null
      linkedTicketCount: number
    }>()

    const emit = defineEmits<{ updated: [] }>()

    // --- Elapsed time ---
    const elapsedMinutes = ref(0)
    let elapsedInterval: ReturnType<typeof setInterval> | null = null

    function computeElapsed() {
      if (!props.flaggedAt) return
      elapsedMinutes.value = Math.floor(
        (Date.now() - new Date(props.flaggedAt).getTime()) / 60000
      )
    }

    const elapsedLabel = computed(() => {
      const mins = elapsedMinutes.value
      if (mins < 60) return mins < 1 ? '< 1m' : `${mins}m`
      const h = Math.floor(mins / 60)
      const m = mins % 60
      if (m === 0) return `${h}h`
      return `${h}h ${m}m`
    })

    onMounted(() => {
      computeElapsed()
      elapsedInterval = setInterval(computeElapsed, 60_000)
    })

    onUnmounted(() => {
      if (elapsedInterval) clearInterval(elapsedInterval)
    })

    // --- Propagate update modal ---
    const showPropagateModal = ref(false)
    const updateMessage = ref('')
    const messageError = ref('')

    const propagateResource = createResource({
      url: 'helpdesk.api.incident.propagate_update',
      onSuccess() {
        showPropagateModal.value = false
        updateMessage.value = ''
        messageError.value = ''
        emit('updated')
      },
      onError(err: any) {
        messageError.value = err?.message || __('Failed to post update. Please try again.')
      },
    })

    function submitPropagation() {
      messageError.value = ''
      if (!updateMessage.value.trim()) {
        messageError.value = __('Update message cannot be empty.')
        return
      }
      propagateResource.submit({
        ticket: props.ticketName,
        message: updateMessage.value,
      })
    }
    </script>
    ```
  - [ ] 5.2 Register `MajorIncidentBanner.vue` in the ticket detail view. Locate the ticket detail page component (e.g., `desk/src/pages/ticket/index.vue` or `TicketDetail.vue`) and:
    - Import the component: `import MajorIncidentBanner from '@/components/ticket/MajorIncidentBanner.vue'`
    - Add it in the template above the conversation thread:
      ```vue
      <MajorIncidentBanner
        :ticket-name="ticket.name"
        :is-major-incident="!!ticket.is_major_incident"
        :flagged-at="ticket.major_incident_flagged_at"
        :linked-ticket-count="ticket.related_tickets?.length ?? 0"
        @updated="reloadTicket"
      />
      ```
    - Ensure the ticket resource includes the fields `is_major_incident`, `major_incident_flagged_at`, and `related_tickets` (count or array).

- [ ] Task 6 — Add confirmation dialog for the `is_major_incident` checkbox (AC: #1)
  - [ ] 6.1 In the ticket detail view where the `is_major_incident` checkbox is rendered, intercept the change event to show the confirmation dialog before calling the API. This can be implemented as a `watch` on the checkbox field value or as a click handler that prevents the default toggle and shows a confirmation `Dialog` from frappe-ui.
  - [ ] 6.2 On confirmation: call `flag_major_incident` via `createResource` and on success set `ticket.is_major_incident = 1` and `ticket.major_incident_flagged_at` from the API response.
  - [ ] 6.3 On cancel: revert the checkbox value to `0` so the UI stays consistent with the server state.
  - [ ] 6.4 Example pattern:
    ```vue
    <script setup lang="ts">
    import { ref } from 'vue'
    import { createResource, Dialog } from 'frappe-ui'

    const showMajorIncidentConfirm = ref(false)

    function onMajorIncidentChange(newVal: boolean) {
      if (newVal) {
        // Intercept: show confirmation before actually setting
        ticket.is_major_incident = 0  // revert optimistic update
        showMajorIncidentConfirm.value = true
      }
    }

    const flagResource = createResource({
      url: 'helpdesk.api.incident.flag_major_incident',
      onSuccess(data: { flagged_at: string }) {
        ticket.is_major_incident = 1
        ticket.major_incident_flagged_at = data.flagged_at
        showMajorIncidentConfirm.value = false
      },
    })

    function confirmFlagMajorIncident() {
      flagResource.submit({ ticket: ticket.name })
    }
    </script>
    ```

- [ ] Task 7 — Create `MajorIncidentDashboard.vue` page and register route (AC: #11, #12, #13)
  - [ ] 7.1 Create `desk/src/pages/major-incidents/MajorIncidentDashboard.vue`:
    ```vue
    <template>
      <div class="mx-auto max-w-5xl px-4 py-6">
        <h1 class="text-2xl font-bold text-gray-900 mb-6">
          {{ __('Major Incidents') }}
        </h1>

        <!-- Active Incidents -->
        <section>
          <h2 class="text-base font-semibold text-gray-700 mb-3">
            {{ __('Active') }}
            <span v-if="activeIncidents.length" class="ml-1 text-sm font-normal text-gray-500">
              ({{ activeIncidents.length }})
            </span>
          </h2>

          <div v-if="listResource.loading" class="text-sm text-gray-400">
            {{ __('Loading...') }}
          </div>

          <div v-else-if="activeIncidents.length === 0" class="rounded-md border border-dashed border-gray-300 py-10 text-center text-sm text-gray-400">
            {{ __('No active major incidents') }}
          </div>

          <div v-else class="space-y-3">
            <MajorIncidentCard
              v-for="incident in activeIncidents"
              :key="incident.name"
              :incident="incident"
            />
          </div>
        </section>

        <!-- Resolved Incidents -->
        <section v-if="resolvedIncidents.length" class="mt-8">
          <h2 class="text-base font-semibold text-gray-700 mb-3">
            {{ __('Resolved') }}
            <span class="ml-1 text-sm font-normal text-gray-500">
              ({{ resolvedIncidents.length }})
            </span>
          </h2>
          <div class="space-y-3">
            <MajorIncidentCard
              v-for="incident in resolvedIncidents"
              :key="incident.name"
              :incident="incident"
              :resolved="true"
            />
          </div>
        </section>
      </div>
    </template>

    <script setup lang="ts">
    import { computed } from 'vue'
    import { createListResource } from 'frappe-ui'
    import MajorIncidentCard from './MajorIncidentCard.vue'

    const listResource = createListResource({
      doctype: 'HD Ticket',
      fields: [
        'name',
        'subject',
        'status',
        'is_major_incident',
        'major_incident_flagged_at',
        'raised_by',
      ],
      filters: { is_major_incident: 1 },
      orderBy: 'major_incident_flagged_at asc',
      pageLength: 200,
      auto: true,
    })

    const RESOLVED_STATUSES = ['Resolved', 'Closed']

    const activeIncidents = computed(() =>
      (listResource.data || []).filter(
        (t: any) => !RESOLVED_STATUSES.includes(t.status)
      )
    )

    const resolvedIncidents = computed(() =>
      (listResource.data || []).filter(
        (t: any) => RESOLVED_STATUSES.includes(t.status)
      )
    )
    </script>
    ```
  - [ ] 7.2 Create `desk/src/pages/major-incidents/MajorIncidentCard.vue` — a card sub-component that:
    - Accepts props: `incident` (ticket data object) and `resolved` (boolean, default false)
    - Displays: subject as a `<router-link>` to `/helpdesk/tickets/{name}`, status badge, elapsed time (using same calculation as banner), linked ticket count and affected customer count (fetched via `get_major_incident_summary`)
    - Uses `createResource` to call `helpdesk.api.incident.get_major_incident_summary` on mount
  - [ ] 7.3 Register the route in the Vue Router configuration (e.g., `desk/src/router/index.ts` or the routes file):
    ```javascript
    {
      path: '/helpdesk/major-incidents',
      name: 'MajorIncidents',
      component: () => import('@/pages/major-incidents/MajorIncidentDashboard.vue'),
    }
    ```
  - [ ] 7.4 Add a navigation link to the major incidents dashboard in the sidebar navigation (wherever agent navigation links are defined — e.g., `desk/src/components/Sidebar.vue` or equivalent).

- [ ] Task 8 — Write migration patch for HD Ticket schema changes (AC: #9)
  - [ ] 8.1 Create `helpdesk/patches/v1_phase1/add_major_incident_fields_to_ticket.py`:
    ```python
    """
    Patch: Add major incident fields to HD Ticket.
    Story: 1.8 -- Major Incident Flag and Workflow
    """
    import frappe


    def execute():
        frappe.reload_doctype("HD Ticket", force=True)
    ```
  - [ ] 8.2 Register the patch in `patches.txt`:
    ```
    helpdesk.patches.v1_phase1.add_major_incident_fields_to_ticket
    ```
  - [ ] 8.3 Similarly create and register a patch for HD Settings:
    ```python
    # helpdesk/patches/v1_phase1/add_major_incident_contacts_to_settings.py
    import frappe

    def execute():
        frappe.reload_doctype("HD Settings", force=True)
    ```
  - [ ] 8.4 Confirm `helpdesk/patches/v1_phase1/__init__.py` exists (Stories 1.1–1.7 may have already created it).

- [ ] Task 9 — Write unit tests (AC: #14)
  - [ ] 9.1 Create `helpdesk/helpdesk/doctype/hd_ticket/test_hd_ticket_major_incident.py`:
    ```python
    import frappe
    from frappe.tests.utils import FrappeTestCase
    from helpdesk.api.incident import (
        flag_major_incident,
        propagate_update,
        get_major_incident_summary,
    )


    class TestMajorIncidentWorkflow(FrappeTestCase):
        """Unit tests for Story 1.8: Major Incident Flag and Workflow."""

        def setUp(self):
            # Create a test agent user
            if not frappe.db.exists("User", "agent.mi@test.com"):
                frappe.get_doc({
                    "doctype": "User",
                    "email": "agent.mi@test.com",
                    "full_name": "MI Agent",
                    "first_name": "MI",
                    "last_name": "Agent",
                    "send_welcome_email": 0,
                    "roles": [{"role": "HD Agent"}],
                }).insert(ignore_permissions=True)

            frappe.set_user("agent.mi@test.com")

            # Primary major incident ticket
            self.ticket = frappe.get_doc({
                "doctype": "HD Ticket",
                "subject": "Production Outage — All Users Affected",
                "raised_by": "customer1@example.com",
            }).insert(ignore_permissions=True)

            # Linked tickets
            self.linked1 = frappe.get_doc({
                "doctype": "HD Ticket",
                "subject": "Cannot log in",
                "raised_by": "customer2@example.com",
            }).insert(ignore_permissions=True)

            self.linked2 = frappe.get_doc({
                "doctype": "HD Ticket",
                "subject": "Dashboard shows error",
                "raised_by": "customer3@example.com",
            }).insert(ignore_permissions=True)

        def tearDown(self):
            frappe.set_user("Administrator")
            frappe.db.rollback()

        def _link_ticket(self, parent_name: str, child_name: str):
            """Helper: add a related ticket entry."""
            parent = frappe.get_doc("HD Ticket", parent_name)
            parent.append("related_tickets", {
                "related_ticket": child_name,
                "link_type": "Related to",
            })
            parent.save(ignore_permissions=True)

        # --- flag_major_incident ---

        def test_flag_sets_is_major_incident_and_flagged_at(self):
            result = flag_major_incident(ticket=self.ticket.name)
            self.assertTrue(result.get("success"))
            self.assertIsNotNone(result.get("flagged_at"))

            doc = frappe.get_doc("HD Ticket", self.ticket.name)
            self.assertEqual(doc.is_major_incident, 1)
            self.assertIsNotNone(doc.major_incident_flagged_at)

        def test_flag_raises_permission_error_for_non_agent(self):
            frappe.set_user("Guest")
            with self.assertRaises(frappe.PermissionError):
                flag_major_incident(ticket=self.ticket.name)
            frappe.set_user("agent.mi@test.com")

        # --- propagate_update ---

        def test_propagate_update_posts_to_parent_and_linked_tickets(self):
            self._link_ticket(self.ticket.name, self.linked1.name)
            self._link_ticket(self.ticket.name, self.linked2.name)

            result = propagate_update(
                ticket=self.ticket.name,
                message="System is being restored. ETA 15 minutes.",
            )
            self.assertTrue(result.get("success"))
            propagated = result.get("propagated_to", [])
            self.assertIn(self.ticket.name, propagated)
            self.assertIn(self.linked1.name, propagated)
            self.assertIn(self.linked2.name, propagated)
            self.assertEqual(len(propagated), 3)

        def test_propagate_update_succeeds_with_no_linked_tickets(self):
            result = propagate_update(
                ticket=self.ticket.name,
                message="Status update with no linked tickets.",
            )
            self.assertTrue(result.get("success"))
            self.assertEqual(result.get("propagated_to"), [self.ticket.name])

        def test_propagate_update_raises_on_empty_message(self):
            with self.assertRaises(frappe.ValidationError):
                propagate_update(ticket=self.ticket.name, message="")

        def test_propagate_update_message_prefixed(self):
            self._link_ticket(self.ticket.name, self.linked1.name)
            propagate_update(
                ticket=self.ticket.name,
                message="Investigating root cause.",
            )
            # Check that the parent ticket has the prefixed comment
            # (Exact method to check communications depends on how HD Ticket stores them)
            doc = frappe.get_doc("HD Ticket", self.ticket.name)
            contents = [c.content for c in doc.get("communications", [])]
            self.assertTrue(
                any("[Major Incident Update]" in (c or "") for c in contents),
                "Expected '[Major Incident Update]' prefix in ticket communications",
            )

        # --- get_major_incident_summary ---

        def test_summary_returns_correct_counts(self):
            self._link_ticket(self.ticket.name, self.linked1.name)
            self._link_ticket(self.ticket.name, self.linked2.name)

            summary = get_major_incident_summary(ticket=self.ticket.name)
            self.assertEqual(summary["linked_ticket_count"], 2)
            # 3 unique customers: customer1, customer2, customer3
            self.assertEqual(summary["affected_customer_count"], 3)
            self.assertIn(self.linked1.name, summary["linked_tickets"])
            self.assertIn(self.linked2.name, summary["linked_tickets"])

        def test_summary_returns_zeroes_for_no_linked_tickets(self):
            summary = get_major_incident_summary(ticket=self.ticket.name)
            self.assertEqual(summary["linked_ticket_count"], 0)
            # 1 customer: the major incident ticket's raised_by
            self.assertEqual(summary["affected_customer_count"], 1)
            self.assertEqual(summary["linked_tickets"], [])

        def test_summary_deduplicates_customers(self):
            # Create a third ticket with the SAME customer as linked1
            dup = frappe.get_doc({
                "doctype": "HD Ticket",
                "subject": "Duplicate customer report",
                "raised_by": "customer2@example.com",  # same as linked1
            }).insert(ignore_permissions=True)
            self._link_ticket(self.ticket.name, self.linked1.name)
            self._link_ticket(self.ticket.name, dup.name)

            summary = get_major_incident_summary(ticket=self.ticket.name)
            # Unique customers: customer1 (parent), customer2 (linked1 + dup) = 2
            self.assertEqual(summary["affected_customer_count"], 2)
    ```
  - [ ] 9.2 Run tests:
    ```bash
    bench --site <site> run-tests --module helpdesk.helpdesk.doctype.hd_ticket.test_hd_ticket_major_incident
    ```
  - [ ] 9.3 Verify >= 80% line coverage on all new backend Python code (NFR-M-01).

## Dev Notes

### Architecture Patterns

- **HD Ticket Extension (ADR-01):** `is_major_incident`, `major_incident_flagged_at`, and the three post-incident review fields (`root_cause_summary`, `corrective_actions`, `prevention_measures`) are added directly to the HD Ticket DocType JSON via field modification — NOT as Custom Fields (AR-04). This maintains backward compatibility (NULL default for all legacy records). [Source: architecture.md#ADR-01, epics.md#AR-04]

- **API Location (ADR-08):** All major incident API endpoints (`flag_major_incident`, `propagate_update`, `get_major_incident_summary`) belong in `helpdesk/api/incident.py`. This module is explicitly listed in the architecture's API design table. [Source: architecture.md#ADR-08]

- **Background Job for Notifications (ADR-12):** Escalation notifications (email + in-app) MUST be sent via `frappe.enqueue()` with `queue="short"` to avoid blocking the API response. The `_send_major_incident_notifications` function is the background job target — it is NOT decorated with `@frappe.whitelist()`. [Source: architecture.md#ADR-12]

- **Notification Pipeline (cross-cutting concern):** Major incident notifications flow through the unified notification pipeline described in the architecture. In-app notifications use `frappe.realtime.publish` to the `agent:{email}` Socket.IO room (AR-07 room naming convention). [Source: architecture.md#Cross-Cutting Concerns, AR-07]

- **HD Settings Configuration:** The `major_incident_contacts` field is a comma-separated Small Text field in HD Settings. This follows the existing pattern used for other configuration fields (e.g., email routing). Parse with `[c.strip() for c in contacts.split(",") if c.strip()]` to handle spaces and empty entries.

- **Dependency on Story 1.6 (Related Ticket Linking):** This story depends on the `HD Related Ticket` child table being present on HD Ticket (implemented in Story 1.6). The `propagate_update` endpoint queries `HD Related Ticket` with filter `{"parent": ticket}`. If Story 1.6 is not yet merged, mock or stub the related tickets table in tests. [Source: epics.md#Story 1.8 AC, prd.md#FR-IM-05]

- **`propagate_update` Comment Mechanism:** The comment is appended to each ticket's `communications` child table. Check whether the existing HD Ticket model uses `frappe.get_doc().append("communications", {...})` or a custom `add_comment()` method — use whichever pattern Stories 1.4/1.5 (Internal Notes) established for adding ticket communications to stay consistent.

- **`depends_on` for Post-Incident Fields (Frappe pattern):** The `depends_on` attribute on DocType fields uses JavaScript expressions evaluated in the form context. The expression `eval:doc.is_major_incident && (doc.status=='Resolved'||doc.status=='Closed')` hides the fields unless both conditions are true. This is a pure Frappe DocType JSON feature — no custom JS required. [Source: Frappe Framework documentation]

- **Frontend Component Location (ADR-09):** `MajorIncidentBanner.vue` is explicitly listed in the architecture's shared component map at `desk/src/components/ticket/MajorIncidentBanner.vue`. The dashboard page is at `desk/src/pages/major-incidents/` (following the `pages/{domain}/` pattern). [Source: architecture.md#ADR-09]

- **`createListResource` for Dashboard (ADR-09):** The major incident dashboard uses `createListResource` from `frappe-ui` (not raw fetch/axios) to load the list of major incident tickets. This follows the established codebase pattern. [Source: architecture.md]

- **UX-DR-09:** The architecture and epics explicitly specify that the major incident banner is "displayed prominently on ticket view with elapsed time and linked ticket count". The red color scheme (`bg-red-50`, `border-red-200`, `text-red-800`) follows the ITIL major incident visual convention. [Source: epics.md#UX-DR-09]

### Files to Create / Modify

| Action | Path | Notes |
|--------|------|-------|
| Modify | `helpdesk/helpdesk/doctype/hd_ticket/hd_ticket.json` | Add 5 new fields (is_major_incident, major_incident_flagged_at, root_cause_summary, corrective_actions, prevention_measures) |
| Modify | `helpdesk/helpdesk/doctype/hd_settings/hd_settings.json` | Add major_incident_contacts field |
| Create | `helpdesk/api/incident.py` | flag_major_incident, propagate_update, get_major_incident_summary, _send_major_incident_notifications |
| Create | `helpdesk/templates/major_incident_alert.html` | Email template for escalation notifications |
| Create | `helpdesk/patches/v1_phase1/add_major_incident_fields_to_ticket.py` | Migration patch for HD Ticket |
| Create | `helpdesk/patches/v1_phase1/add_major_incident_contacts_to_settings.py` | Migration patch for HD Settings |
| Modify | `patches.txt` | Register both migration patches |
| Create | `desk/src/components/ticket/MajorIncidentBanner.vue` | Red banner with elapsed time, linked count, propagate update action |
| Create | `desk/src/pages/major-incidents/MajorIncidentDashboard.vue` | Manager dashboard listing all major incidents |
| Create | `desk/src/pages/major-incidents/MajorIncidentCard.vue` | Card component for each major incident |
| Modify | `desk/src/pages/ticket/{TicketDetail or index}.vue` | Register MajorIncidentBanner + is_major_incident confirmation dialog |
| Modify | `desk/src/router/index.ts` (or routes file) | Add /helpdesk/major-incidents route |
| Modify | `desk/src/components/Sidebar.vue` (or nav file) | Add navigation link to major incidents dashboard |
| Create | `helpdesk/helpdesk/doctype/hd_ticket/test_hd_ticket_major_incident.py` | Unit tests |

### Testing Standards

- Use `frappe.tests.utils.FrappeTestCase` as the base class (consistent with Stories 1.4–1.7 patterns).
- All test fixtures created in `setUp` must be cleaned up via `frappe.db.rollback()` in `tearDown`.
- Use `frappe.set_user()` to simulate different user roles; always restore to `"Administrator"` in `tearDown`.
- The `_send_major_incident_notifications` background job function should NOT be directly tested in unit tests — it uses `frappe.sendmail` and `frappe.realtime.publish` which require real infrastructure. Test `flag_major_incident` only up to the `frappe.enqueue()` call; the notifications test is integration-level.
- The `propagate_update` test MUST create actual `HD Related Ticket` child table entries (via `doc.append("related_tickets", {...})`) — do NOT mock the related ticket relationship.
- Minimum **80% line coverage** on all new backend Python code (NFR-M-01).

### Constraints

- `is_major_incident` can only be set to `1` via the `flag_major_incident` API endpoint — NOT by direct DocType save without the confirmation dialog. The checkbox in the UI must be intercepted with a confirmation dialog before calling the API (AC #1).
- The `major_incident_flagged_at` field is `read_only: 1` in the DocType JSON — it is set server-side only by `flag_major_incident`. Never allow client-side writes to this field.
- Post-incident review fields (`root_cause_summary`, `corrective_actions`, `prevention_measures`) are NOT required — they use `depends_on` for conditional visibility only. Do NOT add `reqd: 1` to these fields.
- The `_send_major_incident_notifications` function must log a warning (not raise) if `major_incident_contacts` is empty. Never let a missing configuration field crash the major incident flagging flow.
- All user-facing strings must use `frappe._()` in Python and `__()` in Vue/TypeScript for i18n compatibility.
- The elapsed time component must clean up its `setInterval` in `onUnmounted` to prevent memory leaks in the SPA.
- Do NOT implement "unflag" (reverting `is_major_incident` to 0) in this story. Once a ticket is flagged as a major incident, it stays flagged. Unflag capability can be added in a follow-up story if needed.

### Project Structure Notes

- **`patches/v1_phase1/__init__.py`:** This file may already exist from Stories 1.1–1.7. Check before creating — do not overwrite if it exists.
- **`helpdesk/api/incident.py`:** This is a new module, explicitly listed in architecture.md#ADR-08. Verify `helpdesk/api/` directory exists (it should, from prior stories). No registration in `__init__.py` is needed.
- **HD Related Ticket child table:** This is the child DocType created in Story 1.6. The field on HD Ticket that holds it is likely `related_tickets`. Confirm the exact field name by checking `hd_ticket.json` after Story 1.6 is merged. If the field name differs, update the `propagate_update` and `get_major_incident_summary` queries accordingly.
- **Ticket detail page structure:** Inspect where Stories 1.4–1.7 added their components (InternalNote, RelatedTickets, TimeTracker) to understand the ticket detail layout. Place `MajorIncidentBanner` above the conversation thread — it should be among the first visible elements on the ticket view.
- **Router registration:** Follow the existing pattern in the router file. The route `/helpdesk/major-incidents` should use lazy loading (`() => import(...)`) consistent with other routes for code-splitting.

### References

- FR-IM-05 (Major incident flag, expedited workflow, management notification, linked ticket updates, post-incident review): [Source: _bmad-output/planning-artifacts/prd.md#FR-IM-05]
- Story 1.8 AC (from Epics): [Source: _bmad-output/planning-artifacts/epics.md#Story 1.8]
- UX-DR-09 (Major incident banner with elapsed time and linked ticket count): [Source: _bmad-output/planning-artifacts/epics.md#UX-DR-09]
- ADR-01 (Extend HD Ticket rather than separate DocTypes): [Source: _bmad-output/planning-artifacts/architecture.md#ADR-01]
- ADR-08 (`helpdesk/api/incident.py` API module mapping): [Source: _bmad-output/planning-artifacts/architecture.md#ADR-08]
- ADR-09 (`desk/src/components/ticket/MajorIncidentBanner.vue` component location): [Source: _bmad-output/planning-artifacts/architecture.md#ADR-09]
- ADR-12 (Background job architecture — queue="short" for notifications): [Source: _bmad-output/planning-artifacts/architecture.md#ADR-12]
- AR-02 (HD prefix naming, standard Frappe DocType structure): [Source: _bmad-output/planning-artifacts/epics.md#AR-02]
- AR-04 (New fields via DocType JSON, not Custom Fields): [Source: _bmad-output/planning-artifacts/epics.md#AR-04]
- AR-05 (Migration patches in `helpdesk/patches/v1_phase1/`): [Source: _bmad-output/planning-artifacts/epics.md#AR-05]
- AR-07 (Socket.IO room naming: `agent:{email}`): [Source: _bmad-output/planning-artifacts/epics.md#AR-07]
- NFR-M-01 (80% unit test coverage on all new backend code): [Source: _bmad-output/planning-artifacts/epics.md#Non-Functional Requirements]
- NFR-M-02 (All new DocTypes accessible via REST API): [Source: _bmad-output/planning-artifacts/epics.md#Non-Functional Requirements]
- NFR-U-04 (WCAG 2.1 AA for all new UI components): [Source: _bmad-output/planning-artifacts/epics.md#Non-Functional Requirements]
- Story 1.6 dependency (HD Related Ticket child table used by propagate_update): [Source: _bmad-output/planning-artifacts/epics.md#Story 1.6]
- Story 1.1 dependency (HD Settings itil_mode_enabled, extended for major_incident_contacts): [Source: _bmad-output/planning-artifacts/epics.md#Story 1.1]

## Dev Agent Record

### Agent Model Used

Claude Sonnet 4.5 (create-story workflow)

### Debug Log References

_None — story creation phase_

### Completion Notes List

_To be filled by implementing dev agent_

### File List

_To be filled by implementing dev agent upon completion_
