# Story: Fix: Story 3.7 CSAT Survey — Comment submission CSRF error for guest users

Status: done
Task ID: mn4faexe3ejr35
Task Number: #289
Workflow: quick-dev
Model: sonnet
Created: 2026-03-24T09:39:32.704Z

## Description

## Fix Task (from QA report docs/qa-report-task-36.md)

### SCOPE LOCK
You MUST only modify the files listed below. Any change outside this scope = failure.

### Issues to fix
#### Issue 1: submit_comment CSRF token error breaks comment feature for all guest users
- File: `helpdesk/api/csat.py`
- Line: 82
- Current: `@frappe.whitelist(allow_guest=True)`
- Expected: `@frappe.whitelist(allow_guest=True, xss_safe=True)`
- Context: The thank-you page is rendered via `frappe.respond_as_web_page()` as a guest web page. The embedded JS `fetch()` POSTs to `submit_comment` with `X-Frappe-CSRF-Token: 'fetch'`, but no CSRF cookie exists in the guest context, so Frappe rejects the request with CSRFTokenError (HTTP 400). Adding `xss_safe=True` bypasses CSRF validation, which is safe because the endpoint already validates the survey token string.
- Verify: `cd /home/ubuntu/frappe-bench && bench --site help.frappe.local console` then:
  ```python
  import frappe
  from helpdesk.api.csat import submit_comment
  print(getattr(submit_comment, '__func__', submit_comment).__module__)
  # Then grep to confirm xss_safe:
  ```
  Also: `grep -n 'xss_safe' /home/ubuntu/frappe-bench/apps/helpdesk/helpdesk/api/csat.py` should show `xss_safe=True` on line 82

### IMPORTANT: Apply to BOTH codebases
- Dev: `helpdesk/api/csat.py` (in /home/ubuntu/bmad-project/helpdesk/)
- Bench: Copy to `/home/ubuntu/frappe-bench/apps/helpdesk/helpdesk/api/csat.py`
- Then reload gunicorn: `kill -HUP $(pgrep -f 'gunicorn.*frappe.app.*preload' | head -1)`

### Done Checklist (ALL must pass)
- [ ] Line 82 of `helpdesk/api/csat.py` reads `@frappe.whitelist(allow_guest=True, xss_safe=True)`
- [ ] Verify: `grep -n 'xss_safe' helpdesk/api/csat.py` shows the change
- [ ] Verify: `grep -n 'xss_safe' /home/ubuntu/frappe-bench/apps/helpdesk/helpdesk/api/csat.py` shows the change
- [ ] Gunicorn reloaded after bench copy
- [ ] Browser test: Navigate to `submit_rating?token=...&rating=4`, type comment, click Submit — no CSRF e

## Acceptance Criteria

- [ ] Implementation matches task description
- [ ] No regressions introduced
- [ ] Code compiles/builds without errors

## Tasks / Subtasks

- [x] Implement changes
- [x] Verify build passes

## Dev Notes



### References

- Task source: Claude Code Studio task #289

## Dev Agent Record

### Agent Model Used

sonnet

### Completion Notes List

- Added `xss_safe=True` to `@frappe.whitelist` on `submit_comment` (line 82) to bypass CSRF validation for guest users. Safe because the endpoint validates the survey token string.

### Change Log

- `helpdesk/api/csat.py` line 82: `@frappe.whitelist(allow_guest=True)` → `@frappe.whitelist(allow_guest=True, xss_safe=True)`

### File List

- `helpdesk/api/csat.py` (modified — dev + bench copy)
