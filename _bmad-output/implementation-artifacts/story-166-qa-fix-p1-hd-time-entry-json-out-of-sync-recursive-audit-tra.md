# Story: QA: Fix: P1 hd_time_entry.json out of sync + recursive audit trail violation in task-146

Status: done
Task ID: mn3eia9nhyycia
Task Number: #166
Workflow: adversarial-review
Model: opus
Created: 2026-03-23T16:29:44.102Z

## Description

## QA Task for Story-163

### What was changed
- `helpdesk/test_utils.py`: Replaced `frappe.throw()` with `raise AssertionError(...)` in `ensure_hd_admin_user`, `ensure_agent_manager_user`, `ensure_system_manager_user`
- `story-130` completion notes: audit correction attribution changed from task-146 to task-148 (commit 8b17c65c3)
- `story-146` completion notes: added AUDIT CORRECTION block + updated test count 71→80
- DB: `bench migrate` run to sync System Manager permissions for HD Time Entry (create/write removed)

### What to test
1. Verify `helpdesk/test_utils.py` ensure_* helpers raise AssertionError (not frappe.throw)
2. Verify `hd_time_entry.json` and DB are in sync — System Manager has no create/write
3. Verify story-130 completion notes correctly reference task-148 (not task-146)
4. Verify story-146 completion notes have AUDIT CORRECTION and 80 tests (not 71)
5. Run `bench run-tests --app helpdesk` to check no regressions

### Expected behavior
- All ensure_* helpers raise Python AssertionError on role pollution
- DB tabDocPerm for HD Time Entry: System Manager create=0, write=0
- Story attribution correct (task-148/8b17c65c3)
- Test count shows 80

### Files changed
- helpdesk/test_utils.py
- _bmad-output/implementation-artifacts/story-130-*.md
- _bmad-output/implementation-artifacts/story-146-*.md

## Acceptance Criteria

- [x] All ensure_* helpers raise Python AssertionError on role pollution
- [x] DB tabDocPerm for HD Time Entry: System Manager create=0, write=0
- [x] Story attribution correct (task-148/8b17c65c3)
- [x] Test count shows 80

## Tasks / Subtasks

- [x] Verify `helpdesk/test_utils.py` ensure_* helpers raise AssertionError (not frappe.throw)
- [x] Verify `hd_time_entry.json` and DB are in sync — System Manager has no create/write
- [x] Verify story-130 completion notes correctly reference task-148 (not task-146)
- [x] Verify story-146 completion notes have AUDIT CORRECTION and 80 tests (not 71)
- [x] Run `bench run-tests --app helpdesk` to check no regressions

## Dev Notes



### References

- Task source: Claude Code Studio task #166

## Dev Agent Record

### Agent Model Used

opus

### Completion Notes List

- Adversarial review completed with 14 findings (3 P1, 5 P2, 6 P3).
- All 4 acceptance criteria verified as PASSING (code does what it claims).
- However, 3 P1 findings discovered — most critically, commit 0a45dc533 repeats the exact commit-scope pollution anti-pattern that this 6-story remediation chain was designed to eliminate (undeclared hd_ticket.py + test_incident_model.py changes).
- Story-146 change log still references `frappe.throw()` despite task-163 changing it to `AssertionError`.
- System Manager JSON permissions include generous auxiliary flags (share, email, export, print, report) inconsistent with stated read-only intent.
- `on_trash()` still has the double-`get_roles()` pattern that was fixed only in `delete_entry()`.
- Full report: `docs/qa-report-task-166-adversarial-review.md`

### Change Log

- `docs/qa-report-task-166-adversarial-review.md`: Created adversarial review report with 14 findings.
- `_bmad-output/implementation-artifacts/story-166-*.md`: Updated status, checkboxes, completion notes.

### File List

- `docs/qa-report-task-166-adversarial-review.md` (new)
- `_bmad-output/implementation-artifacts/story-166-qa-fix-p1-hd-time-entry-json-out-of-sync-recursive-audit-tra.md` (modified)
