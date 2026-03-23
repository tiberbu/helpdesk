# Story: QA: Story 1.9: Incident Models / Templates

Status: done
Task ID: mn39hzqiuq25qf
Task Number: #61
Workflow: adversarial-review
Model: opus
Created: 2026-03-23T14:09:18.908Z

## Description

## QA Report Task -- DO NOT MODIFY CODE

**Review task #25: Story 1.9: Incident Models / Templates**

### What to verify
Read the story file for acceptance criteria: `_bmad-output/implementation-artifacts/story-25-story-1-9-incident-models-templates.md`
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
Produce `docs/qa-report-task-25.md` with:
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

Adversarial review completed. 12 issues found (2 P1, 6 P2, 4 P3). Fix task created for P1/P2 issues.

### References

- Task source: Claude Code Studio task #61
- QA Report: `docs/qa-report-task-25.md`

## Dev Agent Record

### Agent Model Used

opus

### Completion Notes List

**Completed:** 2026-03-23

Adversarial QA review of Story 1.9: Incident Models / Templates.

**Findings:** 12 issues total (0 P0, 2 P1, 6 P2, 4 P3)

Key P1 issues:
1. Missing `__` translation import in TicketDetailsTab.vue -- causes ReferenceError at runtime
2. Client-side resolution guard misses "Duplicate" status (server-side catches it, but UX is broken)

Key P2 issues:
3. No ITIL feature flag gating
4. Priority field type mismatch (Select vs Link)
5. No is_agent() check -- customers can toggle checklist items
6. Auto-close bypasses checklist validation
7. Test data leaks due to explicit frappe.db.commit()
8. Fixture child entries missing doctype key

Fix task created via API.

### Change Log

- Created `docs/qa-report-task-25.md` -- full QA report with 12 findings

### File List

- `docs/qa-report-task-25.md` (created)
