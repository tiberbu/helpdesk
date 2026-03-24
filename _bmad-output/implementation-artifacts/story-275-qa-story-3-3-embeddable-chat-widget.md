# Story: QA: Story 3.3: Embeddable Chat Widget

Status: done
Task ID: mn4c25h2ygtmnx
Task Number: #275
Workflow: playwright-qa
Model: opus
Created: 2026-03-24T08:22:04.080Z

## Description

## QA Report Task — DO NOT MODIFY CODE

**Review task #32: Story 3.3: Embeddable Chat Widget**
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
Read the story file for acceptance criteria: `_bmad-output/implementation-artifacts/story-32-story-3-3-embeddable-chat-widget.md`

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
Produce `docs/qa-report-task-32.md` with:
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
  "description": "## Fix Task (from QA report docs/qa-report-task-32.md)\n\n### SCOPE LOCK\nYou MUST only modify the files listed below. Any change outside this scope = failure.\n\n### Issues to fix\n#### Issue 1: [title]\n- File: [exact path]\n- Line: [number]\n- Current: `[code snippet]`\n- Expected: `[code snippet]`\n- Verify: `[command that proves fix works]`\n\n#### Issue 2: ...\n\n### Done Checklist (ALL must pass)\n- [ ] Issue 1 fixed — verify with: [command]\n- [ ] Issue 2 fixed — verify with: [command]\n- [ ] No files modified outside scope\n- [ ] `git diff --stat` shows only expected files\n- [ ] App builds without errors: [build command]\n- [ ] No console errors on affected pages\n\n### MANDATORY COMPLETION GATE\nBefore marking done, run EVERY verify command above. If ANY fails, fix it. Do not skip.",
  "workdir": "/home/ubuntu/bmad-project/helpdesk",
  "status": "bmad_workflow",
  "notes": "[bmad-workflow:quick-dev]",
  "model": "sonnet",
  "max_turns": 60,
  "chain_id": "epic-3-omnichannel"
}
TASK_JSON
```

**CRITICAL: Do NOT create more than ONE fix task. Do NOT create fix tasks for P2/P3 issues.**

## Acceptance Criteria

- [ ] Use `mcp__playwright__browser_navigate` to go to http://help.frappe.local
- [ ] Login using Playwright tools (navigate to login, type credentials, click login)
- [ ] Navigate to the relevant pages for this feature
- [ ] Test each acceptance criterion using Playwright interactions
- [ ] Take screenshots: `mcp__playwright__browser_screenshot`
- [ ] Check console for errors
- [ ] Test each acceptance criterion from the story file
- [ ] Check for regressions in related functionality
- [ ] Verify no console errors
- [ ] **ONE task only** — consolidate all findings into a single fix task
- [ ] **Atomic scope** — only fix what this QA found, nothing else
- [ ] **Exact file paths + line numbers** for every issue
- [ ] **Before/after code snippets** showing exactly what to change
- [ ] **Verification command** for each fix (e.g. grep, curl, test command)
- [ ] **Done criteria checklist** — each item must be independently verifiable
- [ ] Title format: "Fix: [parent story title] — [issue summary]"

## Tasks / Subtasks

- [ ] Use `mcp__playwright__browser_navigate` to go to http://help.frappe.local
- [ ] Login using Playwright tools (navigate to login, type credentials, click login)
- [ ] Navigate to the relevant pages for this feature
- [ ] Test each acceptance criterion using Playwright interactions
- [ ] Take screenshots: `mcp__playwright__browser_screenshot`
- [ ] Check console for errors
- [ ] Test each acceptance criterion from the story file
- [ ] Check for regressions in related functionality
- [ ] Verify no console errors
- [ ] **ONE task only** — consolidate all findings into a single fix task
- [ ] **Atomic scope** — only fix what this QA found, nothing else
- [ ] **Exact file paths + line numbers** for every issue
- [ ] **Before/after code snippets** showing exactly what to change
- [ ] **Verification command** for each fix (e.g. grep, curl, test command)
- [ ] **Done criteria checklist** — each item must be independently verifiable
- [ ] Title format: "Fix: [parent story title] — [issue summary]"

## Dev Notes



### References

- Task source: Claude Code Studio task #275

## Dev Agent Record

### Agent Model Used

opus

### Completion Notes List

**Completed:** 2026-03-24T08:27:14.803Z

✅ Unit tests verified: 62/62 pass across 6 test files — `cd widget && npx vitest run`
✅ Backend APIs tested: get_availability ✓, get_widget_config ✓ (curl verified)
✅ Previous P0 fixes verified: API paths now correct (`helpdesk.api.chat.*`), create_offline_ticket has Administrator elevation
🌐 Browser test: Navigated to widget test page via Playwright, confirmed widget FAILS to render — screenshot `task-32-widget-load-error.png` shows blank page with only host elements
❌ AC1 (widget loads): FAIL — P0: `ReferenceError: process is not defined` → Fix task #279 created
❌ AC2-AC5: BLOCKED by P0 (cannot test without working widget)
✅ Fix task created: Task #279 — single consolidated fix task for the P0 `process.env.NODE_ENV` issue
✅ Console errors captured: 1 critical error documented
FINAL: ⚠️ 1 P0 issue found, fix task created (task #279)
```

## Summary

**Story 3.3: Embeddable Chat Widget — FAIL (1 P0 blocker)**

The widget has solid architecture (Shadow DOM isolation, custom element, separate Vite build, good component structure, 62 passing unit tests, APIs all working correctly). However, the **production IIFE bundle crashes immediately** because `vite.config.js` is missing `define: { 'process.env.NODE_ENV': JSON.stringify('production') }` — Vue 3's runtime references `process.env.NODE_ENV` which doesn't exist in browser context.

**Fix task #279** created with the one-line config fix + rebuild steps. Once fixed, all ACs should pass based on code review and API verification.

### Change Log

_(Updated by agent during implementation)_

### File List

_(Updated by agent — list all files created or modified)_
