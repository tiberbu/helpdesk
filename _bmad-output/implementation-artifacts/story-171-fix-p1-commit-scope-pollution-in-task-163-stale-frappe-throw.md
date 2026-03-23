# Story: Fix: P1 commit-scope pollution in task-163 + stale frappe.throw ref in story-146 + on_trash double get_roles

Status: in-progress
Task ID: mn3enktsmbjchx
Task Number: #171
Workflow: quick-dev
Model: sonnet
Created: 2026-03-23T16:33:52.032Z

## Description

## P1 Fixes from adversarial review task-166

See docs/qa-report-task-166-adversarial-review.md for full report (14 findings).

### P1-1: Task-163 commit (0a45dc533) contains UNDECLARED Python changes
Commit includes hd_ticket.py (F-13 status_category clearing) and test_incident_model.py changes NOT listed in story-163 completion notes/change log/file list. Update story-163 completion notes with accurate file list.

### P1-2: Story-146 change log still says frappe.throw()
Line 76 of story-146 says "Added role-pollution frappe.throw() assertions" but task-163 changed these to raise AssertionError. Update the change log entry.

### P1-3: hd_time_entry.json System Manager has share/email/export/print/report=1
Inconsistent with read-only intent. Review and remove share at minimum.

### P2-7: on_trash() double get_roles()
on_trash() calls is_agent(user) then _check_delete_permission(self, user) without passing user_roles — same double DB hit pattern fixed in delete_entry().

### P2-4: No test for ensure_* AssertionError behavior
Add a test that deliberately pollutes roles and verifies AssertionError is raised.

### Files to change
- story-163 completion notes (add undeclared files)
- story-146 completion notes (fix frappe.throw ref)
- helpdesk/helpdesk/doctype/hd_time_entry/hd_time_entry.py (on_trash user_roles passthrough)
- helpdesk/helpdesk/doctype/hd_time_entry/hd_time_entry.json (review System Manager permissions)
- helpdesk/helpdesk/doctype/hd_time_entry/test_hd_time_entry.py (test ensure_* raises AssertionError)

## Acceptance Criteria

- [ ] Implementation matches task description
- [ ] No regressions introduced
- [ ] Code compiles/builds without errors

## Tasks / Subtasks

- [ ] Implement changes
- [ ] Verify build passes

## Dev Notes



### References

- Task source: Claude Code Studio task #171

## Dev Agent Record

### Agent Model Used

sonnet

### Completion Notes List

_(Updated by agent on completion)_

### Change Log

_(Updated by agent during implementation)_

### File List

_(Updated by agent — list all files created or modified)_
