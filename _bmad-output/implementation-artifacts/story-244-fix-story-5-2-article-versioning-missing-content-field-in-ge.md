# Story: Fix: Story 5.2 Article Versioning — Missing content field in get_article_versions API breaks preview and diff

Status: done
Task ID: mn3x4zsoaixfjo
Task Number: #244
Workflow: quick-dev
Model: sonnet
Created: 2026-03-24T01:11:02.714Z

## Description

## Fix Task (from QA report docs/qa-report-task-43.md)

### SCOPE LOCK
You MUST only modify the files listed below. Any change outside this scope = failure.

### Issues to fix
#### Issue 1: get_article_versions API missing content field
- File: `helpdesk/api/knowledge_base.py`
- Line: 314
- Current: `fields=["name", "version_number", "title", "author", "timestamp", "change_summary"],`
- Expected: `fields=["name", "version_number", "title", "author", "timestamp", "change_summary", "content"],`
- Verify: `curl -s -b /tmp/qa-cookies.txt 'http://helpdesk.localhost:8004/api/method/helpdesk.api.knowledge_base.get_article_versions?article=o7cqrsuh30' | python3 -c "import sys,json; d=json.load(sys.stdin)['message']; print('PASS' if all('content' in v for v in d) else 'FAIL')"`

**Context:** The frontend `ArticleVersionHistory.vue` uses `previewVersion.content` (line 155) for the version preview panel and `diffVersions[N].content` (lines 307-308) for the side-by-side diff comparison. Without `content` in the API response, both features render blank/empty.

### Done Checklist (ALL must pass)
- [x] Issue 1 fixed — verify with: `cd /home/ubuntu/frappe-bench/sites && source ../env/bin/activate && python3 -c "import frappe; frappe.connect(site='helpdesk.localhost'); frappe.set_user('Administrator'); from helpdesk.api.knowledge_base import get_article_versions; v=get_article_versions('o7cqrsuh30'); print('PASS' if v and 'content' in v[0] else 'FAIL'); frappe.destroy()"` → PASS
- [x] Copy fix to bench: done
- [x] Reload gunicorn: done
- [x] Unit tests still pass: 7/7 tests OK
- [x] No files modified outside scope
- [x] `git diff --stat` shows only knowledge_base.py

## Acceptance Criteria

- [x] Implementation matches task description
- [x] No regressions introduced
- [x] Code compiles/builds without errors

## Tasks / Subtasks

- [x] Implement changes
- [x] Verify build passes

## Dev Notes



### References

- Task source: Claude Code Studio task #244

## Dev Agent Record

### Agent Model Used

sonnet

### Completion Notes List

- Added `"content"` to the `fields` list in `get_article_versions()` (line 314 of `knowledge_base.py`). This single-field addition restores the version preview panel and side-by-side diff in `ArticleVersionHistory.vue`. All 7 existing unit tests continue to pass.

### Change Log

- 2026-03-24: Added `"content"` field to `get_article_versions` frappe.get_all fields list.

### File List

- `helpdesk/api/knowledge_base.py` (modified)
