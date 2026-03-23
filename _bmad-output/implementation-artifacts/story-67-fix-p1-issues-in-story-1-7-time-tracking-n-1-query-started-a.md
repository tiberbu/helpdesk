# Story: Fix: P1 issues in Story 1.7 Time Tracking (N+1 query, started_at validation, customer data exposure, pagination bug)

Status: done
Task ID: mn3afxg4ksevrs
Task Number: #67
Workflow: quick-dev
Model: sonnet
Created: 2026-03-23T14:35:46.810Z

## Description

## P1 Fixes from QA Report (docs/qa-report-task-59.md)

### Issue #1: N+1 Query in get_summary
`get_summary()` in `time_tracking.py` fires a separate `frappe.db.get_value("User", ...)` per entry to resolve agent names. Collect unique agents, do one bulk query, build a lookup dict.

### Issue #2: No started_at Validation in stop_timer
`stop_timer` accepts `started_at` as raw string without validation. Parse with `frappe.utils.get_datetime()`, validate not in the future, raise ValidationError on failure.

### Issue #3: get_summary Exposes Time Entries to Customers
`get_summary` only checks HD Ticket read permission. Customers with read access to their tickets can see internal time/billing data. Add `is_agent()` check.

### Issue #13 (upgraded to P1): get_summary Pagination Bug
`frappe.get_all()` defaults to `limit_page_length=20`. Tickets with >20 entries return truncated data and WRONG totals. Pass `limit=0` or compute totals via SQL.

### Also fix if time allows:
- Issue #5: Add maxlength=500 to description textarea in TimeEntryDialog.vue
- Issue #6: Add test for admin override delete
- Issue #7: Add onError handlers with toast feedback to TimeTracker.vue resources
- Issue #11: Fix delete_entry to use ignore_permissions in frappe.delete_doc (rely on custom check only)

### Files to Modify
- `helpdesk/api/time_tracking.py`
- `desk/src/components/ticket/TimeEntryDialog.vue`
- `desk/src/components/ticket/TimeTracker.vue`
- `helpdesk/helpdesk/doctype/hd_time_entry/test_hd_time_entry.py`

## Acceptance Criteria

- [x] Implementation matches task description
- [x] No regressions introduced
- [x] Code compiles/builds without errors

## Tasks / Subtasks

- [x] Implement changes
- [x] Verify build passes

## Dev Notes



### References

- Task source: Claude Code Studio task #67

## Dev Agent Record

### Agent Model Used

sonnet

### Completion Notes List

All P1 issues and secondary issues resolved:
1. **N+1 fix**: `get_summary` now collects unique agent emails, runs a single bulk `frappe.get_all("User", ...)`, builds a dict, and maps names — O(1) DB calls instead of O(n).
2. **started_at validation**: `stop_timer` now parses `started_at` with `get_datetime()` (raises ValidationError on bad format) and rejects any future timestamp.
3. **Customer data exposure**: `get_summary` now calls `is_agent()` after the ticket permission check; raises PermissionError for non-agents.
4. **Pagination bug**: Added `limit=0` to `frappe.get_all()` in `get_summary` so all entries are fetched regardless of count.
5. **delete_entry ignore_permissions**: `frappe.delete_doc(..., ignore_permissions=True)` so our custom auth check is the sole gate.
6. **TimeEntryDialog maxlength**: Added `:maxlength="500"` to description textarea.
7. **TimeTracker onError handlers**: Added `onError` to `startResource`, `summaryResource`, and `deleteResource` resources with `toast.error()` feedback.
8. **Admin override delete test**: Added `test_delete_entry_admin_can_delete_any_entry` plus `test_get_summary_blocked_for_customer`, `test_stop_timer_rejects_future_started_at`, `test_stop_timer_rejects_invalid_started_at_format`.

All 14 tests pass. Frontend build succeeds.

### Change Log

- `helpdesk/api/time_tracking.py`: Added `get_datetime` import + `is_agent` import; fixed `stop_timer` started_at validation; fixed `get_summary` (is_agent check, limit=0, bulk user name lookup); fixed `delete_entry` (ignore_permissions=True).
- `desk/src/components/ticket/TimeEntryDialog.vue`: Added `:maxlength="500"` to description textarea.
- `desk/src/components/ticket/TimeTracker.vue`: Added `toast` import; added `onError` handlers to `startResource`, `summaryResource`, `deleteResource`.
- `helpdesk/helpdesk/doctype/hd_time_entry/test_hd_time_entry.py`: Added 4 new tests (admin override delete, customer blocked from summary, future started_at rejected, invalid started_at format rejected). Total: 14 tests.

### File List

- `helpdesk/api/time_tracking.py` (modified)
- `desk/src/components/ticket/TimeEntryDialog.vue` (modified)
- `desk/src/components/ticket/TimeTracker.vue` (modified)
- `helpdesk/helpdesk/doctype/hd_time_entry/test_hd_time_entry.py` (modified)
