# Story: QA: Fix: Redundant except types + OperationalError kills cron batch + stale cache docstring

Status: in-progress
Task ID: mn3ep6tngrpfms
Task Number: #173
Workflow: adversarial-review
Model: opus
Created: 2026-03-23T16:41:53.921Z

## Description

## QA Review for Story #168

Verify the following fixes in `helpdesk/helpdesk/doctype/hd_ticket/hd_ticket.py`:

### What was changed
1. **F-01+F-02** (`close_tickets_after_n_days`, ~line 1551): `except (frappe.ValidationError, ...)` replaced with `except Exception as exc` + differential logging — ValidationError logs WARNING, unexpected exceptions log ERROR. Loop continues in all cases.
2. **F-03** (`set_status_category` docstring, ~line 1052): Added explicit NOTE about cross-process cache staleness with Gunicorn workers.
3. **F-06**: Pre-existing test `test_save_raises_validation_error_when_status_has_no_category` already covers empty-category branch — no new test added.

### Test steps
1. Run `bench --site helpdesk.localhost run-tests --app helpdesk --module helpdesk.helpdesk.doctype.hd_ticket.test_incident_model` — all 20 tests must pass.
2. Read `hd_ticket.py` around line 1551 and confirm: `except Exception as exc`, `isinstance(exc, frappe.ValidationError)` → WARNING, else ERROR, loop never broken.
3. Read docstring at `set_status_category` (~line 1058) and confirm cross-process staleness note is present.
4. Confirm `frappe.LinkValidationError` and `frappe.DoesNotExistError` no longer appear in the except clause.

### Files changed
- `helpdesk/helpdesk/doctype/hd_ticket/hd_ticket.py`

### Expected behaviour
- No cron batch crash on OperationalError
- Docstring accurately describes cache scope
- All 20 incident model tests pass

## Acceptance Criteria

- [ ] **F-01+F-02** (`close_tickets_after_n_days`, ~line 1551): `except (frappe.ValidationError, ...)` replaced with `except Exception as exc` + differential logging — ValidationError logs WARNING, unexpected exceptions log ERROR. Loop continues in all cases.
- [ ] **F-03** (`set_status_category` docstring, ~line 1052): Added explicit NOTE about cross-process cache staleness with Gunicorn workers.
- [ ] **F-06**: Pre-existing test `test_save_raises_validation_error_when_status_has_no_category` already covers empty-category branch — no new test added.
- [ ] Run `bench --site helpdesk.localhost run-tests --app helpdesk --module helpdesk.helpdesk.doctype.hd_ticket.test_incident_model` — all 20 tests must pass.
- [ ] Read `hd_ticket.py` around line 1551 and confirm: `except Exception as exc`, `isinstance(exc, frappe.ValidationError)` → WARNING, else ERROR, loop never broken.
- [ ] Read docstring at `set_status_category` (~line 1058) and confirm cross-process staleness note is present.
- [ ] Confirm `frappe.LinkValidationError` and `frappe.DoesNotExistError` no longer appear in the except clause.

## Tasks / Subtasks

- [ ] **F-01+F-02** (`close_tickets_after_n_days`, ~line 1551): `except (frappe.ValidationError, ...)` replaced with `except Exception as exc` + differential logging — ValidationError logs WARNING, unexpected exceptions log ERROR. Loop continues in all cases.
- [ ] **F-03** (`set_status_category` docstring, ~line 1052): Added explicit NOTE about cross-process cache staleness with Gunicorn workers.
- [ ] **F-06**: Pre-existing test `test_save_raises_validation_error_when_status_has_no_category` already covers empty-category branch — no new test added.
- [ ] Run `bench --site helpdesk.localhost run-tests --app helpdesk --module helpdesk.helpdesk.doctype.hd_ticket.test_incident_model` — all 20 tests must pass.
- [ ] Read `hd_ticket.py` around line 1551 and confirm: `except Exception as exc`, `isinstance(exc, frappe.ValidationError)` → WARNING, else ERROR, loop never broken.
- [ ] Read docstring at `set_status_category` (~line 1058) and confirm cross-process staleness note is present.
- [ ] Confirm `frappe.LinkValidationError` and `frappe.DoesNotExistError` no longer appear in the except clause.

## Dev Notes



### References

- Task source: Claude Code Studio task #173

## Dev Agent Record

### Agent Model Used

opus

### Completion Notes List

_(Updated by agent on completion)_

### Change Log

_(Updated by agent during implementation)_

### File List

_(Updated by agent — list all files created or modified)_
