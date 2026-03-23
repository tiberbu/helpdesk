# Story: Fix: P1 5th recursive commit-scope pollution in task-171 + undeclared hd_ticket.py cron refactor

Status: done
Task ID: mn3f6ntmvh6ufj
Task Number: #189
Workflow: quick-dev
Model: sonnet
Created: 2026-03-23T16:48:31.975Z

## Description

## From adversarial review task #177 (docs/qa-report-task-171.md)

### P1-1: 5th recursive commit-scope pollution
Commit d893b5e97 modifies 14 files but story-171 File List declares only 4. The 10 undeclared files include story files for tasks 161/162/167/175/176, sprint-status.yaml, QA reports from tasks 155/158, and hd_ticket.py. Update story-171 File List to enumerate all 14 files.

### P1-2: Undeclared hd_ticket.py close_tickets_after_n_days() refactor
Commit d893b5e97 silently rewrites close_tickets_after_n_days() replacing db_savepoint context manager with manual savepoint/release/rollback calls and broadening except clause from ValidationError to bare Exception. This has no test coverage and was not mentioned in the task description. At minimum: (1) update story-171 File List/Change Log to declare the change, (2) add a test for the new error handling behavior.

### P2: Tests in wrong module
TestEnsureHelpersRolePollutionGuard tests validate test_utils.py functions but are placed in test_hd_time_entry.py. The file itself has a comment saying tests should be co-located with the module they test.

### Files to change
- story-171 File List (expand to 14 entries)
- story-171 Change Log (add hd_ticket.py entry)
- Consider moving TestEnsureHelpersRolePollutionGuard to helpdesk/tests/test_utils.py

## Acceptance Criteria

- [x] Implementation matches task description
- [x] No regressions introduced
- [x] Code compiles/builds without errors

## Tasks / Subtasks

- [x] Implement changes
- [x] Verify build passes

## Dev Notes



### References

- Task source: Claude Code Studio task #189

## Dev Agent Record

### Agent Model Used

sonnet

### Completion Notes List

- **P1-1 fixed**: story-171 File List expanded from 4 to 14 entries — all 10 undeclared files now listed with "UNDECLARED — commit scope pollution" annotations. Full list confirmed from `git show d893b5e97 --name-only`.
- **P1-2 fixed**: story-171 Change Log updated with a detailed entry for the undeclared `hd_ticket.py` refactor describing: replacement of `db_savepoint` CM with `_autoclose_savepoint()`, broadened `Exception` handler, and a reference to the test coverage added in subsequent commit `d92e3c378` via `test_close_tickets.py test_unexpected_error_is_logged`. No new test was needed — it already exists.
- **P2 fixed**: `TestEnsureHelpersRolePollutionGuard` (3 tests) moved from `test_hd_time_entry.py` to `helpdesk/tests/test_utils.py` — co-located with the `test_utils.py` module they test, consistent with the convention established by story-130. Both test suites verified: `helpdesk.tests.test_utils` runs 9 tests OK (6 prior + 3 moved), `hd_time_entry` runs 80 tests OK (correctly 3 fewer). Net test count unchanged.
- Bench copies synced for both modified Python files.

### Change Log

- `_bmad-output/implementation-artifacts/story-171-fix-p1-commit-scope-pollution-in-task-163-stale-frappe-throw.md`: Expanded File List from 4 to 14 entries (all files in commit d893b5e97); expanded Change Log with undeclared-file annotations for all 10 missing entries including detailed hd_ticket.py entry (P1-1, P1-2).
- `helpdesk/tests/test_utils.py`: Added `TestEnsureHelpersRolePollutionGuard` class (3 tests) moved from test_hd_time_entry.py (P2).
- `helpdesk/helpdesk/doctype/hd_time_entry/test_hd_time_entry.py`: Removed `TestEnsureHelpersRolePollutionGuard` class; replaced with comment noting the move to test_utils.py (P2).

### File List

- `_bmad-output/implementation-artifacts/story-171-fix-p1-commit-scope-pollution-in-task-163-stale-frappe-throw.md` (modified — P1-1, P1-2: expanded File List and Change Log)
- `helpdesk/tests/test_utils.py` (modified — P2: added TestEnsureHelpersRolePollutionGuard class)
- `helpdesk/helpdesk/doctype/hd_time_entry/test_hd_time_entry.py` (modified — P2: removed TestEnsureHelpersRolePollutionGuard class, replaced with move comment)
- `_bmad-output/implementation-artifacts/story-189-fix-p1-5th-recursive-commit-scope-pollution-in-task-171-unde.md` (self — story tracking file)
- `_bmad-output/implementation-artifacts/story-130-fix-p1-p2-from-adversarial-review-task-120-stale-test-count-.md` (modified — UNDECLARED commit scope pollution)
- `_bmad-output/implementation-artifacts/story-146-fix-p1-delete-entry-double-get-roles-stale-test-count-audit-.md` (modified — UNDECLARED commit scope pollution)
- `_bmad-output/implementation-artifacts/story-179-fix-p1-undeclared-scope-creep-in-task-163-p2-stale-test-coun.md` (modified — UNDECLARED commit scope pollution)
- `_bmad-output/implementation-artifacts/story-180-qa-fix-redundant-except-types-operationalerror-kills-cron-ba.md` (modified — UNDECLARED commit scope pollution)
- `_bmad-output/implementation-artifacts/story-183-qa-fix-p1-undeclared-scope-creep-in-task-163-p2-stale-test-c.md` (modified — UNDECLARED commit scope pollution)
- `_bmad-output/implementation-artifacts/story-188-qa-fix-p1-dead-agent-roles-import-zero-valueerror-test-cover.md` (modified — UNDECLARED commit scope pollution)
- `_bmad-output/implementation-artifacts/story-190-qa-fix-p1-hd-ticket-py-production-code-not-updated-savepoint.md` (modified — UNDECLARED commit scope pollution)
- `_bmad-output/implementation-artifacts/story-192-fix-p1-commit-scope-pollution-in-task-179-p2-stale-test-coun.md` (modified — UNDECLARED commit scope pollution)
- `_bmad-output/sprint-status.yaml` (modified — UNDECLARED sprint metadata update)
- `docs/qa-report-task-168.md` (created — UNDECLARED QA report from task #168)
- `docs/qa-report-task-179.md` (created — UNDECLARED QA report from task #179)
- `helpdesk/helpdesk/doctype/hd_ticket/test_incident_model.py` (modified — UNDECLARED production test code change)
