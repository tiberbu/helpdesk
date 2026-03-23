# Story: Fix: P1 7th recursive commit-scope pollution in task-202 + stale 80-test count + ignored pre-commit hook recommendation

Status: in-progress
Task ID: mn3fy95vfid0s8
Task Number: #210
Workflow: quick-dev
Model: sonnet
Created: 2026-03-23T17:09:54.788Z

## Description

## From adversarial review task #205 (docs/qa-report-task-202.md)

### P1-1: 7th recursive commit-scope pollution
Commit f26716cd9 modifies 15 files but story-202 File List declares only 4. The 11 undeclared files include 6 story artifacts, sprint-status.yaml, and 3 QA reports. Update story-202 File List to enumerate all 15 files.

### P1-2: Systemic pre-commit hook recommendation ignored
The QA report from task-194 recommended a pre-commit hook to break the pollution cycle. Task-202 silently dropped this. Either implement a lightweight hook or add an explicit policy decision to the project docs explaining why story File Lists need not track auto-generated bmad/QA artifacts.

### P1-3: Stale test count in story-171 cross-reference
Story-171 line 69 says test_hd_time_entry.py has 80 tests after the move, but actual count is 81. The 81st test was added by commit bf2e19d09 (task-196). Fix the count or remove absolute counts from cross-references.

### Systemic recommendation
Consider adding a policy document or .gitattributes rule that excludes _bmad-output/ and docs/qa-report-*.md from File List tracking requirements, which would break the infinite pollution loop permanently.

## Acceptance Criteria

- [ ] Implementation matches task description
- [ ] No regressions introduced
- [ ] Code compiles/builds without errors

## Tasks / Subtasks

- [ ] Implement changes
- [ ] Verify build passes

## Dev Notes



### References

- Task source: Claude Code Studio task #210

## Dev Agent Record

### Agent Model Used

sonnet

### Completion Notes List

_(Updated by agent on completion)_

### Change Log

_(Updated by agent during implementation)_

### File List

_(Updated by agent — list all files created or modified)_
