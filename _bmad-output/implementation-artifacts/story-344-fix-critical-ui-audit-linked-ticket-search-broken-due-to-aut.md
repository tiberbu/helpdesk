# Story: Fix: Critical UI Audit — Linked ticket search broken due to Autocomplete compareFn crash on null

Status: done
Task ID: mngaalo3l93t4p
Task Number: #344
Workflow: quick-dev
Model: sonnet
Created: 2026-04-01T16:52:59.741Z

## Description

## Fix Task (from QA report docs/qa-report-task-334.md)

### SCOPE LOCK
You MUST only modify the files listed below. Any change outside this scope = failure.

### Issues to fix
#### Issue 1: Autocomplete compareFn crashes on null selectedTicket — search results never render
- File: `desk/src/components/ticket/LinkTicketDialog.vue`
- Line: 14-20 (Autocomplete component usage)
- Problem: The frappe-ui Autocomplete's default `compareFn` is `(a, b) => a.value === b.value`. When `selectedTicket` is `null` (initial state), headlessui's Combobox calls `compareFn(null, option)` → `null.value` → TypeError. This crash prevents ComboboxOption items from rendering, so users see 'No results found' despite the API returning correct data.
- Console error: `TypeError: Cannot read properties of null (reading 'value')` at `Object.compare` / `Object.isSelected`
- Current (line 14-20):
```vue
<Autocomplete
  :options="searchOptions"
  :placeholder="__('Search by ID or subject…')"
  v-model="selectedTicket"
  :filter-results="false"
  @update:query="onSearchQuery"
/>
```
- Expected:
```vue
<Autocomplete
  :options="searchOptions"
  :placeholder="__('Search by ID or subject…')"
  v-model="selectedTicket"
  :compareFn="(a, b) => a?.value === b?.value"
  @update:query="onSearchQuery"
/>
```
- Rationale: (1) Add `:compareFn` with null-safe optional chaining to prevent TypeError when selectedTicket is null. (2) Remove `:filter-results="false"` since frappe-ui Autocomplete does NOT define this prop — it's silently ignored. The internal `filterOptions()` always runs, but since labels now include subject text (from task #334 fix: `#N — subject`), the filter will correctly match both ID and subject searches.
- Verify: Open http://help.frappe.local/helpdesk/tickets/3, scroll sidebar to Related Tickets, click '+ Link', type 'Priority' in search — should show ticket #10. Type '1' — should show multiple tickets. No TypeError in console.

### Build & Deploy Steps
1. Apply the fix to BOTH codebases:
 

## Acceptance Criteria

- [x] Implementation matches task description
- [x] No regressions introduced
- [x] Code compiles/builds without errors

## Tasks / Subtasks

- [x] Implement changes
- [x] Verify build passes

## Dev Notes



### References

- Task source: Claude Code Studio task #344

## Dev Agent Record

### Agent Model Used

sonnet

### Completion Notes List

- Replaced `:filter-results="false"` (unsupported frappe-ui prop) with `:compareFn="(a, b) => a?.value === b?.value"` (null-safe compareFn) in LinkTicketDialog.vue Autocomplete component
- Fix applied to both dev and bench copies
- Frontend rebuilt successfully via `yarn build` (29.74s)
- Browser-tested: "Priority" search returns `#10 — PriorityOrder Test Ticket`; "1" returns 20+ tickets. No TypeError in console.

### Change Log

- 2026-04-01: Fixed Autocomplete `compareFn` crash on null `selectedTicket` — replaced `:filter-results="false"` with `:compareFn="(a, b) => a?.value === b?.value"`

### File List

- `desk/src/components/ticket/LinkTicketDialog.vue` (dev + bench)
- `/home/ubuntu/frappe-bench/apps/helpdesk/desk/src/components/ticket/LinkTicketDialog.vue`
