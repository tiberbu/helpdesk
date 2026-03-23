# Story 6.5: Time Tracking Reports

Status: ready-for-dev

## Story

As a team manager,
I want time reports by agent, team, and period with billable breakdown,
so that I can track effort, manage billing, and optimize team productivity.

## Acceptance Criteria

1. **[Time Tracking Reports Dashboard Page]** Given a manager navigates to `/helpdesk/dashboard/time`, when the page loads, then it displays all of the following panels: (a) a filter bar with date range presets (Last 7 Days, Last 30 Days, Last 90 Days, Custom Range), agent multi-select, team multi-select, and billable/non-billable toggle; (b) a summary row with three metric cards — "Total Hours" (all logged time in period), "Billable Hours" (sum of billable entries), and "Non-Billable Hours" (sum of non-billable entries), all formatted as "Xh Ym"; (c) hours-by-agent table (AC #2); (d) average time per ticket section (AC #3); (e) time entry detail table (AC #5). The dashboard loads within 1 second per widget (NFR-P-07).

2. **[Hours by Agent per Period with Billable Breakdown]** Given HD Time Entry records exist (from Epic 1 Story 1.7), when the manager views the hours-by-agent table, then a table is displayed with the following columns: Agent Name, Total Hours (formatted "Xh Ym"), Billable Hours, Non-Billable Hours, Billable % (percentage of total that is billable, shown as a progress bar + number), and Ticket Count (number of distinct tickets with time entries). Rows are sorted by Total Hours descending by default. Clicking a column header re-sorts the table. Clicking an agent row expands an inline detail view showing that agent's individual time entries filtered to the current period.

3. **[Average Time per Ticket by Category and Priority]** Given HD Time Entry records and resolved tickets exist, when the manager views the average time section, then two sub-tables are shown side by side: (a) "By Category" table — columns: Category, Avg Time per Ticket ("Xh Ym"), Ticket Count, Total Hours; (b) "By Priority" table — columns: Priority, Avg Time per Ticket, Ticket Count, Total Hours, Billable %. Both tables calculate average time as `sum(duration_minutes for all entries on tickets in category/priority) / count(distinct tickets with time entries in that category/priority)`. If Story 1.3 (categorization) is not yet deployed, the "By Category" table shows "Uncategorized" for all tickets. If no time entries exist for a category or priority, it is excluded from the table (no zero rows).

4. **[ERPNext Timesheet Sync — Optional Integration]** Given ERPNext is installed AND `erpnext_timesheet_sync_enabled` is checked in HD Settings, when billable HD Time Entry records are saved or the sync job runs, then: (a) each billable HD Time Entry is synced to ERPNext as a Timesheet record with fields: `company` (from HD Settings `erpnext_company`), `employee` (looked up by agent email from ERPNext Employee DocType), `time_logs` containing one entry per HD Time Entry with `activity_type`, `from_time`, `hours` (duration_minutes / 60), `project` (from ticket's linked ERPNext project, or a default project from HD Settings), `is_billable = 1`; (b) the sync creates a new Timesheet per agent per day (grouping all same-day billable entries for one agent); (c) the HD Time Entry records store the synced Timesheet name in a `erpnext_timesheet` field (Link to ERPNext Timesheet, optional) so duplicate sync is prevented (if already set, skip re-sync); (d) if ERPNext is not reachable or the sync fails, the error is logged to `frappe.log_error()` and the time entry remains unsynced (retry on next run — no data loss).

5. **[All Features Work Without ERPNext]** Given ERPNext is NOT installed, when the time tracking feature and reports are used, then: (a) all dashboard features (hours by agent, averages, filters, export) work normally; (b) the ERPNext sync section is hidden from HD Settings; (c) no errors or warnings are shown to the user related to ERPNext; (d) the `erpnext_timesheet` field on HD Time Entry is safely ignored (not rendered in UI); (e) the `sync_erpnext_timesheets` API endpoint returns a clear message "ERPNext integration is not enabled" rather than an error.

6. **[`get_time_tracking_summary` API Endpoint]** Given a request to `helpdesk.api.time_tracking.get_time_tracking_summary`, when called with optional parameters `date_from` (str), `date_to` (str), `agent` (str or list), `team` (str or list), and `billable` (bool or null — null means all), then the backend: (a) queries HD Time Entry records using `frappe.qb` (no raw SQL — Enforcement Guideline #6); (b) joins with HD Ticket to get team/category/priority; (c) aggregates by agent: `{"agent": str, "total_minutes": int, "billable_minutes": int, "non_billable_minutes": int, "ticket_count": int}`; (d) includes overall `summary`: `{"total_minutes": int, "billable_minutes": int, "non_billable_minutes": int, "entry_count": int}`; (e) requires `frappe.has_permission("HD Time Entry", "read", throw=True)` before data access; (f) returns JSON with `summary` and `agents` list.

7. **[`get_avg_time_per_ticket` API Endpoint]** Given a request to `helpdesk.api.time_tracking.get_avg_time_per_ticket`, when called with optional parameters `date_from`, `date_to`, `agent`, `team`, and `group_by` (str: "category"|"priority", default: "category"), then the backend: (a) queries HD Time Entry records joined to HD Ticket via `frappe.qb`; (b) groups by the requested dimension; (c) for each group computes: `total_minutes = sum(duration_minutes)`, `ticket_count = count(DISTINCT ticket)`, `avg_minutes_per_ticket = total_minutes / ticket_count`, `billable_pct = sum(billable*duration_minutes) / total_minutes * 100`; (d) returns JSON with `groups` list sorted by `total_minutes` descending; (e) requires `frappe.has_permission("HD Time Entry", "read", throw=True)`.

8. **[`sync_erpnext_timesheets` API Endpoint]** Given a request to `helpdesk.api.time_tracking.sync_erpnext_timesheets`, when called (optionally with `date_from`, `date_to` to sync a specific range), then: (a) checks `erpnext_timesheet_sync_enabled` in HD Settings; if false, returns `{"message": "ERPNext integration is not enabled", "synced": 0}`; (b) if enabled, checks ERPNext is accessible via `frappe.db.get_value("Company", ...)` or equivalent — if ERPNext DocTypes are not available, returns the disabled message; (c) fetches unsynced billable HD Time Entry records (`billable = 1` AND `erpnext_timesheet` is null); (d) groups by agent + date; (e) for each group, creates or updates an ERPNext Timesheet record; (f) on success, sets `erpnext_timesheet` on each HD Time Entry; (g) returns `{"synced": int, "failed": int, "errors": [str]}`; (h) requires `System Manager` or `HD Admin` role.

9. **[Time Entry Detail Table with Export]** Given the time tracking dashboard is displayed, when the manager scrolls to the detail section or clicks "View All Entries", then a paginated table shows all individual time entries for the current filter with columns: Date, Agent, Ticket (link to ticket), Duration, Billable (checkbox icon), Description (truncated). The table supports: (a) sorting by any column; (b) pagination (25 rows per page); (c) CSV export of the full filtered dataset (not just current page) via a "Export CSV" button. The CSV includes: date, agent_name, ticket_id, ticket_subject, duration_minutes, duration_formatted, billable, description.

10. **[Unit Tests — Time Tracking Report Accuracy]** Given the API implementations, when the test suite runs, then unit tests for `get_time_tracking_summary`, `get_avg_time_per_ticket`, and `sync_erpnext_timesheets` pass with minimum 80% code coverage (NFR-M-01). Required test cases: (a) `test_hours_by_agent_billable_breakdown` — insert 3 time entries for agent A (2 billable 60min, 1 non-billable 30min) and 2 for agent B (1 billable 45min, 1 non-billable 45min); call `get_time_tracking_summary()`; assert agent A: total=150min, billable=120min, non_billable=30min; agent B: total=90min, billable=45min; (b) `test_hours_by_agent_date_filter` — insert entries across 3 months; filter to last 30 days; assert only current-period entries returned; (c) `test_hours_by_agent_team_filter` — insert entries for agents in different teams; filter by team; assert only correct team's entries returned; (d) `test_avg_time_group_by_category` — insert entries on tickets with categories; assert avg_minutes_per_ticket computed correctly per category; (e) `test_avg_time_group_by_priority` — same for priority; (f) `test_avg_time_no_category` — insert entries on tickets without category; assert "Uncategorized" group returned; (g) `test_sync_erpnext_disabled` — call `sync_erpnext_timesheets` when setting is off; assert returns disabled message with `synced == 0`; (h) `test_get_time_tracking_summary_requires_permission` — call as Guest; assert `frappe.PermissionError`; (i) `test_billable_filter` — call with `billable=True`; assert only billable entries in result; (j) `test_export_csv_structure` — verify CSV export includes all required columns.

11. **[Routes Registered]** Given the frontend router configuration, when the app loads, then route `/helpdesk/dashboard/time` (component: `TimeTrackingDashboard.vue`) is registered and navigable. The route is accessible to users with `HD Manager`, `HD Admin`, or `System Manager` roles. Navigating while unauthenticated redirects to the login page.

12. **[Dashboard Widgets for Time Tracking]** Given an agent/manager has configured their home page with time tracking widgets, when the home page loads, then two optional home page widgets are available: (a) `TimeTrackingSummaryWidget.vue` — shows "Xh Ym Total | Xh Ym Billable" for the current week, with a "View Dashboard" link to `/helpdesk/dashboard/time`; (b) `BillableRatioWidget.vue` — shows a donut/gauge chart of billable % (e.g., "65% Billable") for the last 30 days with a trend arrow vs the prior 30 days. Both widgets load within 1 second (NFR-P-07) and register in the existing home page widget registry.

## Tasks / Subtasks

- [ ] Task 1 — Extend HD Time Entry DocType for ERPNext sync field (AC: #4, #5)
  - [ ] 1.1 Open `helpdesk/helpdesk/doctype/hd_time_entry/hd_time_entry.json`. Add a new field: `erpnext_timesheet` (fieldtype: "Data", label: "ERPNext Timesheet", read_only: 1, description: "Set when synced to ERPNext Timesheet record"). Using Data type (not Link) to avoid ERPNext DocType dependency — store the Timesheet name as a string. Make the field hidden/read-only in normal UI.
  - [ ] 1.2 Add `erpnext_timesheet_sync_enabled` (Check, default 0, label: "Enable ERPNext Timesheet Sync") and `erpnext_company` (Data, label: "ERPNext Company for Timesheets") and `erpnext_default_project` (Data, label: "Default ERPNext Project") to `HD Settings` DocType JSON (`helpdesk/helpdesk/doctype/hd_settings/hd_settings.json`).
  - [ ] 1.3 Create migration patch `helpdesk/patches/v1_phase1/add_erpnext_sync_fields_to_time_entry.py` that adds the `erpnext_timesheet` column to `tabHD Time Entry` if it does not exist. Follow the pattern of existing patches in `helpdesk/patches/v1_phase1/`.
  - [ ] 1.4 Add the patch path to `patches.txt` in the correct order after existing Phase 1 patches.

- [ ] Task 2 — Implement `get_time_tracking_summary` in `helpdesk/api/time_tracking.py` (AC: #6, #2)
  - [ ] 2.1 Open (or create) `helpdesk/api/time_tracking.py`. This file is defined in ADR-08 with existing methods `start_timer`, `stop_timer`, `add_entry`, `get_summary` from Story 1.7. Add `get_time_tracking_summary` alongside those.
  - [ ] 2.2 Decorate with `@frappe.whitelist()`. Add `frappe.has_permission("HD Time Entry", "read", throw=True)` at the top.
  - [ ] 2.3 Build base query using `frappe.qb` on `HD Time Entry` joined to `HD Ticket` (for team, category, priority). Apply optional filters: `date_from` / `date_to` (filter on `hd_time_entry.creation`), `agent` (if list, use `IN`), `team` (join condition on `hd_ticket.team`), `billable` (if not null, filter `hd_time_entry.billable`).
  - [ ] 2.4 Aggregate per agent: group by `hd_time_entry.agent`, compute `sum(duration_minutes)` as `total_minutes`, `sum(CASE WHEN billable=1 THEN duration_minutes ELSE 0 END)` as `billable_minutes`, `count(DISTINCT ticket)` as `ticket_count`. Use `frappe.qb.functions` for aggregates.
  - [ ] 2.5 Compute overall `summary` by summing across all matching entries: `total_minutes`, `billable_minutes`, `non_billable_minutes = total_minutes - billable_minutes`, `entry_count` (total row count).
  - [ ] 2.6 Return JSON: `{"summary": {...}, "agents": [{"agent": str, "agent_name": str, "total_minutes": int, "billable_minutes": int, "non_billable_minutes": int, "ticket_count": int, "billable_pct": float}, ...]}` sorted by `total_minutes` descending.
  - [ ] 2.7 Cache result in Redis for 2 minutes: key `time_summary_{site}_{hash(frozenset(params.items()))}`, TTL 120s. Invalidate on HD Time Entry `after_insert` / `on_update` via a short-queue enqueue.

- [ ] Task 3 — Implement `get_avg_time_per_ticket` in `helpdesk/api/time_tracking.py` (AC: #7, #3)
  - [ ] 3.1 Add `@frappe.whitelist()` decorated function `get_avg_time_per_ticket(date_from=None, date_to=None, agent=None, team=None, group_by="category")`.
  - [ ] 3.2 Call `frappe.has_permission("HD Time Entry", "read", throw=True)`.
  - [ ] 3.3 Build `frappe.qb` query on `HD Time Entry` joined to `HD Ticket`. Apply same optional filters as Task 2.3. Group by the dimension field: `HDTicket.category` when `group_by="category"` or `HDTicket.priority` when `group_by="priority"`. Use `frappe.qb.functions.IfNull(HDTicket.category, "Uncategorized")` for category grouping to handle null categories.
  - [ ] 3.4 Compute per group: `total_minutes = sum(HDTimeEntry.duration_minutes)`, `ticket_count = count(DISTINCT HDTimeEntry.ticket)`, `avg_minutes = total_minutes / ticket_count` (as float, round to 1 decimal), `billable_minutes = sum(CASE WHEN billable=1 THEN duration_minutes ELSE 0 END)`, `billable_pct = billable_minutes / total_minutes * 100` (round to 1 decimal).
  - [ ] 3.5 Return JSON: `{"group_by": str, "groups": [{"dimension": str, "total_minutes": int, "avg_minutes": float, "ticket_count": int, "billable_pct": float}, ...]}` sorted by `total_minutes` descending. Exclude groups with `ticket_count == 0`.

- [ ] Task 4 — Implement `sync_erpnext_timesheets` in `helpdesk/api/time_tracking.py` (AC: #4, #5, #8)
  - [ ] 4.1 Add `@frappe.whitelist()` decorated function `sync_erpnext_timesheets(date_from=None, date_to=None)`. Add role check: `frappe.only_for(["System Manager", "HD Admin"])`.
  - [ ] 4.2 Read `erpnext_timesheet_sync_enabled` from HD Settings. If false (or if ERPNext is not installed — check via `frappe.db.table_exists("tabTimesheet")` or `"erpnext" not in frappe.get_installed_apps()`), return `{"message": frappe._("ERPNext integration is not enabled"), "synced": 0, "failed": 0, "errors": []}`.
  - [ ] 4.3 Fetch unsynced billable entries: `frappe.qb` on HD Time Entry where `billable = 1` AND `(erpnext_timesheet IS NULL OR erpnext_timesheet = "")`. Apply optional date range filter on `creation`. Fetch fields: `name`, `ticket`, `agent`, `duration_minutes`, `description`, `creation`, `billable`.
  - [ ] 4.4 Group entries by `(agent, date(creation))`. For each group, look up the ERPNext Employee record by matching `hd_agent.user` email to `tabEmployee.user_id`. If no Employee found, log warning and skip this agent's entries (add to `errors` list), continue with other agents.
  - [ ] 4.5 For each `(agent, date)` group, build ERPNext Timesheet dict: `{"doctype": "Timesheet", "company": erpnext_company, "employee": employee_name, "time_logs": [{"activity_type": "Support", "from_time": entry.creation, "hours": entry.duration_minutes / 60.0, "project": get_ticket_project(entry.ticket) or erpnext_default_project, "is_billable": 1, "description": entry.description} for entry in group_entries]}`. Insert via `frappe.get_doc(ts_dict).insert(ignore_permissions=True)`.
  - [ ] 4.6 On successful insert, update each HD Time Entry: `frappe.db.set_value("HD Time Entry", entry.name, "erpnext_timesheet", timesheet.name)`. Commit after each agent-day group to avoid large transactions.
  - [ ] 4.7 Wrap each group's insert in try/except. On failure: `frappe.log_error(...)`, increment `failed`, append error description to `errors` list, continue.
  - [ ] 4.8 Return `{"synced": synced_count, "failed": failed_count, "errors": errors_list}`.
  - [ ] 4.9 Add scheduler event in `hooks.py` for automatic daily sync: `"0 2 * * *": ["helpdesk.api.time_tracking.sync_erpnext_timesheets"]` (runs at 2 AM daily on "long" queue). Use `frappe.enqueue` wrapper for scheduler call.

- [ ] Task 5 — Implement CSV export endpoint (AC: #9)
  - [ ] 5.1 Add `@frappe.whitelist()` function `export_time_entries_csv(date_from=None, date_to=None, agent=None, team=None, billable=None)` in `helpdesk/api/time_tracking.py`.
  - [ ] 5.2 Call `frappe.has_permission("HD Time Entry", "read", throw=True)`.
  - [ ] 5.3 Build `frappe.qb` query on HD Time Entry joined to HD Ticket. Apply all optional filters. Fetch fields: `hd_time_entry.creation` as date, `hd_time_entry.agent`, `hd_time_entry.ticket`, `hd_ticket.subject`, `hd_time_entry.duration_minutes`, `hd_time_entry.billable`, `hd_time_entry.description`.
  - [ ] 5.4 Build CSV rows: `date, agent_name, ticket_id, ticket_subject, duration_minutes, duration_formatted ("Xh Ym"), billable (Yes/No), description`. Use Python's `csv` module with `io.StringIO`.
  - [ ] 5.5 Return a `frappe.response` with `content_type = "text/csv"`, `filename = "time_entries_{date_from}_{date_to}.csv"`, and the CSV string as response body. Follow the Frappe file-response pattern (see existing export implementations in the codebase).

- [ ] Task 6 — Write unit tests for time tracking reports (AC: #10)
  - [ ] 6.1 Create `helpdesk/tests/test_time_tracking_reports.py` (or add to existing test infrastructure from Story 1.7).
  - [ ] 6.2 Write `test_hours_by_agent_billable_breakdown`: create HD Time Entry records for 2 agents with mixed billable/non-billable entries; call `get_time_tracking_summary()`; assert per-agent totals match expected values; assert `billable_pct` is correct.
  - [ ] 6.3 Write `test_hours_by_agent_date_filter`: insert entries with creation dates in different months; call with `date_from` / `date_to` covering only one month; assert only that month's entries appear.
  - [ ] 6.4 Write `test_hours_by_agent_team_filter`: insert entries for agents on different teams; call with team filter; assert only that team's agent entries appear.
  - [ ] 6.5 Write `test_avg_time_group_by_category`: create tickets with categories and time entries; call `get_avg_time_per_ticket(group_by="category")`; assert avg_minutes_per_ticket is `total / distinct_ticket_count`.
  - [ ] 6.6 Write `test_avg_time_group_by_priority`: same approach for priority grouping.
  - [ ] 6.7 Write `test_avg_time_no_category`: create tickets without category set (null); call with `group_by="category"`; assert result contains "Uncategorized" dimension.
  - [ ] 6.8 Write `test_sync_erpnext_disabled`: set `erpnext_timesheet_sync_enabled = 0` in HD Settings (or mock it); call `sync_erpnext_timesheets()`; assert response `synced == 0` and message contains "not enabled".
  - [ ] 6.9 Write `test_get_time_tracking_summary_requires_permission`: call `get_time_tracking_summary()` as Guest; assert `frappe.PermissionError`.
  - [ ] 6.10 Write `test_billable_filter`: insert mix of billable and non-billable entries; call `get_time_tracking_summary(billable=True)`; assert `summary.non_billable_minutes == 0` and only billable entries returned.
  - [ ] 6.11 Ensure all test data is cleaned up in `tearDown` or via `addCleanup`. Run with: `bench --site <site> run-tests --module helpdesk.tests.test_time_tracking_reports`.

- [ ] Task 7 — Create `TimeTrackingDashboard.vue` page component (AC: #1, #2, #3, #9)
  - [ ] 7.1 Create `desk/src/pages/dashboard/TimeTrackingDashboard.vue`. This directory exists from Stories 6.3 and 6.4. Use `<script setup lang="ts">` (ADR-09).
  - [ ] 7.2 Declare reactive filter state: `dateRange` (ref, default Last 30 Days), `selectedAgents` (ref, default `[]`), `selectedTeams` (ref, default `[]`), `billableFilter` (ref, default `null` — all), `avgGroupBy` (ref, default `"category"`), `detailPage` (ref, default `1`).
  - [ ] 7.3 Create resources: (a) `summaryResource = createResource({ url: "helpdesk.api.time_tracking.get_time_tracking_summary", auto: true, params: computed(...) })`; (b) `avgResource = createResource({ url: "helpdesk.api.time_tracking.get_avg_time_per_ticket", auto: true, params: computed(...) })`; (c) `detailResource = createListResource({ doctype: "HD Time Entry", fields: [...], filters: computed(...), pageLength: 25, auto: true })`. Re-fetch all when filters change via `watch`.
  - [ ] 7.4 Summary row: three `<TimeMetricCard>` components for Total, Billable, Non-Billable hours. Show skeleton loaders while loading.
  - [ ] 7.5 Hours by Agent table: `<table>` or frappe-ui `ListView` with columns: Agent, Total Hours, Billable, Non-Billable, Billable % (progress bar using frappe-ui or inline `<div>`), Ticket Count. Sortable by clicking column headers (toggle asc/desc, update local sort state). On row click/expand, show inline list of that agent's entries for the period (fetched via `createListResource` filter on agent + date range).
  - [ ] 7.6 Average Time section: tab group ["By Category", "By Priority"] that toggles `avgGroupBy` ref. Each tab renders a table with columns: Dimension, Avg Time per Ticket, Ticket Count, Total Hours, Billable %. Format avg time using `formatTime(minutes)`.
  - [ ] 7.7 Time Entry Detail section: paginated table (`<ListView>` or `<table>`) with columns: Date, Agent, Ticket (link), Duration, Billable (icon), Description. Add "Export CSV" button that calls `helpdesk.api.time_tracking.export_time_entries_csv` with current filters and triggers browser file download.
  - [ ] 7.8 Filter bar: date range presets (7d/30d/90d/Custom), Agent multi-select (from HD Agents list), Team multi-select (from HD Teams list), Billable toggle (All/Billable Only/Non-Billable Only). All controls update the shared filter state and trigger resource re-fetch.
  - [ ] 7.9 Empty state: if `summaryResource.data.summary.total_minutes == 0`, show "No time entries found for this period" centered message.
  - [ ] 7.10 Format helper: create or reuse `useTimeFormat.ts` composable with `formatTime(minutes: number): string` returning "Xh Ym" (e.g., `formatTime(90)` → `"1h 30m"`, `formatTime(30)` → `"30m"`, `formatTime(0)` → `"< 1m"`).

- [ ] Task 8 — Create reusable `TimeMetricCard.vue` component (AC: #1, #12)
  - [ ] 8.1 Create `desk/src/components/reports/TimeMetricCard.vue`. Define props: `label` (String), `totalMinutes` (Number | null), `loading` (Boolean, default false), `variant` (String: "default"|"billable"|"non-billable", default "default" — used for color accent: blue/green/gray).
  - [ ] 8.2 Render: label in small text, formatted time value in large bold text using `formatTime(totalMinutes)` (show "—" when null), optional sub-label. Apply color accent based on variant. Show skeleton placeholder when `loading`.
  - [ ] 8.3 All strings use `__()` for i18n.

- [ ] Task 9 — Create `TimeTrackingSummaryWidget.vue` and `BillableRatioWidget.vue` home page widgets (AC: #12)
  - [ ] 9.1 Create `desk/src/components/reports/TimeTrackingSummaryWidget.vue`. On mount, fetch `get_time_tracking_summary` with `date_from = start_of_week`. Display "Xh Ym Total | Xh Ym Billable" as two numbers. Add "View Dashboard" link. Handle null/empty state.
  - [ ] 9.2 Create `desk/src/components/reports/BillableRatioWidget.vue`. On mount, fetch `get_time_tracking_summary` for last 30 days AND prior 30 days (two calls). Render a small donut/gauge showing `billable_pct` (e.g., "65%") and a trend arrow (green up if ratio improved, red down if decreased, gray dash if <2% change). Handle empty state ("No data").
  - [ ] 9.3 Both widgets must be `auto: true` and render within 1 second (NFR-P-07).
  - [ ] 9.4 Register both in the home page widget registry (locate in `desk/src/pages/home/`): `TimeTrackingSummaryWidget` with `id: "time_tracking_summary"`, `title: __("Time Tracking This Week")`; `BillableRatioWidget` with `id: "billable_ratio"`, `title: __("Billable Ratio")`. Both with `roles: ["HD Manager", "HD Admin"]`.

- [ ] Task 10 — Register frontend route (AC: #11)
  - [ ] 10.1 Open `desk/src/router/index.ts` (or the main router file — check `desk/src/router/`).
  - [ ] 10.2 Add lazy-loaded route: `{ path: "/helpdesk/dashboard/time", component: () => import("@/pages/dashboard/TimeTrackingDashboard.vue"), name: "TimeTrackingDashboard" }`.
  - [ ] 10.3 Ensure role guard allows `HD Manager`, `HD Admin`, and `System Manager`. Unauthenticated access redirects to login.
  - [ ] 10.4 Verify no conflict with existing `/helpdesk/dashboard/csat` (Story 6.3) and `/helpdesk/dashboard/mttr` (Story 6.4) routes.

## Dev Notes

### Architecture Patterns

- **Dependency on Story 1.7 (Per-Ticket Time Tracking)** — This story is a pure reporting layer on top of the `HD Time Entry` DocType created in Story 1.7. The `HD Time Entry` schema is: `ticket (Link to HD Ticket)`, `agent (Link to HD Agent)`, `duration_minutes (Int)`, `billable (Check)`, `description (Small Text)`, `timestamp (Datetime)`. Story 1.7 also created `helpdesk/api/time_tracking.py` with `start_timer`, `stop_timer`, `add_entry`, `get_summary`. Add all new endpoints to this same file (ADR-08).

- **`frappe.qb` Join Pattern** — Use the Query Builder for joined aggregation:
  ```python
  from frappe.query_builder import DocType
  from frappe.query_builder.functions import Sum, Count, Coalesce

  HDTimeEntry = DocType("HD Time Entry")
  HDTicket = DocType("HD Ticket")

  results = (
      frappe.qb.from_(HDTimeEntry)
      .join(HDTicket).on(HDTimeEntry.ticket == HDTicket.name)
      .select(
          HDTimeEntry.agent,
          Sum(HDTimeEntry.duration_minutes).as_("total_minutes"),
          Count(HDTimeEntry.ticket.distinct()).as_("ticket_count")
      )
      .where(HDTimeEntry.creation >= date_from)
      .groupby(HDTimeEntry.agent)
  ).run(as_dict=True)
  ```
  Never use `frappe.db.sql()` with raw SQL strings (Enforcement Guideline #6).

- **ERPNext Integration Safety** — ERPNext is optional. Always guard with existence check before attempting ERPNext DocType access:
  ```python
  def is_erpnext_available():
      return (
          frappe.db.get_single_value("HD Settings", "erpnext_timesheet_sync_enabled")
          and "erpnext" in frappe.get_installed_apps()
          and frappe.db.table_exists("tabTimesheet")
      )
  ```
  Import ERPNext DocType names only inside the guard block. Never import at module level (would fail without ERPNext).

- **Redis Caching Pattern** — Match the pattern established in Story 6.3/6.4:
  ```python
  import hashlib, json
  cache_key = f"time_summary_{frappe.local.site}_{hashlib.md5(json.dumps(sorted(kwargs.items())).encode()).hexdigest()}"
  cached = frappe.cache().get_value(cache_key)
  if cached:
      return cached
  result = _compute_summary(...)
  frappe.cache().set_value(cache_key, result, expires_in_sec=120)
  return result
  ```
  Cache invalidation: on `HD Time Entry` `after_insert` and `on_update`, enqueue a short-queue job to delete matching cache keys.

- **Background Job for ERPNext Sync** — The daily sync is added to `hooks.py` `scheduler_events`:
  ```python
  # hooks.py
  scheduler_events = {
      # ... existing ...
      "cron": {
          # ... existing 5-minute SLA check ...
          "0 2 * * *": [
              "helpdesk.api.time_tracking._daily_erpnext_sync"
          ]
      }
  }
  ```
  Create a wrapper function `_daily_erpnext_sync()` in `time_tracking.py` that calls `frappe.enqueue("helpdesk.api.time_tracking.sync_erpnext_timesheets", queue="long")` to avoid blocking the scheduler worker.

- **CSV Export via Frappe Response** — Use the Frappe file response pattern. Check existing exports in the codebase (e.g., SLA or report export) for the exact pattern. Typically:
  ```python
  frappe.response["type"] = "csv"
  frappe.response["result"] = csv_string
  frappe.response["doctype"] = "HD Time Entry"
  frappe.response["name"] = f"time_entries_{date_from}_to_{date_to}.csv"
  ```
  Alternatively, return the CSV as a base64-encoded string and trigger download client-side via a Blob URL in Vue. Check how Story 6.2 (Report Scheduling and Export) handles CSV export from `helpdesk/api/reports.py` for the established pattern.

- **`formatTime` Composable** — Create `desk/src/composables/useTimeFormat.ts` if it does not already exist from Story 6.4's `useMTTRFormat.ts`. If `useMTTRFormat.ts` already exists, check if it exports a generic `formatMinutes` function that can be reused here. Do not duplicate logic — import from the existing composable if applicable.

- **Billable Percentage Progress Bar** — Use Tailwind CSS inline `<div>` pattern for the progress bar in the hours-by-agent table (no external library needed):
  ```html
  <div class="flex items-center gap-2">
    <div class="h-2 flex-1 bg-gray-100 rounded-full overflow-hidden">
      <div class="h-full bg-green-500 rounded-full" :style="{ width: `${billablePct}%` }"></div>
    </div>
    <span class="text-sm text-gray-600">{{ billablePct.toFixed(0) }}%</span>
  </div>
  ```

- **Dependencies on Other Stories:**
  - **Story 1.7** (Per-Ticket Time Tracking) — HD Time Entry DocType and `helpdesk/api/time_tracking.py` MUST exist. If not yet deployed, this story cannot proceed. Check `helpdesk/helpdesk/doctype/hd_time_entry/` exists.
  - **Story 1.3** (Multi-Level Ticket Categorization) — `category` field on HD Ticket needed for "By Category" breakdown. If not deployed, "By Category" table shows "Uncategorized" for all — handle gracefully per AC #3.
  - **Story 6.3** (CSAT Analytics Dashboard) — shares `desk/src/pages/dashboard/` directory.
  - **Story 6.4** (MTTR Dashboard) — shares `desk/src/pages/dashboard/` directory and potentially the `useMTTRFormat.ts` / `formatMinutes` composable.
  - **Story 6.1** (Custom Report Builder) — `helpdesk/api/reports.py` exists from this story. The `time_tracking.py` module is separate per ADR-08; do NOT add time tracking endpoints to `reports.py`.

### Files to Create / Modify

| Action | Path | Notes |
|--------|------|-------|
| Modify | `helpdesk/helpdesk/doctype/hd_time_entry/hd_time_entry.json` | Add `erpnext_timesheet` (Data, read-only) field |
| Modify | `helpdesk/helpdesk/doctype/hd_settings/hd_settings.json` | Add `erpnext_timesheet_sync_enabled`, `erpnext_company`, `erpnext_default_project` fields |
| Create | `helpdesk/patches/v1_phase1/add_erpnext_sync_fields_to_time_entry.py` | Migration patch for new field |
| Modify | `helpdesk/patches.txt` | Add new patch in correct order |
| Modify | `helpdesk/api/time_tracking.py` | Add `get_time_tracking_summary`, `get_avg_time_per_ticket`, `sync_erpnext_timesheets`, `export_time_entries_csv`, `_daily_erpnext_sync` |
| Modify | `helpdesk/hooks.py` | Add daily ERPNext sync scheduler event (cron `0 2 * * *`) |
| Create | `helpdesk/tests/test_time_tracking_reports.py` | Unit tests for all new API endpoints (min 80% coverage, NFR-M-01) |
| Create | `desk/src/pages/dashboard/TimeTrackingDashboard.vue` | Main time tracking reports dashboard page |
| Create | `desk/src/components/reports/TimeMetricCard.vue` | Reusable metric card (Total/Billable/Non-Billable) |
| Create | `desk/src/components/reports/TimeTrackingSummaryWidget.vue` | Home page compact time tracking widget |
| Create | `desk/src/components/reports/BillableRatioWidget.vue` | Home page billable ratio donut widget |
| Create or Modify | `desk/src/composables/useTimeFormat.ts` | `formatTime(minutes)` composable (reuse from useMTTRFormat.ts if exists) |
| Modify | `desk/src/router/index.ts` (or similar) | Register `/helpdesk/dashboard/time` route |
| Modify | Home page widget registry (`desk/src/pages/home/`) | Register `TimeTrackingSummaryWidget` and `BillableRatioWidget` |

### Testing Standards

- Minimum 80% unit test coverage on all new backend code (NFR-M-01).
- Use `frappe.tests.utils.FrappeTestCase` as the base class for all Python tests.
- Test data (HD Time Entry records, HD Ticket records) must be cleaned up in `tearDown` or via `addCleanup`.
- Mock `frappe.cache()` in tests to avoid Redis dependency: `unittest.mock.patch("frappe.cache")`.
- For ERPNext sync tests, mock `frappe.get_installed_apps()` to return `["erpnext"]` (enabled) or not (disabled) rather than requiring a real ERPNext install.
- Run tests: `bench --site <site> run-tests --module helpdesk.tests.test_time_tracking_reports`

### Constraints

- Do NOT use raw SQL; all queries must use `frappe.qb` or `frappe.db.get_all()` (Enforcement Guideline #6).
- ERPNext integration MUST be fully optional — no import or reference to ERPNext DocTypes at the module level (Enforcement Guideline: conditional imports only inside `is_erpnext_available()` guard).
- Dashboard route `/helpdesk/dashboard/time` must not conflict with `/helpdesk/dashboard/csat` (Story 6.3) or `/helpdesk/dashboard/mttr` (Story 6.4).
- `formatTime(0)` must return a meaningful value (e.g., `"< 1m"`) not `"0h 0m"`.
- The `erpnext_timesheet` field on `HD Time Entry` must use `Data` type (not `Link`) to avoid hard ERPNext dependency at the DocType level — stores the ERPNext Timesheet docname as a plain string.
- All user-facing strings use `frappe._()` in Python and `__()` in Vue (Enforcement Guideline #7).
- The BillableRatioWidget donut chart should use a lightweight SVG approach rather than importing a full chart library — keep home page bundle small (NFR-P-05 principle applied to home page).

### Project Structure Notes

- **API location:** `helpdesk/api/time_tracking.py` — as defined in ADR-08 (architecture.md). This file already exists from Story 1.7 with `start_timer`, `stop_timer`, `add_entry`, `get_summary`. All new reporting endpoints are added to this same file.
- **Frontend page:** `desk/src/pages/dashboard/TimeTrackingDashboard.vue` — follows ADR-09. Shares the `dashboard/` subdirectory with `CSATDashboard.vue` (Story 6.3) and `MTTRDashboard.vue` (Story 6.4).
- **Frontend components:** `desk/src/components/reports/` — per ADR-09. Joins existing components from Stories 6.1–6.4 (`ReportFieldPicker.vue`, `CSATScoreCard.vue`, `MTTRMetricCard.vue`, etc.).
- **DocType modifications:** `hd_time_entry.json` and `hd_settings.json` — additive field changes only, following AR-04 (no Custom Fields, modify source DocType JSON directly).
- **Migration patch:** Required for the new `erpnext_timesheet` field on `HD Time Entry`. Follows `helpdesk/patches/v1_phase1/` pattern established by other Phase 1 stories.
- **No new DocTypes** — Story 6.5 is a reporting layer on top of existing `HD Time Entry` data. No new DocType JSON files are needed.

### References

- FR-TT-02 (Time reporting and ERPNext integration): [Source: _bmad-output/planning-artifacts/epics.md#Story 6.5]
- FR-TT-02 full requirements: [Source: _bmad-output/planning-artifacts/prd.md#FR-TT-02]
- FR-TT-01 (Per-Ticket Time Logging — HD Time Entry DocType, source of data): [Source: _bmad-output/planning-artifacts/prd.md#FR-TT-01]
- FR-TT-01 epic story (Story 1.7): [Source: _bmad-output/planning-artifacts/epics.md#Story 1.7]
- NFR-P-07 (Dashboard widget load < 1 second): [Source: _bmad-output/planning-artifacts/epics.md#Non-Functional Requirements]
- NFR-M-01 (80% unit test coverage): [Source: _bmad-output/planning-artifacts/epics.md#Non-Functional Requirements]
- NFR-M-02 (All new DocTypes accessible via REST API): [Source: _bmad-output/planning-artifacts/epics.md#Non-Functional Requirements]
- NFR-M-04 (All ITIL features toggleable via HD Settings): [Source: _bmad-output/planning-artifacts/epics.md#Non-Functional Requirements]
- AR-04 (New fields added to DocType JSON, not Custom Fields): [Source: _bmad-output/planning-artifacts/epics.md#Additional Requirements]
- AR-05 (Migration patches in helpdesk/patches/v1_phase1/): [Source: _bmad-output/planning-artifacts/epics.md#Additional Requirements]
- ADR-02 (New DocType Schema — HD Time Entry fields and relationships): [Source: _bmad-output/planning-artifacts/architecture.md#ADR-02]
- ADR-08 (API Design — time_tracking.py for time tracking endpoints): [Source: _bmad-output/planning-artifacts/architecture.md#ADR-08]
- ADR-09 (Frontend Component Organization — reports/ components, dashboard/ pages): [Source: _bmad-output/planning-artifacts/architecture.md#ADR-09]
- ADR-12 (Background Job Architecture — "long" queue for sync, "short" for cache invalidation): [Source: _bmad-output/planning-artifacts/architecture.md#ADR-12]
- Enforcement Guideline #5 (createResource for frontend data fetching): [Source: _bmad-output/planning-artifacts/architecture.md#Enforcement Guidelines]
- Enforcement Guideline #6 (No raw SQL — use frappe.qb): [Source: _bmad-output/planning-artifacts/architecture.md#Enforcement Guidelines]
- Enforcement Guideline #7 (i18n — frappe._() and __()): [Source: _bmad-output/planning-artifacts/architecture.md#Enforcement Guidelines]
- Enforcement Guideline #8 (frappe.enqueue for operations >1 second): [Source: _bmad-output/planning-artifacts/architecture.md#Enforcement Guidelines]
- Project Directory Structure (api/time_tracking.py, components/reports/, pages/dashboard/): [Source: _bmad-output/planning-artifacts/architecture.md#Complete Project Directory Structure]
- Story 1.7 (Per-Ticket Time Tracking — HD Time Entry schema and existing API): [Source: _bmad-output/planning-artifacts/epics.md#Story 1.7]
- Story 1.3 (Multi-Level Ticket Categorization — category field on HD Ticket): [Source: _bmad-output/planning-artifacts/epics.md#Story 1.3]
- Story 6.3 (CSAT Analytics Dashboard — shares pages/dashboard/ and components/reports/): [Source: _bmad-output/planning-artifacts/epics.md#Story 6.3]
- Story 6.4 (MTTR Dashboard — shares pages/dashboard/ and potentially formatMinutes composable): [Source: _bmad-output/planning-artifacts/epics.md#Story 6.4]
- Story 6.2 (Report Scheduling and Export — CSV export pattern to follow): [Source: _bmad-output/planning-artifacts/epics.md#Story 6.2]
- UX-DR-04 (Time tracker component with start/stop timer in ticket sidebar): [Source: _bmad-output/planning-artifacts/epics.md#UX Design Requirements]
- SC-06 (Agent productivity measurable — >80% resolved tickets have time entries): [Source: _bmad-output/planning-artifacts/prd.md#Success Criteria]

## Dev Agent Record

### Agent Model Used

_To be filled by implementing dev agent_

### Debug Log References

_None — story creation phase_

### Completion Notes List

_To be filled by implementing dev agent_

### File List

_To be filled by implementing dev agent upon completion_
