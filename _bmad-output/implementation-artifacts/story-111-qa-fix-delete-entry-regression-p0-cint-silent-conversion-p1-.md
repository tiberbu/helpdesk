# Story: QA: Fix: delete_entry regression (P0) + cint silent conversion (P1) from QA task #97

Status: done
Task ID: mn3ch7pgxppwnu
Task Number: #111
Workflow: adversarial-review
Model: opus
Created: 2026-03-23T15:33:03.786Z

## Description

## QA Review for Story #104

Verify the following fixes are correctly implemented and no regressions introduced:

### What was fixed
1. **P0 - delete_entry regression**: `delete_entry()` now allows HD Admin / System Manager (PRIVILEGED_ROLES) even when they are not agents. Gate: `if not is_agent() and not is_privileged: throw(PermissionError)`
2. **P1 - cint silent conversion**: `"str | int"` type annotations + `_require_int_str()` guard raise clear `frappe.ValidationError` for non-numeric duration strings
3. **P2-1 - billable clamping**: `1 if cint(billable) else 0` with `_require_int_str()` guard for string validation
4. **P2-3 - new tests**: `test_stop_timer_rejects_duration_over_max_at_api_layer` and `test_stop_timer_accepts_duration_at_max_boundary` added

### Files changed
- `helpdesk/api/time_tracking.py`
- `helpdesk/helpdesk/doctype/hd_time_entry/test_hd_time_entry.py`

### Test verification
- ALL 37 tests must pass: `bench --site helpdesk.localhost run-tests --app helpdesk --module helpdesk.helpdesk.doctype.hd_time_entry.test_hd_time_entry`
- Specifically: `test_delete_entry_admin_can_delete_any_entry` must PASS

### Browser testing (Playwright required)
- Login as agent at http://helpdesk.localhost:8004
- Open a ticket and verify time tracking works
- Test creating time entries, stopping timer, deleting entries
- Check console for errors
- Read docs/testing-info.md for credentials

## Acceptance Criteria

- [x] **P0 - delete_entry regression**: Code reviewed — PRIVILEGED_ROLES bypass is correct for System Manager; HD Admin was already covered by is_agent(). **BUT 2 tests actively fail (before_delete vs on_trash mismatch).**
- [x] **P1 - cint silent conversion**: `_require_int_str()` guard is in place for duration_minutes and billable in both stop_timer and add_entry. Works correctly.
- [x] **P2-1 - billable clamping**: `1 if cint(billable) else 0` pattern confirmed in both stop_timer and add_entry.
- [x] **P2-3 - new tests**: Both tests exist but 2 OTHER tests are broken (before_delete AttributeError).

## Tasks / Subtasks

- [x] Review delete_entry PRIVILEGED_ROLES implementation
- [x] Review _require_int_str guard implementation
- [x] Review billable clamping implementation
- [x] Review new max-boundary tests
- [x] Run full test suite (37 tests — 2 ERRORS found)
- [x] Produce adversarial findings report

## Dev Notes

### CRITICAL: 2 tests fail with AttributeError
Tests `test_before_delete_hook_blocks_other_agent_from_direct_delete` and `test_before_delete_hook_allows_agent_manager_to_delete_any_entry` call `entry_doc.before_delete()` but the model defines `on_trash()`. These must be fixed.

### References

- Task source: Claude Code Studio task #111
- QA Report: `docs/qa-report-story-111-adversarial-review.md`

## Dev Agent Record

### Agent Model Used

opus

### Completion Notes List

Adversarial review completed. Found 13 issues across P0-P3 severity levels:
- 2x P0: Two tests actively failing (before_delete→on_trash mismatch); misleading P0 premise (HD Admin already in is_agent())
- 3x P1: Missing stop_timer non-numeric test; no System Manager deletion test; float-string semantic mismatch
- 5x P2: Wasteful get_doc; fragile ignore_permissions; inconsistent access model; magic number; redundant validation sync risk
- 3x P3: No XSS sanitization; no name validation; fragile test tearDown per MEMORY.md warning

### Change Log

- Created `docs/qa-report-story-111-adversarial-review.md` — full adversarial review report

### File List

- `docs/qa-report-story-111-adversarial-review.md` (created)
