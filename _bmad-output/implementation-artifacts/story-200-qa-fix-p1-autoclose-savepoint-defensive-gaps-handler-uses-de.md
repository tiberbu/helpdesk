# Story: QA: Fix: P1 _autoclose_savepoint defensive gaps — handler uses dead DB + Error Log l

Status: in-progress
Task ID: mn3fodx7nh4900
Task Number: #200
Workflow: adversarial-review
Model: opus
Created: 2026-03-23T17:02:14.933Z

## Description

## QA Report Task — DO NOT MODIFY CODE

**Review task #198: Fix: P1 _autoclose_savepoint defensive gaps — handler uses dead DB + Error Log lost in savepoint scope + missing multi-ticket OperationalError test**

### What to verify
Read the story file for acceptance criteria: `_bmad-output/implementation-artifacts/story-198-fix-p1-autoclose-savepoint-defensive-gaps-handler-uses-dead-.md`
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
Produce `docs/qa-report-task-198.md` with:
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

- [ ] Login to the app (see docs/testing-info.md for credentials)
- [ ] Navigate to the relevant pages
- [ ] Test each acceptance criterion from the story file
- [ ] Check for regressions in related functionality
- [ ] Verify no console errors

## Tasks / Subtasks

- [ ] Login to the app (see docs/testing-info.md for credentials)
- [ ] Navigate to the relevant pages
- [ ] Test each acceptance criterion from the story file
- [ ] Check for regressions in related functionality
- [ ] Verify no console errors

## Dev Notes



### References

- Task source: Claude Code Studio task #200

## Dev Agent Record

### Agent Model Used

opus

### Completion Notes List

_(Updated by agent on completion)_

### Change Log

_(Updated by agent during implementation)_

### File List

_(Updated by agent — list all files created or modified)_
