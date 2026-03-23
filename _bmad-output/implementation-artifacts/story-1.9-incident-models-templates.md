# Story 1.9: Incident Models / Templates

Status: done

## Story

As an administrator,
I want to create incident models with predefined fields,
so that common incident types are logged consistently.

## Acceptance Criteria

1. **[HD Incident Model DocType — Schema]** Given the HD Incident Model DocType exists, when an administrator creates or edits a model, then the form includes all of the following fields:
   - `model_name` (Data, required, label: "Model Name") — human-readable name displayed in selection dropdowns
   - `description` (Small Text, label: "Description") — optional summary of when to use this model
   - `default_category` (Link → HD Ticket Category, label: "Default Category") — pre-set category applied to ticket
   - `default_sub_category` (Link → HD Ticket Category, label: "Default Sub-Category", `depends_on: "eval:doc.default_category"`) — filtered to children of `default_category`
   - `default_priority` (Select, label: "Default Priority", options: `\nLow\nMedium\nHigh\nUrgent`) — pre-set priority
   - `default_team` (Link → HD Team, label: "Default Team") — pre-set assignment team
   - `checklist_items` (Table → HD Incident Checklist Item, label: "Checklist Items") — child table of checklist entries
   - The DocType uses the naming convention `HD Incident Model` (AR-02: HD prefix)
   - The DocType JSON is in `helpdesk/helpdesk/doctype/hd_incident_model/hd_incident_model.json`

2. **[HD Incident Checklist Item — Child DocType Schema]** Given the HD Incident Checklist Item child DocType exists, when inspected, then it has the following fields:
   - `item` (Data, required, label: "Checklist Item", in_list_view: 1) — description of the task to complete
   - `is_mandatory` (Check, label: "Mandatory", default: 1, in_list_view: 1) — if checked, must be completed before ticket resolution
   - The DocType is named `HD Incident Checklist Item` and its JSON is in `helpdesk/helpdesk/doctype/hd_incident_checklist_item/hd_incident_checklist_item.json`
   - `istable: 1` and `parentfield` maps to `checklist_items` in HD Incident Model

3. **[HD Ticket — `incident_model` Link Field]** Given the HD Ticket DocType is modified, when inspected, then it includes:
   - `incident_model` (Link → HD Incident Model, label: "Incident Model", insert_after an appropriate field such as the priority section)
   - All new fields are added via DocType JSON modification (AR-04), NOT via Custom Fields
   - Run `bench migrate` to apply schema changes to `tabHD Ticket`

4. **[HD Ticket — `ticket_checklist` Child Table Field]** Given the HD Ticket DocType is modified, when a model is applied and checklist items exist, then:
   - A child table field `ticket_checklist` (Table → HD Ticket Checklist Item) is present on HD Ticket
   - This table stores the per-ticket copy of checklist items (distinct from the model template — each ticket has its own completion state)
   - The field is hidden in the DocType JSON (`hidden: 0`, visible via the dedicated checklist UI component)

5. **[HD Ticket Checklist Item — Child DocType Schema]** Given the HD Ticket Checklist Item child DocType exists, when inspected, then it has:
   - `item` (Data, required, label: "Item", in_list_view: 1) — copied from the model checklist item text
   - `is_mandatory` (Check, label: "Mandatory", default: 1, in_list_view: 1) — copied from model
   - `is_completed` (Check, label: "Completed", default: 0, in_list_view: 1) — agent checks off each item
   - `completed_by` (Link → User, label: "Completed By", read_only: 1) — auto-set on completion
   - `completed_at` (Datetime, label: "Completed At", read_only: 1) — auto-set on completion
   - The DocType is named `HD Ticket Checklist Item`, `istable: 1`, parent maps to `ticket_checklist` on HD Ticket

6. **[API — `apply_incident_model` Endpoint]** Given the `apply_incident_model(ticket, model)` API endpoint is called by an agent, when executed, then:
   - It fetches the HD Incident Model document by `model` name
   - It updates HD Ticket fields: sets `category` from `default_category`, `sub_category` from `default_sub_category`, `priority` from `default_priority`, `agent_group` (team) from `default_team`, and `incident_model` to the model name — skipping any field where the model value is blank/None
   - It deletes all existing `ticket_checklist` child table entries for the ticket (fresh application)
   - It creates new `HD Ticket Checklist Item` entries in `ticket_checklist` for each item in the model's `checklist_items` child table, copying `item` and `is_mandatory`
   - The ticket is saved with `ignore_permissions=False` (standard permission check)
   - Returns `{ "success": True, "fields_applied": { "category": ..., "priority": ..., ... }, "checklist_items_count": int }`
   - The endpoint uses `@frappe.whitelist()` and requires write permission on HD Ticket
   - Located in `helpdesk/api/incident_model.py`

7. **[API — `complete_checklist_item` Endpoint]** Given the `complete_checklist_item(ticket, checklist_item_name)` API endpoint is called, when a checklist item is toggled:
   - If `is_completed` is currently `0`: sets `is_completed = 1`, `completed_by = frappe.session.user`, `completed_at = frappe.utils.now_datetime()`
   - If `is_completed` is currently `1`: sets `is_completed = 0`, clears `completed_by` and `completed_at` (allows unchecking)
   - Saves the parent ticket via `doc.save()`
   - Returns `{ "success": True, "is_completed": int, "completed_by": str | None, "completed_at": str | None }`
   - Uses `@frappe.whitelist()` and requires write permission on HD Ticket

8. **[Resolution Validation — Server-Side]** Given a ticket has one or more mandatory checklist items (from `ticket_checklist` where `is_mandatory = 1`), when an agent attempts to resolve or close the ticket (status changes to "Resolved" or "Closed"), then:
   - A `validate` hook in `helpdesk/helpdesk/overrides/hd_ticket.py` (or `hd_ticket.py`) checks all `ticket_checklist` rows where `is_mandatory = 1`
   - If any mandatory item has `is_completed = 0`, `frappe.throw()` is raised with the message: `"Cannot resolve ticket: {N} mandatory checklist item(s) must be completed first: {item list}"`
   - The validation only triggers when `doc.status` changes to "Resolved" or "Closed" AND `doc.ticket_checklist` is non-empty with mandatory incomplete items
   - The validation is registered via `doc_events` in `hooks.py`

9. **[Frontend — Incident Model Selector on Ticket Form]** Given an agent is creating or editing a ticket, when they use the `incident_model` Link field, then:
   - The field is a standard Link field rendered in the ticket form (the auto-populate is triggered client-side)
   - On `change` of the `incident_model` field value (watch in Vue component), the frontend calls the `apply_incident_model` API endpoint
   - On successful API response, the ticket form fields (`category`, `sub_category`, `priority`, `agent_group`) are updated in the reactive ticket data (no full page reload)
   - A success toast/notification shows: "Incident model applied: {model_name}"
   - If the model has checklist items, the `TicketChecklist.vue` component re-renders with the new items
   - The logic is implemented in the ticket detail/edit component (e.g., `desk/src/pages/ticket/TicketDetail.vue` or equivalent)

