# Story: QA: Story 3.3: Embeddable Chat Widget

Status: done
Task ID: mn3r7wtscctxi3
Task Number: #228
Workflow: playwright-qa
Model: opus
Created: 2026-03-23T22:25:27.398Z

## Description

## QA Report Task — DO NOT MODIFY CODE

**Review task #32: Story 3.3: Embeddable Chat Widget**
**QA Depth: 1/1** (max depth reached = no further QA cycles)

### What was verified
Read the story file for acceptance criteria: `_bmad-output/implementation-artifacts/story-32-story-3-3-embeddable-chat-widget.md`

### Deliverable
Produced `docs/qa-report-task-32.md` with full PASS/FAIL results per AC.

## Acceptance Criteria

- [x] Test each acceptance criterion from the story file
- [x] Check for regressions in related functionality
- [x] Check console errors / API errors
- [x] **ONE task only** — consolidated fix task created (task #229)
- [x] **Atomic scope** — only P0 issues from this QA
- [x] **Exact file paths + line numbers** for every issue
- [x] **Before/after code snippets** showing exactly what to change
- [x] **Verification command** for each fix
- [x] **Done criteria checklist** — each item independently verifiable
- [x] Title format: "Fix: Story 3.3 Embeddable Chat Widget — wrong API paths + offline ticket Guest permission"

## Tasks / Subtasks

- [x] Read story file and acceptance criteria
- [x] Review all widget source files (Widget.vue, PreChatForm.vue, OfflineForm.vue, ChatView.vue, BrandingHeader.vue, socket.js, main.js, styles.css)
- [x] Test API endpoints via curl (get_availability, get_widget_config, create_session, send_message, get_messages, create_offline_ticket)
- [x] Run widget unit tests (42/42 pass)
- [x] Build widget and check bundle size (43.12 KB gzipped < 50KB)
- [x] Check for security issues (v-html XSS, permission elevation)
- [x] Write QA report (docs/qa-report-task-32.md)
- [x] Create consolidated fix task for P0 issues (task #229)

## Dev Notes

Playwright MCP tools were not available in this environment. Testing was done via:
- curl for all 6 API endpoints
- Code review of all widget source files
- vitest for unit tests (42/42 pass)
- Vite build for bundle size verification

### References

- Task source: Claude Code Studio task #228
- Fix task: #229

## Dev Agent Record

### Agent Model Used

opus

### Completion Notes List

- QA completed for Story 3.3: Embeddable Chat Widget
- Found 2 P0 issues, 2 P2 issues, 1 P3 issue
- P0 #1: All 6 widget API calls use wrong module path `helpdesk.helpdesk.api.chat.*` instead of `helpdesk.api.chat.*` — widget completely non-functional
- P0 #2: `create_offline_ticket` fails for Guest users — missing `frappe.set_user("Administrator")` elevation
- Created consolidated fix task #229
- All 42 unit tests pass; bundle size 43.12 KB gzipped (under 50KB limit)

### Change Log

- Created `docs/qa-report-task-32.md` — full QA report with PASS/FAIL per AC

### File List

**Created:**
- `docs/qa-report-task-32.md`
