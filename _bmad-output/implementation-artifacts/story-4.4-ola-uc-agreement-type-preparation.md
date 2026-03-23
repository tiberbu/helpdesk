# Story 4.4: OLA/UC Agreement Type Preparation

Status: ready-for-dev

## Story

As an administrator,
I want to tag SLA agreements as SLA, OLA, or UC type,
so that the system is prepared for full OLA/UC tracking in Phase 2 and agreements are clearly classified in the current list view.

## Acceptance Criteria

1. **[agreement_type Select Field on HD Service Level Agreement]** Given an administrator opens an HD Service Level Agreement form, when they view the record, then: (a) a new `agreement_type` Select field is present with options `"SLA"`, `"OLA"`, `"UC"`; (b) the field defaults to `"SLA"` for all new records; (c) the field label is "Agreement Type"; (d) legacy SLA records created before this migration show `"SLA"` as their agreement type (migrated via patch with `"SLA"` as default for NULL values); (e) the field is placed in the agreement details section near `start_date`/`end_date`.

2. **[Agreement Type Badge on SLA List View]** Given the agreement type is set to any value ("SLA", "OLA", or "UC"), when the administrator views the HD Service Level Agreement list page, then: (a) the `agreement_type` field is visible as a column in the list view (`in_list_view: 1`); (b) SLA records without a value (legacy) show "SLA" (migrated default); (c) the column is labelled "Agreement Type" and sortable.

3. **[internal_team Link Field — Visible When OLA]** Given the `internal_team` Link field (linked to `HD Team`) has been added to HD Service Level Agreement, when an administrator views an SLA record: (a) if `agreement_type` is `"OLA"`, the `internal_team` field is visible; (b) if `agreement_type` is `"SLA"` or `"UC"`, the `internal_team` field is hidden; (c) the field label is "Internal Team"; (d) the field is optional (not required); (e) the conditional visibility is enforced via a client script (`hd_service_level_agreement.js`) using `frappe.ui.form.on` `refresh` and field change handlers.

4. **[vendor Data Field — Visible When UC]** Given the `vendor` Data field has been added to HD Service Level Agreement, when an administrator views an SLA record: (a) if `agreement_type` is `"UC"`, the `vendor` field is visible; (b) if `agreement_type` is `"SLA"` or `"OLA"`, the `vendor` field is hidden; (c) the field label is "Vendor"; (d) the field is optional (not required); (e) the same client script from AC #3 controls this conditional visibility as part of the same `toggle_visibility` function pattern.

5. **[DocType JSON Modifications — No Custom Fields]** Given the three new fields (`agreement_type`, `internal_team`, `vendor`) are added to the HD Service Level Agreement DocType, when the DocType JSON file at `helpdesk/helpdesk/doctype/hd_service_level_agreement/hd_service_level_agreement.json` is inspected: (a) all three fields appear in the `"fields"` array and `"field_order"` list; (b) fields are added via DocType JSON modification (AR-04 — not via Custom Fields tool); (c) `agreement_type` has `"fieldtype": "Select"`, `"options": "SLA\nOLA\nUC"`, `"default": "SLA"`, `"in_list_view": 1`; (d) `internal_team` has `"fieldtype": "Link"`, `"options": "HD Team"`; (e) `vendor` has `"fieldtype": "Data"`.

6. **[Migration Patch — Existing Records Default to SLA]** Given the migration patch at `helpdesk/patches/v1_phase1/add_sla_agreement_type.py` exists and runs successfully, when the patch is executed on a site with existing SLA records: (a) all HD Service Level Agreement records where `agreement_type IS NULL` or `agreement_type = ""` are updated to `agreement_type = "SLA"`; (b) the patch is idempotent (safe to run multiple times — skips records already having a valid agreement_type value); (c) the patch is registered in `helpdesk/patches.txt` so Frappe runs it during `bench migrate`; (d) patch uses `frappe.db.sql` or `frappe.db.set_value` bulk-update pattern (not per-record Python loops for performance).

