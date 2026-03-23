# Story: QA: Fix: Reverted savepoint isolation + broad except in close_tickets_after_n_days (

Status: done
Task ID: mn3e9kn0w3ze7y
Task Number: #157
Workflow: adversarial-review
Model: opus
Created: 2026-03-23T16:25:49.577Z

## Description

## QA Report Task — DO NOT MODIFY CODE

**Review task #125: Fix: Reverted savepoint isolation + broad except in close_tickets_after_n_days (P1s from QA task-116)**

### What to verify
Read the story file for acceptance criteria: `_bmad-output/implementation-artifacts/story-125-fix-reverted-savepoint-isolation-broad-except-in-close-ticke.md`
Run Playwright browser tests to verify each acceptance criterion.

### Files changed
(check git diff for changes)

### Test steps
1. Login to the app (see docs/testing-info.md for credentials)
2. Navigate to the relevant pages
3. Test each acceptance criterion from the story file
4. Check for regressions in related functionality
5. Verify no console errors

### Deliverable
Produce `docs/qa-report-task-125.md` with:
- Each AC: PASS/FAIL with evidence
- Screenshots referenced (use task-prefixed naming)
- Console errors captured
- Severity ratings (P0-P3) for any failures

### If P0/P1 issues found
Create a fix task using this exact command:
```
curl -b /tmp/ccs.cookie -X POST http://localhost:3000/api/tasks -H "Content-Type: application/json" -d '{"title":"Fix: [issue summary]","description":"[paste QA findings]","workdir":"/home/ubuntu/bmad-project/helpdesk","status":"bmad_workflow","notes":"[bmad-workflow:quick-dev]","chain_id":"epic-1-itil-incident-management","sort_order":999}'
```

## Acceptance Criteria

- [x] Login to the app (see docs/testing-info.md for credentials)
- [x] Navigate to the relevant pages
- [x] Test each acceptance criterion from the story file
- [x] Check for regressions in related functionality
- [x] Verify no console errors

## Tasks / Subtasks

- [x] Login to the app (see docs/testing-info.md for credentials)
- [x] Navigate to the relevant pages
- [x] Test each acceptance criterion from the story file
- [x] Check for regressions in related functionality
- [x] Verify no console errors

## Dev Notes



### References

- Task source: Claude Code Studio task #157

## Dev Agent Record

### Agent Model Used

opus

### Completion Notes List

- Adversarial QA review completed for task #125 (Fix: Reverted savepoint isolation + broad except)
- Found 12 issues: 1x P1, 4x P2, 6x P3
- P1: Tests deadlock with QueryDeadlockError when run via bench test runner (2 of 4 fail)
- Key P2s: redundant exception hierarchy (LinkValidationError/DoesNotExistError are subclasses of ValidationError), destructive setUp nukes all HD Tickets, no test for DoesNotExistError path
- Report written to docs/qa-report-task-125.md

### Change Log

- Created `docs/qa-report-task-125.md` — full adversarial QA report with 12 findings

### File List

- `docs/qa-report-task-125.md` (created)