10. **[Frontend — `TicketChecklist.vue` Component]** Given a ticket has `ticket_checklist` rows, when the agent views the ticket, then:
    - A `TicketChecklist.vue` component is visible in the ticket sidebar or below the ticket fields
    - It displays all checklist items as a list with a checkbox for each item
    - Mandatory items are visually marked (e.g., a red asterisk or "Required" badge)
    - Completed items show a checkmark and the `completed_by` + `completed_at` details
    - Clicking a checkbox calls `complete_checklist_item` API endpoint and updates the UI on success
    - A progress summary shows: "X / Y completed" (with a progress bar or fraction)
    - If all mandatory items are complete, a green "All required items completed" indicator shows
    - The component is located at `desk/src/components/ticket/TicketChecklist.vue`

11. **[Frontend — Resolution Blocking — Client-Side]** Given a ticket has incomplete mandatory checklist items, when an agent attempts to resolve the ticket via the UI, then:
    - Before submitting the status change to "Resolved"/"Closed", the frontend checks the `ticket_checklist` data for incomplete mandatory items
    - If any are found, a warning toast/message is displayed: "Complete all mandatory checklist items before resolving"
    - The resolve action is blocked client-side (the API call is NOT made)
    - The server-side validation (AC #8) acts as the authoritative guard; the client-side check is UX enhancement only

12. **[Default Incident Model Fixtures]** Given a fresh Frappe Helpdesk installation, when the app is installed or `bench migrate` is run after installation, then at least 5 default HD Incident Model records are available:

    | Model Name        | Default Priority | Checklist Items (count) | Description |
    |-------------------|-----------------|------------------------|-------------|
    | Password Reset    | Low             | 3                      | User cannot log in — password reset required |
    | System Outage     | Urgent          | 4                      | Critical system unavailable — all users affected |
    | Access Request    | Medium          | 3                      | New system or application access required |
    | Hardware Failure  | High            | 4                      | Physical device malfunction or failure |
    | Software Bug      | Medium          | 3                      | Application error or unexpected behavior |

    - Fixtures are defined as JSON files in `helpdesk/fixtures/`
    - Fixtures are registered in `hooks.py` under `fixtures = [{"dt": "HD Incident Model"}]` or equivalent
    - Each fixture record includes `model_name`, `description`, `default_priority`, and at least 2 `checklist_items`
    - No default team or category is set (those are site-specific)

13. **[Unit Tests — Backend]** Given the implementation is complete, when the test suite runs, then unit tests exist covering:
    - `apply_incident_model` populates ticket fields from model (category, priority, team)
    - `apply_incident_model` skips blank/None fields in the model (does not overwrite ticket values with empty strings)
    - `apply_incident_model` creates `ticket_checklist` rows matching the model's `checklist_items`
    - `apply_incident_model` replaces existing `ticket_checklist` rows on re-application
    - `complete_checklist_item` sets `is_completed=1` and records `completed_by` + `completed_at`
    - `complete_checklist_item` clears `is_completed`, `completed_by`, `completed_at` when toggling off
    - Resolution validation raises `frappe.ValidationError` when mandatory items are incomplete
    - Resolution validation passes when all mandatory items are completed
    - Resolution validation is skipped when `ticket_checklist` is empty
    - Minimum 80% line coverage on all new backend Python code (NFR-M-01)

## Tasks / Subtasks

- [ ] Task 1 — Create `HD Incident Checklist Item` child DocType (AC: #2)
  - [ ] 1.1 Create directory `helpdesk/helpdesk/doctype/hd_incident_checklist_item/` with:
    - `__init__.py` (empty)
    - `hd_incident_checklist_item.json`:
      ```json
      {
        "actions": [],
        "autoname": "hash",
        "creation": "2026-01-01 00:00:00.000000",
        "doctype": "DocType",
        "editable_grid": 1,
        "engine": "InnoDB",
        "field_order": ["item", "is_mandatory"],
        "fields": [
          {
            "fieldname": "item",
            "fieldtype": "Data",
            "in_list_view": 1,
            "label": "Checklist Item",
            "reqd": 1
          },
          {
            "default": "1",
            "fieldname": "is_mandatory",
            "fieldtype": "Check",
            "in_list_view": 1,
            "label": "Mandatory"
          }
        ],
        "istable": 1,
        "links": [],
        "modified": "2026-01-01 00:00:00.000000",
        "modified_by": "Administrator",
        "module": "Helpdesk",
        "name": "HD Incident Checklist Item",
        "owner": "Administrator",
        "permissions": [],
        "sort_field": "modified",
        "sort_order": "DESC"
      }
      ```
    - `hd_incident_checklist_item.py` (standard empty controller):
      ```python
      # Copyright (c) 2026, Frappe Technologies Pvt. Ltd. and contributors
      # For license information, please see license.txt

      import frappe
      from frappe.model.document import Document


      class HDIncidentChecklistItem(Document):
          pass
      ```

- [ ] Task 2 — Create `HD Incident Model` DocType (AC: #1)
  - [ ] 2.1 Create directory `helpdesk/helpdesk/doctype/hd_incident_model/` with:
    - `__init__.py` (empty)
    - `hd_incident_model.json`:
      ```json
      {
        "actions": [],
        "autoname": "field:model_name",
        "creation": "2026-01-01 00:00:00.000000",
        "doctype": "DocType",
        "engine": "InnoDB",
        "field_order": [
          "model_name", "description", "section_defaults",
          "default_category", "default_sub_category", "column_break_defaults",
          "default_priority", "default_team", "section_checklist", "checklist_items"
        ],
        "fields": [
          {
            "fieldname": "model_name",
            "fieldtype": "Data",
            "label": "Model Name",
            "reqd": 1,
            "unique": 1,
            "in_list_view": 1
          },
          {
            "fieldname": "description",
            "fieldtype": "Small Text",
            "label": "Description"
          },
          {
            "fieldname": "section_defaults",
            "fieldtype": "Section Break",
            "label": "Default Field Values"
          },
          {
            "fieldname": "default_category",
            "fieldtype": "Link",
            "label": "Default Category",
            "options": "HD Ticket Category"
          },
          {
            "depends_on": "eval:doc.default_category",
            "fieldname": "default_sub_category",
            "fieldtype": "Link",
            "label": "Default Sub-Category",
            "options": "HD Ticket Category"
          },
          {
            "fieldname": "column_break_defaults",
            "fieldtype": "Column Break"
          },
          {
            "fieldname": "default_priority",
            "fieldtype": "Select",
            "label": "Default Priority",
            "options": "\nLow\nMedium\nHigh\nUrgent"
          },
          {
            "fieldname": "default_team",
            "fieldtype": "Link",
            "label": "Default Team",
            "options": "HD Team"
          },
          {
            "fieldname": "section_checklist",
            "fieldtype": "Section Break",
            "label": "Checklist Items"
          },
          {
            "fieldname": "checklist_items",
            "fieldtype": "Table",
            "label": "Checklist Items",
            "options": "HD Incident Checklist Item"
          }
        ],
        "istable": 0,
        "links": [],
        "modified": "2026-01-01 00:00:00.000000",
        "modified_by": "Administrator",
        "module": "Helpdesk",
        "name": "HD Incident Model",
        "naming_rule": "By fieldname",
        "owner": "Administrator",
        "permissions": [
          {
            "create": 1,
            "delete": 1,
            "email": 1,
            "export": 1,
            "print": 1,
            "read": 1,
            "report": 1,
            "role": "HD Admin",
            "share": 1,
            "write": 1
          },
          {
            "export": 1,
            "print": 1,
            "read": 1,
            "report": 1,
            "role": "HD Agent",
            "share": 1
          }
        ],
        "sort_field": "modified",
        "sort_order": "DESC"
      }
      ```
    - `hd_incident_model.py`:
      ```python
      # Copyright (c) 2026, Frappe Technologies Pvt. Ltd. and contributors
      # For license information, please see license.txt

      import frappe
      from frappe.model.document import Document


      class HDIncidentModel(Document):
          pass
      ```
  - [ ] 2.2 Run `bench migrate` to create the `tabHD Incident Model` and `tabHD Incident Checklist Item` database tables.

- [ ] Task 3 — Create `HD Ticket Checklist Item` child DocType (AC: #5)
  - [ ] 3.1 Create directory `helpdesk/helpdesk/doctype/hd_ticket_checklist_item/` with:
    - `__init__.py` (empty)
    - `hd_ticket_checklist_item.json`:
      ```json
      {
        "actions": [],
        "autoname": "hash",
        "creation": "2026-01-01 00:00:00.000000",
        "doctype": "DocType",
        "editable_grid": 1,
        "engine": "InnoDB",
        "field_order": ["item", "is_mandatory", "is_completed", "completed_by", "completed_at"],
        "fields": [
          {
            "fieldname": "item",
            "fieldtype": "Data",
            "in_list_view": 1,
            "label": "Item",
            "reqd": 1
          },
          {
            "default": "1",
            "fieldname": "is_mandatory",
            "fieldtype": "Check",
            "in_list_view": 1,
            "label": "Mandatory"
          },
          {
            "default": "0",
            "fieldname": "is_completed",
            "fieldtype": "Check",
            "in_list_view": 1,
            "label": "Completed"
          },
          {
            "fieldname": "completed_by",
            "fieldtype": "Link",
            "label": "Completed By",
            "options": "User",
            "read_only": 1
          },
          {
            "fieldname": "completed_at",
            "fieldtype": "Datetime",
            "label": "Completed At",
            "read_only": 1
          }
        ],
        "istable": 1,
        "links": [],
        "modified": "2026-01-01 00:00:00.000000",
        "modified_by": "Administrator",
        "module": "Helpdesk",
        "name": "HD Ticket Checklist Item",
        "owner": "Administrator",
        "permissions": [],
        "sort_field": "modified",
        "sort_order": "DESC"
      }
      ```
    - `hd_ticket_checklist_item.py`:
      ```python
      # Copyright (c) 2026, Frappe Technologies Pvt. Ltd. and contributors
      # For license information, please see license.txt

      import frappe
      from frappe.model.document import Document


      class HDTicketChecklistItem(Document):
          pass
      ```

- [ ] Task 4 — Modify HD Ticket DocType JSON to add `incident_model` and `ticket_checklist` fields (AC: #3, #4)
  - [ ] 4.1 Open `helpdesk/helpdesk/doctype/hd_ticket/hd_ticket.json` and add these fields to the `fields` array (place `incident_model` in a logical position near the priority/category section; place `ticket_checklist` near the bottom of the fields list):
    ```json
    {
      "fieldname": "incident_model",
      "fieldtype": "Link",
      "label": "Incident Model",
      "options": "HD Incident Model"
    },
    {
      "fieldname": "ticket_checklist",
      "fieldtype": "Table",
      "label": "Checklist",
      "options": "HD Ticket Checklist Item",
      "hidden": 0
    }
    ```
  - [ ] 4.2 Run `bench migrate` to apply schema changes to `tabHD Ticket`.

- [ ] Task 5 — Create `helpdesk/api/incident_model.py` with `apply_incident_model` and `complete_checklist_item` endpoints (AC: #6, #7)
  - [ ] 5.1 Create `helpdesk/api/incident_model.py`:
    ```python
    # Copyright (c) 2026, Frappe Technologies Pvt. Ltd. and contributors
    # For license information, please see license.txt

    import frappe
    from frappe import _
    from frappe.utils import now_datetime


    @frappe.whitelist()
    def apply_incident_model(ticket: str, model: str) -> dict:
        """
        Apply an HD Incident Model to a ticket.

        Populates ticket fields from the model's defaults and copies checklist
        items into the ticket's ticket_checklist child table.

        Returns:
            {
                "success": True,
                "fields_applied": {"category": ..., "priority": ..., ...},
                "checklist_items_count": int
            }
        """
        frappe.has_permission("HD Ticket", "write", doc=ticket, throw=True)

        ticket_doc = frappe.get_doc("HD Ticket", ticket)
        model_doc = frappe.get_doc("HD Incident Model", model)

        fields_applied = {}

        # Apply default fields — only if the model value is non-empty
        field_map = {
            "default_category": "category",
            "default_sub_category": "sub_category",
            "default_priority": "priority",
            "default_team": "agent_group",
        }
        for model_field, ticket_field in field_map.items():
            value = model_doc.get(model_field)
            if value:
                ticket_doc.set(ticket_field, value)
                fields_applied[ticket_field] = value

        # Set the incident_model reference
        ticket_doc.incident_model = model
        fields_applied["incident_model"] = model

        # Replace checklist items — clear existing, copy from model
        ticket_doc.set("ticket_checklist", [])
        for model_item in model_doc.get("checklist_items", []):
            ticket_doc.append("ticket_checklist", {
                "item": model_item.item,
                "is_mandatory": model_item.is_mandatory,
                "is_completed": 0,
            })

        ticket_doc.save()
        frappe.db.commit()

        return {
            "success": True,
            "fields_applied": fields_applied,
            "checklist_items_count": len(ticket_doc.ticket_checklist),
        }


    @frappe.whitelist()
    def complete_checklist_item(ticket: str, checklist_item_name: str) -> dict:
        """
        Toggle the completion state of a single checklist item on a ticket.

        If currently incomplete: marks completed with timestamp and user.
        If currently complete: clears completion state (allows unchecking).

        Returns:
            {
                "success": True,
                "is_completed": int,
                "completed_by": str | None,
                "completed_at": str | None
            }
        """
        frappe.has_permission("HD Ticket", "write", doc=ticket, throw=True)

        ticket_doc = frappe.get_doc("HD Ticket", ticket)
        checklist_row = None
        for row in ticket_doc.get("ticket_checklist", []):
            if row.name == checklist_item_name:
                checklist_row = row
                break

        if not checklist_row:
            frappe.throw(
                _("Checklist item {0} not found on ticket {1}").format(
                    checklist_item_name, ticket
                ),
                frappe.DoesNotExistError,
            )

        if checklist_row.is_completed:
            # Toggle off — clear completion state
            checklist_row.is_completed = 0
            checklist_row.completed_by = None
            checklist_row.completed_at = None
        else:
            # Toggle on — record completion
            checklist_row.is_completed = 1
            checklist_row.completed_by = frappe.session.user
            checklist_row.completed_at = now_datetime()

        ticket_doc.save()
        frappe.db.commit()

        return {
            "success": True,
            "is_completed": checklist_row.is_completed,
            "completed_by": checklist_row.completed_by,
            "completed_at": str(checklist_row.completed_at) if checklist_row.completed_at else None,
        }
    ```
  - [ ] 5.2 Verify `helpdesk/api/__init__.py` exists (should be present from prior stories). No explicit import needed — `@frappe.whitelist()` functions are auto-discoverable.

- [ ] Task 6 — Add resolution validation hook for checklist completeness (AC: #8)
  - [ ] 6.1 Open `helpdesk/helpdesk/overrides/hd_ticket.py` (the override module used by prior stories for `validate_priority_matrix` and similar hooks). Add or update the `validate` function:
    ```python
    def validate_checklist_before_resolution(doc, method=None):
        """
        Prevent ticket resolution/closure if mandatory checklist items are incomplete.
        Story 1.9: Incident Models / Templates
        """
        if doc.status not in ("Resolved", "Closed"):
            return

        checklist = doc.get("ticket_checklist", [])
        if not checklist:
            return

        incomplete_mandatory = [
            row.item
            for row in checklist
            if row.is_mandatory and not row.is_completed
        ]

        if incomplete_mandatory:
            item_list = ", ".join(f'"{i}"' for i in incomplete_mandatory)
            frappe.throw(
                _(
                    "Cannot resolve ticket: {0} mandatory checklist item(s) must be "
                    "completed first: {1}"
                ).format(len(incomplete_mandatory), item_list),
                frappe.ValidationError,
            )
    ```
  - [ ] 6.2 Register the new validate function in `hooks.py` `doc_events` for `"HD Ticket"`. Add (or extend the existing validate list):
    ```python
    doc_events = {
        "HD Ticket": {
            "validate": [
                "helpdesk.helpdesk.overrides.hd_ticket.validate_priority_matrix",
                # ... other existing validate hooks ...
                "helpdesk.helpdesk.overrides.hd_ticket.validate_checklist_before_resolution",
            ],
        }
    }
    ```
    Note: If `validate` is currently a string (single handler), convert it to a list.

- [ ] Task 7 — Create `TicketChecklist.vue` frontend component (AC: #10, #11)
  - [ ] 7.1 Create `desk/src/components/ticket/TicketChecklist.vue`:
    ```vue
    <template>
      <div v-if="checklist.length > 0" class="mt-4">
        <div class="flex items-center justify-between mb-2">
          <h3 class="text-sm font-semibold text-gray-700">
            {{ __('Checklist') }}
          </h3>
          <span
            class="text-xs font-medium"
            :class="allMandatoryComplete ? 'text-green-600' : 'text-gray-500'"
          >
            {{ completedCount }} / {{ checklist.length }} {{ __('completed') }}
          </span>
        </div>

        <!-- Progress bar -->
        <div class="mb-3 h-1.5 w-full rounded-full bg-gray-200">
          <div
            class="h-1.5 rounded-full transition-all"
            :class="allMandatoryComplete ? 'bg-green-500' : 'bg-blue-500'"
            :style="{ width: progressPercent + '%' }"
          />
        </div>

        <!-- All mandatory complete indicator -->
        <p v-if="allMandatoryComplete" class="mb-2 text-xs text-green-600 font-medium">
          {{ __('All required items completed') }}
        </p>

        <!-- Checklist items -->
        <ul class="space-y-2">
          <li
            v-for="item in checklist"
            :key="item.name"
            class="flex items-start gap-2 rounded-md p-2 transition-colors"
            :class="item.is_completed ? 'bg-gray-50' : 'bg-white'"
          >
            <input
              type="checkbox"
              :checked="!!item.is_completed"
              :disabled="toggleResource.loading"
              class="mt-0.5 h-4 w-4 cursor-pointer rounded border-gray-300 text-blue-600 focus:ring-blue-500"
              @change="toggleItem(item)"
            />
            <div class="min-w-0 flex-1">
              <span
                class="text-sm"
                :class="item.is_completed ? 'text-gray-400 line-through' : 'text-gray-700'"
              >
                {{ item.item }}
              </span>
              <span
                v-if="item.is_mandatory && !item.is_completed"
                class="ml-1 inline-flex items-center rounded-full bg-red-50 px-1.5 py-0.5 text-xs font-medium text-red-600"
              >
                {{ __('Required') }}
              </span>
              <p v-if="item.is_completed && item.completed_by" class="mt-0.5 text-xs text-gray-400">
                {{ __('By') }} {{ item.completed_by }}
                <template v-if="item.completed_at">
                  &middot; {{ formatDatetime(item.completed_at) }}
                </template>
              </p>
            </div>
          </li>
        </ul>
      </div>
    </template>

    <script setup lang="ts">
    import { computed } from 'vue'
    import { createResource } from 'frappe-ui'
    import { formatDatetime } from '@/utils'

    interface ChecklistItem {
      name: string
      item: string
      is_mandatory: 0 | 1
      is_completed: 0 | 1
      completed_by?: string
      completed_at?: string
    }

    const props = defineProps<{
      ticketName: string
      checklist: ChecklistItem[]
    }>()

    const emit = defineEmits<{ itemToggled: [itemName: string, isCompleted: boolean] }>()

    const completedCount = computed(() =>
      props.checklist.filter((i) => i.is_completed).length
    )

    const progressPercent = computed(() =>
      props.checklist.length === 0
        ? 0
        : Math.round((completedCount.value / props.checklist.length) * 100)
    )

    const allMandatoryComplete = computed(() =>
      props.checklist
        .filter((i) => i.is_mandatory)
        .every((i) => i.is_completed)
    )

    const toggleResource = createResource({
      url: 'helpdesk.api.incident_model.complete_checklist_item',
      onSuccess(data: { is_completed: number }) {
        // Parent component handles data refresh
      },
      onError(err: any) {
        console.error('Failed to toggle checklist item', err)
      },
    })

    function toggleItem(item: ChecklistItem) {
      toggleResource.submit({
        ticket: props.ticketName,
        checklist_item_name: item.name,
      }, {
        onSuccess(data: any) {
          emit('itemToggled', item.name, !!data.is_completed)
        },
      })
    }
    </script>
    ```
  - [ ] 7.2 Register `TicketChecklist.vue` in the ticket detail/sidebar view. Locate the ticket detail page component (e.g., `desk/src/pages/ticket/TicketDetail.vue` or equivalent) and:
    - Import: `import TicketChecklist from '@/components/ticket/TicketChecklist.vue'`
    - Add in the ticket sidebar or below the main ticket fields:
      ```vue
      <TicketChecklist
        :ticket-name="ticket.name"
        :checklist="ticket.ticket_checklist ?? []"
        @item-toggled="onChecklistItemToggled"
      />
      ```
    - Implement `onChecklistItemToggled(itemName, isCompleted)` to update the local ticket data without a full reload (update the matching item in `ticket.ticket_checklist`).

- [ ] Task 8 — Implement incident model auto-populate on ticket form (AC: #9)
  - [ ] 8.1 In the ticket detail/edit component, add a `watch` on the `incident_model` field (or on the relevant `createResource` data):
    ```typescript
    import { watch } from 'vue'
    import { createResource } from 'frappe-ui'

    const applyModelResource = createResource({
      url: 'helpdesk.api.incident_model.apply_incident_model',
      onSuccess(data: any) {
        // Merge applied fields into local ticket reactive object
        if (data.fields_applied) {
          Object.assign(ticket, data.fields_applied)
        }
        // Reload ticket checklist data
        reloadTicket()
        // Show success toast
        toast({ title: `Incident model applied`, variant: 'success' })
      },
      onError(err: any) {
        toast({ title: 'Failed to apply model', message: err?.message, variant: 'error' })
      },
    })

    watch(
      () => ticket.incident_model,
      (newModel, oldModel) => {
        if (newModel && newModel !== oldModel) {
          applyModelResource.submit({
            ticket: ticket.name,
            model: newModel,
          })
        }
      }
    )
    ```
  - [ ] 8.2 Add a client-side guard to block "Resolve"/"Close" actions when mandatory checklist items are incomplete (AC: #11):
    ```typescript
    function canResolveTicket(): boolean {
      const checklist = ticket.ticket_checklist ?? []
      const incompleteRequired = checklist.filter(
        (item: any) => item.is_mandatory && !item.is_completed
      )
      if (incompleteRequired.length > 0) {
        toast({
          title: 'Complete all mandatory checklist items before resolving',
          variant: 'warning',
        })
        return false
      }
      return true
    }
    ```
    Call `canResolveTicket()` before the status-change API call in the resolve/close handler.

- [ ] Task 9 — Create default incident model fixtures (AC: #12)
  - [ ] 9.1 Create `helpdesk/fixtures/hd_incident_model.json`:
    ```json
    [
      {
        "doctype": "HD Incident Model",
        "model_name": "Password Reset",
        "description": "User cannot log in and requires a password reset.",
        "default_priority": "Low",
        "checklist_items": [
          {"item": "Verify user identity via secondary authentication", "is_mandatory": 1},
          {"item": "Reset password and notify user via secure channel", "is_mandatory": 1},
          {"item": "Confirm user can log in successfully", "is_mandatory": 1}
        ]
      },
      {
        "doctype": "HD Incident Model",
        "model_name": "System Outage",
        "description": "Critical system or service is unavailable affecting multiple users.",
        "default_priority": "Urgent",
        "checklist_items": [
          {"item": "Notify stakeholders and management of outage", "is_mandatory": 1},
          {"item": "Identify root cause and document initial findings", "is_mandatory": 1},
          {"item": "Apply fix or initiate rollback procedure", "is_mandatory": 1},
          {"item": "Verify service restoration and monitor for 15 minutes", "is_mandatory": 1}
        ]
      },
      {
        "doctype": "HD Incident Model",
        "model_name": "Access Request",
        "description": "Request to grant new system, application, or data access.",
        "default_priority": "Medium",
        "checklist_items": [
          {"item": "Obtain manager or data owner approval", "is_mandatory": 1},
          {"item": "Provision access in the relevant system", "is_mandatory": 1},
          {"item": "Notify requestor and confirm access is working", "is_mandatory": 1}
        ]
      },
      {
        "doctype": "HD Incident Model",
        "model_name": "Hardware Failure",
        "description": "Physical device (laptop, printer, server component) has failed or malfunctioned.",
        "default_priority": "High",
        "checklist_items": [
          {"item": "Diagnose failure and document symptoms", "is_mandatory": 1},
          {"item": "Arrange replacement or loaner equipment if needed", "is_mandatory": 0},
          {"item": "Recover or backup user data where possible", "is_mandatory": 1},
          {"item": "Confirm user can continue work on replacement device", "is_mandatory": 1}
        ]
      },
      {
        "doctype": "HD Incident Model",
        "model_name": "Software Bug",
        "description": "Application is behaving unexpectedly or producing errors.",
        "default_priority": "Medium",
        "checklist_items": [
          {"item": "Reproduce the issue and capture error details / screenshots", "is_mandatory": 1},
          {"item": "Identify and document workaround for affected users", "is_mandatory": 0},
          {"item": "Log bug report with development team or vendor reference number", "is_mandatory": 1}
        ]
      }
    ]
    ```
  - [ ] 9.2 Register the fixture in `hooks.py`:
    ```python
    fixtures = [
        # ... existing fixtures ...
        {"dt": "HD Incident Model"},
    ]
    ```
    If `fixtures` already exists in `hooks.py`, append the new entry rather than replacing the list.
  - [ ] 9.3 Run `bench migrate` then verify fixtures are loaded: `bench --site <site> frappe.utils.bench_helper.main execute helpdesk.fixtures` or simply check via `frappe.get_all("HD Incident Model")`.

- [ ] Task 10 — Create migration patches (AC: #3, #4)
  - [ ] 10.1 Create `helpdesk/patches/v1_phase1/add_incident_model_doctypes.py`:
    ```python
    """
    Patch: Create HD Incident Model, HD Incident Checklist Item,
    and HD Ticket Checklist Item DocTypes; add incident_model and
    ticket_checklist fields to HD Ticket.
    Story: 1.9 -- Incident Models / Templates
    """
    import frappe


    def execute():
        frappe.reload_doctype("HD Incident Checklist Item", force=True)
        frappe.reload_doctype("HD Incident Model", force=True)
        frappe.reload_doctype("HD Ticket Checklist Item", force=True)
        frappe.reload_doctype("HD Ticket", force=True)
    ```
  - [ ] 10.2 Register the patch in `patches.txt`:
    ```
    helpdesk.patches.v1_phase1.add_incident_model_doctypes
    ```
  - [ ] 10.3 Confirm `helpdesk/patches/v1_phase1/__init__.py` exists (created by Stories 1.1–1.8). Do not overwrite.

- [ ] Task 11 — Write unit tests (AC: #13)
  - [ ] 11.1 Create `helpdesk/helpdesk/doctype/hd_ticket/test_hd_ticket_incident_model.py`:
    ```python
    import frappe
    from frappe.tests.utils import FrappeTestCase
    from helpdesk.api.incident_model import apply_incident_model, complete_checklist_item


    class TestIncidentModelApplication(FrappeTestCase):
        """Unit tests for Story 1.9: Incident Models / Templates."""

        def setUp(self):
            # Create a test agent user
            if not frappe.db.exists("User", "agent.im@test.com"):
                frappe.get_doc({
                    "doctype": "User",
                    "email": "agent.im@test.com",
                    "full_name": "IM Agent",
                    "first_name": "IM",
                    "last_name": "Agent",
                    "send_welcome_email": 0,
                    "roles": [{"role": "HD Agent"}],
                }).insert(ignore_permissions=True)

            frappe.set_user("agent.im@test.com")

            # Create a test incident model with checklist items
            self.model = frappe.get_doc({
                "doctype": "HD Incident Model",
                "model_name": f"Test Model {frappe.generate_hash(length=8)}",
                "description": "Test model for unit tests",
                "default_priority": "High",
                "checklist_items": [
                    {"item": "Mandatory item 1", "is_mandatory": 1},
                    {"item": "Optional item",   "is_mandatory": 0},
                    {"item": "Mandatory item 2", "is_mandatory": 1},
                ],
            }).insert(ignore_permissions=True)

            # Create a test ticket
            self.ticket = frappe.get_doc({
                "doctype": "HD Ticket",
                "subject": "Test Ticket for Incident Model",
                "raised_by": "customer@example.com",
            }).insert(ignore_permissions=True)

        def tearDown(self):
            frappe.set_user("Administrator")
            frappe.db.rollback()

        # --- apply_incident_model ---

        def test_apply_model_sets_priority(self):
            result = apply_incident_model(
                ticket=self.ticket.name, model=self.model.name
            )
            self.assertTrue(result["success"])
            self.assertIn("priority", result["fields_applied"])
            doc = frappe.get_doc("HD Ticket", self.ticket.name)
            self.assertEqual(doc.priority, "High")

        def test_apply_model_sets_incident_model_reference(self):
            apply_incident_model(ticket=self.ticket.name, model=self.model.name)
            doc = frappe.get_doc("HD Ticket", self.ticket.name)
            self.assertEqual(doc.incident_model, self.model.name)

        def test_apply_model_skips_blank_fields(self):
            """Model with no default_category should NOT overwrite ticket category."""
            # Ensure model has no default_category
            self.assertFalse(self.model.default_category)
            self.ticket.reload()
            original_category = self.ticket.category

            apply_incident_model(ticket=self.ticket.name, model=self.model.name)
            doc = frappe.get_doc("HD Ticket", self.ticket.name)
            # category should be unchanged (still whatever it was before)
            self.assertEqual(doc.category, original_category)

        def test_apply_model_creates_checklist_rows(self):
            result = apply_incident_model(
                ticket=self.ticket.name, model=self.model.name
            )
            self.assertEqual(result["checklist_items_count"], 3)
            doc = frappe.get_doc("HD Ticket", self.ticket.name)
            self.assertEqual(len(doc.ticket_checklist), 3)
            items = [row.item for row in doc.ticket_checklist]
            self.assertIn("Mandatory item 1", items)
            self.assertIn("Optional item", items)
            self.assertIn("Mandatory item 2", items)

        def test_apply_model_replaces_existing_checklist(self):
            # Apply once
            apply_incident_model(ticket=self.ticket.name, model=self.model.name)
            # Apply again — should replace, not duplicate
            result = apply_incident_model(
                ticket=self.ticket.name, model=self.model.name
            )
            doc = frappe.get_doc("HD Ticket", self.ticket.name)
            # Should still be exactly 3, not 6
            self.assertEqual(len(doc.ticket_checklist), 3)
            self.assertEqual(result["checklist_items_count"], 3)

        # --- complete_checklist_item ---

        def test_complete_checklist_item_sets_completed(self):
            apply_incident_model(ticket=self.ticket.name, model=self.model.name)
            doc = frappe.get_doc("HD Ticket", self.ticket.name)
            item = doc.ticket_checklist[0]

            result = complete_checklist_item(
                ticket=self.ticket.name, checklist_item_name=item.name
            )
            self.assertTrue(result["success"])
            self.assertEqual(result["is_completed"], 1)
            self.assertEqual(result["completed_by"], frappe.session.user)
            self.assertIsNotNone(result["completed_at"])

        def test_complete_checklist_item_toggles_off(self):
            apply_incident_model(ticket=self.ticket.name, model=self.model.name)
            doc = frappe.get_doc("HD Ticket", self.ticket.name)
            item = doc.ticket_checklist[0]

            # Complete it
            complete_checklist_item(
                ticket=self.ticket.name, checklist_item_name=item.name
            )
            # Then uncomplete it
            result = complete_checklist_item(
                ticket=self.ticket.name, checklist_item_name=item.name
            )
            self.assertEqual(result["is_completed"], 0)
            self.assertIsNone(result["completed_by"])
            self.assertIsNone(result["completed_at"])

        # --- resolution validation ---

        def test_resolution_blocked_when_mandatory_items_incomplete(self):
            apply_incident_model(ticket=self.ticket.name, model=self.model.name)
            # Do NOT complete checklist items
            doc = frappe.get_doc("HD Ticket", self.ticket.name)
            doc.status = "Resolved"
            with self.assertRaises(frappe.ValidationError):
                doc.save()

        def test_resolution_allowed_when_all_mandatory_items_complete(self):
            apply_incident_model(ticket=self.ticket.name, model=self.model.name)
            doc = frappe.get_doc("HD Ticket", self.ticket.name)

            # Complete all mandatory items (items at index 0 and 2)
            for row in doc.ticket_checklist:
                if row.is_mandatory:
                    complete_checklist_item(
                        ticket=self.ticket.name, checklist_item_name=row.name
                    )

            # Now resolution should succeed
            doc.reload()
            doc.status = "Resolved"
            try:
                doc.save()  # Should NOT raise
            except frappe.ValidationError as e:
                self.fail(f"Resolution should be allowed but got: {e}")

        def test_resolution_allowed_when_no_checklist(self):
            """Ticket with no checklist should resolve without error."""
            doc = frappe.get_doc("HD Ticket", self.ticket.name)
            self.assertEqual(len(doc.ticket_checklist), 0)
            doc.status = "Resolved"
            try:
                doc.save()
            except frappe.ValidationError as e:
                self.fail(f"Resolution without checklist should be allowed: {e}")
    ```
  - [ ] 11.2 Run tests:
    ```bash
    bench --site <site> run-tests --module helpdesk.helpdesk.doctype.hd_ticket.test_hd_ticket_incident_model
    ```
  - [ ] 11.3 Verify >= 80% line coverage on all new backend Python code (NFR-M-01).

## Dev Notes

### Architecture Patterns

- **New DocTypes (ADR-02):** `HD Incident Model`, `HD Incident Checklist Item`, and `HD Ticket Checklist Item` are all explicitly listed in the architecture's new DocType schema. `HD Incident Model` is a first-class DocType (not a child); `HD Incident Checklist Item` is its child table; `HD Ticket Checklist Item` is the per-ticket copy of checklist items. [Source: architecture.md#ADR-02]

- **HD Ticket Extension (ADR-01):** The `incident_model` Link field and `ticket_checklist` Table field are added directly to HD Ticket JSON (AR-04). The architecture explicitly models `incident_model → HD Incident Model (Link)` as a relationship on HD Ticket. [Source: architecture.md#ADR-01, ADR-02]

- **API Location (ADR-08):** The `apply_incident_model` and `complete_checklist_item` endpoints are placed in a new module `helpdesk/api/incident_model.py`. The architecture lists `helpdesk/api/incident.py` for major incident operations — this new module is a sibling for incident model operations, following the same pattern. [Source: architecture.md#ADR-08]

- **Fixture Approach:** Frappe fixtures are JSON files in `{app}/fixtures/` registered via `hooks.py`. The fixture JSON format is a list of documents. When `bench migrate` runs on a fresh install, fixtures are automatically loaded. For updates, `bench execute frappe.utils.fixtures.export_fixtures` / `bench import-fixtures` can re-sync. [Source: Frappe Framework fixture docs]

- **Child Table Copy Pattern:** When a model is applied to a ticket, the `checklist_items` from HD Incident Model are **copied** (not linked) into the ticket's `ticket_checklist` child table. This means each ticket has its own independent checklist state — completing an item on one ticket does not affect other tickets using the same model. This is the correct pattern for Frappe child tables.

- **Resolution Validation via `hooks.py` `doc_events`:** The validate hook approach (adding to the `validate` key in `doc_events`) is the standard Frappe pattern for cross-cutting validation logic. Ensure the `validate` key can hold a list of handler paths (Frappe supports this). If it was previously a string, convert to a list. [Source: architecture.md#ADR-01, Frappe hooks documentation]

- **Frontend Field Watch Pattern (ADR-09):** The `incident_model` auto-populate uses Vue's `watch()` on the reactive ticket data. This follows the same composable/reactive pattern established by Stories 1.2 (impact/urgency → priority) and 1.3 (category → sub-category filter). [Source: architecture.md#ADR-09]

- **`createResource` for API Calls (ADR-09):** Both `apply_incident_model` and `complete_checklist_item` are called via `createResource` from `frappe-ui`, consistent with all other helpdesk frontend API calls. [Source: architecture.md]

- **NFR-SE-04:** Automation rules are restricted to System Manager or HD Admin. Similarly, creating/editing HD Incident Models should be restricted to HD Admin role. Agents (HD Agent role) have read-only access to models for applying them to tickets. This is reflected in the permissions array in the DocType JSON.

- **NFR-M-02:** All new DocTypes (`HD Incident Model`, `HD Incident Checklist Item`, `HD Ticket Checklist Item`) are automatically accessible via the Frappe REST API (`/api/resource/HD Incident Model`) without any additional code. This is a Frappe Framework guarantee.

### Files to Create / Modify

| Action | Path | Notes |
|--------|------|-------|
| Create | `helpdesk/helpdesk/doctype/hd_incident_checklist_item/__init__.py` | Empty init |
| Create | `helpdesk/helpdesk/doctype/hd_incident_checklist_item/hd_incident_checklist_item.json` | Child DocType for model checklist template items |
| Create | `helpdesk/helpdesk/doctype/hd_incident_checklist_item/hd_incident_checklist_item.py` | Empty controller |
| Create | `helpdesk/helpdesk/doctype/hd_incident_model/__init__.py` | Empty init |
| Create | `helpdesk/helpdesk/doctype/hd_incident_model/hd_incident_model.json` | Main incident model DocType |
| Create | `helpdesk/helpdesk/doctype/hd_incident_model/hd_incident_model.py` | Empty controller |
| Create | `helpdesk/helpdesk/doctype/hd_ticket_checklist_item/__init__.py` | Empty init |
| Create | `helpdesk/helpdesk/doctype/hd_ticket_checklist_item/hd_ticket_checklist_item.json` | Child DocType for per-ticket checklist with completion state |
| Create | `helpdesk/helpdesk/doctype/hd_ticket_checklist_item/hd_ticket_checklist_item.py` | Empty controller |
| Modify | `helpdesk/helpdesk/doctype/hd_ticket/hd_ticket.json` | Add `incident_model` (Link) and `ticket_checklist` (Table) fields |
| Create | `helpdesk/api/incident_model.py` | `apply_incident_model`, `complete_checklist_item` API endpoints |
| Modify | `helpdesk/helpdesk/overrides/hd_ticket.py` | Add `validate_checklist_before_resolution` function |
| Modify | `helpdesk/hooks.py` | Register validate hook + fixture entry for HD Incident Model |
| Create | `helpdesk/fixtures/hd_incident_model.json` | 5 default incident model fixture records |
| Create | `helpdesk/patches/v1_phase1/add_incident_model_doctypes.py` | Migration patch |
| Modify | `patches.txt` | Register migration patch |
| Create | `desk/src/components/ticket/TicketChecklist.vue` | Checklist display with completion toggles |
| Modify | `desk/src/pages/ticket/{TicketDetail or index}.vue` | Register TicketChecklist + incident_model watch + resolve guard |
| Create | `helpdesk/helpdesk/doctype/hd_ticket/test_hd_ticket_incident_model.py` | Unit tests |

### Testing Standards

- Use `frappe.tests.utils.FrappeTestCase` as the base class (consistent with Stories 1.4–1.8).
- All test fixtures created in `setUp` must be cleaned up via `frappe.db.rollback()` in `tearDown`.
- Use `frappe.set_user()` to simulate different user roles; always restore to `"Administrator"` in `tearDown`.
- The `model_name` for test models should include a random hash (e.g., `frappe.generate_hash(length=8)`) to avoid conflicts between test runs.
- Resolution validation tests must call `doc.save()` (triggers validate hook) — not `doc.db_update()` (which bypasses hooks).
- Minimum **80% line coverage** on all new backend Python code (NFR-M-01).

### Constraints

- The `HD Incident Model` name is the `model_name` field value (autoname: `field:model_name`). Ensure `model_name` is unique across all models.
- `apply_incident_model` must be idempotent — calling it twice with the same model on the same ticket should produce the same result (checklist rows are replaced, not duplicated).
- The `ticket_checklist` rows are independent copies — do NOT store a `Link` back to the original model checklist item. This is intentional: the model can change after application without affecting existing ticket checklists.
- The `validate_checklist_before_resolution` hook only fires when `doc.status` changes to "Resolved" or "Closed". It must NOT fire during normal ticket edits (e.g., when an agent adds a comment or changes assignee). Guard with `if doc.status not in ("Resolved", "Closed"): return`.
- Default team field on the model maps to `agent_group` on HD Ticket (the standard Frappe Helpdesk field for team assignment). Verify the exact field name in the existing `hd_ticket.json` before implementation.
- Do NOT use `frappe.db.set_value()` in `apply_incident_model` — use `doc.save()` so all validation hooks (priority matrix, etc.) run correctly.
- All user-facing strings must use `frappe._()` in Python and `__()` in Vue/TypeScript for i18n compatibility.
- The 5 default fixture models intentionally have no `default_category` or `default_team` (these are site-specific). Admins can customize after installation.

### Project Structure Notes

- **`patches/v1_phase1/__init__.py`:** Should already exist from Stories 1.1–1.8. Verify before creating.
- **`helpdesk/fixtures/` directory:** May or may not exist. If it does not, create it with an empty `__init__.py`. Frappe discovers fixture files automatically from `{app}/fixtures/*.json`.
- **`hooks.py` fixtures key:** If `fixtures` already exists in `hooks.py` (from prior stories), append to the list. Do NOT replace the entire `fixtures` list.
- **`hooks.py` `doc_events` validate hook:** Prior stories (1.1–1.8) may have already added validate handlers for HD Ticket. Check the current state of `doc_events` before modifying — ensure you extend rather than replace.
- **HD Team field name on HD Ticket:** The field for team assignment on HD Ticket may be `agent_group` (the Frappe Helpdesk default). Verify by inspecting the existing `hd_ticket.json` before writing `apply_incident_model`.
- **`helpdesk/api/` directory:** Should exist from Story 1.8 (`helpdesk/api/incident.py`). The new `incident_model.py` module is a sibling file — no additional registration needed.

### Dependencies

- **Story 1.1** — HD Settings `itil_mode_enabled` feature flag. Incident Models are available in both Simple and ITIL Mode (models are not ITIL-specific). No feature flag gating required for Story 1.9.
- **Story 1.3** — HD Ticket Category DocType must exist for `default_category` and `default_sub_category` Link fields on HD Incident Model to resolve correctly.
- **Story 1.2** — Priority matrix (`validate_priority_matrix` hook) may already be in `hd_ticket.py`. Ensure the new `validate_checklist_before_resolution` is added without breaking existing validation.

### References

- FR-IM-03 (Incident models/templates with pre-set fields, checklist items, auto-actions): [Source: _bmad-output/planning-artifacts/epics.md#FR-IM-03]
- Story 1.9 AC (from Epics): [Source: _bmad-output/planning-artifacts/epics.md#Story 1.9]
- ADR-01 (Extend HD Ticket — `incident_model` Link field): [Source: _bmad-output/planning-artifacts/architecture.md#ADR-01]
- ADR-02 (New DocTypes: HD Incident Model listed explicitly): [Source: _bmad-output/planning-artifacts/architecture.md#ADR-02]
- ADR-08 (API module pattern — `helpdesk/api/` modules): [Source: _bmad-output/planning-artifacts/architecture.md#ADR-08]
- ADR-09 (Frontend component organization — `desk/src/components/ticket/`): [Source: _bmad-output/planning-artifacts/architecture.md#ADR-09]
- AR-02 (HD prefix naming convention): [Source: _bmad-output/planning-artifacts/epics.md#AR-02]
- AR-04 (New fields via DocType JSON, not Custom Fields): [Source: _bmad-output/planning-artifacts/epics.md#AR-04]
- AR-05 (Migration patches in `helpdesk/patches/v1_phase1/`): [Source: _bmad-output/planning-artifacts/epics.md#AR-05]
- NFR-M-01 (80% unit test coverage): [Source: _bmad-output/planning-artifacts/epics.md#Non-Functional Requirements]
- NFR-M-02 (All new DocTypes accessible via REST API): [Source: _bmad-output/planning-artifacts/epics.md#Non-Functional Requirements]
- NFR-SE-04 (Automation/admin-only management features): [Source: _bmad-output/planning-artifacts/epics.md#Non-Functional Requirements]
- Story 1.3 dependency (HD Ticket Category DocType for category Link fields): [Source: _bmad-output/planning-artifacts/epics.md#Story 1.3]

## Dev Agent Record

### Agent Model Used

Claude Sonnet 4.6 (dev-story workflow)

### Debug Log References

- HD Ticket.name is autoincrement int — test calls cast with `str(ticket.name)` to satisfy type-annotated API (require_type_annotated_api_methods = True in hooks.py)
- Fixture records require explicit `name` field (matching `model_name`) for Frappe `import_file_by_path` to resolve the document
- Resolution validation uses `status_category == "Resolved"` (not raw status string) to correctly detect the resolved state via the computed fetch field

### Completion Notes List

- Created 3 new DocTypes: HD Incident Model, HD Incident Checklist Item (model template), HD Ticket Checklist Item (per-ticket copy with completion state)
- Added `incident_model` (Link) and `ticket_checklist` (Table) fields to HD Ticket JSON
- API module `helpdesk/api/incident_model.py`: `apply_incident_model` + `complete_checklist_item`
- Resolution validation added directly to `HDTicket.validate()` as `validate_checklist_before_resolution()`
- Frontend: `TicketChecklist.vue` component with progress bar, required badges, toggle; integrated into `TicketDetailsTab.vue` below RelatedTickets; `incident_model` field change triggers auto-populate via `applyModelResource`; client-side resolution guard in `handleFieldUpdate`
- 5 default fixture models loaded via `helpdesk/fixtures/hd_incident_model.json` + `hooks.py` fixtures entry
- Migration patch registered in `patches.txt`
- 11 unit tests: all pass (apply model, checklist toggle, resolution validation)
- Bench migrate ran successfully; gunicorn reloaded; frontend build successful

### File List

**Backend — new files:**
- `helpdesk/helpdesk/doctype/hd_incident_checklist_item/__init__.py`
- `helpdesk/helpdesk/doctype/hd_incident_checklist_item/hd_incident_checklist_item.json`
- `helpdesk/helpdesk/doctype/hd_incident_checklist_item/hd_incident_checklist_item.py`
- `helpdesk/helpdesk/doctype/hd_incident_model/__init__.py`
- `helpdesk/helpdesk/doctype/hd_incident_model/hd_incident_model.json`
- `helpdesk/helpdesk/doctype/hd_incident_model/hd_incident_model.py`
- `helpdesk/helpdesk/doctype/hd_ticket_checklist_item/__init__.py`
- `helpdesk/helpdesk/doctype/hd_ticket_checklist_item/hd_ticket_checklist_item.json`
- `helpdesk/helpdesk/doctype/hd_ticket_checklist_item/hd_ticket_checklist_item.py`
- `helpdesk/api/incident_model.py`
- `helpdesk/fixtures/hd_incident_model.json`
- `helpdesk/patches/v1_phase1/add_incident_model_doctypes.py`
- `helpdesk/helpdesk/doctype/hd_ticket/test_incident_model.py`

**Backend — modified files:**
- `helpdesk/helpdesk/doctype/hd_ticket/hd_ticket.json` — added `incident_model` + `ticket_checklist` fields
- `helpdesk/helpdesk/doctype/hd_ticket/hd_ticket.py` — added `validate_checklist_before_resolution()`
- `helpdesk/hooks.py` — added `fixtures` list
- `helpdesk/patches.txt` — registered new patch

**Frontend — new files:**
- `desk/src/components/ticket/TicketChecklist.vue`

**Frontend — modified files:**
- `desk/src/components/ticket-agent/TicketDetailsTab.vue` — TicketChecklist integration, applyIncidentModel, resolution guard
