# Story: Fix: _require_int_str float-string mismatch (P1) + undocumented is_admin(user) fix (P1) from QA task #112

Status: in-progress
Task ID: mn3crp0h5ualkh
Task Number: #121
Workflow: quick-dev
Model: sonnet
Created: 2026-03-23T15:41:04.508Z

## Description

## P1 findings from adversarial review task #112 (docs/qa-report-task-104.md)

### P1-1: _require_int_str() rejects float strings that cint() accepts
_require_int_str("3.5") raises ValidationError because int("3.5") raises ValueError, but cint("3.5") returns 3. Zero tests for edge cases: float strings, empty strings, whitespace, booleans, None. Add comprehensive tests and document intended behavior. Consider using int(float(value.strip())) to match cint behavior.

### P1-2: is_admin(user) parameter fix in utils.py is undocumented
The change from is_admin() to is_admin(user) in is_agent() has global scope affecting all callers. Add a dedicated test: is_agent(user="someone") must check that specific user, not frappe.session.user. Document in story change log.

### Files to modify
- helpdesk/api/time_tracking.py (_require_int_str edge cases)
- helpdesk/helpdesk/doctype/hd_time_entry/test_hd_time_entry.py (add edge case tests)
- helpdesk/utils.py (add test for is_agent with explicit user param)
- Sync to bench + reload gunicorn

## Acceptance Criteria

- [ ] Implementation matches task description
- [ ] No regressions introduced
- [ ] Code compiles/builds without errors

## Tasks / Subtasks

- [ ] Implement changes
- [ ] Verify build passes

## Dev Notes



### References

- Task source: Claude Code Studio task #121

## Dev Agent Record

### Agent Model Used

sonnet

### Completion Notes List

_(Updated by agent on completion)_

### Change Log

_(Updated by agent during implementation)_

### File List

_(Updated by agent — list all files created or modified)_
