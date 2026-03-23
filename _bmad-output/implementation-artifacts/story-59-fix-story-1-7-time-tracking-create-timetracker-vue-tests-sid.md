# Story: Fix: Story 1.7 Time Tracking — Create TimeTracker.vue, Tests, Sidebar Integration, Patches

Status: in-progress
Task ID: mn390wnmtnq0kb
Task Number: #59
Workflow: quick-dev
Model: sonnet
Created: 2026-03-23T14:16:17.698Z

## Description

## Fix Task from QA Report (task #56)

The backend APIs for Story 1.7 are functional but the frontend is completely missing. See `docs/qa-report-story-1.7-time-tracking.md` for full details.

### P0 Issues to Fix
1. **Create `TimeTracker.vue`** — The main sidebar component with start/stop timer, elapsed time display (HH:MM:SS monospace), localStorage persistence (`hd_timer_{ticketId}`), cross-ticket timer warning, time summary display, entry list, and delete button. Use the story spec in `_bmad-output/implementation-artifacts/story-1.7-per-ticket-time-tracking.md` Task 3 as reference.
2. **Integrate into sidebar** — Import TimeTracker into `desk/src/components/ticket-agent/TicketDetailsTab.vue` (same pattern as RelatedTickets.vue from Story 1.6)
3. **Create unit tests** — `helpdesk/helpdesk/doctype/hd_time_entry/test_hd_time_entry.py` with 7+ test cases per AC-12
4. **localStorage persistence** — Implement in TimeTracker.vue per AC-1, AC-11
5. **Rebuild frontend** — `cd desk && yarn build` and sync to bench

### P1 Issues to Fix
6. **Migration patch** — Create `helpdesk/patches/v1_phase1/create_hd_time_entry.py` and register in `patches.txt`
7. **Remove `ignore_permissions=True`** from `time_tracking.py` inserts (lines 53, 88)
8. **Remove manual `frappe.db.commit()`** from `time_tracking.py` (lines 54, 89)
9. **Fix `createResource` non-reactive URL** in `TimeEntryDialog.vue`
10. **Add `autoname`** to `hd_time_entry.json` (e.g., `hash` or naming series)
11. **Add ownership check for delete** — Agents can only delete their own entries per AC-7

### Files to Create
- `desk/src/components/ticket/TimeTracker.vue`
- `helpdesk/helpdesk/doctype/hd_time_entry/test_hd_time_entry.py`
- `helpdesk/patches/v1_phase1/create_hd_time_entry.py`

### Files to Modify
- `desk/src/components/ticket-agent/TicketDetailsTab.vue` (add TimeTracker import)
- `desk/src/components/ticket/TimeEntryDialog.vue` (fix createResource URL)
- `helpdesk/api/time_tracking.py` (remove ignore_permissions, d

## Acceptance Criteria

- [ ] **Create `TimeTracker.vue`** — The main sidebar component with start/stop timer, elapsed time display (HH:MM:SS monospace), localStorage persistence (`hd_timer_{ticketId}`), cross-ticket timer warning, time summary display, entry list, and delete button. Use the story spec in `_bmad-output/implementation-artifacts/story-1.7-per-ticket-time-tracking.md` Task 3 as reference.
- [ ] **Integrate into sidebar** — Import TimeTracker into `desk/src/components/ticket-agent/TicketDetailsTab.vue` (same pattern as RelatedTickets.vue from Story 1.6)
- [ ] **Create unit tests** — `helpdesk/helpdesk/doctype/hd_time_entry/test_hd_time_entry.py` with 7+ test cases per AC-12
- [ ] **localStorage persistence** — Implement in TimeTracker.vue per AC-1, AC-11
- [ ] **Rebuild frontend** — `cd desk && yarn build` and sync to bench
- [ ] **Migration patch** — Create `helpdesk/patches/v1_phase1/create_hd_time_entry.py` and register in `patches.txt`
- [ ] **Remove `ignore_permissions=True`** from `time_tracking.py` inserts (lines 53, 88)
- [ ] **Remove manual `frappe.db.commit()`** from `time_tracking.py` (lines 54, 89)
- [ ] **Fix `createResource` non-reactive URL** in `TimeEntryDialog.vue`
- [ ] **Add `autoname`** to `hd_time_entry.json` (e.g., `hash` or naming series)
- [ ] **Add ownership check for delete** — Agents can only delete their own entries per AC-7

## Tasks / Subtasks

- [ ] **Create `TimeTracker.vue`** — The main sidebar component with start/stop timer, elapsed time display (HH:MM:SS monospace), localStorage persistence (`hd_timer_{ticketId}`), cross-ticket timer warning, time summary display, entry list, and delete button. Use the story spec in `_bmad-output/implementation-artifacts/story-1.7-per-ticket-time-tracking.md` Task 3 as reference.
- [ ] **Integrate into sidebar** — Import TimeTracker into `desk/src/components/ticket-agent/TicketDetailsTab.vue` (same pattern as RelatedTickets.vue from Story 1.6)
- [ ] **Create unit tests** — `helpdesk/helpdesk/doctype/hd_time_entry/test_hd_time_entry.py` with 7+ test cases per AC-12
- [ ] **localStorage persistence** — Implement in TimeTracker.vue per AC-1, AC-11
- [ ] **Rebuild frontend** — `cd desk && yarn build` and sync to bench
- [ ] **Migration patch** — Create `helpdesk/patches/v1_phase1/create_hd_time_entry.py` and register in `patches.txt`
- [ ] **Remove `ignore_permissions=True`** from `time_tracking.py` inserts (lines 53, 88)
- [ ] **Remove manual `frappe.db.commit()`** from `time_tracking.py` (lines 54, 89)
- [ ] **Fix `createResource` non-reactive URL** in `TimeEntryDialog.vue`
- [ ] **Add `autoname`** to `hd_time_entry.json` (e.g., `hash` or naming series)
- [ ] **Add ownership check for delete** — Agents can only delete their own entries per AC-7

## Dev Notes



### References

- Task source: Claude Code Studio task #59

## Dev Agent Record

### Agent Model Used

sonnet

### Completion Notes List

_(Updated by agent on completion)_

### Change Log

_(Updated by agent during implementation)_

### File List

_(Updated by agent — list all files created or modified)_
