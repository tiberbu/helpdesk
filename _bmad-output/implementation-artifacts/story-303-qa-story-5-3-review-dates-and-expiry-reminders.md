# Story: QA: Story 5.3: Review Dates and Expiry Reminders

Status: done
Task ID: mn4ifdkwtcrxd5
Task Number: #303
Workflow: playwright-qa
Model: opus
Created: 2026-03-24T11:13:19.338Z

## Description

## QA Report Task — DO NOT MODIFY CODE

**Review task #44: Story 5.3: Review Dates and Expiry Reminders**
**QA Depth: 1/1** (max depth reached = no further QA cycles)

### MANDATORY: Use Playwright MCP for ALL browser testing
You have access to Playwright MCP tools. You MUST use them. The tools are prefixed with `mcp__playwright__`.

**Available Playwright MCP tools (use these exact names):**
- `mcp__playwright__browser_navigate` — navigate to a URL
- `mcp__playwright__browser_click` — click an element
- `mcp__playwright__browser_type` — type into an input
- `mcp__playwright__browser_screenshot` — take a screenshot
- `mcp__playwright__browser_snapshot` — get accessibility snapshot of page
- `mcp__playwright__browser_wait` — wait for element/time

**If you skip Playwright testing, the task will be considered FAILED.**

Start by navigating to the app: `mcp__playwright__browser_navigate` with url `http://help.frappe.local`
Then login with credentials from docs/testing-info.md (or use: Administrator / admin)

### What to verify
Read the story file for acceptance criteria: `_bmad-output/implementation-artifacts/story-44-story-5-3-review-dates-and-expiry-reminders.md`

### Files changed
(check git diff for changes)

### Test steps
1. Use `mcp__playwright__browser_navigate` to go to http://help.frappe.local
2. Login using Playwright tools (navigate to login, type credentials, click login)
3. Navigate to the relevant pages for this feature
4. Test each acceptance criterion using Playwright interactions
5. Take screenshots: `mcp__playwright__browser_screenshot`
6. Check console for errors
3. Test each acceptance criterion from the story file
4. Check for regressions in related functionality
5. Verify no console errors

### Deliverable
Produce `docs/qa-report-task-44.md` with:
- Each AC: PASS/FAIL with evidence
- Screenshots referenced (use task-prefixed naming)
- Console errors captured
- Severity ratings (P0-P3) for any failures

### Creating fix tasks (STRICT RULES)
If you find P0 or P1 failures, you MUST create ONE consolidated fix task.
Rules for the fix task:
1. **ONE task only** — consolidate all findings into a single fix task
2. **Atomic scope** — only fix what this QA found, nothing else
3. **Exact file paths + line numbers** for every issue
4. **Before/after code snippets** showing exactly what to change
5. **Verification command** for each fix (e.g. grep, curl, test command)
6. **Done criteria checklist** — each item must be independently verifiable
7. Title format: "Fix: [parent story title] — [issue summary]"

Create the fix task using:
```
curl -b /tmp/ccs.cookie -X POST http://localhost:3000/api/tasks -H "Content-Type: application/json" -d @- <<'TASK_JSON'
{
  "title": "Fix: [story title] — [1-line summary of all issues]",
  "description": "## Fix Task (from QA report docs/qa-report-task-44.md)\n\n### SCOPE LOCK\nYou MUST only modify the files listed below. Any change outside this scope = failure.\n\n### Issues to fix\n#### Issue 1: [title]\n- File: [exact path]\n- Line: [number]\n- Current: `[code snippet]`\n- Expected: `[code snippet]`\n- Verify: `[command that proves fix works]`\n\n#### Issue 2: ...\n\n### Done Checklist (ALL must pass)\n- [ ] Issue 1 fixed — verify with: [command]\n- [ ] Issue 2 fixed — verify with: [command]\n- [ ] No files modified outside scope\n- [ ] `git diff --stat` shows only expected files\n- [ ] App builds without errors: [build command]\n- [ ] No console errors on affected pages\n\n### MANDATORY COMPLETION GATE\nBefore marking done, run EVERY verify command above. If ANY fails, fix it. Do not skip.",
  "workdir": "/home/ubuntu/bmad-project/helpdesk",
  "status": "bmad_workflow",
  "notes": "[bmad-workflow:quick-dev]",
  "model": "sonnet",
  "max_turns": 60,
  "chain_id": "epic-5-knowledge-base"
}
TASK_JSON
```

**CRITICAL: Do NOT create more than ONE fix task. Do NOT create fix tasks for P2/P3 issues.**

## Acceptance Criteria

- [x] Use `mcp__playwright__browser_navigate` to go to http://help.frappe.local
- [x] Login using Playwright tools (navigate to login, type credentials, click login)
- [x] Navigate to the relevant pages for this feature
- [x] Test each acceptance criterion using Playwright interactions
- [x] Take screenshots: `mcp__playwright__browser_screenshot`
- [x] Check console for errors
- [x] Test each acceptance criterion from the story file
- [x] Check for regressions in related functionality
- [x] Verify no console errors (found P1 toast bug)
- [x] **ONE task only** — consolidate all findings into a single fix task (#305)
- [x] **Atomic scope** — only fix what this QA found, nothing else
- [x] **Exact file paths + line numbers** for every issue
- [x] **Before/after code snippets** showing exactly what to change
- [x] **Verification command** for each fix (e.g. grep, curl, test command)
- [x] **Done criteria checklist** — each item must be independently verifiable
- [x] Title format: "Fix: [parent story title] — [issue summary]"

## Tasks / Subtasks

- [x] Use `mcp__playwright__browser_navigate` to go to http://help.frappe.local
- [x] Login using Playwright tools (navigate to login, type credentials, click login)
- [x] Navigate to the relevant pages for this feature
- [x] Test each acceptance criterion using Playwright interactions
- [x] Take screenshots: `mcp__playwright__browser_screenshot`
- [x] Check console for errors
- [x] Test each acceptance criterion from the story file
- [x] Check for regressions in related functionality
- [x] Verify no console errors (found P1 toast bug)
- [x] **ONE task only** — consolidate all findings into a single fix task (#305)
- [x] **Atomic scope** — only fix what this QA found, nothing else
- [x] **Exact file paths + line numbers** for every issue
- [x] **Before/after code snippets** showing exactly what to change
- [x] **Verification command** for each fix (e.g. grep, curl, test command)
- [x] **Done criteria checklist** — each item must be independently verifiable
- [x] Title format: "Fix: [parent story title] — [issue summary]"

## Dev Notes



### References

- Task source: Claude Code Studio task #303

## Dev Agent Record

### Agent Model Used

opus

### Completion Notes List

- QA complete. All 3 ACs PASS. 29/29 unit tests pass.
- Found P1 bug: `toast()` called as function instead of `toast.create()` in 4 locations across 2 Vue components. Causes TypeError and missing user feedback toasts.
- Fix task #305 created with exact file paths, line numbers, before/after code, and verification commands.

### Change Log

- 2026-03-24: Full QA complete. Report at `docs/qa-report-task-44.md`. Fix task #305 created for P1 toast bug.

### File List

- `docs/qa-report-task-44.md` — QA report (updated from prior QA run)
- `task-44-review-widget-both-sections.png` — Screenshot: widget with overdue + upcoming sections
- `task-44-dashboard-full.png` — Screenshot: full dashboard with widget
- `task-44-dashboard-review-widget.png` — Screenshot: widget close-up
- `task-44-hd-settings-review-period.png` — Screenshot: HD Settings review period config
