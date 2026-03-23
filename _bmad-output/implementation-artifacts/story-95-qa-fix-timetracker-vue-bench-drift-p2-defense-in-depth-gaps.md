# Story: QA: Fix TimeTracker.vue bench drift + P2 defense-in-depth gaps

Status: in-progress
Task ID: mn3bxrrpd3w40o
Task Number: #95
Workflow: adversarial-review
Model: opus
Created: 2026-03-23T15:17:33.782Z

## Description

## QA Verification for Story #93 fixes

### What was changed
- `helpdesk/api/time_tracking.py` (dev + bench): `int()` → `cint()` for `duration_minutes` and `billable` parameters in `stop_timer()` and `add_entry()` to prevent unhandled ValueError on non-numeric input
- Confirmed all other items (TimeTracker.vue Agent Manager sync, MAX_DURATION_MINUTES check, TimeEntryDialog :max) were already correctly in place in both dev and bench

### Expected behavior
1. Passing non-numeric string as `duration_minutes` returns a graceful error (not a 500 unhandled ValueError)
2. Passing non-numeric string as `billable` returns a graceful error
3. `canDelete()` in TimeTracker.vue shows the delete button for Agent Manager role users
4. TimeEntryDialog hours input has max=24 and shows error when duration > 24h

### Test Steps (use Playwright)
1. Login at http://helpdesk.localhost:8004 with agent credentials
2. Navigate to a ticket and open the Time Tracker section
3. Add a manual time entry — verify it saves correctly
4. Verify the hours field in TimeEntryDialog has max=24 attribute
5. Test API via curl: call stop_timer/add_entry with duration_minutes=abc — verify graceful 417 error not a 500
6. Check browser console for JS errors
7. Screenshot the Time Tracker UI

### Files changed
- `helpdesk/api/time_tracking.py`

## Acceptance Criteria

- [ ] Passing non-numeric string as `duration_minutes` returns a graceful error (not a 500 unhandled ValueError)
- [ ] Passing non-numeric string as `billable` returns a graceful error
- [ ] `canDelete()` in TimeTracker.vue shows the delete button for Agent Manager role users
- [ ] TimeEntryDialog hours input has max=24 and shows error when duration > 24h

## Tasks / Subtasks

- [ ] Passing non-numeric string as `duration_minutes` returns a graceful error (not a 500 unhandled ValueError)
- [ ] Passing non-numeric string as `billable` returns a graceful error
- [ ] `canDelete()` in TimeTracker.vue shows the delete button for Agent Manager role users
- [ ] TimeEntryDialog hours input has max=24 and shows error when duration > 24h
- [ ] Login at http://helpdesk.localhost:8004 with agent credentials
- [ ] Navigate to a ticket and open the Time Tracker section
- [ ] Add a manual time entry — verify it saves correctly
- [ ] Verify the hours field in TimeEntryDialog has max=24 attribute
- [ ] Test API via curl: call stop_timer/add_entry with duration_minutes=abc — verify graceful 417 error not a 500
- [ ] Check browser console for JS errors
- [ ] Screenshot the Time Tracker UI

## Dev Notes



### References

- Task source: Claude Code Studio task #95

## Dev Agent Record

### Agent Model Used

opus

### Completion Notes List

_(Updated by agent on completion)_

### Change Log

_(Updated by agent during implementation)_

### File List

_(Updated by agent — list all files created or modified)_
