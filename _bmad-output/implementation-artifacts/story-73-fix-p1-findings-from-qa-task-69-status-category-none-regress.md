# Story: Fix: P1 findings from QA task-69 — status_category None regression, missing bypass test, migration hardening

Status: in-progress
Task ID: mn3ata28e6ihmx
Task Number: #73
Workflow: quick-dev
Model: sonnet
Created: 2026-03-23T14:46:16.827Z

## Description

## P1 Findings from Adversarial Review (docs/qa-report-task-68.md)

### F-01 [P1] — set_status_category() now sets None for invalid/empty statuses

The fix removed the `or` short-circuit but introduced a regression: when self.status is None, empty, or references a deleted HD Ticket Status record, frappe.get_value() returns None, and status_category is silently wiped. The correct fix should check `self.has_value_changed("status") or not self.status_category` before re-deriving, or fall back to existing value when frappe.get_value returns None.

### F-02 [P1] — No test for the exact stale status_category bypass scenario

The core P1 fix has zero automated regression protection. Need a test that: (1) saves a ticket as Replied (category Paused), (2) changes status to Resolved, (3) verifies status_category updates to Resolved (not stale Paused).

### Also fix (P2):
- F-03: Add frappe.db.commit() to migration patch
- F-04: Add try/except for tabHD Ticket Priority table existence in migration
- F-05: Reload HD Incident Checklist Item child doctype in migration
- F-06: Clean up test user in permission test tearDown
- F-07: Add permission test for complete_checklist_item (not just apply_incident_model)

### Files to modify:
- helpdesk/helpdesk/doctype/hd_ticket/hd_ticket.py (set_status_category defensive fix)
- helpdesk/patches/v1_phase1/reload_incident_model_for_link_field.py (hardening)
- helpdesk/helpdesk/doctype/hd_ticket/test_incident_model.py (add bypass test + complete_checklist_item tests)

## Acceptance Criteria

- [ ] Implementation matches task description
- [ ] No regressions introduced
- [ ] Code compiles/builds without errors

## Tasks / Subtasks

- [ ] Implement changes
- [ ] Verify build passes

## Dev Notes



### References

- Task source: Claude Code Studio task #73

## Dev Agent Record

### Agent Model Used

sonnet

### Completion Notes List

_(Updated by agent on completion)_

### Change Log

_(Updated by agent during implementation)_

### File List

_(Updated by agent — list all files created or modified)_
