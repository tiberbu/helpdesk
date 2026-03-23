# Story: QA: Fix: Time Tracking adversarial review P1/P2 findings

Status: in-progress
Task ID: mn3bxwpz17exfr
Task Number: #96
Workflow: adversarial-review
Model: opus
Created: 2026-03-23T20:32:11.107Z

## Description

## QA for Time Tracking P1/P2 Adversarial Review Fixes

### What to test
Verify all 5 P1/P2 findings from adversarial review (task #88) are correctly fixed.

### Files changed
- `desk/src/components/ticket/TimeTracker.vue` — Added `__ import`
- `desk/src/components/ticket/TimeEntryDialog.vue` — Added `__ import`, MAX_DURATION_MINUTES constant, showMaxDurationError computed, updated isValid, max error UI, max=24 on hours input
- `helpdesk/api/time_tracking.py` — Added MAX_DURATION_MINUTES/PRIVILEGED_ROLES imports, max-duration checks in stop_timer()/add_entry(), removed duplicated local vars in delete_entry()

### Expected behavior
1. **P1 canDelete Agent Manager**: TimeTracker.vue canDelete() shows trash icon for HD Admin, Agent Manager, AND System Manager roles
2. **P2 __ import**: No JS console errors about __ being undefined in time tracking components
3. **P2 Max duration validation**: TimeEntryDialog shows error when hours > 24 or total > 1440 min; Save button disabled
4. **P2 delete_entry dedup**: No local is_privileged/user_roles vars in delete_entry() (code review)
5. **P2 API max duration**: stop_timer/add_entry return 417 ValidationError for duration > 1440 min

### Test steps (Playwright)
1. Login as agent at http://helpdesk.localhost:8004
2. Open a ticket, navigate to time tracking section
3. Click Add Entry — set hours to 25 — verify max-duration error appears and Save is disabled
4. Set hours to 23 minutes 59 — verify save works
5. Check browser console for __ import errors
6. Screenshot time tracking UI

### Test credentials
See docs/testing-info.md

### QA task is READ-ONLY — produce a structured report in docs/ only

## Acceptance Criteria

- [ ] **P1 canDelete Agent Manager**: TimeTracker.vue canDelete() shows trash icon for HD Admin, Agent Manager, AND System Manager roles
- [ ] **P2 __ import**: No JS console errors about __ being undefined in time tracking components
- [ ] **P2 Max duration validation**: TimeEntryDialog shows error when hours > 24 or total > 1440 min; Save button disabled
- [ ] **P2 delete_entry dedup**: No local is_privileged/user_roles vars in delete_entry() (code review)
- [ ] **P2 API max duration**: stop_timer/add_entry return 417 ValidationError for duration > 1440 min

## Tasks / Subtasks

- [ ] **P1 canDelete Agent Manager**: TimeTracker.vue canDelete() shows trash icon for HD Admin, Agent Manager, AND System Manager roles
- [ ] **P2 __ import**: No JS console errors about __ being undefined in time tracking components
- [ ] **P2 Max duration validation**: TimeEntryDialog shows error when hours > 24 or total > 1440 min; Save button disabled
- [ ] **P2 delete_entry dedup**: No local is_privileged/user_roles vars in delete_entry() (code review)
- [ ] **P2 API max duration**: stop_timer/add_entry return 417 ValidationError for duration > 1440 min
- [ ] Login as agent at http://helpdesk.localhost:8004
- [ ] Open a ticket, navigate to time tracking section
- [ ] Click Add Entry — set hours to 25 — verify max-duration error appears and Save is disabled
- [ ] Set hours to 23 minutes 59 — verify save works
- [ ] Check browser console for __ import errors
- [ ] Screenshot time tracking UI

## Dev Notes



### References

- Task source: Claude Code Studio task #96

## Dev Agent Record

### Agent Model Used

opus

### Completion Notes List

_(Updated by agent on completion)_

### Change Log

_(Updated by agent during implementation)_

### File List

_(Updated by agent — list all files created or modified)_
