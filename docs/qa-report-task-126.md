# Adversarial QA Report: Task #126 — Fix: Missing on_trash tests for System Manager/HD Admin + test naming inconsistency

**Reviewer:** Adversarial QA (Task #129)
**Date:** 2026-03-23
**Model:** opus
**Verdict:** CONDITIONAL PASS with 14 findings (0 P0, 3 P1, 6 P2, 5 P3)

---

## Acceptance Criteria Verification

### AC1: Add `test_on_trash_allows_system_manager_to_delete_any_entry`
**Status:** PASS

Test exists at line 479. Creates a bare System Manager user via `_ensure_system_manager_user()`, calls `entry_doc.on_trash()` directly, and verifies no PermissionError is raised. Test passes in the full 58-test suite.

**Evidence:** `Ran 58 tests in 14.554s OK`

### AC2: Add `test_on_trash_allows_hd_admin_to_delete_any_entry`
**Status:** PASS

Test exists at line 495. Creates an HD Admin user via `_ensure_hd_admin_user()`, calls `entry_doc.on_trash()` directly, and verifies no PermissionError is raised. Test passes.

**Evidence:** `test_on_trash_allows_hd_admin_to_delete_any_entry` listed in passing tests.

### AC3: Rename 3 test methods from `before_delete` to `on_trash`
**Status:** PASS

All three renames confirmed:
- `test_on_trash_blocks_other_agent_from_direct_delete` (line 322)
- `test_on_trash_allows_own_entry_direct_delete` (line 344)
- `test_on_trash_allows_agent_manager_to_delete_any_entry` (line 463)

No remaining `before_delete` references in test method names.

### AC4: Remove try/except anti-pattern in agent manager on_trash test
**Status:** PASS

Line 476 now calls `entry_doc.on_trash()` directly without try/except wrapper. Framework catches unexpected exceptions automatically.

### AC5: All tests pass
**Status:** PASS

58 tests pass, 0 failures, 0 errors. Dev and bench copies are identical.

### AC6: Files synced to bench
**Status:** PASS

`diff` between dev and bench copies returns zero differences for test file, model, and API.

---

## Adversarial Review Findings

### Finding 1 — Task #126 commit contains ZERO code changes (P1)

**Severity:** P1 (Process/integrity violation)

The commit `aafbe478a` (tagged as task #126) only modifies markdown story files and `sprint-status.yaml`. The **actual code changes** (renames, new tests, try/except removal) landed in commit `d1a9de058` ("Fix: P1 performance regression...") which was a DIFFERENT task. The story file for #126 claims "Status: done" and "All 58 tests pass" — but the task took credit for work that was committed under a different task's banner.

This means:
- Git history is misleading: `git log --oneline -- test_hd_time_entry.py` does NOT show commit `aafbe478a`
- Audit trail is broken: tracing which task made which change is impossible via git
- The story file's "Change Log" documents changes that don't exist in its own commit

### Finding 2 — The new on_trash tests only call `on_trash()` but never verify the entry is actually deletable end-to-end (P1)

**Severity:** P1 (Incomplete test coverage)

Both `test_on_trash_allows_system_manager_to_delete_any_entry` and `test_on_trash_allows_hd_admin_to_delete_any_entry` call `entry_doc.on_trash()` and verify it doesn't raise. But they never call `frappe.delete_doc()` or `delete_entry()` to confirm the entry is actually deleted. The test proves the hook doesn't block, but not that a full deletion succeeds. There could be other permission layers (DocType-level grants, controller permissions) that still block System Manager or HD Admin from actually completing a deletion. The Agent Manager already has a separate `test_agent_manager_can_delete_any_entry_via_delete_entry` test for the full API path — but System Manager and HD Admin do NOT have equivalent `delete_entry()` API-path tests.

Wait — `test_delete_entry_system_manager_can_delete_any_entry` (line 596) and `test_delete_entry_admin_can_delete_any_entry` (line 166) DO exist for the API path. So coverage IS complete for those two roles through `delete_entry()`. But `test_on_trash_allows_system_manager_to_delete_any_entry` still doesn't assert the entry *doesn't exist* after `on_trash()` — it only checks no exception is raised. This is weaker than the Agent Manager test pattern which also lacks an existence assertion after `on_trash()`, so it's at least consistent. Downgrading severity.

**Revised Severity:** P2

### Finding 3 — `_ensure_hd_admin_user` helper does not verify role was actually applied (P2)

**Severity:** P2 (Silent failure risk)

The `_ensure_hd_admin_user()` helper (line 152) calls `admin_user.add_roles("HD Admin")` but never asserts the role was actually applied. If "HD Admin" role doesn't exist in the system (e.g., after a migration error), `add_roles()` silently does nothing (no exception). The test would then pass because `on_trash()` would see a user with NO privileged roles, and if `entry.agent != user` is True (which it is), `PermissionError` would be raised — but the test expects NO exception. So in practice, a missing HD Admin role WOULD cause the test to fail. But the failure message would be confusing ("PermissionError raised") rather than clear ("HD Admin role does not exist").

The same issue affects `_ensure_system_manager_user()` and `_ensure_agent_manager_user()`.

### Finding 4 — Test user helpers use "create if not exists" pattern that leaks across test runs (P2)

**Severity:** P2 (Test isolation)

`_ensure_system_manager_user()`, `_ensure_hd_admin_user()`, and `_ensure_agent_manager_user()` all use `if not frappe.db.exists(...)` guards. Since `tearDown()` only calls `frappe.db.rollback()`, but Frappe internals sometimes call `frappe.db.commit()` during user creation, these users may persist across test runs. The "if not exists" guard masks this leak — on re-runs, the user already exists with potentially stale role assignments from a prior run. If a developer changes the role setup in the helper, old leaked users retain old roles until manually cleaned up.

This was already flagged as Finding 4 in the prior QA report (qa-report-task-114.md) and was NOT addressed by task #126. The task description only covered P1 and P2 items from the prior report but cherry-picked which ones to fix.

### Finding 5 — The `_require_int_str` function still doesn't handle `"inf"` / `"infinity"` strings (P1)

**Severity:** P1 (Unhandled exception → 500 error)

This was flagged as Finding 6 (P2) in the prior QA report (qa-report-task-114.md) and was NOT addressed. `int(float("inf"))` raises `OverflowError`, not `ValueError`, so the `except ValueError` clause in `_require_int_str` does not catch it. Passing `duration_minutes="inf"` to `add_entry()` or `stop_timer()` produces an unhandled 500 Internal Server Error instead of a clean 417 ValidationError.

This is arguably P1 because it's a server error from user-controlled input — any user can trigger it by passing `"inf"` as a string parameter to a whitelisted API.

### Finding 6 — `test_on_trash_allows_own_entry_direct_delete` still uses `ignore_permissions=True` (P2)

**Severity:** P2 (Test doesn't test what it claims)

Line 351: `frappe.delete_doc("HD Time Entry", entry_name, ignore_permissions=True)`. This test claims to verify "own entry direct delete" but `ignore_permissions=True` bypasses the Frappe permission layer entirely. The `on_trash()` hook is still called, so ownership IS checked — but if the DocType permission grants for Agent were broken, this test would still pass. A real agent going through REST DELETE would NOT have `ignore_permissions=True`.

This was flagged as Finding 7 (P2) in the prior QA report and was NOT addressed by task #126.

### Finding 7 — No assertion that `on_trash()` tests are actually running the permission check path (P2)

**Severity:** P2 (Weak assertions)

The new `on_trash` tests for System Manager and HD Admin simply call `entry_doc.on_trash()` and rely on the absence of an exception as proof of success. But if `on_trash()` were accidentally emptied or the `_check_delete_permission` call were removed, the tests would still pass (no exception from an empty method). There is no positive assertion — e.g., verifying that `_check_delete_permission` was called, or that `frappe.get_roles()` returned the expected roles for the test user.

The negative test (`test_on_trash_blocks_other_agent_from_direct_delete`) provides confidence that `on_trash()` does SOMETHING — but the positive tests for privileged roles have no way to distinguish "hook ran and allowed" from "hook is a no-op."

### Finding 8 — 58 test methods in a single class is a maintenance problem (P2)

**Severity:** P2 (Code quality / maintainability)

`TestHDTimeEntry` has grown to 54 test methods (plus 4 in `TestIsAgentExplicitUser`). The class mixes concerns: add_entry validation, stop_timer validation, delete_entry permissions, on_trash hooks, input sanitization, timezone handling, billable clamping, and more. This violates the Single Responsibility Principle for test classes. Test method ordering in the file is chaotic — `_ensure_system_manager_user()` is defined at line 582 but the on_trash tests using it are at line 479, requiring the reader to scroll back and forth. Related tests are not grouped in inner classes or separate test files.

### Finding 9 — Story file says "58 tests pass" but the commit itself changed zero test files (P3)

**Severity:** P3 (Documentation accuracy)

The story-126 completion notes say "All 58 tests pass (58/58 OK)" but the commit `aafbe478a` made zero changes to any `.py` file. The tests pass because they were already passing BEFORE this commit was created. The story is technically accurate (tests do pass) but misleading (implies this commit made them pass).

### Finding 10 — Missing test for `delete_entry` with non-existent entry name (P3)

**Severity:** P3 (Missing edge case)

`delete_entry()` calls `frappe.get_doc("HD Time Entry", name)` which raises `DoesNotExistError` if the name is invalid. There is no test verifying this path returns a sensible error rather than a raw traceback.

### Finding 11 — `_ensure_hd_admin_user` is defined inline instead of in `test_utils.py` (P3)

**Severity:** P3 (Code reuse)

Three separate `_ensure_*_user()` helpers follow the same pattern (create user, add role) but are defined as private methods in the test class. `test_utils.py` already provides `create_agent()` for the Agent role. The HD Admin, System Manager, and Agent Manager helpers should follow the same pattern and be reusable from `test_utils.py` for consistency and reuse across future DocType tests.

### Finding 12 — No test verifies that `PRIVILEGED_ROLES` frozenset matches the DocType JSON permissions (P3)

**Severity:** P3 (Drift risk)

`PRIVILEGED_ROLES = frozenset({"HD Admin", "Agent Manager", "System Manager"})` in `hd_time_entry.py` must stay in sync with the `delete:1` grants in the DocType JSON file. If a developer adds a new role with `delete:1` to the JSON but forgets to update `PRIVILEGED_ROLES`, on_trash will block that role's deletion. There is no integration test that reads the DocType JSON and verifies `PRIVILEGED_ROLES` matches.

### Finding 13 — `test_on_trash_allows_own_entry_direct_delete` doesn't actually call `on_trash()` (P3)

**Severity:** P3 (Misleading test name vs. test section header)

The test is under the `# --- on_trash ownership hook tests ---` section and its name says "on_trash allows own entry." But the implementation calls `frappe.delete_doc()` (which internally calls `on_trash`), not `entry_doc.on_trash()` directly like the other on_trash tests do. This is a semantic inconsistency — other on_trash tests call the hook directly, this one tests it indirectly through the delete path. The inconsistency makes the test suite harder to reason about when debugging a failure.

### Finding 14 — Prior QA findings (qa-report-task-114.md) marked as P2 were not all addressed (P3)

**Severity:** P3 (Process gap)

The task #126 description says it fixes "P1/P2 from QA #118" but the qa-report-task-114.md contains 5 P2 findings:
1. Finding 1 (P2): Test naming inconsistency — **FIXED**
2. Finding 4 (P2): Test user leak — **NOT FIXED**
3. Finding 5 (P2): try/except anti-pattern — **FIXED**
4. Finding 6 (P2): `_require_int_str` inf/nan — **NOT FIXED** (arguably P1)
5. Finding 7 (P2): `ignore_permissions=True` in own-entry test — **NOT FIXED**

Only 2 of 5 P2 items were addressed. The task description was selective about which P2s to include, and the ones omitted were silently dropped without documentation explaining why they were deferred.

---

## Test Execution Evidence

```
Ran 58 tests in 14.554s
OK
```

All 58 tests pass. Dev and bench copies are identical (zero diff).

---

## Console Errors

No console errors — this is a backend-only test file change with no frontend component.

---

## Summary

| Severity | Count | Description |
|----------|-------|-------------|
| P0       | 0     | No blocking issues |
| P1       | 3     | Commit contains no code (process), `_require_int_str` inf/nan uncaught, incomplete API-path parity (revised to P2) |
| P2       | 6     | No post-delete assertion, role verification gaps, test isolation leaks, ignore_permissions, weak assertions, class bloat |
| P3       | 5     | Documentation inaccuracy, missing edge cases, code reuse, drift risk, selective P2 fixes |

**Revised P1 count after downgrade of Finding 2:** 2 P1, 7 P2, 5 P3

**Recommendation:** Finding 5 (`_require_int_str` inf/nan producing 500 errors from user input) is a real P1 that has now been flagged in two consecutive QA reports without being addressed. It should be fixed in the next sprint. Finding 1 (empty commit) is a process issue that should be flagged to the team to prevent audit trail corruption.
