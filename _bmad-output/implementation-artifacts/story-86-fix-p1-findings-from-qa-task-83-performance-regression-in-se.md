# Story: Fix: P1 findings from QA task-83 — performance regression in set_status_category, Closed category bypass in checklist guard

Status: done
Task ID: mn3bhqpf1gaegm
Task Number: #86
Workflow: quick-dev
Model: sonnet
Created: 2026-03-23T15:05:16.859Z

## Description

## P1 Findings from Adversarial Review (docs/qa-report-task-81.md)

### F-01 [P1] — set_status_category() unconditional re-derivation is a performance regression
The has_value_changed guard was completely removed, meaning every ticket.save() now executes a DB query to look up status_category even when status has not changed. The correct fix should re-derive when status changed but validate the match when it did not, preserving the fast path.

### F-02 [P1] — validate_checklist_before_resolution() only checks Resolved, not Closed; auto-close scheduler bypasses validation
Line 104: `if self.status_category not in ("Resolved",):` does not include "Closed". The docstring claims to prevent resolution/closure. Additionally, close_tickets_after_n_days() sets ignore_validate=True which bypasses the guard entirely.

### Also fix (P2):
- F-03: HD Ticket Status records created in tests never cleaned up in tearDown
- F-04: Exception matching by English substring in migration is fragile
- F-05: Stale status_category silently preserved when HD Ticket Status record is deleted

### Files to modify:
- helpdesk/helpdesk/doctype/hd_ticket/hd_ticket.py (F-01: restore optimized guard with validation; F-02: add Closed to checklist guard)
- helpdesk/helpdesk/doctype/hd_ticket/test_incident_model.py (F-03: cleanup HD Ticket Status records in tearDown)
- helpdesk/patches/v1_phase1/reload_incident_model_for_link_field.py (F-04: use numeric error code instead of string match)

## Acceptance Criteria

- [x] Implementation matches task description
- [x] No regressions introduced
- [x] Code compiles/builds without errors

## Tasks / Subtasks

- [x] Implement changes
- [x] Verify build passes

## Dev Notes



### References

- Task source: Claude Code Studio task #86

## Dev Agent Record

### Agent Model Used

sonnet

### Completion Notes List

- F-01: Restored fast path in `set_status_category()` — skips DB query when status is unchanged and `status_category` is already set. Re-derives only when status changed or category is missing. Added F-05 fix: clears stale `status_category` when the referenced HD Ticket Status record has been deleted.
- F-02: Added `"Closed"` to the checklist guard in `validate_checklist_before_resolution()`. Removed `ignore_validate=True` from `close_tickets_after_n_days()` so the auto-close scheduler no longer bypasses validation.
- F-03: Added `_pre_existing_statuses` snapshot in `setUp`; `tearDown` now explicitly deletes any `_TEST_STATUS_NAMES` records that were created by the test (guards against `db.rollback()` no-ops after mid-test commits).
- F-04: Replaced fragile English-substring exception matching in the migration patch with numeric MySQL/MariaDB error code check (`e.args[0] == 1146`).
- All 17 `test_incident_model` tests pass; 10 `test_internal_notes` tests pass; no regressions.

### Change Log

- 2026-03-23: F-01 — restored fast path + F-05 stale category clear in `set_status_category()`
- 2026-03-23: F-02 — added "Closed" to checklist guard; removed `ignore_validate=True` from auto-close scheduler
- 2026-03-23: F-03 — added setUp snapshot + tearDown cleanup for HD Ticket Status records in `test_incident_model.py`
- 2026-03-23: F-04 — numeric error code check in migration patch

### File List

- `helpdesk/helpdesk/doctype/hd_ticket/hd_ticket.py` (modified — F-01, F-02, F-05)
- `helpdesk/helpdesk/doctype/hd_ticket/test_incident_model.py` (modified — F-03)
- `helpdesk/patches/v1_phase1/reload_incident_model_for_link_field.py` (modified — F-04)
- (All three also synced to `/home/ubuntu/frappe-bench/apps/helpdesk/`)