7. **[Unit Tests — Field Visibility Logic and Migration Patch]** Given the unit test file for this story exists, when the tests run, then at minimum the following pass with 80%+ coverage (NFR-M-01): (a) `test_agreement_type_default_is_sla` — create a new HD Service Level Agreement without setting `agreement_type`; assert `doc.agreement_type == "SLA"`; (b) `test_agreement_type_select_options` — assert `agreement_type` field options include exactly `"SLA"`, `"OLA"`, `"UC"` and no others; (c) `test_migration_patch_sets_sla_default` — create two test SLA records with null `agreement_type`, run the patch function directly, assert both records now have `agreement_type = "SLA"`; (d) `test_migration_patch_is_idempotent` — run the patch twice; assert no error and records retain correct values; (e) `test_internal_team_field_exists` — assert the `internal_team` field exists on the DocType meta; (f) `test_vendor_field_exists` — assert the `vendor` field exists on the DocType meta; (g) `test_api_requires_permission` — attempt to read HD Service Level Agreement without login; assert `frappe.PermissionError`.

## Tasks / Subtasks

- [ ] Task 1 — Modify HD Service Level Agreement DocType JSON to add new fields (AC: #1, #5)
  - [ ] 1.1 Open `helpdesk/helpdesk/doctype/hd_service_level_agreement/hd_service_level_agreement.json`
  - [ ] 1.2 Add `agreement_type` Select field to the `"fields"` array:
        ```json
        {
          "fieldname": "agreement_type",
          "fieldtype": "Select",
          "label": "Agreement Type",
          "options": "SLA\nOLA\nUC",
          "default": "SLA",
          "in_list_view": 1,
          "in_standard_filter": 1
        }
        ```
  - [ ] 1.3 Add `internal_team` Link field to the `"fields"` array:
        ```json
        {
          "fieldname": "internal_team",
          "fieldtype": "Link",
          "label": "Internal Team",
          "options": "HD Team"
        }
        ```
  - [ ] 1.4 Add `vendor` Data field to the `"fields"` array:
        ```json
        {
          "fieldname": "vendor",
          "fieldtype": "Data",
          "label": "Vendor"
        }
        ```
  - [ ] 1.5 Add `"agreement_type"`, `"internal_team"`, `"vendor"` to the `"field_order"` list — place `"agreement_type"` after `"end_date"` in the `agreement_details_section`, and `"internal_team"` and `"vendor"` after `"agreement_type"` (use a Column Break if needed to maintain form layout)
  - [ ] 1.6 Verify the JSON is valid (no syntax errors) by running `python3 -c "import json; json.load(open('hd_service_level_agreement.json'))"` after editing

- [ ] Task 2 — Create Client Script for Conditional Field Visibility (AC: #3, #4)
  - [ ] 2.1 Open (or create) `helpdesk/helpdesk/doctype/hd_service_level_agreement/hd_service_level_agreement.js`
  - [ ] 2.2 Implement a `toggle_agreement_type_fields(frm)` helper function that reads `frm.doc.agreement_type` and sets field visibility:
        ```javascript
        function toggle_agreement_type_fields(frm) {
            const agreement_type = frm.doc.agreement_type;
            frm.toggle_display("internal_team", agreement_type === "OLA");
            frm.toggle_display("vendor", agreement_type === "UC");
        }
        ```
  - [ ] 2.3 Register the helper on the `refresh` event so it runs when the form loads:
        ```javascript
        frappe.ui.form.on("HD Service Level Agreement", {
            refresh(frm) {
                toggle_agreement_type_fields(frm);
            },
            agreement_type(frm) {
                toggle_agreement_type_fields(frm);
            }
        });
        ```
  - [ ] 2.4 Verify that when `agreement_type` is `"SLA"` (the default): both `internal_team` and `vendor` are hidden; when `"OLA"`: only `internal_team` is shown; when `"UC"`: only `vendor` is shown

- [ ] Task 3 — Create Migration Patch (AC: #6)
  - [ ] 3.1 Create directory `helpdesk/patches/v1_phase1/` if it does not already exist (check existing stories — Story 4.1 may have created it)
  - [ ] 3.2 Create `helpdesk/patches/v1_phase1/__init__.py` (empty file) if it does not exist
  - [ ] 3.3 Create `helpdesk/patches/v1_phase1/add_sla_agreement_type.py` with the following content:
        ```python
        import frappe


        def execute():
            """Set agreement_type = 'SLA' for all existing HD Service Level Agreement
            records that have a NULL or empty agreement_type value.
            This patch is idempotent — safe to run multiple times.
            """
            # Bulk update using frappe.db for performance (avoids per-record Python loop)
            frappe.db.sql(
                """
                UPDATE `tabHD Service Level Agreement`
                SET agreement_type = 'SLA'
                WHERE agreement_type IS NULL OR agreement_type = ''
                """
            )
            frappe.db.commit()
        ```
  - [ ] 3.4 Open `helpdesk/patches.txt` and add the patch entry on a new line:
        `helpdesk.patches.v1_phase1.add_sla_agreement_type`
        Place it after any existing `v1_phase1` patch entries (e.g., after `add_itil_fields_to_ticket` if present) to maintain correct migration order
  - [ ] 3.5 Verify `patches.txt` syntax by confirming the line matches the Python dotted module path exactly

- [ ] Task 4 — Write Unit Tests (AC: #7)
  - [ ] 4.1 Create `helpdesk/helpdesk/doctype/hd_service_level_agreement/test_hd_service_level_agreement_agreement_type.py` (or add to existing `test_hd_service_level_agreement.py` if it already exists — check first)
  - [ ] 4.2 Implement `test_agreement_type_default_is_sla`:
        ```python
        def test_agreement_type_default_is_sla(self):
            doc = frappe.get_doc({
                "doctype": "HD Service Level Agreement",
                "service_level": "_Test SLA Default",
                # agreement_type intentionally omitted
            })
            self.assertEqual(doc.agreement_type, "SLA")
        ```
  - [ ] 4.3 Implement `test_agreement_type_select_options`:
        ```python
        def test_agreement_type_select_options(self):
            meta = frappe.get_meta("HD Service Level Agreement")
            field = meta.get_field("agreement_type")
            self.assertIsNotNone(field)
            options = [opt.strip() for opt in field.options.split("\n") if opt.strip()]
            self.assertEqual(sorted(options), sorted(["SLA", "OLA", "UC"]))
        ```
  - [ ] 4.4 Implement `test_migration_patch_sets_sla_default` and `test_migration_patch_is_idempotent` — use `frappe.db.sql` to insert test records with NULL agreement_type, call `execute()` from the patch module, assert updated values, then call `execute()` again and assert no errors
  - [ ] 4.5 Implement `test_internal_team_field_exists` and `test_vendor_field_exists` — use `frappe.get_meta("HD Service Level Agreement").get_field(fieldname)` and assert not None
  - [ ] 4.6 Implement `test_api_requires_permission` — use `frappe.set_user("Guest")` and attempt to fetch a record; assert `frappe.PermissionError` is raised; restore user in `tearDown`
  - [ ] 4.7 Run tests to verify all pass:
        `bench --site <site> run-tests --module helpdesk.helpdesk.doctype.hd_service_level_agreement.test_hd_service_level_agreement_agreement_type`

- [ ] Task 5 — Verify DocType Changes and Run bench migrate (AC: #1, #2, #5, #6)
  - [ ] 5.1 Run `bench --site <site> migrate` to apply the DocType schema changes and the migration patch
  - [ ] 5.2 Confirm `agreement_type` column is present in `tabHD Service Level Agreement` via `bench --site <site> mariadb` → `DESCRIBE tabHD\ Service\ Level\ Agreement;`
  - [ ] 5.3 Confirm existing SLA records have `agreement_type = 'SLA'` post-migration
  - [ ] 5.4 Open the HD Service Level Agreement list in the browser and confirm the "Agreement Type" column appears in the list view
  - [ ] 5.5 Open an SLA form, change `agreement_type` between SLA/OLA/UC, and verify only the correct contextual field (internal_team or vendor) appears at each value

## Dev Notes

### Architecture Patterns

- **Informational-Only Phase 1 Scope (FR-SL-04):** The architecture explicitly states this story is "OLA/UC field preparation" — `agreement_type` is informational only in Phase 1. No routing logic, escalation rules, or separate SLA calculation tracks based on agreement type are implemented here. Phase 2 will build on this foundation. [Source: _bmad-output/planning-artifacts/epics.md#FR-SL-04, architecture.md#ADR-02]

- **DocType JSON Modification (Mandatory — AR-04):** All three new fields (`agreement_type`, `internal_team`, `vendor`) MUST be added directly to the DocType JSON file, NOT via Frappe's Custom Fields tool. This is because this is the app source code (not a customization layer). The DocType JSON is the canonical schema definition. [Source: _bmad-output/planning-artifacts/epics.md#AR-04]

- **HD Service Level Agreement DocType JSON Location:**
  ```
  helpdesk/helpdesk/helpdesk/doctype/hd_service_level_agreement/hd_service_level_agreement.json
  ```
  Note the nested `helpdesk/helpdesk/helpdesk/` path structure — the Frappe app module directory mirrors the app name. Verify this path before editing.

- **Existing DocType Structure (inspect before modifying):** The current `field_order` in the DocType JSON is:
  ```
  ["default_priority", "service_level", "column_break_2", "description", "enabled",
   "filters_section", "default_sla", "column_break_15", "condition", "condition_json",
   "agreement_details_section", "start_date", "column_break_7", "end_date",
   "response_and_resolution_time_section", "apply_sla_for_resolution", "priorities",
   "status_details", "default_ticket_status", "column_break_baqo", "ticket_reopen_status",
   "support_and_resolution_section_break", "holiday_list", "support_and_resolution"]
  ```
  Insert the new fields after `"end_date"` in the `agreement_details_section`. Suggested final order in that section: `"start_date"`, `"column_break_7"`, `"end_date"`, `"agreement_type"`, `"internal_team"`, `"vendor"`. Adding a `Column Break` between `agreement_type` and `internal_team`/`vendor` is optional for layout but not required.

- **Select Field Options Format (Frappe Convention):** Frappe Select fields store options as a newline-separated string in the JSON:
  ```json
  "options": "SLA\nOLA\nUC"
  ```
  The first option in the list is the default when `"default": "SLA"` is also set. Confirm this double-default pattern by inspecting another Select field in the codebase (e.g., `priority` on HD Ticket) to ensure the `"default"` key is used alongside `"options"`.

- **Client Script Conditional Visibility Pattern:** Frappe form client scripts use `frm.toggle_display(fieldname, show_boolean)` to show/hide fields. This is the standard idiomatic pattern — do NOT use `frm.set_df_property("fieldname", "hidden", 1)` directly as it is less reliable across form reloads. The `refresh` trigger fires on form load, and `agreement_type` trigger fires when the user changes the dropdown value.
  ```javascript
  // Standard pattern used across the codebase
  frappe.ui.form.on("HD Service Level Agreement", {
      refresh(frm) { toggle_agreement_type_fields(frm); },
      agreement_type(frm) { toggle_agreement_type_fields(frm); }
  });
  ```

- **Migration Patch Registration in patches.txt:** Frappe discovers patches via `helpdesk/patches.txt`. The format is one dotted Python module path per line. Check if `v1_phase1` entries already exist in `patches.txt` (earlier stories 4.1, 4.2, 4.3 may have added entries). Place the new patch after any existing `v1_phase1` entries:
  ```
  helpdesk.patches.v1_phase1.add_sla_agreement_type
  ```
  Frappe runs patches exactly once per site (tracked in `__PatchLog`). Running `bench migrate` applies pending patches automatically.

- **Patch Performance — Bulk SQL Update:** The migration patch uses raw SQL (`frappe.db.sql`) for the bulk update rather than iterating Python objects. This is necessary for performance if the site has many SLA records. Raw SQL is acceptable in migration patches (not in application logic per Enforcement Guideline #6). Always follow with `frappe.db.commit()`.

- **No hooks.py Changes Needed:** This story adds no scheduler events, doc_events, or new API endpoints. The `hd_service_level_agreement.js` client script is auto-discovered by Frappe via the DocType's associated `.js` file convention. No registration in `hooks.py` is required for client scripts.

- **No New DocTypes:** This story modifies one existing DocType only (`HD Service Level Agreement`). No new DocTypes are created. [Source: _bmad-output/planning-artifacts/architecture.md#ADR-02]

- **Link Field for internal_team — HD Team DocType:** The `internal_team` field links to `HD Team` (the existing team management DocType). Verify the exact DocType name by checking `helpdesk/helpdesk/doctype/hd_team/` exists. If the DocType is named differently, adjust the `"options"` value accordingly.

- **i18n:** Field labels in the DocType JSON (`"label": "Agreement Type"`, `"label": "Internal Team"`, `"label": "Vendor"`) are automatically handled by Frappe's translation layer. In the client script, if any user-facing messages are shown via `frappe.msgprint`, wrap them in `__("...")`. [Source: _bmad-output/planning-artifacts/architecture.md#Enforcement Guideline #3]

- **List View Column (in_list_view: 1):** Setting `"in_list_view": 1` on `agreement_type` makes it appear as a column in the Frappe list view automatically. The list view uses the raw field value ("SLA", "OLA", "UC") as text. If a badge/color display is desired, a `formatters` override in the List View JS would be needed — but for Phase 1 informational purposes, plain text is acceptable. The `in_standard_filter: 1` flag also adds it to the quick filter bar for easy filtering by agreement type.

- **Story Dependencies:** This story is self-contained with no blocking dependencies on other Sprint 11-12 stories. It modifies the existing `HD Service Level Agreement` DocType which is foundational infrastructure present since the original Frappe Helpdesk codebase. Stories 4.1, 4.2, and 4.3 do NOT need to be complete before starting this story — they work on separate aspects of the SLA system.

### Files to Create / Modify

| Action | Path | Notes |
|--------|------|-------|
| Modify | `helpdesk/helpdesk/doctype/hd_service_level_agreement/hd_service_level_agreement.json` | Add `agreement_type` (Select), `internal_team` (Link→HD Team), `vendor` (Data) fields; update `field_order` |
| Create/Modify | `helpdesk/helpdesk/doctype/hd_service_level_agreement/hd_service_level_agreement.js` | Add `toggle_agreement_type_fields()` and form event handlers for `refresh` and `agreement_type` change |
| Create | `helpdesk/patches/v1_phase1/add_sla_agreement_type.py` | Migration patch — set `agreement_type = 'SLA'` for all existing NULL records |
| Create | `helpdesk/patches/v1_phase1/__init__.py` | Empty init file (if not already created by earlier stories) |
| Modify | `helpdesk/patches.txt` | Register `helpdesk.patches.v1_phase1.add_sla_agreement_type` |
| Create | `helpdesk/helpdesk/doctype/hd_service_level_agreement/test_hd_service_level_agreement_agreement_type.py` | Unit tests for all 7 AC test scenarios (80%+ coverage) |

### Testing Standards

- Minimum 80% unit test coverage on all new backend Python code (NFR-M-01).
- Use `frappe.tests.utils.FrappeTestCase` as the base class for all Python test cases.
- For DocType field presence tests, use `frappe.get_meta("HD Service Level Agreement").get_field(fieldname)` — this reads the DocType definition directly without needing DB records.
- The migration patch test should use `frappe.db.sql` to manipulate test data directly (faster than creating full DocType documents with all required fields).
- Clean up test records in `tearDown` to avoid polluting the test database.
- Run backend tests with: `bench --site <site> run-tests --module helpdesk.helpdesk.doctype.hd_service_level_agreement.test_hd_service_level_agreement_agreement_type`

### Constraints

- **Phase 1 is informational only** — do NOT implement OLA/UC-specific SLA calculation logic, routing, or dashboards. The `agreement_type` field is purely a classification label for Phase 2 readiness.
- **Do NOT modify hooks.py** — no new events, triggers, or server-side handlers based on `agreement_type` are needed in Phase 1.
- **Do NOT create a new API module** — no new `@frappe.whitelist()` endpoints are needed for this story. The DocType's auto-generated REST API (`/api/resource/HD Service Level Agreement`) is sufficient.
- **All DocType changes via JSON only** (AR-04) — never use the Frappe web UI's Customize Form to add these fields.
- **Patch must use SQL for bulk update** — do not iterate records in Python for the migration (performance concern for large installs).
- **Do NOT set agreement_type as required** — it has a default of "SLA" but must remain optional to avoid breaking existing integrations.

### Project Structure Notes

- **patches/v1_phase1/ directory:** The architecture defines `helpdesk/patches/v1_phase1/` as the target directory for all Phase 1 migration patches (AR-05). Earlier stories (4.1 for `add_itil_fields_to_ticket`, 1.3 for `create_default_categories`) may have already created this directory. Check `ls helpdesk/patches/` before creating — use existing `__init__.py` if present.
- **SLA DocType path:** Note that the path is `helpdesk/helpdesk/helpdesk/doctype/...` (triple-nested due to Frappe app structure: `<app_name>/<app_module>/doctype/`). Always verify with `ls` before editing.
- **Client script auto-discovery:** Frappe automatically loads `hd_service_level_agreement.js` from the same DocType directory when the form is opened. No additional registration is required in `hooks.py` or anywhere else.
- **Story 4.4 in Sprint 11-12:** Per sprint-status.yaml, this story is scheduled in Sprint 11-12 alongside Epic 6 stories 6.2, 6.5 and Epic 5 stories 5.2, 5.3, 5.5. It is the final story in Epic 4 and has the smallest scope — estimated 1 developer-day.

### References

- FR-SL-04 (OLA/UC field preparation — agreement_type Select field on HD SLA, informational only in Phase 1): [Source: _bmad-output/planning-artifacts/epics.md#Functional Requirements]
- FR-SL-04 (Story 4.4 Acceptance Criteria — agreement_type field, internal_team Link, vendor Data, list badge): [Source: _bmad-output/planning-artifacts/epics.md#Story 4.4]
- AR-02 (All new DocTypes follow HD prefix — here: modifying existing HD SLA): [Source: _bmad-output/planning-artifacts/epics.md#Additional Requirements]
- AR-04 (All new fields added to existing DocTypes via DocType JSON modification — NOT Custom Fields): [Source: _bmad-output/planning-artifacts/epics.md#Additional Requirements]
- AR-05 (Migration patches in helpdesk/patches/v1_phase1/): [Source: _bmad-output/planning-artifacts/epics.md#Additional Requirements]
- NFR-M-01 (Minimum 80% unit test coverage on all new backend code): [Source: _bmad-output/planning-artifacts/epics.md#Non-Functional Requirements]
- NFR-M-04 (All ITIL features toggleable via HD Settings — agreement_type is passive, no Settings flag required): [Source: _bmad-output/planning-artifacts/epics.md#Non-Functional Requirements]
- ADR-02 (New DocType Schema — HD SLA gets agreement_type Select field): [Source: _bmad-output/planning-artifacts/architecture.md#ADR-02]
- Architecture Enforcement Guideline #7 (Add new fields to DocType JSON, not via Custom Field): [Source: _bmad-output/planning-artifacts/architecture.md#Enforcement Guidelines]
- HD Service Level Agreement DocType: `helpdesk/helpdesk/doctype/hd_service_level_agreement/`
- HD Team DocType: `helpdesk/helpdesk/doctype/hd_team/`
- patches.txt: `helpdesk/patches.txt`
- Sprint 11-12 assignment: [Source: _bmad-output/sprint-status.yaml]

## Dev Agent Record

### Agent Model Used

Claude Sonnet 4.5 (create-story workflow)

### Debug Log References

_None — story creation phase_

### Completion Notes List

_To be filled by implementing dev agent_

### File List

_To be filled by implementing dev agent upon completion_
