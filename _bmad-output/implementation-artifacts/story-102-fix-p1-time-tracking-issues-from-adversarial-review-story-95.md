# Story: Fix: P1 time tracking issues from adversarial review (Story #95)

Status: in-progress
Task ID: mn3c11but1xjrr
Task Number: #102
Workflow: quick-dev
Model: sonnet
Created: 2026-03-23T15:20:19.132Z

## Description

## Fix P1 findings from adversarial review (docs/qa-report-story-95-adversarial-review.md)

### P1 Issues to Fix

1. **billable silently coerced to 0** — `cint("abc")` returns 0, no error. Add explicit validation that billable is in {0, 1} after cint conversion. If input is non-numeric string, throw a clear ValidationError.

2. **No unit tests for the cint() fix** — Add tests for `add_entry(duration_minutes="abc")` and `stop_timer(billable="xyz")` to prove non-numeric inputs produce graceful errors (not 500s). This is the core regression test for the int()->cint() change.

3. **duration_minutes not cross-validated against started_at** — In stop_timer(), add a sanity check: `duration_minutes <= (now - started_at).total_seconds() / 60 + tolerance`. Prevents billing fraud where agent claims 24h but timer ran 5min.

### Also fix (P2)
4. **delete_entry info leak** — Move `is_agent()` check before `frappe.get_doc()` in delete_entry.
5. **cint produces misleading error** — Before cint(), check if the raw string is numeric; if not, throw "duration_minutes must be a valid integer".

### Files to modify
- `helpdesk/api/time_tracking.py` (dev + bench)
- `helpdesk/helpdesk/doctype/hd_time_entry/test_hd_time_entry.py` (dev + bench)

### Test verification
- Run: `cd /home/ubuntu/frappe-bench && bench --site helpdesk.localhost run-tests --app helpdesk --module helpdesk.helpdesk.doctype.hd_time_entry.test_hd_time_entry`
- All existing + new tests must pass

## Acceptance Criteria

- [ ] **billable silently coerced to 0** — `cint("abc")` returns 0, no error. Add explicit validation that billable is in {0, 1} after cint conversion. If input is non-numeric string, throw a clear ValidationError.
- [ ] **No unit tests for the cint() fix** — Add tests for `add_entry(duration_minutes="abc")` and `stop_timer(billable="xyz")` to prove non-numeric inputs produce graceful errors (not 500s). This is the core regression test for the int()->cint() change.
- [ ] **duration_minutes not cross-validated against started_at** — In stop_timer(), add a sanity check: `duration_minutes <= (now - started_at).total_seconds() / 60 + tolerance`. Prevents billing fraud where agent claims 24h but timer ran 5min.
- [ ] **delete_entry info leak** — Move `is_agent()` check before `frappe.get_doc()` in delete_entry.
- [ ] **cint produces misleading error** — Before cint(), check if the raw string is numeric; if not, throw "duration_minutes must be a valid integer".

## Tasks / Subtasks

- [ ] **billable silently coerced to 0** — `cint("abc")` returns 0, no error. Add explicit validation that billable is in {0, 1} after cint conversion. If input is non-numeric string, throw a clear ValidationError.
- [ ] **No unit tests for the cint() fix** — Add tests for `add_entry(duration_minutes="abc")` and `stop_timer(billable="xyz")` to prove non-numeric inputs produce graceful errors (not 500s). This is the core regression test for the int()->cint() change.
- [ ] **duration_minutes not cross-validated against started_at** — In stop_timer(), add a sanity check: `duration_minutes <= (now - started_at).total_seconds() / 60 + tolerance`. Prevents billing fraud where agent claims 24h but timer ran 5min.
- [ ] **delete_entry info leak** — Move `is_agent()` check before `frappe.get_doc()` in delete_entry.
- [ ] **cint produces misleading error** — Before cint(), check if the raw string is numeric; if not, throw "duration_minutes must be a valid integer".

## Dev Notes



### References

- Task source: Claude Code Studio task #102

## Dev Agent Record

### Agent Model Used

sonnet

### Completion Notes List

_(Updated by agent on completion)_

### Change Log

_(Updated by agent during implementation)_

### File List

_(Updated by agent — list all files created or modified)_
