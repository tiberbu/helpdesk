# Story: QA: Fix: P1s from adversarial review task-84 — deduplicate privileged_roles, fix tz

Status: done
Task ID: mn3bmr76vjpc1n
Task Number: #90
Workflow: adversarial-review
Model: opus
Created: 2026-03-23T15:11:29.731Z

## Description

## QA Report Task — DO NOT MODIFY CODE

**Review task #87: Fix: P1s from adversarial review task-84 — deduplicate privileged_roles, fix tz API misuse, remove redundant API desc check, frontend canDelete Agent Manager**

### What to verify
Read the story file for acceptance criteria: `_bmad-output/implementation-artifacts/story-87-fix-p1s-from-adversarial-review-task-84-deduplicate-privileg.md`
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
Produce `docs/qa-report-task-87.md` with:
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

- Task source: Claude Code Studio task #90

## Dev Agent Record

### Agent Model Used

opus

### Completion Notes List

- Adversarial review completed: 13 findings (2 P1, 7 P2, 4 P3)
- P1: delete_entry() still has duplicated permission logic despite dedup goal; close_tickets_after_n_days() can crash entire cron on single ticket
- P2: Bench frontend not synced, missing __ import, astimezone uses process tz not Frappe tz, misleading comment, lifecycle ordering issue, mutable PRIVILEGED_ROLES set, no tz regression test
- Report produced at docs/qa-report-task-87.md
- Fix task created for P1 issues

### Change Log

- 2026-03-23: Completed adversarial review, produced QA report with 13 findings

### File List

- `docs/qa-report-task-87.md` — adversarial review report (created)
