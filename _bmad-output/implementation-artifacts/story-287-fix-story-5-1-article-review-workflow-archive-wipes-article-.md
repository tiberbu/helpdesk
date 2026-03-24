# Story: Fix: Story 5.1 Article Review Workflow — Archive wipes article category to NULL

Status: done
Task ID: mn4ey64mw7jyny
Task Number: #287
Workflow: quick-dev
Model: sonnet
Created: 2026-03-24T09:29:37.416Z

## Description

## Fix Task (from QA report docs/qa-report-task-42.md)

### SCOPE LOCK
You MUST only modify the files listed below. Any change outside this scope = failure.

### Issues to fix
#### Issue 1: Archiving an article wipes its category to NULL
- File: `helpdesk/helpdesk/doctype/hd_article/hd_article.py`
- Line: 43-44
- Current:
```python
if self.status == "Archived" and self.category != None:
    self.category = None
```
- Expected: Remove these two lines entirely. Archived articles should retain their category association. The category is needed for breadcrumb navigation and API responses (`get_article` returns `category_id` and `category_name`).
- Verify: `cd /home/ubuntu/frappe-bench && bench --site help.frappe.local run-tests --app helpdesk --module helpdesk.helpdesk.doctype.hd_article.test_hd_article`
- Verify manually:
```bash
cd /home/ubuntu/frappe-bench && bench --site help.frappe.local console <<'EOF'
# Create article, archive it, check category is preserved
doc = frappe.get_doc({"doctype": "HD Article", "title": "Test", "status": "Published", "category": frappe.get_all("HD Article Category", limit=1)[0].name, "content": "test"}).insert(ignore_permissions=True)
old_cat = doc.category
doc.status = "Archived"
doc.save(ignore_permissions=True)
assert doc.category == old_cat, f"Category wiped! {doc.category} != {old_cat}"
print("PASS: category preserved after archive")
frappe.db.delete("HD Article", {"name": doc.name})
frappe.db.commit()
EOF
```

#### Issue 2: Dead code `return article` on line 55 of knowledge_base.py
- File: `helpdesk/api/knowledge_base.py`
- Line: 55
- Current: `return article` (unreachable after the dict return on line 37)
- Expected: Delete line 55 entirely
- Verify: `grep -n 'return article' helpdesk/api/knowledge_base.py` should return no results

### IMPORTANT: Apply changes to BOTH codebases
- Dev path: `/home/ubuntu/bmad-project/helpdesk/`
- Bench path: `/home/ubuntu/frappe-bench/apps/helpdesk/`

### Done Checklist (ALL must pass)
- [ ] Issu

## Acceptance Criteria

- [ ] Implementation matches task description
- [ ] No regressions introduced
- [ ] Code compiles/builds without errors

## Tasks / Subtasks

- [x] Implement changes
- [x] Verify build passes

## Dev Notes



### References

- Task source: Claude Code Studio task #287

## Dev Agent Record

### Agent Model Used

sonnet

### Completion Notes List

- Removed 2-line block (lines 43-44) from `hd_article.py` `before_save()` that cleared `self.category` when status became "Archived". Archived articles now retain their category for breadcrumb navigation and `get_article` API responses.
- Removed unreachable `return article` dead code (line 55) from `knowledge_base.py` `get_article()` function that appeared after an explicit dict return.
- Both changes applied to dev path and bench path.
- All 29 `test_hd_article` tests pass.

### Change Log

- 2026-03-24: Removed archive-wipes-category block from `hd_article.py` (Issue 1)
- 2026-03-24: Removed dead `return article` line from `knowledge_base.py` (Issue 2)

### File List

- `helpdesk/helpdesk/doctype/hd_article/hd_article.py` (dev + bench)
- `helpdesk/api/knowledge_base.py` (dev + bench)
