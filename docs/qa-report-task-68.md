# Adversarial QA Report: Task #68 — Fix: P1 findings from QA task-62

**Reviewer:** Adversarial Review (Opus model)
**Date:** 2026-03-23
**Artifact:** Git diff a054d39ba..e26f43a03 (task #68 fix commit)
**Scope:** F-01 (status_category bypass), F-02 (migration patch), F-04 (permission test), F-05 (ITIL disabled test)
**Verdict:** 14 findings. 2 P1, 4 P2, 8 P3.

---

## Acceptance Criteria Assessment

### AC-1: F-01 fix — `set_status_category()` always re-derives from current status
**PASS** (with caveats, see F-01 and F-02 below)

The `or` short-circuit was removed. `set_status_category()` now always calls `frappe.get_value("HD Ticket Status", self.status, "category")`. This correctly re-derives the category on every save.

### AC-2: F-02 fix — Migration patch for Select->Link field type change
**PASS** (with caveats, see F-03, F-04, F-05 below)

New patch `reload_incident_model_for_link_field.py` was created and added to `patches.txt`. It reloads the doctype and clears invalid `default_priority` values.

### AC-3: F-04 fix — Test for is_agent() permission guard
**PASS** (with caveats, see F-06, F-07 below)

New test `test_apply_model_raises_permission_error_for_non_agent` verifies non-agent gets `PermissionError`.

### AC-4: F-05 fix — Test for ITIL-mode-disabled rejection
**PASS** (with caveats, see F-08 below)

New test `test_apply_model_raises_validation_error_when_itil_disabled` verifies `ValidationError` when ITIL mode is off.

---

## Findings

### F-01 [P1] — `set_status_category()` now sets `None` for invalid/empty statuses, silently corrupting data

**Description:** The old `or` short-circuit was a bug, but it also served as a safety net: if `self.status` was `None`, empty, or pointed to a non-existent `HD Ticket Status` record, the existing `status_category` was preserved. Now, `set_status_category()` unconditionally overwrites `status_category` with whatever `frappe.get_value()` returns. When `self.status` is `None`, empty, or references a deleted status record, `frappe.get_value()` returns `None`, and `status_category` is set to `None`.

This is a regression in edge cases: a ticket that previously had a valid `status_category` will have it wiped to `None` if `self.status` is temporarily invalid during a save operation. No defensive check was added.

**Evidence:** Verified in bench console:
```python
frappe.get_value("HD Ticket Status", None, "category")  # Returns None
frappe.get_value("HD Ticket Status", "", "category")    # Returns None
frappe.get_value("HD Ticket Status", "NONEXISTENT", "category")  # Returns None
```

**Impact:** Any ticket with a corrupted/missing `self.status` will have its `status_category` silently wiped. Downstream logic relying on `status_category` (SLA calculations, resolution guard, workflows) will malfunction.

---

### F-02 [P1] — No dedicated test for the exact F-01 bypass scenario (status_category stale after status change)

**Description:** The entire point of this fix was to prevent `status_category` from remaining stale when status changes (e.g., Replied->Resolved keeping "Paused" instead of updating to "Resolved"). Yet there is **zero test** for this specific scenario. The existing resolution tests (`test_resolution_blocked_when_mandatory_items_incomplete`) create a fresh ticket and set status to Resolved in one step — they never exercise the status_category re-derivation path because status_category was never previously set to a different value.

A future developer could reintroduce the `or` short-circuit (e.g., as a "performance optimization") and all 13 tests would still pass. The fix is unverified by any automated test.

**Evidence:** `grep -r "status_category" test_incident_model.py` returns zero matches. No test changes status from one category to another and verifies `status_category` updates.

---

### F-03 [P2] — Migration patch has no `frappe.db.commit()` — UPDATE may be lost

**Description:** The migration patch `reload_incident_model_for_link_field.py` executes a raw SQL `UPDATE` to clear invalid `default_priority` values, but never calls `frappe.db.commit()`. While Frappe's patch runner typically commits after each patch, this is an implementation detail that varies by Frappe version. If the patch runner does NOT auto-commit (or if an exception occurs in a later patch that triggers rollback), the UPDATE is lost. The `frappe.reload_doctype()` call is DDL (ALTER TABLE) which auto-commits in MySQL, but the subsequent UPDATE is DML and subject to transaction boundaries.

**Evidence:** `grep "commit" reload_incident_model_for_link_field.py` returns zero matches.

---

### F-04 [P2] — Migration patch doesn't handle the case where `tabHD Ticket Priority` table doesn't exist

**Description:** The migration patch runs a subquery against `tabHD Ticket Priority`. If this table doesn't exist (e.g., the helpdesk was installed without the priority matrix feature from Story 1.2), the SQL query will fail with a "Table doesn't exist" error, aborting migration entirely. There's no `try/except` or existence check.

**Evidence:** The patch assumes `tabHD Ticket Priority` exists. But this table is created by Story 1.2 (impact/urgency fields), which is a separate feature. A deployment that skipped Story 1.2 but has Story 1.9 (incident models) would hit this.

---

### F-05 [P2] — Migration patch doesn't reload child doctype `HD Incident Checklist Item`

**Description:** The patch only calls `frappe.reload_doctype("HD Incident Model", force=True)` but doesn't reload `HD Incident Checklist Item` (the child table). If any schema changes were made to the checklist child DocType in the same commit window, they won't be picked up. This is a defensive coding gap — the original `add_incident_model_doctypes.py` patch reloads both parent and child.

**Evidence:** The original patch:
```python
frappe.reload_doctype("HD Incident Model")
frappe.reload_doctype("HD Incident Checklist Item")
```
The new patch only reloads `HD Incident Model`.

---

### F-06 [P2] — Permission test creates a user but never cleans it up

**Description:** `test_apply_model_raises_permission_error_for_non_agent` creates user `im_customer_noagent@example.com` with `doc.insert(ignore_permissions=True)`, but the tearDown only calls `frappe.db.rollback()`. Since `frappe.db.rollback()` is called AFTER `frappe.db.set_single_value("HD Settings", "itil_mode_enabled", 0)` (which may auto-commit), the user creation might persist depending on transaction boundaries. Even if rollback works, the `if not frappe.db.exists("User", customer_email)` guard means the test silently reuses stale data from a previous failed run. This is the same test data leak pattern that was specifically called out in the original QA report (F-08).

**Evidence:** `test_incident_model.py` line 225: `if not frappe.db.exists("User", customer_email)` — this is a "create if missing" pattern that masks test pollution.

---

### F-07 [P2] — Permission test only covers `apply_incident_model`, not `complete_checklist_item`

**Description:** The F-04 finding specified adding a test for the `is_agent()` permission guard. The fix added a test for `apply_incident_model` but NOT for `complete_checklist_item`, which also has an `is_agent()` guard (line 92 of `incident_model.py`). The same non-agent bypass could exist on the checklist toggling path and would go undetected.

**Evidence:** `grep "complete_checklist.*permission\|complete_checklist.*non.agent" test_incident_model.py` returns zero matches.

---

### F-08 [P3] — ITIL-disabled test only covers `apply_incident_model`, not `complete_checklist_item`

**Description:** Same asymmetry as F-07. The ITIL-mode-disabled test only validates `apply_incident_model`. The `complete_checklist_item` function has its own ITIL gate (line 96-97) but no test verifies it fires when ITIL is off.

**Evidence:** No test calls `complete_checklist_item` with ITIL mode disabled.

---

### F-09 [P3] — ITIL-disabled test re-enables ITIL in its own body instead of deferring to tearDown

**Description:** `test_apply_model_raises_validation_error_when_itil_disabled` manually re-enables ITIL mode at the end of the test body (lines 259-261) rather than letting tearDown handle cleanup. This means if the `assertRaises` fails (test failure), the re-enable code still runs, masking the failure's side effects. More importantly, it's redundant with tearDown which already sets `itil_mode_enabled = 0` — but wait, tearDown disables it, so the test is re-enabling before tearDown disables. This is confusing control flow. If a developer reads tearDown and assumes ITIL is always disabled there, they'll be surprised that this test re-enables it first.

**Evidence:** Lines 259-261 re-enable; tearDown line 57 disables. The re-enable in the test body is redundant since tearDown will set it to 0 regardless.

---

### F-10 [P3] — Story file completion notes don't mention the migration patch was NOT run

**Description:** The story-68 completion notes say "F-02 fixed: New patch added to patches.txt" but don't mention whether `bench migrate` was actually executed. In fact, I verified the patch had NOT been run until I manually executed `bench migrate` during this review. The dev workflow notes in MEMORY.md explicitly state "After backend changes to bench copy: `bench --site helpdesk.localhost migrate` if schema changed" — this step was skipped.

**Evidence:** `tabPatch Log` had no record for `reload_incident_model_for_link_field` until I ran `bench migrate` during this review. The patch creation timestamp is `2026-03-23 20:13:19` (my review time), not the commit time.

---

### F-11 [P3] — No idempotency guard on migration patch

**Description:** The migration patch has no idempotency check. If it runs twice (e.g., patch log was cleared, or manual execution via `bench execute`), the `frappe.reload_doctype()` call is harmless, but the SQL UPDATE would clear `default_priority` values that were validly set between the first and second run. While Frappe's patch runner normally prevents double execution, defensive patches should be idempotent.

**Evidence:** No `if frappe.db.has_column(...)` or other guard. The UPDATE unconditionally runs against all rows.

---

### F-12 [P3] — Original QA findings F-03, F-06, F-07, F-08, F-09, F-10, F-11, F-12, F-13 remain unaddressed

**Description:** The task description said "Also fix (P2): F-04, F-05" — implying F-03, F-06 through F-13 were intentionally deferred. However, the story completion notes don't document which findings were deferred or why. There's no tracking of the remaining P2/P3 technical debt. A reader looking at the fix would assume all 13 findings from qa-report-task-62 were addressed.

**Evidence:** Story-68 completion notes mention only F-01, F-02, F-04, F-05. Findings F-03 (async store race), F-06 (depends_on DB call), F-07 (frontend ITIL gating), F-08 (test data leak), F-09 (fixture priority names), F-10 (getStatus fragility), F-11 (undefined handling), F-12 (incomplete comment), F-13 (PostIncidentReview conflict) are neither addressed nor explicitly deferred.

---

### F-13 [P3] — Permission test doesn't verify the error message, only the exception type

**Description:** `test_apply_model_raises_permission_error_for_non_agent` uses `self.assertRaises(frappe.PermissionError)` which only checks the exception type. If the PermissionError is raised by `frappe.has_permission(..., throw=True)` (line 28) instead of the intended `is_agent()` guard (line 26-27), the test still passes. This means the `is_agent()` check could be removed entirely and the test would pass because `frappe.has_permission` would still raise PermissionError for the non-agent user.

**Evidence:** The test doesn't use `assertRaisesRegex` or check the exception message ("Not permitted") to distinguish between the two permission checks.

---

### F-14 [P3] — `set_status_category` makes a DB call on every ticket save regardless of whether status changed

**Description:** The old `or` short-circuit, despite its bug, had the side effect of avoiding unnecessary DB calls when `status_category` was already set. The fix removes the short-circuit entirely, meaning every single ticket save now hits the database to look up the status category — even when the status hasn't changed. A more surgical fix would be: `if self.has_value_changed("status") or not self.status_category: self.status_category = frappe.get_value(...)`. This preserves correctness while avoiding the extra DB query on non-status-change saves.

**Evidence:** The original QA report F-01 explicitly suggested checking `self.has_value_changed("status")` as the correct fix. The implementer chose the simpler but less performant approach.

---

## Summary

| ID | Severity | Title |
|------|----------|-------|
| F-01 | P1 | `set_status_category()` now sets `None` for invalid/empty statuses |
| F-02 | P1 | No test for the exact F-01 bypass scenario (stale status_category) |
| F-03 | P2 | Migration patch missing `frappe.db.commit()` |
| F-04 | P2 | Migration patch crashes if `tabHD Ticket Priority` doesn't exist |
| F-05 | P2 | Migration patch doesn't reload child doctype |
| F-06 | P2 | Permission test user never cleaned up (test data leak) |
| F-07 | P2 | No permission test for `complete_checklist_item` |
| F-08 | P3 | No ITIL-disabled test for `complete_checklist_item` |
| F-09 | P3 | ITIL test re-enables flag redundantly before tearDown |
| F-10 | P3 | Migration patch was never actually run after commit |
| F-11 | P3 | No idempotency guard on migration patch |
| F-12 | P3 | 9 original QA findings remain unaddressed and untracked |
| F-13 | P3 | Permission test doesn't distinguish between two PermissionError sources |
| F-14 | P3 | Unnecessary DB call on every save even when status unchanged |

---

## Recommendation

**F-01** is a real risk: the fix trades one bug (stale value) for another (wiped value). The correct implementation should check `self.has_value_changed("status") or not self.status_category` before re-deriving, or at minimum fall back to the existing value when `frappe.get_value` returns `None`.

**F-02** is a process gap: the core P1 fix has zero automated regression protection. A single test that saves a ticket as "Replied" (category "Paused"), then changes to "Resolved", and verifies `status_category` updates to "Resolved" would close this gap.

The migration patch (F-03 through F-05) needs hardening for production use. The test additions (F-06 through F-09) are functionally correct but incomplete — they only cover half the API surface.
