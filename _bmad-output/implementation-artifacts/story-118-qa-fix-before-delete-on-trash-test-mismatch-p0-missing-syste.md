# Story: QA: Fix: before_delete->on_trash test mismatch (P0) + missing System Manager/stop_tim

Status: done
Task ID: mn3coweqch25n7
Task Number: #118
Workflow: adversarial-review
Model: opus
Created: 2026-03-23T15:42:57.042Z

## Description

## QA Report Task -- DO NOT MODIFY CODE

**Review task #114: Fix: before_delete->on_trash test mismatch (P0) + missing System Manager/stop_timer tests (P1)**

### What to verify
Read the story file for acceptance criteria: `_bmad-output/implementation-artifacts/story-114-fix-before-delete-on-trash-test-mismatch-p0-missing-system-m.md`
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
Produce `docs/qa-report-task-114.md` with:
- Each AC: PASS/FAIL with evidence
- Screenshots referenced (use task-prefixed naming)
- Console errors captured
- Severity ratings (P0-P3) for any failures

### If P0/P1 issues found
Create a fix task using this exact command:
```
curl -b /tmp/ccs.cookie -X POST http://localhost:3000/api/tasks -H "Content-Type: application/json" -d '{"title":"Fix: [issue summary]","description":"[paste QA findings]","workdir":"/home/ubuntu/bmad-project/helpdesk","status":"bmad_workflow","notes":"[bmad-workflow:quick-dev]","chain_id":"mn3ch7pgxppwnu","sort_order":999}'
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

- Task source: Claude Code Studio task #118

## Dev Agent Record

### Agent Model Used

opus

### Completion Notes List

- Adversarial review completed with 12 findings (0 P0, 2 P1, 5 P2, 5 P3)
- All 56 tests pass (Ran 56 tests in 12.836s OK)
- Both ACs from task #114 verified as PASS
- Dev/bench file parity confirmed (zero diff)
- API endpoints verified via curl (add_entry, delete_entry, validation paths)
- P1 findings: missing on_trash direct-delete tests for System Manager and HD Admin
- P2 findings: test names still say "before_delete" (ironic given P0 was naming mismatch), test isolation leaks, try/except anti-pattern, _require_int_str doesn't handle "inf"/"nan"
- Fix task created for P1 issues

### Change Log

- Created `docs/qa-report-task-114.md` with full adversarial review findings

### File List

- `docs/qa-report-task-114.md` (created)
