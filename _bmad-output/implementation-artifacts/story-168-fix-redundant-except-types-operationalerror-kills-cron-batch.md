# Story: Fix: Redundant except types + OperationalError kills cron batch + stale cache docstring

Status: in-progress
Task ID: mn3eiurk00ajtj
Task Number: #168
Workflow: quick-dev
Model: sonnet
Created: 2026-03-23T16:30:11.322Z

## Description

## P1 Findings from adversarial review (docs/qa-report-task-122.md)

### F-01 [P1] — Redundant exception types in except clause
File: hd_ticket.py:1531 — `except (frappe.ValidationError, frappe.LinkValidationError, frappe.DoesNotExistError):`
Both LinkValidationError and DoesNotExistError are subclasses of ValidationError. Simplify to `except frappe.ValidationError:`.

### F-02 [P1] — Narrowed except clause crashes entire cron batch on OperationalError
File: hd_ticket.py:1531 — close_tickets_after_n_days narrowed from bare `except Exception` to only ValidationError. If ticket #3 of 100 triggers a transient OperationalError (deadlock, lock wait timeout), tickets 4-100 never get processed. Fix: catch Exception but log at different levels (WARNING for ValidationError, ERROR for unexpected), while continuing the loop for all exceptions.

### F-03 [P1] — get_cached_value docstring misleading about cross-process staleness
File: hd_ticket.py:1045-1063 — Docstring claims cache is invalidated when HD Ticket Status is saved, but frappe.get_cached_value uses in-process document cache, not shared across Gunicorn workers. Add a note about cross-process staleness.

### Also fix (P2):
- F-06: No test for empty-category branch of F-02 disambiguation. Add test_save_raises_when_status_has_empty_category.

### Files to modify:
- helpdesk/helpdesk/doctype/hd_ticket/hd_ticket.py (F-01, F-02, F-03)
- helpdesk/helpdesk/doctype/hd_ticket/test_incident_model.py (F-06)

## Acceptance Criteria

- [ ] Implementation matches task description
- [ ] No regressions introduced
- [ ] Code compiles/builds without errors

## Tasks / Subtasks

- [ ] Implement changes
- [ ] Verify build passes

## Dev Notes



### References

- Task source: Claude Code Studio task #168

## Dev Agent Record

### Agent Model Used

sonnet

### Completion Notes List

_(Updated by agent on completion)_

### Change Log

_(Updated by agent during implementation)_

### File List

_(Updated by agent — list all files created or modified)_
