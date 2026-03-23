# Story 1.3: Multi-Level Ticket Categorization

Status: ready-for-dev

## Story

As a support agent,
I want to categorize tickets with Category and Sub-category,
so that reporting and routing can use granular classification.

## Acceptance Criteria

1. **[HD Ticket Category DocType Exists]** Given the HD Ticket Category DocType has been created, when an administrator opens the Helpdesk setup, then they can create, list, update, and delete HD Ticket Category records with the following fields: `name` (Data, mandatory), `parent_category` (Link → HD Ticket Category, optional), `description` (Small Text, optional), `is_active` (Check, default 1). The DocType follows standard Frappe naming and file structure conventions.

2. **[Hierarchical Category Structure]** Given an administrator creates HD Ticket Category records with a `parent_category` reference, when the category record is saved, then a valid parent-child (Category > Sub-category) hierarchy is established — a category with no `parent_category` is a top-level Category; a category with a `parent_category` is a Sub-category. Self-referential links (a category referencing itself) must be rejected with a validation error.

3. **[category and sub_category Fields on HD Ticket]** Given the HD Ticket DocType JSON has been updated, when any ticket form is rendered, then `category` (Link → HD Ticket Category) and `sub_category` (Link → HD Ticket Category) fields are present on the ticket. In Simple Mode (`itil_mode_enabled = 0`), these fields are visible. In ITIL Mode (`itil_mode_enabled = 1`), these fields are also visible (ITIL fields are additive, not exclusive).

4. **[Cascading Sub-category Filter]** Given an agent opens a ticket form and selects a value for the `category` field, when the `category` field changes, then the `sub_category` dropdown is dynamically filtered to show only HD Ticket Category records whose `parent_category` equals the selected category. If `category` is cleared, the `sub_category` field is also cleared and its filter is removed.

5. **[Category Hierarchy Example — Billing]** Given a category hierarchy exists (e.g., "Billing" as parent with children "Invoice Dispute" and "Refund Request"), when an agent selects Category "Billing" on a ticket, then the Sub-category dropdown shows only "Invoice Dispute" and "Refund Request" (not other top-level categories or unrelated sub-categories).

6. **[category_required_on_resolution Setting]** Given an administrator opens HD Settings, when they enable the `category_required_on_resolution` checkbox, then the setting is saved. When the checkbox is disabled (default), no category enforcement occurs on resolution.

7. **[Category Validation on Resolution]** Given `category_required_on_resolution` is enabled in HD Settings, when an agent attempts to resolve a ticket (sets status to "Resolved" or "Closed") without a `category` set, then a `frappe.ValidationError` is raised server-side with a clear message (e.g., "Category is required before resolving a ticket."), and the resolution is prevented until category is provided.

8. **[No Validation When Setting Disabled]** Given `category_required_on_resolution` is disabled in HD Settings (default state), when an agent resolves a ticket without a category, then no validation error is raised and the ticket resolves normally. This ensures backward compatibility.

9. **[sub_category Must Belong to Selected category]** Given both `category` and `sub_category` are set on a ticket, when the ticket is saved (server-side validate hook), then the server verifies that the selected `sub_category`'s `parent_category` matches the selected `category`. If they do not match, a `frappe.ValidationError` is raised.

10. **[Default Category Seed Data]** Given a fresh installation or initial migration patch run, when the seed data patch executes, then at least 5 default top-level categories are created (e.g., "Hardware", "Software", "Network", "Access & Accounts", "Billing") each with at least 2 sub-categories, providing immediate usability out of the box.

11. **[Migration Patch for Schema Changes]** Given a pre-existing helpdesk installation, when the Phase 1 migration patch for Story 1.3 runs, then: (a) `category` and `sub_category` columns are present on `tabHD Ticket`, and (b) `category_required_on_resolution` is present on the HD Settings singleton — all without data loss or errors on existing ticket records.

