# Story: Fix: P1 findings from adversarial review task-92 — None status_category bypass, fast-path trust gap, auto-close batch crash

Status: in-progress
Task ID: mn3by6kf7mawo1
Task Number: #99
Workflow: quick-dev
Model: sonnet
Created: 2026-03-23T15:17:52.961Z

## Description

## P1 Findings from Adversarial Review (docs/qa-report-task-92-adversarial-review.md)

### F-01 [P1] — Fast-path trust gap: manually-SET status_category is never validated on unchanged-status saves
The restored fast path (lines 1060-1065) skips the DB query when status has not changed and status_category is already set. If someone directly manipulates status_category via REST API or frappe.set_value(), the incorrect value is trusted indefinitely. Add validation: when status is unchanged, verify existing status_category matches the DB value (or at minimum, add a read-only guard on the field).

### F-02 [P1] — None status_category from F-05 fix bypasses ALL category-based validation
When an HD Ticket Status record is deleted, set_status_category() sets status_category = None. But validate_checklist_before_resolution() returns early for None (not in (Resolved, Closed) tuple), and validate_category() also skips. A ticket with None status_category bypasses all category guards. Fix: raise ValidationError when status is non-empty but status_category is None after lookup.

### Also fix (P2):
- F-03: No regression test for Closed category path in validate_checklist_before_resolution()
- F-04: close_tickets_after_n_days() needs try/except per ticket to prevent batch abort on first error
- F-07: assertRaises msg parameter misuse — switch to assertRaisesRegex

### Files to modify:
- helpdesk/helpdesk/doctype/hd_ticket/hd_ticket.py (F-01: add validation on fast path; F-02: raise on None status_category; F-04: add try/except in auto-close loop)
- helpdesk/helpdesk/doctype/hd_ticket/test_incident_model.py (F-03: add Closed path test; F-07: use assertRaisesRegex)

## Acceptance Criteria

- [ ] Implementation matches task description
- [ ] No regressions introduced
- [ ] Code compiles/builds without errors

## Tasks / Subtasks

- [ ] Implement changes
- [ ] Verify build passes

## Dev Notes



### References

- Task source: Claude Code Studio task #99

## Dev Agent Record

### Agent Model Used

sonnet

### Completion Notes List

_(Updated by agent on completion)_

### Change Log

_(Updated by agent during implementation)_

### File List

_(Updated by agent — list all files created or modified)_
