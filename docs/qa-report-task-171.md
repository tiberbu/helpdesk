# QA / Adversarial Review Report: Task #171

**Reviewed by:** Opus (adversarial reviewer)
**Date:** 2026-03-23
**Commit under review:** `d893b5e97` ("Fix: P1 commit-scope pollution in task-163 + stale frappe.throw ref in story-146")
**Story file:** `_bmad-output/implementation-artifacts/story-171-fix-p1-commit-scope-pollution-in-task-163-stale-frappe-throw.md`

---

## Acceptance Criteria Verification

| AC | Status | Evidence |
|----|--------|----------|
| AC-1: Implementation matches task description | **PASS** | P1-1 (story-163 notes updated), P1-2 (story-146 frappe.throw ref fixed), P1-3 (share:1 removed from SM), P2-4 (3 pollution guard tests added) all verified in diff and live DB |
| AC-2: No regressions introduced | **PASS** | All 83 tests pass in 7.143s; API returns 200 for HD Time Entry list; bench/dev copies in sync |
| AC-3: Code compiles/builds without errors | **PASS** | Test suite runs clean, no import errors |

---

## Adversarial Findings (14 total)

### Finding 1 (P1): **FIFTH recursive commit-scope pollution** -- the exact defect this chain exists to fix

Commit `d893b5e97` modifies **14 files** but the story's File List declares only **4**. The 10 undeclared files are:

