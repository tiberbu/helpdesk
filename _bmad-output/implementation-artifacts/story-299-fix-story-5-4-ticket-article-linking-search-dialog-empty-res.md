# Story: Fix: Story 5.4 Ticket-Article Linking — Search dialog empty results, missing article titles, broken Create Article route

Status: in-progress
Task ID: mn4gv4z8mluhfn
Task Number: #299
Workflow: quick-dev
Model: sonnet
Created: 2026-03-24T10:24:25.057Z

## Description

## Fix Task (from QA report docs/qa-report-task-45.md)

### SCOPE LOCK
You MUST only modify the files listed below. Any change outside this scope = failure.

### Issues to fix

#### Issue 1: Article search dialog shows "No results found" (P1, AC1)
- **File:** `desk/src/components/knowledge-base/ArticleLinkDialog.vue`
- **Line:** 46 (import), 14-21 (template)
- **Current:** Imports `Autocomplete` from `frappe-ui` — this component does not reactively update its dropdown options when `:options` ref changes asynchronously while the popover is open.
- **Expected:** Import from the local `@/components` Autocomplete which uses `@update:query` correctly (see `SearchComplete.vue` for working pattern).
- **Fix:** Change line 46 from:
  ```typescript
  import { Autocomplete, Button, Dialog, createResource } from "frappe-ui";
  ```
  to:
  ```typescript
  import { Button, Dialog, createResource } from "frappe-ui";
  import Autocomplete from "@/components/Autocomplete.vue";
  ```
  Also update the template to use `@change` instead of `v-model` and `:value` instead of `v-model` to match the local Autocomplete's API (check `SearchComplete.vue` for the exact pattern). The local Autocomplete uses `value` prop and `@change` event, not `v-model`.
- **Verify:** Open ticket page, click Link, type "Intro" in search — should show "Introduction" article in dropdown.

#### Issue 2: Linked articles list shows no title or link (P1, AC2)
- **File:** `desk/src/components/ticket/LinkedArticles.vue`
- **Lines:** 144-156
- **Current:** Uses `frappe.client.get_list` on `HD Ticket Article` child table. Since `HD Ticket Article` is `istable=1` with empty permissions, `get_list` only returns `name` — `article` and `article_title` fields are stripped.
- **Expected:** Article title and clickable link should be visible for each linked article.
- **Fix:** Replace the `frappe.client.get_list` resource with a call that reads from the parent HD Ticket document's `linked_articles` child table. Two approaches 

## Acceptance Criteria

- [ ] Implementation matches task description
- [ ] No regressions introduced
- [ ] Code compiles/builds without errors

## Tasks / Subtasks

- [ ] Implement changes
- [ ] Verify build passes

## Dev Notes



### References

- Task source: Claude Code Studio task #299

## Dev Agent Record

### Agent Model Used

sonnet

### Completion Notes List

_(Updated by agent on completion)_

### Change Log

_(Updated by agent during implementation)_

### File List

_(Updated by agent — list all files created or modified)_
