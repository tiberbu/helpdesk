# Story 4.3: SLA Compliance Dashboard

Status: ready-for-dev

## Story

As a team manager,
I want real-time SLA compliance metrics with drill-down capability,
so that I can monitor service quality and identify improvement areas across teams, agents, priorities, and categories.

## Acceptance Criteria

1. **[Dashboard Route and Overall Compliance Cards]** Given SLA data exists with business hours calculations (from Story 4.1) and breach status tracked in `agreement_status` (from Story 4.2), when a manager navigates to `/helpdesk/dashboard/sla`, then the page loads within 1 second (NFR-P-07) and displays: (a) an "Overall Response Compliance %" card as a large number with fraction (e.g., "87% — 261 / 300 responded in time"); (b) an "Overall Resolution Compliance %" card as a large number with fraction; (c) both cards update dynamically when filters are changed; (d) the page requires HD Agent or System Manager role to access.

2. **[Filter Bar — Date Range, Team, Agent, Priority, Category]** Given the SLA dashboard is open, when the manager interacts with the filter bar at the top of the page, then they can set: (a) a date range picker (default: last 30 days) that filters on `resolution_date` / `first_responded_on`; (b) a Team multi-select filter (linked to HD Team); (c) an Agent multi-select filter (linked to HD Agent, dynamically filtered by selected Team if any); (d) a Priority select filter (Urgent / High / Medium / Low); (e) a Category select filter (linked to HD Ticket Category); when any filter changes, all dashboard panels (compliance cards, drill-down table, trend chart, breach analysis) refresh simultaneously.

3. **[Drill-Down Table — By Team, Agent, Priority, Category]** Given the SLA dashboard is displayed with filters applied, when the manager selects a drill-down dimension (Team / Agent / Priority / Category) from a dimension toggle above the table, then a data table shows: (a) the dimension value (e.g., team name or agent name); (b) total tickets count; (c) response compliance % and fraction; (d) resolution compliance % and fraction; (e) average response time (business minutes); (f) average resolution time (business minutes); (g) breach count; the table is sortable by any column and supports pagination (50 rows per page); clicking a row in Team drill-down filters the Agent dimension to that team.

4. **[Trend Chart — Daily/Weekly/Monthly with Prior Period Comparison]** Given the SLA dashboard is displayed, when the manager views the trend chart panel and toggles between "Daily", "Weekly", and "Monthly" granularity, then: (a) a line chart renders showing response compliance % and resolution compliance % over the selected date range; (b) a second set of lines (dashed / muted color) shows the same metric for the equivalent prior period (same duration, shifted back); (c) the prior period lines are labeled "Prior Period" in the legend; (d) hovering over a data point shows a tooltip with: date label, current compliance %, prior period compliance %, and ticket count for that period bucket; (e) the chart uses `frappe-ui` chart primitives or an equivalent (e.g., chart.js via Vue wrapper).

5. **[Breach Analysis — By Category]** Given breach data exists (tickets where `agreement_status = "Failed"`), when viewing the breach analysis panel on the SLA dashboard, then: (a) a horizontal bar chart shows the top 10 breach categories by count, with category name and breach count labels; (b) if the ticket has no category set, it is grouped under "Uncategorized"; (c) clicking a category bar filters the main dashboard to show only that category.

6. **[Breach Analysis — By Time-of-Day]** Given breach data exists, when viewing the time-of-day breach distribution panel, then: (a) a heat map or bar chart shows breach count distributed across 24 hours of the day (x-axis: hour 0–23, y-axis: breach count); (b) the data represents the hour the ticket was created (i.e., when it entered the SLA clock), grouped by the team's configured timezone (default: system timezone); (c) a tooltip on each bar/cell shows: hour range (e.g., "14:00–15:00"), breach count, and % of total breaches for that period.

