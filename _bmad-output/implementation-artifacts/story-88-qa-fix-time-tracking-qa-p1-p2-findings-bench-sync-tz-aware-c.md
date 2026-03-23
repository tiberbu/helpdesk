# Story: QA: Fix: Time Tracking QA P1/P2 findings (bench sync, tz-aware crash, toast API, is_agent gaps)

Status: done
Task ID: mn3birt253exl1
Task Number: #88
Workflow: adversarial-review
Model: opus
Created: 2026-03-23T15:05:55.545Z

## Description

## QA Task: Verify Time Tracking P1/P2 fixes

### What was changed
- `desk/src/components/ticket/TimeEntryDialog.vue`: Fixed toast API syntax from `toast({title, text, type})` to `toast.error(msg)` matching codebase convention. Added toast import. Synced to bench.
- `desk/src/components/ticket-agent/TicketDetailsTab.vue`: Synced to bench (dev had `v-if="ticket?.doc?.name && isAgent"` gating TimeTracker to agents only; bench was missing this check).
- Python files already in sync: `is_agent()` gates on `stop_timer()` and `add_entry()`, `MAX_DURATION_MINUTES=1440` upper bound, `_check_delete_permission()` shared helper, `convert_utc_to_system_timezone()` for tz fix. All 32 tests pass.

### What to test in browser
1. Login as agent at http://helpdesk.localhost:8004
2. Open a ticket → verify Time Tracker panel appears in the sidebar
3. Start the timer, let it run, stop it → verify the dialog opens and entry is saved correctly
4. Manually add a time entry → verify toast appears correctly on error (e.g. try submitting 0 min)
5. Login as customer → verify Time Tracker panel is NOT visible
6. Take screenshots at each step
7. Check browser console for errors

### Test credentials
See docs/testing-info.md

### Expected behavior
- Time Tracker panel visible only for agents
- Toast errors use `.error()` API (no visual regression)
- All time entry operations work correctly

## Acceptance Criteria

- [ ] Time Tracker panel visible only for agents
- [ ] Toast errors use `.error()` API (no visual regression)
- [ ] All time entry operations work correctly

## Tasks / Subtasks

- [ ] Login as agent at http://helpdesk.localhost:8004
- [ ] Open a ticket → verify Time Tracker panel appears in the sidebar
- [ ] Start the timer, let it run, stop it → verify the dialog opens and entry is saved correctly
- [ ] Manually add a time entry → verify toast appears correctly on error (e.g. try submitting 0 min)
- [ ] Login as customer → verify Time Tracker panel is NOT visible
- [ ] Take screenshots at each step
- [ ] Check browser console for errors

## Dev Notes



### References

- Task source: Claude Code Studio task #88

## Dev Agent Record

### Agent Model Used

opus

### Completion Notes List

- Adversarial review completed with 13 findings (1 P1, 8 P2, 3 P3)
- P1: Frontend `canDelete()` excludes Agent Manager role — functional gap with backend
- Key P2s: missing `__` import in script setup, no frontend upper-bound validation, duplicated permission logic in delete_entry, no XSS sanitization on description, localStorage race conditions, duration/started_at integrity gap
- Report saved to `docs/qa-report-task-88-adversarial-review.md`

### Change Log

- Created `docs/qa-report-task-88-adversarial-review.md` — full adversarial review report

### File List

- `docs/qa-report-task-88-adversarial-review.md` (created)
