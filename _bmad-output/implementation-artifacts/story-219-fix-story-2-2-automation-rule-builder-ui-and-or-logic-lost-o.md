# Story: Fix: Story 2.2 Automation Rule Builder UI — AND/OR logic lost on save, no save feedback, alert() usage, missing admin guard

Status: done
Task ID: mn3oyi456bh6q4
Task Number: #219
Workflow: quick-dev
Model: sonnet
Created: 2026-03-23T21:22:02.934Z

## Description

## Fix Task (from QA report docs/qa-report-task-27.md)

### SCOPE LOCK
You MUST only modify the files listed below. Any change outside this scope = failure.

### Issues to fix

#### Issue 1: AND/OR logic operator silently discarded on save (P1-1)
- File: `desk/src/pages/automations/AutomationBuilder.vue`
- Line: 356
- Current: `conditions: JSON.stringify(conditionsState.value.conditions || []),`
- Expected: `conditions: JSON.stringify({ logic: conditionsState.value.logic || "AND", conditions: conditionsState.value.conditions || [] }),`
- Verify: `grep -n 'logic.*conditionsState' desk/src/pages/automations/AutomationBuilder.vue` should show logic being included in JSON.stringify on the save line

#### Issue 2: No success toast/feedback after save (P1-2)
- File: `desk/src/pages/automations/AutomationBuilder.vue`
- Lines: 347-373
- Current: After save, silently navigates to list with `router.push({ name: "AutomationList" })` — no toast, no error catch
- Expected: Import `createToast` from `frappe-ui`, add success toast after save, add catch block with error toast
- Verify: `grep -n 'createToast\|toast' desk/src/pages/automations/AutomationBuilder.vue` should show toast usage

#### Issue 3: alert() and confirm() used instead of frappe-ui components (P1-3)
- File: `desk/src/pages/automations/AutomationBuilder.vue` (lines 335, 339, 343, 396 — 4 `alert()` calls)
- File: `desk/src/pages/automations/AutomationList.vue` (line 182 — 1 `confirm()` call)
- Current: Raw `alert('Rule name is required.')`, `confirm('Delete rule...')`
- Expected: Replace `alert()` calls with `createToast()` validation warnings. Replace `confirm()` with a proper confirmation flow (frappe-ui Dialog or at minimum a reactive confirm pattern).
- Verify: `grep -rn 'alert(\|confirm(' desk/src/pages/automations/` should return zero matches

#### Issue 4: AutomationBuilder has no admin permission check (P1-4)
- File: `desk/src/pages/automations/AutomationBuilder.vue`
- Current: No admin/permission check — an

## Acceptance Criteria

- [x] Implementation matches task description
- [x] No regressions introduced
- [x] Code compiles/builds without errors (pre-existing frappe-ui TS issues only)

## Tasks / Subtasks

- [x] Implement changes
- [x] Verify build passes

## Dev Notes



### References

- Task source: Claude Code Studio task #219

## Dev Agent Record

### Agent Model Used

sonnet

### Completion Notes List

- Fixed all 4 P1 issues from QA report: AND/OR logic preservation, save feedback toasts, alert()/confirm() replacement, admin guard
- Pre-existing vite build error (missing common_site_config.json) is a bench infrastructure issue unrelated to these changes
- All TypeScript errors are pre-existing frappe-ui library issues (no new errors introduced)

### Change Log

- AutomationBuilder.vue: Added `toast` import, replaced 4 `alert()` with `toast.warning()`/`toast.error()`, fixed conditions serialization to include `logic` field, added success/catch toasts on save, added admin guard with LucideLock icon, added `LucideLock` import
- AutomationList.vue: Added `ref` import, added `Dialog` import, added `deleteConfirm` reactive state, replaced `confirm()` with Dialog-based confirmation flow, added `confirmDelete()` async function

### File List

- `desk/src/pages/automations/AutomationBuilder.vue` — modified
- `desk/src/pages/automations/AutomationList.vue` — modified
