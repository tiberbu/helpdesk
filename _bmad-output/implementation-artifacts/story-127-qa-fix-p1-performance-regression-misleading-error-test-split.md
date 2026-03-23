# Story: QA: Fix P1 performance regression + misleading error + test split reality

Status: done
Task ID: mn3d0w8pi79qof
Task Number: #127
Workflow: adversarial-review
Model: opus
Created: 2026-03-23T16:22:44.179Z

## Description

## QA for Story #122 fixes

Verify all fixes from task mn3csloyxbktc8:

### Changes to verify:
1. **F-01**: `set_status_category()` in hd_ticket.py now uses `frappe.get_cached_value()` instead of `frappe.get_value()` — confirm the method signature changed, no regressions in tests.
2. **F-02**: Disambiguated None return — two distinct error messages: (a) deleted record → "no longer exists"; (b) empty category field → "exists but has no category assigned".
3. **F-03**: `_resolve_ticket()` in test_hd_ticket.py no longer hard-codes `ticket.status_category = "Resolved"`, now calls `ticket.set_status_category()` instead.
4. **F-05**: New test `test_save_raises_validation_error_when_status_record_deleted` in test_incident_model.py passes.
5. **F-08**: `close_tickets_after_n_days()` commits error log before rollback.

### Test steps:
- Run `bench --site helpdesk.localhost run-tests --app helpdesk --module helpdesk.helpdesk.doctype.hd_ticket.test_hd_ticket` — verify category tests pass
- Run `bench --site helpdesk.localhost run-tests --app helpdesk --module helpdesk.helpdesk.doctype.hd_ticket.test_incident_model --skip-before-tests` — verify all 19 pass
- Code review: confirm get_cached_value usage, disambiguated error messages, test fix

### Files changed:
- helpdesk/helpdesk/doctype/hd_ticket/hd_ticket.py
- helpdesk/helpdesk/doctype/hd_ticket/test_hd_ticket.py
- helpdesk/helpdesk/doctype/hd_ticket/test_incident_model.py

Use Playwright MCP for browser testing if applicable.

## Acceptance Criteria

- [x] **F-01**: `set_status_category()` in hd_ticket.py now uses `frappe.get_cached_value()` instead of `frappe.get_value()` — confirm the method signature changed, no regressions in tests.
- [x] **F-02**: Disambiguated None return — two distinct error messages: (a) deleted record → "no longer exists"; (b) empty category field → "exists but has no category assigned".
- [x] **F-03**: `_resolve_ticket()` in test_hd_ticket.py no longer hard-codes `ticket.status_category = "Resolved"`, now calls `ticket.set_status_category()` instead.
- [x] **F-05**: New test `test_save_raises_validation_error_when_status_record_deleted` in test_incident_model.py passes.
- [x] **F-08**: `close_tickets_after_n_days()` commits error log before rollback.

## Tasks / Subtasks

- [x] **F-01**: `set_status_category()` in hd_ticket.py now uses `frappe.get_cached_value()` instead of `frappe.get_value()` — confirm the method signature changed, no regressions in tests.
- [x] **F-02**: Disambiguated None return — two distinct error messages: (a) deleted record → "no longer exists"; (b) empty category field → "exists but has no category assigned".
- [x] **F-03**: `_resolve_ticket()` in test_hd_ticket.py no longer hard-codes `ticket.status_category = "Resolved"`, now calls `ticket.set_status_category()` instead.
- [x] **F-05**: New test `test_save_raises_validation_error_when_status_record_deleted` in test_incident_model.py passes.
- [x] **F-08**: `close_tickets_after_n_days()` commits error log before rollback.

## Dev Notes



### References

- Task source: Claude Code Studio task #127

## Dev Agent Record

### Agent Model Used

opus

### Completion Notes List

- Adversarial review completed with 13 findings (5x P2, 8x P3)
- All 5 acceptance criteria verified: code changes confirmed, tests pass
- All 19 incident model tests pass; all 5 category validation tests pass
- Dev/bench file parity confirmed (zero diff on all 3 files)
- Key findings: no test for F-02 path (b) empty-category, F-05 test may catch Frappe link validation not custom guard, inconsistent caching strategy, pre-existing 42% test failure rate in TestHDTicket

### Change Log

- Created `docs/qa-report-story-127-adversarial-review.md` — full adversarial review report

### File List

- `docs/qa-report-story-127-adversarial-review.md` (created)
