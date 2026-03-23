# QA Report: Task #114 — Fix: before_delete->on_trash test mismatch (P0) + missing System Manager/stop_timer tests (P1)

**Reviewer:** Adversarial QA (Task #118)
**Date:** 2026-03-23
**Model:** opus
**Verdict:** CONDITIONAL PASS with 12 findings (0 P0, 2 P1, 5 P2, 5 P3)

---

## Acceptance Criteria Verification

### AC1: Add `test_delete_entry_system_manager_can_delete_any_entry`
**Status:** PASS

The test exists at line 567. It creates a bare System Manager user (no Agent/HD Admin role) via `_ensure_system_manager_user()` and verifies deletion of another agent's entry via `delete_entry()`. Test passes in the full suite (56/56 OK).

**Evidence:** `Ran 56 tests in 12.836s OK` — `test_delete_entry_system_manager_can_delete_any_entry` listed as passing.

### AC2: Add `test_stop_timer_rejects_non_numeric_duration`
**Status:** PASS

The test exists at line 585. It passes `duration_minutes="abc"` to `stop_timer()` and asserts `frappe.ValidationError` is raised. Test passes in suite.

**Evidence:** `test_stop_timer_rejects_non_numeric_duration` listed as passing.

### AC3: P0 fix — `before_delete()` -> `on_trash()` test mismatch
**Status:** PASS (pre-existing)

Per the completion notes, the P0 fix was already applied in prior commits. Lines 341 and 477 correctly call `entry_doc.on_trash()`. The model defines `on_trash()` at hd_time_entry.py:55. No mismatch remains.

### AC4: All tests pass
**Status:** PASS

56 tests pass, 0 failures, 0 errors.

### AC5: Files synced to bench
**Status:** PASS

`diff` between dev and bench copies shows zero differences for all three files (test file, model, API).

---

## Adversarial Review Findings

### Finding 1 — Test method names still reference `before_delete` despite the hook being `on_trash` (P2)

**Severity:** P2 (Misleading, maintenance hazard)

Two test methods use `before_delete` in their names but actually test `on_trash()`:
- `test_before_delete_hook_blocks_other_agent_from_direct_delete` (line 322)
- `test_before_delete_hook_allows_own_entry_direct_delete` (line 344)
- `test_before_delete_hook_allows_agent_manager_to_delete_any_entry` (line 463)

The *entire point of the P0 fix* was that the tests were calling `before_delete()` when the model defines `on_trash()`. Yet after the fix, the method *names* still say "before_delete". This is the exact kind of drift that caused the original P0. A future developer reading these test names will assume `before_delete` is the hook, not `on_trash`. The docstrings were updated but the names were not. Inconsistent naming after a naming-related P0 is a maintenance red flag.

### Finding 2 — No test for System Manager via `on_trash()` direct-delete path (P1)

**Severity:** P1 (Missing coverage for a claimed-fixed scenario)

The task added `test_delete_entry_system_manager_can_delete_any_entry` for the `delete_entry()` API path only. However, there are *parallel* tests for Agent Manager covering both paths:
- `test_agent_manager_can_delete_any_entry_via_delete_entry` (API path)
- `test_before_delete_hook_allows_agent_manager_to_delete_any_entry` (on_trash direct path)

System Manager has only the API-path test. There is **no** `test_on_trash_allows_system_manager_to_delete_any_entry` test. Since `on_trash()` is the REST DELETE bypass defense, the most critical path for System Manager is untested. The task description says "System Manager is in PRIVILEGED_ROLES" but doesn't verify it works through the direct-delete hook.

### Finding 3 — No test for HD Admin via `on_trash()` direct-delete path (P1)

**Severity:** P1 (Missing coverage parity)

Similarly, `_ensure_hd_admin_user()` and `test_delete_entry_admin_can_delete_any_entry` exist for the API path, but there is no corresponding `on_trash()` direct-hook test for HD Admin. Agent Manager has both paths tested, but HD Admin does not. This is an asymmetry in the test matrix that could hide a regression if `PRIVILEGED_ROLES` or `_check_delete_permission` is ever refactored.

### Finding 4 — `_ensure_*_user()` helpers create users that leak across tests (P2)

**Severity:** P2 (Test isolation concern)

The `_ensure_system_manager_user()`, `_ensure_hd_admin_user()`, and `_ensure_agent_manager_user()` helpers use "create if not exists" patterns. Since `tearDown` only does `frappe.db.rollback()`, these users **persist in the database across test runs** if any test in the suite calls `frappe.db.commit()` (which several Frappe internals do). The `if not frappe.db.exists(...)` guard hides the leak — on the second run the user already exists, so the test silently assumes prior state. This means:
- Tests are not truly isolated
- Role assignments from a prior test could pollute the next
- If someone changes the role setup in a helper, old leaked users retain old roles

### Finding 5 — Test uses `try/except` anti-pattern instead of `assertRaises` (P2)

**Severity:** P2 (Test quality)

`test_before_delete_hook_allows_agent_manager_to_delete_any_entry` (line 463) uses:
```python
try:
    entry_doc.on_trash()
except frappe.PermissionError:
    self.fail("...")
```

This is the inverted anti-pattern — it catches only `PermissionError`, but if `on_trash()` raises a *different* exception (e.g. `ValidationError`, `AttributeError`), the test passes silently. The correct pattern is to call `on_trash()` directly and let the test framework catch any unexpected exception. No `try/except` is needed for a "must not raise" test in unittest — just calling the method is sufficient; any exception will fail the test automatically.

### Finding 6 — `_require_int_str` does not handle `NaN` or `Infinity` float strings (P2)

**Severity:** P2 (Edge case)

`_require_int_str` uses `int(float(value.strip()))` to validate. However:
- `float("inf")` succeeds, then `int(float("inf"))` raises `OverflowError` (not `ValueError`)
- `float("nan")` succeeds, then `int(float("nan"))` raises `ValueError`

The `except ValueError` clause will not catch `OverflowError` for `"inf"` / `"infinity"`, meaning those strings will propagate as unhandled exceptions (500 server error) instead of a clean 417 ValidationError.

No test covers `duration_minutes="inf"` or `duration_minutes="nan"`.

### Finding 7 — `test_before_delete_hook_allows_own_entry_direct_delete` uses `ignore_permissions=True` (P2)

**Severity:** P2 (Test does not actually test what it claims)

Line 351: `frappe.delete_doc("HD Time Entry", entry_name, ignore_permissions=True)` is called to test "own entry direct delete." But `ignore_permissions=True` bypasses the Frappe permission layer entirely. The `on_trash()` hook is still called, so it partially works, but the test name says "direct delete" which implies testing the actual delete path a real agent would use. A real agent would NOT have `ignore_permissions=True`. The test could pass even if the DocType permissions were completely broken for Agent role.

### Finding 8 — No negative test for `start_timer` with non-existent ticket (P3)

**Severity:** P3 (Missing edge case)

`start_timer()` calls `frappe.has_permission("HD Ticket", "write", doc=ticket, throw=True)`. There is no test verifying what happens when `ticket` refers to a non-existent HD Ticket. The behavior is framework-dependent and untested.

### Finding 9 — `test_stop_timer_rejects_duration_exceeding_elapsed_time` is time-sensitive (P3)

**Severity:** P3 (Flaky test risk)

Line 543: `started_at = str(now_datetime() - datetime.timedelta(minutes=2))` with `duration_minutes=MAX_DURATION_MINUTES`. The test assumes the delta between "2 minutes ago" and "now" is stable, but test suite execution time, slow CI, or clock adjustments could affect this. The 5-minute tolerance constant (`_DURATION_ELAPSED_TOLERANCE_MINUTES`) is only 5 minutes, so this test is safe with MAX_DURATION=1440 vs elapsed=2, but the *pattern* of using `now_datetime()` in tests is fragile.

### Finding 10 — No test for concurrent deletion race condition (P3)

**Severity:** P3 (Missing coverage)

`delete_entry()` does a read-then-delete: it fetches the entry, checks permission, then deletes. If two requests arrive simultaneously, both could pass the permission check, and only the first delete succeeds while the second raises `DoesNotExistError`. There is no test documenting this behavior or verifying it degrades gracefully (e.g., with a proper error message rather than a traceback).

### Finding 11 — DocType JSON does NOT grant `delete` to Agent role, but `delete_entry()` uses `ignore_permissions=True` to bypass this (P3)

**Severity:** P3 (Architecture concern)

The Agent role in `hd_time_entry.json` (line 76-86) has `create:1, read:1, write:1` but no `delete:1`. The `delete_entry()` API compensates by using `ignore_permissions=True`. This means the ownership check in `_check_delete_permission` is the *only* barrier. If a developer adds a new delete path and forgets to call `_check_delete_permission`, agents could delete any entry. The `on_trash()` hook is the safety net, but the architecture relies on two independent checks staying in sync — a Single Responsibility violation.

### Finding 12 — `test_stop_timer_rejects_non_numeric_duration` duplicates existing coverage (P3)

**Severity:** P3 (Test bloat)

`test_stop_timer_rejects_non_numeric_billable` (line 521) already existed and tests the `_require_int_str` path for `stop_timer`. The new `test_stop_timer_rejects_non_numeric_duration` (line 585) tests the same `_require_int_str` function with a different parameter name. While testing both parameters is reasonable, the description in the task says "mirrors test_add_entry_rejects_non_numeric_duration for stop_timer" — but `test_stop_timer_rejects_non_numeric_billable` already proved `_require_int_str` works inside `stop_timer`. The marginal value of this test is low; it's testing framework wiring, not logic.

---

## Console Errors

API endpoints tested via curl — no unexpected errors. All validation paths return proper HTTP 417 with structured error messages.

---

## Summary

| Severity | Count | Description |
|----------|-------|-------------|
| P0       | 0     | No blocking issues |
| P1       | 2     | Missing on_trash tests for System Manager and HD Admin |
| P2       | 5     | Naming inconsistency, test isolation leaks, anti-pattern, edge case |
| P3       | 5     | Missing edge cases, architecture concerns, test bloat |

**Recommendation:** The P1 findings (missing `on_trash()` direct-delete tests for System Manager and HD Admin) should be addressed in a follow-up fix task. The naming inconsistency (P2, Finding 1) is ironic given the P0 that prompted this task was itself a naming mismatch, and should be cleaned up to prevent future confusion.
