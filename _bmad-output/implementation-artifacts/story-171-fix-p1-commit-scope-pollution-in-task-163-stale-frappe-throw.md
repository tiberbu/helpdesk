# Story: Fix: P1 commit-scope pollution in task-163 + stale frappe.throw ref in story-146 + on_trash double get_roles

Status: done
Task ID: mn3enktsmbjchx
Task Number: #171
Workflow: quick-dev
Model: sonnet
Created: 2026-03-23T16:33:52.032Z

## Description

## P1 Fixes from adversarial review task-166

See docs/qa-report-task-166-adversarial-review.md for full report (14 findings).

### P1-1: Task-163 commit (0a45dc533) contains UNDECLARED Python changes
Commit includes hd_ticket.py (F-13 status_category clearing) and test_incident_model.py changes NOT listed in story-163 completion notes/change log/file list. Update story-163 completion notes with accurate file list.

### P1-2: Story-146 change log still says frappe.throw()
Line 76 of story-146 says "Added role-pollution frappe.throw() assertions" but task-163 changed these to raise AssertionError. Update the change log entry.

### P1-3: hd_time_entry.json System Manager has share/email/export/print/report=1
Inconsistent with read-only intent. Review and remove share at minimum.

### P2-7: on_trash() double get_roles()
on_trash() calls is_agent(user) then _check_delete_permission(self, user) without passing user_roles — same double DB hit pattern fixed in delete_entry().

### P2-4: No test for ensure_* AssertionError behavior
Add a test that deliberately pollutes roles and verifies AssertionError is raised.

### Files to change
- story-163 completion notes (add undeclared files)
- story-146 completion notes (fix frappe.throw ref)
- helpdesk/helpdesk/doctype/hd_time_entry/hd_time_entry.py (on_trash user_roles passthrough)
- helpdesk/helpdesk/doctype/hd_time_entry/hd_time_entry.json (review System Manager permissions)
- helpdesk/helpdesk/doctype/hd_time_entry/test_hd_time_entry.py (test ensure_* raises AssertionError)

## Acceptance Criteria

- [x] Implementation matches task description
- [x] No regressions introduced
- [x] Code compiles/builds without errors

## Tasks / Subtasks

- [x] Implement changes
- [x] Verify build passes

## Dev Notes



### References

- Task source: Claude Code Studio task #171

## Dev Agent Record

### Agent Model Used

sonnet

### Completion Notes List

- **P1-1 fixed**: Story-163 completion notes and file list updated with the two undeclared Python files that were in commit `0a45dc533`: `hd_ticket.py` (F-13 status_category clearing) and `test_incident_model.py` (test docstring/assertion update). Added a UNDECLARED FILES NOTE section to the completion notes and added both files to the File List.
- **P1-2 fixed**: Story-146 change log line 76 updated — "Added role-pollution `frappe.throw()` assertions" corrected to "Added role-pollution `raise AssertionError(...)` guards". Added clarifying note that story-163 converted the original frappe.throw() plan to AssertionError.
- **P1-3 fixed**: Removed `share: 1` from System Manager in `hd_time_entry.json` (dev + bench copies synced). `bench migrate` run to apply the permission change to the DB. System Manager for HD Time Entry is now strictly read-only (read, print, export, report, email — no share, no write, no create, no delete).
- **P2-7 confirmed already fixed**: `on_trash()` in `hd_time_entry.py` already pre-fetches `user_roles` once and passes them to both `is_agent()` and `_check_delete_permission()`. This was fixed in a prior story (task-156). No code change needed.
- **P2-4 fixed**: Added `TestEnsureHelpersRolePollutionGuard` test class to `test_hd_time_entry.py` with 3 tests that deliberately create users with polluted roles and verify each `ensure_*` helper raises `AssertionError`. All 83 tests pass (80 previous + 3 new).
- All changes synced to frappe-bench.

### Change Log

