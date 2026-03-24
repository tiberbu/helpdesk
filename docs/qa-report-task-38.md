# QA Report: Task #38 — Story 4.1: Business Hours SLA Calculation Engine

**QA Date**: 2026-03-24
**QA Depth**: 1/1 (max depth reached)
**Tester**: Claude QA Agent (Opus)
**Status**: PASS (all ACs verified, no P0/P1 issues)

---

## Acceptance Criteria Results

### AC1: Team business hours (Mon-Fri 9:00-18:00 US/Eastern) — SLA timer counts business time only, pauses weekends
**Result: PASS**

**Evidence:**
- `helpdesk/utils/business_hours.py` implements `calculate_business_minutes()` with full timezone support via `pytz`
- Unit tests confirm:
  - Same-day within hours: Mon 10:00-12:00 = 120 min (test_same_day_within_hours)
  - Outside hours: Mon 19:00-21:00 = 0 min (test_same_day_outside_hours)
  - Weekend span: Fri 17:00-Mon 10:00 = 120 min (test_full_weekend_span)
  - Timezone conversion: US/Eastern 09:00-18:00 correctly maps to UTC 14:00-23:00 (test_different_timezone)
- SLA controller `calc_elapsed_time()` (line 412) delegates to business hours calculator
- API confirmed: SLA documents have timezone field set to "UTC" with 18 IANA zone options available
- All 21 unit tests pass in 0.006s

### AC2: Holiday calendar (HD Service Holiday List) linked to SLA — timer pauses on holidays
**Result: PASS**

**Evidence:**
- `HD Service Holiday List` doctype exists and is accessible via API
- Holiday list is linked from SLA doctype via `holiday_list` field (Link to "HD Service Holiday List")
- `get_holidays()` and `get_holidays_set()` methods load holiday dates from the linked holiday list
- Redis caching with 24h TTL on holiday data (`sla:holiday_set:{holiday_list}`)
- Unit test `test_holiday_exclusion`: Mon-Wed span with Tue as holiday = 1080 min (540+0+540), confirming holiday dates are excluded
- Cache invalidation on SLA update: `on_update()` clears holiday cache

### AC3: Existing pause-on-status (e.g., Waiting on Customer) works together with business hours
**Result: PASS**

**Evidence:**
- `subtract_pause_minutes()` function in `business_hours.py` correctly computes pause overlap with business hours
- `set_hold_time()` (line 233) calls `self.calc_elapsed_time(paused_since, now_datetime())` — this now uses the business hours calculator, meaning hold time is only counted during business hours
- Unit tests confirm:
  - `test_pause_status_compatibility`: 300 min - 2x60 min pause = 180 min
  - `test_pause_outside_business_hours_ignored`: Pauses outside business hours don't subtract anything
  - `test_pause_clamps_to_zero`: Result never goes below 0
- `sla_recalculation.py` respects paused status categories when recalculating

### AC4: SLA recalculation for 1000 tickets completes within 5 seconds with Redis caching
**Result: PASS**

**Evidence:**
- All 3 performance tests pass in 0.009s total:
  - `test_1000_business_minutes_calculations_under_5_seconds`: PASS
  - `test_cache_hit_rate_exceeds_90_percent`: PASS (950/1000 = 95% hit rate)
  - `test_recalculation_batch_throughput`: PASS
- Redis caching implemented:
  - Service day config: `sla:config:{name}` with 1h TTL
  - Holiday dates: `sla:holiday_set:{holiday_list}` with 24h TTL
  - SLA doc cache in recalculation job (in-memory dict)
- Batch processing: 100 tickets per batch, Redis run-lock prevents concurrent recalculations
- Recalculation API endpoint works: `POST enqueue_sla_recalculation` returns `{"message": "SLA recalculation enqueued."}`
- Permission check: unauthenticated calls return PermissionError

---

## Additional Verifications

### Migration Patch
**PASS** — `patches/v1_phase1/add_business_hours_to_sla.py` registered in `patches.txt` (line 61). Patch sets `timezone = "UTC"` and seeds Mon-Fri 09:00-18:00 for SLAs without working-hours rows.

### Utils Package Conversion
**PASS** — `helpdesk/utils.py` was converted to `helpdesk/utils/__init__.py` package. All 42 existing imports across 36 files continue to work.

### Scheduler Integration
**PASS** — `hooks.py` line 45 contains `check_sla_breaches` scheduler event (already present before this story).

### Schema Changes
**PASS** — `timezone` field added to `hd_service_level_agreement.json` as a Select field with 18 IANA timezone options, default "UTC". Confirmed in database via SQL.

### Security
**PASS** — `enqueue_sla_recalculation` is properly gated with `frappe.only_for(["System Manager", "Agent Manager"])`.

---

## Issues Found

### P2: Stale `utils.py` file in bench deployment
- **File**: `/home/ubuntu/frappe-bench/apps/helpdesk/helpdesk/utils.py`
- **Description**: The old `utils.py` file still exists alongside the new `utils/` directory in the bench copy. Python 3.14 correctly resolves the package (directory) over the file, so this does not cause runtime failures. However, it could confuse developers or tools.
- **Impact**: Low — no functional impact observed after gunicorn reload.
- **Note**: Not a code bug — this is a deployment artifact from the file-to-package conversion.

### P3: Unused import of private function `_normalize_time`
- **File**: `helpdesk/helpdesk/doctype/hd_service_level_agreement/hd_service_level_agreement.py`, line 22
- **Description**: `_normalize_time` is imported from `business_hours.py` but never used in the controller.
- **Impact**: Cosmetic — unused import of a private function.

---

## Console Errors
- Initial API call to SLA controller returned `ModuleNotFoundError: No module named 'helpdesk.utils.business_hours'; 'helpdesk.utils' is not a package` — this was due to stale gunicorn worker cache. After `kill -HUP` reload, all API calls succeed without errors.

---

## Regression Check
- All 42 existing `from helpdesk.utils import ...` statements verified to be unaffected by the package conversion
- SLA controller validation methods (`validate_priorities`, `validate_support_and_resolution`, etc.) unchanged
- Existing `calc_time()` method for computing response_by/resolution_by deadlines unchanged
- Holiday list integration unchanged (Redis caching added as enhancement)

---

## Test Results Summary

| Test Suite | Tests | Result | Time |
|-----------|-------|--------|------|
| `test_business_hours.py` (unit) | 21 | All PASS | 0.006s |
| `test_sla_performance.py` (perf) | 3 | All PASS | 0.009s |
| API: SLA recalculation endpoint | 1 | PASS | — |
| API: Permission check (unauthenticated) | 1 | PASS | — |
| API: SLA timezone field | 1 | PASS | — |
| API: Holiday list exists | 1 | PASS | — |

---

## Verdict

**ALL ACCEPTANCE CRITERIA PASS.** No P0 or P1 issues found. No fix task required.

Two minor issues noted (P2/P3) for future cleanup but neither blocks functionality.
