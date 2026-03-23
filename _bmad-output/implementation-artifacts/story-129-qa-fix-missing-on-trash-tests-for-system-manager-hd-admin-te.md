# Story: QA: Fix: Missing on_trash tests for System Manager/HD Admin + test naming inconsiste

Status: done
Task ID: mn3d1clbbqzdc5
Task Number: #129
Workflow: adversarial-review
Model: opus
Created: 2026-03-23T15:48:20.881Z

## Description

## QA Report Task — DO NOT MODIFY CODE

**Review task #126: Fix: Missing on_trash tests for System Manager/HD Admin + test naming inconsistency (P1/P2 from QA #118)**

### What to verify
Read the story file for acceptance criteria: `_bmad-output/implementation-artifacts/story-126-fix-missing-on-trash-tests-for-system-manager-hd-admin-test-.md`
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
Produce `docs/qa-report-task-126.md` with:
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

This is a backend-only task (test file changes). No frontend/UI to test via Playwright. All verification was done via:
1. Running the full test suite (58/58 pass)
2. Reviewing git diff and commit history
3. Comparing dev and bench copies (zero diff)
4. Reading the actual code changes against the AC

### References

- Task source: Claude Code Studio task #129

## Dev Agent Record

### Agent Model Used

opus

### Completion Notes List

- Adversarial QA review completed for task #126
- All 6 acceptance criteria PASS (new tests exist, renames done, anti-pattern removed, tests pass, bench synced)
- 14 findings identified: 2 P1, 7 P2, 5 P3
- P1-1: Task #126 commit contains zero code changes (process/audit trail issue)
- P1-2: `_require_int_str` still doesn't handle "inf"/"infinity" strings (500 error from user input, flagged in 2 consecutive QA reports)
- QA report written to `docs/qa-report-task-126.md`
- Fix task created for P1 findings

### Change Log

- Created `docs/qa-report-task-126.md` (adversarial QA report)

### File List

- `docs/qa-report-task-126.md` (created)
