# Story: QA: Story 3.3: Embeddable Chat Widget

Status: done
Task ID: mn3r7wtscctxi3
Task Number: #228
Workflow: playwright-qa
Model: opus
Created: 2026-03-23T22:25:27.398Z

## Description

QA Report for Story 3.3: Embeddable Chat Widget.
Full report at `docs/qa-report-task-32.md`.

## Acceptance Criteria

- [x] Test each acceptance criterion from the story file
- [x] Browser testing via Playwright MCP
- [x] API endpoint verification via curl
- [x] Unit test execution
- [x] Console error checking
- [x] ONE consolidated fix task created (task #280)
- [x] Exact file paths + line numbers for every issue
- [x] Before/after code snippets showing exactly what to change
- [x] Verification commands for each fix
- [x] Done criteria checklist — each item independently verifiable

## Tasks / Subtasks

- [x] Navigate to helpdesk app via Playwright (http://help.frappe.local/helpdesk)
- [x] Login with Administrator / Velocity@2026!
- [x] Verify Live Chat agent page loads correctly
- [x] Create widget test page and load in browser
- [x] Test widget script tag loading (P0 FAIL: process.env crash)
- [x] Test all 6 backend API endpoints via curl (all PASS)
- [x] Run widget unit tests (58 pass, 4 fail)
- [x] Check bundle size (42.9 KB gzipped, under 50KB)
- [x] Take screenshots of test results
- [x] Write QA report (docs/qa-report-task-32.md)
- [x] Create fix task #280 for P0 + P1 issues

## Dev Notes

### Test Environment
- Site: http://help.frappe.local (port 80 via nginx)
- Playwright MCP browser testing confirmed working
- Widget test page at: /assets/helpdesk/widget-test.html

### References

- QA report: `docs/qa-report-task-32.md`
- Fix task: #280

## Dev Agent Record

### Agent Model Used

opus

### Completion Notes List

- QA completed for Story 3.3: Embeddable Chat Widget
- Found 1 P0 issue: Widget bundle crashes with `ReferenceError: process is not defined` (vite.config.js missing `define`)
- Found 1 P1 issue: 4 unit tests broken by Story 3.4 changes
- Found 2 P2 issues (Shadow DOM querySelector, missing CSS for new components)
- All 6 backend API endpoints verified working via curl
- Agent-side Live Chat page verified working via Playwright
- Created fix task #280

### Change Log

- Created `docs/qa-report-task-32.md` — full QA report
- Created `/home/ubuntu/frappe-bench/sites/assets/helpdesk/widget-test.html` — browser test page

### File List

**Created:**
- `docs/qa-report-task-32.md`
- `task-32-widget-test-page-no-fab.png` (screenshot)
- `task-32-live-chat-agent-page.png` (screenshot)
