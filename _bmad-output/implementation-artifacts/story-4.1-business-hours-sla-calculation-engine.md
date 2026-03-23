# Story 4.1: Business Hours SLA Calculation Engine

Status: ready-for-dev

## Story

As an administrator,
I want SLA timers to count only during business hours and exclude holidays,
so that SLA targets reflect actual working time and avoid penalising agents for off-hours periods.

## Acceptance Criteria

1. **[Business Hours Timer — Weekend Pause]** Given a team has business hours configured as Mon-Fri 9:00-18:00 in timezone US/Eastern, when a ticket is created at Friday 17:00 US/Eastern and no pause-on-status is active, then the SLA timer accumulates exactly 1 hour of business time for that Friday (17:00–18:00), pauses at 18:00, does not count any time over Saturday or Sunday, and resumes counting from Monday 09:00.

2. **[Holiday Calendar Integration]** Given an HD Service Holiday List is linked to an HD Service Level Agreement and that holiday list contains a date that falls on a weekday, when the SLA timer is being calculated and the current date matches a holiday, then the SLA timer pauses for the entire holiday day (zero business minutes accumulated for that date), and resumes on the next business day.

3. **[Pause-on-Status Compatibility]** Given an HD Service Level Agreement has pause-on-status configured (e.g., pausing when status is "Waiting on Customer"), when a ticket enters a pause status, then both the pause-on-status logic and the business hours logic apply together: the timer pauses on non-business hours AND on pause-status periods, and no double-counting of paused time occurs; elapsed business time is correctly calculated when the ticket exits the pause status during business hours.

4. **[Redis Caching for Performance]** Given the SLA recalculation background job is running, when it processes 1000 tickets, then it completes within 5 seconds (NFR-P-04), and service-day configuration and holiday list data are cached in Redis to prevent repeated database queries; the cache is invalidated when holiday list or business hours configuration changes.

5. **[Business Hours Calculator Module]** Given the `helpdesk/utils/business_hours.py` module exists, when `calculate_business_minutes(start, end, service_days, holidays, timezone)` is called with valid inputs, then it returns the correct integer count of business minutes elapsed, correctly handling: start/end on same day, overnight spans, multi-day spans crossing weekends, spans that cross holidays, and all-day non-business periods.

6. **[Per-Team Business Hours Configuration]** Given an HD Service Level Agreement is linked to a team, when business hours are configured on that SLA (or inherited from its linked team), then the business hours calculator uses those team-specific hours and timezone; different teams can have different working hours (e.g., US/Eastern 9:00-18:00 vs Asia/Kolkata 10:00-19:00) and each ticket's SLA is calculated using the SLA's configured timezone.

7. **[SLA Recalculation Background Job]** Given the SLA recalculation background job is enqueued, when it runs via `frappe.enqueue` on the `long` queue, then it re-evaluates `agreement_end_date` / `response_by` and `resolution_by` for all open tickets with an active SLA, applying the business hours logic, and persists the updated values without blocking ticket CRUD operations.

8. **[Scheduler Event — Every 5 Minutes]** Given the SLA monitor cron job is registered in `hooks.py` under `scheduler_events`, when the cron fires every 5 minutes, then `helpdesk.helpdesk.doctype.hd_service_level_agreement.sla_monitor.check_sla_breaches` is called, which identifies tickets approaching or past SLA breach thresholds (using business-hours-aware elapsed time) and enqueues breach alert notifications.

9. **[Unit Tests — Business Hours Edge Cases]** Given the unit test suite for `business_hours.py`, when the tests run, then at minimum the following cases pass with 80%+ coverage (NFR-M-01): same-day within hours, same-day outside hours, start before business hours, end after business hours, full weekend span, span crossing a holiday, span in a different timezone, zero-duration interval, and multi-timezone correctness.

