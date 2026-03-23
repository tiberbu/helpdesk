# Story: Fix: P2 findings from adversarial review of Story #122 fixes

Status: in-progress
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

- [ ] **Finding #5**: Add test for F-02 path (b) — empty category field error message. Create test_save_raises_validation_error_when_status_has_no_category in test_incident_model.py that creates an HD Ticket Status with category="" and verifies the "exists but has no category assigned" error fires.
- [ ] **Finding #6**: Strengthen test_save_raises_validation_error_when_status_record_deleted to use assertRaisesRegex matching "no longer exists" so it proves the custom F-02 guard fires (not just Frappe link validation).
- [ ] **Finding #13**: Handle the edge case in set_status_category() where self.status is falsy — either set status_category to None/empty or raise an error, rather than silently preserving stale status_category.

## Tasks / Subtasks

- [ ] **Finding #5**: Add test for F-02 path (b) — empty category field error message. Create test_save_raises_validation_error_when_status_has_no_category in test_incident_model.py that creates an HD Ticket Status with category="" and verifies the "exists but has no category assigned" error fires.
- [ ] **Finding #6**: Strengthen test_save_raises_validation_error_when_status_record_deleted to use assertRaisesRegex matching "no longer exists" so it proves the custom F-02 guard fires (not just Frappe link validation).
- [ ] **Finding #13**: Handle the edge case in set_status_category() where self.status is falsy — either set status_category to None/empty or raise an error, rather than silently preserving stale status_category.

## Dev Notes



### References

- Task source: Claude Code Studio task #164

## Dev Agent Record

### Agent Model Used

sonnet

### Completion Notes List

_(Updated by agent on completion)_

### Change Log

_(Updated by agent during implementation)_

### File List

_(Updated by agent — list all files created or modified)_
