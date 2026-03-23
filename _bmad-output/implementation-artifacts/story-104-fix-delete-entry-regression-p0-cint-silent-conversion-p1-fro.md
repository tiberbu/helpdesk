# Story: Fix: delete_entry regression (P0) + cint silent conversion (P1) from QA task #97

Status: done
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

- [x] Implementation matches task description
- [x] No regressions introduced
- [x] Code compiles/builds without errors

## Tasks / Subtasks

- [x] Implement changes
- [x] Verify build passes

## Dev Notes



### References

- Task source: Claude Code Studio task #104

## Dev Agent Record

### Agent Model Used

sonnet

### Completion Notes List

- Root cause: The bench/dev-disk had a regressed version of `time_tracking.py` (from a prior story) that lacked `PRIVILEGED_ROLES` import + check in `delete_entry()` and had incorrect `int` type annotations instead of `"str | int"`. The correct implementation was already in dev git (Story 95, commit 0ef5d9c8e) — restored that version and synced to bench.
- P0 fix: `delete_entry()` now checks `not is_agent() and not is_privileged` so HD Admin / System Manager users who aren't agents can delete entries.
- P1 fix: `"str | int"` type annotations + `_require_int_str()` guard raise clear `frappe.ValidationError` for non-numeric duration_minutes strings (e.g. "abc"), before `cint()` could silently coerce to 0.
- P2-1 fix: Billable clamped to `1 if cint(billable) else 0` with `_require_int_str()` guard for non-numeric strings.
- P2-3: Added 2 new tests: `test_stop_timer_rejects_duration_over_max_at_api_layer` and `test_stop_timer_accepts_duration_at_max_boundary`.
- Removed duplicate test `test_add_entry_rejects_invalid_string_duration` (identical to existing `test_add_entry_rejects_non_numeric_duration` from Story 102).
- All 37 tests pass (was 31 before fix, 1 failing for P0 + Story 102 tests failing from wrong type annotations).

### Change Log

- 2026-03-23: Restored Story 95 version of `time_tracking.py` (commit 0ef5d9c8e) to dev disk and bench. Added P2-3 stop_timer max-duration tests to test file. Removed duplicate test.

### File List

- `helpdesk/api/time_tracking.py` (restored correct version, synced to bench)
- `helpdesk/helpdesk/doctype/hd_time_entry/test_hd_time_entry.py` (added P2-3 stop_timer tests, removed duplicate, synced to bench)
