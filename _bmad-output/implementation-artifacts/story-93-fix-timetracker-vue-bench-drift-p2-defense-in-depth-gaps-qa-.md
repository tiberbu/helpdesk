# Story: Fix: TimeTracker.vue bench drift + P2 defense-in-depth gaps (QA task #89)

Status: done
Task ID: mn3btsuldop3q6
Task Number: #93
Workflow: quick-dev
Model: sonnet
Created: 2026-03-23T15:14:44.416Z

## Description

## Fix P1 and P2 issues from adversarial review task #89 (docs/qa-report-task-80.md)

### P1 Fix
1. **Sync TimeTracker.vue to bench** — Dev copy has `has_role("Agent Manager")` in `canDelete()` (line 348) but bench copy does not. Sync file, rebuild frontend, reload gunicorn.

### P2 Fixes
2. **Add MAX_DURATION_MINUTES check to API layer** — `stop_timer()` and `add_entry()` check `< 1` but not `> MAX_DURATION_MINUTES`. Add defense-in-depth check matching the description length pattern.
3. **Use cint() instead of int() for whitelist params** — `int(duration_minutes)` and `int(billable)` raise unhandled ValueError on non-numeric input. Use `frappe.utils.cint()` or wrap in try/except.
4. **Add :max to hours FormControl** — TimeEntryDialog.vue hours input has no upper bound. Add `:max="24"` and consider client-side validation message.

### Files to modify
- desk/src/components/ticket/TimeTracker.vue (sync to bench)
- helpdesk/api/time_tracking.py (duration upper bound + cint)
- desk/src/components/ticket/TimeEntryDialog.vue (hours max)
- Sync all to bench + rebuild

## Acceptance Criteria

- [x] **Sync TimeTracker.vue to bench** — Both dev and bench copies already had `has_role("Agent Manager")` in `canDelete()` (confirmed identical, no change needed).
- [x] **Add MAX_DURATION_MINUTES check to API layer** — Already present in both stop_timer() and add_entry() in both dev and bench copies (confirmed, no change needed).
- [x] **Use cint() instead of int() for whitelist params** — Changed `int(duration_minutes)` → `cint(duration_minutes)` and `int(billable)` → `cint(billable)` in both dev and bench time_tracking.py; added `cint` to imports. Gunicorn reloaded.
- [x] **Add :max to hours FormControl** — Already present (`:max="24"`) in TimeEntryDialog.vue in both dev and bench copies with `showMaxDurationError` validation (no change needed).

## Tasks / Subtasks

- [x] **Sync TimeTracker.vue to bench** — Both dev and bench copies already had `has_role("Agent Manager")` in `canDelete()` (confirmed identical, no change needed).
- [x] **Add MAX_DURATION_MINUTES check to API layer** — Already present in both stop_timer() and add_entry() in both dev and bench copies (confirmed, no change needed).
- [x] **Use cint() instead of int() for whitelist params** — Changed `int(duration_minutes)` → `cint(duration_minutes)` and `int(billable)` → `cint(billable)` in both dev and bench time_tracking.py; added `cint` to imports. Gunicorn reloaded.
- [x] **Add :max to hours FormControl** — Already present (`:max="24"`) in TimeEntryDialog.vue in both dev and bench copies with `showMaxDurationError` validation (no change needed).

## Dev Notes



### References

- Task source: Claude Code Studio task #93

## Dev Agent Record

### Agent Model Used

sonnet

### Completion Notes List

- P1 (TimeTracker.vue sync): Both dev and bench copies were already identical with `has_role("Agent Manager")` present. No change required.
- P2 (MAX_DURATION_MINUTES): Already implemented in time_tracking.py for both stop_timer() and add_entry() in both copies. No change required.
- P2 (cint): Applied `cint()` for `duration_minutes` and `billable` in both dev and bench time_tracking.py. Also added `cint` to imports. This prevents unhandled ValueError on non-numeric whitelist params.
- P2 (TimeEntryDialog :max="24"): Already present in both dev and bench Vue files with client-side max duration error message. No change required.
- Gunicorn reloaded after Python changes.

### Change Log

- 2026-03-23: Fixed `int()` → `cint()` in helpdesk/api/time_tracking.py (both dev and bench); confirmed all other items already in correct state.

### File List

- helpdesk/api/time_tracking.py (dev + bench) — `int()` → `cint()` for duration_minutes and billable; added cint import
