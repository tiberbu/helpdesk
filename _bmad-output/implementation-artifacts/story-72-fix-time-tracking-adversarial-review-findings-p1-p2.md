# Story: Fix: Time Tracking adversarial review findings (P1/P2)

Status: done
Task ID: mn3aqlore1znks
Task Number: #72
Workflow: quick-dev
Model: sonnet
Created: 2026-03-23T14:44:01.823Z

## Description

Fix P1 and P2 issues found in adversarial review task #70.

## P1 Fixes Required
1. **Server-side description length validation** — Add max 500 char check in `stop_timer()` and `add_entry()` in `helpdesk/api/time_tracking.py`. The current maxlength=500 is frontend-only.
2. **Add `is_agent()` check to `start_timer()`** — Currently only checks has_permission on HD Ticket. Should require agent role like `get_summary()` does.
3. **Add `is_agent()` check to `delete_entry()`** — Currently has ownership/admin check but no agent gate. Non-agents should be blocked.

## P2 Fixes Required
4. **Add `onError` handlers to `TimeEntryDialog.vue`** — Both `stopTimerResource` and `addEntryResource` lack onError. Add toast.error handlers.
5. **Gate `TimeTracker` component in `TicketDetailsTab.vue`** — Add agent role check so the component does not render for customers at all (currently it renders and shows an error toast).
6. **Add `start_timer()` test coverage** — At least one happy-path test and one permission test.
7. **Add server-side description length test** — Prove the server rejects >500 char descriptions.

## Files to modify
- `helpdesk/api/time_tracking.py`
- `desk/src/components/ticket/TimeEntryDialog.vue`
- `desk/src/components/ticket-agent/TicketDetailsTab.vue`
- `helpdesk/helpdesk/doctype/hd_time_entry/test_hd_time_entry.py`
- Sync all backend changes to `/home/ubuntu/frappe-bench/apps/helpdesk/`

## QA Report
See `docs/qa-report-task-70-adversarial-review-time-tracking-p1-fixes.md` for full findings.

## Acceptance Criteria

- [x] **Server-side description length validation** — Add max 500 char check in `stop_timer()` and `add_entry()` in `helpdesk/api/time_tracking.py`. The current maxlength=500 is frontend-only.
- [x] **Add `is_agent()` check to `start_timer()`** — Currently only checks has_permission on HD Ticket. Should require agent role like `get_summary()` does.
- [x] **Add `is_agent()` check to `delete_entry()`** — Currently has ownership/admin check but no agent gate. Non-agents should be blocked.
- [x] **Add `onError` handlers to `TimeEntryDialog.vue`** — Both `stopTimerResource` and `addEntryResource` lack onError. Add toast.error handlers.
- [x] **Gate `TimeTracker` component in `TicketDetailsTab.vue`** — Add agent role check so the component does not render for customers at all (currently it renders and shows an error toast).
- [x] **Add `start_timer()` test coverage** — At least one happy-path test and one permission test.
- [x] **Add server-side description length test** — Prove the server rejects >500 char descriptions.

## Tasks / Subtasks

- [x] **Server-side description length validation** — Add max 500 char check in `stop_timer()` and `add_entry()` in `helpdesk/api/time_tracking.py`. The current maxlength=500 is frontend-only.
- [x] **Add `is_agent()` check to `start_timer()`** — Currently only checks has_permission on HD Ticket. Should require agent role like `get_summary()` does.
- [x] **Add `is_agent()` check to `delete_entry()`** — Currently has ownership/admin check but no agent gate. Non-agents should be blocked.
- [x] **Add `onError` handlers to `TimeEntryDialog.vue`** — Both `stopTimerResource` and `addEntryResource` lack onError. Add toast.error handlers.
- [x] **Gate `TimeTracker` component in `TicketDetailsTab.vue`** — Add agent role check so the component does not render for customers at all (currently it renders and shows an error toast).
- [x] **Add `start_timer()` test coverage** — At least one happy-path test and one permission test.
- [x] **Add server-side description length test** — Prove the server rejects >500 char descriptions.

## Dev Notes



### References

- Task source: Claude Code Studio task #72

## Dev Agent Record

### Agent Model Used

sonnet

### Completion Notes List

- All 7 P1/P2 items implemented and verified.
- 21 tests pass (added 6 new tests: start_timer happy-path, start_timer customer blocked, customer cannot delete, description >500 rejection for both stop_timer and add_entry, description exactly 500 accepted).
- `delete_entry` `is_agent()` gate refined: HD Admin / System Manager bypass the agent gate (they're already allowed to delete any entry by design).
- Gunicorn reloaded to pick up Python changes; both dev and bench copies synced.

### Change Log

- `helpdesk/api/time_tracking.py`: Added `is_agent()` gate to `start_timer()`; added 500-char description validation to `stop_timer()` and `add_entry()`; added combined agent+admin gate to `delete_entry()`.
- `desk/src/components/ticket/TimeEntryDialog.vue`: Added `toast` import; added `onError` handlers to `stopTimerResource` and `addEntryResource`.
- `desk/src/components/ticket-agent/TicketDetailsTab.vue`: Imported `useAuthStore` + `storeToRefs`; added `isAgent` ref; gated `TimeTracker` with `v-if="ticket?.doc?.name && isAgent"`.
- `helpdesk/helpdesk/doctype/hd_time_entry/test_hd_time_entry.py`: Added `start_timer` import; added 6 new tests.

### File List

- `helpdesk/api/time_tracking.py` (modified)
- `desk/src/components/ticket/TimeEntryDialog.vue` (modified)
- `desk/src/components/ticket-agent/TicketDetailsTab.vue` (modified)
- `helpdesk/helpdesk/doctype/hd_time_entry/test_hd_time_entry.py` (modified)
