# Story: QA: Fix HD Admin phantom permission — broken test, missing DocType grant, is_agent gate, error handler inconsistency

Status: done
Task ID: mn3ccs9a4lu4um
Task Number: #108
Workflow: adversarial-review
Model: opus
Created: 2026-03-23T15:29:26.113Z

## Description

## QA task for Story #105

### What was changed
- `helpdesk/utils.py` — Added `"HD Admin"` to `is_agent()` so HD Admin users can call time tracking APIs
- `helpdesk/helpdesk/doctype/hd_time_entry/hd_time_entry.json` — Added HD Admin permission entry (create, delete, read, write) to DocType JSON
- `desk/src/components/ticket/TimeEntryDialog.vue` — Fixed onError handlers from `error.message` to `error?.messages?.[0]` (Frappe API format)

### What to test
1. **Backend**: All 38 HD Time Entry tests pass (run: `bench --site helpdesk.localhost run-tests --app helpdesk --module helpdesk.helpdesk.doctype.hd_time_entry.test_hd_time_entry`)
2. **is_agent() gate**: An HD Admin user can call delete_entry(), add_entry(), start_timer() without PermissionError
3. **DocType permissions**: HD Admin role appears in hd_time_entry.json permissions with delete:1
4. **Frontend error messages**: Server validation errors (e.g. duration > 1440 minutes) now surface in the toast via TimeEntryDialog.vue
5. **No regressions**: TimeTracker.vue still works, existing agent/customer permission boundaries unchanged

### Test credentials and URL
- See docs/testing-info.md for login credentials
- URL: http://helpdesk.localhost:8004

### Test steps
1. Login as agent, navigate to a ticket, open Time Tracking panel
2. Try adding a time entry with duration > 1440 minutes — should show server error toast
3. Verify timer start/stop works normally
4. Verify agent can delete own entries, cannot delete others
5. Check console for JS errors

### Files changed
- `helpdesk/utils.py`
- `helpdesk/helpdesk/doctype/hd_time_entry/hd_time_entry.json`
- `desk/src/components/ticket/TimeEntryDialog.vue`

## Acceptance Criteria

- [ ] **Backend**: All 38 HD Time Entry tests pass (run: `bench --site helpdesk.localhost run-tests --app helpdesk --module helpdesk.helpdesk.doctype.hd_time_entry.test_hd_time_entry`)
- [ ] **is_agent() gate**: An HD Admin user can call delete_entry(), add_entry(), start_timer() without PermissionError
- [ ] **DocType permissions**: HD Admin role appears in hd_time_entry.json permissions with delete:1
- [ ] **Frontend error messages**: Server validation errors (e.g. duration > 1440 minutes) now surface in the toast via TimeEntryDialog.vue
- [ ] **No regressions**: TimeTracker.vue still works, existing agent/customer permission boundaries unchanged
- [ ] Login as agent, navigate to a ticket, open Time Tracking panel
- [ ] Try adding a time entry with duration > 1440 minutes — should show server error toast
- [ ] Verify timer start/stop works normally
- [ ] Verify agent can delete own entries, cannot delete others
- [ ] Check console for JS errors

## Tasks / Subtasks

- [ ] **Backend**: All 38 HD Time Entry tests pass (run: `bench --site helpdesk.localhost run-tests --app helpdesk --module helpdesk.helpdesk.doctype.hd_time_entry.test_hd_time_entry`)
- [ ] **is_agent() gate**: An HD Admin user can call delete_entry(), add_entry(), start_timer() without PermissionError
- [ ] **DocType permissions**: HD Admin role appears in hd_time_entry.json permissions with delete:1
- [ ] **Frontend error messages**: Server validation errors (e.g. duration > 1440 minutes) now surface in the toast via TimeEntryDialog.vue
- [ ] **No regressions**: TimeTracker.vue still works, existing agent/customer permission boundaries unchanged
- [ ] Login as agent, navigate to a ticket, open Time Tracking panel
- [ ] Try adding a time entry with duration > 1440 minutes — should show server error toast
- [ ] Verify timer start/stop works normally
- [ ] Verify agent can delete own entries, cannot delete others
- [ ] Check console for JS errors

## Dev Notes



### References

- Task source: Claude Code Studio task #108

## Dev Agent Record

### Agent Model Used

opus

### Completion Notes List

Adversarial review completed. Found 12 issues (2x P1, 6x P2, 4x P3). Key P1 findings: (1) no test coverage for HD Admin calling add_entry/start_timer, (2) no migration step documented for DocType JSON permission change. Key P2 findings: triple get_roles() call in is_agent(), is_admin() bug with passed user arg, stale comments in delete_entry(), over-permissioning in DocType JSON.

### Change Log

- Created `docs/qa-report-task-108-adversarial-review.md` — full adversarial review report with 12 findings

### File List

- `docs/qa-report-task-108-adversarial-review.md` (created)
