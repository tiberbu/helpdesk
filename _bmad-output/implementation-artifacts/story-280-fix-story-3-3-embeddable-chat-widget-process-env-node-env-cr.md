# Story: Fix: Story 3.3 Embeddable Chat Widget — process.env.NODE_ENV crash + 4 broken tests

Status: done
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

- [x] `PreChatForm.test.js` line 64: `emits session-created with session_id and token on success` — PASSES (62/62 tests pass)
- [x] `ChatView.test.js` line 134: `emits session-ended when start new chat button clicked` — PASSES (62/62 tests pass)

## Tasks / Subtasks

- [x] Issue 1 (P0): `widget/vite.config.js` — `define: { 'process.env.NODE_ENV': '"production"' }` present, bundle has 0 occurrences of `process.env`
- [x] Issue 2 (P1): All 62 unit tests pass — `PreChatForm.test.js` and `ChatView.test.js` fully green

## Dev Notes



### References

- Task source: Claude Code Studio task #280

## Dev Agent Record

### Agent Model Used

sonnet

### Completion Notes List

- Both fixes were already applied prior to this agent run (likely by a previous session or concurrent work).
- Issue 1 (P0): `widget/vite.config.js` already contains `define: { 'process.env.NODE_ENV': '"production"' }` in both dev and bench copies. Built IIFE bundle (`helpdesk-chat.iife.js`) has **0** occurrences of `process.env`.
- Issue 2 (P1): All **62 unit tests pass** (6 test files: socket, PreChatForm, ChatView, Widget, OfflineForm, ChatRealtime). The two specific failing tests (`PreChatForm.test.js` line 64 and `ChatView.test.js` line 134) are now green.
- No code changes required — verified existing state satisfies all acceptance criteria.

### Change Log

- No code changes needed — both fixes were already in place.

### File List

- `widget/vite.config.js` — already fixed (define key present)
- `helpdesk/public/js/helpdesk-chat.iife.js` — already rebuilt (0 process.env occurrences)
