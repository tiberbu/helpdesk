# Story: Fix: P1 undeclared scope creep in task-163 + P2 stale test count + story-130 frappe.throw stale docs

Status: done
Task ID: mn3exm1mzl57jd
Task Number: #179
Workflow: quick-dev
Model: sonnet
Created: 2026-03-23T16:41:38.916Z

## Description

## P1/P2 Fixes from adversarial review task-167

See docs/qa-report-task-163.md for full report (14 findings).

### P1-1: Undeclared F-13 code change has no dedicated test
Commit 0a45dc533 added F-13 fix (status_category = None when status is falsy) to hd_ticket.py but NO test covers this specific path. Add a test that sets status to empty string, saves, and verifies status_category is None.

### P2-2: Story-146 test count already stale (claims 80, actual 83)
Replace hardcoded count with "All tests pass" or update to 83. Better: stop embedding point-in-time counts.

### P2-3: Story-130 line 78 still says frappe.throw() but code uses AssertionError
Update story-130 completion notes line 78 to say raise AssertionError instead of frappe.throw().

### Files to change
- helpdesk/helpdesk/doctype/hd_ticket/test_incident_model.py (add F-13 test)
- _bmad-output/implementation-artifacts/story-130-*.md (fix frappe.throw -> AssertionError in docs)
- _bmad-output/implementation-artifacts/story-146-*.md (fix test count 80 -> 83 or remove hardcoded count)

## Acceptance Criteria

- [x] Implementation matches task description
- [x] No regressions introduced
- [x] Code compiles/builds without errors

## Tasks / Subtasks

- [x] Implement changes
- [x] Verify build passes

## Dev Notes



### References

- Task source: Claude Code Studio task #179

## Dev Agent Record

### Agent Model Used

sonnet

### Completion Notes List

- **P1-1 fixed**: Added `test_falsy_status_clears_status_category` to `test_incident_model.py`. Test seeds `status_category="Open"`, sets `status=""`, calls `doc.set_status_category()` directly, and asserts `status_category is None`. All 21 tests in the module pass.
- **P2-2 fixed**: Removed hardcoded "80" count from story-146 completion notes. New text: "All tests in `test_hd_time_entry.py` pass. (Point-in-time count removed — hardcoded counts become stale as the suite grows.)"
- **P2-3 fixed**: Updated story-130 completion notes line 78: `frappe.throw()` → `raise AssertionError(...)` to match the actual committed code.
- All 21 `test_incident_model` tests pass. No regressions.

### Change Log

- `helpdesk/helpdesk/doctype/hd_ticket/test_incident_model.py`: Added `test_falsy_status_clears_status_category` (F-13 coverage). Synced to frappe-bench.
- `_bmad-output/implementation-artifacts/story-130-*.md`: Fixed completion notes line 78: `frappe.throw()` → `raise AssertionError(...)`.
- `_bmad-output/implementation-artifacts/story-146-*.md`: Removed hardcoded "80" test count, replaced with "All tests pass" + note explaining why point-in-time counts are removed.

### File List

All 9 files present in commit `0dc9def81` are acknowledged below. The 6 extra files beyond the 3 originally declared were committed alongside intended changes — a recurrence of commit-scope pollution (task description P1):

- `helpdesk/helpdesk/doctype/hd_ticket/test_incident_model.py` (modified — added F-13 test)
- `_bmad-output/implementation-artifacts/story-130-fix-p1-p2-from-adversarial-review-task-120-stale-test-count-.md` (modified)
- `_bmad-output/implementation-artifacts/story-146-fix-p1-delete-entry-double-get-roles-stale-test-count-audit-.md` (modified)
- `_bmad-output/implementation-artifacts/story-170-qa-fix-p2-findings-from-adversarial-review-of-story-122-fixe.md` (extra — from task #170, committed unintentionally)
- `_bmad-output/implementation-artifacts/story-174-qa-fix-p1-test-deadlocks-in-test-close-tickets-p2-redundant-.md` (extra — from task #174, committed unintentionally)
- `_bmad-output/implementation-artifacts/story-179-fix-p1-undeclared-scope-creep-in-task-163-p2-stale-test-coun.md` (this file — committed as part of the task)
- `_bmad-output/implementation-artifacts/story-182-fix-p1-dev-bench-desync-in-utils-py-hd-time-entry-py-commit-.md` (extra — from task #182, committed unintentionally)
- `_bmad-output/sprint-status.yaml` (extra — committed unintentionally)
- `docs/qa-report-task-164.md` (extra — from QA task #164, committed unintentionally)
