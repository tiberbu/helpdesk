# Story: Fix: P1 5th recursive commit-scope pollution in task-171 + undeclared hd_ticket.py cron refactor

Status: in-progress
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

- [ ] Implementation matches task description
- [ ] No regressions introduced
- [ ] Code compiles/builds without errors

## Tasks / Subtasks

- [ ] Implement changes
- [ ] Verify build passes

## Dev Notes



### References

- Task source: Claude Code Studio task #189

## Dev Agent Record

### Agent Model Used

sonnet

### Completion Notes List

_(Updated by agent on completion)_

### Change Log

_(Updated by agent during implementation)_

### File List

_(Updated by agent — list all files created or modified)_
