# Story: Fix: Redundant except types + OperationalError kills cron batch + stale cache docstring

Status: complete
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

- [x] Implementation matches task description
- [x] No regressions introduced
- [x] Code compiles/builds without errors

## Tasks / Subtasks

- [x] Implement changes
- [x] Verify build passes

## Dev Notes



### References

- Task source: Claude Code Studio task #168

## Dev Agent Record

### Agent Model Used

sonnet

### Completion Notes List

- F-01: Removed redundant `frappe.LinkValidationError` and `frappe.DoesNotExistError` from except clause — both are subclasses of `frappe.ValidationError`. Replaced entire tuple with `except Exception as exc` to also fix F-02.
- F-02: Changed narrowed except clause back to `except Exception` so OperationalErrors (deadlock, lock timeout) don't crash the cron batch. ValidationError logged at WARNING; unexpected exceptions logged at ERROR via `frappe.log_error()`. All exceptions continue the loop.
- F-03: Added explicit `NOTE — cross-process cache staleness` section to `set_status_category()` docstring clarifying that `frappe.get_cached_value()` is in-process only (not shared across Gunicorn workers), with explanation of acceptable risk window.
- F-06: Already covered — `test_save_raises_validation_error_when_status_has_no_category` (line 590 of test_incident_model.py) tests the identical empty-category branch. No new test needed.
- All 20 tests in test_incident_model pass with changes applied.

### Change Log

- 2026-03-23: hd_ticket.py — F-01+F-02: replaced `except (frappe.ValidationError, frappe.LinkValidationError, frappe.DoesNotExistError)` with `except Exception as exc` + differential log levels; F-03: expanded docstring with cross-process staleness note.

### File List

- `helpdesk/helpdesk/doctype/hd_ticket/hd_ticket.py` (F-01, F-02, F-03)
- `helpdesk/helpdesk/doctype/hd_ticket/test_incident_model.py` (F-06 — pre-existing test confirmed sufficient, no changes needed)
