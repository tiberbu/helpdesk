# QA Report: Task #122 — Fix: P1 performance regression (uncached DB query every save) + misleading error

**Reviewer:** Adversarial Review (Opus)
**Date:** 2026-03-23
**Task Under Review:** Story #122 (commit d1a9de058, subsequently modified by ef92053e9+)
**Verdict:** 11 findings, 3 at P1 severity

---

## Acceptance Criteria Verification

### AC-1: Implementation matches task description
**PASS (with caveats)** — All five fixes (F-01 through F-08) are present in the codebase. However, the implementation has been modified by at least two subsequent commits that reverted and re-implemented the `close_tickets_after_n_days` savepoint strategy. The final code differs from what task #122 originally committed.

### AC-2: No regressions introduced
**CONDITIONAL PASS** — Unit tests pass (19/19 incident model, 1/1 category validation). But see findings below for regression risks in edge cases that are NOT covered by tests.

### AC-3: Code compiles/builds without errors
**PASS** — No syntax or import errors. Dev and bench copies are in sync.

---

## Adversarial Findings

### F-01 [P1] — Redundant exception types in close_tickets_after_n_days except clause

**File:** `helpdesk/helpdesk/doctype/hd_ticket/hd_ticket.py:1531`
**Code:** `except (frappe.ValidationError, frappe.LinkValidationError, frappe.DoesNotExistError):`

Both `LinkValidationError` and `DoesNotExistError` are **subclasses** of `ValidationError` (verified via MRO inspection). Listing all three is redundant — `except frappe.ValidationError:` alone catches all three. This is not just style: it signals the developer didn't verify the exception hierarchy, raising the question of whether the narrowing from bare `except Exception` was done with full understanding. If someone reads this and thinks the three types are independent, they might add a fourth "independent" exception type and miss that it's already a `ValidationError` subclass. **Impact:** Misleading code that suggests the author didn't understand the exception tree they were narrowing.

---

### F-02 [P1] — Narrowed except clause creates a new failure mode: OperationalError crashes the entire cron run

**File:** `helpdesk/helpdesk/doctype/hd_ticket/hd_ticket.py:1531`

The original code caught bare `except Exception`. The fix narrows to `(ValidationError, LinkValidationError, DoesNotExistError)`. The comment explicitly says: "OperationalError, SecurityException, and other unexpected failures still propagate and surface properly."

The problem: this is a **cron job** (`close_tickets_after_n_days`). If ticket #3 of 100 triggers a transient `OperationalError` (e.g., deadlock, lock wait timeout — extremely common in MySQL under load), the entire cron run aborts and tickets 4-100 never get processed. The previous bare `except Exception` was arguably better for a batch cron job because it ensured no single ticket could crash the entire batch. The fix solves one problem (silently swallowing unexpected errors) but introduces another (one transient DB error kills the whole batch).

A proper fix would catch `Exception`, but log at WARNING level for `ValidationError` subclasses and ERROR level for unexpected exceptions, while still continuing the loop.

---

### F-03 [P1] — get_cached_value returns stale data after HD Ticket Status update in a different process

**File:** `helpdesk/helpdesk/doctype/hd_ticket/hd_ticket.py:1069`

The docstring claims: "The in-process document cache is invalidated whenever an HD Ticket Status record is saved." This is only true **within the same process**. `frappe.get_cached_value` uses the in-process cache (`frappe.local.document_cache`) which is NOT shared across Gunicorn workers or RQ workers. If an admin updates the category of an HD Ticket Status record via worker A, worker B still serves the stale cached value until its process restarts or the cache entry TTL expires (which for document cache is effectively "never" within a request lifecycle, but indefinite across requests in a long-lived worker).

The original `frappe.get_value()` at least hit the DB every time, guaranteeing freshness. The caching fix trades correctness for performance without documenting the staleness window or providing any cache-busting mechanism (e.g., Redis pub/sub invalidation, or at minimum a note that `bench restart` is needed after changing HD Ticket Status categories).

**Caveat:** This is how `frappe.get_cached_value` works throughout the codebase (lines 224, 381, 382, 422 use it too), so this may be an accepted trade-off. But the docstring's claim that "freshly-updated values are always reflected within the same request" is technically correct yet misleadingly omits the cross-process staleness issue.

---

### F-04 [P2] — _resolve_ticket calls set_status_category() on an unsaved ticket — race condition with DB state

**File:** `helpdesk/helpdesk/doctype/hd_ticket/test_hd_ticket.py:984`

The F-03 fix replaced `ticket.status_category = "Resolved"` with `ticket.set_status_category()`. But `set_status_category()` calls `frappe.get_cached_value("HD Ticket Status", self.status, "category")`. The ticket object's `self.status` has been set to the resolved status name, but the ticket has NOT been saved yet. This works because `get_cached_value` reads from the HD Ticket Status table (not the ticket itself), but the pattern is fragile: if `set_status_category` ever adds logic that depends on the ticket being persisted (e.g., checking DB state), this will silently break. The test helper is building an in-memory state that may not match what `save()` would produce, which was exactly the "split reality" the fix was supposed to eliminate.

The proper fix would be to call `ticket.save(ignore_permissions=True)` and let the validate hook chain run, then reload. But the tests call `validate_category()` directly without saving, which means they still test a path that production code never takes.

---

### F-05 [P2] — test_save_raises_validation_error_when_status_record_deleted weakened to assertRaises instead of assertRaisesRegex

