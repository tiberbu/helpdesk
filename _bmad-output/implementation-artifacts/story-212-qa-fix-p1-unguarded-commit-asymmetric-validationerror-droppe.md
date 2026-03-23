# Story: QA: Fix P1 unguarded commit() + asymmetric ValidationError + dropped F-06

Status: in-progress
Task ID: mn3fyujucumun0
Task Number: #212
Workflow: adversarial-review
Model: opus
Created: 2026-03-23T17:10:22.507Z

## Description

Adversarial code review of story-207 fixes to _autoclose_savepoint and close_tickets_after_n_days in hd_ticket.py.

## What was changed
- hd_ticket.py: F-01 — frappe.db.commit() in loop now wrapped in try/except
- hd_ticket.py: F-02 — frappe.logger().warning() in ValidationError handler now wrapped in try/except
- hd_ticket.py: F-03 — rollback failure except blocks now log a WARNING instead of bare pass
- hd_ticket.py: F-06 — str(_pending_log[1] or "") prevents None concatenation TypeError
- test_close_tickets.py: F-05 — new test_log_error_failure_falls_back_to_python_logger test
- story-165 artifact: F-04 — corrected false db_savepoint claims

## Files changed
- helpdesk/helpdesk/doctype/hd_ticket/hd_ticket.py
- helpdesk/helpdesk/doctype/hd_ticket/test_close_tickets.py
- _bmad-output/implementation-artifacts/story-165-fix-p1-test-deadlocks-in-test-close-tickets-p2-redundant-exc.md

## Test steps
1. Read hd_ticket.py around _autoclose_savepoint (lines ~1507-1640) and verify all 6 fixes applied correctly
2. Read test_close_tickets.py and verify new test (h) covers the fallback path properly
3. Run: bench --site helpdesk.localhost run-tests --app helpdesk --module helpdesk.helpdesk.doctype.hd_ticket.test_close_tickets
4. Verify all 8 tests pass
5. Check for edge cases or regressions — no browser testing needed (backend-only changes)

## Expected: all 8 tests pass, code is defensively correct with no new issues

## Acceptance Criteria

- [ ] Read hd_ticket.py around _autoclose_savepoint (lines ~1507-1640) and verify all 6 fixes applied correctly
- [ ] Read test_close_tickets.py and verify new test (h) covers the fallback path properly
- [ ] Run: bench --site helpdesk.localhost run-tests --app helpdesk --module helpdesk.helpdesk.doctype.hd_ticket.test_close_tickets
- [ ] Verify all 8 tests pass
- [ ] Check for edge cases or regressions — no browser testing needed (backend-only changes)

## Tasks / Subtasks

- [ ] Read hd_ticket.py around _autoclose_savepoint (lines ~1507-1640) and verify all 6 fixes applied correctly
- [ ] Read test_close_tickets.py and verify new test (h) covers the fallback path properly
- [ ] Run: bench --site helpdesk.localhost run-tests --app helpdesk --module helpdesk.helpdesk.doctype.hd_ticket.test_close_tickets
- [ ] Verify all 8 tests pass
- [ ] Check for edge cases or regressions — no browser testing needed (backend-only changes)

## Dev Notes



### References

- Task source: Claude Code Studio task #212

## Dev Agent Record

### Agent Model Used

opus

### Completion Notes List

_(Updated by agent on completion)_

### Change Log

_(Updated by agent during implementation)_

### File List

_(Updated by agent — list all files created or modified)_
