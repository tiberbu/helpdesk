# QA Report: Task #119 — Fix: Flaky time tracking tests (duplicate test, missing coverage, test isolation)

**Reviewer:** Adversarial Review (Opus)
**Date:** 2026-03-23
**Artifact reviewed:** Commit `fc98b5cfe` — changes to `helpdesk/api/time_tracking.py` and `helpdesk/helpdesk/doctype/hd_time_entry/test_hd_time_entry.py`
**Test runs:** 3 sequential runs (56 tests/27 errors, 56 tests/0 errors, 58 tests/0 errors)

---

## Acceptance Criteria Verification

### AC1: Duplicate test method removed
**FAIL (P2)** — The story claims "Duplicate test `test_add_entry_rejects_invalid_string_duration` was already absent from current file (resolved in a prior task); no removal needed." This is a cop-out. The original task description specifically said to remove the duplicate. The completion notes should have explicitly verified the prior task's removal instead of hand-waving it away. No evidence of verification was provided.

### AC2: Race condition fixed — `server_now` captured once in `stop_timer`
**PASS** — `now_datetime()` is now called exactly once as `server_now` (line 100) and reused for the future check (line 106), elapsed calc (line 122), and timestamp (line 146). Clean fix.

### AC3: Billable clamping fixed (`max(0, min(1, cint(billable)))`)
**PASS** — Both `stop_timer` (line 136) and `add_entry` (line 196) use the correct clamping expression. The old `1 if cint(billable) else 0` (which mapped `-1` to `1`) is gone.

### AC4: Three new tests added
**PASS** — `test_add_entry_rejects_non_numeric_billable`, `test_add_entry_clamps_billable_above_one`, `test_add_entry_clamps_negative_billable_to_zero` are present and pass.

### AC5: Test flakiness resolved
**FAIL (P1)** — Three consecutive test runs produced **different test counts**: 56, 56, 58. The first run had 27 errors (deadlock + global test record inconsistency). This is exactly the "oscillating test count" symptom the task was supposed to fix. The root cause — Frappe test infrastructure fragility with `Connected App` global records and database deadlocks during `setUp` — was not addressed. The completion notes claim "Cleared stale `.pyc` files before running tests" as the fix, but `.pyc` clearing is a one-time manual action, not a durable fix.

### AC6: Dev and bench copies in sync
**PASS** — `diff` between dev and bench copies shows zero differences for both `time_tracking.py` and `test_hd_time_entry.py`.

---

## Adversarial Findings (10+)

### Finding 1 (P1): `_require_int_str` does not catch `OverflowError` for `"inf"` / `"Infinity"`
`int(float("inf"))` raises `OverflowError`, not `ValueError`. The `except ValueError` on line 39 will not catch it. Passing `billable="inf"` or `duration_minutes="Infinity"` will produce an unhandled 500 error instead of a clean `ValidationError`. The downstream `MAX_DURATION_MINUTES` check would never execute because the crash happens first.

**Proof:**
```python
>>> int(float("inf"))
OverflowError: cannot convert float infinity to integer
```

**Fix:** Change `except ValueError` to `except (ValueError, OverflowError)`.

### Finding 2 (P1): Test count oscillates between 56 and 58 across runs
Three consecutive runs produced 56, 56, and 58 tests. The task's stated goal was to fix "Test count oscillation due to duplicate test" but the oscillation persists. The `TestIsAgentExplicitUser` class (4 tests) is intermittently not discovered by the Frappe test runner, causing 54+4=58 vs 54+2=56 fluctuation. This is the same class of flakiness the task was supposed to eliminate.

### Finding 3 (P2): No billable clamping tests for `stop_timer`
The new clamping tests (`test_add_entry_clamps_billable_above_one`, `test_add_entry_clamps_negative_billable_to_zero`) only cover `add_entry`. The identical clamping logic in `stop_timer` has zero test coverage for boundary values. If someone reverts the `stop_timer` clamping, no test would catch it.

### Finding 4 (P2): `_require_int_str` accepts scientific notation strings like `"1e10"` and `"1e308"`
`float("1e10")` succeeds and `int(float("1e10"))` produces `10000000000`. While the downstream `MAX_DURATION_MINUTES` check would reject this for `duration_minutes`, it's semantically wrong to accept scientific notation as "a valid integer." `"1e308"` produces an astronomically large integer that could cause memory issues before the bounds check.

