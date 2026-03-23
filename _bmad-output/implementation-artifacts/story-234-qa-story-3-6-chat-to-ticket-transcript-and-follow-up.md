# Story: QA: Story 3.6: Chat-to-Ticket Transcript and Follow-up

Status: done
Task ID: mn3t4ugp1vd7dh
Task Number: #234
Workflow: playwright-qa
Model: opus
Created: 2026-03-23T23:18:57.914Z

## Description

## QA Report Task — DO NOT MODIFY CODE

**Review task #35: Story 3.6: Chat-to-Ticket Transcript and Follow-up**
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

Start by navigating to the app: `mcp__playwright__browser_navigate` with url `http://localhost:8069`
Then login with credentials from docs/testing-info.md (or use: Administrator / admin)

### What to verify
Read the story file for acceptance criteria: `_bmad-output/implementation-artifacts/story-35-story-3-6-chat-to-ticket-transcript-and-follow-up.md`

### Files changed
(check git diff for changes)

### Test steps
1. Use `mcp__playwright__browser_navigate` to go to http://localhost:8069
2. Login using Playwright tools (navigate to login, type credentials, click login)
3. Navigate to the relevant pages for this feature
4. Test each acceptance criterion using Playwright interactions
5. Take screenshots: `mcp__playwright__browser_screenshot`
6. Check console for errors
3. Test each acceptance criterion from the story file
4. Check for regressions in related functionality
5. Verify no console errors

### Deliverable
Produce `docs/qa-report-task-35.md` with:
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
  "description": "## Fix Task (from QA report docs/qa-report-task-35.md)\n\n### SCOPE LOCK\nYou MUST only modify the files listed below. Any change outside this scope = failure.\n\n### Issues to fix\n#### Issue 1: [title]\n- File: [exact path]\n- Line: [number]\n- Current: `[code snippet]`\n- Expected: `[code snippet]`\n- Verify: `[command that proves fix works]`\n\n#### Issue 2: ...\n\n### Done Checklist (ALL must pass)\n- [ ] Issue 1 fixed — verify with: [command]\n- [ ] Issue 2 fixed — verify with: [command]\n- [ ] No files modified outside scope\n- [ ] `git diff --stat` shows only expected files\n- [ ] App builds without errors: [build command]\n- [ ] No console errors on affected pages\n\n### MANDATORY COMPLETION GATE\nBefore marking done, run EVERY verify command above. If ANY fails, fix it. Do not skip.",
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

- [x] Navigate to app (Playwright MCP not available; used curl API + bench tests)
- [x] Login via API (curl to helpdesk.localhost:8004)
- [x] Test each acceptance criterion from the story file
- [x] Check for regressions in related functionality (294/296 pass, 2 pre-existing)
- [x] No P0/P1 issues found — no fix task needed

## Tasks / Subtasks

- [x] Review all changed files from Story 3.6
- [x] Run 20 integration tests (all pass)
- [x] Test AC1: Chat messages stored as ticket communications (PASS)
- [x] Test AC2: Ticket remains open when chat ends (PASS)
- [x] Test AC3: Email follow-up works (PASS — standard Frappe flow)
- [x] Verify source field on HD Ticket (PASS)
- [x] Check XSS sanitization (PASS)
- [x] Check feature flag gating (PASS)
- [x] Run full regression (294/296, 2 pre-existing)
- [x] Write QA report (docs/qa-report-task-35.md)

## Dev Notes



### References

- Task source: Claude Code Studio task #234

## Dev Agent Record

### Agent Model Used

opus

### Completion Notes List

- QA completed: All 3 acceptance criteria PASS. 20/20 Story 3.6 tests pass. 294/296 full regression (2 pre-existing failures from Story 3.5).
- One P2 issue found: Frontend source badge not synced to bench copy (visual only, no fix task per rules).
- Playwright MCP tools were not available in this environment; testing done via unit tests, bench console, and curl API.

### Change Log

| Date | Change |
|------|--------|
| 2026-03-23 | Created QA report: docs/qa-report-task-35.md |

### File List

**Created:**
- `docs/qa-report-task-35.md` — QA report for Story 3.6
