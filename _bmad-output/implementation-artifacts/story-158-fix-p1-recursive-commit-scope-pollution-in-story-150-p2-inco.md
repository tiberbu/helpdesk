# Story: Fix: P1 recursive commit-scope pollution in story-150 + P2 incomplete File List + stale 7-count in story-144

Status: in-progress
Task ID: mn3eao24ifk5xp
Task Number: #158
Workflow: quick-dev
Model: sonnet
Created: 2026-03-23T16:23:48.995Z

## Description

## From adversarial review task #154 (docs/qa-report-task-150.md)

### P1: Task #150 commit bundles 4 unrelated files (same defect it was created to fix)
Commit 95e55885a touches 7 files but only 3 are in scope. story-149, story-152, sprint-status.yaml, and docs/qa-report-task-149.md are unrelated. This is the third recursive instance.

### P2: Story-150 File List is incomplete (lists 3 of 7 files)
Same defect as the P2 it fixed in story-144.

### P2: Story-144 Completion Notes still say "7 string inf/nan tests"
Task-150 corrected story-133 to say 5 but did not update story-144 own reference to the same count.

### P2: 2 HD Admin tests in da95326be unaccounted in story-133 audit
test_hd_admin_can_stop_timer and test_hd_admin_can_get_summary are not mentioned in story-133 corrected notes.

### Files to modify
- story-150 File List (expand to 7)
- story-144 Completion Notes (7 -> 5 correction)
- story-133 (add HD Admin test attribution)

## Acceptance Criteria

- [ ] Implementation matches task description
- [ ] No regressions introduced
- [ ] Code compiles/builds without errors

## Tasks / Subtasks

- [ ] Implement changes
- [ ] Verify build passes

## Dev Notes



### References

- Task source: Claude Code Studio task #158

## Dev Agent Record

### Agent Model Used

sonnet

### Completion Notes List

_(Updated by agent on completion)_

### Change Log

_(Updated by agent during implementation)_

### File List

_(Updated by agent — list all files created or modified)_