**File:** `helpdesk/helpdesk/doctype/hd_ticket/test_incident_model.py:573`

The original test used `assertRaisesRegex(frappe.ValidationError, r"no longer exists")` to verify the F-02 fix's specific error message. It was weakened to bare `assertRaises(frappe.ValidationError)` because Frappe's link validation fires first with a different message ("Could not find Status: ..."). This means the test no longer verifies that the custom F-02 disambiguation logic in `set_status_category()` actually works — it only verifies that *some* ValidationError is raised, which could be any of dozens of validation checks. The F-02 fix's custom error messages ("exists but has no category assigned" / "no longer exists") are now **completely untested**.

---

### F-06 [P2] — No test for the "empty category" branch of F-02

**File:** `helpdesk/helpdesk/doctype/hd_ticket/hd_ticket.py:1078-1087`

The F-02 fix added two error paths: (a) status record deleted, (b) status record exists but category is empty. There's a test for case (a) (`test_save_raises_validation_error_when_status_record_deleted`). There is **no test** for case (b) — an HD Ticket Status record with a blank category field. This is the more insidious case because it's a data integrity issue that could happen silently (admin creates a status but forgets to set category). The entire point of F-02 was to disambiguate these two cases, but only one is tested.

---

### F-07 [P2] — Savepoint naming uses ticket name directly — potential SQL injection or collision

**File:** `helpdesk/helpdesk/doctype/hd_ticket/hd_ticket.py:1520`
**Code:** `_sp = f"sp_autoclose_{ticket}"`

HD Ticket names are autoincrement integers so this is safe in practice. But the pattern of directly interpolating user-derived data into a savepoint name is a code smell. If the naming scheme ever changes (e.g., to string-based names like "HD-TICKET-001"), characters like hyphens could break the savepoint SQL. The savepoint name is not sanitized or quoted.

---

### F-08 [P2] — commit() after log_error() in except block may commit partial state from BEFORE the savepoint rollback

**File:** `helpdesk/helpdesk/doctype/hd_ticket/hd_ticket.py:1537-1542`

The flow is:
1. `frappe.db.savepoint(_sp)` — creates savepoint
2. Exception occurs during `doc.save()`
3. `frappe.db.rollback(save_point=_sp)` — rolls back to savepoint
4. `frappe.log_error(...)` — inserts Error Log record
5. `frappe.db.commit()` — commits

The `commit()` on line 1542 commits the Error Log insert, but it also commits **any uncommitted state from previous successful iterations** that hadn't been explicitly committed yet (though line 1530 does commit after each success). The ordering is correct IF and ONLY IF every previous success path commits. If a future refactor moves or removes the commit on line 1530, the error-path commit becomes a time bomb that silently commits work from other iterations.

---

### F-09 [P3] — Story completion notes claim "pre-existing freezegun failures in test_hd_ticket are unrelated" without evidence

**File:** Story #122 completion notes

The claim that freezegun failures are "unrelated" is an unsubstantiated assertion. Without showing which tests fail and why they're pre-existing, there's no way to verify this. A disciplined fix would list the specific failing test names and their failure mode to prove they're not regressions.

---

### F-10 [P3] — F-08 fix description in story notes contradicts actual implementation

**File:** Story #122 completion notes

The completion notes say: "close_tickets_after_n_days() now commits the frappe.log_error() result before calling frappe.db.rollback(), preventing the error log from being silently discarded."

But the actual code (after subsequent commits) does `rollback(save_point=_sp)` BEFORE `log_error()` and then `commit()`. The order is: rollback → log → commit, NOT log → commit → rollback as described. The notes describe the intermediate implementation from commit d1a9de058, not the final state after ef92053e9 reverted and re-implemented it. This means the documentation is stale and misleading.

---

### F-11 [P3] — No integration test for close_tickets_after_n_days with the narrowed except clause and an OperationalError

**File:** `helpdesk/helpdesk/doctype/hd_ticket/test_close_tickets.py`

The test file covers happy path, error isolation (ValidationError), and checklist guards. There is no test verifying behavior when a non-ValidationError exception occurs (e.g., OperationalError). Given that F-02 explicitly narrowed the except clause, there should be a test proving that unexpected exceptions DO propagate and that the batch job handles them appropriately (or at least documents the expected behavior).

---

## Test Results

| Test Suite | Result | Count |
|---|---|---|
| test_incident_model | PASS | 19/19 |
| test_category_required_on_resolution_enabled | PASS | 1/1 |
| Dev/bench file sync | PASS | Files identical |

---

## Summary

| Severity | Count | Findings |
|---|---|---|
| P1 | 3 | F-01 (redundant except), F-02 (cron crash on OperationalError), F-03 (stale cache cross-process) |
| P2 | 4 | F-04 (unsaved ticket set_status_category), F-05 (weakened test assertion), F-06 (no empty-category test), F-07 (savepoint naming), F-08 (commit ordering fragility) |
| P3 | 3 | F-09 (unsubstantiated claim), F-10 (stale docs), F-11 (missing OperationalError test) |

**Recommendation:** The P1 findings (especially F-02 — OperationalError killing entire cron batch) warrant a fix task. The except-clause narrowing was well-intentioned but created a worse failure mode for a batch job. The caching change (F-03) is an accepted Frappe pattern but the docstring should be honest about cross-process staleness.
