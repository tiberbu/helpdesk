# Story: Fix: P1s from adversarial review task-77 — tz conversion, maxlength validate hook, deduplicate delete logic

Status: done
Task ID: mn3b5jwxrp5xsp
Task Number: #79
Workflow: quick-dev
Model: sonnet
Created: 2026-03-23T14:55:46.840Z

## Description

## P1 Fixes from Adversarial Review (docs/qa-report-task-74.md)

### Issue #2 (P1): Timezone stripping is semantically wrong for non-UTC offsets
`started_at_dt.replace(tzinfo=None)` discards the offset without converting to server-local time. A client sending `2026-03-23T23:50:00+05:30` (IST) gets naive `23:50` compared against UTC server clock — incorrectly rejected as future. Fix: use `started_at_dt.astimezone(tz=None).replace(tzinfo=None)` or convert to UTC before stripping.

### Issue #3/#4 (P1): maxlength not enforced on direct REST resource creation
The 500-char `description` limit only exists in the API layer (`time_tracking.py`). Direct `POST /api/resource/HD Time Entry` bypasses it. Fix: add `if len(self.description or "") > 500: frappe.throw(...)` in `hd_time_entry.py` validate() method. Optionally add `length` to the JSON field definition.

### Issue #9 (P1): Duplicated delete permission logic invites drift
`delete_entry` API and `before_delete` hook have identical but separate ownership checks. Fix: either (a) remove ignore_permissions from delete_entry and let the hook handle it, or (b) extract a shared `_check_delete_permission(entry, user)` helper.

### Additional P2s to address if time permits
- #1: Agent Manager excluded from before_delete exemptions despite having delete:1 in JSON
- #12: Use `frappe.get_roles()` instead of querying Has Role table directly
- #13: Add upper bound on duration_minutes
- #11: Extract MAX_DESCRIPTION_LENGTH constant

## Acceptance Criteria

- [x] Implementation matches task description
- [x] No regressions introduced
- [x] Code compiles/builds without errors

## Tasks / Subtasks

- [x] Implement changes
- [x] Verify build passes

## Dev Notes



### References

- Task source: Claude Code Studio task #79

## Dev Agent Record

### Agent Model Used

sonnet

### Completion Notes List

- P1 #2: Fixed tz stripping in `stop_timer` — now uses `convert_utc_to_system_timezone()` before `replace(tzinfo=None)` so IST/non-UTC offsets are converted correctly before comparison with `now_datetime()`.
- P1 #3/#4: Added description length validation to `HDTimeEntry.validate()` using `MAX_DESCRIPTION_LENGTH` constant — direct REST `POST /api/resource/HD Time Entry` no longer bypasses the 500-char limit.
- P1 #9: Extracted `_check_delete_permission(entry, user)` module-level helper in `hd_time_entry.py`; `delete_entry` API and `before_delete` hook both delegate to it — zero logic duplication.
- P2 #1: "Agent Manager" added to privileged roles in `_check_delete_permission` and `delete_entry` (consistent with `delete:1` in DocType JSON).
- P2 #11: `MAX_DESCRIPTION_LENGTH = 500` and `MAX_DURATION_MINUTES = 1440` constants extracted to `hd_time_entry.py`; imported where needed.
- P2 #12: `frappe.get_roles()` used in both `_check_delete_permission` and `delete_entry` instead of raw `Has Role` table query.
- P2 #13: Added `duration_minutes > MAX_DURATION_MINUTES` upper-bound check in `validate()`.
- 4 new regression tests added; total suite 29 tests, all passing.

### Change Log

- `hd_time_entry.py`: Added `MAX_DESCRIPTION_LENGTH`, `MAX_DURATION_MINUTES` constants, `_check_delete_permission()` helper; extended `validate()` with description-length and upper-bound checks; simplified `before_delete()` to delegate to helper.
- `time_tracking.py`: Added import of helper + constant; updated `delete_entry` to use shared helper + `frappe.get_roles()`; used `MAX_DESCRIPTION_LENGTH` constant in description checks.
- `test_hd_time_entry.py`: Added 4 new tests covering IST-offset correctness, direct-insert description validation bypass, and duration upper/boundary bounds.

### File List

- `helpdesk/helpdesk/doctype/hd_time_entry/hd_time_entry.py` — modified
- `helpdesk/api/time_tracking.py` — modified
- `helpdesk/helpdesk/doctype/hd_time_entry/test_hd_time_entry.py` — modified
