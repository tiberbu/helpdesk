# Story: QA: Fix: P1 issues from QA task-71 — tz-aware crash, REST delete bypass, backend max

Status: done
Task ID: mn3b0jm4ad8kxn
Task Number: #77
Workflow: adversarial-review
Model: opus
Created: 2026-03-23T14:52:54.686Z

## Description

## QA Report Task — DO NOT MODIFY CODE

**Review task #74: Fix: P1 issues from QA task-71 — tz-aware crash, REST delete bypass, backend maxlength**

### What to verify
Read the story file for acceptance criteria: `_bmad-output/implementation-artifacts/story-74-fix-p1-issues-from-qa-task-71-tz-aware-crash-rest-delete-byp.md`
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
Produce `docs/qa-report-task-74.md` with:
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

- Task source: Claude Code Studio task #77

## Dev Agent Record

### Agent Model Used

opus

### Completion Notes List

- Adversarial review completed with 14 findings (3 P1, 5 P2, 6 P3).
- Key P1s: (a) tz offset stripping is semantically wrong for non-UTC offsets, (b) maxlength not enforced on direct REST resource creation (no validate hook or JSON constraint), (c) duplicated permission logic between API and hook invites drift.
- Report written to `docs/qa-report-task-74.md`.
- Fix task created for the 3 P1 issues.

### Change Log

- Created `docs/qa-report-task-74.md` — adversarial QA report with 14 findings.

### File List

- `docs/qa-report-task-74.md`