7. **[SLA Compliance Widget — Agent Home Page]** Given the SLA compliance widget is available, when an agent or manager configures their home page at `/helpdesk`, then: (a) an "SLA Compliance" widget is available in the widget picker; (b) when added, the widget displays: response compliance % (30-day rolling, circular gauge or percentage), resolution compliance % (30-day rolling), and a small trend arrow (up/down/flat) comparing to the prior 30 days; (c) the widget respects the same permission model as the full dashboard (agent sees their team's data; manager sees all); (d) widget loads within 1 second (NFR-P-07); (e) the widget links to the full `/helpdesk/dashboard/sla` page.

8. **[API — Compliance Overview Endpoint]** Given the API endpoint `helpdesk.api.sla.get_compliance_overview` exists and is `@frappe.whitelist()`, when called with parameters `date_from`, `date_to`, and optional `team`, `agent`, `priority`, `category`, then it returns: `{"response_compliance_pct": float, "response_met": int, "response_total": int, "resolution_compliance_pct": float, "resolution_met": int, "resolution_total": int}`; response compliance uses `first_responded_on <= first_response_by`; resolution compliance uses `agreement_status = "Met"` among resolved tickets; tickets without an SLA policy are excluded from compliance counts.

9. **[API — Compliance Trend Endpoint]** Given the API endpoint `helpdesk.api.sla.get_compliance_trend` exists, when called with `date_from`, `date_to`, `granularity` ("daily"/"weekly"/"monthly"), and optional filters, then it returns a time-series array of `{period_label, resolution_compliance_pct, response_compliance_pct, ticket_count}` for both the selected period and the prior equivalent period; prior period is auto-calculated as `(date_to - date_from)` shifted back by that same duration.

10. **[API — Drill-Down Endpoint]** Given the API endpoint `helpdesk.api.sla.get_compliance_by_dimension` exists, when called with `dimension` ("team"/"agent"/"priority"/"category"), `date_from`, `date_to`, and optional filters, then it returns an array of `{dimension_value, total_tickets, response_met, response_total, response_compliance_pct, resolution_met, resolution_total, resolution_compliance_pct, avg_response_minutes, avg_resolution_minutes, breach_count}`; the query uses `frappe.qb` for aggregation (no raw SQL).

11. **[API — Breach Analysis Endpoint]** Given the API endpoint `helpdesk.api.sla.get_breach_analysis` exists, when called with `date_from`, `date_to`, and optional filters, then it returns: (a) `by_category`: array of `{category, breach_count}` sorted desc, top 10; (b) `by_hour`: array of 24 objects `{hour, breach_count}` for hours 0–23; breach detection uses `agreement_status = "Failed"` on HD Ticket; all queries use `frappe.qb` and respect Frappe permission model.

12. **[Unit Tests — API Accuracy]** Given the unit test suite for SLA compliance API, when the tests run, then at minimum the following pass with 80%+ coverage (NFR-M-01): compliance % calculation correctness (response met/total, resolution met/total); edge case with zero tickets (returns 0% not division-by-zero); dimension drill-down returns correct groupings; trend endpoint returns correct prior-period calculation; breach analysis by category correctly groups "Uncategorized"; all endpoints return `frappe.PermissionError` for unauthenticated requests.

## Tasks / Subtasks

- [ ] Task 1 — Create `helpdesk/api/sla.py` with Compliance Overview Endpoint (AC: #8)
  - [ ] 1.1 Create `helpdesk/helpdesk/api/sla.py` (note: existing API files at `helpdesk/helpdesk/api/` — verify by checking `helpdesk/helpdesk/api/__init__.py`; if the module is at `helpdesk/api/` not `helpdesk/helpdesk/api/`, adjust path accordingly)
  - [ ] 1.2 Implement `get_compliance_overview(date_from, date_to, team=None, agent=None, priority=None, category=None)` decorated with `@frappe.whitelist()`:
        ```python
        @frappe.whitelist()
        def get_compliance_overview(date_from: str, date_to: str, team: str = None,
                                     agent: str = None, priority: str = None,
                                     category: str = None) -> dict:
            frappe.has_permission("HD Ticket", "read", throw=True)
            filters = _build_filters(date_from, date_to, team, agent, priority, category)
            # Count response compliance: first_responded_on <= first_response_by AND first_response_by IS NOT NULL
            # Count resolution compliance: agreement_status = "Met" among closed tickets
            ...
        ```
  - [ ] 1.3 Implement `_build_filters()` helper that converts API filter params to `frappe.qb` WHERE clauses; date filter applies to `resolution_date` for resolved tickets and `creation` for open tickets
  - [ ] 1.4 Use `frappe.qb` for all aggregation queries:
        ```python
        from frappe.query_builder.functions import Count, Avg
        ticket = frappe.qb.DocType("HD Ticket")
        query = (
            frappe.qb.from_(ticket)
            .select(Count("*").as_("total"))
            .where(ticket.first_response_by.isnotnull())
            ...
        )
        ```
  - [ ] 1.5 Handle edge case: if total tickets = 0, return `pct = 0.0` (avoid ZeroDivisionError)
  - [ ] 1.6 Ensure response uses `{"message": result}` format (standard Frappe whitelist return)

- [ ] Task 2 — Add Compliance Trend Endpoint (AC: #9)
  - [ ] 2.1 Implement `get_compliance_trend(date_from, date_to, granularity="daily", team=None, agent=None, priority=None, category=None)` in `sla.py`
  - [ ] 2.2 Implement period bucketing logic:
        - `"daily"`: group tickets by `DATE(resolution_date)` or `DATE(creation)` — iterate day by day
        - `"weekly"`: group by ISO week (YEARWEEK in MariaDB via `frappe.qb`)
        - `"monthly"`: group by YEAR+MONTH
  - [ ] 2.3 Calculate prior period: `prior_date_to = date_from - 1 day`, `prior_date_from = prior_date_to - (date_to - date_from)`; run the same bucketing query against the prior range and align by relative offset
  - [ ] 2.4 Return structure:
        ```python
        {
            "current": [{"period_label": "2026-03-01", "resolution_compliance_pct": 87.5, "response_compliance_pct": 91.2, "ticket_count": 24}, ...],
            "prior": [{"period_label": "2026-02-01", ...}, ...]
        }
        ```
  - [ ] 2.5 Limit result to a maximum of 90 data points per period (to avoid chart overload on large date ranges)

- [ ] Task 3 — Add Drill-Down and Breach Analysis Endpoints (AC: #10, #11)
  - [ ] 3.1 Implement `get_compliance_by_dimension(dimension, date_from, date_to, team=None, agent=None, priority=None, category=None)` in `sla.py`
  - [ ] 3.2 For each dimension, use the corresponding HD Ticket field:
        - `"team"` → `ticket.team`
        - `"agent"` → `ticket.assigned_to`
        - `"priority"` → `ticket.priority`
        - `"category"` → `ticket.category` (Link to HD Ticket Category)
  - [ ] 3.3 Use `frappe.qb` GROUP BY on the dimension field; include `Count("*")`, `Sum(Case when agreement_status="Met")`, `Avg(first_response_elapsed_minutes)` etc.
  - [ ] 3.4 For `avg_response_minutes` and `avg_resolution_minutes`: compute from stored SLA timestamps — `frappe.db` provides `first_responded_on`, `first_response_by`, `resolution_date`, `resolution_by` — calculate elapsed business minutes using utility from `helpdesk.utils.business_hours` if available; otherwise use calendar minutes as approximation and note this in the code comment
  - [ ] 3.5 Implement `get_breach_analysis(date_from, date_to, team=None, agent=None, priority=None, category=None)` in `sla.py`
  - [ ] 3.6 For `by_category`: query tickets with `agreement_status = "Failed"`, group by `category`, COALESCE null to `"Uncategorized"`, order by breach count DESC, LIMIT 10
  - [ ] 3.7 For `by_hour`: query tickets with `agreement_status = "Failed"`, extract HOUR from `creation` field (when ticket entered SLA clock), group by hour 0–23; return all 24 hours including those with 0 breaches

- [ ] Task 4 — Create SLA Dashboard Page Component (AC: #1, #2)
  - [ ] 4.1 Create `helpdesk/desk/src/pages/dashboard/SLADashboard.vue` as the main page component
  - [ ] 4.2 Implement the filter bar at the top using `frappe-ui` `FormControl` components:
        - Date range: two date pickers (`date_from`, `date_to`), defaulting to `today - 30 days` and `today`
        - Team: `createListResource("HD Team")` as a Select/Autocomplete
        - Agent: `createListResource("HD Agent")` filtered by selected team
        - Priority: static Select (`Urgent`, `High`, `Medium`, `Low`)
        - Category: `createListResource("HD Ticket Category")` as Autocomplete
        - A "Apply Filters" button or auto-apply on filter change using `watch()`
  - [ ] 4.3 Implement two large compliance cards using `frappe-ui` Card or custom Tailwind card:
        - Response Compliance: "87%" in large font, "261 / 300 responded on time" subtitle
        - Resolution Compliance: same pattern
        - Cards show loading skeleton while data fetches
  - [ ] 4.4 Register the route in `helpdesk/desk/src/router/index.ts` (or equivalent router file):
        ```typescript
        {
          path: "/helpdesk/dashboard/sla",
          component: () => import("../pages/dashboard/SLADashboard.vue"),
          meta: { auth: true }
        }
        ```
  - [ ] 4.5 Add a navigation link to the dashboard in the sidebar or dashboard menu (check existing dashboard navigation pattern — likely in `helpdesk/desk/src/pages/home/` or sidebar component)

- [ ] Task 5 — Implement Drill-Down Table Component (AC: #3)
  - [ ] 5.1 Create `helpdesk/desk/src/components/sla/SLADrillDownTable.vue` component
  - [ ] 5.2 Accept props: `dimension` ("team"|"agent"|"priority"|"category"), `filters` (date_from, date_to, team, agent, priority, category)
  - [ ] 5.3 Implement a dimension toggle bar (four buttons: Team / Agent / Priority / Category) that emits `update:dimension` to parent; active dimension highlighted
  - [ ] 5.4 Render a table using `frappe-ui` `ListView` or standard HTML table with Tailwind styling; columns: Dimension Value | Total Tickets | Response Compliance | Resolution Compliance | Avg Response Time | Avg Resolution Time | Breaches
  - [ ] 5.5 Make all column headers clickable for sorting (ascending/descending); implement client-side sort on fetched data
  - [ ] 5.6 Show compliance % as colored badges: ≥90% green, 75–89% yellow, <75% red (consistent with UX-DR-06 color coding principles)
  - [ ] 5.7 Add "Team" row click handler that emits `filter:team` event to parent to filter Agent drill-down to that team

- [ ] Task 6 — Implement Trend Chart Component (AC: #4)
  - [ ] 6.1 Create `helpdesk/desk/src/components/sla/SLATrendChart.vue` component
  - [ ] 6.2 Accept props: `filters`, `granularity` ("daily"|"weekly"|"monthly"), data fetched internally via `createResource`
  - [ ] 6.3 Implement granularity toggle buttons (Daily / Weekly / Monthly) at top of chart panel
  - [ ] 6.4 Render line chart with two series:
        - Current period: Response compliance % (solid line, primary color) + Resolution compliance % (solid line, secondary color)
        - Prior period: Same metrics (dashed line, muted variants)
  - [ ] 6.5 Chart implementation options (use whichever pattern exists in the codebase — check `helpdesk/desk/src/` for existing chart usage):
        - Option A: `frappe-ui` `AxisChart` / `LineChart` component if available
        - Option B: Wrap `Chart.js` (likely already a dependency) with Vue `ref` and `onMounted` canvas init
        - Option C: Use `@frappe/charts` if present in `package.json`
        Inspect `helpdesk/desk/package.json` before implementing to choose the right approach
  - [ ] 6.6 Implement tooltip showing: date label, current period response/resolution %, prior period response/resolution %, ticket count
  - [ ] 6.7 Add legend: "Response (Current)", "Resolution (Current)", "Response (Prior Period)", "Resolution (Prior Period)"

- [ ] Task 7 — Implement Breach Analysis Components (AC: #5, #6)
  - [ ] 7.1 Create `helpdesk/desk/src/components/sla/SLABreachByCategory.vue` component
  - [ ] 7.2 Render a horizontal bar chart (longest bar = most breaches) using the same chart library chosen in Task 6; show category name on Y-axis, breach count on X-axis; show count label on each bar
  - [ ] 7.3 Add click handler on each bar that emits `filter:category` to parent SLADashboard, causing the category filter to be set and all panels to refresh
  - [ ] 7.4 Create `helpdesk/desk/src/components/sla/SLABreachByHour.vue` component
  - [ ] 7.5 Render a bar chart with 24 bars (hours 0–23 on X-axis, breach count on Y-axis); highlight bars above average with a slightly darker color; add tooltip per bar: hour range, count, % of total breaches
  - [ ] 7.6 Add a note below the chart: "Times shown in [team timezone] timezone" if team filter is applied, or "Times shown in system timezone" otherwise

- [ ] Task 8 — Implement SLA Compliance Home Page Widget (AC: #7)
  - [ ] 8.1 Create `helpdesk/desk/src/components/sla/SLAComplianceWidget.vue` component
  - [ ] 8.2 The widget should display in a compact card format (matches the home page widget grid dimensions used by other widgets — inspect existing widgets in `helpdesk/desk/src/pages/home/` for sizing conventions)
  - [ ] 8.3 Show: Response Compliance % (large number with circular progress ring or text %) + Resolution Compliance % + trend arrow comparing current 30-day vs prior 30-day (↑ green if improved ≥2%, ↓ red if declined ≥2%, → gray if flat)
  - [ ] 8.4 Compute trend arrow: call `get_compliance_overview` twice (current 30 days, prior 30 days) or use a single `get_compliance_trend` call and compare first vs last bucket
  - [ ] 8.5 Add a "View Full Dashboard" link at bottom of widget → navigates to `/helpdesk/dashboard/sla`
  - [ ] 8.6 Register the widget in the home page widget registry — check `helpdesk/desk/src/pages/home/` for the pattern used to register widgets (likely a `widgets.ts` or `widgetConfig.ts` file); add `{ id: "sla_compliance", label: "SLA Compliance", component: SLAComplianceWidget }` to the registry
  - [ ] 8.7 Permission check in widget: if current agent's role is `HD Manager` or `System Manager`, show org-wide data; otherwise show data scoped to their team (pass `team` filter equal to agent's default team)

- [ ] Task 9 — Write Unit Tests for SLA Compliance API (AC: #12)
  - [ ] 9.1 Create `helpdesk/helpdesk/tests/test_sla_compliance_api.py` (or alongside `sla.py` as `test_sla.py` — follow existing test file placement convention for API files)
  - [ ] 9.2 `test_compliance_overview_correct_calculation` — create 10 test HD Ticket records: 8 with `agreement_status = "Met"`, 2 with `agreement_status = "Failed"`; call `get_compliance_overview` and assert `resolution_compliance_pct = 80.0`, `resolution_met = 8`, `resolution_total = 10`
  - [ ] 9.3 `test_compliance_overview_zero_tickets` — call `get_compliance_overview` with date range that has no tickets; assert `resolution_compliance_pct = 0.0` without raising ZeroDivisionError
  - [ ] 9.4 `test_compliance_overview_response_compliance` — create tickets with `first_responded_on` before `first_response_by` (met) and after (missed); assert response compliance % is correct
  - [ ] 9.5 `test_compliance_by_dimension_team` — create tickets assigned to two teams; call `get_compliance_by_dimension("team", ...)` and assert two rows returned, each with correct compliance counts
  - [ ] 9.6 `test_compliance_by_dimension_priority` — create tickets with different priorities; assert priority drill-down returns correct groupings
  - [ ] 9.7 `test_compliance_trend_prior_period_calculation` — call `get_compliance_trend` for a 7-day period; assert `prior` array covers the 7 days immediately preceding the request range
  - [ ] 9.8 `test_breach_analysis_by_category_uncategorized` — create breached tickets with null category; assert they appear under `"Uncategorized"` in `by_category`
  - [ ] 9.9 `test_breach_analysis_by_hour` — create breached tickets at creation hour=14; assert `by_hour[14]["breach_count"]` is correct, and all 24 hours are present in the array
  - [ ] 9.10 `test_api_requires_permission` — call endpoints without login; assert `frappe.PermissionError` is raised
  - [ ] 9.11 Run tests with: `bench --site <site> run-tests --module helpdesk.helpdesk.tests.test_sla_compliance_api`

## Dev Notes

### Architecture Patterns

- **Story Dependency (Critical):** This story depends on Stories 4.1 and 4.2. Story 4.1 provides the `agreement_status` field on HD Ticket (values: `"Met"`, `"Failed"`, `"First Response Due"`) and the business hours calculation engine at `helpdesk/helpdesk/utils/business_hours.py`. Story 4.2 ensures `agreement_status` is correctly set to `"Failed"` when breaches occur and sets `first_responded_on` upon first response. Do NOT start this story until Story 4.1 is at least in `review` status. [Source: _bmad-output/planning-artifacts/architecture.md#ADR-13]

- **No New DocTypes Required:** This story does not create new DocTypes — it reads from existing `HD Ticket`, `HD Team`, `HD Agent`, `HD Ticket Category`, and `HD Service Level Agreement` records. This is a pure read/analytics story. All writes (compliance status) are already handled by Stories 4.1 and 4.2.

- **API Module Location:** Architecture specifies new API modules at `helpdesk/helpdesk/api/` with the pattern `helpdesk.api.{module}`. Verify the actual path by inspecting `helpdesk/helpdesk/api/__init__.py`. The full method path for whitelisted calls will be `helpdesk.helpdesk.api.sla.get_compliance_overview` (or `helpdesk.api.sla.*` depending on app structure). [Source: _bmad-output/planning-artifacts/architecture.md#ADR-08]

- **`frappe.qb` for Aggregation Queries (Mandatory):**
  ```python
  from frappe.query_builder.functions import Count, Sum, Avg
  from frappe import qb

  ticket = qb.DocType("HD Ticket")
  result = (
      qb.from_(ticket)
      .select(
          ticket.team,
          Count("*").as_("total_tickets"),
          Sum(Case().when(ticket.agreement_status == "Met", 1).else_(0)).as_("resolution_met"),
      )
      .where(ticket.first_response_by.isnotnull())
      .where(ticket.creation >= date_from)
      .where(ticket.creation <= date_to)
      .groupby(ticket.team)
  ).run(as_dict=True)
  ```
  NEVER use raw SQL strings. `frappe.qb` is the correct tool for complex aggregation. [Source: _bmad-output/planning-artifacts/architecture.md#Enforcement Guidelines #6]

- **HD Ticket SLA Fields (from Story 4.1):** The following fields exist on HD Ticket and are used for compliance calculation:
  - `first_response_by`: datetime — SLA deadline for first response (set by SLA engine)
  - `first_responded_on`: datetime — actual first response timestamp (set when agent replies)
  - `resolution_by`: datetime — SLA deadline for resolution
  - `resolution_date`: datetime — actual resolution timestamp
  - `agreement_status`: Select — `"Met"` | `"Failed"` | `"First Response Due"` (set by Story 4.2's sla_monitor)
  If any of these field names differ from actual implementation in Story 4.1's file, the dev agent MUST inspect `helpdesk/helpdesk/doctype/hd_ticket/hd_ticket.json` before writing queries. [Source: _bmad-output/implementation-artifacts/story-4.1-business-hours-sla-calculation-engine.md]

- **Frontend Data Fetching Pattern (`createResource`):**
  ```typescript
  import { createResource } from 'frappe-ui'

  const complianceData = createResource({
    url: 'helpdesk.api.sla.get_compliance_overview',
    params: computed(() => ({
      date_from: filters.value.dateFrom,
      date_to: filters.value.dateTo,
      team: filters.value.team || undefined,
      agent: filters.value.agent || undefined,
      priority: filters.value.priority || undefined,
      category: filters.value.category || undefined,
    })),
    auto: true,
  })
  ```
  Use `computed()` for params so the resource auto-refetches when filters change. Show `complianceData.loading` state with a skeleton loader. [Source: _bmad-output/planning-artifacts/architecture.md#ADR-09, Enforcement Guideline #5]

- **Dashboard Page Route and Navigation:**
  Route `/helpdesk/dashboard/sla` must be added to `helpdesk/desk/src/router/index.ts` (or equivalent — locate by checking existing dashboard routes). The architecture shows the dashboard directory at `desk/src/pages/dashboard/` — inspect existing files there (e.g., for CSAT dashboard) to understand the established page structure. [Source: _bmad-output/planning-artifacts/architecture.md#ADR-09 New Page Components]

- **Chart Library Selection:** Before implementing chart components, inspect `helpdesk/desk/package.json` to determine which charting library is already used. Common choices in Frappe projects:
  - `@frappe/charts` — Frappe's own chart library (likely present)
  - `chart.js` + `vue-chartjs` — popular alternative
  - `frappe-ui` built-in chart components
  Choose the library already in `package.json` to avoid adding new dependencies. If no chart library exists, prefer `@frappe/charts` as it is Frappe-ecosystem-native.

- **Widget Registry Pattern:** Home page widgets in Frappe Helpdesk typically follow a registry pattern. Inspect `helpdesk/desk/src/pages/home/` (the `home/` directory listed in architecture). Look for any existing widget registration pattern or a `widgets.ts` / `widgetConfig.ts` file. The CSAT dashboard widget (Story 6.3 / FR-CS-02) is defined similarly — check `CSATDashboardWidget.vue` if it exists as a reference. [Source: _bmad-output/planning-artifacts/architecture.md#ADR-09 New Shared Components, csat/CSATDashboardWidget.vue]

- **Permission Model:** SLA dashboard is read-only. Apply `frappe.has_permission("HD Ticket", "read", throw=True)` at the start of every API method. On the frontend, the route guard should require `isAgent` or `isManager` authentication — follow the existing route meta pattern. Internal notes security boundary (NFR-SE-01) does not apply here, but Frappe's permission model applies to all ticket data queries automatically via `frappe.qb` (it respects DocType permissions). [Source: _bmad-output/planning-artifacts/architecture.md#ADR-04]

- **NFR-P-07 (Widget Load < 1 Second):** Dashboard widgets must load within 1 second. For the compliance overview endpoint, avoid joining more than 2 tables. Cache the 30-day compliance summary in Redis with a 5-minute TTL:
  ```python
  cache_key = f"sla_compliance_{date_from}_{date_to}_{team}_{agent}_{priority}_{category}"
  cached = frappe.cache().get_value(cache_key)
  if cached:
      return cached
  result = _compute_compliance(...)
  frappe.cache().set_value(cache_key, result, expires_in_sec=300)
  return result
  ```
  Cache keys must include all filter params to avoid stale cross-filter data. [Source: _bmad-output/planning-artifacts/epics.md#NFR-P-07]

- **i18n:** All user-facing labels (column headers, axis labels, tooltips) must use `frappe._("...")` in Python and `__("...")` in JavaScript/TypeScript. [Source: _bmad-output/planning-artifacts/architecture.md#Enforcement Guideline #3]

- **No New `hooks.py` Entries Needed:** This story adds no new scheduled jobs or doc_events. The SLA monitor cron (Story 4.2) already keeps `agreement_status` up to date. The dashboard is purely a read-time analytics view.

### Files to Create / Modify

| Action | Path | Notes |
|--------|------|-------|
| Create | `helpdesk/helpdesk/api/sla.py` | All four API endpoints (compliance_overview, compliance_trend, compliance_by_dimension, breach_analysis) — verify actual `api/` path by inspecting existing API modules |
| Create | `helpdesk/desk/src/pages/dashboard/SLADashboard.vue` | Main dashboard page (route: `/helpdesk/dashboard/sla`) |
| Create | `helpdesk/desk/src/components/sla/SLAComplianceWidget.vue` | Home page widget |
| Create | `helpdesk/desk/src/components/sla/SLADrillDownTable.vue` | Drill-down table with dimension toggle |
| Create | `helpdesk/desk/src/components/sla/SLATrendChart.vue` | Trend line chart with period comparison |
| Create | `helpdesk/desk/src/components/sla/SLABreachByCategory.vue` | Breach by category horizontal bar chart |
| Create | `helpdesk/desk/src/components/sla/SLABreachByHour.vue` | Breach by time-of-day bar chart |
| Modify | `helpdesk/desk/src/router/index.ts` | Add `/helpdesk/dashboard/sla` route (confirm file path by checking existing router) |
| Modify | `helpdesk/desk/src/pages/home/<WidgetRegistry>` | Register SLA Compliance widget — confirm exact file by inspecting `desk/src/pages/home/` |
| Create | `helpdesk/helpdesk/tests/test_sla_compliance_api.py` | Unit tests for all API endpoints (80%+ coverage) |

### Testing Standards

- Minimum 80% unit test coverage on all new backend Python code (NFR-M-01).
- Use `frappe.tests.utils.FrappeTestCase` as the base class for all Python test cases.
- Create test HD Ticket fixtures with explicit `agreement_status`, `first_responded_on`, `first_response_by`, `resolution_date`, `resolution_by` values — do not rely on SLA engine execution in unit tests.
- Mock `frappe.cache()` in unit tests to test cache hit/miss behavior independently.
- For frontend components, verify that `createResource` calls use the correct API method names (match exactly with the Python `@frappe.whitelist()` decorated function paths).
- Run backend tests with: `bench --site <site> run-tests --module helpdesk.helpdesk.tests.test_sla_compliance_api`

### Constraints

- **Do NOT add new DocTypes** — this story is entirely read-only analytics on existing data.
- **Do NOT modify `hooks.py`** — no new scheduler events or doc_events are needed.
- **All DB queries via `frappe.qb`** — no raw SQL strings (Architecture Enforcement Guideline #6).
- **Tickets without an SLA policy assigned must be excluded** from compliance counts — filter by `ticket.first_response_by IS NOT NULL` to identify SLA-tracked tickets.
- **Do NOT hard-code "Met"/"Failed" strings** — use `frappe._("Met")` / `frappe._("Failed")` for any user-facing display; use the raw values for DB filtering.
- **Respect Frappe's multi-tenancy** — all queries must use `frappe.qb` which automatically applies site-level data scoping.
- **Patches NOT required** — no schema changes are made in this story.

### Project Structure Notes

- **SLA components directory is new:** `helpdesk/desk/src/components/sla/` does not exist yet. Create it. The architecture defines `components/csat/`, `components/ticket/`, etc. as domain-specific component folders. The SLA folder follows the same pattern. [Source: _bmad-output/planning-artifacts/architecture.md#ADR-09 New Shared Components]
- **Dashboard page placement:** The architecture lists `desk/src/pages/dashboard/` as an existing directory. Inspect it for existing dashboard pages (e.g., MTTR dashboard from Story 6.4) to follow the same page layout conventions. The SLA dashboard must visually match any existing dashboard pages.
- **Widget story dependency chain:** Story 4.3 → SLA widget registered on home page. Story 6.3 (CSAT Dashboard) creates a similar `CSATDashboardWidget.vue` — inspect Story 6.3's implementation (if merged) before implementing the SLA widget to share any widget base component patterns.
- **Story dependency chain:** Story 4.1 (business hours engine + agreement_status fields) → Story 4.2 (breach detection sets agreement_status = "Failed", first_responded_on timestamps) → **Story 4.3 (reads this data for compliance analytics)**. Ensure Stories 4.1 and 4.2 are in `review` or `done` before starting 4.3.
- **API module registration:** Frappe discovers `@frappe.whitelist()` functions automatically if the module is in the app. No manual endpoint registration needed. However, the API module must be imported at least once — verify there is an `__init__.py` in the `api/` directory and that it either imports the module or Frappe's discovery mechanism handles it automatically (standard Frappe behavior).

### References

- FR-SL-03 (SLA Compliance Dashboard — real-time metrics, drill-down, trend charts, period comparison): [Source: _bmad-output/planning-artifacts/epics.md#Story 4.3]
- FR-SL-03 (SLA compliance dashboard with real-time metrics, drill-down by team/agent/priority): [Source: _bmad-output/planning-artifacts/epics.md#Functional Requirements]
- NFR-P-07 (Dashboard widget load < 1 second per widget): [Source: _bmad-output/planning-artifacts/epics.md#Non-Functional Requirements]
- NFR-M-01 (Minimum 80% unit test coverage on all new backend code): [Source: _bmad-output/planning-artifacts/epics.md#Non-Functional Requirements]
- NFR-SE-05 (Custom reports respect Frappe permission model): [Source: _bmad-output/planning-artifacts/epics.md#Non-Functional Requirements]
- UX-DR-06 (SLA breach color coding — yellow/orange/red zones): [Source: _bmad-output/planning-artifacts/epics.md#UX Design Requirements]
- ADR-08 (API Design — `@frappe.whitelist()` methods in `helpdesk/api/` modules): [Source: _bmad-output/planning-artifacts/architecture.md#ADR-08]
- ADR-09 (Frontend Component Organization — `pages/dashboard/`, `components/sla/`): [Source: _bmad-output/planning-artifacts/architecture.md#ADR-09]
- ADR-11 (State Management — `createResource` / Pinia stores): [Source: _bmad-output/planning-artifacts/architecture.md#ADR-11]
- ADR-13 (SLA Business Hours Calculation Engine — `agreement_status`, `utils/business_hours.py`): [Source: _bmad-output/planning-artifacts/architecture.md#ADR-13]
- AR-03 (Background jobs use Redis Queue — caching via `frappe.cache()`): [Source: _bmad-output/planning-artifacts/epics.md#Additional Requirements]
- AR-04 (No Custom Fields — use DocType JSON): [Source: _bmad-output/planning-artifacts/epics.md#Additional Requirements]
- Architecture Enforcement Guideline #6 (Never use raw SQL — use `frappe.qb`): [Source: _bmad-output/planning-artifacts/architecture.md#Enforcement Guidelines]
- API module structure (`helpdesk/api/sla.py` with `@frappe.whitelist()`): [Source: _bmad-output/planning-artifacts/architecture.md#ADR-08, API Module Structure]
- HD Ticket DocType: `helpdesk/helpdesk/doctype/hd_ticket/`
- HD Team DocType: `helpdesk/helpdesk/doctype/hd_team/`
- HD Ticket Category DocType: `helpdesk/helpdesk/doctype/hd_ticket_category/`
- HD Service Level Agreement DocType: `helpdesk/helpdesk/doctype/hd_service_level_agreement/`
- `sla_monitor.py` (breach detection, `agreement_status = "Failed"`): `helpdesk/helpdesk/doctype/hd_service_level_agreement/sla_monitor.py` (Story 4.1/4.2)
- Business hours utility: `helpdesk/helpdesk/utils/business_hours.py` (Story 4.1)
- Frontend stores: `helpdesk/desk/src/stores/`
- Frontend router: `helpdesk/desk/src/router/index.ts`
- Home page widgets: `helpdesk/desk/src/pages/home/`

## Dev Agent Record

### Agent Model Used

Claude Sonnet 4.5 (create-story workflow)

### Debug Log References

_None — story creation phase_

### Completion Notes List

_To be filled by implementing dev agent_

### File List

_To be filled by implementing dev agent upon completion_
