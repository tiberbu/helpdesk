# Story: Fix: P2 findings from adversarial review of Story #122 fixes

Status: done
Task ID: mn3ee8i490rk11
Task Number: #164
Workflow: quick-dev
Model: sonnet
Created: 2026-03-23T16:26:41.023Z

## Description

## Fix P2 findings from QA report docs/qa-report-story-127-adversarial-review.md

### P2 Issues to fix:
1. **Finding #5**: Add test for F-02 path (b) — empty category field error message. Create test_save_raises_validation_error_when_status_has_no_category in test_incident_model.py that creates an HD Ticket Status with category="" and verifies the "exists but has no category assigned" error fires.
2. **Finding #6**: Strengthen test_save_raises_validation_error_when_status_record_deleted to use assertRaisesRegex matching "no longer exists" so it proves the custom F-02 guard fires (not just Frappe link validation).
3. **Finding #13**: Handle the edge case in set_status_category() where self.status is falsy — either set status_category to None/empty or raise an error, rather than silently preserving stale status_category.

### Files to modify:
- helpdesk/helpdesk/doctype/hd_ticket/hd_ticket.py (Finding #13)
- helpdesk/helpdesk/doctype/hd_ticket/test_incident_model.py (Findings #5, #6)

### Test verification:
- Run bench --site helpdesk.localhost run-tests --app helpdesk --module helpdesk.helpdesk.doctype.hd_ticket.test_incident_model --skip-before-tests
- All tests must pass including new ones

## Acceptance Criteria

- [x] **Finding #5**: Add test for F-02 path (b) — empty category field error message. Create test_save_raises_validation_error_when_status_has_no_category in test_incident_model.py that creates an HD Ticket Status with category="" and verifies the "exists but has no category assigned" error fires.
- [x] **Finding #6**: Strengthen test_save_raises_validation_error_when_status_record_deleted to use assertRaisesRegex matching "no longer exists" so it proves the custom F-02 guard fires (not just Frappe link validation).
- [x] **Finding #13**: Handle the edge case in set_status_category() where self.status is falsy — either set status_category to None/empty or raise an error, rather than silently preserving stale status_category.

## Tasks / Subtasks

- [x] **Finding #5**: Add test for F-02 path (b) — empty category field error message. Create test_save_raises_validation_error_when_status_has_no_category in test_incident_model.py that creates an HD Ticket Status with category="" and verifies the "exists but has no category assigned" error fires.
- [x] **Finding #6**: Strengthen test_save_raises_validation_error_when_status_record_deleted to use assertRaisesRegex matching "no longer exists" so it proves the custom F-02 guard fires (not just Frappe link validation).
- [x] **Finding #13**: Handle the edge case in set_status_category() where self.status is falsy — either set status_category to None/empty or raise an error, rather than silently preserving stale status_category.

## Dev Notes



### References

- Task source: Claude Code Studio task #164

## Dev Agent Record

### Agent Model Used

sonnet

### Completion Notes List

- All 3 P2 findings implemented and all 20 tests pass.
- **Finding #13**: When `self.status` is falsy in `set_status_category()`, we now set `self.status_category = None` before returning. This prevents stale `status_category` values from persisting when a ticket's status field is cleared.
- **Finding #6**: Used `doc.flags.ignore_links = True` to bypass Frappe's built-in link validation (which runs at `_validate_links()` before `run_before_save_methods()` in document.py). Combined with `frappe.clear_document_cache()` to evict the stale Redis cache entry, this ensures our custom F-02 guard in `set_status_category()` fires first and produces the "no longer exists" message verified by `assertRaisesRegex`.
- **Finding #5**: New test inserts a status with a valid category, then uses `frappe.db.set_value` + `frappe.clear_document_cache` to wipe the category in DB and evict the cache, so `get_cached_value` returns `None` and F-02 path (b) fires the "exists but has no category assigned" error.

### Change Log

- 2026-03-23: hd_ticket.py — added `self.status_category = None` before early return in `set_status_category()` when status is falsy (Finding #13)
- 2026-03-23: test_incident_model.py — strengthened `test_save_raises_validation_error_when_status_record_deleted` with `assertRaisesRegex`, cache clearing, and `doc.flags.ignore_links = True` (Finding #6)
- 2026-03-23: test_incident_model.py — added `test_save_raises_validation_error_when_status_has_no_category` test (Finding #5)

### File List

- `helpdesk/helpdesk/doctype/hd_ticket/hd_ticket.py` — Finding #13 fix
- `helpdesk/helpdesk/doctype/hd_ticket/test_incident_model.py` — Finding #5 new test + Finding #6 strengthened test