12. **[Unit Tests — Category Hierarchy and Validation]** Given the categorization implementation, when the test suite runs, then unit tests cover: HD Ticket Category DocType CRUD, self-referential validation rejection, cascading filter logic (sub_category filtered by parent), `category_required_on_resolution` enforcement (enabled and disabled cases), sub_category/category mismatch server-side validation, and the seed data migration patch. Minimum 80% coverage on new backend code (NFR-M-01).

## Tasks / Subtasks

- [ ] Task 1 — Create HD Ticket Category DocType (AC: #1, #2)
  - [ ] 1.1 Create directory `helpdesk/helpdesk/doctype/hd_ticket_category/`
  - [ ] 1.2 Create `helpdesk/helpdesk/doctype/hd_ticket_category/__init__.py` (empty)
  - [ ] 1.3 Create `helpdesk/helpdesk/doctype/hd_ticket_category/hd_ticket_category.json` with the following fields:
    - `name` field (auto-named by title using `autoname: "field:category_name"` or `autoname: "prompt"`)
    - `category_name` (Data, mandatory, label "Category Name") — the human-readable name
    - `parent_category` (Link → "HD Ticket Category", optional, label "Parent Category")
    - `description` (Small Text, optional)
    - `is_active` (Check, default 1, label "Is Active")
    - Set `title_field: "category_name"`, `search_fields: "category_name"`, `sort_field: "category_name"`, `sort_order: "ASC"`
    - `in_list_view: 1` for `category_name`, `parent_category`, `is_active`
    - Standard Frappe DocType metadata: `module: "Helpdesk"`, permissions for HD Admin/System Manager (all), HD Agent (read)
  - [ ] 1.4 Create `helpdesk/helpdesk/doctype/hd_ticket_category/hd_ticket_category.py` controller with:
    - `validate(self)` method that checks for self-referential `parent_category` (if `self.name == self.parent_category`, raise `frappe.ValidationError`)
    - Ensure `parent_category` link target is different from self even during creation (check `self.category_name` vs linked doc's `category_name`)
  - [ ] 1.5 Create `helpdesk/helpdesk/doctype/hd_ticket_category/test_hd_ticket_category.py` (stub — full tests in Task 7)

- [ ] Task 2 — Add `category` and `sub_category` Link fields to HD Ticket DocType JSON (AC: #3)
  - [ ] 2.1 Open `helpdesk/helpdesk/doctype/hd_ticket/hd_ticket.json`
  - [ ] 2.2 Add `category` field: `fieldtype: "Link"`, `options: "HD Ticket Category"`, `label: "Category"`, `fieldname: "category"`, `in_list_view: 0`, `search_index: 1`
  - [ ] 2.3 Add `sub_category` field: `fieldtype: "Link"`, `options: "HD Ticket Category"`, `label: "Sub-category"`, `fieldname: "sub_category"`, `depends_on: "eval:doc.category"` (only relevant when category is set)
  - [ ] 2.4 Place both fields logically adjacent to the `priority` field in the field order (after impact/urgency per Story 1.2, following ITIL grouping convention)
  - [ ] 2.5 Verify the `hidden` attribute is NOT set on these fields (they should be visible in both Simple and ITIL modes per AC #3 — progressive disclosure applies to impact/urgency per Story 1.1, not to category)

- [ ] Task 3 — Implement cascading sub_category filter (client script) (AC: #4, #5)
  - [ ] 3.1 Open `helpdesk/helpdesk/doctype/hd_ticket/hd_ticket.js`
  - [ ] 3.2 Add `onload` and `category` field `onchange` handler:
    ```javascript
    frappe.ui.form.on("HD Ticket", {
        category: function(frm) {
            if (frm.doc.category) {
                frm.set_query("sub_category", function() {
                    return {
                        filters: { parent_category: frm.doc.category }
                    };
                });
            } else {
                // Clear sub_category when category is cleared
                frm.set_value("sub_category", "");
                frm.set_query("sub_category", function() { return {}; });
            }
            frm.refresh_field("sub_category");
        }
    });
    ```
  - [ ] 3.3 Apply the same filter on form `onload`/`refresh` if `category` is already set (so editing existing tickets respects filter)
  - [ ] 3.4 Test manually: create "Billing" with children "Invoice Dispute" and "Refund Request"; verify only those appear when Billing is selected

- [ ] Task 4 — Implement frontend `TicketCategorySelect.vue` component (AC: #4, #5)
  - [ ] 4.1 Create `desk/src/components/ticket/TicketCategorySelect.vue`
  - [ ] 4.2 Component accepts props: `ticketId`, `category` (current value), `subCategory` (current value)
  - [ ] 4.3 Emits `update:category` and `update:subCategory` events on change
  - [ ] 4.4 Category dropdown: `createListResource` fetching HD Ticket Category where `parent_category` is null/empty and `is_active = 1`
  - [ ] 4.5 Sub-category dropdown: `createListResource` fetching HD Ticket Category where `parent_category = selectedCategory` and `is_active = 1`; re-fetches reactively on category change
  - [ ] 4.6 When category changes, clear sub-category value and re-fetch sub-category list
  - [ ] 4.7 Follow existing frappe-ui `FormControl` pattern used elsewhere in the ticket form components

- [ ] Task 5 — Add `category_required_on_resolution` field to HD Settings (AC: #6, #7, #8)
  - [ ] 5.1 Open `helpdesk/helpdesk/doctype/hd_settings/hd_settings.json`
  - [ ] 5.2 Add `category_required_on_resolution` field: `fieldtype: "Check"`, `default: 0`, `label: "Category required on resolution"`, placed in the ITIL settings section (near `itil_mode_enabled`)
  - [ ] 5.3 Open `helpdesk/helpdesk/doctype/hd_settings/hd_settings.py` — no additional validate logic needed here (validation is on HD Ticket side)

- [ ] Task 6 — Implement server-side validate hook for category enforcement and sub_category integrity (AC: #7, #8, #9)
  - [ ] 6.1 Open `helpdesk/helpdesk/doctype/hd_ticket/hd_ticket.py` (or `helpdesk/helpdesk/overrides/hd_ticket.py` — follow existing pattern)
  - [ ] 6.2 Implement `validate_category(doc, method=None)` function:
    ```python
    def validate_category(doc, method=None):
        # AC #9: Verify sub_category belongs to selected category
        if doc.sub_category and doc.category:
            parent = frappe.db.get_value(
                "HD Ticket Category", doc.sub_category, "parent_category"
            )
            if parent != doc.category:
                frappe.throw(
                    frappe._("Sub-category '{0}' does not belong to Category '{1}'.").format(
                        doc.sub_category, doc.category
                    ),
                    frappe.ValidationError
                )
        # AC #7, #8: Category required on resolution
        resolution_statuses = {"Resolved", "Closed"}
        if doc.status in resolution_statuses:
            required = frappe.db.get_single_value(
                "HD Settings", "category_required_on_resolution"
            )
            if required and not doc.category:
                frappe.throw(
                    frappe._("Category is required before resolving a ticket."),
                    frappe.ValidationError
                )
    ```
  - [ ] 6.3 Register `validate_category` in `helpdesk/hooks.py` under `doc_events["HD Ticket"]["validate"]` (in addition to existing hooks, not replacing them)

- [ ] Task 7 — Write unit tests (AC: #12)
  - [ ] 7.1 Create `helpdesk/helpdesk/doctype/hd_ticket_category/test_hd_ticket_category.py`:
    - `test_create_top_level_category` — create a category without parent_category; assert saved successfully
    - `test_create_sub_category` — create a category with valid parent_category; assert saved successfully
    - `test_self_referential_rejected` — attempt to set `parent_category` to self; assert `frappe.ValidationError`
    - `test_is_active_default_true` — create category without `is_active`; assert it defaults to 1
  - [ ] 7.2 Open (or create) `helpdesk/helpdesk/doctype/hd_ticket/test_hd_ticket.py`:
    - `test_category_required_on_resolution_enabled` — set `category_required_on_resolution = 1` in HD Settings; attempt to resolve ticket without category; assert `frappe.ValidationError` raised
    - `test_category_required_on_resolution_disabled` — set `category_required_on_resolution = 0`; resolve ticket without category; assert no error (backward compat)
    - `test_sub_category_mismatch_rejected` — set category="Billing", sub_category from "Network" children; assert `frappe.ValidationError`
    - `test_sub_category_valid_accepted` — set category="Billing", sub_category="Invoice Dispute" (child of Billing); assert no error
    - `test_no_category_no_sub_category_resolves_ok_when_disabled` — basic happy path with setting disabled
  - [ ] 7.3 All tests use `addCleanup` to restore `category_required_on_resolution` to 0 in HD Settings
  - [ ] 7.4 All tests use test-created category fixtures (do NOT rely on seed data being present during test run)

- [ ] Task 8 — Create migration patch and default category seed data (AC: #10, #11)
  - [ ] 8.1 Confirm `helpdesk/patches/v1_phase1/` directory exists (created in Story 1.1); create if absent
  - [ ] 8.2 Create `helpdesk/patches/v1_phase1/add_category_fields_to_hd_ticket.py`:
    ```python
    def execute():
        """Add category and sub_category fields to tabHD Ticket."""
        import frappe
        if not frappe.db.has_column("HD Ticket", "category"):
            frappe.db.add_column("HD Ticket", "category", "varchar(140)")
        if not frappe.db.has_column("HD Ticket", "sub_category"):
            frappe.db.add_column("HD Ticket", "sub_category", "varchar(140)")
        if not frappe.db.has_column("HD Settings", "category_required_on_resolution"):
            frappe.db.add_column("HD Settings", "category_required_on_resolution", "int(1) default 0")
    ```
  - [ ] 8.3 Create `helpdesk/patches/v1_phase1/create_default_categories.py`:
    ```python
    def execute():
        """Seed default HD Ticket Categories if none exist."""
        import frappe
        if frappe.db.count("HD Ticket Category") > 0:
            return  # Skip if categories already exist
        default_categories = {
            "Hardware": ["Laptop / Desktop", "Printer / Scanner", "Peripheral Device"],
            "Software": ["Application Error", "Installation / Upgrade", "License Issue"],
            "Network": ["Connectivity Issue", "VPN Access", "Wi-Fi Problem"],
            "Access & Accounts": ["Password Reset", "New User Access", "Permission Request"],
            "Billing": ["Invoice Dispute", "Refund Request", "Subscription Change"],
        }
        for parent_name, children in default_categories.items():
            if not frappe.db.exists("HD Ticket Category", parent_name):
                parent = frappe.get_doc({
                    "doctype": "HD Ticket Category",
                    "category_name": parent_name,
                    "is_active": 1,
                })
                parent.insert(ignore_permissions=True)
            for child_name in children:
                if not frappe.db.exists("HD Ticket Category", child_name):
                    frappe.get_doc({
                        "doctype": "HD Ticket Category",
                        "category_name": child_name,
                        "parent_category": parent_name,
                        "is_active": 1,
                    }).insert(ignore_permissions=True)
        frappe.db.commit()
    ```
  - [ ] 8.4 Register both patches in `helpdesk/patches.txt` in order (after Story 1.2 patch entry):
    ```
    helpdesk.patches.v1_phase1.add_category_fields_to_hd_ticket
    helpdesk.patches.v1_phase1.create_default_categories
    ```

## Dev Notes

### Architecture Patterns

- **New DocType — HD Ticket Category:** This is one of the 10 new DocTypes defined in ADR-02. It provides the multi-level categorization tree for FR-IM-02. The DocType lives at `helpdesk/helpdesk/doctype/hd_ticket_category/` following the standard structure: `__init__.py`, `hd_ticket_category.json`, `hd_ticket_category.py`, `test_hd_ticket_category.py`. [Source: architecture.md#ADR-02]

- **Extend HD Ticket (ADR-01):** The `category` and `sub_category` fields are added directly to HD Ticket DocType JSON — not via Custom Fields (AR-04). Both are Link fields targeting HD Ticket Category. The architecture explicitly lists:
  ```
  HD Ticket
  ├── category → HD Ticket Category (Link)
  └── sub_category → HD Ticket Category (Link, filtered by category)
  ```
  [Source: architecture.md#ADR-01, ADR-02]

- **Cascading Filter Pattern (Frappe):** The standard Frappe client-script pattern for linked field filtering is `frm.set_query("fieldname", function() { return { filters: {...} }; })`. This is sufficient for the Frappe form (used in backend/legacy views). The Vue-based desk frontend needs its own reactive filtering via `TicketCategorySelect.vue`. Both must be implemented — the Frappe form is used for admin DocType editing, while the Vue desk is the primary agent UI. [Source: architecture.md#ADR-09]

- **TicketCategorySelect.vue Component:** The architecture document explicitly calls out this component:
  ```
  desk/src/components/ticket/
  └── TicketCategorySelect.vue  # Cascading category/sub-category
  ```
  Use `createListResource` for data fetching (existing SWR-like pattern) and follow the frappe-ui `FormControl` component structure. [Source: architecture.md#ADR-09]

- **Categories Settings Page:** The architecture defines a dedicated categories management page:
  ```
  /helpdesk/settings/categories → desk/src/pages/settings/Categories.vue
  ```
  This page allows admins to manage the category hierarchy. If not implemented in this story, note it as a follow-up. [Source: architecture.md#ADR-09]

- **Validate Hook Registration:** The `validate_category` function must be registered in `hooks.py` under `doc_events["HD Ticket"]["validate"]`. Multiple hooks can be chained as a list:
  ```python
  doc_events = {
      "HD Ticket": {
          "validate": [
              "helpdesk.helpdesk.overrides.hd_ticket.validate_priority_matrix",  # Story 1.2
              "helpdesk.helpdesk.overrides.hd_ticket.validate_category",          # This story
          ],
      }
  }
  ```
  Check whether the existing Story 1.1/1.2 registration uses a list or single string — convert to list if needed. [Source: architecture.md#ADR-01]

- **HD Settings Singleton Pattern:** Access via `frappe.db.get_single_value("HD Settings", "category_required_on_resolution")` for the boolean check. Never use `frappe.get_doc("HD Settings", "HD Settings")` with a name argument. [Source: story-1.2 Dev Notes]

- **ITIL Feature Flag (NFR-M-04):** Unlike impact/urgency fields (which are hidden in Simple Mode), category and sub-category are useful in BOTH Simple and ITIL modes for routing and reporting. Therefore, do NOT gate these fields behind `itil_mode_enabled`. The `category_required_on_resolution` setting is its own independent toggle. [Source: epics.md#NFR-M-04, architecture.md#ADR-03]

- **Progressive Disclosure (UX-DR-01):** Per UX spec, ITIL fields (impact, urgency, category) use progressive disclosure — but "hidden in Simple Mode" primarily refers to impact and urgency. Category is part of ITIL enrichment but serves general routing purposes. Confirm with UX spec whether category should be hidden in Simple Mode. The epics AC (Story 1.3) does not gate on `itil_mode_enabled`, so implement it as always visible unless there is explicit contrary UX guidance. [Source: epics.md#UX-DR-01]

- **Resolution Status Values:** The Frappe Helpdesk likely uses "Resolved" and/or "Closed" as terminal statuses. Confirm the exact string values by checking `helpdesk/helpdesk/doctype/hd_ticket/hd_ticket.json` for the `status` Select field options. The validate hook must target the correct status strings. Common values: `"Resolved"`, `"Closed"`.

- **Patch Safety:** Both migration patches must be idempotent — safe to run multiple times. Use `frappe.db.has_column()` before `add_column()` and `frappe.db.exists()` before creating category records. [Source: architecture.md, AR-05]

- **Naming Autoname:** For HD Ticket Category, use `autoname: "field:category_name"` if category names are globally unique (recommended for simplicity), or `autoname: "prompt"` to let admins set explicit IDs. Using `field:category_name` means the Frappe `name` (primary key) equals `category_name`, simplifying link lookups. This is the recommended approach here since category names should be unique.

### Files to Create / Modify

| Action | Path | Notes |
|--------|------|-------|
| Create | `helpdesk/helpdesk/doctype/hd_ticket_category/__init__.py` | Empty init file |
| Create | `helpdesk/helpdesk/doctype/hd_ticket_category/hd_ticket_category.json` | New DocType schema |
| Create | `helpdesk/helpdesk/doctype/hd_ticket_category/hd_ticket_category.py` | Controller with self-ref validation |
| Create | `helpdesk/helpdesk/doctype/hd_ticket_category/test_hd_ticket_category.py` | Unit tests for DocType |
| Modify | `helpdesk/helpdesk/doctype/hd_ticket/hd_ticket.json` | Add `category` and `sub_category` Link fields |
| Modify | `helpdesk/helpdesk/doctype/hd_ticket/hd_ticket.js` | Add cascading filter client script |
| Modify | `helpdesk/helpdesk/doctype/hd_ticket/hd_ticket.py` (or `overrides/hd_ticket.py`) | Add `validate_category` function |
| Create/Modify | `helpdesk/helpdesk/doctype/hd_ticket/test_hd_ticket.py` | Tests for category validation on resolution |
| Modify | `helpdesk/helpdesk/doctype/hd_settings/hd_settings.json` | Add `category_required_on_resolution` Check field |
| Modify | `helpdesk/hooks.py` | Register `validate_category` in `doc_events["HD Ticket"]["validate"]` |
| Create | `helpdesk/patches/v1_phase1/add_category_fields_to_hd_ticket.py` | Migration patch for schema |
| Create | `helpdesk/patches/v1_phase1/create_default_categories.py` | Seed data patch |
| Modify | `helpdesk/patches.txt` | Register both new patches in order after Story 1.2 entries |
| Create | `desk/src/components/ticket/TicketCategorySelect.vue` | Vue cascading category selector component |
| Create (optional) | `desk/src/pages/settings/Categories.vue` | Admin category hierarchy management page |

### Testing Standards

- Minimum **80% unit test coverage** on all new backend logic (NFR-M-01).
- Use `frappe.tests.utils.FrappeTestCase` as the base test class.
- All tests must be self-contained: use `addCleanup` or `setUp`/`tearDown` to restore `category_required_on_resolution` to 0 in HD Settings after each test.
- Category fixture records created in tests should use `frappe.get_doc(...).insert(ignore_permissions=True)` and cleaned up with `frappe.delete_doc(...)` in cleanup.
- Run DocType-specific tests with:
  - `bench --site <site> run-tests --module helpdesk.helpdesk.doctype.hd_ticket_category.test_hd_ticket_category`
  - `bench --site <site> run-tests --module helpdesk.helpdesk.doctype.hd_ticket.test_hd_ticket`

### Constraints

- Do NOT use Custom Fields — modify DocType JSON files directly (AR-04).
- Do NOT break existing ticket behavior — `validate_category` must silently pass when `category` is not set and `category_required_on_resolution` is disabled (AC #8).
- Patch files must be idempotent — safe to run on a fresh install or on an existing install (AR-05).
- All user-facing validation messages must use `frappe._()` for Python i18n and `__()` in JavaScript.
- The `parent_category` Link on HD Ticket Category points to `HD Ticket Category` itself (self-referential Link field) — this is valid in Frappe and requires no special treatment in the JSON schema.
- `sub_category` can only be set if `category` is set first — enforce both client-side (hide/clear) and server-side (validate_category check).

### Project Structure Notes

- **Depends on Story 1.1** for: `itil_mode_enabled` flag in HD Settings, and the ITIL fields client script pattern in `hd_ticket.js`. Confirm Story 1.1 is merged before starting Task 3.
- **Depends on Story 1.2** for: existing `doc_events["HD Ticket"]["validate"]` hook registration pattern. Extend the hooks list rather than replacing it.
- **HD Ticket Category** is one of the 10 new DocTypes listed in ADR-02. It is the only new DocType in this story.
- **Patch Sequencing:** `add_category_fields_to_hd_ticket` must run before `create_default_categories` (the seed data patch requires the DocType to exist). Both must run after Story 1.1 and 1.2 patches.
- **Categories Settings Page** (`desk/src/pages/settings/Categories.vue`) is referenced in the architecture but is a stretch goal for this story — the DocType's built-in Frappe list view is sufficient for MVP. Implement if time permits; otherwise create as a follow-up task.
- **No New API Modules:** This story does not require a new `helpdesk/api/` module. All category interactions go through standard Frappe DocType CRUD REST (`/api/resource/HD Ticket Category`) and the `validate` hook on HD Ticket.

### References

- Story 1.3 acceptance criteria: [Source: _bmad-output/planning-artifacts/epics.md#Story 1.3]
- FR-IM-02 (Multi-level categorization, required on resolution): [Source: _bmad-output/planning-artifacts/epics.md#Functional Requirements]
- ADR-01 (Extend HD Ticket): [Source: _bmad-output/planning-artifacts/architecture.md#ADR-01]
- ADR-02 (New DocTypes — HD Ticket Category listed): [Source: _bmad-output/planning-artifacts/architecture.md#ADR-02]
- ADR-09 (Frontend — TicketCategorySelect.vue, Categories settings page): [Source: _bmad-output/planning-artifacts/architecture.md#ADR-09]
- NFR-M-01 (80% unit test coverage): [Source: _bmad-output/planning-artifacts/epics.md#Non-Functional Requirements]
- NFR-M-04 (ITIL features toggleable via HD Settings): [Source: _bmad-output/planning-artifacts/epics.md#Non-Functional Requirements]
- AR-04 (Modify DocType JSON, not Custom Fields): [Source: _bmad-output/planning-artifacts/epics.md#Additional Requirements]
- AR-05 (Migration patches in `helpdesk/patches/v1_phase1/`): [Source: _bmad-output/planning-artifacts/epics.md#Additional Requirements]
- UX-DR-01 (Progressive disclosure for ITIL fields): [Source: _bmad-output/planning-artifacts/epics.md#UX Design Requirements]
- HD Ticket DocType files: `helpdesk/helpdesk/doctype/hd_ticket/`
- HD Settings DocType files: `helpdesk/helpdesk/doctype/hd_settings/`
- Story 1.1 (prerequisite — feature flags): [Source: _bmad-output/implementation-artifacts/story-1.1-feature-flag-infrastructure-for-itil-mode.md]
- Story 1.2 (prerequisite — impact/urgency hooks): [Source: _bmad-output/implementation-artifacts/story-1.2-impact-and-urgency-fields-with-priority-matrix.md]

## Dev Agent Record

### Agent Model Used

Claude Sonnet 4.5 (create-story workflow)

### Debug Log References

_None — story creation phase_

### Completion Notes List

_To be filled by implementing dev agent_

### File List

_To be filled by implementing dev agent upon completion_
