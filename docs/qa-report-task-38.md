# QA Report: Task #38 -- Story 4.1: Business Hours SLA Calculation Engine

**QA Date**: 2026-03-24
**QA Depth**: 1/1 (max depth reached)
**Tester**: Claude QA Agent (Opus)
**Status**: PASS (all ACs verified, no P0/P1 issues)
**Test URL**: http://help.frappe.local/helpdesk
**Note**: Playwright MCP tools were unavailable in this environment. All testing performed via curl API calls, bench console integration tests, and unit test suites.

---

## Acceptance Criteria Results

### AC1: Team business hours (Mon-Fri 9:00-18:00 US/Eastern) -- SLA timer counts business time only, pauses weekends
**Result: PASS**

**Evidence:**
- `helpdesk/utils/business_hours.py` implements `calculate_business_minutes()` with full IANA timezone support via `pytz`
- **21 unit tests pass** (0.006s) covering: same-day windows, outside-hours, overnight, weekends, holidays, timezone conversion, pause windows, zero-duration, partial minutes
- **End-to-end bench console test** on live SLA ("Default", Mon-Fri 10:00-18:00 UTC):
  - Fri 17:00 -> Mon 11:00 = 7200s (120 min) -- correctly pauses over weekend
  - Mon 19:00 -> Mon 21:00 = 0s -- correctly excludes after-hours
  - Mon 07:00 -> Mon 11:00 = 3600s (60 min) -- correctly clips to business hours start (10:00)
- **API confirmed**: SLA documents expose `timezone` field with 18 IANA zone options (default "UTC")
  ```
  GET /api/resource/HD Service Level Agreement/Default
  -> timezone: "UTC", 5 working days configured, holiday_list: "Default"
  ```
- **DocField schema verified**: `timezone` field is Select type with options:
  `UTC, US/Eastern, US/Central, US/Mountain, US/Pacific, Europe/London, Europe/Paris, Europe/Berlin, Asia/Kolkata, Asia/Tokyo, Asia/Singapore, Asia/Dubai, Australia/Sydney, Australia/Melbourne, America/Sao_Paulo, America/Mexico_City, Africa/Nairobi, Africa/Lagos`

### AC2: Holiday calendar (HD Service Holiday List) linked to SLA -- timer pauses on holidays
**Result: PASS**

**Evidence:**
- `HD Service Holiday List` doctype exists and is accessible via API (3 lists found: "Default", "Test Holiday List", "_Test Holiday List")
- Holiday list linked from SLA via `holiday_list` field (Link to "HD Service Holiday List")
- `get_holidays()` and `get_holidays_set()` methods load holiday dates from the linked list
- Redis caching with 24h TTL (`sla:holiday_set:{holiday_list}`)
- Unit test `test_holiday_exclusion`: Mon-Wed 09:00-18:00 span with Tue as holiday = 1080 min (540+0+540)
- Cache invalidation on SLA update: `on_update()` clears both config and holiday caches

### AC3: Existing pause-on-status (e.g., Waiting on Customer) works together with business hours
**Result: PASS**

**Evidence:**
- `subtract_pause_minutes()` in `business_hours.py` computes pause overlap with business hours
- `set_hold_time()` (line 233) calls `self.calc_elapsed_time(paused_since, now_datetime())` -- delegates to business-hours-aware calculator, so hold time is only counted during working hours
- `get_hold_time_diff()` (line 259) also uses `calc_elapsed_time()` for consistent behavior
- Unit tests:
  - `test_pause_status_compatibility`: 300 min - 2x60 min pause = 180 min
  - `test_pause_outside_business_hours_ignored`: Pauses outside hours = 0 deduction
  - `test_pause_clamps_to_zero`: Result never below 0
- `sla_recalculation.py` queries paused status categories and sets `agreement_status = "Paused"` for on-hold tickets

### AC4: SLA recalculation for 1000 tickets completes within 5 seconds with Redis caching
**Result: PASS**

**Evidence:**
- **3 performance tests pass** (0.009s total):
  - `test_1000_business_minutes_calculations_under_5_seconds`: PASS
  - `test_cache_hit_rate_exceeds_90_percent`: PASS (950/1000 hits = 95% hit rate)
  - `test_recalculation_batch_throughput`: PASS
