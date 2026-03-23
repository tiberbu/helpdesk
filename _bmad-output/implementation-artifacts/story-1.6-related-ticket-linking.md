# Story 1.6: Related Ticket Linking

Status: ready-for-dev

## Story

As a support agent,
I want to link related tickets together,
so that patterns are visible and updates can propagate between related issues.

## Acceptance Criteria

1. **[Link Ticket — Bidirectional "Related to"]** Given an agent is viewing Ticket A, when they click "Link Ticket" in the ticket sidebar and select Ticket B with link type "Related to", then:
   - Ticket B appears in Ticket A's "Related Tickets" sidebar panel with the link type label "Related to"
   - Ticket A appears in Ticket B's "Related Tickets" sidebar panel with the inverse label "Related to" (bidirectional — AC mirrors itself)
   - The link is stored as an `HD Related Ticket` child record on both Ticket A and Ticket B

2. **[Link Ticket — Bidirectional "Caused by"]** Given an agent links Ticket A to Ticket B with type "Caused by", when saved, then:
   - Ticket B appears in Ticket A's Related Tickets panel as "Caused by [Ticket B]"
   - Ticket A appears in Ticket B's Related Tickets panel as "Caused [Ticket A]" (inverse direction)
   - The backend `link_tickets` API creates both child records atomically (within the same DB transaction)

