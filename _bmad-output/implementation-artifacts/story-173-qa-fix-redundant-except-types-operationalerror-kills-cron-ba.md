# Story: QA: Fix: Redundant except types + OperationalError kills cron batch + stale cache docstring

Status: done
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

- [x] **F-01+F-02** (`close_tickets_after_n_days`, ~line 1551): `except (frappe.ValidationError, ...)` replaced with `except Exception as exc` + differential logging — ValidationError logs WARNING, unexpected exceptions log ERROR. Loop continues in all cases.
- [x] **F-03** (`set_status_category` docstring, ~line 1052): Added explicit NOTE about cross-process cache staleness with Gunicorn workers.
- [x] **F-06**: Pre-existing test `test_save_raises_validation_error_when_status_has_no_category` already covers empty-category branch — no new test added.
- [x] Run `bench --site helpdesk.localhost run-tests --app helpdesk --module helpdesk.helpdesk.doctype.hd_ticket.test_incident_model` — all 20 tests must pass.
- [x] Read `hd_ticket.py` around line 1551 and confirm: `except Exception as exc`, `isinstance(exc, frappe.ValidationError)` → WARNING, else ERROR, loop never broken.
- [x] Read docstring at `set_status_category` (~line 1058) and confirm cross-process staleness note is present.
- [x] Confirm `frappe.LinkValidationError` and `frappe.DoesNotExistError` no longer appear in the except clause.

## Tasks / Subtasks

- [x] **F-01+F-02** (`close_tickets_after_n_days`, ~line 1551): `except (frappe.ValidationError, ...)` replaced with `except Exception as exc` + differential logging — ValidationError logs WARNING, unexpected exceptions log ERROR. Loop continues in all cases.
- [x] **F-03** (`set_status_category` docstring, ~line 1052): Added explicit NOTE about cross-process cache staleness with Gunicorn workers.
- [x] **F-06**: Pre-existing test `test_save_raises_validation_error_when_status_has_no_category` already covers empty-category branch — no new test added.
- [x] Run `bench --site helpdesk.localhost run-tests --app helpdesk --module helpdesk.helpdesk.doctype.hd_ticket.test_incident_model` — all 20 tests must pass.
- [x] Read `hd_ticket.py` around line 1551 and confirm: `except Exception as exc`, `isinstance(exc, frappe.ValidationError)` → WARNING, else ERROR, loop never broken.
- [x] Read docstring at `set_status_category` (~line 1058) and confirm cross-process staleness note is present.
- [x] Confirm `frappe.LinkValidationError` and `frappe.DoesNotExistError` no longer appear in the except clause.

## Dev Notes



### References

- Task source: Claude Code Studio task #173

## Dev Agent Record

### Agent Model Used

opus

### Completion Notes List

Adversarial review completed. 12 findings (1 P1, 5 P2, 6 P3). Full report at `docs/qa-report-task-173-adversarial-review.md`. All 20 incident model tests pass. All acceptance criteria verified — the code changes are present and correct. Key concerns: (1) no test for the OperationalError branch (P2), (2) unconditional commit without finally guard (P1), (3) docstring inaccuracy about cache staleness window (P2).

### Change Log

- Created `docs/qa-report-task-173-adversarial-review.md` — adversarial review report with 12 findings

### File List

- `docs/qa-report-task-173-adversarial-review.md` (created)
