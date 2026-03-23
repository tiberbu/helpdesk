# Story 6.1: Custom Report Builder

Status: ready-for-dev

## Story

As a team manager,
I want to build custom reports by selecting data source, fields, filters, and grouping,
so that I get exactly the data I need without developer help.

## Acceptance Criteria

1. **[HD Custom Report DocType]** Given the HD Custom Report DocType is installed, when a developer inspects the schema, then the following fields exist: `report_name` (Data, required), `description` (Small Text), `data_source` (Select: "HD Ticket\nHD CSAT Response\nHD Article\nHD Time Entry"), `selected_fields` (JSON — list of field names), `filters` (JSON — array of filter conditions), `group_by` (JSON — array of up to 3 field names), `sort_by` (Data), `sort_order` (Select: "ASC\nDESC"), and `chart_type` (Select: "table\nbar\nline\npie"). The DocType follows the `HD` prefix naming convention (AR-02) and all fields are added directly to the DocType JSON, not via Custom Fields (AR-04).

2. **[Report List Page]** Given a manager navigates to `/helpdesk/reports`, when the page loads, then a list of all saved HD Custom Report records is displayed with name, description, data source, and last modified date columns, and a "New Report" button is visible.

3. **[Report Builder — Data Source Selection]** Given a manager opens `/helpdesk/reports/new`, when the page loads, then they can select a data source from the four supported options: HD Ticket, HD CSAT Response, HD Article, HD Time Entry. Upon selection, the available fields panel updates to show columns from the selected DocType.

4. **[Report Builder — Drag-and-Drop Fields]** Given a data source is selected, when the manager drags fields from the available fields panel into the selected fields area, then the selected fields list updates with the chosen columns and the report preview refreshes. Field order in the selected list is user-configurable via drag.

5. **[Report Builder — Filter Configuration]** Given a data source and fields are selected, when the manager adds a filter, then they can specify: field name, operator (equals, not_equals, contains, not_contains, greater_than, less_than, between, is_set, is_not_set), and value. Multiple filters can be added and are combined with AND logic. The filter configuration is stored as a JSON array.

6. **[Report Builder — Group By (up to 3 levels)]** Given the report configuration panel, when a manager sets group-by fields, then they can select up to 3 fields for hierarchical grouping. Attempting to add a 4th group-by field displays a validation message and is prevented.

7. **[Report Builder — Chart Type]** Given the report configuration, when the manager selects a chart type (bar, line, pie, table), then the preview panel renders the report using the selected visualization. The "table" type is the default and shows a paginated data grid.

8. **[Real-time Preview]** Given the report builder is open, when any configuration setting changes (data source, fields, filters, group-by, sort-by, chart type), then the report preview panel updates within 2 seconds without requiring a manual "Run" button click (debounced auto-execute on change with 500ms delay).

9. **[Save Report]** Given a completed report configuration, when the manager enters a report name and clicks "Save", then the HD Custom Report record is persisted to the database with all configuration fields, and the URL updates to `/helpdesk/reports/{report-id}` for reuse and sharing.

