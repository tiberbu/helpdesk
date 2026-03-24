# Story: Fix: Story 1.5 QA Issues — Non-Internal Comment Mention Notifications

Status: done
Task ID: mn48wolap2j1ri
Task Number: #258
Workflow: quick-dev
Model: sonnet
Created: 2026-03-24T07:03:37.998Z

## Description

## P1: AC #9 — notify_mentions() fires for ALL comments, not just internal notes

**Problem:** `HDTicketComment.after_insert()` and `on_update()` in `helpdesk/helpdesk/doctype/hd_ticket_comment/hd_ticket_comment.py` call `self.notify_mentions()` unconditionally. Per AC #9, mention notifications should ONLY fire for internal notes (`is_internal=1`).

**Fix needed:** Add `is_internal` guard before `notify_mentions()` calls in `after_insert()` and `on_update()` methods.

**Files to modify:**
- `helpdesk/helpdesk/doctype/hd_ticket_comment/hd_ticket_comment.py` — gate `notify_mentions()` with `if self.is_internal:`
- `helpdesk/helpdesk/doctype/hd_ticket/test_mention_notifications.py` — add test verifying non-internal comments do NOT trigger mention notifications

## P2: AC #11 — No dedicated get_mentionable_agents API

The frontend uses the HD Agent list resource (loads ALL agents client-side). A dedicated `get_mentionable_agents(query)` endpoint would be more secure and performant. Lower priority — current approach works.

See: docs/qa-report-epic1-story-1.5.md for full details.

## Acceptance Criteria

- [x] Implementation matches task description
- [x] No regressions introduced
- [x] Code compiles/builds without errors

## Tasks / Subtasks

- [x] Implement changes
- [x] Verify build passes

## Dev Notes



### References

- Task source: Claude Code Studio task #258

## Dev Agent Record

### Agent Model Used

sonnet

### Completion Notes List

- Added `if self.is_internal:` guard in `after_insert()` and `if self.is_internal and` in `on_update()` of `HDTicketComment` to gate `notify_mentions()` calls — only internal notes now fire mention notifications.
- Added 2 new tests: `test_mention_in_non_internal_comment_does_not_notify` and `test_editing_non_internal_comment_does_not_notify`.
- All 14 tests pass (12 existing + 2 new).
- Changes applied to both dev (`/home/ubuntu/bmad-project/helpdesk/`) and bench (`/home/ubuntu/frappe-bench/apps/helpdesk/`) copies.

### Change Log

- 2026-03-24: Added `is_internal` guard to `notify_mentions()` calls in `HDTicketComment.after_insert()` and `on_update()`.
- 2026-03-24: Added 2 tests for non-internal comment mention suppression.

### File List

- `helpdesk/helpdesk/doctype/hd_ticket_comment/hd_ticket_comment.py` (dev + bench)
- `helpdesk/helpdesk/doctype/hd_ticket/test_mention_notifications.py` (dev + bench)
