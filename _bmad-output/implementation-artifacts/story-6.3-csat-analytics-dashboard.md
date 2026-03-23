# Story 6.3: CSAT Analytics Dashboard

Status: ready-for-dev

## Story

As a team manager,
I want to view CSAT scores by agent, team, time period, and category,
so that I can identify satisfaction trends and coaching opportunities.

## Acceptance Criteria

1. **[CSAT Dashboard Page]** Given a manager navigates to `/helpdesk/dashboard/csat`, when the page loads, then it displays all of the following metric panels: (a) overall CSAT score card showing the 30-day rolling average star rating (1.0–5.0, to one decimal place), (b) response rate percentage (surveys responded / surveys sent × 100, 30-day rolling), (c) rating distribution bar chart showing counts for each star level (1–5 stars), (d) score by agent table with columns: Agent Name, Average Score, Response Count, Trend (up/down/flat arrow), (e) score trend line chart showing the daily average CSAT score over the selected time period. The dashboard loads within 1 second per widget (NFR-P-07).

2. **[Date Range and Filters]** Given the CSAT dashboard is displayed, when the manager applies filters, then they can filter by: date range (preset options: Last 7 Days, Last 30 Days, Last 90 Days, Custom Range), team (multi-select from active HD Teams), agent (multi-select from active agents), and ticket category. All charts and tables update immediately when filters change. The default view is Last 30 Days with all teams and agents included.

3. **[Drill-Down to Individual Responses]** Given the CSAT dashboard is displayed, when the manager clicks on a specific agent row in the score-by-agent table or a specific bar in the rating distribution chart, then a slide-over panel opens showing the individual survey responses that make up that score. Each response in the panel shows: Star Rating (rendered as filled/empty stars), Customer Name, Ticket Link (navigates to `/helpdesk/tickets/{ticket_id}`), Agent Name, Submitted Date, and Comment (if any). The panel is dismissible (Escape key or close button).

