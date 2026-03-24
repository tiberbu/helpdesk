# Story: Fix: Story 3.3 Embeddable Chat Widget — process.env.NODE_ENV crash + 4 broken tests

Status: in-progress
Task ID: mn4cr0i64cnv4u
Task Number: #280
Workflow: quick-dev
Model: sonnet
Created: 2026-03-24T08:28:04.305Z

## Description

## Fix Task (from QA report docs/qa-report-task-32.md)

### SCOPE LOCK
You MUST only modify the files listed below. Any change outside this scope = failure.

### Issues to fix

#### Issue 1 (P0): Widget bundle crashes with `ReferenceError: process is not defined`
- **File**: `widget/vite.config.js`
- **Line**: 5 (inside `defineConfig`)
- **Problem**: Vite library mode does not auto-replace `process.env.NODE_ENV` in the IIFE output. Vue 3 runtime checks `process.env.NODE_ENV` at 4 locations in the bundle. In browser context, `process` is undefined, causing an immediate crash. The widget FAB never renders.
- **Current** (missing `define` key):
```js
export default defineConfig({
  plugins: [vue()],
  build: {
    lib: {
```
- **Expected** (add `define` before `build`):
```js
export default defineConfig({
  plugins: [vue()],
  define: {
    'process.env.NODE_ENV': JSON.stringify('production'),
  },
  build: {
    lib: {
```
- **Verify**: After fix, rebuild with `cd widget && npx vite build` then check: `grep -c 'process.env.NODE_ENV' ../helpdesk/public/js/helpdesk-chat.iife.js` should return `0`
- **Browser verify**: Load `http://help.frappe.local/assets/helpdesk/widget-test.html` — FAB button should appear, no console errors about `process`

#### Issue 2 (P1): 4 unit tests fail after Story 3.4 changes
- **Files**: `widget/src/__tests__/Widget.test.js`, `widget/src/__tests__/PreChatForm.test.js`, `widget/src/__tests__/ChatView.test.js`
- **Problem**: Story 3.4 modified component internals (ChatView now imports TypingIndicator/StatusIcon, PreChatForm emit handling changed, Widget.vue methods no longer exposed via `wrapper.vm` due to `<script setup>`) but original Story 3.3 tests weren't updated.
- **Failing tests**:
  1. `PreChatForm.test.js` line 64: `emits session-created with session_id and token on success` — fetch mock response format may need updating to match new API shape
  2. `ChatView.test.js` line 134: `emits session-ended when start new chat button clicked` 

## Acceptance Criteria

- [ ] `PreChatForm.test.js` line 64: `emits session-created with session_id and token on success` — fetch mock response format may need updating to match new API shape
- [ ] `ChatView.test.js` line 134: `emits session-ended when start new chat button clicked`

## Tasks / Subtasks

- [ ] `PreChatForm.test.js` line 64: `emits session-created with session_id and token on success` — fetch mock response format may need updating to match new API shape
- [ ] `ChatView.test.js` line 134: `emits session-ended when start new chat button clicked`

## Dev Notes



### References

- Task source: Claude Code Studio task #280

## Dev Agent Record

### Agent Model Used

sonnet

### Completion Notes List

_(Updated by agent on completion)_

### Change Log

_(Updated by agent during implementation)_

### File List

_(Updated by agent — list all files created or modified)_
