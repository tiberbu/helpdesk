# Story: Fix: P1 undeclared scope creep in task-163 + P2 stale test count + story-130 frappe.throw stale docs

Status: in-progress
Task ID: mn3exm1mzl57jd
Task Number: #179
Workflow: quick-dev
Model: sonnet
Created: 2026-03-23T16:41:38.916Z

## Description

## P1/P2 Fixes from adversarial review task-167

See docs/qa-report-task-163.md for full report (14 findings).

### P1-1: Undeclared F-13 code change has no dedicated test
Commit 0a45dc533 added F-13 fix (status_category = None when status is falsy) to hd_ticket.py but NO test covers this specific path. Add a test that sets status to empty string, saves, and verifies status_category is None.

### P2-2: Story-146 test count already stale (claims 80, actual 83)
Replace hardcoded count with "All tests pass" or update to 83. Better: stop embedding point-in-time counts.

### P2-3: Story-130 line 78 still says frappe.throw() but code uses AssertionError
Update story-130 completion notes line 78 to say raise AssertionError instead of frappe.throw().

### Files to change
- helpdesk/helpdesk/doctype/hd_ticket/test_incident_model.py (add F-13 test)
- _bmad-output/implementation-artifacts/story-130-*.md (fix frappe.throw -> AssertionError in docs)
- _bmad-output/implementation-artifacts/story-146-*.md (fix test count 80 -> 83 or remove hardcoded count)

## Acceptance Criteria

- [ ] Implementation matches task description
- [ ] No regressions introduced
- [ ] Code compiles/builds without errors

## Tasks / Subtasks

- [ ] Implement changes
- [ ] Verify build passes

## Dev Notes



### References

- Task source: Claude Code Studio task #179

## Dev Agent Record

### Agent Model Used

sonnet

### Completion Notes List

_(Updated by agent on completion)_

### Change Log

_(Updated by agent during implementation)_

### File List

_(Updated by agent — list all files created or modified)_
