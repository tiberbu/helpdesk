# QA Report: Task #125 — Fix: Reverted savepoint isolation + broad except in close_tickets_after_n_days

**Review Type:** Adversarial QA Review
**Reviewer Model:** Opus
**Task Under Review:** #125 (quick-dev, sonnet)
**Date:** 2026-03-23
**Verdict:** CONDITIONAL PASS with 12 findings (2x P1, 4x P2, 6x P3)

---

## Acceptance Criteria Verification

### AC1: Savepoint isolation re-added per iteration
**Status:** PASS (with caveats — see Finding #1)

The code at `hd_ticket.py:1520-1537` correctly uses named savepoints:
```python
_sp = f"sp_autoclose_{ticket}"
frappe.db.savepoint(_sp)
try:
    ...
    frappe.db.release_savepoint(_sp)
    frappe.db.commit()
except (...):
    frappe.db.rollback(save_point=_sp)
```

Evidence: Lines 1520-1542 confirmed via direct file read. Pattern matches Frappe's `frappe.db.savepoint(name)` / `release_savepoint(name)` / `rollback(save_point=name)` API.

### AC2: Except clause narrowed from `except Exception` to specific types
**Status:** PASS (with caveats — see Finding #2)

Line 1531: `except (frappe.ValidationError, frappe.LinkValidationError, frappe.DoesNotExistError):`

### AC3: Tests added with coverage for happy path, error isolation, checklist guard
**Status:** FAIL — Tests deadlock in CI environment (see Finding #3)

4 tests exist in `test_close_tickets.py` but 2 of 4 fail with `QueryDeadlockError` when run via bench test runner.

---

## Findings

### Finding #1 — P1: Tests fail with QueryDeadlockError (deadlock in tearDown)

**Severity:** P1
**Description:** Running `bench run-tests --module helpdesk.helpdesk.doctype.hd_ticket.test_close_tickets` results in 2 of 4 tests failing with `frappe.exceptions.QueryDeadlockError: (1213, 'Deadlock found when trying to get lock; try restarting transaction')`. The deadlock occurs in `tearDown` during `frappe.db.set_single_value("HD Settings", ...)` which issues a DELETE on `tabSingles`. The root cause is the `frappe.db.commit()` calls inside `close_tickets_after_n_days` (line 1530, 1542) interacting with the test runner's transaction boundaries. The `setUp` method deletes all HD Tickets and Communications, and tearDown does the same plus restores HD Settings — these bulk DELETEs on committed data compete with the function's own commits for row-level locks.

**Steps to reproduce:**
```bash
cd /home/ubuntu/frappe-bench
bench --site helpdesk.localhost run-tests --app helpdesk --module helpdesk.helpdesk.doctype.hd_ticket.test_close_tickets
```

**Expected:** All 4 tests pass.
**Actual:** 2 tests fail with deadlock errors.

**Impact:** The primary deliverable of P1 #3 ("Zero test coverage") is not actually functional — the tests exist but can't be reliably run.

---

### Finding #2 — P1: `LinkValidationError` is a subclass of `ValidationError` — redundant in except tuple

**Severity:** P2 (downgraded from initial P1 assessment — functionally harmless but reveals incomplete analysis)
**Description:** `frappe.exceptions.LinkValidationError` inherits from `frappe.ValidationError` (confirmed in `frappe/exceptions.py:150`). Similarly, `DoesNotExistError` also inherits from `ValidationError` (line 44). The except clause `except (frappe.ValidationError, frappe.LinkValidationError, frappe.DoesNotExistError)` is therefore equivalent to just `except frappe.ValidationError:`. Including the subclasses is redundant and misleading — it suggests these are independent exception hierarchies when they aren't.

More critically, this means the "narrowing" from `except Exception` is actually just `except frappe.ValidationError`. The completion notes and comments claim it catches "expected failure modes" like "missing links, stale references" but in reality ANY ValidationError subclass is caught, which is a much broader net than the comment implies. This includes `frappe.MandatoryError`, `frappe.UniqueValidationError`, `frappe.InvalidNameError`, `frappe.DuplicateEntryError`, and dozens more — many of which could indicate bugs rather than expected auto-close failures.

---

### Finding #3 — P2: `setUp` does destructive `frappe.db.delete("HD Ticket")` — nukes ALL tickets

**Severity:** P2
**Description:** The test's `setUp` (line 135) runs `frappe.db.delete("HD Ticket")` which deletes **every single HD Ticket** in the database, not just test-created ones. If this test module is ever run against a database with real data (even staging), it will destroy all tickets. The same applies to Communications at line 136. The tearDown repeats this destructive pattern.

This violates the project's own test pattern documented in MEMORY.md which recommends explicit per-record cleanup: "Use explicit `frappe.delete_doc()` + `frappe.db.commit()` in tearDown instead."

---

### Finding #4 — P2: `commit()` after `release_savepoint()` means savepoint provides no real isolation benefit

**Severity:** P2
**Description:** The code does:
```python
frappe.db.release_savepoint(_sp)
frappe.db.commit()  # line 1530
```
On success, this commits the entire transaction — not just the savepoint. If a PREVIOUS iteration succeeded (committed), and the CURRENT iteration fails after the savepoint was created but before commit, the rollback to savepoint correctly undoes the current iteration. However, the `frappe.db.commit()` on line 1530 commits ALL pending changes, not just the savepoint's scope. This means the savepoint is only useful for the error path — but on the error path, if `doc.save()` internally calls `frappe.db.commit()` (which many Frappe hooks do), the savepoint rollback may not undo everything.

The story #125 completion notes acknowledge this concern but don't address it: "If a Frappe hook or child document internally calls commit() before the except block, partial state persists across iterations."

---

### Finding #5 — P2: No test for `DoesNotExistError` — one of the three explicitly-caught exceptions

**Severity:** P2
**Description:** The except clause catches three exception types: `ValidationError`, `LinkValidationError`, and `DoesNotExistError`. The tests cover ValidationError (checklist guard) but there is no test that triggers a `DoesNotExistError` (e.g., a ticket that was deleted between the SQL query and the `frappe.get_doc()` call). This is a real race condition in production (ticket deleted by another process between query and close attempt) and was explicitly called out in the story description as a "stale references" failure mode.

---

### Finding #6 — P2: Frappe provides `frappe.db.savepoint` context manager — not used

**Severity:** P3 (code style, not functional)
**Description:** Frappe provides `from frappe.database.database import savepoint` — a context manager that handles savepoint creation, release on success, and rollback on exception automatically. The code instead manually manages savepoint lifecycle (create, release, rollback) across 7 lines. The context manager would reduce this to:
```python
from frappe.database.database import savepoint
with savepoint(catch=(frappe.ValidationError,)):
    doc = frappe.get_doc("HD Ticket", ticket)
    doc.status = "Closed"
    doc.save(ignore_permissions=True)
```
This is more idiomatic, less error-prone, and eliminates the risk of forgetting to release/rollback.

---

### Finding #7 — P3: Savepoint name uses ticket ID directly — potential SQL injection vector

**Severity:** P3
**Description:** Line 1520: `_sp = f"sp_autoclose_{ticket}"`. The `ticket` value comes from a SQL query result (ticket name/ID), which for HD Ticket is an autoincrement integer, so this is safe in practice. However, the savepoint name is interpolated directly into SQL via `frappe.db.savepoint(_sp)` which internally does `self.sql(f"savepoint {save_point}")`. If the ticket naming scheme ever changes to include special characters, this could break or become an injection vector. A safer pattern would be to hash or sanitize the name.

---

### Finding #8 — P3: `_age_all_communications` uses raw SQL UPDATE without commit

**Severity:** P3
**Description:** The test helper `_age_all_communications` (line 91-95) does a raw SQL UPDATE but doesn't commit. It relies on the implicit transaction from previous operations. While this works in the test context, it means the test's data setup is fragile and order-dependent. If a commit happens between `_age_all_communications` and `close_tickets_after_n_days`, the backdated communications may or may not be visible depending on transaction isolation level.

---

### Finding #9 — P3: Error log assertion uses LIKE pattern matching — fragile

**Severity:** P3
**Description:** Line 277: `frappe.db.count("Error Log", {"method": ["like", "%Auto-close failed%"]})`. The `method` field of Error Log may not contain the `title` string passed to `frappe.log_error()`. In Frappe, `log_error(title=...)` stores the title in the `method` field only in certain versions. If the Frappe version changes how `log_error` maps its kwargs to Error Log fields, this assertion silently passes (count stays 0 before and after). A more robust check would assert on the actual Error Log content.

---

### Finding #10 — P3: No test for the "feature flag on, but no matching tickets" path

**Severity:** P3
**Description:** There's a test for feature flag OFF (`test_no_action_when_feature_disabled`) but no test for feature flag ON with zero eligible tickets (all communications are recent, or no tickets in the target status). This is the most common production scenario and should be verified to not raise errors.

---

### Finding #11 — P3: Test deletes Communications globally for HD Ticket doctype

**Severity:** P3
**Description:** Line 136/149: `frappe.db.delete("Communication", {"reference_doctype": "HD Ticket"})`. This deletes ALL Communications linked to ANY HD Ticket, not just test-created ones. In a shared test environment, this could interfere with other test modules running concurrently or leave the database in an inconsistent state for subsequent test suites.

---

### Finding #12 — P3: Story file claims "4 integration tests" but test isolation is questionable

**Severity:** P3
**Description:** The completion notes claim "4 integration tests — all pass" but the tests deadlock when actually run (Finding #1). The story was marked "done" without evidence the tests pass in the bench test runner. The test may have been validated only by running individual test methods or in a different execution context. The "all pass" claim in the completion notes is unverified and contradicted by actual execution.

---

## Console Errors

N/A — This is a backend-only change (scheduler function + tests). No frontend/UI changes. Playwright browser testing is not applicable for verifying backend scheduler behavior.

## Summary

| Severity | Count | Description |
|----------|-------|-------------|
| P1 | 1 | Tests deadlock — primary deliverable non-functional |
| P2 | 4 | Redundant exception hierarchy, destructive setUp, savepoint/commit interaction, missing DoesNotExistError test |
| P3 | 6 | Code style, fragile assertions, missing edge case tests, unverified claims |

**Recommendation:** The P1 deadlock issue must be fixed before this can be considered complete. The test suite is the primary deliverable of P1 #3 and it doesn't reliably run. The code changes to `hd_ticket.py` (savepoint + narrowed except) are correct in isolation but the exception tuple is misleadingly redundant and broader than documented.
