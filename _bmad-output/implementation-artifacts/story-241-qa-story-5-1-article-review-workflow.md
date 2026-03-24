# Story: QA: Story 5.1: Article Review Workflow

Status: done
Task ID: mn3wbxl9dj694k
Task Number: #241
Workflow: playwright-qa
Model: opus
Created: 2026-03-24T00:48:28.645Z

## Description

## QA Report Task — DO NOT MODIFY CODE

**Review task #42: Story 5.1: Article Review Workflow**
**QA Depth: 1/1** (max depth reached = no further QA cycles)

### What to verify
Read the story file for acceptance criteria: `_bmad-output/implementation-artifacts/story-42-story-5-1-article-review-workflow.md`

### Deliverable
Produce `docs/qa-report-task-42.md` with:
- Each AC: PASS/FAIL with evidence
- Screenshots referenced (use task-prefixed naming)
- Console errors captured
- Severity ratings (P0-P3) for any failures

## Acceptance Criteria

- [x] Navigate to app and login via Playwright browser
- [x] Test each acceptance criterion from the story file via Playwright
- [x] Check for regressions in related functionality
- [x] Check console/error logs for errors
- [x] No P0/P1 issues found — no fix task needed

## Tasks / Subtasks

- [x] Read story file and testing info
- [x] Login to app via Playwright MCP browser (http://help.frappe.local)
- [x] Navigate to KB and verify article list with status badges
- [x] Test AC1: Full lifecycle via UI (Draft -> In Review -> Published -> Archived)
- [x] Test AC2: Submit for Review with toast notification
- [x] Test AC3: Approve, Request Changes (with inline comment form), Reject (with confirmation dialog)
- [x] Test AC4: Portal visibility — Published articles appear, non-published hidden
- [x] Test AC5: Agent visibility — In Review articles visible in KB list
- [x] Verify status badges: Draft (orange), In Review (yellow), Published (green)
- [x] Verify reviewer feedback amber box display
- [x] Check console errors (only infrastructure-level socket.io errors, no app errors)
- [x] Run unit tests (29/29 pass)
- [x] Write QA report (docs/qa-report-task-42.md)
- [x] Take screenshots for evidence

## Dev Notes

Playwright MCP browser testing performed on http://help.frappe.local. All 5 ACs tested interactively.

Previously reported P1 email crash (from first QA pass) has been fixed:
- `frappe.sendmail` uses `delayed=True`
- API wraps `on_workflow_action` in try/except

### References

- Task source: Claude Code Studio task #241
- QA Report: docs/qa-report-task-42.md
- Previous fix task: #242 (email notification crash — now resolved)

## Dev Agent Record

### Agent Model Used

opus

### Completion Notes List

- Full Playwright browser QA testing completed for Story 5.1
- All 5 ACs PASS — no issues found
- 29/29 unit tests passing
- Full lifecycle tested in browser: Draft -> In Review -> Draft(changes) -> In Review -> Published -> Archived
- Reject workflow tested: In Review -> Archived with confirmation dialog
- Status badges verified: Draft (orange), In Review (yellow), Published (green)
- Reviewer feedback amber box verified
- No helpdesk-specific console errors
- Screenshots taken for all key states

### Change Log

| Date | Change |
|------|--------|
| 2026-03-24 | Initial QA pass — found P1 email crash, created fix task #242 |
| 2026-03-24 | Re-QA with Playwright browser testing — all ACs PASS after fix |
| 2026-03-24 | Updated QA report with browser test evidence and screenshots |

### File List

**Created/Updated:**
- `docs/qa-report-task-42.md` — Final QA report with browser test evidence
- `task-42-kb-list-in-review-badge.png` — KB list showing In Review badge
- `task-42-article-in-review-buttons.png` — Article page with Approve/Request Changes/Reject buttons
- `task-42-request-changes-form.png` — Inline reviewer comment form
- `task-42-draft-with-reviewer-feedback.png` — Draft article with amber reviewer feedback box
- `task-42-article-published-archive-btn.png` — Published article with Archive button
- `task-42-kb-list-draft-badge.png` — KB list showing Draft badge
- `task-42-kb-list-published-badge.png` — KB list showing Published badge
