# Story: QA: Feat: County + Sub-County picker on ticket creation with auto-remember per accou

Status: done
Task ID: mnge7uumwofr06
Task Number: #360
Workflow: playwright-qa
Model: opus
Created: 2026-04-01T18:42:24.552Z

## Description

## QA Report Task — DO NOT MODIFY CODE

**Review task #354: Feat: County + Sub-County picker on ticket creation with auto-remember per account**
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
Read the story file for acceptance criteria: `_bmad-output/implementation-artifacts/story-354-feat-county-sub-county-picker-on-ticket-creation-with-auto-r.md`

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
Produce `docs/qa-report-task-354.md` with:
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
  "description": "## Fix Task (from QA report docs/qa-report-task-354.md)\n\n### SCOPE LOCK\nYou MUST only modify the files listed below. Any change outside this scope = failure.\n\n### Issues to fix\n#### Issue 1: [title]\n- File: [exact path]\n- Line: [number]\n- Current: `[code snippet]`\n- Expected: `[code snippet]`\n- Verify: `[command that proves fix works]`\n\n#### Issue 2: ...\n\n### Done Checklist (ALL must pass)\n- [ ] Issue 1 fixed — verify with: [command]\n- [ ] Issue 2 fixed — verify with: [command]\n- [ ] No files modified outside scope\n- [ ] `git diff --stat` shows only expected files\n- [ ] App builds without errors: [build command]\n- [ ] No console errors on affected pages\n\n### MANDATORY COMPLETION GATE\nBefore marking done, run EVERY verify command above. If ANY fails, fix it. Do not skip.",
  "workdir": "/home/ubuntu/bmad-project/helpdesk",
  "status": "bmad_workflow",
  "notes": "[bmad-workflow:quick-dev]",
  "model": "sonnet",
  "max_turns": 60,
  "chain_id": ""
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
- [x] Verify no console errors (all errors are pre-existing infra issues)
- [x] No P0/P1 fix task needed — all ACs pass

## Tasks / Subtasks

- [x] Use `mcp__playwright__browser_navigate` to go to http://help.frappe.local
- [x] Login using Playwright tools (navigate to login, type credentials, click login)
- [x] Navigate to the relevant pages for this feature
- [x] Test each acceptance criterion using Playwright interactions
- [x] Take screenshots: `mcp__playwright__browser_screenshot`
- [x] Check console for errors
- [x] Test each acceptance criterion from the story file
- [x] Check for regressions in related functionality
- [x] Verify no console errors

## Dev Notes



### References

- Task source: Claude Code Studio task #360

## Dev Agent Record

### Agent Model Used

opus

### Completion Notes List

- QA PASS: All 9 acceptance criteria verified via Playwright MCP browser testing
- County dropdown loads Nairobi, TestCounty from HD Facility Mapping
- Sub-County cascading filter works: Nairobi → Starehe, Westlands; TestCounty → TestSC
- Sub-County disabled with "Select a county first" when no county selected
- Cascading clear works: changing county resets sub-county
- Fields are optional: ticket #307 created without county/sub-county
- Auto-routing works: ticket #306 (Nairobi/Westlands) → Billing team, L0 - Sub-County
- Customer portal has same County/Sub-County pickers
- Location APIs all functional: get_counties, get_sub_counties, get_contact_location
- No feature-specific console errors; all errors are pre-existing infra (socket.io)
- No P0/P1 issues found — no fix task created

### Change Log

- 2026-04-01: QA report created at docs/qa-report-task-354.md
- 2026-04-01: 12 screenshots captured in test-screenshots/task-354-*.png

### File List

- `docs/qa-report-task-354.md` — QA report with all AC results
- `test-screenshots/task-354-01-new-ticket-form-v2.png` — Initial form
- `test-screenshots/task-354-02-county-options.png` — County dropdown
- `test-screenshots/task-354-03-county-selected.png` — Nairobi selected
- `test-screenshots/task-354-04-subcounty-options.png` — Sub-county options
- `test-screenshots/task-354-05-both-selected.png` — Both fields selected
- `test-screenshots/task-354-06-cascading-filter-testcounty.png` — Cascading filter
- `test-screenshots/task-354-07-before-submit.png` — Before submit
- `test-screenshots/task-354-08-after-submit.png` — After submit
- `test-screenshots/task-354-09-optional-fields.png` — Optional fields test
- `test-screenshots/task-354-10-submitted-no-county.png` — No county submitted
- `test-screenshots/task-354-11-ticket-306-detail.png` — Ticket detail
- `test-screenshots/task-354-12-customer-portal-new.png` — Customer portal
