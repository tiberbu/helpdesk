# Story: QA: Fix: P1 issues in Story 1.7 Time Tracking (N+1 query, started_at validation, cus

Status: done
Task ID: mn3amzi9b5znsk
Task Number: #71
Workflow: adversarial-review
Model: opus
Created: 2026-03-23T14:41:11.517Z

## Description

## QA Report Task — DO NOT MODIFY CODE

**Review task #67: Fix: P1 issues in Story 1.7 Time Tracking (N+1 query, started_at validation, customer data exposure, pagination bug)**

### What to verify
Read the story file for acceptance criteria: `_bmad-output/implementation-artifacts/story-67-fix-p1-issues-in-story-1-7-time-tracking-n-1-query-started-a.md`
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
Produce `docs/qa-report-task-67.md` with:
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

- Task source: Claude Code Studio task #71

## Dev Agent Record

### Agent Model Used

opus

### Completion Notes List

Adversarial review complete. Produced `docs/qa-report-task-67.md` with 14 findings:
- 3 P1 issues: timezone-aware started_at crash, REST API delete bypass, no backend maxlength on description
- 8 P2 issues: no duration upper bound, canDelete frontend check, missing onError in TimeEntryDialog, billable validation, no N+1 test, admin test data leak, limit=0 DoS risk, git commit misattribution
- 3 P3 issues: agent email in response, partial HTML stored, stale localStorage
- All 14 backend tests pass
- Live API testing confirmed all P1 bugs reproducible
- Created fix task for P1 issues

### Change Log

- Created `docs/qa-report-task-67.md` — full adversarial QA report with 14 findings

### File List

- `docs/qa-report-task-67.md` (created)
