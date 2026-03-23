# Story: Fix: P1 findings from QA task-83 — performance regression in set_status_category, Closed category bypass in checklist guard

Status: in-progress
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

- [ ] Implementation matches task description
- [ ] No regressions introduced
- [ ] Code compiles/builds without errors

## Tasks / Subtasks

- [ ] Implement changes
- [ ] Verify build passes

## Dev Notes



### References

- Task source: Claude Code Studio task #86

## Dev Agent Record

### Agent Model Used

sonnet

### Completion Notes List

_(Updated by agent on completion)_

### Change Log

_(Updated by agent during implementation)_

### File List

_(Updated by agent — list all files created or modified)_
