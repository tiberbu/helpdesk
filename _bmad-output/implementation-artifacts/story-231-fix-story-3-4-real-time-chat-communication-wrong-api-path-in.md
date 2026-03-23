# Story: Fix: Story 3.4 Real-Time Chat Communication — wrong API path in ChatView.vue

Status: done
Task ID: mn3rzwnzv471nl
Task Number: #231
Workflow: quick-dev
Model: sonnet
Created: 2026-03-23T22:47:07.296Z

## Description

## Fix Task (from QA report docs/qa-report-task-33.md)

### SCOPE LOCK
You MUST only modify the files listed below. Any change outside this scope = failure.

### Issues to fix
#### Issue 1: Wrong API path in ChatView.vue (P0)
ChatView.vue uses `helpdesk.helpdesk.api.chat.*` (double `helpdesk`) instead of the correct `helpdesk.api.chat.*`. This breaks ALL chat functionality: message sending, message history loading, typing indicators, delivery receipts, and read receipts.

- File: `widget/src/components/ChatView.vue`
- Line 57: `fetchHistory()` URL
  - Current: `helpdesk.helpdesk.api.chat.get_messages`
  - Expected: `helpdesk.api.chat.get_messages`
- Line 166: `sendMessage()` URL
  - Current: `helpdesk.helpdesk.api.chat.send_message`
  - Expected: `helpdesk.api.chat.send_message`
- Line 256: `callApi()` helper URL
  - Current: `helpdesk.helpdesk.api.chat.${method}`
  - Expected: `helpdesk.api.chat.${method}`
- Verify: `grep -n 'helpdesk\.helpdesk\.api\.chat' widget/src/components/ChatView.vue` should return 0 results after fix
- Verify: `grep -c 'helpdesk\.api\.chat' widget/src/components/ChatView.vue` should return 3
- Verify: `cd widget && npx vitest run src/__tests__/ChatRealtime.test.js` should pass all 20 tests

### Done Checklist (ALL must pass)
- [ ] Line 57 fixed — `helpdesk.helpdesk.api.chat.get_messages` → `helpdesk.api.chat.get_messages`
- [ ] Line 166 fixed — `helpdesk.helpdesk.api.chat.send_message` → `helpdesk.api.chat.send_message`
- [ ] Line 256 fixed — `helpdesk.helpdesk.api.chat.${method}` → `helpdesk.api.chat.${method}`
- [ ] Verify: `grep 'helpdesk\.helpdesk\.api\.chat' widget/src/components/ChatView.vue` returns no matches
- [ ] Verify: `grep -c 'helpdesk\.api\.chat' widget/src/components/ChatView.vue` returns 3
- [ ] No files modified outside scope
- [ ] `git diff --stat` shows only `widget/src/components/ChatView.vue`
- [ ] All 20 frontend tests pass: `cd widget && npx vitest run src/__tests__/ChatRealtime.test.js`
- [ ] No console errors on ch

## Acceptance Criteria

- [ ] Implementation matches task description
- [ ] No regressions introduced
- [ ] Code compiles/builds without errors

## Tasks / Subtasks

- [x] Implement changes
- [x] Verify build passes

## Dev Notes



### References

- Task source: Claude Code Studio task #231

## Dev Agent Record

### Agent Model Used

sonnet

### Completion Notes List

- Fixed 3 occurrences of `helpdesk.helpdesk.api.chat` → `helpdesk.api.chat` in ChatView.vue
- All 20 ChatRealtime frontend tests pass
- Only one file modified (within scope)

### Change Log

- `widget/src/components/ChatView.vue`: corrected API path at lines 57, 166, 256

### File List

- `widget/src/components/ChatView.vue` (modified)
