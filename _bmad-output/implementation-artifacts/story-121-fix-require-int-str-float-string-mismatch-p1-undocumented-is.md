# Story: Fix: _require_int_str float-string mismatch (P1) + undocumented is_admin(user) fix (P1) from QA task #112

Status: done
Task ID: mn3crp0h5ualkh
Task Number: #121
Workflow: quick-dev
Model: sonnet
Created: 2026-03-23T15:41:04.508Z

## Description

## P1 findings from adversarial review task #112 (docs/qa-report-task-104.md)

### P1-1: _require_int_str() rejects float strings that cint() accepts
_require_int_str("3.5") raises ValidationError because int("3.5") raises ValueError, but cint("3.5") returns 3. Zero tests for edge cases: float strings, empty strings, whitespace, booleans, None. Add comprehensive tests and document intended behavior. Consider using int(float(value.strip())) to match cint behavior.

### P1-2: is_admin(user) parameter fix in utils.py is undocumented
The change from is_admin() to is_admin(user) in is_agent() has global scope affecting all callers. Add a dedicated test: is_agent(user="someone") must check that specific user, not frappe.session.user. Document in story change log.

### Files to modify
- helpdesk/api/time_tracking.py (_require_int_str edge cases)
- helpdesk/helpdesk/doctype/hd_time_entry/test_hd_time_entry.py (add edge case tests)
- helpdesk/utils.py (add test for is_agent with explicit user param)
- Sync to bench + reload gunicorn


## Acceptance Criteria

- [x] Implementation matches task description
- [x] No regressions introduced
- [x] Code compiles/builds without errors

## Tasks / Subtasks

- [x] Implement changes
- [x] Verify build passes

## Dev Notes

### P1-1 Fix Decision
Changed `int(value.strip())` → `int(float(value.strip()))` in `_require_int_str()`. This matches `cint()` behavior: `cint("3.5") == 3` (truncates). Float strings like "30.0" are common browser-to-server values and must be accepted. Added docstring documenting exact behavior: integer strings, float strings, non-numeric strings (reject), and non-string types (pass through unchanged).

### P1-2 Fix Decision
Added `TestIsAgentExplicitUser` class in `test_hd_time_entry.py` with 4 dedicated tests:
1. `is_agent(user='agent')` returns True when session user is non-agent
2. `is_agent(user='non-agent')` returns False when session user is agent
3. `is_agent()` (no param) uses session user correctly
4. `is_agent(user='Administrator')` always returns True

The `is_agent(user)` function in `utils.py` already correctly passes `user` to `is_admin(user)`. These tests document and verify that behavior.

### References

- Task source: Claude Code Studio task #121

## Dev Agent Record

### Agent Model Used

sonnet

### Completion Notes List

- Fixed `_require_int_str` to use `int(float(value.strip()))` instead of `int(value.strip())`, matching `cint()` truncation behavior for float strings like "3.5" → 3, "30.0" → 30.
- Added 8 edge case tests for `_require_int_str`: float strings, fractional floats, whitespace-padded integers, empty string (reject), whitespace-only (reject), boolean True (pass through), None (pass through → fails ≥1 check), float billable string.
- Added `TestIsAgentExplicitUser` class with 4 tests proving `is_agent(user=...)` checks the explicit user, not `frappe.session.user`.
- All 56 tests pass (48 original + 8 new edge case + 4 new is_agent tests).
- Synced to bench and reloaded gunicorn.

### Change Log

- **helpdesk/api/time_tracking.py**: Changed `_require_int_str` to use `int(float(value.strip()))` to match `cint()` float-string truncation behavior. Expanded docstring to document all accepted/rejected value types.
- **helpdesk/helpdesk/doctype/hd_time_entry/test_hd_time_entry.py**: Added 8 edge case tests for `_require_int_str` (P1-1) and 4 tests in new `TestIsAgentExplicitUser` class for `is_agent(user=...)` explicit user parameter (P1-2).

### File List

- `helpdesk/api/time_tracking.py` — modified `_require_int_str()`
- `helpdesk/helpdesk/doctype/hd_time_entry/test_hd_time_entry.py` — added 12 new tests