3. **[Link Ticket — "Duplicate of" with Auto-Close]** Given an agent links Ticket A to Ticket B with type "Duplicate of", when the link is saved, then:
   - Ticket A is automatically closed (status set to "Duplicate" or mapped to the site's "Resolved" equivalent)
   - A system comment is automatically added to Ticket A: `"Closed as duplicate of [Ticket B link]"` where `[Ticket B link]` is a clickable hyperlink to Ticket B
   - Ticket B appears in Ticket A's Related Tickets panel as "Duplicate of [Ticket B]"
   - Ticket A appears in Ticket B's Related Tickets panel as "Duplicate [Ticket A]" (inverse)
   - The auto-close and comment happen atomically in the same backend transaction as the link creation

4. **[Link Types — Required Selection]** Given an agent opens the "Link Ticket" dialog, when they initiate a link, then:
   - Exactly three link types are available in the type selector: "Related to", "Caused by", "Duplicate of"
   - The type field is required — the dialog's "Save" / "Link" button remains disabled until a link type is selected AND a target ticket is chosen
   - Selecting a type shows a brief tooltip or helper text describing the semantic meaning (e.g., "Duplicate of: marks this ticket as a duplicate and auto-closes it")

5. **[Link Ticket — Ticket Search / Selection]** Given the "Link Ticket" dialog is open, when the agent types in the ticket search field, then:
   - A debounced (200ms) search returns matching HD Ticket records by ticket subject or ticket ID (name)
   - The dropdown shows: ticket ID, subject, status, and assigned agent for each result (up to 10 results)
   - The agent cannot link a ticket to itself (self-link is rejected with a validation error)
   - The agent cannot create a duplicate link between two tickets that already have an existing link (any type) — a validation error is shown

6. **[Related Tickets Sidebar Panel — Display]** Given one or more related ticket links exist on a ticket, when an agent views the ticket in the agent workspace, then:
   - A "Related Tickets" section is visible in the ticket sidebar (implemented as `RelatedTickets.vue` per ADR-09)
   - Each related ticket is displayed as a row showing: ticket ID (clickable link), subject (truncated to 60 chars), link type badge, and status badge
   - Clicking the ticket ID navigates to that ticket's detail page via Vue Router
   - If there are no related tickets, the panel shows an empty state with a "Link Ticket" button

7. **[Related Tickets Sidebar Panel — Unlink Action]** Given an agent is viewing the Related Tickets panel, when they click the "Unlink" (remove) icon on a related ticket row, then:
   - A confirmation dialog appears: "Remove link to [Ticket ID]? This will also remove the reverse link."
   - On confirmation, both the HD Related Ticket child record on the current ticket AND the corresponding reverse record on the linked ticket are deleted atomically
   - The panel refreshes to reflect the removed link (optimistic UI update)

8. **[HD Related Ticket DocType — Schema]** Given the HD Related Ticket child DocType is created, when inspected, then it has these fields:
   - `ticket` (Link → HD Ticket, required): the linked ticket
   - `link_type` (Select, required): options "Related to" | "Caused by" | "Duplicate of"
   - `linked_by` (Link → User, read-only): agent who created the link
   - `linked_on` (Datetime, read-only): timestamp of link creation
   - The DocType is a child table (is_child_table = 1) with parent DocType HD Ticket
   - Field `related_tickets` (Table → HD Related Ticket) is added to HD Ticket DocType JSON

9. **[Bidirectional Logic — Backend Enforcement]** Given the `link_tickets` API is called with `(ticket_a, ticket_b, link_type)`, then:
   - The function creates one `HD Related Ticket` child record on Ticket A with `ticket = B` and the specified `link_type`
   - The function creates one `HD Related Ticket` child record on Ticket B with `ticket = A` and the inverse `link_type` (see inverse mapping in Dev Notes)
   - Both records are created in a single Frappe `db.commit()` to prevent half-linked states
   - The function is idempotent: if a link between A and B already exists (any direction), it raises a `frappe.ValidationError` rather than creating a duplicate

10. **[Auto-Close for Duplicate — Detail]** Given `link_type == "Duplicate of"` is passed to `link_tickets`, then:
    - Ticket A's status is set to the "Duplicate" status option (add if not present) OR the closest available closed status ("Resolved") per site configuration
    - A `Communication` record (type "Comment", is_internal=0, public comment) is inserted on Ticket A with content: `"This ticket has been closed as a duplicate of <a href='/helpdesk/tickets/{B_name}'>{B_subject} ({B_name})</a>."`
    - The auto-close only applies to Ticket A (the ticket being marked as duplicate), NOT to Ticket B
    - The agent cannot manually re-open a "Duplicate"-status ticket without removing the duplicate link first (optional: soft enforcement via UI warning only)

11. **[Permission Check]** Given any agent attempts to use the `link_tickets` API, then:
    - The caller must have write permission on both HD Ticket records (agent role or above)
    - Unauthenticated or Customer-role callers receive a `frappe.PermissionError`
    - The `link_tickets` function is decorated with `@frappe.whitelist()` and internally calls `frappe.has_permission("HD Ticket", "write", doc=ticket_a_doc, throw=True)`

12. **[Unit Tests — Linking Logic and Bidirectionality]** Given the implementation is complete, when the test suite runs, then unit tests exist covering:
    - Creating a "Related to" link results in two HD Related Ticket records (one on each ticket)
    - Creating a "Caused by" link results in the correct inverse link type on the remote ticket
    - Creating a "Duplicate of" link auto-closes Ticket A and adds the system comment
    - Attempting to link a ticket to itself raises `frappe.ValidationError`
    - Attempting to create a duplicate link raises `frappe.ValidationError`
    - Unlinking removes both the forward and reverse `HD Related Ticket` child records
    - Permission check: non-Agent caller to `link_tickets` raises `frappe.PermissionError`
    - Minimum 80% line coverage on all new backend Python code (NFR-M-01)

## Tasks / Subtasks

- [ ] Task 1 — Create `HD Related Ticket` child DocType (AC: #8)
  - [ ] 1.1 Create DocType JSON at `helpdesk/helpdesk/doctype/hd_related_ticket/hd_related_ticket.json`:
    ```json
    {
      "name": "HD Related Ticket",
      "doctype": "DocType",
      "module": "Helpdesk",
      "is_child_table": 1,
      "istable": 1,
      "fields": [
        {
          "fieldname": "ticket",
          "fieldtype": "Link",
          "label": "Ticket",
          "options": "HD Ticket",
          "reqd": 1,
          "in_list_view": 1
        },
        {
          "fieldname": "link_type",
          "fieldtype": "Select",
          "label": "Link Type",
          "options": "Related to\nCaused by\nDuplicate of",
          "reqd": 1,
          "in_list_view": 1
        },
        {
          "fieldname": "linked_by",
          "fieldtype": "Link",
          "label": "Linked By",
          "options": "User",
          "read_only": 1,
          "default": "__user"
        },
        {
          "fieldname": "linked_on",
          "fieldtype": "Datetime",
          "label": "Linked On",
          "read_only": 1,
          "default": "Now"
        }
      ],
      "permissions": [
        {"role": "HD Agent", "read": 1, "write": 1, "create": 1, "delete": 1},
        {"role": "System Manager", "read": 1, "write": 1, "create": 1, "delete": 1}
      ]
    }
    ```
  - [ ] 1.2 Create `helpdesk/helpdesk/doctype/hd_related_ticket/__init__.py` (empty).
  - [ ] 1.3 Create `helpdesk/helpdesk/doctype/hd_related_ticket/hd_related_ticket.py`:
    ```python
    # Copyright (c) 2026, Frappe Technologies Pvt. Ltd. and contributors
    # For license information, please see license.txt

    import frappe
    from frappe.model.document import Document


    class HDRelatedTicket(Document):
        pass
    ```
  - [ ] 1.4 Run `bench migrate` to create the database table for HD Related Ticket.

- [ ] Task 2 — Add `related_tickets` Table field to HD Ticket DocType JSON (AC: #8)
  - [ ] 2.1 Open `helpdesk/helpdesk/doctype/hd_ticket/hd_ticket.json`. Locate the `fields` array and append the following field definition (place it near other sidebar-related fields):
    ```json
    {
      "fieldname": "related_tickets",
      "fieldtype": "Table",
      "label": "Related Tickets",
      "options": "HD Related Ticket",
      "read_only": 1
    }
    ```
    > Note: `read_only: 1` because modifications happen through the dedicated `link_tickets` / `unlink_tickets` API methods, not via the standard Frappe child table form UI.
  - [ ] 2.2 Run `bench migrate` to apply the schema change to HD Ticket.

- [ ] Task 3 — Implement `link_tickets` and `unlink_tickets` API (AC: #9, #10, #11, #5)
  - [ ] 3.1 In `helpdesk/api/incident.py` (create the file if it does not exist), implement:
    ```python
    import frappe
    from frappe import _
    from frappe.utils import now_datetime


    # Inverse link type mapping (what Ticket B sees when Ticket A links to it)
    INVERSE_LINK_TYPE = {
        "Related to": "Related to",   # symmetric
        "Caused by": "Causes",         # A "Caused by" B → B "Causes" A
        "Duplicate of": "Duplicated by",  # A "Duplicate of" B → B "Duplicated by" A
    }


    @frappe.whitelist()
    def link_tickets(ticket_a: str, ticket_b: str, link_type: str) -> dict:
        """
        Create a bidirectional link between ticket_a and ticket_b.
        For "Duplicate of" link type, auto-closes ticket_a.

        Returns: {"success": True, "link_a": <child_name>, "link_b": <child_name>}
        """
        # Permission check
        frappe.has_permission("HD Ticket", "write", doc=ticket_a, throw=True)
        frappe.has_permission("HD Ticket", "write", doc=ticket_b, throw=True)

        # Validate inputs
        if ticket_a == ticket_b:
            frappe.throw(_("Cannot link a ticket to itself."), frappe.ValidationError)

        valid_types = ["Related to", "Caused by", "Duplicate of"]
        if link_type not in valid_types:
            frappe.throw(
                _("Invalid link type '{0}'. Must be one of: {1}").format(
                    link_type, ", ".join(valid_types)
                ),
                frappe.ValidationError,
            )

        # Check for existing link (either direction)
        _assert_no_existing_link(ticket_a, ticket_b)

        doc_a = frappe.get_doc("HD Ticket", ticket_a)
        doc_b = frappe.get_doc("HD Ticket", ticket_b)

        now = now_datetime()
        user = frappe.session.user

        # Create forward link on Ticket A
        doc_a.append("related_tickets", {
            "ticket": ticket_b,
            "link_type": link_type,
            "linked_by": user,
            "linked_on": now,
        })
        doc_a.flags.ignore_permissions = True
        doc_a.save()

        # Create reverse link on Ticket B
        inverse = INVERSE_LINK_TYPE.get(link_type, link_type)
        doc_b.append("related_tickets", {
            "ticket": ticket_a,
            "link_type": inverse,
            "linked_by": user,
            "linked_on": now,
        })
        doc_b.flags.ignore_permissions = True
        doc_b.save()

        # Auto-close for "Duplicate of"
        if link_type == "Duplicate of":
            _auto_close_duplicate(doc_a, doc_b)

        frappe.db.commit()

        return {"success": True}


    @frappe.whitelist()
    def unlink_tickets(ticket_a: str, ticket_b: str) -> dict:
        """
        Remove all links between ticket_a and ticket_b (both directions).
        """
        frappe.has_permission("HD Ticket", "write", doc=ticket_a, throw=True)

        doc_a = frappe.get_doc("HD Ticket", ticket_a)
        doc_b = frappe.get_doc("HD Ticket", ticket_b)

        # Remove forward links from A → B
        doc_a.related_tickets = [
            r for r in doc_a.related_tickets if r.ticket != ticket_b
        ]
        doc_a.flags.ignore_permissions = True
        doc_a.save()

        # Remove reverse links from B → A
        doc_b.related_tickets = [
            r for r in doc_b.related_tickets if r.ticket != ticket_a
        ]
        doc_b.flags.ignore_permissions = True
        doc_b.save()

        frappe.db.commit()

        return {"success": True}


    def _assert_no_existing_link(ticket_a: str, ticket_b: str) -> None:
        """Raise ValidationError if a link already exists between the two tickets."""
        exists = frappe.db.exists(
            "HD Related Ticket",
            {"parent": ticket_a, "ticket": ticket_b},
        ) or frappe.db.exists(
            "HD Related Ticket",
            {"parent": ticket_b, "ticket": ticket_a},
        )
        if exists:
            frappe.throw(
                _("A link between {0} and {1} already exists.").format(ticket_a, ticket_b),
                frappe.ValidationError,
            )


    def _auto_close_duplicate(doc_a, doc_b) -> None:
        """Auto-close Ticket A as a duplicate of Ticket B and add a system comment."""
        # Determine duplicate status — prefer "Duplicate" option if it exists
        ticket_meta = frappe.get_meta("HD Ticket")
        status_field = ticket_meta.get_field("status")
        available_statuses = []
        if status_field and status_field.options:
            available_statuses = [s.strip() for s in status_field.options.split("\n") if s.strip()]

        target_status = "Duplicate" if "Duplicate" in available_statuses else "Resolved"
        doc_a.status = target_status
        doc_a.flags.ignore_permissions = True
        doc_a.save()

        # Add public system comment on Ticket A
        b_link = (
            f"<a href='/helpdesk/tickets/{doc_b.name}'>"
            f"{frappe.utils.escape_html(doc_b.subject)} ({doc_b.name})"
            f"</a>"
        )
        comment = frappe.get_doc({
            "doctype": "Communication",
            "communication_type": "Comment",
            "comment_type": "Info",
            "reference_doctype": "HD Ticket",
            "reference_name": doc_a.name,
            "content": _("This ticket has been closed as a duplicate of {0}.").format(b_link),
            "sender": frappe.session.user,
            "sent_or_received": "Sent",
        })
        comment.insert(ignore_permissions=True)
    ```
  - [ ] 3.2 Add `helpdesk/api/incident.py` to `helpdesk/api/__init__.py` imports if needed (check if the api package uses explicit imports).
  - [ ] 3.3 Verify the `INVERSE_LINK_TYPE` mapping covers all three types. Note: "Caused by" and "Duplicate of" require additional Select options on the child table ("Causes", "Duplicated by") — add these to the HD Related Ticket DocType JSON in Task 1.1.
    > **Important:** Extend the `link_type` Select options in `hd_related_ticket.json` to include inverse types used by Ticket B:
    > ```
    > "options": "Related to\nCaused by\nCauses\nDuplicate of\nDuplicated by"
    > ```

- [ ] Task 4 — Implement `RelatedTickets.vue` sidebar panel component (AC: #6, #7, #4, #5)
  - [ ] 4.1 Create `desk/src/components/ticket/RelatedTickets.vue` — the sidebar panel:
    ```vue
    <template>
      <div class="related-tickets-panel">
        <div class="flex items-center justify-between mb-3">
          <h3 class="text-sm font-semibold text-gray-700">
            {{ __('Related Tickets') }}
            <span v-if="relatedTickets.length" class="ml-1 text-gray-400 font-normal">
              ({{ relatedTickets.length }})
            </span>
          </h3>
          <Button size="sm" variant="ghost" @click="openLinkDialog" :label="__('Link Ticket')">
            <template #prefix><LucidePlus class="w-3 h-3" /></template>
          </Button>
        </div>

        <!-- Empty State -->
        <div v-if="!relatedTickets.length" class="text-center py-4 text-gray-400 text-sm">
          <LucideLink2 class="w-5 h-5 mx-auto mb-1 opacity-50" />
          <p>{{ __('No related tickets') }}</p>
          <Button size="sm" variant="outline" class="mt-2" @click="openLinkDialog">
            {{ __('Link a ticket') }}
          </Button>
        </div>

        <!-- Related Ticket Rows -->
        <ul v-else class="space-y-2">
          <li
            v-for="link in relatedTickets"
            :key="link.name"
            class="flex items-start justify-between gap-2 rounded border border-gray-100 bg-gray-50 px-3 py-2 hover:bg-gray-100 transition-colors"
          >
            <div class="min-w-0 flex-1">
              <a
                :href="`/helpdesk/tickets/${link.ticket}`"
                class="text-xs font-medium text-blue-600 hover:underline"
                @click.prevent="navigateToTicket(link.ticket)"
              >
                {{ link.ticket }}
              </a>
              <p class="text-xs text-gray-600 truncate mt-0.5" :title="link.ticket_subject">
                {{ link.ticket_subject || __('(No subject)') }}
              </p>
              <div class="flex gap-1 mt-1">
                <Badge :label="link.link_type" theme="blue" size="sm" />
                <Badge :label="link.ticket_status" :theme="statusTheme(link.ticket_status)" size="sm" />
              </div>
            </div>
            <button
              class="text-gray-400 hover:text-red-500 transition-colors flex-shrink-0 mt-0.5"
              :title="__('Remove link')"
              :aria-label="__('Remove link to {0}', [link.ticket])"
              @click="confirmUnlink(link)"
            >
              <LucideX class="w-3.5 h-3.5" />
            </button>
          </li>
        </ul>

        <!-- Link Ticket Dialog -->
        <LinkTicketDialog
          v-if="showLinkDialog"
          :current-ticket="ticketId"
          @linked="onLinked"
          @close="showLinkDialog = false"
        />

        <!-- Unlink Confirmation Dialog -->
        <Dialog
          v-if="unlinkTarget"
          :options="{
            title: __('Remove Link'),
            message: __('Remove link to {0}? This will also remove the reverse link.', [unlinkTarget.ticket]),
            actions: [
              { label: __('Cancel'), variant: 'subtle', onClick: () => unlinkTarget = null },
              { label: __('Remove'), variant: 'solid', theme: 'red', onClick: doUnlink },
            ],
          }"
          @close="unlinkTarget = null"
        />
      </div>
    </template>

    <script setup lang="ts">
    import { ref, computed } from 'vue'
    import { useRouter } from 'vue-router'
    import { createResource, Button, Badge, Dialog } from 'frappe-ui'
    import { LucidePlus, LucideLink2, LucideX } from 'lucide-vue-next'
    import LinkTicketDialog from './LinkTicketDialog.vue'

    const props = defineProps<{ ticketId: string }>()
    const router = useRouter()

    const showLinkDialog = ref(false)
    const unlinkTarget = ref<{ name: string; ticket: string } | null>(null)

    // Fetch related tickets for this ticket
    const relatedTicketsResource = createResource({
      url: 'frappe.client.get',
      params: { doctype: 'HD Ticket', name: props.ticketId, fields: ['related_tickets'] },
      auto: true,
    })

    const relatedTickets = computed(() =>
      relatedTicketsResource.data?.related_tickets ?? []
    )

    function statusTheme(status: string) {
      const map: Record<string, string> = {
        Open: 'green', Replied: 'blue', Resolved: 'gray',
        Closed: 'gray', Duplicate: 'orange', 'On Hold': 'yellow',
      }
      return map[status] ?? 'gray'
    }

    function openLinkDialog() { showLinkDialog.value = true }

    function navigateToTicket(ticketId: string) {
      router.push(`/tickets/${ticketId}`)
    }

    function onLinked() {
      showLinkDialog.value = false
      relatedTicketsResource.reload()
    }

    function confirmUnlink(link: { name: string; ticket: string }) {
      unlinkTarget.value = link
    }

    const unlinkResource = createResource({
      url: 'helpdesk.api.incident.unlink_tickets',
      onSuccess() {
        unlinkTarget.value = null
        relatedTicketsResource.reload()
      },
    })

    function doUnlink() {
      if (!unlinkTarget.value) return
      unlinkResource.submit({
        ticket_a: props.ticketId,
        ticket_b: unlinkTarget.value.ticket,
      })
    }
    </script>
    ```
  - [ ] 4.2 Create `desk/src/components/ticket/LinkTicketDialog.vue` — the search-and-link modal:
    ```vue
    <template>
      <Dialog
        :options="{ title: __('Link a Ticket'), size: 'md' }"
        v-model="show"
        @close="emit('close')"
      >
        <template #body-content>
          <div class="space-y-4">
            <!-- Ticket Search -->
            <FormControl
              :label="__('Search Ticket')"
              type="autocomplete"
              :placeholder="__('Search by ID or subject...')"
              v-model="selectedTicket"
              :options="ticketOptions"
              @update:query="onSearchQuery"
            />

            <!-- Link Type -->
            <FormControl
              :label="__('Link Type')"
              type="select"
              v-model="selectedLinkType"
              :options="linkTypeOptions"
            />
            <p v-if="linkTypeDescription" class="text-xs text-gray-500 -mt-2">
              {{ linkTypeDescription }}
            </p>

            <!-- Error -->
            <p v-if="errorMessage" class="text-sm text-red-600">{{ errorMessage }}</p>
          </div>
        </template>
        <template #actions>
          <Button variant="subtle" @click="emit('close')">{{ __('Cancel') }}</Button>
          <Button
            variant="solid"
            :disabled="!selectedTicket || !selectedLinkType || linkResource.loading"
            :loading="linkResource.loading"
            @click="doLink"
          >
            {{ __('Link Ticket') }}
          </Button>
        </template>
      </Dialog>
    </template>

    <script setup lang="ts">
    import { ref, computed } from 'vue'
    import { createResource, Button, Dialog, FormControl } from 'frappe-ui'
    import { useDebounceFn } from '@vueuse/core'

    const props = defineProps<{ currentTicket: string }>()
    const emit = defineEmits<{ linked: []; close: [] }>()

    const show = ref(true)
    const selectedTicket = ref('')
    const selectedLinkType = ref('')
    const errorMessage = ref('')
    const ticketOptions = ref<{ label: string; value: string }[]>([])

    const linkTypeOptions = [
      { label: __('Related to'), value: 'Related to' },
      { label: __('Caused by'), value: 'Caused by' },
      { label: __('Duplicate of'), value: 'Duplicate of' },
    ]

    const LINK_TYPE_DESCRIPTIONS: Record<string, string> = {
      'Related to': __('This ticket is related to the selected ticket (no status change).'),
      'Caused by': __('This ticket was caused by the selected ticket.'),
      'Duplicate of': __('This ticket is a duplicate — it will be auto-closed when linked.'),
    }

    const linkTypeDescription = computed(
      () => LINK_TYPE_DESCRIPTIONS[selectedLinkType.value] ?? ''
    )

    const searchResource = createResource({
      url: 'frappe.client.get_list',
      onSuccess(data: any[]) {
        ticketOptions.value = data.map((t) => ({
          value: t.name,
          label: `${t.name} — ${t.subject ?? ''}`,
          description: t.status,
        }))
      },
    })

    const onSearchQuery = useDebounceFn((query: string) => {
      if (!query || query.length < 2) return
      searchResource.submit({
        doctype: 'HD Ticket',
        filters: [['name', '!=', props.currentTicket]],
        or_filters: [
          ['name', 'like', `%${query}%`],
          ['subject', 'like', `%${query}%`],
        ],
        fields: ['name', 'subject', 'status'],
        limit: 10,
      })
    }, 200)

    const linkResource = createResource({
      url: 'helpdesk.api.incident.link_tickets',
      onSuccess() { emit('linked') },
      onError(err: any) {
        errorMessage.value = err?.messages?.[0] ?? __('Failed to link tickets.')
      },
    })

    function doLink() {
      errorMessage.value = ''
      linkResource.submit({
        ticket_a: props.currentTicket,
        ticket_b: selectedTicket.value,
        link_type: selectedLinkType.value,
      })
    }
    </script>
    ```
  - [ ] 4.3 Register `RelatedTickets.vue` in the ticket detail sidebar. Locate the ticket sidebar composition (likely `desk/src/pages/ticket/TicketSidebar.vue` or `desk/src/pages/ticket/index.vue`) and import + add `<RelatedTickets :ticket-id="ticket.name" />` in the appropriate sidebar section (alongside Time Tracker, Internal Notes, etc.).
  - [ ] 4.4 Ensure `RelatedTickets.vue` and `LinkTicketDialog.vue` meet WCAG 2.1 AA requirements (NFR-U-04): `aria-label` on icon-only buttons, `role="list"` on the related ticket list, focus management on dialog open/close.

- [ ] Task 5 — Write unit tests for all link types and bidirectional behavior (AC: #12)
  - [ ] 5.1 Create `helpdesk/helpdesk/doctype/hd_related_ticket/test_hd_related_ticket.py`:
    ```python
    import frappe
    from frappe.tests.utils import FrappeTestCase
    from helpdesk.api.incident import link_tickets, unlink_tickets, _assert_no_existing_link


    class TestRelatedTicketLinking(FrappeTestCase):
        """Unit tests for Story 1.6: Related Ticket Linking."""

        def setUp(self):
            self.ticket_a = frappe.get_doc({
                "doctype": "HD Ticket",
                "subject": "Test Ticket A",
                "raised_by": "customer.a@test.com",
            }).insert(ignore_permissions=True)
            self.ticket_b = frappe.get_doc({
                "doctype": "HD Ticket",
                "subject": "Test Ticket B",
                "raised_by": "customer.b@test.com",
            }).insert(ignore_permissions=True)
            self.ticket_c = frappe.get_doc({
                "doctype": "HD Ticket",
                "subject": "Test Ticket C",
                "raised_by": "customer.c@test.com",
            }).insert(ignore_permissions=True)
            # Create test agent
            if not frappe.db.exists("User", "agent.test@test.com"):
                frappe.get_doc({
                    "doctype": "User",
                    "email": "agent.test@test.com",
                    "full_name": "Test Agent",
                    "first_name": "Test",
                    "send_welcome_email": 0,
                    "roles": [{"role": "HD Agent"}],
                }).insert(ignore_permissions=True)
            frappe.set_user("agent.test@test.com")

        def tearDown(self):
            frappe.set_user("Administrator")
            frappe.db.rollback()

        # ---- Bidirectionality Tests ----

        def test_related_to_creates_bidirectional_links(self):
            link_tickets(self.ticket_a.name, self.ticket_b.name, "Related to")
            a_links = frappe.get_all(
                "HD Related Ticket",
                filters={"parent": self.ticket_a.name, "ticket": self.ticket_b.name},
            )
            b_links = frappe.get_all(
                "HD Related Ticket",
                filters={"parent": self.ticket_b.name, "ticket": self.ticket_a.name},
            )
            self.assertEqual(len(a_links), 1, "Forward link not created on Ticket A")
            self.assertEqual(len(b_links), 1, "Reverse link not created on Ticket B")

        def test_caused_by_creates_correct_inverse(self):
            link_tickets(self.ticket_a.name, self.ticket_b.name, "Caused by")
            a_link = frappe.get_all(
                "HD Related Ticket",
                filters={"parent": self.ticket_a.name, "ticket": self.ticket_b.name},
                fields=["link_type"],
            )
            b_link = frappe.get_all(
                "HD Related Ticket",
                filters={"parent": self.ticket_b.name, "ticket": self.ticket_a.name},
                fields=["link_type"],
            )
            self.assertEqual(a_link[0]["link_type"], "Caused by")
            self.assertEqual(b_link[0]["link_type"], "Causes",
                             "Ticket B should show inverse 'Causes' link type")

        # ---- Duplicate of / Auto-Close Tests ----

        def test_duplicate_of_auto_closes_ticket_a(self):
            link_tickets(self.ticket_a.name, self.ticket_b.name, "Duplicate of")
            ticket_a_doc = frappe.get_doc("HD Ticket", self.ticket_a.name)
            self.assertIn(
                ticket_a_doc.status,
                ["Duplicate", "Resolved"],
                "Ticket A should be auto-closed as Duplicate or Resolved",
            )

        def test_duplicate_of_adds_system_comment(self):
            link_tickets(self.ticket_a.name, self.ticket_b.name, "Duplicate of")
            comments = frappe.get_all(
                "Communication",
                filters={
                    "reference_doctype": "HD Ticket",
                    "reference_name": self.ticket_a.name,
                    "communication_type": "Comment",
                },
                fields=["content"],
            )
            self.assertTrue(len(comments) > 0, "System comment should be added to Ticket A")
            self.assertIn(self.ticket_b.name, comments[0]["content"],
                          "Comment should mention the duplicate target ticket ID")

        def test_duplicate_of_does_not_close_ticket_b(self):
            original_status_b = self.ticket_b.status
            link_tickets(self.ticket_a.name, self.ticket_b.name, "Duplicate of")
            ticket_b_doc = frappe.get_doc("HD Ticket", self.ticket_b.name)
            self.assertEqual(ticket_b_doc.status, original_status_b,
                             "Ticket B status must not change when Ticket A is marked duplicate of it")

        # ---- Validation Tests ----

        def test_self_link_raises_validation_error(self):
            with self.assertRaises(frappe.ValidationError):
                link_tickets(self.ticket_a.name, self.ticket_a.name, "Related to")

        def test_duplicate_link_raises_validation_error(self):
            link_tickets(self.ticket_a.name, self.ticket_b.name, "Related to")
            with self.assertRaises(frappe.ValidationError):
                link_tickets(self.ticket_a.name, self.ticket_b.name, "Caused by")

        def test_invalid_link_type_raises_validation_error(self):
            with self.assertRaises(frappe.ValidationError):
                link_tickets(self.ticket_a.name, self.ticket_b.name, "InvalidType")

        # ---- Unlink Tests ----

        def test_unlink_removes_both_directions(self):
            link_tickets(self.ticket_a.name, self.ticket_b.name, "Related to")
            unlink_tickets(self.ticket_a.name, self.ticket_b.name)
            a_links = frappe.get_all(
                "HD Related Ticket",
                filters={"parent": self.ticket_a.name, "ticket": self.ticket_b.name},
            )
            b_links = frappe.get_all(
                "HD Related Ticket",
                filters={"parent": self.ticket_b.name, "ticket": self.ticket_a.name},
            )
            self.assertEqual(len(a_links), 0, "Forward link should be removed")
            self.assertEqual(len(b_links), 0, "Reverse link should be removed")

        # ---- Permission Tests ----

        def test_customer_cannot_link_tickets(self):
            frappe.set_user("customer.a@test.com")
            with self.assertRaises(frappe.PermissionError):
                link_tickets(self.ticket_a.name, self.ticket_b.name, "Related to")
            frappe.set_user("agent.test@test.com")
    ```
  - [ ] 5.2 Run tests with:
    ```bash
    bench --site <site> run-tests --module helpdesk.helpdesk.doctype.hd_related_ticket.test_hd_related_ticket
    ```
  - [ ] 5.3 Ensure test coverage meets NFR-M-01 (≥80% line coverage on all new backend Python code).

- [ ] Task 6 — Add migration patch for existing installations (AC: #8)
  - [ ] 6.1 Create `helpdesk/patches/v1_phase1/create_hd_related_ticket.py`:
    ```python
    """
    Patch: Create HD Related Ticket DocType table and add related_tickets field to HD Ticket.
    Story: 1.6 — Related Ticket Linking
    """
    import frappe


    def execute():
        # Sync the new HD Related Ticket child table
        frappe.reload_doctype("HD Related Ticket", force=True)
        # Sync the modified HD Ticket (new related_tickets Table field)
        frappe.reload_doctype("HD Ticket", force=True)
    ```
  - [ ] 6.2 Register the patch in `patches.txt`:
    ```
    helpdesk.patches.v1_phase1.create_hd_related_ticket
    ```

## Dev Notes

### Architecture Patterns

- **DocType: HD Related Ticket (ADR-02):** The architecture explicitly defines `HD Related Ticket` as a new child table DocType with the relationship: `HD Ticket → related_tickets → HD Related Ticket (Table, child)`. This is the canonical pattern per ADR-02 ("New DocType Schema for Phase 1"). Do NOT implement linking via a standalone (non-child) DocType or via Custom Fields. [Source: architecture.md#ADR-02]

- **Extend HD Ticket Directly (ADR-01):** All new fields on HD Ticket (including `related_tickets`) are added directly to `hd_ticket.json`. Do NOT use Frappe Custom Fields. This is a firm requirement per ADR-01 and AR-04. [Source: architecture.md#ADR-01, epics.md#AR-04]

- **API Location (ADR-08):** The `link_tickets` and `unlink_tickets` functions belong in `helpdesk/api/incident.py`. The architecture already maps this module to: `flag_major_incident`, `link_tickets`, `propagate_update`. [Source: architecture.md#ADR-08]

- **Bidirectional Inverse Link Type Mapping:** The three user-facing link types have the following inverse semantics when the reverse record is created on Ticket B:
  ```
  Ticket A  →  (Forward)   →  Ticket B
  Ticket B  →  (Inverse)   →  Ticket A

  "Related to"   ↔  "Related to"     (symmetric)
  "Caused by"    →  "Causes"         (A was caused by B → B causes A)
  "Duplicate of" →  "Duplicated by"  (A is duplicate of B → B is duplicated by A)
  ```
  The `HD Related Ticket` `link_type` Select field must include all 5 values: `Related to`, `Caused by`, `Causes`, `Duplicate of`, `Duplicated by`. Only the first three are user-selectable in the UI dialog; the latter two are set programmatically as inverse links.

- **Frontend Component Location (ADR-09):** `RelatedTickets.vue` is explicitly listed in the architecture's shared component map at `desk/src/components/ticket/RelatedTickets.vue`. Do NOT place it elsewhere. The `LinkTicketDialog.vue` is a companion component in the same directory. [Source: architecture.md#ADR-09]

- **createResource for Data Fetching:** Follow the existing codebase pattern of `createResource` / `createListResource` from `frappe-ui` for all API calls in Vue components. Do NOT use raw `fetch` or `axios`. [Source: architecture.md — "createResource / createListResource for frontend data fetching"]

- **Frappe DB Transaction Safety:** The `link_tickets` function creates two child records (forward + reverse) and, for duplicates, updates a ticket status and inserts a Communication record. All must succeed or fail together. Use `frappe.db.commit()` at the end only after all operations succeed; rely on Frappe's implicit transaction rollback on exception for atomicity. Do NOT call `frappe.db.commit()` mid-function.

- **Auto-Close Status — "Duplicate":** The `_auto_close_duplicate` helper checks whether a "Duplicate" status option exists in the HD Ticket `status` field before using it. If not present, it falls back to "Resolved". To ensure "Duplicate" is available, add it to the HD Ticket `status` Select field options in `hd_ticket.json`. Inspect the current options list before modifying.

- **No Real-Time Events for Story 1.6:** Unlike Story 1.5 (@mentions), related ticket linking does NOT require real-time Socket.IO events. The sidebar refreshes via `createResource.reload()` after a link operation. Real-time propagation of link updates is a potential future enhancement, not a Phase 1 requirement.

- **Performance:** The `_assert_no_existing_link` function uses `frappe.db.exists()` which is an indexed lookup. Ensure `HD Related Ticket` has a composite index on `(parent, ticket)` — Frappe creates this automatically for child tables via the `in_list_view` configuration, but verify after migration.

- **WCAG 2.1 AA (NFR-U-04):** Icon-only buttons (the "X" unlink button) must have `aria-label` attributes. The related tickets list must use semantic HTML (`<ul>/<li>` or `role="list"`). The `LinkTicketDialog` must manage focus: move focus to the first interactive element when opened, and return focus to the trigger when closed.

### Files to Create / Modify

| Action | Path | Notes |
|--------|------|-------|
| Create | `helpdesk/helpdesk/doctype/hd_related_ticket/hd_related_ticket.json` | New child table DocType definition |
| Create | `helpdesk/helpdesk/doctype/hd_related_ticket/__init__.py` | Python package init |
| Create | `helpdesk/helpdesk/doctype/hd_related_ticket/hd_related_ticket.py` | DocType controller (minimal) |
| Create | `helpdesk/helpdesk/doctype/hd_related_ticket/test_hd_related_ticket.py` | Unit tests |
| Modify | `helpdesk/helpdesk/doctype/hd_ticket/hd_ticket.json` | Add `related_tickets` Table field and optionally "Duplicate" to status options |
| Create | `helpdesk/api/incident.py` | `link_tickets`, `unlink_tickets` API methods |
| Create | `helpdesk/patches/v1_phase1/create_hd_related_ticket.py` | Migration patch |
| Modify | `patches.txt` | Register the migration patch |
| Create | `desk/src/components/ticket/RelatedTickets.vue` | Sidebar panel component |
| Create | `desk/src/components/ticket/LinkTicketDialog.vue` | Link creation modal |
| Modify | `desk/src/pages/ticket/{TicketSidebar or TicketDetail}.vue` | Register RelatedTickets in sidebar |

### Testing Standards

- Use `frappe.tests.utils.FrappeTestCase` as base class (consistent with Story 1.4 / 1.5 patterns).
- All test fixtures created in `setUp` must be cleaned up in `tearDown` via `frappe.db.rollback()`.
- Test both forward and reverse `HD Related Ticket` child records — do NOT only assert on the initiating ticket.
- For the `_auto_close_duplicate` test, verify BOTH the status change AND the Communication record.
- The permission test (`test_customer_cannot_link_tickets`) must set `frappe.set_user` to a non-agent user and restore it in `tearDown`.
- Minimum **80% line coverage** on all new backend Python code (NFR-M-01).

### Constraints

- Do NOT implement related ticket linking via a separate non-child DocType (e.g., a standalone "HD Ticket Link" doctype with two Link fields). The architecture mandates a child table on HD Ticket. [Source: architecture.md#ADR-02]
- The "Duplicate of" auto-close must only affect the ticket being linked (Ticket A), never the target ticket (Ticket B).
- Do NOT expose `link_type` inverse values ("Causes", "Duplicated by") in the UI link type selector — only "Related to", "Caused by", "Duplicate of" are user-selectable.
- The `related_tickets` Table field on HD Ticket must be `read_only: 1` — all modifications must go through the `link_tickets` / `unlink_tickets` API to enforce bidirectionality and business rules.
- All user-facing strings must use `frappe._()` in Python and `__()` in Vue/TypeScript for i18n compatibility.

### Project Structure Notes

- **Dependencies — None (Self-contained):** Story 1.6 has no hard code dependencies on Stories 1.1–1.5. The `related_tickets` Table field is independent of the ITIL mode flag. However, Story 1.8 (Major Incident) depends on Story 1.6 — see `story-1.8` for the `is_major_incident` flag which builds on the related ticket infrastructure.
- **`helpdesk/api/incident.py`** is a new module. Confirm `helpdesk/api/__init__.py` exists (check other api modules like `ticket.py` — if the api directory is a flat module collection, no init changes are needed; if it is a package, ensure `incident` is importable).
- **`patches/v1_phase1/`:** Multiple stories in Phase 1 will add patches here. Create `helpdesk/patches/v1_phase1/__init__.py` if it does not already exist.
- **`hd_ticket.json` Status Field:** Before adding "Duplicate" as a status option, inspect the current options in `hd_ticket.json`. Common existing statuses: Open, Replied, Resolved, Closed, On Hold. Add "Duplicate" only if not already present. The `_auto_close_duplicate` helper handles graceful fallback to "Resolved" if "Duplicate" is absent.
- **Ticket sidebar wiring:** Inspect the existing ticket detail page to find where the sidebar components are composed (likely `desk/src/pages/ticket/TicketSidebar.vue` or `desk/src/pages/ticket/index.vue`). Look for where `TimeTracker.vue` or similar sidebar panels are registered — place `RelatedTickets` in the same area.

### References

- FR-IM-04 (Related incidents linking — bidirectional, link types, auto-close duplicates): [Source: _bmad-output/planning-artifacts/epics.md#FR-IM-04]
- Story 1.6 AC (from Epics): [Source: _bmad-output/planning-artifacts/epics.md#Story 1.6]
- ADR-01 (Extend HD Ticket, no separate DocTypes): [Source: _bmad-output/planning-artifacts/architecture.md#ADR-01]
- ADR-02 (HD Related Ticket child table in the 10 new DocTypes): [Source: _bmad-output/planning-artifacts/architecture.md#ADR-02]
- ADR-08 (API in `helpdesk/api/incident.py`): [Source: _bmad-output/planning-artifacts/architecture.md#ADR-08]
- ADR-09 (Frontend component at `desk/src/components/ticket/RelatedTickets.vue`): [Source: _bmad-output/planning-artifacts/architecture.md#ADR-09]
- AR-02 (HD prefix naming, standard Frappe DocType structure): [Source: _bmad-output/planning-artifacts/epics.md#AR-02]
- AR-04 (New fields via DocType JSON, not Custom Fields): [Source: _bmad-output/planning-artifacts/epics.md#AR-04]
- AR-05 (Migration patches in `helpdesk/patches/v1_phase1/`): [Source: _bmad-output/planning-artifacts/epics.md#AR-05]
- NFR-M-01 (80% unit test coverage): [Source: _bmad-output/planning-artifacts/epics.md#Non-Functional Requirements]
- NFR-M-02 (All new DocTypes accessible via REST API): [Source: _bmad-output/planning-artifacts/epics.md#Non-Functional Requirements]
- NFR-U-04 (WCAG 2.1 AA compliance for all new UI components): [Source: _bmad-output/planning-artifacts/epics.md#Non-Functional Requirements]
- Story 1.8 (Major Incident — depends on related_tickets from this story): [Source: _bmad-output/planning-artifacts/epics.md#Story 1.8]

## Dev Agent Record

### Agent Model Used

Claude Sonnet 4.5 (create-story workflow)

### Debug Log References

_None — story creation phase_

### Completion Notes List

_To be filled by implementing dev agent_

### File List

_To be filled by implementing dev agent upon completion_