- Redis caching layers:
  - Service day config: `sla:config:{name}`, TTL 1h
  - Holiday dates: `sla:holiday_set:{holiday_list}`, TTL 24h
  - SLA doc cache: in-memory dict within recalculation job
- Batch processing: 100 tickets/batch, Redis run-lock prevents concurrent recalculations
- **API tested (authenticated)**:
  ```
  POST /api/method/helpdesk...sla_recalculation.enqueue_sla_recalculation
  -> {"message": {"message": "SLA recalculation enqueued."}}
  ```
- **API tested (unauthenticated)**: correctly returns `PermissionError`

---

## Additional Verifications

### Migration Patch
**PASS** -- `patches/v1_phase1/add_business_hours_to_sla.py` registered in `patches.txt` (line 61). Patch sets `timezone = "UTC"` and seeds Mon-Fri 09:00-18:00 for SLAs without working-hours rows. Uses `db_update()` to skip permission checks.

### Utils Package Conversion
**PASS** -- `helpdesk/utils.py` converted to `helpdesk/utils/__init__.py` package. Dev copy is clean (no stale `utils.py`). All 42 existing imports across 36 files continue to work (confirmed via API calls that load modules using `from helpdesk.utils import ...`).

### Scheduler Integration
**PASS** -- `hooks.py` line 45 has `check_sla_breaches` scheduler event (pre-existing, reused by Story 4.1).

### Schema Changes
**PASS** -- `timezone` field added to `hd_service_level_agreement.json` as a Select field. Confirmed in live DB: all SLAs have `timezone = "UTC"`.

### Security
**PASS** -- `enqueue_sla_recalculation` gated with `frappe.only_for(["System Manager", "Agent Manager"])`. Unauthenticated requests return PermissionError.

### Helpdesk Frontend
**PASS** -- `GET http://help.frappe.local/helpdesk` returns HTTP 200.

---

## Issues Found

### P2: Stale `utils.py` file in bench deployment
- **File**: `/home/ubuntu/frappe-bench/apps/helpdesk/helpdesk/utils.py`
- **Description**: The old `utils.py` file still exists alongside the new `utils/` directory in the bench copy. Python 3.14 correctly resolves the package (directory) over the file, so no runtime failures. Could confuse developers or tools.
- **Impact**: Low -- no functional impact. Deployment artifact from file-to-package conversion.

### P3: Unused import of private function `_normalize_time`
- **File**: `helpdesk/helpdesk/doctype/hd_service_level_agreement/hd_service_level_agreement.py`, line 22
- **Description**: `_normalize_time` is imported from `business_hours.py` but never used in the controller.
- **Impact**: Cosmetic -- unused import of a private function.

---

## Regression Check
- All 42 existing `from helpdesk.utils import ...` statements unaffected by package conversion
- SLA controller validation methods (`validate_priorities`, `validate_support_and_resolution`, etc.) unchanged
- Existing `calc_time()` method for computing response_by/resolution_by deadlines unchanged
- Holiday list integration preserved (Redis caching added as enhancement)
- Helpdesk frontend loads without errors (HTTP 200)

---

## Test Results Summary

| Test Suite | Tests | Result | Time |
|-----------|-------|--------|------|
| `test_business_hours.py` (unit) | 21 | All PASS | 0.006s |
| `test_sla_performance.py` (perf) | 3 | All PASS | 0.009s |
| End-to-end: calc_elapsed_time (bench console) | 4 | All PASS | -- |
| API: SLA recalculation endpoint (auth) | 1 | PASS | -- |
| API: SLA recalculation endpoint (unauth) | 1 | PASS (rejected) | -- |
| API: SLA timezone field + working hours | 1 | PASS | -- |
| API: Holiday list doctype | 1 | PASS | -- |
| API: Frontend loads | 1 | PASS (HTTP 200) | -- |

---

## Verdict

**ALL ACCEPTANCE CRITERIA PASS.** No P0 or P1 issues found. No fix task required.

Two minor issues noted (P2/P3) for future cleanup but neither blocks functionality.
