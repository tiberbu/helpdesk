# Story: Fix: delete_entry regression (P0) + cint silent conversion (P1) from QA task #97

Status: in-progress
Task ID: mn3c3ejvy6ufzm
Task Number: #104
Workflow: quick-dev
Model: sonnet
Created: 2026-03-23T15:22:10.187Z

## Description

## Fix P0 and P1 issues from adversarial review task #97 (docs/qa-report-task-93.md)

### P0-1: delete_entry regression — HD Admin blocked by is_agent() gate
The delete_entry() API pre-gates with `if not is_agent(): frappe.throw(...)` which blocks HD Admin users who are NOT also agents. The prior version had `if not is_agent() and not is_privileged:` which allowed privileged non-agent users through. Task #93 removed this, causing test_delete_entry_admin_can_delete_any_entry to FAIL.

**Fix:** Restore the privileged-role check in the is_agent gate:
```python
user_roles = set(frappe.get_roles(frappe.session.user))
is_privileged = bool(user_roles & PRIVILEGED_ROLES)
if not is_agent() and not is_privileged:
    frappe.throw(_("Not permitted"), frappe.PermissionError)
```

### P1-1: cint() silently converts garbage to 0 — misleading errors
cint("abc") returns 0, then "Duration must be at least 1 minute" fires instead of "invalid integer". Use try/except int() with clear error message for duration_minutes; keep cint() only for billable boolean.

### P2-1: billable not clamped to 0/1
cint(billable) can store values >1 in Check field. Clamp to `1 if cint(billable) else 0`.

### P2-3: No test for MAX_DURATION_MINUTES at API layer
Add tests for stop_timer and add_entry with duration > MAX_DURATION_MINUTES.

### Files to modify
- helpdesk/api/time_tracking.py (fix is_agent gate, int validation, billable clamping)
- test_hd_time_entry.py (add API-layer max duration tests)
- Sync to bench + reload gunicorn

### Verification
- All 32 tests must pass (currently 31 pass, 1 fails)
- New tests for API-layer max duration
- Confirm HD Admin user can delete entries

## Acceptance Criteria

- [ ] Implementation matches task description
- [ ] No regressions introduced
- [ ] Code compiles/builds without errors

## Tasks / Subtasks

- [ ] Implement changes
- [ ] Verify build passes

## Dev Notes



### References

- Task source: Claude Code Studio task #104

## Dev Agent Record

### Agent Model Used

sonnet

### Completion Notes List

_(Updated by agent on completion)_

### Change Log

_(Updated by agent during implementation)_

### File List

_(Updated by agent — list all files created or modified)_
