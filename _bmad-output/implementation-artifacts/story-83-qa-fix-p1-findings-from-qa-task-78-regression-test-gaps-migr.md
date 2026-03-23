# Story: QA: Fix: P1 findings from QA task-78 — regression test gaps, migration error handlin

Status: done
Task ID: mn3bc5kdkwl2wf
Task Number: #83
Workflow: adversarial-review
Model: opus
Created: 2026-03-23T15:01:12.950Z

## Description

## QA Report Task — DO NOT MODIFY CODE

**Review task #81: Fix: P1 findings from QA task-78 — regression test gaps, migration error handling, status_category trust boundary**

### What to verify
Read the story file for acceptance criteria: `_bmad-output/implementation-artifacts/story-81-fix-p1-findings-from-qa-task-78-regression-test-gaps-migrati.md`
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
Produce `docs/qa-report-task-81.md` with:
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

- Task source: Claude Code Studio task #83

## Dev Agent Record

### Agent Model Used

opus

### Completion Notes List

- Adversarial review completed with 14 findings: 2 P1, 3 P2, 9 P3
- All 17 tests verified passing via bench run-tests
- All 3 changed files confirmed synced between dev and bench copies
- F-01 (P1): Unconditional re-derivation on every save is a performance regression -- optimization removed without profiling
- F-02 (P1): validate_checklist_before_resolution() only checks "Resolved" category, not "Closed"; auto-close scheduler bypasses validation entirely with ignore_validate=True
- Full report at docs/qa-report-task-81.md

### Change Log

- `docs/qa-report-task-81.md` — created adversarial QA report with 14 findings

### File List

- `docs/qa-report-task-81.md` (created)
