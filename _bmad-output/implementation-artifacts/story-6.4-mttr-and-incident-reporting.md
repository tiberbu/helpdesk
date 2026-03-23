# Story 6.4: MTTR and Incident Reporting

Status: ready-for-dev

## Story

As a team manager,
I want to view Mean Time to Resolve, incident volume trends, and category distribution,
so that I can identify improvement areas and track support performance over time.

## Acceptance Criteria

1. **[MTTR Dashboard Page]** Given a manager navigates to `/helpdesk/dashboard/mttr`, when the page loads, then it displays all of the following metric panels: (a) three MTTR summary cards showing the 30-day, 60-day, and 90-day rolling MTTR averages (displayed in hours and minutes, e.g., "4h 22m"), (b) MTTR breakdown table with three tabs — "By Priority", "By Team", and "By Category" — each tab shows a table with columns: Dimension (Priority/Team/Category name), MTTR (hours:minutes), Ticket Count, and Change vs Prior Period (colored arrow with % delta), (c) incident volume trend chart (described in AC #3), (d) category distribution pie chart (described in AC #4). The dashboard loads within 1 second per widget (NFR-P-07).

2. **[MTTR Excludes Waiting on Customer Time]** Given resolved tickets that include periods in "Waiting on Customer" status, when MTTR is calculated, then the time spent in "Waiting on Customer" status is subtracted from the total resolution duration. MTTR = `(resolution_time − creation_time) − sum_of_all_waiting_on_customer_intervals`. This mirrors the SLA pause-on-status logic (FR-SL-01, Story 4.1). If a ticket has no status history records in the pause status, full elapsed time from creation to resolution is used. Only tickets with `status = "Resolved"` or `status = "Closed"` and a non-null `resolution_date` are included in MTTR calculations.

3. **[Incident Volume Trend Chart]** Given incident ticket data exists, when the manager views the trend chart section, then a line/bar combo chart shows: X-axis = date (bucketed by selected granularity), Y-axis = ticket count, with two series: "Current Period" (solid line or bars) and "Prior Period" (dashed line, same date range shifted back). The manager can toggle granularity between Daily, Weekly, and Monthly using a button group. A "Prior Period" toggle enables/disables the comparison series. The default view is Weekly granularity for the last 90 days with prior period enabled.

4. **[Category Distribution Pie Chart]** Given categorized tickets exist (from Epic 1 Story 1.3), when viewing the category distribution section, then a pie chart renders showing the top 10 categories by ticket volume for the selected time period. Each slice shows: category name, percentage of total, and ticket count. Slices beyond the top 10 are grouped as "Other" with their combined count and percentage. If fewer than 10 categories exist, all are shown. Hovering a slice shows a tooltip with the exact count and percentage.

5. **[Date Range and Filters]** Given the MTTR dashboard is displayed, when the manager applies filters, then they can filter by: (a) date range presets (Last 30 Days, Last 60 Days, Last 90 Days, Custom Range — custom range uses a date picker pair), (b) team (multi-select from active HD Teams), (c) priority (multi-select: Urgent, High, Medium, Low), (d) category (single-select from HD Ticket Category records). All charts, tables, and summary cards refresh immediately when any filter changes. The default view is Last 90 Days with no team/priority/category filters (all included).

6. **[`get_mttr_data` API Endpoint]** Given a request to `helpdesk.api.reports.get_mttr_data`, when called with optional parameters `date_from` (str), `date_to` (str), `team` (str), `priority` (str), `category` (str), and `group_by` (str: "priority"|"team"|"category", default: "priority"), then the backend: (a) queries HD Ticket records for resolved/closed tickets in the date range using `frappe.qb` (no raw SQL — Enforcement Guideline #6), (b) for each ticket fetches its status change history from `HD Ticket Activity` or similar audit log to compute total "Waiting on Customer" pause duration, (c) computes MTTR per ticket as `(resolution_date − creation) − pause_duration`, then aggregates by the requested `group_by` dimension, (d) returns a JSON object with:
   - `summary`: `{"mttr_30d": minutes, "mttr_60d": minutes, "mttr_90d": minutes}` — overall rolling averages regardless of group_by
   - `breakdown`: list of `{"dimension": str, "mttr_minutes": int, "ticket_count": int, "prior_period_mttr_minutes": int}` sorted by `ticket_count` descending
   The endpoint requires `frappe.has_permission("HD Ticket", "read", throw=True)` before any data access.

7. **[`get_incident_volume_trend` API Endpoint]** Given a request to `helpdesk.api.reports.get_incident_volume_trend`, when called with optional parameters `date_from`, `date_to`, `team`, `priority`, `category`, and `granularity` (str: "daily"|"weekly"|"monthly", default: "weekly"), then the backend: (a) queries HD Ticket records (any status, not just resolved) in the date range, (b) groups by the appropriate date bucket based on `granularity` (DATE for daily, YEARWEEK for weekly, DATE_FORMAT YYY-MM for monthly), (c) also computes the prior same-length period for comparison, (d) returns a JSON object with:
   - `current_period`: list of `{"date": str, "count": int}` sorted ascending by date
   - `prior_period`: list of `{"date": str, "count": int}` for the same length period shifted back, dates expressed as original period dates for alignment on the same chart X-axis
   - `total_current`: int (sum of current period)
   - `total_prior`: int (sum of prior period)
   - `change_pct`: float (percentage change current vs prior, null if prior is 0)
   The endpoint requires `frappe.has_permission("HD Ticket", "read", throw=True)`.

8. **[`get_category_distribution` API Endpoint]** Given a request to `helpdesk.api.reports.get_category_distribution`, when called with optional parameters `date_from`, `date_to`, `team`, `priority`, and `limit` (int, default: 10), then the backend: (a) queries HD Ticket records in the date range grouped by `category`, (b) returns the top N categories by count plus an aggregated "Other" bucket for the remainder, (c) returns a JSON object:
   - `categories`: list of `{"category": str, "count": int, "percentage": float}` for top N, sorted by count descending
   - `other`: `{"count": int, "percentage": float}` for remaining categories beyond top N (null if <= N categories total)
   - `total`: int (total ticket count in period)
   Tickets without a category (null/empty `category` field) are grouped under the label "Uncategorized" and ranked alongside named categories. The endpoint requires `frappe.has_permission("HD Ticket", "read", throw=True)`.

9. **[MTTR Breakdown Component — By Priority/Team/Category Tabs]** Given the MTTR breakdown table is rendered, when the manager clicks a tab ("By Priority", "By Team", "By Category"), then: (a) the table rows update immediately (no page reload) using cached data from a single `get_mttr_data` call (pass `group_by` param to API or compute all three client-side from the one call), (b) MTTR values are displayed as "Xh Ym" (e.g., "2h 15m" or "<1m" for sub-minute values), (c) the "Change vs Prior Period" column shows a green up-arrow if MTTR improved (decreased) by >5%, a red down-arrow if MTTR worsened (increased) by >5%, and a gray dash if change is within ±5% or prior period has no data. A tooltip on the arrow shows the raw delta in minutes.

10. **[Unit Tests — MTTR Calculation Accuracy]** Given the MTTR API implementation, when the test suite runs, then unit tests for `get_mttr_data`, `get_incident_volume_trend`, and `get_category_distribution` pass with minimum 80% code coverage (NFR-M-01). Required test cases: (a) `test_mttr_excludes_waiting_on_customer_time` — create a resolved ticket with a 60-minute "Waiting on Customer" interval; assert MTTR is `(total_elapsed_minutes − 60)`; (b) `test_mttr_no_pause_status` — create a resolved ticket with no status pauses; assert MTTR equals full elapsed time from creation to resolution; (c) `test_mttr_group_by_priority` — insert resolved tickets with different priorities; assert breakdown is grouped correctly with correct per-priority MTTR; (d) `test_mttr_group_by_team` — same as above but grouped by team; (e) `test_mttr_group_by_category` — same for category; (f) `test_mttr_rolling_windows` — insert tickets spread over 100 days; assert 30d/60d/90d summary values differ as expected; (g) `test_incident_volume_trend_weekly` — insert tickets over 3 weeks; assert weekly buckets match; (h) `test_incident_volume_trend_prior_period` — assert prior period returns correct ticket counts for shifted date range; (i) `test_category_distribution_top_10_and_other` — insert tickets with 15 distinct categories; assert result contains 10 named + "Other" bucket with correct counts and percentages summing to 100%; (j) `test_get_mttr_data_requires_permission` — call as Guest, assert PermissionError.

11. **[Routes Registered]** Given the frontend router configuration, when the app loads, then route `/helpdesk/dashboard/mttr` (component: `MTTRDashboard.vue`) is registered and navigable. The route is accessible to users with `HD Manager`, `HD Admin`, or `System Manager` roles. Navigating while unauthenticated redirects to the login page.

12. **[Dashboard Widgets for MTTR Metrics]** Given an agent/manager has configured their home page with MTTR widgets, when the home page loads, then two optional home page widgets are available: (a) `MTTRSummaryWidget.vue` — shows a compact 3-number display with 30d/60d/90d MTTR averages (as "Xh Ym"), title "MTTR Overview", and a "View Dashboard" link; (b) `IncidentVolumeTrendWidget.vue` — shows a small sparkline (mini line chart) of daily/weekly incident volume for the last 30 days with the total count and % change vs prior period. Both widgets load within 1 second (NFR-P-07) and register themselves in the existing home page widget registry.

## Tasks / Subtasks

- [ ] Task 1 — Implement ticket status pause-duration calculator utility (AC: #2, #6)
  - [ ] 1.1 Audit the existing HD Ticket activity/comment log to determine how status changes are currently stored. Look in `helpdesk/helpdesk/doctype/hd_ticket_activity/` or Frappe's built-in `Activity Log` or `HD Ticket Comment`. Identify the field that records status transitions with timestamps.
  - [ ] 1.2 Create or extend `helpdesk/utils/mttr.py` with a function `calculate_pause_duration(ticket_name: str, pause_statuses: list = None) -> int` that: (a) defaults `pause_statuses` to `["Waiting on Customer"]` (or reads from HD Settings if configurable), (b) queries status change records for the ticket ordered by creation ASC, (c) iterates transitions to identify entry/exit pairs for each pause status, (d) sums total pause minutes across all intervals, (e) returns total pause duration in minutes (int). Return 0 if no status history or no pause intervals found.
  - [ ] 1.3 Add a second function `calculate_mttr_minutes(ticket_doc) -> int` that takes an HD Ticket document and returns `max(0, round((ticket_doc.resolution_date - ticket_doc.creation).total_seconds() / 60) - calculate_pause_duration(ticket_doc.name))`. Return `None` if `ticket_doc.resolution_date` is null.
  - [ ] 1.4 Cache the pause duration per ticket in Redis (key: `mttr_pause_{ticket_name}`, TTL: 1 hour) to avoid repeated DB lookups during bulk MTTR calculations.
  - [ ] 1.5 Write unit tests in `helpdesk/tests/test_mttr_utils.py`: `test_calculate_pause_duration_no_history`, `test_calculate_pause_duration_single_interval`, `test_calculate_pause_duration_multiple_intervals`, `test_calculate_mttr_minutes_with_pause`, `test_calculate_mttr_minutes_no_resolution_date`.

- [ ] Task 2 — Implement `get_mttr_data` in `helpdesk/api/reports.py` (AC: #6, #2)
  - [ ] 2.1 Open (or create) `helpdesk/api/reports.py`. This file may already contain `execute_report`, `schedule_report`, `export_report` from Story 6.1/6.2. Add `get_mttr_data` alongside those.
  - [ ] 2.2 Decorate with `@frappe.whitelist()`. Add `frappe.has_permission("HD Ticket", "read", throw=True)` at the top.
  - [ ] 2.3 Build base query using `frappe.qb` on `HD Ticket` DocType. Apply filters: `status IN ("Resolved", "Closed")` AND `resolution_date IS NOT NULL`. Apply optional filters for `date_from` (filter on `resolution_date >= date_from`), `date_to` (`resolution_date <= date_to`), `team`, `priority`, `category`.
  - [ ] 2.4 Fetch matching ticket records (fields: `name`, `priority`, `team`, `category`, `creation`, `resolution_date`). For scalability, process in batches of 500 using `frappe.qb` pagination if >1000 results.
  - [ ] 2.5 For each ticket, call `calculate_mttr_minutes(ticket)` from `helpdesk.utils.mttr`. Collect `(ticket_name, dimension_value, mttr_minutes)` tuples where `dimension_value` is the `group_by` field value.
  - [ ] 2.6 Compute `summary`: run three sub-queries (or filter the fetched tickets in-memory) for 30-day, 60-day, 90-day rolling windows ending at `date_to` (or today). Compute `mean(mttr_minutes)` for each window.
  - [ ] 2.7 Compute `breakdown`: group tickets by `group_by` field. For each group: `mttr_minutes = mean(mttr_list)`, `ticket_count = len(mttr_list)`. Also compute prior-period MTTR (period of equal length shifted back by the current window length) for `prior_period_mttr_minutes`. Sort by `ticket_count` descending.
  - [ ] 2.8 Return the JSON object with `summary` and `breakdown` as specified in AC #6.
  - [ ] 2.9 Cache results in Redis for 5 minutes: key `mttr_data_{site}_{hash(params)}`, TTL 300s. Invalidate cache on HD Ticket resolve/close events (enqueue cache invalidation on "short" queue from `hd_ticket.on_update`).

- [ ] Task 3 — Implement `get_incident_volume_trend` in `helpdesk/api/reports.py` (AC: #7)
  - [ ] 3.1 Add `@frappe.whitelist()` decorated function `get_incident_volume_trend(date_from=None, date_to=None, team=None, priority=None, category=None, granularity="weekly")`.
  - [ ] 3.2 Call `frappe.has_permission("HD Ticket", "read", throw=True)`.
  - [ ] 3.3 Build `frappe.qb` query on `HD Ticket` (all statuses, not just resolved) with optional filters applied. Add `WHERE creation BETWEEN date_from AND date_to`.
  - [ ] 3.4 Use `frappe.qb` grouping by date bucket: for `"daily"` use `frappe.qb.functions.Date(HDTicket.creation)`; for `"weekly"` use `frappe.qb.functions.Week(HDTicket.creation)`; for `"monthly"` use a combination of Year + Month functions. Count records per bucket.
  - [ ] 3.5 Determine the prior period window: if `date_from` and `date_to` are set, shift both back by `(date_to - date_from)` days. Run the same aggregation query for the prior period.
  - [ ] 3.6 Align prior period data to current period dates by index position (bucket 1 of prior maps to bucket 1 of current for chart overlay). Include the prior period dates as-is in `prior_period` list.
  - [ ] 3.7 Compute `total_current`, `total_prior`, `change_pct = ((total_current - total_prior) / total_prior * 100)` (null if `total_prior == 0`).
  - [ ] 3.8 Return the complete JSON response as specified in AC #7.

- [ ] Task 4 — Implement `get_category_distribution` in `helpdesk/api/reports.py` (AC: #8)
  - [ ] 4.1 Add `@frappe.whitelist()` decorated function `get_category_distribution(date_from=None, date_to=None, team=None, priority=None, limit=10)`.
  - [ ] 4.2 Call `frappe.has_permission("HD Ticket", "read", throw=True)`.
  - [ ] 4.3 Build `frappe.qb` query on `HD Ticket` grouped by `category`. Apply filters for `date_from`, `date_to`, `team`, `priority`. Use `frappe.qb.functions.Count("*").as_("count")` and `frappe.qb.functions.IfNull(HDTicket.category, "Uncategorized").as_("category")` for grouping.
  - [ ] 4.4 Fetch all category-count pairs sorted by count descending. Compute `total = sum of all counts`.
  - [ ] 4.5 Take top `limit` rows for `categories` list; sum remaining rows into `other`. Compute `percentage = round(count / total * 100, 1)` for each entry.
  - [ ] 4.6 Return JSON response as specified in AC #8.

- [ ] Task 5 — Write unit tests for MTTR calculation accuracy (AC: #10)
  - [ ] 5.1 Create `helpdesk/tests/test_mttr_api.py` (or add to existing test infrastructure).
  - [ ] 5.2 Write `test_mttr_excludes_waiting_on_customer_time`: (a) create an HD Ticket via `frappe.get_doc(...).insert(ignore_permissions=True)`, (b) insert status change activity records: status set to "Waiting on Customer" at T+10min, status changed to "Replied" at T+70min (60 min pause), (c) set `resolution_date = T+120min`, (d) call `calculate_mttr_minutes(ticket)`, (e) assert result is `60` minutes (120 total − 60 pause). Clean up in `tearDown`.
  - [ ] 5.3 Write `test_mttr_no_pause_status`: create resolved ticket with no status history records in pause status. Assert MTTR equals `round((resolution_date - creation).total_seconds() / 60)`.
  - [ ] 5.4 Write `test_mttr_group_by_priority`: insert 4 resolved tickets: 2 with priority "Urgent" (MTTR 30min, 60min), 2 with priority "Low" (MTTR 120min, 240min). Call `get_mttr_data(group_by="priority")`. Assert breakdown has two rows; Urgent row `mttr_minutes ≈ 45`, Low row `mttr_minutes ≈ 180`.
  - [ ] 5.5 Write `test_mttr_group_by_team` and `test_mttr_group_by_category` using the same approach as 5.4.
  - [ ] 5.6 Write `test_mttr_rolling_windows`: insert 100 tickets spread uniformly over 100 days with MTTR of 60min each. Call `get_mttr_data()` (default filters). Assert `summary.mttr_30d == 60`, `summary.mttr_60d == 60`, `summary.mttr_90d == 60` (all equal since MTTR is uniform).
  - [ ] 5.7 Write `test_incident_volume_trend_weekly`: insert 10 tickets each week for 4 weeks. Call `get_incident_volume_trend(granularity="weekly")` with date range covering those 4 weeks. Assert `len(current_period) == 4` and each bucket has count `== 10`.
  - [ ] 5.8 Write `test_incident_volume_trend_prior_period`: insert 5 tickets in current month and 8 in prior month. Assert `total_current == 5`, `total_prior == 8`, `change_pct ≈ -37.5`.
  - [ ] 5.9 Write `test_category_distribution_top_10_and_other`: insert tickets with 15 distinct categories (5 tickets each). Call `get_category_distribution(limit=10)`. Assert `len(categories) == 10`, `other.count == 25` (5 categories × 5 tickets), all percentages sum to `100.0`.
  - [ ] 5.10 Write `test_get_mttr_data_requires_permission`: call `get_mttr_data()` as Guest user; assert `frappe.PermissionError`. Restore user in teardown.
  - [ ] 5.11 Ensure tests can be run with: `bench --site <site> run-tests --module helpdesk.tests.test_mttr_api`.

- [ ] Task 6 — Create `MTTRDashboard.vue` page component (AC: #1, #3, #4, #5, #9)
  - [ ] 6.1 Create directory `desk/src/pages/dashboard/` if it does not already exist (it may exist from Story 6.3). Create `desk/src/pages/dashboard/MTTRDashboard.vue`.
  - [ ] 6.2 Use `<script setup lang="ts">` syntax (ADR-09). Import `createResource` from `frappe-ui`.
  - [ ] 6.3 Declare reactive filter state: `dateRange` (ref, default Last 90 Days), `selectedTeams` (ref, default `[]`), `selectedPriorities` (ref, default `[]`), `selectedCategory` (ref, default `""`), `volumeGranularity` (ref, default `"weekly"`), `showPriorPeriod` (ref, default `true`), `mttrGroupBy` (ref, default `"priority"`).
  - [ ] 6.4 Create three resources: (a) `mttrResource = createResource({ url: "helpdesk.api.reports.get_mttr_data", auto: true, params: computed(...) })`, (b) `volumeResource = createResource({ url: "helpdesk.api.reports.get_incident_volume_trend", auto: true, params: computed(...) })`, (c) `categoryResource = createResource({ url: "helpdesk.api.reports.get_category_distribution", auto: true, params: computed(...) })`. Re-fetch all three when any filter changes via `watch`.
  - [ ] 6.5 Implement filter bar: Date range preset buttons (30d/60d/90d + Custom), Team multi-select, Priority multi-select (Urgent/High/Medium/Low checkboxes), Category select.
  - [ ] 6.6 MTTR Summary row: three `<MTTRMetricCard>` components side-by-side showing 30d, 60d, 90d MTTR values from `mttrResource.data.summary`. Add skeleton loaders while `mttrResource.loading`.
  - [ ] 6.7 MTTR Breakdown section: tab group using frappe-ui `Tabs` component with tabs ["By Priority", "By Team", "By Category"]. On tab change, update `mttrGroupBy` ref (this triggers a new API call). Render the breakdown as a `<table>` or frappe-ui `ListView` with columns: Dimension, MTTR ("Xh Ym"), Ticket Count, Change vs Prior (colored arrow + %).
  - [ ] 6.8 Incident Volume Trend chart: render below MTTR breakdown. Add granularity toggle buttons (Daily / Weekly / Monthly) that update `volumeGranularity` and refetch. Add "Compare Prior Period" toggle that shows/hides the dashed prior-period series. Use the project's existing charting library (`@frappe/charts` or equivalent) for the line/bar combo chart.
  - [ ] 6.9 Category Distribution chart: render below volume trend. Use a pie/donut chart. Each slice labeled with category name and percentage. "Other" slice shown in neutral gray. Implement tooltip on hover showing exact count and percentage. Limit chart to top 10 + Other as per AC #4.
  - [ ] 6.10 Add loading skeleton states and empty states: if `mttrResource.data` returns no tickets in the selected period, show "No resolved tickets found for this period" empty state message centered in the MTTR section.
  - [ ] 6.11 Format helper: create a composable `useMTTRFormat.ts` or inline `formatMTTR(minutes: number): string` function that returns "Xh Ym" (e.g., `formatMTTR(135)` → `"2h 15m"`, `formatMTTR(0)` → `"< 1m"`).

- [ ] Task 7 — Create reusable `MTTRMetricCard.vue` component (AC: #1, #12)
  - [ ] 7.1 Create `desk/src/components/reports/MTTRMetricCard.vue`.
  - [ ] 7.2 Define props: `label` (String, e.g., "30-Day MTTR"), `mttrMinutes` (Number | null), `ticketCount` (Number, default: 0), `loading` (Boolean, default: false).
  - [ ] 7.3 Render: title label in small text (`text-sm text-gray-500`), large MTTR value using `formatMTTR(mttrMinutes)` in `text-2xl font-bold text-gray-900` (show "—" when null), subtitle `"${ticketCount} tickets"` in `text-sm text-gray-500`. Use a card container with white background, rounded corners, shadow-sm — matching frappe-ui design tokens.
  - [ ] 7.4 Show a loading skeleton placeholder (animated gray bar) when `loading` prop is true.
  - [ ] 7.5 All strings use `__()` for i18n (Enforcement Guideline #7).

- [ ] Task 8 — Create `MTTRSummaryWidget.vue` and `IncidentVolumeTrendWidget.vue` home page widgets (AC: #12)
  - [ ] 8.1 Create `desk/src/components/reports/MTTRSummaryWidget.vue`. Import `createResource`. Fetch `get_mttr_data` with `date_to=today`, `date_from=90d ago` on mount. Display 3 numbers (30d/60d/90d MTTR using `formatMTTR()`). Add "View Dashboard" link to `/helpdesk/dashboard/mttr`. Handle null/empty state ("No data").
  - [ ] 8.2 Create `desk/src/components/reports/IncidentVolumeTrendWidget.vue`. Import `createResource`. Fetch `get_incident_volume_trend` with `granularity="daily"`, `date_from=30d ago` on mount. Render a small sparkline (mini chart, max height 60px). Show total count and change % (green if positive/more tickets, contextually-colored). Add "View Dashboard" link to `/helpdesk/dashboard/mttr`. Handle empty state.
  - [ ] 8.3 Both widgets must auto-load (`auto: true`) and render within 1 second (NFR-P-07).
  - [ ] 8.4 Register both widgets in the existing home page widget registry (locate in `desk/src/pages/home/`): `MTTRSummaryWidget` with `id: "mttr_summary"`, `title: "MTTR Overview"`; `IncidentVolumeTrendWidget` with `id: "incident_volume_trend"`, `title: "Incident Volume Trend"`. Both with `roles: ["HD Manager", "HD Admin"]`.

- [ ] Task 9 — Register frontend route (AC: #11)
  - [ ] 9.1 Open the frontend router file (`desk/src/router/index.ts` or similar).
  - [ ] 9.2 Add route: `{ path: "/helpdesk/dashboard/mttr", component: () => import("@/pages/dashboard/MTTRDashboard.vue"), name: "MTTRDashboard" }` using lazy import for code splitting.
  - [ ] 9.3 If a navigation guard restricts routes by role, ensure `MTTRDashboard` is accessible to `HD Manager`, `HD Admin`, and `System Manager` roles. Unauthenticated access redirects to login.
  - [ ] 9.4 Verify no conflict with existing `/helpdesk/dashboard/csat` route (from Story 6.3) or the home page route.

## Dev Notes

### Architecture Patterns

- **MTTR Calculation — Pause-on-Status Integration** — The MTTR calculation (AC #2) must mirror the SLA pause-on-status logic implemented in Story 4.1 (`helpdesk/utils/business_hours.py`). The key difference is that MTTR uses wall-clock elapsed time (not business hours), while SLA uses business hours only. The "Waiting on Customer" status name should be read from a configurable setting (or hardcoded constant) consistent with the value used in Story 4.1's SLA pause logic. Check `HD Settings` for a `sla_pause_statuses` or similar field; if present, reuse it for MTTR pause detection.

- **Status Change History Storage** — Before implementing Task 1, audit where Frappe Helpdesk stores ticket status history. Look for: `HD Ticket Activity` DocType, Frappe's built-in `Activity Log`, or status change entries in `HD Ticket Comment`. The relevant entries will have a `content` or `field_name` indicating a status change. If no per-status timestamp log exists, this story requires adding one. Add a lightweight `hd_ticket_activity` hook in `hooks.py` `doc_events["HD Ticket"]["on_update"]` that logs status changes with timestamp if not already present. Example:
  ```python
  # helpdesk/helpdesk/doctype/hd_ticket/hd_ticket.py (on_update)
  def log_status_change(self):
      if self.has_value_changed("status"):
          frappe.get_doc({
              "doctype": "HD Ticket Activity",
              "ticket": self.name,
              "action": "Status Changed",
              "old_value": self.get_doc_before_save().status,
              "new_value": self.status,
              "creation": frappe.utils.now_datetime()
          }).insert(ignore_permissions=True)
  ```
  If `HD Ticket Activity` does not exist as a DocType, use `frappe.log_error` or check for the Frappe Communication-based approach.

- **`frappe.qb` for Aggregation** — All dashboard queries use Frappe's Query Builder. Example for category distribution:
  ```python
  from frappe.query_builder import DocType
  from frappe.query_builder.functions import Count, IfNull

  HDTicket = DocType("HD Ticket")
  results = (
      frappe.qb.from_(HDTicket)
      .select(
          IfNull(HDTicket.category, "Uncategorized").as_("category"),
          Count("*").as_("count")
      )
      .where(HDTicket.creation >= date_from)
      .groupby(HDTicket.category)
      .orderby(Count("*"), order=frappe.qb.desc)
  ).run(as_dict=True)
  ```
  Never use `frappe.db.sql()` with raw SQL strings (Enforcement Guideline #6).

- **Background Job for Bulk MTTR** — For installations with >10K resolved tickets, computing pause durations per-ticket in a synchronous API call may be too slow. Use `frappe.enqueue` on the "long" queue to pre-compute and cache MTTR data periodically:
  ```python
  # In hooks.py scheduler_events
  "0 */4 * * *": [
      "helpdesk.helpdesk.reports.mttr_cache.refresh_mttr_cache"
  ]
  ```
  The API endpoint checks Redis cache first; if cache miss, computes synchronously for the requested range (acceptable for typical SMB deployments with <5K tickets/month per NFR-S-03).

- **Chart Library** — Use the same charting library already present in the project. Check `desk/src/pages/` for existing chart usage (likely `@frappe/charts` or `chart.js`). For the pie chart (AC #4), a donut style is preferred for readability. For the volume trend (AC #3), a dual-axis or layered chart showing both current (bars) and prior (line) series is the target UX.

- **Dashboard Performance (NFR-P-07)** — Cache all three API responses in Redis:
  ```python
  cache_key = f"mttr_data_{frappe.local.site}_{hash(frozenset(kwargs.items()))}"
  cached = frappe.cache().get_value(cache_key)
  if cached:
      return cached
  result = _compute_mttr_data(...)
  frappe.cache().set_value(cache_key, result, expires_in_sec=300)
  return result
  ```
  TTL of 300 seconds (5 minutes) is acceptable — MTTR dashboards don't need real-time precision.

- **Dependencies on Prior Stories** — This story depends on:
  - **Story 1.3** (Multi-Level Ticket Categorization) — `category` and `sub_category` fields on HD Ticket must exist. If not yet implemented, Category Distribution chart will show "Uncategorized" for all tickets.
  - **Story 4.1** (Business Hours SLA Calculation Engine) — The `sla_pause_statuses` configuration and any status change history mechanism should be consistent with how SLA pauses are tracked. Coordinate on the shared data structure.
  - **Story 6.1** (Custom Report Builder) — `helpdesk/api/reports.py` may already exist from Story 6.1. Add new endpoints to the same module rather than creating a separate file.

- **Frontend Data Fetching (Enforcement Guideline #5)** — All API calls use `createResource` / `createListResource` from frappe-ui. No direct `axios` or `fetch` calls.

- **Vue Component Structure (ADR-09)** — All components use `<script setup lang="ts">`. Props must have explicit TypeScript types.

- **i18n (Enforcement Guideline #7)** — All user-facing strings in Python use `frappe._()`. All user-facing strings in Vue use `__()`.

- **Permission Model (ADR-04)** — MTTR dashboard data is read-only and requires HD Ticket read permission. No special role beyond standard Agent/Manager read access is needed. The API endpoints check `frappe.has_permission("HD Ticket", "read", throw=True)`.

### Files to Create / Modify

| Action | Path | Notes |
|--------|------|-------|
| Create | `helpdesk/utils/mttr.py` | MTTR calculation utilities: `calculate_pause_duration`, `calculate_mttr_minutes` |
| Modify | `helpdesk/api/reports.py` | Add `get_mttr_data`, `get_incident_volume_trend`, `get_category_distribution` alongside Story 6.1/6.2 endpoints |
| Modify | `helpdesk/helpdesk/doctype/hd_ticket/hd_ticket.py` | Add `log_status_change` in `on_update` if status history not yet tracked |
| Modify | `helpdesk/hooks.py` | Add scheduler event for periodic MTTR cache refresh (every 4 hours on "long" queue) |
| Create | `helpdesk/tests/test_mttr_utils.py` | Unit tests for MTTR utility functions |
| Create | `helpdesk/tests/test_mttr_api.py` | Unit tests for all three API endpoints (min 80% coverage, NFR-M-01) |
| Create | `desk/src/pages/dashboard/MTTRDashboard.vue` | Main MTTR and incident reporting dashboard page |
| Create | `desk/src/components/reports/MTTRMetricCard.vue` | Reusable MTTR metric card component |
| Create | `desk/src/components/reports/MTTRSummaryWidget.vue` | Home page compact MTTR widget |
| Create | `desk/src/components/reports/IncidentVolumeTrendWidget.vue` | Home page incident volume sparkline widget |
| Create | `desk/src/composables/useMTTRFormat.ts` | `formatMTTR(minutes)` formatting composable |
| Modify | `desk/src/router/index.ts` (or similar) | Register `/helpdesk/dashboard/mttr` route |
| Modify | Home page widget registry (in `desk/src/pages/home/`) | Register `MTTRSummaryWidget` and `IncidentVolumeTrendWidget` |

### Testing Standards

- Minimum 80% unit test coverage on all new backend code (NFR-M-01).
- Use `frappe.tests.utils.FrappeTestCase` as base class for all Python tests.
- Test data (HD Ticket records, status history) must be cleaned up in `tearDown` or via `addCleanup`.
- Mock `frappe.cache()` in tests to avoid Redis dependency: `unittest.mock.patch("frappe.cache")`.
- For time-sensitive tests (rolling windows), use `unittest.mock.patch("frappe.utils.today")` and `frappe.utils.now_datetime()` to control the reference date.
- Run tests: `bench --site <site> run-tests --module helpdesk.tests.test_mttr_api`

### Constraints

- Do NOT use raw SQL; all queries must use `frappe.qb` or `frappe.db.get_all()` (Enforcement Guideline #6).
- MTTR calculation MUST exclude "Waiting on Customer" pause time as specified in FR-IM-06 and AC #2. A ticket with a very long waiting period must show the agent's actual resolution effort time.
- Dashboard routes must not conflict with existing routes (`/helpdesk/dashboard` home page, `/helpdesk/dashboard/csat` from Story 6.3).
- If Story 1.3 (Categorization) is not yet deployed, the category distribution chart should gracefully show "Uncategorized" for all tickets rather than crashing.
- All user-facing strings use `frappe._()` in Python and `__()` in Vue (Enforcement Guideline #7).
- `formatMTTR(0)` must return a meaningful display value (e.g., `"< 1m"`) rather than `"0h 0m"`.
- The `IncidentVolumeTrendWidget.vue` sparkline should NOT require the full chart library — use an SVG-based mini-sparkline or the lightest available option to keep the home page bundle small.

### Project Structure Notes

- **API location:** `helpdesk/api/reports.py` — as defined in ADR-08 (architecture.md). This file is shared with Story 6.1 (`execute_report`, `schedule_report`, `export_report`) and Story 6.2. Add MTTR endpoints to the same module.
- **Utility location:** `helpdesk/utils/mttr.py` — follows the pattern of `helpdesk/utils/business_hours.py` (created in Story 4.1). The `utils/` directory hosts shared pure-Python calculation utilities.
- **Frontend page:** `desk/src/pages/dashboard/MTTRDashboard.vue` — follows ADR-09. The `dashboard/` subdirectory is shared with `CSATDashboard.vue` (Story 6.3).
- **Frontend components:** `desk/src/components/reports/` — per ADR-09. Existing components from Story 6.1 (`ReportFieldPicker.vue`, `ReportFilterBuilder.vue`, `ReportChartRenderer.vue`) are in this directory; MTTR components join them.
- **No new DocTypes required** — Story 6.4 is a read-only analytics layer on top of existing HD Ticket data. No new DocType JSON files are needed unless status change history tracking requires a new child DocType (assessed in Task 1.1).
- **Migration patches:** No schema changes required unless status history is added. If `log_status_change` requires a new child table, add a migration patch in `helpdesk/patches/v1_phase1/`.

### References

- FR-IM-06 (MTTR and incident reporting): [Source: _bmad-output/planning-artifacts/epics.md#Story 6.4]
- FR-IM-06 full requirements: [Source: _bmad-output/planning-artifacts/prd.md#FR-IM-06]
- FR-IM-02 (Categorization — provides category field for distribution chart): [Source: _bmad-output/planning-artifacts/epics.md#Story 1.3]
- FR-SL-01 (SLA pause-on-status — MTTR must mirror this logic for "Waiting on Customer"): [Source: _bmad-output/planning-artifacts/epics.md#Story 4.1]
- NFR-P-07 (Dashboard widget load < 1 second): [Source: _bmad-output/planning-artifacts/epics.md#Non-Functional Requirements]
- NFR-M-01 (80% unit test coverage): [Source: _bmad-output/planning-artifacts/epics.md#Non-Functional Requirements]
- NFR-S-03 (Handle 100K tickets/month without degradation): [Source: _bmad-output/planning-artifacts/epics.md#Non-Functional Requirements]
- AR-03 (Background jobs via frappe.enqueue with named queues): [Source: _bmad-output/planning-artifacts/epics.md#Additional Requirements]
- ADR-02 (New DocType Schema — HD Ticket fields including category, priority, team): [Source: _bmad-output/planning-artifacts/architecture.md#ADR-02]
- ADR-08 (API Design — reports.py for custom report and analytics endpoints): [Source: _bmad-output/planning-artifacts/architecture.md#ADR-08]
- ADR-09 (Frontend Component Organization — reports/ components, dashboard/ pages): [Source: _bmad-output/planning-artifacts/architecture.md#ADR-09]
- ADR-12 (Background Job Architecture — "long" queue for report generation, "short" for cache invalidation): [Source: _bmad-output/planning-artifacts/architecture.md#ADR-12]
- ADR-13 (SLA Business Hours Calculation — pause-on-status design, shared with MTTR): [Source: _bmad-output/planning-artifacts/architecture.md#ADR-13]
- Enforcement Guideline #5 (createResource for frontend data fetching): [Source: _bmad-output/planning-artifacts/architecture.md#Enforcement Guidelines]
- Enforcement Guideline #6 (No raw SQL — use frappe.qb): [Source: _bmad-output/planning-artifacts/architecture.md#Enforcement Guidelines]
- Enforcement Guideline #7 (i18n — frappe._() and __()): [Source: _bmad-output/planning-artifacts/architecture.md#Enforcement Guidelines]
- Enforcement Guideline #8 (frappe.enqueue for operations >1 second): [Source: _bmad-output/planning-artifacts/architecture.md#Enforcement Guidelines]
- Project Directory Structure (api/reports.py, utils/, components/reports/, pages/dashboard/): [Source: _bmad-output/planning-artifacts/architecture.md#Complete Project Directory Structure]
- Story 4.1 (Business Hours SLA Calculation — pause-on-status logic to mirror): [Source: _bmad-output/planning-artifacts/epics.md#Story 4.1]
- Story 6.1 (Custom Report Builder — shares helpdesk/api/reports.py): [Source: _bmad-output/planning-artifacts/epics.md#Story 6.1]
- Story 6.3 (CSAT Analytics Dashboard — shares desk/src/pages/dashboard/ directory): [Source: _bmad-output/planning-artifacts/epics.md#Story 6.3]

## Dev Agent Record

### Agent Model Used

_To be filled by implementing dev agent_

### Debug Log References

_None — story creation phase_

### Completion Notes List

_To be filled by implementing dev agent_

### File List

_To be filled by implementing dev agent upon completion_
