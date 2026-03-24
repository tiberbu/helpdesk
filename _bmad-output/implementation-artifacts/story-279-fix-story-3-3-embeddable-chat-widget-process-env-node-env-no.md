# Story: Fix: Story 3.3 Embeddable Chat Widget — process.env.NODE_ENV not replaced in IIFE bundle crashes widget

Status: done
Task ID: mn4cpddgiu5l3d
Task Number: #279
Workflow: quick-dev
Model: sonnet
Created: 2026-03-24T08:26:47.670Z

## Description

## Fix Task (from QA report docs/qa-report-task-32.md)

### SCOPE LOCK
You MUST only modify the files listed below. Any change outside this scope = failure.

### Issues to fix
#### Issue 1: Widget bundle crashes with `ReferenceError: process is not defined`
- File: `widget/vite.config.js`
- Line: 5 (inside `defineConfig` object)
- Current: No `define` option — Vue 3 runtime references `process.env.NODE_ENV` which is undefined in browser IIFE context
- Expected: Add `define: { 'process.env.NODE_ENV': JSON.stringify('production') }` at the top level of the config object (sibling of `plugins`, `build`, `test`)
- After adding, rebuild: `cd widget && npx vite build`
- Copy built file: `cp helpdesk/public/js/helpdesk-chat.iife.js /home/ubuntu/frappe-bench/apps/helpdesk/helpdesk/public/js/helpdesk-chat.iife.js`
- Verify: `grep -c 'process.env' helpdesk/public/js/helpdesk-chat.iife.js` should return `0`

### Done Checklist (ALL must pass)
- [x] Issue 1 fixed — `define` added to vite.config.js
- [x] Widget rebuilt: `cd widget && npx vite build` succeeds
- [x] `grep -c 'process.env' helpdesk/public/js/helpdesk-chat.iife.js` returns `0`
- [x] Bundle still under 50KB gzipped: `gzip -c helpdesk/public/js/helpdesk-chat.iife.js | wc -c` < 51200 (32284 bytes)
- [x] Widget unit tests still pass: `cd widget && npx vitest run` — 62/62 pass
- [x] Built file copied to bench: `/home/ubuntu/frappe-bench/apps/helpdesk/helpdesk/public/js/helpdesk-chat.iife.js`
- [x] No files modified outside scope
- [x] `git diff --stat` shows only `widget/vite.config.js` and `helpdesk/public/js/helpdesk-chat.iife.js` (other diff entries are pre-existing)

### MANDATORY COMPLETION GATE
Before marking done, run EVERY verify command above. If ANY fails, fix it. Do not skip.

## Acceptance Criteria

- [x] Implementation matches task description
- [x] No regressions introduced
- [x] Code compiles/builds without errors

## Tasks / Subtasks

- [x] Implement changes
- [x] Verify build passes

## Dev Notes



### References

- Task source: Claude Code Studio task #279

## Dev Agent Record

### Agent Model Used

sonnet

### Completion Notes List

- Changed `defineConfig({...})` to `defineConfig(({ command }) => ({...}))` function form so `define` is conditional: only applied during `command === 'build'`, not during test runs
- This prevents Vue 3 from running in production mode during Vitest, which was causing 4 test failures (`handleSessionCreated`/`handleSessionEnded` not accessible, event emission failures)
- Bundle rebuilt: 92.35 kB raw / 32.31 kB gzipped — no `process.env` references remain
- All 62 unit tests pass
- Built file copied to bench at `/home/ubuntu/frappe-bench/apps/helpdesk/helpdesk/public/js/helpdesk-chat.iife.js`

### Change Log

- `widget/vite.config.js`: Changed static `defineConfig({})` to function form `defineConfig(({ command }) => ({}))`, made `define` block conditional on `command === 'build'` to avoid breaking Vitest
- `helpdesk/public/js/helpdesk-chat.iife.js`: Rebuilt bundle (no `process.env` references)

### File List

- `widget/vite.config.js` — modified (define conditional on build command)
- `helpdesk/public/js/helpdesk-chat.iife.js` — rebuilt
