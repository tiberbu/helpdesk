# Story: QA: Fix: P1s from adversarial review task-90 — dedup delete_entry logic, auto-close crash guard, frozenset PRIVILEGED_ROLES

Status: in-progress
Task ID: mn3c08za7x54a7
Task Number: #100
Workflow: adversarial-review
Model: opus
Created: 2026-03-23T15:19:44.220Z

## Description

## QA Review for Task #94 — P1/P2 fixes

### What was changed
1. `helpdesk/api/time_tracking.py` — `delete_entry()` inline privilege check removed; only `is_agent()` pre-gate + `_check_delete_permission()` remain. `PRIVILEGED_ROLES` import removed.
2. `helpdesk/helpdesk/doctype/hd_time_entry/hd_time_entry.py` — `PRIVILEGED_ROLES` changed from `set` to `frozenset`.
3. `helpdesk/helpdesk/doctype/hd_ticket/hd_ticket.py` — `close_tickets_after_n_days()` loop wrapped in `try/except Exception` with `frappe.log_error` + `frappe.db.rollback()`.

### Expected behaviour
- `delete_entry()` still rejects non-agents; agents can only delete their own entries unless privileged role.
- A ticket with an incomplete mandatory checklist does NOT crash the entire cron loop — it logs an error and continues.
- `PRIVILEGED_ROLES` is immutable (frozenset).

### Test steps
1. Code review: verify no duplicate privilege logic in delete_entry
2. Code review: verify frozenset
3. Code review: verify try/except wraps entire per-ticket block
4. Browser: navigate to helpdesk.localhost:8004, log in as agent, open a ticket, use time tracking (start/stop timer, add manual entry, delete entry)
5. Check browser console for errors
6. Verify delete of own entry works, delete of another agent's entry is rejected with permission error

### Files to review
- helpdesk/api/time_tracking.py
- helpdesk/helpdesk/doctype/hd_time_entry/hd_time_entry.py
- helpdesk/helpdesk/doctype/hd_ticket/hd_ticket.py

This QA task MUST use Playwright browser testing. Produce a structured QA report in docs/qa-report-task-94.md.

## Acceptance Criteria

- [ ] `helpdesk/api/time_tracking.py` — `delete_entry()` inline privilege check removed; only `is_agent()` pre-gate + `_check_delete_permission()` remain. `PRIVILEGED_ROLES` import removed.
- [ ] `helpdesk/helpdesk/doctype/hd_time_entry/hd_time_entry.py` — `PRIVILEGED_ROLES` changed from `set` to `frozenset`.
- [ ] `helpdesk/helpdesk/doctype/hd_ticket/hd_ticket.py` — `close_tickets_after_n_days()` loop wrapped in `try/except Exception` with `frappe.log_error` + `frappe.db.rollback()`.
- [ ] Code review: verify no duplicate privilege logic in delete_entry
- [ ] Code review: verify frozenset
- [ ] Code review: verify try/except wraps entire per-ticket block
- [ ] Browser: navigate to helpdesk.localhost:8004, log in as agent, open a ticket, use time tracking (start/stop timer, add manual entry, delete entry)
- [ ] Check browser console for errors
- [ ] Verify delete of own entry works, delete of another agent's entry is rejected with permission error

## Tasks / Subtasks

- [ ] `helpdesk/api/time_tracking.py` — `delete_entry()` inline privilege check removed; only `is_agent()` pre-gate + `_check_delete_permission()` remain. `PRIVILEGED_ROLES` import removed.
- [ ] `helpdesk/helpdesk/doctype/hd_time_entry/hd_time_entry.py` — `PRIVILEGED_ROLES` changed from `set` to `frozenset`.
- [ ] `helpdesk/helpdesk/doctype/hd_ticket/hd_ticket.py` — `close_tickets_after_n_days()` loop wrapped in `try/except Exception` with `frappe.log_error` + `frappe.db.rollback()`.
- [ ] Code review: verify no duplicate privilege logic in delete_entry
- [ ] Code review: verify frozenset
- [ ] Code review: verify try/except wraps entire per-ticket block
- [ ] Browser: navigate to helpdesk.localhost:8004, log in as agent, open a ticket, use time tracking (start/stop timer, add manual entry, delete entry)
- [ ] Check browser console for errors
- [ ] Verify delete of own entry works, delete of another agent's entry is rejected with permission error

## Dev Notes



### References

- Task source: Claude Code Studio task #100

## Dev Agent Record

### Agent Model Used

opus

### Completion Notes List

_(Updated by agent on completion)_

### Change Log

_(Updated by agent during implementation)_

### File List

_(Updated by agent — list all files created or modified)_
