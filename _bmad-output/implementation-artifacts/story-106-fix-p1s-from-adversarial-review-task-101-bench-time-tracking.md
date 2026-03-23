# Story: Fix: P1s from adversarial review task-101 — bench time_tracking.py sync, delete_entry info leak, auto-close savepoint isolation

Status: in-progress
Task ID: mn3c9ldhj1fhwv
Task Number: #106
Workflow: quick-dev
Model: sonnet
Created: 2026-03-23T15:26:59.453Z

## Description

## P1 Fixes from Adversarial Review (docs/qa-report-task-94.md)

### P1 #1: Bench time_tracking.py catastrophically out of sync
The bench copy at `/home/ubuntu/frappe-bench/apps/helpdesk/helpdesk/api/time_tracking.py` is missing: `_require_int_str()` helper, `_DURATION_ELAPSED_TOLERANCE_MINUTES`, elapsed-time cross-validation in stop_timer(), `_require_int_str()` calls in add_entry(), and billable {0,1} range validation. The deployed app accepts `billable=999` and `duration_minutes="abc"` without API-layer validation. Fix: rsync the dev copy to bench and reload gunicorn.

### P1 #2: Bench delete_entry() has is_agent() after frappe.get_doc() — info leak
The bench copy fetches the doc before checking `is_agent()`, allowing non-agents to probe entry existence via error type differentiation. The dev copy is correct (is_agent first). Fix: included in the sync from P1 #1.

### P1 #3: Auto-close commit/rollback with no savepoint isolation
The close_tickets_after_n_days loop calls commit() per ticket with no savepoint boundary. Cross-contamination possible. Fix: use frappe.db.savepoint() per iteration.

### P2 #4: except Exception too broad
Narrow to (frappe.ValidationError, frappe.LinkValidationError).

### P2 #6: Double _check_delete_permission on API delete
The before_delete hook runs the same check again. Either skip it in before_delete when called from API, or remove explicit call from delete_entry and drop ignore_permissions.

### P2 #10: Unused exc variable
Change `except Exception as exc:` to `except Exception:`.

### Files to modify
- Sync `helpdesk/api/time_tracking.py` to bench
- `helpdesk/helpdesk/doctype/hd_ticket/hd_ticket.py` — savepoint + narrow except
- `helpdesk/api/time_tracking.py` or `hd_time_entry.py` — fix double permission check
- Reload gunicorn after sync

## Acceptance Criteria

- [ ] Implementation matches task description
- [ ] No regressions introduced
- [ ] Code compiles/builds without errors

## Tasks / Subtasks

- [ ] Implement changes
- [ ] Verify build passes

## Dev Notes



### References

- Task source: Claude Code Studio task #106

## Dev Agent Record

### Agent Model Used

sonnet

### Completion Notes List

_(Updated by agent on completion)_

### Change Log

_(Updated by agent during implementation)_

### File List

_(Updated by agent — list all files created or modified)_