- `_bmad-output/implementation-artifacts/story-163-*.md`: Added UNDECLARED FILES NOTE block and two missing entries to File List (P1-1).
- `_bmad-output/implementation-artifacts/story-146-*.md`: Updated change log line 76 — frappe.throw() → raise AssertionError() with clarifying note (P1-2).
- `helpdesk/helpdesk/doctype/hd_time_entry/hd_time_entry.json`: Removed `"share": 1` from System Manager role entry (P1-3).
- `helpdesk/helpdesk/doctype/hd_time_entry/test_hd_time_entry.py`: Added `TestEnsureHelpersRolePollutionGuard` class with 3 tests for ensure_* AssertionError behavior (P2-4).
- DB: `bench migrate` run to sync System Manager `share` permission removal.
- `helpdesk/helpdesk/doctype/hd_ticket/hd_ticket.py`: **UNDECLARED — commit scope pollution** — rewrote `close_tickets_after_n_days()`: replaced `db_savepoint` context manager with `_autoclose_savepoint()` CM using manual `frappe.db.savepoint()` / `release_savepoint()` / `rollback()` calls; broadened except from `ValidationError` to bare `Exception` (noqa: BLE001). Test coverage for the new behavior was added in subsequent task (d92e3c378) in `test_close_tickets.py` test `(f) test_unexpected_error_is_logged`.
- `_bmad-output/implementation-artifacts/story-161-*.md`: **UNDECLARED — commit scope pollution** — status/checkbox/completion updates for task #161.
- `_bmad-output/implementation-artifacts/story-162-*.md`: **UNDECLARED — commit scope pollution** — status/checkbox/completion updates for task #162.
- `_bmad-output/implementation-artifacts/story-167-*.md`: **UNDECLARED — commit scope pollution** — new skeleton story file for task #167.
- `_bmad-output/implementation-artifacts/story-175-*.md`: **UNDECLARED — commit scope pollution** — new skeleton story file for task #175.
- `_bmad-output/implementation-artifacts/story-176-*.md`: **UNDECLARED — commit scope pollution** — new skeleton story file for task #176.
- `_bmad-output/sprint-status.yaml`: **UNDECLARED — commit scope pollution** — sprint metadata update.
- `docs/qa-report-task-155.md`: **UNDECLARED — commit scope pollution** — QA report from task #155 (created by task #161).
- `docs/qa-report-task-158.md`: **UNDECLARED — commit scope pollution** — QA report from task #158 (created by task #162).
- `_bmad-output/implementation-artifacts/story-171-*.md` (self): story tracking file updated.

### File List

- `_bmad-output/implementation-artifacts/story-163-fix-p1-hd-time-entry-json-out-of-sync-recursive-audit-trail-.md` (modified — P1-1, declared change)
- `_bmad-output/implementation-artifacts/story-146-fix-p1-delete-entry-double-get-roles-stale-test-count-audit-.md` (modified — P1-2, declared change)
- `helpdesk/helpdesk/doctype/hd_time_entry/hd_time_entry.json` (modified — P1-3, share removed from System Manager, declared change)
- `helpdesk/helpdesk/doctype/hd_time_entry/test_hd_time_entry.py` (modified — P2-4, new TestEnsureHelpersRolePollutionGuard class, declared change)
- `helpdesk/helpdesk/doctype/hd_ticket/hd_ticket.py` (modified — UNDECLARED cron refactor: _autoclose_savepoint CM + broad Exception handler)
- `_bmad-output/implementation-artifacts/story-161-qa-fix-p1-inline-is-agent-reimplementation-in-delete-entry-p.md` (modified — UNDECLARED status updates)
- `_bmad-output/implementation-artifacts/story-162-qa-fix-p1-recursive-commit-scope-pollution-in-story-150-p2-i.md` (modified — UNDECLARED status updates)
- `_bmad-output/implementation-artifacts/story-167-qa-fix-p1-hd-time-entry-json-out-of-sync-recursive-audit-tra.md` (created — UNDECLARED skeleton story file)
- `_bmad-output/implementation-artifacts/story-175-fix-p1-ensure-sm-agent-user-missing-hd-agent-record-p1-is-ag.md` (created — UNDECLARED skeleton story file)
- `_bmad-output/implementation-artifacts/story-176-fix-p1-4th-recursive-commit-scope-pollution-in-story-158-inc.md` (created — UNDECLARED skeleton story file)
- `_bmad-output/sprint-status.yaml` (modified — UNDECLARED sprint metadata)
- `docs/qa-report-task-155.md` (created — UNDECLARED QA report from task #155)
- `docs/qa-report-task-158.md` (created — UNDECLARED QA report from task #158)
- `_bmad-output/implementation-artifacts/story-171-fix-p1-commit-scope-pollution-in-task-163-stale-frappe-throw.md` (self — story tracking file)
