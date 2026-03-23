# Story: Fix: P1 story-204 claims credit for task-203 work + commit-scope pollution (story-206/207 bundled) + stale counts

Status: in-progress
Task ID: mn3fz67njx1pwg
Task Number: #214
Workflow: quick-dev
Model: sonnet
Created: 2026-03-23T17:10:37.620Z

## Description

## P1/P2 Fixes from adversarial review task-208

See docs/qa-report-task-204.md for full report (14 findings).

### P1-1: Story-204 audit trail fabrication
Story-204 Completion Notes, Change Log, and File List claim to have modified story-130 (line 75: 4->9 tests) and story-153 (line 78: 84->89 tests). Both changes are in commit 5c626bfce (task-203), NOT commit d0fe50464 (task-204). Story-204 File List and Change Log must be corrected.

### P1-2: Commit-scope pollution in task-204 commit
Commit d0fe50464 bundles story-206 and story-207 (unrelated tasks). Story-204 File List must acknowledge this.

### P2: Story-153 line 78 stale count
Line 78 says "80 in test_hd_time_entry.py" but actual is 81. Total says 89 but should be 90.

### P2: Story-130 line 75 hardcoded count
Line 75 says "all 9 tests pass" -- hardcoded count violates policy on line 81. Remove count per established policy.

### Files to change
- _bmad-output/implementation-artifacts/story-204-*.md (correct audit trail)
- _bmad-output/implementation-artifacts/story-130-*.md (remove hardcoded count on line 75)
- _bmad-output/implementation-artifacts/story-153-*.md (fix 80->81, 89->90 on line 78)

## Acceptance Criteria

- [ ] Implementation matches task description
- [ ] No regressions introduced
- [ ] Code compiles/builds without errors

## Tasks / Subtasks

- [ ] Implement changes
- [ ] Verify build passes

## Dev Notes



### References

- Task source: Claude Code Studio task #214

## Dev Agent Record

### Agent Model Used

sonnet

### Completion Notes List

_(Updated by agent on completion)_

### Change Log

_(Updated by agent during implementation)_

### File List

_(Updated by agent — list all files created or modified)_
