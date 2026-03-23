# Story: Fix: P1 5th recursive commit-scope pollution in task-176 + false docs-only claim + undocumented breaking is_agent() change

Status: in-progress
Task ID: mn3f6fm2jkszei
Task Number: #187
Workflow: quick-dev
Model: sonnet
Created: 2026-03-23T16:48:21.722Z

## Description

## From adversarial review task #178 (docs/qa-report-task-176.md)

### P1-1: 5th recursive instance of commit-scope pollution
Task #176 commit (fb0c46668) touches 8 files but File List declares only 3. Out-of-scope files: story-170 (new 83-line file), sprint-status.yaml, test_close_tickets.py, hd_time_entry.py, utils.py. This is the 5th recursive instance of the defect the chain was created to fix.

### P1-2: False "documentation-only" claim in Completion Notes
Story-176 states "No source code changes; no regressions possible. This is a documentation-only fix." The commit modifies 3 Python source files with substantive logic changes.

### P1-3: Breaking is_agent() ValueError with no migration path
utils.py now raises ValueError when user_roles is passed for non-session user. This is a behavioral breaking change bundled silently into a docs-only task.

### P2-1: PRIVILEGED_ROLES changed from dynamic to static enumeration
hd_time_entry.py rewrote PRIVILEGED_ROLES from AGENT_ROLES - {"Agent"} to explicit frozenset — undocumented privilege model change.

### P2-2: Test weakening in test_close_tickets.py
Error Log count assertions removed without replacement assertions.

### Recommendation
1. Update story-176 File List to 8 entries (label 5 out-of-scope as tooling artifacts)
2. Correct the false "documentation-only" Completion Notes
3. Review whether the is_agent() ValueError, PRIVILEGED_ROLES change, and test weakening should be reverted or properly documented as separate tasks
4. Add task-specific AC to prevent future recurrence

## Acceptance Criteria

- [ ] Update story-176 File List to 8 entries (label 5 out-of-scope as tooling artifacts)
- [ ] Correct the false "documentation-only" Completion Notes
- [ ] Review whether the is_agent() ValueError, PRIVILEGED_ROLES change, and test weakening should be reverted or properly documented as separate tasks
- [ ] Add task-specific AC to prevent future recurrence

## Tasks / Subtasks

- [ ] Update story-176 File List to 8 entries (label 5 out-of-scope as tooling artifacts)
- [ ] Correct the false "documentation-only" Completion Notes
- [ ] Review whether the is_agent() ValueError, PRIVILEGED_ROLES change, and test weakening should be reverted or properly documented as separate tasks
- [ ] Add task-specific AC to prevent future recurrence

## Dev Notes



### References

- Task source: Claude Code Studio task #187

## Dev Agent Record

### Agent Model Used

sonnet

### Completion Notes List

_(Updated by agent on completion)_

### Change Log

_(Updated by agent during implementation)_

### File List

_(Updated by agent — list all files created or modified)_
