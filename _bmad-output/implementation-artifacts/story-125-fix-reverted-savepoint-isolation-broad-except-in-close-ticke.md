# Story: Fix: Reverted savepoint isolation + broad except in close_tickets_after_n_days (P1s from QA task-116)

Status: done
Task ID: mn3cyabpids6so
Task Number: #125
Workflow: quick-dev
Model: sonnet
Created: 2026-03-23T15:46:10.353Z

## Description

## P1 Fixes Required

### P1 #1: Savepoint isolation was reverted
Story #106 added `frappe.db.savepoint()` per iteration in `close_tickets_after_n_days` but commit a7891185d removed it. The current code uses bare commit/rollback with no savepoint boundary. If a Frappe hook or child document internally calls commit() before the except block, partial state persists across iterations.

**Fix:** Re-add `with frappe.db.savepoint():` around each iteration in the loop.

### P1 #2: Except clause broadened back to except Exception
Story #106 narrowed to `(frappe.ValidationError, frappe.LinkValidationError)` but a7891185d changed it back to `except Exception:`. This swallows OperationalError, SecurityException, etc.

**Fix:** Narrow to `except (frappe.ValidationError, frappe.LinkValidationError, frappe.DoesNotExistError):` — these are the only expected failure modes for auto-close.

### P1 #3: Zero test coverage for close_tickets_after_n_days
Add tests covering: (a) happy path auto-close, (b) error isolation — failing ticket does not prevent subsequent closures, (c) checklist validation blocks auto-close.

### Files to modify
- `helpdesk/helpdesk/doctype/hd_ticket/hd_ticket.py` — lines 1506-1524
- New test file or add to existing hd_ticket tests
- Sync to bench after changes

## Acceptance Criteria

- [x] Implementation matches task description
- [x] No regressions introduced
- [x] Code compiles/builds without errors

## Tasks / Subtasks

- [x] Implement changes
- [x] Verify build passes

## Dev Notes



### References

- Task source: Claude Code Studio task #125

## Dev Agent Record

### Agent Model Used

sonnet

### Completion Notes List

- P1 #1: Re-added named savepoint isolation (`_sp = f"sp_autoclose_{ticket}"`) around each iteration. `frappe.db.savepoint(name)` is an instance method (not a context manager), so the pattern uses explicit savepoint/release_savepoint/rollback calls.
- P1 #2: Narrowed except clause from `except Exception:` to `except (frappe.ValidationError, frappe.LinkValidationError, frappe.DoesNotExistError):`.
- P1 #3: Added 4 integration tests in `test_close_tickets.py` — all pass. Root cause of prior test failures: `after_insert` creates a Communication with `communication_date=NOW()`, causing `MAX(communication_date)` to block the SQL query. Fixed by adding `_age_all_communications()` helper that backdates all communications after setup.

### Change Log

- `hd_ticket.py`: Replaced bare `except Exception:` with narrow exception tuple; replaced broken `with frappe.db.savepoint():` with correct named savepoint pattern using `frappe.db.savepoint(_sp)` / `release_savepoint` / `rollback(save_point=_sp)`.
- `test_close_tickets.py` (new): 4 integration tests covering happy path, feature-flag disabled, error isolation, and checklist validation guard.

### File List

- `helpdesk/helpdesk/doctype/hd_ticket/hd_ticket.py` (modified — lines 1515–1542)
- `helpdesk/helpdesk/doctype/hd_ticket/test_close_tickets.py` (created)
