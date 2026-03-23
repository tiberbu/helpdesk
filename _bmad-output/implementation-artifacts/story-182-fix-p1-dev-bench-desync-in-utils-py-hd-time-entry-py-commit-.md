# Story: Fix: P1 dev/bench desync in utils.py + hd_time_entry.py + commit-scope pollution audit

Status: in-progress
Task ID: mn3ezislsg5jss
Task Number: #182
Workflow: quick-dev
Model: sonnet
Created: 2026-03-23T16:43:06.379Z

## Description

## P1 findings from adversarial review (docs/qa-report-task-164.md)

### P1 #1: Commit-scope pollution
Commit 1aab1769d (task #164) contains undeclared changes to utils.py and hd_time_entry.py from unrelated task chains. Story-164 file list only declares hd_ticket.py and test_incident_model.py.

### P1 #2: Dev/bench desync
- utils.py DEV has ValueError enforcement for identity contract in is_agent(); BENCH has only docstring warning
- hd_time_entry.py DEV has PRIVILEGED_ROLES as explicit frozenset; BENCH has AGENT_ROLES - {Agent} derivation
- These are contradictory implementations. Reconcile to one canonical version and sync.

### Files to reconcile:
- helpdesk/utils.py (dev vs bench)
- helpdesk/helpdesk/doctype/hd_time_entry/hd_time_entry.py (dev vs bench)

### Verification:
- diff dev and bench copies — must be identical
- Run full test suite to confirm no regressions

## Acceptance Criteria

- [ ] Implementation matches task description
- [ ] No regressions introduced
- [ ] Code compiles/builds without errors

## Tasks / Subtasks

- [ ] Implement changes
- [ ] Verify build passes

## Dev Notes



### References

- Task source: Claude Code Studio task #182

## Dev Agent Record

### Agent Model Used

sonnet

### Completion Notes List

_(Updated by agent on completion)_

### Change Log

_(Updated by agent during implementation)_

### File List

_(Updated by agent — list all files created or modified)_