10. **[execute_report API]** Given a valid HD Custom Report record ID, when `helpdesk.api.reports.execute_report` is called with the report configuration, then the backend dynamically generates a `frappe.qb` query using the `data_source`, `selected_fields`, `filters`, `group_by`, and `sort_by` parameters, executes it, and returns paginated results with row count. No raw SQL is used (Enforcement Guideline #6).

11. **[Permission Enforcement]** Given a report execution request, when the API is called, then the backend verifies the caller has read permission on the target DocType (`frappe.has_permission(data_source, "read", throw=True)`), ensuring custom reports respect the Frappe permission model (NFR-SE-05). Internal notes communications are never exposed via report data.

12. **[Unit Tests]** Given the reports API implementation, when the test suite runs, then unit tests for `execute_report` (query generation, filter translation, group-by logic, permission enforcement) and data aggregation pass with minimum 80% code coverage (NFR-M-01).

13. **[Routes Registered]** Given the frontend router configuration, when the app loads, then routes `/helpdesk/reports` (ReportList) and `/helpdesk/reports/new` (ReportBuilder) and `/helpdesk/reports/:id` (ReportBuilder with loaded config) are all registered and navigable.

14. **[Report Store]** Given the Pinia store `report.ts` exists, when the report builder is active, then report configuration state (data source, fields, filters, group-by, chart type) is managed reactively in the store (ADR-11), enabling real-time preview updates and clean separation of state from UI.

## Tasks / Subtasks

- [ ] Task 1 — Create HD Custom Report DocType (AC: #1)
  - [ ] 1.1 Create directory `helpdesk/helpdesk/doctype/hd_custom_report/`
  - [ ] 1.2 Create `hd_custom_report/__init__.py` (empty)
  - [ ] 1.3 Create `hd_custom_report/hd_custom_report.json` with fields: `report_name` (Data, reqd), `description` (Small Text), `data_source` (Select, options: "HD Ticket\nHD CSAT Response\nHD Article\nHD Time Entry", reqd), `selected_fields` (JSON), `filters` (JSON), `group_by` (JSON), `sort_by` (Data), `sort_order` (Select, options: "ASC\nDESC", default: "DESC"), `chart_type` (Select, options: "table\nbar\nline\npie", default: "table"). Set `is_submittable: 0`, `track_changes: 1`, naming_rule: "By fieldname", autoname: `field:report_name`.
  - [ ] 1.4 Create `hd_custom_report/hd_custom_report.py` controller with `validate()` method that: (a) ensures `selected_fields` JSON is a valid list, (b) validates `group_by` has at most 3 elements, (c) validates `filters` is a valid array of condition objects, (d) validates `data_source` value is one of the 4 allowed DocTypes.
  - [ ] 1.5 Create `hd_custom_report/test_hd_custom_report.py` with unit tests for DocType validation (see Task 7).
  - [ ] 1.6 Create migration patch `helpdesk/patches/v1_phase1/create_hd_custom_report.py` with `execute()` function that safely registers the new DocType.
  - [ ] 1.7 Register patch in `helpdesk/patches.txt`.

- [ ] Task 2 — Implement `helpdesk/api/reports.py` (AC: #10, #11)
  - [ ] 2.1 Create `helpdesk/api/reports.py` with `@frappe.whitelist()` decorator.
  - [ ] 2.2 Implement `execute_report(report_id: str = None, data_source: str = None, selected_fields: str = None, filters: str = None, group_by: str = None, sort_by: str = None, sort_order: str = "DESC", chart_type: str = "table", page_length: int = 100, page: int = 1)`. When `report_id` is provided, load config from DB; otherwise use inline params.
  - [ ] 2.3 In `execute_report`: call `frappe.has_permission(data_source, "read", throw=True)` before any query.
  - [ ] 2.4 Implement `build_query(data_source, selected_fields, filters, group_by, sort_by, sort_order)` helper using `frappe.qb`. Map filter operators: `equals` → `==`, `not_equals` → `!=`, `contains` → `.like(f"%{v}%")`, `not_contains` → `.not_like(...)`, `greater_than` → `>`, `less_than` → `<`, `between` → `.between(a, b)`, `is_set` → `.isnotnull()`, `is_not_set` → `.isnull()`. Never construct raw SQL strings.
  - [ ] 2.5 Apply `group_by` fields to the query when present. Add COUNT(*) aggregate as `_count` column when group_by is set.
  - [ ] 2.6 Apply pagination: `limit(page_length).offset((page - 1) * page_length)`.
  - [ ] 2.7 Return `{"data": rows, "total_count": total, "page": page, "page_length": page_length, "columns": column_meta}`.
  - [ ] 2.8 Implement `get_available_fields(data_source: str)` endpoint that returns the list of fields (label, fieldname, fieldtype) for a given DocType using `frappe.get_meta(data_source).fields`, filtering to user-friendly fieldtypes only (Data, Select, Link, Date, Datetime, Int, Float, Check, Currency, Small Text).
  - [ ] 2.9 Implement `save_report(report_name, data_source, selected_fields, filters, group_by, sort_by, sort_order, chart_type, description="", report_id=None)` to create or update an HD Custom Report record.

- [ ] Task 3 — Create Pinia store `report.ts` (AC: #14)
  - [ ] 3.1 Create `desk/src/stores/report.ts` with reactive state: `dataSource`, `selectedFields`, `filters`, `groupBy`, `sortBy`, `sortOrder`, `chartType`, `previewData`, `isLoading`, `totalCount`.
  - [ ] 3.2 Implement `setDataSource(source)` action — resets `selectedFields`, `filters`, `groupBy` when source changes.
  - [ ] 3.3 Implement `addField(fieldname)` / `removeField(fieldname)` / `reorderFields(newOrder)` actions.
  - [ ] 3.4 Implement `addFilter(filter)` / `removeFilter(index)` / `updateFilter(index, filter)` actions.
  - [ ] 3.5 Implement `setGroupBy(fields)` action — enforces max 3 fields with a thrown error if exceeded.
  - [ ] 3.6 Implement `executePreview()` async action — calls `helpdesk.api.reports.execute_report` via `createResource`, stores results in `previewData` and `totalCount`.
  - [ ] 3.7 Implement `saveReport(reportName, description)` async action.
  - [ ] 3.8 Implement `loadReport(reportId)` async action that hydrates store state from a saved HD Custom Report record.

- [ ] Task 4 — Create shared report components (AC: #4, #5, #6, #7)
  - [ ] 4.1 Create `desk/src/components/reports/ReportFieldPicker.vue` — renders two panels: "Available Fields" (left) and "Selected Fields" (right). Available fields are filterable by search. Uses Vue's built-in or a lightweight drag library (e.g., `@vueuse/integrations/useSortable`) for drag-and-drop. Emits `field-added`, `field-removed`, `fields-reordered` events.
  - [ ] 4.2 Create `desk/src/components/reports/ReportFilterBuilder.vue` — renders a list of filter rows, each with: field selector (frappe-ui FormControl Select), operator selector, value input (type adapts to fieldtype: text/number/date). "Add Filter" button appends new row. "Remove" icon per row. Emits `filters-changed` event.
  - [ ] 4.3 Create `desk/src/components/reports/ReportChartRenderer.vue` — accepts `chartType`, `data`, and `columns` props. For `table` type: renders a frappe-ui ListView or a plain HTML table with pagination controls. For `bar`/`line`/`pie` types: integrates a lightweight charting library already in the project (or uses `@frappe/charts` if present). Shows skeleton loader while `isLoading` is true. Emits `page-change` event for paginated table.

- [ ] Task 5 — Create ReportList.vue page (AC: #2, #13)
  - [ ] 5.1 Create `desk/src/pages/reports/ReportList.vue`.
  - [ ] 5.2 Use `createListResource` to fetch HD Custom Report records (fields: `name`, `report_name`, `description`, `data_source`, `modified`, `owner`).
  - [ ] 5.3 Display results in a frappe-ui ListView with columns: Report Name, Data Source, Description, Last Modified, Owner.
  - [ ] 5.4 Add "New Report" button (frappe-ui Button, variant="solid") that navigates to `/helpdesk/reports/new`.
  - [ ] 5.5 Clicking a row navigates to `/helpdesk/reports/{name}` (edit existing report).
  - [ ] 5.6 Add empty state message when no reports exist.

- [ ] Task 6 — Create ReportBuilder.vue page (AC: #3, #4, #5, #6, #7, #8, #9)
  - [ ] 6.1 Create `desk/src/pages/reports/ReportBuilder.vue`.
  - [ ] 6.2 On `mount` (when route has `:id`): call `reportStore.loadReport(id)` to populate store state from saved report.
  - [ ] 6.3 Layout: two-column — left panel (configuration, ~40% width), right panel (preview, ~60% width).
  - [ ] 6.4 Left panel includes: (a) Data Source select dropdown at top (required, triggers `setDataSource`), (b) `<ReportFieldPicker>` component bound to store `selectedFields` and `availableFields`, (c) `<ReportFilterBuilder>` component bound to store `filters`, (d) Group By section with up to 3 field selectors (multi-select, max 3, using store `setGroupBy`), (e) Sort By field + Sort Order toggle, (f) Chart Type selector (icon buttons for table/bar/line/pie).
  - [ ] 6.5 Right panel shows: (a) `<ReportChartRenderer>` bound to store `previewData`, `chartType`, `isLoading`, (b) Row count display "Showing {n} of {total} rows", (c) Pagination controls.
  - [ ] 6.6 Implement debounced watcher on store state (500ms debounce using `watchDebounced` from `@vueuse/core`) that triggers `reportStore.executePreview()` on any config change.
  - [ ] 6.7 Header bar with: "Report Builder" breadcrumb, report name input field (frappe-ui Input), description input, "Save" button. "Save" calls `reportStore.saveReport(name, description)` and shows toast on success.
  - [ ] 6.8 Handle loading state: show skeleton in preview panel while `reportStore.isLoading` is true.
  - [ ] 6.9 Handle empty config state: when no data source is selected, show empty state in preview panel with instruction "Select a data source to get started."

- [ ] Task 7 — Write unit tests for query generation and data aggregation (AC: #12)
  - [ ] 7.1 Open `helpdesk/helpdesk/doctype/hd_custom_report/test_hd_custom_report.py`.
  - [ ] 7.2 Write test `test_doctype_validation_group_by_max_3` — create HD Custom Report with 4 group_by fields, assert `frappe.ValidationError` is raised.
  - [ ] 7.3 Write test `test_doctype_validation_invalid_data_source` — set `data_source` to an unlisted value, assert ValidationError.
  - [ ] 7.4 Write test `test_doctype_validation_selected_fields_must_be_list` — set `selected_fields` to non-list JSON, assert ValidationError.
  - [ ] 7.5 Create `helpdesk/tests/test_reports_api.py` (or add to existing test module).
  - [ ] 7.6 Write test `test_execute_report_requires_permission` — call `execute_report` as Guest user, assert PermissionError.
  - [ ] 7.7 Write test `test_execute_report_hd_ticket_basic` — call `execute_report` with `data_source="HD Ticket"`, `selected_fields=["name","subject","status"]`, assert returns dict with `data` (list) and `total_count` keys.
  - [ ] 7.8 Write test `test_execute_report_with_filters` — apply a filter `{"field": "status", "operator": "equals", "value": "Open"}`, assert the returned rows all have `status == "Open"`.
  - [ ] 7.9 Write test `test_execute_report_group_by_aggregation` — apply `group_by=["status"]`, assert response rows include `_count` key and rows are distinct by status.
  - [ ] 7.10 Write test `test_get_available_fields_returns_list` — call `get_available_fields("HD Ticket")`, assert non-empty list of dicts with `fieldname`, `label`, `fieldtype` keys.
  - [ ] 7.11 Write test `test_execute_report_pagination` — request page 1 and page 2 with `page_length=5`, assert different rows and `total_count` is consistent.

- [ ] Task 8 — Register routes in frontend router (AC: #13)
  - [ ] 8.1 Open the frontend router file (likely `desk/src/router/index.ts` or `desk/src/router.ts`).
  - [ ] 8.2 Add route: `{ path: "/helpdesk/reports", component: ReportList, name: "ReportList" }` with lazy import.
  - [ ] 8.3 Add route: `{ path: "/helpdesk/reports/new", component: ReportBuilder, name: "ReportBuilderNew" }` with lazy import.
  - [ ] 8.4 Add route: `{ path: "/helpdesk/reports/:id", component: ReportBuilder, name: "ReportBuilderEdit" }` with lazy import, passing `id` as route param.
  - [ ] 8.5 Verify navigation guard (if any) allows Manager/Admin roles to access report routes.

## Dev Notes

### Architecture Patterns

- **HD Custom Report is a standalone DocType** (not a Single), meaning records are created per report. Use standard `frappe.get_doc("HD Custom Report", name)` to fetch records. Use autoname `field:report_name` so the report name becomes the document ID.
- **Query Generation with `frappe.qb`** — The architecture mandates no raw SQL (Enforcement Guideline #6). Use Frappe's Query Builder (`frappe.qb`) for all dynamic query construction. Example pattern:
  ```python
  from frappe.query_builder import DocType

  def build_query(data_source, selected_fields, filters, group_by, sort_by, sort_order):
      Table = DocType(data_source)
      query = frappe.qb.from_(Table)

      # Select fields
      for field in selected_fields:
          query = query.select(getattr(Table, field))

      # Apply filters
      for f in filters:
          field_obj = getattr(Table, f["field"])
          op = f["operator"]
          val = f["value"]
          if op == "equals":
              query = query.where(field_obj == val)
          elif op == "contains":
              query = query.where(field_obj.like(f"%{val}%"))
          # ... additional operators

      # Group by
      if group_by:
          for g in group_by:
              query = query.groupby(getattr(Table, g))
          query = query.select(frappe.qb.functions.Count("*").as_("_count"))

      return query
  ```
- **Permission Model (NFR-SE-05)** — Custom reports respect the Frappe permission model. Call `frappe.has_permission(data_source, "read", throw=True)` at the top of `execute_report`. This means a guest user executing a report on "HD Ticket" will get a PermissionError. Additionally, Frappe's standard DocType permissions apply to the HD Custom Report record itself (read: all agents, write/create/delete: creator or admin — per ADR-04 permission table).
- **State Management (ADR-11)** — The `report.ts` Pinia store manages report builder state. Follow the pattern of other stores (e.g., `chat.ts`, `notifications.ts`) documented in ADR-11. The store is the single source of truth for preview data.
- **Real-time Preview Pattern** — Use `watchDebounced` from `@vueuse/core` (already present in the project via frappe-ui dependencies) with 500ms delay to avoid excessive API calls on every keystroke. The preview shows a skeleton loader (`isLoading: true`) while executing.
- **Frontend Data Fetching** — Use frappe-ui's `createResource` / `createListResource` pattern for all API calls (Enforcement Guideline #5). Example:
  ```typescript
  const reportResource = createResource({
    url: "helpdesk.api.reports.execute_report",
    params: { report_id: reportId },
    auto: false,
    onSuccess(data) { reportStore.previewData = data.data }
  })
  ```
- **ADR-08: API Method Path** — All whitelisted methods are called as `helpdesk.api.reports.{method_name}`. The full API module is `helpdesk/api/reports.py` and the methods are `execute_report`, `get_available_fields`, `save_report` (ADR-08).
- **i18n** — All user-facing labels use `frappe._()` in Python and `__()` in JS/Vue (Enforcement Guideline, architecture #7).

### Files to Create / Modify

| Action | Path | Notes |
|--------|------|-------|
| Create | `helpdesk/helpdesk/doctype/hd_custom_report/__init__.py` | Empty init |
| Create | `helpdesk/helpdesk/doctype/hd_custom_report/hd_custom_report.json` | DocType schema (report_name, data_source, selected_fields, filters, group_by, sort_by, sort_order, chart_type, description) |
| Create | `helpdesk/helpdesk/doctype/hd_custom_report/hd_custom_report.py` | Controller with validate() — group_by max 3, data_source whitelist, JSON validation |
| Create | `helpdesk/helpdesk/doctype/hd_custom_report/test_hd_custom_report.py` | Unit tests for DocType validation |
| Create | `helpdesk/api/reports.py` | `execute_report`, `get_available_fields`, `save_report` endpoints |
| Create | `helpdesk/tests/test_reports_api.py` | Unit tests for query generation and permission enforcement |
| Create | `helpdesk/patches/v1_phase1/create_hd_custom_report.py` | Migration patch to register DocType |
| Modify | `helpdesk/patches.txt` | Register the migration patch |
| Create | `desk/src/stores/report.ts` | Pinia store for report builder state (ADR-11) |
| Create | `desk/src/pages/reports/ReportList.vue` | Report list page (route: /helpdesk/reports) |
| Create | `desk/src/pages/reports/ReportBuilder.vue` | Report builder page (route: /helpdesk/reports/new and /helpdesk/reports/:id) |
| Create | `desk/src/components/reports/ReportFieldPicker.vue` | Drag-and-drop field selection component |
| Create | `desk/src/components/reports/ReportFilterBuilder.vue` | Filter condition builder component |
| Create | `desk/src/components/reports/ReportChartRenderer.vue` | Chart/table rendering component |
| Modify | `desk/src/router/index.ts` (or similar) | Add /helpdesk/reports, /helpdesk/reports/new, /helpdesk/reports/:id routes |

### Testing Standards

- Minimum 80% unit test coverage on all new backend controller logic (NFR-M-01).
- Use Frappe's `frappe.tests.utils.FrappeTestCase` as base class for all test cases.
- Tests that create HD Custom Report records must clean up after themselves using `addCleanup` or `tearDown`.
- Run DocType tests: `bench --site <site> run-tests --module helpdesk.helpdesk.doctype.hd_custom_report.test_hd_custom_report`
- Run API tests: `bench --site <site> run-tests --module helpdesk.tests.test_reports_api`

### Constraints

- Do NOT use raw SQL; all query construction MUST use `frappe.qb` (Enforcement Guideline #6).
- Do NOT expose internal notes (is_internal communications) via report data — the `HD Ticket` data source query must exclude `HD Communication` records marked `is_internal = 1` (NFR-SE-01).
- Do NOT allow arbitrary DocType queries — `data_source` is whitelisted to exactly 4 DocTypes: HD Ticket, HD CSAT Response, HD Article, HD Time Entry. Validation in controller and API both enforce this allowlist.
- Do NOT use Custom Fields mechanism — create the HD Custom Report DocType as a full DocType JSON file in the app source (AR-04).
- Group-by is limited to 3 levels maximum (per Story ACs).
- Permission check is MANDATORY before any `execute_report` query (NFR-SE-05).
- All new fields default to sensible values: `chart_type = "table"`, `sort_order = "DESC"`.
- `report_name` must be unique (autoname: field:report_name enforces this).

### Project Structure Notes

- **DocType location:** `helpdesk/helpdesk/doctype/hd_custom_report/` — follows the standard DocType module pattern per architecture Structure Patterns section.
- **API location:** `helpdesk/api/reports.py` — per ADR-08 and project directory structure (line 739 in architecture.md).
- **Frontend pages:** `desk/src/pages/reports/ReportList.vue` and `desk/src/pages/reports/ReportBuilder.vue` — per ADR-09 (architecture.md lines 367–368).
- **Frontend components:** `desk/src/components/reports/` — per ADR-09 component organization (architecture.md lines 390–393).
- **Pinia store:** `desk/src/stores/report.ts` — per ADR-11 (architecture.md line 464).
- **Migration patch:** `helpdesk/patches/v1_phase1/create_hd_custom_report.py` — per AR-05 (all schema migration patches for Phase 1 go in `helpdesk/patches/v1_phase1/`).
- **Dependencies:** Story 6.1 has no hard runtime dependencies on other stories (it can query any of the 4 data sources independently), but CSAT data (HD CSAT Response) will be empty until Epic 3 Story 3.7 is complete, and HD Time Entry will be empty until Epic 1 Story 1.7 is complete. The DocType and UI can be built independently.
- **Report query generator is isolated from report UI** — per architecture Architectural Boundaries: "Report query generator is isolated from report UI." Keep `build_query()` as a pure function in `reports.py` to facilitate unit testing.

### References

- FR-CR-01 (Custom report builder): [Source: _bmad-output/planning-artifacts/epics.md#Functional Requirements]
- NFR-SE-05 (Custom reports respect Frappe permission model): [Source: _bmad-output/planning-artifacts/epics.md#Non-Functional Requirements]
- NFR-M-01 (80% unit test coverage): [Source: _bmad-output/planning-artifacts/epics.md#Non-Functional Requirements]
- NFR-P-07 (Dashboard widget load < 1 second): [Source: _bmad-output/planning-artifacts/epics.md#Non-Functional Requirements]
- AR-02 (HD prefix naming convention): [Source: _bmad-output/planning-artifacts/epics.md#Additional Requirements]
- AR-04 (Add fields to DocType JSON, not Custom Fields): [Source: _bmad-output/planning-artifacts/epics.md#Additional Requirements]
- AR-05 (Migration patches in helpdesk/patches/v1_phase1/): [Source: _bmad-output/planning-artifacts/epics.md#Additional Requirements]
- UX-DR-08 (Report builder with drag-and-drop, real-time preview, chart type selector): [Source: _bmad-output/planning-artifacts/epics.md#UX Design Requirements]
- ADR-02 (New DocType Schema for Phase 1): [Source: _bmad-output/planning-artifacts/architecture.md#ADR-02]
- ADR-04 (Permission Model Extensions): [Source: _bmad-output/planning-artifacts/architecture.md#ADR-04]
- ADR-08 (API Design — reports.py endpoints): [Source: _bmad-output/planning-artifacts/architecture.md#ADR-08]
- ADR-09 (Frontend Component Organization — reports pages and components): [Source: _bmad-output/planning-artifacts/architecture.md#ADR-09]
- ADR-11 (Pinia store report.ts): [Source: _bmad-output/planning-artifacts/architecture.md#ADR-11]
- Enforcement Guideline #6 (No raw SQL — use frappe.qb): [Source: _bmad-output/planning-artifacts/architecture.md#Enforcement Guidelines]
- Project Directory Structure (api/reports.py, pages/reports/, components/reports/): [Source: _bmad-output/planning-artifacts/architecture.md#Complete Project Directory Structure]
- Epic 6 Story 6.1 full AC: [Source: _bmad-output/planning-artifacts/epics.md#Story 6.1]

## Dev Agent Record

### Agent Model Used

_To be filled by implementing dev agent_

### Debug Log References

_None — story creation phase_

### Completion Notes List

_To be filled by implementing dev agent_

### File List

_To be filled by implementing dev agent upon completion_