10. **[Performance Test — 1000-Ticket Recalculation]** Given a test environment with 1000 open tickets all having active SLAs, when the background recalculation job is executed, then total wall-clock time is measured and asserted to be under 5 seconds (NFR-P-04); Redis cache hit rate is verified to be >90% during the run.

## Tasks / Subtasks

- [ ] Task 1 — Implement `helpdesk/utils/business_hours.py` — Pure business hours calculator (AC: #1, #2, #5, #6)
  - [ ] 1.1 Create `helpdesk/utils/__init__.py` if it does not exist (empty)
  - [ ] 1.2 Create `helpdesk/utils/business_hours.py` with `calculate_business_minutes(start, end, service_days, holidays, timezone)` implementing the day-by-day algorithm from ADR-13:
        1. Convert `start` and `end` to `pytz` timezone-aware datetimes in `timezone`
        2. Iterate day-by-day from `start.date()` to `end.date()`
        3. For each day: skip if date is in `holidays` set; skip if weekday is not in `service_days`
        4. Compute overlap between `[day_service_start, day_service_end]` and `[start, end]`
        5. Accumulate overlap in minutes
        6. Return total integer minutes
  - [ ] 1.3 Add helper `get_service_day_config(sla_name: str) -> dict` that returns working hours and timezone for a given SLA, fetching from `HD Service Level Agreement` fields
  - [ ] 1.4 Add helper `get_holiday_set(holiday_list_name: str) -> set[date]` that returns all holiday dates from `HD Service Holiday List` for the current year (±1 year buffer)
  - [ ] 1.5 Add helper `get_next_business_start(dt: datetime, service_days, holidays, timezone) -> datetime` that returns the next business hours start from a given datetime (used by SLA due date calculator)

- [ ] Task 2 — Integrate per-team business hours into HD Service Level Agreement DocType (AC: #6)
  - [ ] 2.1 Open `helpdesk/helpdesk/doctype/hd_service_level_agreement/hd_service_level_agreement.json`
  - [ ] 2.2 Add `Section Break` "Business Hours Configuration"
  - [ ] 2.3 Add `Select` field `timezone` with options listing major IANA timezones (e.g., "US/Eastern", "US/Pacific", "Europe/London", "Asia/Kolkata", "Asia/Kolkata", "Australia/Sydney", "UTC"), default "UTC"
  - [ ] 2.4 Add `Table` child field `service_days` linked to a new `HD SLA Service Day` child DocType with columns: `day_of_week` (Select: Monday–Sunday), `start_time` (Time), `end_time` (Time), `enabled` (Check)
  - [ ] 2.5 Create `helpdesk/helpdesk/doctype/hd_sla_service_day/` DocType (child) with fields: day_of_week, start_time, end_time, enabled
  - [ ] 2.6 Add `Link` field `holiday_list` linking to `HD Service Holiday List` (label: "Holiday Calendar")
  - [ ] 2.7 Add a default service days child row seed (Mon–Fri 09:00–18:00 enabled, Sat–Sun disabled) via `on_update` of HD Service Level Agreement controller or a migration patch
  - [ ] 2.8 Update `helpdesk/helpdesk/doctype/hd_service_level_agreement/hd_service_level_agreement.py` with a `validate()` method that ensures: at least one service day is enabled, start_time < end_time for all enabled days

- [ ] Task 3 — Create/extend HD Service Holiday List DocType (AC: #2)
  - [ ] 3.1 Check if `HD Service Holiday List` DocType already exists in the codebase
  - [ ] 3.2 If it does NOT exist: create `helpdesk/helpdesk/doctype/hd_service_holiday_list/` with fields: `holiday_list_name` (Data, mandatory), `from_date` (Date), `to_date` (Date), and a child table `holidays` → `HD Service Holiday` child DocType with fields: `holiday_date` (Date, mandatory), `description` (Data)
  - [ ] 3.3 If it DOES exist: verify it has at minimum `holiday_date` and `description` fields accessible via Frappe ORM; add missing fields as needed
  - [ ] 3.4 Add `__init__.py` files for any new DocType directories
  - [ ] 3.5 Verify `HD Service Holiday List` is listed in `helpdesk/helpdesk/doctype/__init__.py` or the modules.txt equivalent

- [ ] Task 4 — Implement Redis caching layer in business hours utilities (AC: #4)
  - [ ] 4.1 In `helpdesk/utils/business_hours.py`, wrap `get_service_day_config` with `frappe.cache().get_value(f"sla_config:{sla_name}", generator=lambda: _fetch_service_day_config(sla_name), expires_in_sec=3600)`
  - [ ] 4.2 Wrap `get_holiday_set` with `frappe.cache().get_value(f"holiday_set:{holiday_list_name}:{year}", generator=lambda: _fetch_holiday_set(...), expires_in_sec=86400)` (24-hour TTL for holiday data)
  - [ ] 4.3 Add cache invalidation in `HD Service Level Agreement` controller `on_update`: call `frappe.cache().delete_value(f"sla_config:{self.name}")`
  - [ ] 4.4 Add cache invalidation in `HD Service Holiday List` controller `on_update`: iterate linked SLAs and clear their holiday cache keys via `frappe.cache().delete_keys(f"holiday_set:{self.name}:*")`

- [ ] Task 5 — Integrate business hours calculator into SLA timer calculation pipeline (AC: #1, #3, #6)
  - [ ] 5.1 Locate the existing SLA elapsed-time / `agreement_end_date` calculation logic in `helpdesk/helpdesk/doctype/hd_ticket/hd_ticket.py` or SLA override files
  - [ ] 5.2 Replace or wrap the existing calendar-time calculation with a call to `calculate_business_minutes(ticket.creation, now, service_days, holidays, timezone)` when the linked SLA has business hours configured
  - [ ] 5.3 Ensure backward compatibility: if an SLA has no `service_days` configured or no timezone set, fall back to existing 24/7 calendar-time logic
  - [ ] 5.4 Implement pause-on-status compatibility (AC: #3): when computing elapsed time, subtract periods where ticket status was a pause status AND the clock was in business hours — use `HD Ticket Activity` or status change log to identify pause windows; intersect them with business hour windows before subtracting
  - [ ] 5.5 Update `response_by` and `resolution_by` fields on `HD Ticket` to reflect business-hours-aware deadlines when the ticket is first created or SLA is first applied

- [ ] Task 6 — Add SLA recalculation background job (AC: #7, #10)
  - [ ] 6.1 Create `helpdesk/helpdesk/doctype/hd_service_level_agreement/sla_recalculation.py` with function `recalculate_sla_for_open_tickets()`
  - [ ] 6.2 In `recalculate_sla_for_open_tickets()`: fetch all open HD Tickets with an active SLA using `frappe.db.get_all("HD Ticket", filters={"status": ["not in", ["Resolved", "Closed"]], "agreement_status": ["!=", ""]}, fields=["name", "sla", "creation", "first_response_time", "status"])` — paginate in batches of 100 to avoid memory issues
  - [ ] 6.3 For each batch, call the business hours calculator with cached config and update `resolution_by`, `response_by`, and `agreement_status` (Met / Failed / First Response Due) fields
  - [ ] 6.4 Expose `enqueue_sla_recalculation()` as a `@frappe.whitelist()` function that calls `frappe.enqueue("helpdesk.helpdesk.doctype.hd_service_level_agreement.sla_recalculation.recalculate_sla_for_open_tickets", queue="long", timeout=120)`

- [ ] Task 7 — Add scheduler event in `hooks.py` for SLA monitoring (AC: #8)
  - [ ] 7.1 Open `helpdesk/hooks.py`
  - [ ] 7.2 Add to `scheduler_events["cron"]` the key `"*/5 * * * *"` (every 5 minutes) pointing to `"helpdesk.helpdesk.doctype.hd_service_level_agreement.sla_monitor.check_sla_breaches"` if not already present (confirm no duplicate)
  - [ ] 7.3 Create `helpdesk/helpdesk/doctype/hd_service_level_agreement/sla_monitor.py` with `check_sla_breaches()` function that:
        a. Fetches all open tickets with SLA enabled
        b. Calculates remaining business time to `resolution_by` using `calculate_business_minutes(now, resolution_by, ...)`
        c. For tickets within warning thresholds (30, 15, 5 minutes remaining), publishes SLA warning events via `frappe.realtime.publish("sla_warning", {...}, room=f"ticket:{ticket_name}")`
        d. For breached tickets (remaining < 0), updates `agreement_status = "Failed"` and publishes `sla_breached` event
        e. Uses Redis-cached config to avoid DB overhead per ticket
  - [ ] 7.4 Ensure `sla_monitor.py` has a guard: skip tickets already marked as `agreement_status = "Failed"` to avoid redundant processing

- [ ] Task 8 — Write unit tests for business hours calculation edge cases (AC: #9)
  - [ ] 8.1 Create `helpdesk/utils/test_business_hours.py` (or place in `helpdesk/helpdesk/utils/` per project convention) using `frappe.tests.utils.FrappeTestCase` as base
  - [ ] 8.2 `test_same_day_within_hours` — start: Monday 10:00, end: Monday 12:00, service Mon-Fri 09:00-18:00 → expect 120 minutes
  - [ ] 8.3 `test_same_day_outside_hours` — start: Monday 19:00, end: Monday 21:00 → expect 0 minutes
  - [ ] 8.4 `test_start_before_business_hours` — start: Monday 07:00, end: Monday 11:00 → expect 120 minutes (09:00–11:00)
  - [ ] 8.5 `test_end_after_business_hours` — start: Monday 16:00, end: Monday 20:00 → expect 120 minutes (16:00–18:00)
  - [ ] 8.6 `test_overnight_to_next_day` — start: Monday 17:00, end: Tuesday 10:00 → expect 60 + 60 = 120 minutes (Mon 17:00-18:00, Tue 09:00-10:00)
  - [ ] 8.7 `test_full_weekend_span` — start: Friday 17:00, end: Monday 10:00 → expect 60 + 60 = 120 minutes (Fri 17:00-18:00, Mon 09:00-10:00)
  - [ ] 8.8 `test_holiday_exclusion` — start: Monday 09:00, end: Wednesday 18:00, Tuesday is a holiday → expect 2 days * 540 minutes = 1080 minutes (Monday + Wednesday only)
  - [ ] 8.9 `test_different_timezone` — start/end provided in UTC, team timezone is US/Eastern (UTC-5); assert minutes match expected business hours in US/Eastern, not UTC
  - [ ] 8.10 `test_zero_duration` — start == end → expect 0 minutes
  - [ ] 8.11 `test_pause_status_compatibility` — given a ticket with a 2-hour pause window during business hours, assert the pause window is subtracted from elapsed business time

- [ ] Task 9 — Write performance test for 1000-ticket recalculation (AC: #10)
  - [ ] 9.1 Create `helpdesk/helpdesk/doctype/hd_service_level_agreement/test_sla_performance.py`
  - [ ] 9.2 In `test_recalculation_1000_tickets_under_5_seconds`: create (or mock) 1000 HD Ticket records with SLA data in a test database; prime the Redis cache with service day and holiday data; call `recalculate_sla_for_open_tickets()` directly; assert `time.perf_counter()` delta < 5.0 seconds
  - [ ] 9.3 Add a cache-hit rate assertion: mock `frappe.cache().get_value` with a counter wrapper; after the run, assert cache misses <= 10% of total cache calls (i.e., >90% hit rate)
  - [ ] 9.4 Mark this test with `@unittest.skipUnless(os.environ.get("RUN_PERF_TESTS"), "Performance tests skipped — set RUN_PERF_TESTS=1")` so it does not run in CI by default

- [ ] Task 10 — Migration patch for new SLA fields (AC: #6)
  - [ ] 10.1 Create `helpdesk/patches/v1_phase1/add_business_hours_to_sla.py` with `execute()` function
  - [ ] 10.2 In `execute()`: for each existing `HD Service Level Agreement` record, if `service_days` child table is empty, seed default Mon-Fri 09:00-18:00 rows; set `timezone = "UTC"` if not set
  - [ ] 10.3 Register the patch in `helpdesk/patches.txt` (or `patches.json`) after existing Phase 1 patches

## Dev Notes

### Architecture Patterns

- **ADR-13 (SLA Business Hours Calculation Engine):** The business hours calculator lives at `helpdesk/utils/business_hours.py` as a pure-Python utility with no Frappe dependencies in its core calculation function. This makes it independently testable. The function signature is:
  ```python
  def calculate_business_minutes(
      start: datetime,
      end: datetime,
      service_days: list[dict],   # [{weekday: int, start_time: time, end_time: time}]
      holidays: set[date],        # Set of holiday dates
      timezone: str               # IANA timezone string e.g. "US/Eastern"
  ) -> int:
  ```
  The algorithm: convert start/end to target timezone, iterate day-by-day, skip non-service days and holidays, accumulate overlap minutes with service window. [Source: architecture.md#ADR-13]

- **Redis Caching Pattern:** Use `frappe.cache().get_value(key, generator=callable, expires_in_sec=N)` — never raw Redis client. Cache keys follow the pattern `sla_config:{sla_name}` and `holiday_set:{holiday_list}:{year}`. Cache TTL: SLA config 1 hour, holidays 24 hours. Invalidate on DocType `on_update`. [Source: architecture.md#ADR-13 Integration Points]

- **Background Job Pattern (AR-03):** SLA recalculation uses `frappe.enqueue()` on the `long` queue. Never call long-running recalculation synchronously from a ticket `validate` hook:
  ```python
  frappe.enqueue(
      "helpdesk.helpdesk.doctype.hd_service_level_agreement.sla_recalculation.recalculate_sla_for_open_tickets",
      queue="long",
      timeout=120,
      is_async=True,
  )
  ```
  [Source: architecture.md#ADR-12 Background Job Architecture]

- **Scheduler Events (hooks.py):** The every-5-minute cron for SLA breach detection is registered under `scheduler_events["cron"]["*/5 * * * *"]`. Architecture spec already cites this exact key. Verify there is no collision with existing entries. [Source: architecture.md#ADR-12 Scheduler Events]

- **Real-time Event Publishing:** SLA warning events are published via `frappe.realtime.publish("sla_warning", data, room=f"agent:{agent_email}")`. Room naming follows the architecture convention: `agent:{email}` for per-agent notifications, `ticket:{id}` for ticket-level updates. [Source: architecture.md#Communication Patterns]

- **Backward Compatibility (AR-04):** All new fields on `HD Service Level Agreement` are additive. Existing SLAs without `service_days` configured must fall back to 24/7 calendar-time calculation — never raise an error for empty `service_days`. The fallback condition is: `if not self.service_days: use_calendar_time()`.

- **Frappe ORM Rules (Architecture Enforcement #6):** Never use raw SQL. All DB access must use `frappe.db.get_all()`, `frappe.db.get_value()`, or `frappe.qb`. For the 1000-ticket batch query, use:
  ```python
  frappe.db.get_all("HD Ticket",
      filters={"status": ["not in", ["Resolved", "Closed"]]},
      fields=["name", "sla", "creation", "response_by", "resolution_by"],
      limit_page_length=100,
      limit_start=offset
  )
  ```

- **i18n:** All user-facing labels in DocType JSON and controller error messages must use `frappe._("...")` in Python and `__("...")` in JavaScript. [Source: architecture.md#Enforcement Guidelines #7]

- **Timezone Library:** Use Python's `pytz` (already a Frappe dependency) for timezone conversion. Do NOT use `datetime.timezone` for IANA timezone strings — only `pytz` handles the full IANA database correctly. Example:
  ```python
  import pytz
  tz = pytz.timezone("US/Eastern")
  localized = tz.localize(naive_dt)
  ```

### Files to Create / Modify

| Action | Path | Notes |
|--------|------|-------|
| Create | `helpdesk/utils/__init__.py` | Empty init if not exists |
| Create | `helpdesk/utils/business_hours.py` | Core business hours calculator (ADR-13) |
| Create | `helpdesk/utils/test_business_hours.py` | Unit tests for business hours (AC: #9) |
| Modify | `helpdesk/helpdesk/doctype/hd_service_level_agreement/hd_service_level_agreement.json` | Add timezone, service_days Table, holiday_list Link fields |
| Modify | `helpdesk/helpdesk/doctype/hd_service_level_agreement/hd_service_level_agreement.py` | Add validate(), business hours integration |
| Create | `helpdesk/helpdesk/doctype/hd_sla_service_day/` | New child DocType: day_of_week, start_time, end_time, enabled |
| Create or Modify | `helpdesk/helpdesk/doctype/hd_service_holiday_list/` | New DocType (or extend if exists) |
| Create | `helpdesk/helpdesk/doctype/hd_service_level_agreement/sla_monitor.py` | Every-5-min breach detection |
| Create | `helpdesk/helpdesk/doctype/hd_service_level_agreement/sla_recalculation.py` | Background recalculation job |
| Create | `helpdesk/helpdesk/doctype/hd_service_level_agreement/test_sla_performance.py` | Performance test (AC: #10) |
| Modify | `helpdesk/helpdesk/doctype/hd_ticket/hd_ticket.py` | Integrate business hours into SLA deadline calculation |
| Modify | `helpdesk/hooks.py` | Add `*/5 * * * *` scheduler event for SLA monitor |
| Create | `helpdesk/patches/v1_phase1/add_business_hours_to_sla.py` | Migration patch (AC: #6) |
| Modify | `helpdesk/patches.txt` | Register migration patch |

### Testing Standards

- Minimum 80% unit test coverage on all new backend code (NFR-M-01).
- Use `frappe.tests.utils.FrappeTestCase` as the base class for all test cases.
- Test cases must be self-contained; restore any DB changes using `addCleanup` or `tearDown`.
- Business hours tests do NOT require a running Frappe instance for the pure-calculation path — test the `calculate_business_minutes` function directly with in-memory inputs.
- Run tests with: `bench --site <site> run-tests --module helpdesk.utils.test_business_hours`
- Run performance test with: `RUN_PERF_TESTS=1 bench --site <site> run-tests --module helpdesk.helpdesk.doctype.hd_service_level_agreement.test_sla_performance`

### Constraints

- Do NOT break existing SLA functionality — all new fields are additive; existing `agreement_end_date` logic must remain intact when `service_days` is empty (backward compat AR-04).
- Do NOT call `recalculate_sla_for_open_tickets()` synchronously from any `validate` or `on_submit` hook — always enqueue to `long` queue (AR-03).
- The `calculate_business_minutes` core function must have NO Frappe imports — it must be a pure Python function for testability and reuse.
- All DocType fields added to `HD Service Level Agreement` must be declared in the DocType JSON, not via Custom Fields (AR-04).
- SLA recalculation background job must use pagination (100 records per batch) to stay within the 5-second target and avoid OOM issues on large installations.
- The 5-minute scheduler event must NOT block — if a previous cron run is still executing, the new invocation should detect this and skip (use a Redis lock with `frappe.cache().set_value("sla_monitor_lock", 1, expires_in_sec=240)`).

### Project Structure Notes

- **`helpdesk/utils/`** is a new directory per the architecture document's project structure. It houses shared utilities: `business_hours.py` (this story), `token.py` (CSAT, Story 3.7), and `sanitizer.py` (Chat, Story 3.1). Create `helpdesk/utils/__init__.py` as an empty file. [Source: architecture.md#Project Directory Structure]
- **`helpdesk/patches/v1_phase1/`** already created by Story 1.1. Add the new migration patch file here; update `patches.txt` with the new entry below existing Phase 1 patches. [Source: architecture.md#Project Directory Structure]
- **SLA monitor module location:** `helpdesk/helpdesk/doctype/hd_service_level_agreement/sla_monitor.py` — co-located with the SLA DocType controller following the pattern established in the architecture scheduler events section. [Source: architecture.md#ADR-12]
- **No conflicts detected:** The business hours calculation does not overlap with Story 4.2 (Proactive SLA Breach Alerts) beyond the shared `sla_monitor.py` — Story 4.2 builds the notification delivery on top of the breach detection events emitted by Story 4.1's `check_sla_breaches()`. Story 4.1 must be completed before Story 4.2.
- **Story dependency:** This story enhances the existing `HD Service Level Agreement` DocType. It does not depend on Epic 1 fields but is a prerequisite for Stories 4.2 (Proactive Alerts) and 4.3 (SLA Dashboard). The automation trigger `sla_warning` (Story 2.3) also relies on events emitted from `sla_monitor.py`.

### References

- FR-SL-01 (Business Hours and Holiday Calendars): [Source: _bmad-output/planning-artifacts/prd.md#FR-SL-01]
- FR-SL-01 Acceptance Criteria (business hours, holiday, pause-status): [Source: _bmad-output/planning-artifacts/epics.md#Story 4.1]
- NFR-P-04 (SLA recalculation < 5 seconds per 1000 tickets): [Source: _bmad-output/planning-artifacts/epics.md#Non-Functional Requirements]
- NFR-M-01 (80% unit test coverage): [Source: _bmad-output/planning-artifacts/epics.md#Non-Functional Requirements]
- ADR-13 (SLA Business Hours Calculation Engine — algorithm, integration, caching): [Source: _bmad-output/planning-artifacts/architecture.md#ADR-13]
- ADR-12 (Background Job Architecture — queue priorities, scheduler events): [Source: _bmad-output/planning-artifacts/architecture.md#ADR-12]
- AR-03 (Background jobs use Redis Queue): [Source: _bmad-output/planning-artifacts/epics.md#Additional Requirements]
- AR-04 (DocType JSON modification, not Custom Fields): [Source: _bmad-output/planning-artifacts/epics.md#Additional Requirements]
- AR-05 (Migration patches in helpdesk/patches/v1_phase1/): [Source: _bmad-output/planning-artifacts/epics.md#Additional Requirements]
- Enforcement Guidelines (no raw SQL, frappe.whitelist, i18n): [Source: _bmad-output/planning-artifacts/architecture.md#Enforcement Guidelines]
- Project directory structure (`helpdesk/utils/`, `patches/v1_phase1/`): [Source: _bmad-output/planning-artifacts/architecture.md#Project Directory Structure]
- Scheduler events (hooks.py `*/5 * * * *` cron): [Source: _bmad-output/planning-artifacts/architecture.md#ADR-12 Scheduler Events]
- Real-time room naming convention (agent:{email}, ticket:{id}): [Source: _bmad-output/planning-artifacts/architecture.md#Communication Patterns]
- HD Service Level Agreement DocType: `helpdesk/helpdesk/doctype/hd_service_level_agreement/`
- HD Ticket DocType: `helpdesk/helpdesk/doctype/hd_ticket/`
- hooks.py: `helpdesk/hooks.py`

## Dev Agent Record

### Agent Model Used

Claude Sonnet 4.5 (create-story workflow)

### Debug Log References

_None — story creation phase_

### Completion Notes List

_To be filled by implementing dev agent_

### File List

_To be filled by implementing dev agent upon completion_