4. **[`get_dashboard_data` API Endpoint]** Given a request to `helpdesk.api.csat.get_dashboard_data`, when called with optional parameters `date_from`, `date_to`, `team`, `agent`, `category`, then the backend queries HD CSAT Response records using `frappe.qb` (no raw SQL — Enforcement Guideline #6) and returns a JSON object with:
   - `overall_score`: float (average of all ratings in period, rounded to 1 decimal), or `null` if no responses
   - `response_rate`: float (responses received / surveys sent × 100, rounded to 1 decimal)
   - `total_responses`: int (count of HD CSAT Response records in period)
   - `total_surveys_sent`: int (count of HD CSAT Response records where rating is set + where rating is null and ticket is resolved in period)
   - `rating_distribution`: dict `{"1": count, "2": count, "3": count, "4": count, "5": count}`
   - `trend_data`: list of `{"date": "YYYY-MM-DD", "avg_score": float, "count": int}` sorted ascending by date
   The endpoint requires the caller to have read permission on HD CSAT Response (`frappe.has_permission("HD CSAT Response", "read", throw=True)`).

5. **[`get_agent_scores` API Endpoint]** Given a request to `helpdesk.api.csat.get_agent_scores`, when called with optional parameters `date_from`, `date_to`, `team`, `category`, then the backend groups HD CSAT Response records by `agent` and returns a list sorted by average score descending. Each entry contains: `agent` (email), `agent_name` (full name), `avg_score` (float, 1 decimal), `response_count` (int), `trend` (string: "up", "down", or "flat" — calculated by comparing current period avg to prior same-length period avg; "up" if delta > 0.1, "down" if delta < -0.1, "flat" otherwise). The endpoint requires read permission on HD CSAT Response.

6. **[Negative Feedback Alert]** Given a customer submits a CSAT rating of 1 or 2 stars, when the `HD CSAT Response` record's `after_insert` hook fires, then the system sends an in-app notification to the team manager(s) of the ticket's assigned team. The notification message is: "Low CSAT alert: [Customer Name] rated ticket #[Ticket ID] [Rating] stars. Agent: [Agent Name]" with a link to the ticket. The notification is delivered via `frappe.realtime.publish` to the `agent:{manager_email}` room (per AR-07 room naming convention). If the ticket has no assigned team or no manager is configured, the notification is sent to all users with the `HD Manager` or `System Manager` role. Email notification is optional and controlled by a configurable setting `csat_negative_alert_email` (default: false) in HD Settings.

7. **[`CSATDashboardWidget.vue` — Home Page Widget]** Given an agent has added the CSAT widget to their home page, when the home page loads, then the `CSATDashboardWidget.vue` component renders a compact widget card showing: (a) the agent's personal 30-day rolling average star rating displayed numerically (e.g., "4.2") with filled/empty star icons, (b) a trend arrow icon (up-arrow in green if current 30-day avg is > prior 30-day avg by more than 0.1; down-arrow in red if lower by more than 0.1; right-arrow in gray if flat), (c) response count subtitle ("Based on 23 responses"), (d) a "View Dashboard" link that navigates to `/helpdesk/dashboard/csat`. If the agent has no CSAT responses, displays "No ratings yet" placeholder. Widget loads within 1 second (NFR-P-07). The widget is an optional add-on to the existing agent home page widget configuration system.

8. **[`CSATScoreCard.vue` — Reusable Score Display]** Given the `CSATScoreCard.vue` component is used anywhere in the UI, when it receives `score` (Number, 1.0–5.0 or null), `count` (Number), and optional `trend` (String: "up"/"down"/"flat") props, then it renders: a large numeric score (e.g., "4.2"), a row of five star icons (filled proportionally to the score using full/half/empty star display), a small response count label ("23 responses"), and (when `trend` prop is provided) a colored trend arrow. When `score` is null, it shows "—" and greyed stars. The component is styled using Tailwind CSS classes and uses frappe-ui design tokens for colors (no inline styles).

9. **[Score Trend Line Chart]** Given the CSAT dashboard is displayed and `trend_data` is returned by `get_dashboard_data`, when the trend chart renders, then a line chart shows date on the X-axis and average CSAT score (0–5 scale) on the Y-axis. Data points represent daily averages; days with no responses are shown as gaps (not zero). The chart supports the same date range and filter options as the rest of the dashboard (AC: #2). The chart component uses the same charting library already present in the project (`@frappe/charts` if available, or the library used by Story 6.1).

10. **[Unit Tests — API Score Aggregation]** Given the CSAT API implementation, when the test suite runs, then unit tests for `get_dashboard_data` and `get_agent_scores` pass with minimum 80% code coverage (NFR-M-01). Required test cases: (a) `test_get_dashboard_data_no_responses` — returns null overall_score and 0 response_rate when no CSAT records exist; (b) `test_get_dashboard_data_calculates_correctly` — inserts 5 test HD CSAT Response records with known ratings, asserts correct overall_score, rating_distribution, and total_responses; (c) `test_get_dashboard_data_date_filter` — asserts date_from/date_to filters correctly scope results; (d) `test_get_agent_scores_grouping` — inserts responses for 2 different agents, asserts correct per-agent avg_score and response_count; (e) `test_get_dashboard_data_requires_permission` — call as Guest user, assert PermissionError; (f) `test_negative_feedback_alert_fires_for_1_star` — create HD CSAT Response with rating=1, assert notification is created for team manager; (g) `test_negative_feedback_alert_not_fired_for_3_star` — create HD CSAT Response with rating=3, assert no negative-alert notification is created.

11. **[Routes Registered]** Given the frontend router configuration, when the app loads, then route `/helpdesk/dashboard/csat` (component: `CSATDashboard.vue`) is registered and navigable. Navigating to the route while unauthenticated redirects to the login page. The route is accessible to users with `HD Manager`, `HD Admin`, or `System Manager` roles.

## Tasks / Subtasks

- [ ] Task 1 — Implement `get_dashboard_data` in `helpdesk/api/csat.py` (AC: #4)
  - [ ] 1.1 Open (or create) `helpdesk/api/csat.py`. Ensure `submit_rating` (from Story 3.7) is present or stubbed if not yet implemented. This task adds `get_dashboard_data` and `get_agent_scores` alongside it.
  - [ ] 1.2 Add `@frappe.whitelist()` decorator to `get_dashboard_data(date_from: str = None, date_to: str = None, team: str = None, agent: str = None, category: str = None)`.
  - [ ] 1.3 At the top of `get_dashboard_data`, call `frappe.has_permission("HD CSAT Response", "read", throw=True)`.
  - [ ] 1.4 Build a `frappe.qb` base query on the `HD CSAT Response` DocType. Apply filters: if `date_from` is set, add `WHERE submitted_at >= date_from`; if `date_to`, add `WHERE submitted_at <= date_to`; if `team`, join/filter on the associated HD Ticket's `team` field; if `agent`, filter `agent == agent`; if `category`, join/filter on HD Ticket's `category` field. Do NOT use raw SQL strings (Enforcement Guideline #6).
  - [ ] 1.5 Calculate `total_responses` (COUNT of records with `rating IS NOT NULL`). Calculate `total_surveys_sent` (COUNT of all records in period including those without a rating yet). Calculate `response_rate = (total_responses / total_surveys_sent * 100)` if total_surveys_sent > 0, else 0.0.
  - [ ] 1.6 Calculate `overall_score`: `AVG(rating)` over filtered records using `frappe.qb.functions.Avg`. Return `None` (JSON null) if no responses.
  - [ ] 1.7 Calculate `rating_distribution`: for each star level 1–5, count records where `rating == star_level`. Return as dict `{"1": n, "2": n, "3": n, "4": n, "5": n}`.
  - [ ] 1.8 Calculate `trend_data`: group filtered records by `DATE(submitted_at)`, computing AVG(rating) and COUNT(*) per day. Sort ascending. Map to list of `{"date": "YYYY-MM-DD", "avg_score": float, "count": int}`. Only include days that have at least one response (no synthetic zero-rows).
  - [ ] 1.9 Return the complete dict with all keys: `overall_score`, `response_rate`, `total_responses`, `total_surveys_sent`, `rating_distribution`, `trend_data`.

- [ ] Task 2 — Implement `get_agent_scores` in `helpdesk/api/csat.py` (AC: #5)
  - [ ] 2.1 Add `@frappe.whitelist()` decorator to `get_agent_scores(date_from: str = None, date_to: str = None, team: str = None, category: str = None)`.
  - [ ] 2.2 Call `frappe.has_permission("HD CSAT Response", "read", throw=True)`.
  - [ ] 2.3 Build a `frappe.qb` query grouped by `agent`, computing: `AVG(rating) AS avg_score`, `COUNT(*) AS response_count`, `agent`, joining with `tabUser` or using `agent_name` field (stored on HD CSAT Response) to get display name.
  - [ ] 2.4 For each agent row, compute the "trend" by running a second query for the prior same-length period. If `date_from` and `date_to` are set: prior period spans from `(date_from - period_length)` to `(date_from - 1 day)`. If no explicit dates (default 30-day): prior period is days 31–60. Calculate `delta = current_avg - prior_avg`. Set `trend = "up"` if delta > 0.1, `"down"` if delta < -0.1, `"flat"` otherwise. If no prior-period data exists, set `trend = "flat"`.
  - [ ] 2.5 Round `avg_score` to 1 decimal place. Sort results by `avg_score` descending.
  - [ ] 2.6 Return list of dicts: `[{"agent": email, "agent_name": str, "avg_score": float, "response_count": int, "trend": str}]`.

- [ ] Task 3 — Implement negative feedback alert in `hd_csat_response.py` controller (AC: #6)
  - [ ] 3.1 Open `helpdesk/helpdesk/doctype/hd_csat_response/hd_csat_response.py` (created in Story 3.7). Add `after_insert(self)` method (or extend if already exists).
  - [ ] 3.2 In `after_insert`: check `if self.rating and int(self.rating) <= 2:` — if true, proceed with notification.
  - [ ] 3.3 Fetch the associated HD Ticket to get `team` and `agent` fields: `ticket = frappe.get_doc("HD Ticket", self.ticket)`.
  - [ ] 3.4 Determine notification recipients: if `ticket.team` is set, get the `team_manager` from the HD Team record (`frappe.get_value("HD Team", ticket.team, "team_manager")`). If no manager found, fall back to all users with `HD Manager` or `System Manager` role: `frappe.get_all("Has Role", filters={"role": ["in", ["HD Manager", "System Manager"]]}, fields=["parent"], pluck="parent")`.
  - [ ] 3.5 For each recipient manager, publish a real-time notification via `frappe.realtime.publish("notification", {...}, room=f"agent:{manager_email}")` with payload: `{"type": "csat_negative_alert", "message": f"Low CSAT alert: {self.customer_name} rated ticket #{self.ticket} {self.rating} stars. Agent: {self.agent_name}", "ticket": self.ticket, "rating": self.rating}`.
  - [ ] 3.6 If `csat_negative_alert_email` setting is true in HD Settings, also send an email via `frappe.sendmail(recipients=[manager_email], subject=f"Low CSAT Alert — Ticket #{self.ticket}", message=...)`. Wrap in try/except to avoid blocking the main insert.
  - [ ] 3.7 Use `frappe.enqueue` to run the notification dispatch in the background (queue="short") so it does not delay the HTTP response (AR-03, NFR-A-01).

- [ ] Task 4 — Create `CSATDashboard.vue` page component (AC: #1, #2, #3, #9)
  - [ ] 4.1 Create directory `desk/src/pages/dashboard/` if it does not already exist. Create `desk/src/pages/dashboard/CSATDashboard.vue`.
  - [ ] 4.2 Use `<script setup lang="ts">` syntax (ADR-09 Vue component structure). Import `createResource` from `frappe-ui`.
  - [ ] 4.3 Declare reactive filter state: `dateRange` (ref, default: `{from: 30 days ago, to: today}`), `selectedTeams` (ref, default: `[]`), `selectedAgents` (ref, default: `[]`), `selectedCategory` (ref, default: `""`).
  - [ ] 4.4 Create a `dashboardResource` using `createResource` pointing to `helpdesk.api.csat.get_dashboard_data`. Wire filter state as params. Set `auto: true`. On change of any filter, re-fetch (use `watch` on filter state refs).
  - [ ] 4.5 Create an `agentScoresResource` using `createResource` pointing to `helpdesk.api.csat.get_agent_scores`. Wire the same filter params (excluding `agent` — that's a filter for get_dashboard_data scope only). Set `auto: true`.
  - [ ] 4.6 Implement filter bar at the top: Date range preset buttons (Last 7 Days, Last 30 Days, Last 90 Days) + custom date picker (frappe-ui DateRangePicker or DatePicker pair). Team multi-select. Agent multi-select (populated from a `createListResource` on HD Agent). Category select.
  - [ ] 4.7 Layout: 2-column summary row at top (Overall Score using `<CSATScoreCard>`, Response Rate card). Below: full-width Rating Distribution bar chart (horizontal bars, 1–5 stars). Below: two-column layout — Score by Agent table (left) and Score Trend line chart (right).
  - [ ] 4.8 Score by Agent table: render using frappe-ui ListView or a `<table>` with columns: Agent Name, Average Score (render as `<CSATScoreCard :score="row.avg_score" :count="row.response_count" :trend="row.trend" />` in compact mode), Response Count, Trend arrow. Each row is clickable (cursor-pointer). On row click: set `drillDownAgent = row.agent` and `showDrillDown = true`.
  - [ ] 4.9 Implement drill-down slide-over panel: when `showDrillDown = true`, render a side panel (frappe-ui Dialog or custom slide-over) that fetches individual responses via a `createResource` call to `frappe.client.get_list` (DocType: "HD CSAT Response", filters: `{agent: drillDownAgent, ...dateFilters}`, fields: `[name, rating, customer_name, ticket, agent, agent_name, submitted_at, comment]`). Render each response as a card with star display, customer name, ticket link, date, and comment. Close on Escape or close button.
  - [ ] 4.10 Implement rating distribution drill-down: clicking a bar (e.g., the "1 star" bar) opens the same drill-down slide-over but filtered to responses with that specific rating (set `drillDownRating` and pass to filter).
  - [ ] 4.11 Add loading skeleton states for all cards/charts while resources are loading. Use `dashboardResource.loading` for conditional skeleton display.
  - [ ] 4.12 Add empty state: when `dashboardResource.data.total_responses === 0`, display a centered empty state message: "No CSAT responses for the selected period. Responses appear here after customers submit surveys from resolved tickets."

- [ ] Task 5 — Create `CSATDashboardWidget.vue` component (AC: #7)
  - [ ] 5.1 Create `desk/src/components/csat/CSATDashboardWidget.vue`.
  - [ ] 5.2 Use `<script setup lang="ts">`. The component takes no required props (it auto-detects the current agent from session).
  - [ ] 5.3 Fetch the current agent's CSAT data using `createResource` calling `helpdesk.api.csat.get_agent_scores` with no team/category filters and `date_from = 30 days ago`. Filter the response to find the entry matching the current user's email (`frappe.session.user`).
  - [ ] 5.4 Separately fetch the prior-30-day average for trend calculation (or rely on the `trend` field returned by `get_agent_scores`).
  - [ ] 5.5 Render a compact card: title "My CSAT Score", large score number using `<CSATScoreCard :score="agentScore" :count="responseCount" :trend="trend" />` component. Add "Based on {count} responses" subtitle text.
  - [ ] 5.6 Add a "View CSAT Dashboard" link at the bottom that uses `router.push("/helpdesk/dashboard/csat")`.
  - [ ] 5.7 Show placeholder "No ratings yet" state when `responseCount === 0` or resource returns null data for this agent.
  - [ ] 5.8 Widget must render within 1 second (NFR-P-07). Use `auto: true` on the resource so it loads immediately on mount.

- [ ] Task 6 — Create `CSATScoreCard.vue` reusable component (AC: #8)
  - [ ] 6.1 Create `desk/src/components/csat/CSATScoreCard.vue`.
  - [ ] 6.2 Define props: `score` (Number | null, required), `count` (Number, default: 0), `trend` (String as "up" | "down" | "flat" | undefined, optional), `compact` (Boolean, default: false — controls size variant).
  - [ ] 6.3 Render large numeric score: `{{ score !== null ? score.toFixed(1) : "—" }}`. Use large text (`text-2xl font-bold` when not compact, `text-lg font-semibold` when compact) and use `text-gray-900` for scored, `text-gray-400` for null.
  - [ ] 6.4 Render five star icons. For each position 1–5: if `score >= position`, render a filled star (golden, `text-yellow-400`); if `score >= position - 0.5`, render a half star; otherwise render an empty star (`text-gray-300`). Use Lucide `Star` icon or SVG stars. When score is null, all stars are `text-gray-200`.
  - [ ] 6.5 Render response count label: `{{ count }} response{{ count !== 1 ? 's' : '' }}` in small text (`text-sm text-gray-500`).
  - [ ] 6.6 When `trend` prop is provided: render Lucide `TrendingUp` (green, `text-green-500`) for "up", `TrendingDown` (red, `text-red-500`) for "down", `Minus` (gray, `text-gray-400`) for "flat". Place icon inline after the score number.
  - [ ] 6.7 All colors use Tailwind CSS utility classes only (no inline styles). All text uses `frappe._()` / `__()` for i18n strings (Enforcement Guideline #7).

- [ ] Task 7 — Write unit tests for score aggregation API (AC: #10)
  - [ ] 7.1 Create `helpdesk/tests/test_csat_api.py` (or add to existing `helpdesk/helpdesk/doctype/hd_csat_response/test_hd_csat_response.py` if it exists from Story 3.7).
  - [ ] 7.2 Write `test_get_dashboard_data_no_responses`: call `get_dashboard_data()` with no pre-existing CSAT data for the test site, assert `overall_score is None` and `response_rate == 0.0` and `total_responses == 0`.
  - [ ] 7.3 Write `test_get_dashboard_data_calculates_correctly`: insert 5 HD CSAT Response records with ratings [5, 4, 3, 2, 1] using `frappe.get_doc({"doctype": "HD CSAT Response", ...}).insert(ignore_permissions=True)`. Call `get_dashboard_data()`. Assert `overall_score == 3.0`, `rating_distribution == {"1":1,"2":1,"3":1,"4":1,"5":1}`, `total_responses == 5`. Clean up with `addCleanup`.
  - [ ] 7.4 Write `test_get_dashboard_data_date_filter`: insert 2 responses dated 10 days ago and 2 responses dated 40 days ago. Call `get_dashboard_data(date_from=frappe.utils.add_days(today, -15))`. Assert `total_responses == 2` (only the recent ones).
  - [ ] 7.5 Write `test_get_agent_scores_grouping`: insert 3 responses for agent A (ratings 5,4,5) and 2 for agent B (ratings 2,3). Call `get_agent_scores()`. Assert agent A has `avg_score == 4.7` and `response_count == 3`; agent B has `avg_score == 2.5` and `response_count == 2`. Assert results are sorted descending by avg_score (agent A first).
  - [ ] 7.6 Write `test_get_dashboard_data_requires_permission`: use `frappe.set_user("Guest")`, call `get_dashboard_data()`, assert `frappe.PermissionError` is raised. Restore user in teardown.
  - [ ] 7.7 Write `test_negative_feedback_alert_fires_for_1_star`: set up a mock HD Team with a configured team_manager. Insert HD CSAT Response with `rating=1` linked to a ticket in that team. Assert a notification was published (mock `frappe.realtime.publish` or check notification log). Assert no exception raised.
  - [ ] 7.8 Write `test_negative_feedback_alert_not_fired_for_3_star`: insert HD CSAT Response with `rating=3`. Assert `frappe.realtime.publish` was NOT called with `csat_negative_alert` type.
  - [ ] 7.9 Ensure test module can be executed with: `bench --site <site> run-tests --module helpdesk.tests.test_csat_api`.

- [ ] Task 8 — Register frontend route (AC: #11)
  - [ ] 8.1 Open the frontend router file (`desk/src/router/index.ts` or similar).
  - [ ] 8.2 Add route: `{ path: "/helpdesk/dashboard/csat", component: () => import("@/pages/dashboard/CSATDashboard.vue"), name: "CSATDashboard" }` using lazy import for code splitting.
  - [ ] 8.3 If a navigation guard exists that restricts routes by role, ensure `CSATDashboard` is accessible to `HD Manager`, `HD Admin`, and `System Manager` roles.
  - [ ] 8.4 Verify no route conflict with existing dashboard routes (e.g., `/helpdesk/dashboard` for home).

- [ ] Task 9 — Register `CSATDashboardWidget` on agent home page widget system (AC: #7)
  - [ ] 9.1 Locate the existing agent home page widget registration mechanism (likely in `desk/src/pages/home/` or a widget registry file). Study how other home page widgets (e.g., SLA widget) are registered.
  - [ ] 9.2 Register `CSATDashboardWidget` as an available home page widget with: `id: "csat_score"`, `title: "My CSAT Score"`, `component: CSATDashboardWidget`, `description: "Your personal CSAT score and trend"`, `roles: ["HD Agent", "HD Manager"]`.
  - [ ] 9.3 Import the component lazily in the widget registry to avoid increasing bundle size for users who don't add the widget.

## Dev Notes

### Architecture Patterns

- **HD CSAT Response DocType** is created in Story 3.7. Story 6.3 DEPENDS on Story 3.7 being complete (or at minimum the DocType schema existing). The DocType fields include: `ticket` (Link→HD Ticket), `rating` (Int, 1–5), `comment` (Text), `customer` (Data), `customer_name` (Data), `agent` (Link→HD Agent), `agent_name` (Data), `team` (Link→HD Team), `submitted_at` (Datetime), `token_used` (Data, single-use token tracking). If Story 3.7 is not yet complete when implementing this story, consult the HD CSAT Response schema from architecture.md ADR-02 and create a minimal stub.

- **`frappe.qb` for aggregation** — Use Frappe's Query Builder for all dashboard aggregation queries. Example for rating distribution:
  ```python
  from frappe.query_builder import DocType
  from frappe.query_builder.functions import Count, Avg

  CSATResponse = DocType("HD CSAT Response")
  dist = (
      frappe.qb.from_(CSATResponse)
      .select(CSATResponse.rating, Count("*").as_("count"))
      .where(CSATResponse.rating.isnotnull())
      .groupby(CSATResponse.rating)
  ).run(as_dict=True)
  ```
  Never use `frappe.db.sql()` with raw string queries (Enforcement Guideline #6).

- **Background notification dispatch (AR-03)** — The negative feedback alert MUST be dispatched via `frappe.enqueue` on the "short" queue to keep the CSAT submission HTTP response fast. Pattern:
  ```python
  def after_insert(self):
      if self.rating and int(self.rating) <= 2:
          frappe.enqueue(
              "helpdesk.helpdesk.doctype.hd_csat_response.hd_csat_response.send_negative_alert",
              queue="short",
              csat_response_id=self.name
          )

  def send_negative_alert(csat_response_id: str):
      # Separate function (enqueueable) that does the notification logic
      ...
  ```

- **Real-time notification room naming (AR-07)** — Rooms are named `agent:{email}` (e.g., `agent:rajesh@example.com`). Publish via:
  ```python
  frappe.realtime.publish("notification", payload, room=f"agent:{manager_email}")
  ```
  This follows the Socket.IO room naming convention established in AR-07 and used by SLA alerts (FR-SL-02).

- **Trend calculation for agents** — The `trend` field in `get_agent_scores` compares current period vs prior same-length period. To avoid N+1 queries, fetch both periods in a single query by using `CASE WHEN` logic in `frappe.qb` or two separate aggregate queries (one per period). Two separate queries is simpler and acceptable given the typical number of agents (<100). Cache the result in Redis for 5 minutes if performance becomes an issue.

- **Frontend data fetching (Enforcement Guideline #5)** — All API calls from Vue components use `createResource` / `createListResource` from frappe-ui. Never use `axios` or `fetch` directly. The `createResource` pattern handles loading states, error handling, and caching automatically.

- **Vue component structure (ADR-09)** — All components use `<script setup lang="ts">` with TypeScript. Props must have explicit types. Composables use the `use` prefix (e.g., `useCSATData.ts` if shared logic warrants extraction).

- **Permission Model (ADR-04)** — CSAT Response read is allowed for Agent role. The API endpoints call `frappe.has_permission("HD CSAT Response", "read", throw=True)` before any data access. Negative alert notifications target managers via role lookup; only users with `HD Manager` or `System Manager` role receive alerts.

- **Performance (NFR-P-07)** — Dashboard widgets must load within 1 second. Use Redis caching for dashboard aggregation results with a 5-minute TTL if query performance is measured to be slow. Pattern:
  ```python
  cache_key = f"csat_dashboard_{frappe.local.site}_{hash(str(filters))}"
  cached = frappe.cache().get_value(cache_key)
  if cached:
      return cached
  result = compute_dashboard_data(...)
  frappe.cache().set_value(cache_key, result, expires_in_sec=300)
  return result
  ```

### Files to Create / Modify

| Action | Path | Notes |
|--------|------|-------|
| Modify | `helpdesk/api/csat.py` | Add `get_dashboard_data` and `get_agent_scores` endpoints alongside existing `submit_rating` (from Story 3.7) |
| Modify | `helpdesk/helpdesk/doctype/hd_csat_response/hd_csat_response.py` | Add `after_insert` hook for negative feedback alert + background job enqueue |
| Create | `helpdesk/tests/test_csat_api.py` | Unit tests for both API endpoints and alert logic (min 80% coverage, NFR-M-01) |
| Create | `desk/src/pages/dashboard/CSATDashboard.vue` | Main CSAT analytics dashboard page |
| Create | `desk/src/components/csat/CSATDashboardWidget.vue` | Home page compact CSAT score widget |
| Create | `desk/src/components/csat/CSATScoreCard.vue` | Reusable score + star + trend display card |
| Modify | `desk/src/router/index.ts` (or similar) | Register `/helpdesk/dashboard/csat` route |
| Modify | Home page widget registry (locate in `desk/src/pages/home/`) | Register `CSATDashboardWidget` as optional home page widget |

### Testing Standards

- Minimum 80% unit test coverage on all new backend code (NFR-M-01).
- Use `frappe.tests.utils.FrappeTestCase` as base class for all Python tests.
- Test data must be cleaned up in `tearDown` or via `addCleanup` to avoid polluting test DB state.
- Mock `frappe.realtime.publish` in tests to avoid actual WebSocket calls: use `unittest.mock.patch("frappe.realtime.publish")`.
- Test the `get_dashboard_data` endpoint with known data inserted directly (not via API) to avoid coupling to the `submit_rating` endpoint from Story 3.7.
- Run tests: `bench --site <site> run-tests --module helpdesk.tests.test_csat_api`

### Constraints

- Do NOT use raw SQL; all queries must use `frappe.qb` or `frappe.db.get_all()` with appropriate filters (Enforcement Guideline #6).
- Do NOT query HD Ticket communications or expose internal notes through any CSAT API response (NFR-SE-01).
- The `HD CSAT Response` DocType is created in Story 3.7. If Story 3.7 is not complete, this story cannot fully function — mark as a blocking dependency and implement the DocType stub if needed.
- Negative alert must be enqueued on "short" queue, NOT executed synchronously in `after_insert` (to protect core ticket/CSAT submission performance — NFR-A-01).
- `CSATScoreCard.vue` must handle null score gracefully (no divide-by-zero, no broken star rendering when count is 0).
- All user-facing strings use `frappe._()` in Python and `__()` in Vue (Enforcement Guideline #7).
- Dashboard route `/helpdesk/dashboard/csat` must not conflict with the existing `/helpdesk/dashboard` home page route.
- CSAT survey single-use token security (NFR-SE-03, ADR-06) is handled in Story 3.7's `submit_rating`. Story 6.3 only reads existing responses — no token logic needed here.

### Project Structure Notes

- **API location:** `helpdesk/api/csat.py` — as defined in ADR-08 (architecture.md). The file is shared with Story 3.7's `submit_rating` endpoint; Story 6.3 adds the two dashboard endpoints to the same module.
- **DocType controller:** `helpdesk/helpdesk/doctype/hd_csat_response/hd_csat_response.py` — per ADR-02 DocType structure. The `after_insert` hook for negative alerts is added here, not in `hooks.py`, since it is controller-specific logic.
- **Frontend components:** `desk/src/components/csat/` — per ADR-09 component organization (architecture.md lines 384–386 list `CSATDashboardWidget.vue` and `CSATScoreCard.vue` as defined components in this directory).
- **Dashboard page:** `desk/src/pages/dashboard/CSATDashboard.vue` — follows ADR-09 pages-by-feature-domain pattern. The `dashboard/` subdirectory under pages hosts all manager-facing dashboard views.
- **Dependencies:** Story 6.3 has a hard runtime dependency on Story 3.7 (CSAT Survey Infrastructure) for real data. However, the components, API endpoints, and tests can be built independently and will show empty/zero states until 3.7 is deployed and surveys are sent.
- **No new DocTypes required** — Story 6.3 is a read-only analytics layer on top of `HD CSAT Response` (created in 3.7). No new DocType JSON files need to be created.
- **Migration patches:** No schema changes required for Story 6.3 (read-only dashboard). No entry in `helpdesk/patches.txt` is needed.

### References

- FR-CS-02 (CSAT Dashboard AC): [Source: _bmad-output/planning-artifacts/epics.md#Story 6.3]
- FR-CS-02 (CSAT Dashboard full requirements): [Source: _bmad-output/planning-artifacts/prd.md#FR-CS-02]
- FR-CS-01 (CSAT Survey — produces the HD CSAT Response data this story reads): [Source: _bmad-output/planning-artifacts/prd.md#FR-CS-01]
- NFR-P-07 (Dashboard widget load < 1 second): [Source: _bmad-output/planning-artifacts/epics.md#Non-Functional Requirements]
- NFR-M-01 (80% unit test coverage): [Source: _bmad-output/planning-artifacts/epics.md#Non-Functional Requirements]
- NFR-SE-01 (Internal notes never exposed): [Source: _bmad-output/planning-artifacts/epics.md#Non-Functional Requirements]
- NFR-A-01 (Core ticketing unaffected by failures): [Source: _bmad-output/planning-artifacts/epics.md#Non-Functional Requirements]
- AR-03 (Background jobs via frappe.enqueue with named queues): [Source: _bmad-output/planning-artifacts/epics.md#Additional Requirements]
- AR-07 (Socket.IO room naming — `agent:{email}`): [Source: _bmad-output/planning-artifacts/epics.md#Additional Requirements]
- ADR-02 (HD CSAT Response DocType schema): [Source: _bmad-output/planning-artifacts/architecture.md#ADR-02]
- ADR-04 (Permission Model — CSAT Response read: Agent role, write: customer via token): [Source: _bmad-output/planning-artifacts/architecture.md#ADR-04]
- ADR-08 (API Design — csat.py endpoints: submit_rating, get_dashboard_data, get_agent_scores): [Source: _bmad-output/planning-artifacts/architecture.md#ADR-08]
- ADR-09 (Frontend Component Organization — csat/ components, dashboard/ pages): [Source: _bmad-output/planning-artifacts/architecture.md#ADR-09]
- ADR-11 (Pinia stores — notifications.ts for alert state): [Source: _bmad-output/planning-artifacts/architecture.md#ADR-11]
- ADR-12 (Background Job Architecture — "short" queue for notifications): [Source: _bmad-output/planning-artifacts/architecture.md#ADR-12]
- Communication Patterns (Socket.IO room `agent:{email}` for notifications): [Source: _bmad-output/planning-artifacts/architecture.md#Communication Patterns]
- Enforcement Guideline #6 (No raw SQL — use frappe.qb): [Source: _bmad-output/planning-artifacts/architecture.md#Enforcement Guidelines]
- Enforcement Guideline #7 (i18n — frappe._() and __()): [Source: _bmad-output/planning-artifacts/architecture.md#Enforcement Guidelines]
- Project Directory Structure (api/csat.py, components/csat/, pages/dashboard/): [Source: _bmad-output/planning-artifacts/architecture.md#Complete Project Directory Structure]
- Story 3.7 (CSAT Survey Infrastructure — creates HD CSAT Response DocType): [Source: _bmad-output/planning-artifacts/epics.md#Story 3.7]

## Dev Agent Record

### Agent Model Used

_To be filled by implementing dev agent_

### Debug Log References

_None — story creation phase_

### Completion Notes List

_To be filled by implementing dev agent_

### File List

_To be filled by implementing dev agent upon completion_
