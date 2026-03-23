# Story: QA: Story 1.7 Per-Ticket Time Tracking (re-run with Playwright)

Status: in-progress
Task ID: mn38sfpzdoc88t
Task Number: #56
Workflow: adversarial-review
Model: opus
Created: 2026-03-23T13:49:31.702Z

## Description

## QA Report Task — DO NOT MODIFY CODE

**Review: Story 1.7 Per-Ticket Time Tracking**

This is a RE-RUN because the previous QA task (#55) had no Playwright or API access.

### What to verify
1. Read the story file: `_bmad-output/implementation-artifacts/story-1.7-per-ticket-time-tracking.md`
2. Read the previous QA report if it exists: `docs/qa-report-task-23.md`

### Test with Playwright MCP
You MUST use Playwright MCP tools (mcp__playwright__*) for browser testing:
1. Navigate to the helpdesk app (check docs/testing-info.md or use http://localhost:8069)
2. Login as Administrator / Velocity@2026!
3. Open a ticket
4. Test time tracking features: start/stop timer, manual entry, display
5. Take screenshots: test-screenshots/task-{TASK_ID}-01-description.png
6. Check console for errors

### Deliverable
Produce `docs/qa-report-story-1.7-time-tracking.md` with:
- Each AC: PASS/FAIL with evidence
- Screenshots
- Console errors
- Severity (P0-P3)

### If P0/P1 issues found
Create a fix task:
```
curl -b /tmp/ccs.cookie -X POST http://localhost:3000/api/tasks -H "Content-Type: application/json" -d '{"title":"Fix: Time Tracking QA Issues","description":"[paste findings]","workdir":"/home/ubuntu/bmad-project/helpdesk","status":"bmad_workflow","notes":"[bmad-workflow:quick-dev]","chain_id":"epic-1-itil-incident-management","sort_order":999}'
```

## Acceptance Criteria

- [ ] Read the story file: `_bmad-output/implementation-artifacts/story-1.7-per-ticket-time-tracking.md`
- [ ] Read the previous QA report if it exists: `docs/qa-report-task-23.md`
- [ ] Navigate to the helpdesk app (check docs/testing-info.md or use http://localhost:8069)
- [ ] Login as Administrator / Velocity@2026!
- [ ] Open a ticket
- [ ] Test time tracking features: start/stop timer, manual entry, display
- [ ] Take screenshots: test-screenshots/task-{TASK_ID}-01-description.png
- [ ] Check console for errors

## Tasks / Subtasks

- [ ] Read the story file: `_bmad-output/implementation-artifacts/story-1.7-per-ticket-time-tracking.md`
- [ ] Read the previous QA report if it exists: `docs/qa-report-task-23.md`
- [ ] Navigate to the helpdesk app (check docs/testing-info.md or use http://localhost:8069)
- [ ] Login as Administrator / Velocity@2026!
- [ ] Open a ticket
- [ ] Test time tracking features: start/stop timer, manual entry, display
- [ ] Take screenshots: test-screenshots/task-{TASK_ID}-01-description.png
- [ ] Check console for errors

## Dev Notes



### References

- Task source: Claude Code Studio task #56

## Dev Agent Record

### Agent Model Used

opus

### Completion Notes List

_(Updated by agent on completion)_

### Change Log

_(Updated by agent during implementation)_

### File List

_(Updated by agent — list all files created or modified)_
