# Story: Fix: Story 5.1 Article Review Workflow — Email notification crashes API response

Status: done
Task ID: mn3wkipg518g59
Task Number: #242
Workflow: quick-dev
Model: sonnet
Created: 2026-03-24T00:55:07.446Z

## Description

## Fix Task (from QA report docs/qa-report-task-42.md)

### SCOPE LOCK
You MUST only modify the files listed below. Any change outside this scope = failure.

### Issues to fix
#### Issue 1: Email notification methods crash API response when no email server is configured

The workflow action notification methods call `frappe.sendmail(delayed=False)` which throws `frappe.exceptions.ValidationError: Invalid Outgoing Mail Server or Port` when no outgoing email account is configured. Since `doc.save()` already committed the DB change before `on_workflow_action()` is called, the API returns HTTP 500 even though the state transition succeeded.

**Affected API endpoints:** `approve_article`, `request_changes`, `reject_article`, `archive_article` in `helpdesk/api/knowledge_base.py` (lines 203, 226, 245, 264)

**Root cause:** `frappe.sendmail(delayed=False)` in notification helpers at `helpdesk/helpdesk/doctype/hd_article/hd_article.py` (lines 150, 169, 205)

**Fix:** Wrap each `doc.on_workflow_action()` call in the API layer with try/except to catch email errors gracefully. Log the error but return the successful status change to the frontend.

- File: `helpdesk/api/knowledge_base.py`
- Lines: 203, 226, 245, 264 (each `doc.on_workflow_action(...)` call)
- Current:
```python
doc.save(ignore_permissions=True)
doc.on_workflow_action(_APPROVE)
return {"status": doc.status}
```
- Expected:
```python
doc.save(ignore_permissions=True)
try:
    doc.on_workflow_action(_APPROVE)
except Exception:
    frappe.log_error(title="Article workflow notification failed")
return {"status": doc.status}
```
- Apply the same pattern to all 4 endpoints: `approve_article` (line 203), `request_changes` (line 226), `reject_article` (line 245), `archive_article` (line 264)
- Verify: `curl -s -b cookies.txt -X POST 'http://helpdesk.localhost:8004/api/method/helpdesk.api.knowledge_base.approve_article' --data-urlencode 'article=ARTICLE_NAME'` should return HTTP 200 with `{"message":{"status":"Published"}

## Acceptance Criteria

- [x] Implementation matches task description
- [x] No regressions introduced
- [x] Code compiles/builds without errors

## Tasks / Subtasks

- [x] Implement changes
- [x] Verify build passes

## Dev Notes



### References

- Task source: Claude Code Studio task #242

## Dev Agent Record

### Agent Model Used

sonnet

### Completion Notes List

- Wrapped `doc.on_workflow_action(...)` in try/except for all 4 reviewer endpoints: `approve_article`, `request_changes`, `reject_article`, `archive_article`.
- Email/notification errors are now caught, logged via `frappe.log_error`, and the API returns the successful status change instead of HTTP 500.
- Both dev and bench copies updated; gunicorn reloaded.

### Change Log

- 2026-03-24: Applied try/except around `on_workflow_action()` calls in `helpdesk/api/knowledge_base.py` for all 4 affected endpoints.

### File List

- `helpdesk/api/knowledge_base.py` (modified — both dev and bench copies)
