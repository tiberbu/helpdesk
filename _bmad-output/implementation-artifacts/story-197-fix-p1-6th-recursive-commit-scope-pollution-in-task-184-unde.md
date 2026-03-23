# Story: Fix: P1 6th recursive commit-scope pollution in task-184 + undeclared hd_ticket.py refactor + born-fabricated story files

Status: in-progress
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

- [ ] Update story-184 File List to accurately reflect all 13 files in commit
- [ ] Update story-185 to reflect its changes were committed in task-184 commit, not independently
- [ ] Add identity-contract ValueError to _check_delete_permission() matching is_agent() pattern
- [ ] Add test coverage for _autoclose_savepoint() in hd_ticket.py

## Tasks / Subtasks

- [ ] Update story-184 File List to accurately reflect all 13 files in commit
- [ ] Update story-185 to reflect its changes were committed in task-184 commit, not independently
- [ ] Add identity-contract ValueError to _check_delete_permission() matching is_agent() pattern
- [ ] Add test coverage for _autoclose_savepoint() in hd_ticket.py

## Dev Notes



### References

- Task source: Claude Code Studio task #197

## Dev Agent Record

### Agent Model Used

sonnet

### Completion Notes List

_(Updated by agent on completion)_

### Change Log

_(Updated by agent during implementation)_

### File List

_(Updated by agent — list all files created or modified)_
