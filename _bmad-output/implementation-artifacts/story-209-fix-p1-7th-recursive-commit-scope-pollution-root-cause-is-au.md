# Story: Fix: P1 7th recursive commit-scope pollution — root cause is auto-commit staging all dirty files

Status: in-progress
Task ID: mn3fvo8xs6zmpj
Task Number: #209
Workflow: quick-dev
Model: sonnet
Created: 2026-03-23T17:08:09.849Z

## Description

## QA Findings from adversarial review docs/qa-report-task-197.md

**Finding 1 (P1)**: 7th recursive commit-scope pollution. Task-197 deliverables scattered across 3 foreign commits (bf2e19d09, c41b18182, b2e688d8a) with zero deliverables in its own commit. The fix-for-fix chain is a self-referential infinite loop.

**Finding 2 (P1)**: Commit bf2e19d09 (task-196) bundles 17 files including 5 QA reports and task-197 code.

**Finding 3 (P1)**: Story-197 File List is itself inaccurate — declares files that exist in no commit.

**Finding 4 (P1)**: Root cause never addressed. The auto-commit mechanism stages all dirty files regardless of task scope.

**ROOT CAUSE FIX REQUIRED**: Stop creating documentation-only fixes. The auto-commit system must be modified to stage only files declared in the story File List, OR use git stash to isolate the working tree per task, OR accept that File Lists are unreliable and remove them as audit artifacts.

**Finding 5 (P2)**: Test has redundant frappe.set_user call (same user set twice).

**Finding 6 (P2)**: No integration test for ValueError via on_trash() — guard is unreachable from production call paths.

**Finding 7 (P2)**: AC-4 closed by pointing to pre-existing tests rather than writing dedicated unit tests for _autoclose_savepoint() defensive paths.

**Finding 8 (P2)**: Dev/bench sync claimed but commit attribution is broken.

## Acceptance Criteria

- [ ] Implementation matches task description
- [ ] No regressions introduced
- [ ] Code compiles/builds without errors

## Tasks / Subtasks

- [ ] Implement changes
- [ ] Verify build passes

## Dev Notes



### References

- Task source: Claude Code Studio task #209

## Dev Agent Record

### Agent Model Used

sonnet

### Completion Notes List

_(Updated by agent on completion)_

### Change Log

_(Updated by agent during implementation)_

### File List

_(Updated by agent — list all files created or modified)_
