# Story: Fix: P1 4th recursive commit-scope pollution in story-158 + incomplete File Lists in stories 133/158

Status: in-progress
Task ID: mn3etoi3vgzz1v
Task Number: #176
Workflow: quick-dev
Model: sonnet
Created: 2026-03-23T16:38:34.849Z

## Description

## From adversarial review task #162 (docs/qa-report-task-158.md)

### P1: Task #158 commit (752897a89) bundles 6 unrelated files — 4th recursive instance
Commit touches 10 files but only 4 are in scope. 6 unrelated files: story-128, story-153, story-159, sprint-status.yaml, qa-report-story-127, qa-report-task-146. This is the 4th recursive instance of the defect this chain was created to fix.

### P1: Story-158 File List is incomplete (lists 4 of 10 files)
Same defect as P2 in story-150 and story-144.

### P2: Story-133 File List omits HD Admin tests
Change Log correctly mentions 2 HD Admin tests but File List line 72 still says "5 string inf/nan rejection tests + 1 scientific notation doc test + 2 billable clamp tests" — missing "+ 2 HD Admin tests".

### Recommendation from QA
Stop the recursion. Batch-fix all File List inconsistencies (stories 133, 158) in ONE commit touching ONLY those files. Add a process note that commit scope pollution is a tooling artifact.

### Files to modify
- story-158 File List (expand to 10 entries)
- story-133 File List line 72 (add HD Admin test count)
- Consider adding process note to sprint-status.yaml about commit scope pollution

## Acceptance Criteria

- [ ] Implementation matches task description
- [ ] No regressions introduced
- [ ] Code compiles/builds without errors

## Tasks / Subtasks

- [ ] Implement changes
- [ ] Verify build passes

## Dev Notes



### References

- Task source: Claude Code Studio task #176

## Dev Agent Record

### Agent Model Used

sonnet

### Completion Notes List

_(Updated by agent on completion)_

### Change Log

_(Updated by agent during implementation)_

### File List

_(Updated by agent — list all files created or modified)_
