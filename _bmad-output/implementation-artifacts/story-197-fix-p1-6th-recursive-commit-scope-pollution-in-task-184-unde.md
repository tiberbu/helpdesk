# Story: Fix: P1 6th recursive commit-scope pollution in task-184 + undeclared hd_ticket.py refactor + born-fabricated story files

Status: done
Task ID: mn3ffww216o8xv
Task Number: #197
Workflow: quick-dev
Model: sonnet
Created: 2026-03-23T16:55:55.044Z

## Description

P1 findings from adversarial review docs/qa-report-task-184.md:

**Finding 1 (P1)**: 6th recursive commit-scope pollution. Commit 4bff11be6 touches 13 files but story-184 File List declares only 4. Nine undeclared files include production hd_ticket.py refactor, 2 QA reports from other tasks, and 4 out-of-scope story file mutations.

**Finding 2 (P1)**: Undeclared _autoclose_savepoint() context manager + close_tickets_after_n_days() rewrite in hd_ticket.py — production error-handling change with zero test coverage and zero mention in story-184.

**Finding 3 (P1)**: Story-185 and story-181 files born fabricated — created as Status: in-progress but their changes are already committed in the same commit.

**Finding 8 (P2)**: _check_delete_permission() accepts user_roles with no identity contract (unlike is_agent which now has ValueError protection).

Recommended fixes:
1. Update story-184 File List to accurately reflect all 13 files in commit
2. Update story-185 to reflect its changes were committed in task-184 commit, not independently
3. Add identity-contract ValueError to _check_delete_permission() matching is_agent() pattern
4. Add test coverage for _autoclose_savepoint() in hd_ticket.py

## Acceptance Criteria

- [x] Update story-184 File List to accurately reflect all 13 files in commit
- [x] Update story-185 to reflect its changes were committed in task-184 commit, not independently
- [x] Add identity-contract ValueError to _check_delete_permission() matching is_agent() pattern
- [x] Add test coverage for _autoclose_savepoint() in hd_ticket.py

## Tasks / Subtasks

- [x] Update story-184 File List to accurately reflect all 13 files in commit
- [x] Update story-185 to reflect its changes were committed in task-184 commit, not independently
- [x] Add identity-contract ValueError to _check_delete_permission() matching is_agent() pattern
- [x] Add test coverage for _autoclose_savepoint() in hd_ticket.py

## Dev Notes



### References

- Task source: Claude Code Studio task #197

## Dev Agent Record

### Agent Model Used

sonnet

### Completion Notes List

- AC-1: story-184 File List updated to accurately declare all 13 files from commit 4bff11be6. Original listed 4; 9 undeclared files are now documented with explanations (production hd_ticket.py, QA reports from other tasks, born-fabricated story files, sprint status, own story file).
- AC-2: story-185 Completion Notes updated with CORRECTION block clarifying its described implementation was already committed in 4bff11be6 (task-184's commit), not independently. The story has no dedicated commit of its own.
- AC-3: Added ValueError identity-contract check to `_check_delete_permission()` in hd_time_entry.py, mirroring the pattern in `is_agent()`. Raises ValueError when user_roles is provided for a non-session user. Added test `test_check_delete_permission_raises_valueerror_for_mismatched_user_roles`. All 81 hd_time_entry tests pass.
- AC-4: Test coverage for `_autoclose_savepoint()` already exists in test_close_tickets.py (committed in 4bff11be6 as part of story-185's bundled work). Tests (d) checklist guard, (e) stale ticket, and (f) unexpected error directly exercise the ValidationError and Exception paths of `_autoclose_savepoint()`. All 6 tests pass.
- Both modified Python files synced to bench.

### Change Log

- `helpdesk/helpdesk/doctype/hd_time_entry/hd_time_entry.py`: Added ValueError identity-contract guard to `_check_delete_permission()` with docstring update.
- `helpdesk/helpdesk/doctype/hd_time_entry/test_hd_time_entry.py`: Added `test_check_delete_permission_raises_valueerror_for_mismatched_user_roles`.
- `_bmad-output/implementation-artifacts/story-184-fix-p1-dead-agent-roles-import-zero-valueerror-test-coverage.md`: File List expanded from 4 to all 13 committed files with explanations.
- `_bmad-output/implementation-artifacts/story-185-fix-p1-hd-ticket-py-production-code-not-updated-savepoint-cm.md`: Completion Notes corrected — born-fabricated audit trail acknowledged.

### File List

- `helpdesk/helpdesk/doctype/hd_time_entry/hd_time_entry.py` (modified)
- `helpdesk/helpdesk/doctype/hd_time_entry/test_hd_time_entry.py` (modified)
- `_bmad-output/implementation-artifacts/story-184-fix-p1-dead-agent-roles-import-zero-valueerror-test-coverage.md` (corrected)
- `_bmad-output/implementation-artifacts/story-185-fix-p1-hd-ticket-py-production-code-not-updated-savepoint-cm.md` (corrected)
- `_bmad-output/implementation-artifacts/story-197-fix-p1-6th-recursive-commit-scope-pollution-in-task-184-unde.md` (this file)
