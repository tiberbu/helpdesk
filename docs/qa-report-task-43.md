# QA Report: Story 5.2 — Article Versioning (Task #43)

**QA Date:** 2026-03-24
**QA Depth:** 1/1
**Tester:** Claude QA Agent (Opus)
**App URL:** http://helpdesk.localhost:8004
**Test Method:** API testing via curl + bench Python, unit tests, code review

---

## Summary

| AC | Description | Result |
|----|-------------|--------|
| AC1 | Version creation on save (content, title, category) | PASS |
| AC2 | Version History shows all versions with dates and authors | PASS (API), **FAIL (Frontend — P0)** |
| AC3 | Side-by-side diff highlighting changes | **FAIL (P0)** |
| AC4 | Revert restores content from previous version | PASS |

**Overall:** 2 PASS, 2 FAIL (1 root cause)

---

## Detailed Results

### AC1: Version Creation on Save — PASS

**Evidence:**
- Created test article, confirmed version 1 was created automatically on insert
- Updated content → version 2 created with new content snapshot
- Saved without changes → no spurious version created (count stayed at 2)
- Changed title only → version 3 created (title-only change detected)
- Version records include: `content`, `title`, `author`, `timestamp`, `change_summary`
- Sequential version numbers enforced (1, 2, 3)

**API output:**
```
Versions after first save: 1
  v1: title=QA Test Article for Versioning, author=Administrator, ts=2026-03-24 06:37:56
Versions after content update: 2
Versions after no-change save: 2  (PASS: No spurious version)
Versions after title change: 3    (PASS: Title change created version)
```

**Unit tests:** All 7 tests pass (0.310s):
- test_version_created_on_content_change
- test_no_version_on_unchanged_save
- test_version_number_increments
- test_revert_creates_new_version
- test_revert_does_not_change_status
- test_guest_cannot_access_versions
- test_agent_can_access_versions

---

### AC2: Version History Shows Versions with Dates/Authors — PARTIAL PASS

**API (PASS):** `get_article_versions` returns version_number, author, author_full_name, timestamp, change_summary correctly:
```json
{
  "version_number": 4,
  "author": "Administrator",
  "author_full_name": "Administrator",
  "timestamp": "2026-03-24 06:38:25.962968",
  "change_summary": "Reverted to version #1 by Administrator"
}
```

**Frontend drawer (PASS):** `ArticleVersionHistory.vue` correctly renders version list with:
- Version badges (v1, v2, etc.)
- Author names
- Relative timestamps via dayjs
- Change summaries (truncated)
- Checkboxes for comparison selection (max 2)

**Frontend preview (FAIL — P0):** When clicking a version to preview, the preview panel shows **empty content** because `get_article_versions` does not include `content` in the API response fields, but the preview template renders `v-html="previewVersion.content"`.

---

### AC3: Side-by-Side Diff — FAIL (P0)

**Root cause:** Same as AC2 preview — the `get_article_versions` API does not return `content` field. The diff view uses `diffVersions[0].content` and `diffVersions[1].content` which will be `undefined`, causing `computeDiff("", "")` to produce an empty diff.

**Code review of diff utility (articleVersionDiff.ts):** Implementation is correct — LCS-based diff with HTML stripping, proper line-by-line comparison, guard against stack overflow for large content. The issue is purely that the data is missing, not that the algorithm is wrong.

---

### AC4: Revert Functionality — PASS

**Evidence:**
- Reverted article from v3 (modified title + content) to v1 (original)
- Content restored: `<p>Original content version 1</p>`
- Title restored: `QA Test Article for Versioning`
- New version (v4) created with summary: `Reverted to version #1 by Administrator`
- Article status preserved (workflow state unchanged) — verified with Published status test
- Guest user correctly denied access (PermissionError)

**API output:**
```
Revert result: {'success': True, 'new_version_number': 4}
After revert: title=QA Test Article for Versioning, content=<p>Original content version 1</p>
PASS: Content reverted
PASS: Title reverted
PASS: Revert created new version
PASS: Guest correctly denied revert
```

---

## Bugs Found

### BUG-1 (P0): Version preview and diff show empty content

**Severity:** P0 — Core feature broken (preview and diff are non-functional)

**Root cause:** `get_article_versions` API in `helpdesk/api/knowledge_base.py:314` does not include `"content"` in the `fields` list. The frontend components (`ArticleVersionHistory.vue`) expect `content` to be present in each version object for both preview rendering (line 155: `v-html="previewVersion.content"`) and diff comparison (line 307-308: `diffVersions[0].content`).

**File:** `helpdesk/api/knowledge_base.py`
**Line:** 314
**Current:**
```python
fields=["name", "version_number", "title", "author", "timestamp", "change_summary"],
```
**Expected:**
```python
fields=["name", "version_number", "title", "author", "timestamp", "change_summary", "content"],
```

**Impact:** Both the version preview panel and the side-by-side diff view will show blank/empty content, making two of the four acceptance criteria non-functional in the UI.

---

## P2/P3 Notes (No Fix Task Required)

### P3: `revert_article_to_version` returns version number via fragile pattern

`knowledge_base.py:351` — `HDArticleVersion.get_next_version_number(article) - 1` relies on the version already being created by `doc.save()` → `on_update`. Works correctly but is fragile. The return value is only informational (used in toast), so no functional impact.

---

## Console Errors

No server-side errors observed during API testing. The `limit_page_length` deprecation warning in tests is from Frappe framework itself (not this feature's code).

---

## Regression Check

- Existing article CRUD operations unaffected (tested via API)
- `on_update` hook correctly skips version creation when `skip_version_creation` flag is set
- Article workflow transitions (status changes) do not create spurious versions unless content/title/category also changes