### Finding 5 (P2): `tearDown` uses `frappe.db.rollback()` which is documented as unreliable
Per the project's own MEMORY.md: "APIs that call `frappe.db.commit()` make `tearDown`'s `frappe.db.rollback()` a no-op." While the time tracking API itself doesn't call `db.commit()`, Frappe's `insert()` may trigger implicit commits via hooks. The `_ensure_*` helper methods create persistent User records that survive rollback, leaking test state across runs. The recommended pattern (explicit `frappe.delete_doc()` + `frappe.db.commit()` in tearDown) is not used.

### Finding 6 (P2): `_ensure_*` helper methods are scattered and inconsistently placed
- `_ensure_hd_admin_user` is at line 152 (before its callers)
- `_ensure_agent_manager_user` is at line 433 (before its callers)
- `_ensure_system_manager_user` is at line 582 (AFTER its first use at line 489)

This disorganized layout makes maintenance error-prone. These should be `setUpClass` fixtures or at minimum grouped together at the top of the class.

### Finding 7 (P2): New `_require_int_str` edge-case tests only exercise `add_entry`, not `stop_timer`
Tests like `test_require_int_str_accepts_float_string_duration`, `test_require_int_str_rejects_empty_string_duration`, etc. all call `add_entry()`. None call `stop_timer()`. The `_require_int_str` function is shared, but the integration paths differ — `stop_timer` has additional parameters (`started_at`) and cross-checks (`elapsed_minutes`) that could interact with edge cases differently.

### Finding 8 (P3): The `_require_int_str` docstring claims "Behavior matches cint()" but it doesn't
The docstring says "Float strings ('3.5', '1.0') are accepted — cint('3.5') == 3 (truncates)." But `_require_int_str` calls `int(float(value.strip()))` while `cint()` uses `int(flt(value))` (Frappe's `flt()`, not Python's `float()`). These may diverge for locale-specific decimal separators or Frappe-specific edge cases. The claim of behavior matching is not formally verified.

### Finding 9 (P3): `test_require_int_str_accepts_boolean_true_duration` documents pass-through but doesn't test the boundary
The test documents that `True` passes through `_require_int_str` and becomes `1` via `cint(True)`. But it doesn't test `False`, which would become `0` via `cint(False)` and then fail the `< 1` check. The asymmetry is undocumented. Similarly, no test covers `duration_minutes=0.5` (a float, not a string), which `_require_int_str` passes through and `cint(0.5)` truncates to `0`, failing the `< 1` check.

### Finding 10 (P3): No test for `_require_int_str` with `"NaN"` string
`float("nan")` succeeds but `int(float("nan"))` raises `ValueError`. While this is caught, there's no explicit test documenting this behavior. Similarly, no test covers `"+3"` or `"-0"` as duration strings.

### Finding 11 (P3): `test_on_trash_allows_own_entry_direct_delete` doesn't actually test `on_trash()`
The test (line 344) calls `frappe.delete_doc()` which triggers `on_trash()` indirectly. But the test for `test_on_trash_blocks_other_agent_from_direct_delete` (line 322) calls `entry_doc.on_trash()` directly. The inconsistency means the "allows" test path doesn't verify the hook is actually called — it verifies the entire delete pipeline, which might succeed even if `on_trash()` were broken.

### Finding 12 (P3): The story completion notes claim "44 tests, all pass" but the actual count is 56-58
The completion notes say "Test suite: **44 tests, all pass** (up from 41 before this task)." But the actual test suite has 56-58 tests. This discrepancy (off by 12-14) suggests the agent may have run an older version of the file or a different test module. The claimed test count is unreliable evidence of correctness.

---

## Console Errors
N/A — This is a backend-only change. No frontend/browser testing applicable.

## Screenshots
N/A — Backend code changes only. Playwright MCP not available.

## Summary

| Severity | Count | Description |
|----------|-------|-------------|
| P1       | 2     | `OverflowError` crash on `"inf"` input; test count still oscillates |
| P2       | 5     | Missing `stop_timer` clamping tests; scientific notation accepted; unreliable tearDown; scattered helpers; integration paths untested |
| P3       | 5     | Docstring inaccuracy; boolean edge cases; NaN untested; inconsistent on_trash testing; wrong test count in notes |

**Verdict:** The core fixes (race condition, billable clamping) are correct and well-implemented. However, the task's primary goal — fixing test flakiness — is **not achieved**. Test count still oscillates (56 vs 58) and the first run of 3 produced 27 errors from deadlocks. The `_require_int_str` function has an `OverflowError` gap that allows `"inf"` to crash the API with an unhandled exception.