1. `story-161-*.md` -- status/checkbox/completion updates (NOT in task #171 scope)
2. `story-162-*.md` -- status/checkbox/completion updates (NOT in task #171 scope)
3. `story-167-*.md` -- brand-new story file creation (NOT in task #171 scope)
4. `story-175-*.md` -- brand-new story file creation (NOT in task #171 scope)
5. `story-176-*.md` -- brand-new story file creation (NOT in task #171 scope)
6. `_bmad-output/sprint-status.yaml` -- sprint metadata (NOT in task #171 scope)
7. `docs/qa-report-task-155.md` -- QA report from a different task (NOT in task #171 scope)
8. `docs/qa-report-task-158.md` -- QA report from a different task (NOT in task #171 scope)
9. `helpdesk/helpdesk/doctype/hd_ticket/hd_ticket.py` -- major `close_tickets_after_n_days()` refactor (NOT in task #171 scope)
10. `helpdesk/helpdesk/doctype/hd_time_entry/hd_time_entry.json` (IS in scope)

This is now the **fifth recursive instance** of the commit-scope pollution defect. The entire chain (stories 150 -> 158 -> 162 -> 166 -> 171) was created to fix this exact problem, and each fix commit re-introduces it. The developer is either unable or unwilling to use `git add <specific-files>` instead of `git add .` or `git add -A`.

**Severity: P1** -- process defect that undermines audit trail integrity.

---

### Finding 2 (P1): Undeclared `hd_ticket.py` change is a **functional code refactor**, not a documentation fix

The commit silently rewrites `close_tickets_after_n_days()` in `hd_ticket.py` -- replacing `frappe.database.database.savepoint` context-manager usage with manual `frappe.db.savepoint()` / `release_savepoint()` / `rollback(save_point=...)` calls, and broadening the except clause from `frappe.ValidationError` to bare `Exception`. This is a non-trivial behavioral change to a **cron job** that auto-closes tickets. It:

- Was not mentioned anywhere in the task #171 description or acceptance criteria
- Was not listed in the story's Change Log or File List
- Has no corresponding test
- Changes error-handling semantics (ValidationError-only -> catch-all Exception)
- Removes the import of `db_savepoint` from `frappe.database.database`

A stealthy functional change smuggled into a "fix documentation + remove share:1" commit is the most egregious form of scope pollution.

**Severity: P1** -- undeclared functional change with no test coverage.

---

### Finding 3 (P2): `close_tickets_after_n_days()` catch-all `except Exception` may silently swallow critical errors

The refactored code catches **all exceptions** (including `KeyboardInterrupt` via `BaseException` being a parent of... wait, `Exception` doesn't catch `KeyboardInterrupt`). However, it does catch:
- `OperationalError` (database connection lost, deadlocks)
- `MemoryError`
- `SystemError`
- `RecursionError`

For transient DB errors this might be acceptable, but for `MemoryError` or `SystemError` continuing the loop is dangerous -- the process may be in an inconsistent state. The `# noqa: BLE001` comment shows the developer was aware of linting warnings but suppressed them without justification.

**Severity: P2** -- overly broad exception handling in a cron job.

---

### Finding 4 (P2): `TestEnsureHelpersRolePollutionGuard` tests are placed in the wrong test module

The 3 new pollution-guard tests validate behavior of functions in `helpdesk/test_utils.py`:
- `ensure_hd_admin_user()`
- `ensure_agent_manager_user()`
- `ensure_system_manager_user()`

But they are placed in `helpdesk/helpdesk/doctype/hd_time_entry/test_hd_time_entry.py`, which is the test module for the `HD Time Entry` DocType. A prior comment in the same file even says: *"TestIsAgentExplicitUser has been moved to helpdesk/tests/test_utils.py (story-130 P1 fix #8 -- co-locate tests with the module they test)"*. The developer read this comment and then immediately violated the principle it establishes.

**Severity: P2** -- test organization violates the project's own stated convention.

---

### Finding 5 (P2): Pollution guard tests use `if not frappe.db.exists` -- not idempotent across test reruns

Each of the 3 pollution guard tests creates a user only if it doesn't exist:
```python
if not frappe.db.exists("User", email):
    user = frappe.get_doc({...})
    user.insert(ignore_permissions=True)
    user.add_roles("HD Admin", "Agent")
```

If the test fails partway through (e.g., user created but roles not fully applied), subsequent runs will skip user creation but the roles may be incomplete. More critically, `tearDown` calls `frappe.db.rollback()`, but `user.insert()` may have already been committed by Frappe's implicit commit behavior in some configurations. This creates a test that passes on first run but may behave differently on subsequent runs.

**Severity: P2** -- fragile test setup that is not truly idempotent.

---

### Finding 6 (P2): Story-171 completion notes claim "P2-7 confirmed already fixed" but the original QA finding was about `on_trash()` calling `is_agent(user)` then `_check_delete_permission(self, user)` "without passing user_roles"

The completion notes say: *"on_trash() in hd_time_entry.py already pre-fetches user_roles once and passes them to both is_agent() and _check_delete_permission(). This was fixed in a prior story (task-156)."*

However, the task description explicitly says this was a **P2-7 finding**: "on_trash() calls is_agent(user) then _check_delete_permission(self, user) without passing user_roles -- same double DB hit pattern fixed in delete_entry()." If it was already fixed by task-156, then the QA report that created task-171 (task-166) had a stale finding. But the completion notes don't explain WHY the QA report was wrong or cite the specific commit from task-156. "Already fixed" with no evidence is an unverifiable claim.

**Severity: P2** -- unsubstantiated "already fixed" claim without commit reference.

---

### Finding 7 (P2): System Manager retains `email:1`, `export:1`, `print:1`, `report:1` -- inconsistent with "strictly read-only" claim

The completion notes state: *"System Manager for HD Time Entry is now strictly read-only (read, print, export, report, email -- no share, no write, no create, no delete)."*

But `email:1` allows sending documents via email, `export:1` allows data export, `print:1` allows print views, and `report:1` allows report builder access. These are all **action** permissions, not just "read." The claim of "strictly read-only" is misleading. The original QA finding (P1-3) said "Inconsistent with read-only intent. Review and remove share at minimum." The developer removed only `share` and declared victory, but the other action permissions were not reviewed as the finding requested.

**Severity: P2** -- incomplete fix of the original finding; "at minimum" language was not treated as a starting point.

---

### Finding 8 (P3): Story files for tasks #161, #162 updated to "done" status inside a commit for task #171

The commit updates `story-161-*.md` and `story-162-*.md` to `Status: done` with completion notes filled in. These are unrelated QA tasks whose status changes should have been committed in their own respective task commits. Bundling status updates from 2+ other tasks into this commit further confuses the audit trail.

**Severity: P3** -- housekeeping changes in wrong commit.

---

### Finding 9 (P3): New story files created for tasks #167, #175, #176 are skeleton placeholders with "in-progress" status

The commit creates 3 new story files (167, 175, 176) all with `Status: in-progress` and empty completion notes. These are **future tasks** that haven't been started yet. Creating their story files in a commit for task #171 means git blame shows these files as authored by the task-171 commit, which is misleading.

**Severity: P3** -- premature file creation pollutes attribution.

---

### Finding 10 (P3): `sprint-status.yaml` changes not documented

The commit modifies `_bmad-output/sprint-status.yaml` but this is not mentioned in the Change Log or File List. While sprint status is metadata, the pattern of undeclared changes continues.

**Severity: P3** -- undeclared metadata change.

---

### Finding 11 (P3): Pollution guard test assertions check only one pollutant per helper

Each test only verifies one specific pollution combination:
- `ensure_hd_admin_user` tested with `Agent` pollution only (not `Agent Manager` or `System Manager`)
- `ensure_agent_manager_user` tested with `HD Admin` pollution only (not `Agent` or `System Manager`)
- `ensure_system_manager_user` tested with `Agent Manager` pollution only (not `Agent` or `HD Admin`)

A thorough test would parametrize all 3 forbidden roles for each helper (9 combinations), or at minimum test with all 3 forbidden roles simultaneously.

**Severity: P3** -- thin coverage on pollution guard tests.

---

### Finding 12 (P3): Story-171 counts "83 tests" (80 + 3 new) but doesn't reconcile with prior story counts

Previous stories cited 80 tests. Task-171 adds 3 tests for a total of 83. But the prior story chain has had multiple test-count discrepancies (story-130 said 71, story-146 corrected to 80). The 80-to-83 jump should cite which specific test count it's incrementing from and which commit established that baseline.

**Severity: P3** -- recurring test count reconciliation gap.

---

### Finding 13 (P3): `docs/qa-report-task-155.md` and `docs/qa-report-task-158.md` are QA artifacts from different tasks

These two QA report files were created by tasks #161 and #162 respectively, but committed in task #171's commit. They are read-only QA artifacts and shouldn't be modified, but their initial creation was in the wrong commit.

**Severity: P3** -- QA artifacts attributed to wrong commit.

---

### Finding 14 (P3): The `# nosemgrep` annotation on `frappe.db.commit()` in the refactored cron code has no justification comment

The original code had `# nosemgrep` on the commit. The new code copies it (`# nosemgrep -- persist close or error log`) which is slightly better, but Semgrep annotations should explain which specific rule is being suppressed and why, not just describe what the line does.

**Severity: P3** -- inadequate Semgrep suppression documentation.

---

## Summary

| Severity | Count | Key Themes |
|----------|-------|------------|
| P0       | 0     | -- |
| P1       | 2     | 5th recursive commit-scope pollution; undeclared hd_ticket.py functional refactor |
| P2       | 5     | Overly broad exception catch; wrong test module; fragile test setup; unsubstantiated "already fixed" claim; incomplete permission review |
| P3       | 7     | Housekeeping in wrong commits; thin test coverage; metadata attribution |

**Overall Assessment:** The 4 declared changes (P1-1, P1-2, P1-3, P2-4) are technically correct -- the `share:1` removal is reflected in the live DB, the story file corrections are accurate, and the 3 new tests pass. However, the commit is a textbook example of the exact defect it was supposed to fix: 14 files modified with only 4 declared. The undeclared `hd_ticket.py` cron refactor is the most concerning item because it changes production behavior with zero test coverage and zero documentation.

---

## Console Errors

No console errors observed via API testing. Playwright MCP was not available for browser-level console verification.

## Browser Testing

Playwright MCP tools were unavailable. API-level verification performed:
- Logged in successfully as Administrator
- HD Time Entry API returns data correctly
- Live DB confirms System Manager share=0 (P1-3 fix verified)

## Test Results

```
Ran 83 tests in 7.143s -- OK
All 83 HD Time Entry tests pass.
```
