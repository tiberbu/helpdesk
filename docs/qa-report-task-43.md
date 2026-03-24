# QA Report: Story 5.2 — Article Versioning (Task #43)

**QA Date:** 2026-03-24
**QA Depth:** 1/1
**Tester:** Claude QA Agent (Opus)
**App URL:** http://help.frappe.local/helpdesk
**Test Method:** Playwright MCP browser testing + API testing via bench Python + unit tests

---

## Summary

| AC | Description | Result |
|----|-------------|--------|
| AC1 | Version creation on save (content, title, category) | **PASS** |
| AC2 | Version History shows all versions with dates and authors | **PASS** |
| AC3 | Side-by-side diff highlighting changes | **PARTIAL PASS** (P1 bug: broken string interpolation in header) |
| AC4 | Revert restores content from previous version | **PASS** (P1 bug: broken string interpolation in confirmation dialog) |

**Overall:** 4 AC functional, 1 P1 cosmetic bug across AC3+AC4 (same root cause)

---

## Detailed Results

### AC1: Version Creation on Save — PASS

**Backend API Evidence:**
- Created test article → version 1 created automatically on insert
- Updated content → version 2 created with new content snapshot
- Saved without changes → no spurious version created (count stayed at 2)
- Changed title only → version 3 created (title-only change detected)
- Version records include: `content`, `title`, `author`, `timestamp`, `change_summary`
- Sequential version numbers enforced (1, 2, 3)

**Unit tests:** All 7 tests pass (0.310s):
- test_version_created_on_content_change
- test_no_version_on_unchanged_save
- test_version_number_increments
- test_revert_creates_new_version
- test_revert_does_not_change_status
- test_guest_cannot_access_versions
- test_agent_can_access_versions

---

### AC2: Version History Shows Versions with Dates/Authors — PASS

**Browser test (Playwright):**
- Navigated to article page at `/helpdesk/kb/articles/a4pqdda8bu`
- "Version History" button visible in header bar (screenshot: `task-43-article-page-with-version-history-btn.png`)
- Clicked "Version History" → drawer opens with all versions listed
- Each version shows: version badge (v1–v8), author name, relative timestamp, change summary
- Checkboxes present for comparison selection (max 2 enforced — other checkboxes disabled)
- Screenshot: `task-43-version-history-drawer.png`

**Version preview panel:**
- Clicked version v3 → preview panel opens showing:
  - Version badge, author, timestamp, change summary in header
  - Content rendered correctly ("Content for your Article")
  - "Revert to This Version" button present
- Screenshot: `task-43-version-preview-panel.png`

**API verification:**
```json
{
  "version_number": 4,
  "author": "Administrator",
  "author_full_name": "Administrator",
  "timestamp": "2026-03-24 06:38:25.962968",
  "change_summary": "Reverted to version #1 by Administrator",
  "content": "<p>Original content version 1</p>"
}
```
Note: The `content` field was missing in the original implementation (P0) but has been fixed prior to this browser test session.

---

### AC3: Side-by-Side Diff — PARTIAL PASS (P1 cosmetic bug)

**Browser test (Playwright):**
- Selected v1 and v6 checkboxes → "2 versions selected" toolbar appeared with "Compare" button
- Clicked "Compare" → full-screen diff view opened
- Left column shows "V1 — ADMINISTRATOR" with content
- Right column shows "V6 — ADMINISTRATOR" with content
- Side-by-side layout works correctly

**P1 Bug — Broken string interpolation in diff header:**
- Header reads: `Compare v1,Mar 24, 2026 12:33 PM,6,Mar 24, 2026 12:24 PM ({1}) vs v{2} ({3})`
- Expected: `Compare v1 (Mar 24, 2026 12:33 PM) vs v6 (Mar 24, 2026 12:24 PM)`
- Screenshot: `task-43-diff-view-broken-header.png`

**Root cause:** `ArticleVersionHistory.vue:171` passes an array to `__()`:
```js
__("Compare v{0} ({1}) vs v{2} ({3})", [v0, ts0, v1, ts1])
```
But `translation.ts` `translate()` uses `...args: string[]` (rest params). When an array is passed as a single arg, `args[0]` becomes the entire array (stringified with commas for `{0}`), and `{1}`, `{2}`, `{3}` remain unresolved.

---

### AC4: Revert Functionality — PASS (P1 cosmetic bug in dialog)

**Browser test (Playwright):**
- Opened v1 preview → clicked "Revert to This Version"
- Confirmation dialog appeared with title "Revert Article?" and "Revert" button
- Clicked "Revert" → success toast: `"Article reverted to version #1"`
- Version History drawer refreshed showing new v8 with summary: `"Reverted to version #1 by Administrator"`
- Article content preserved correctly
- Screenshot: `task-43-revert-success-toast.png`

**P1 Bug — Broken string interpolation in revert dialog message:**
- Dialog shows: `"This will restore the article content from version #1,Mar 24, 2026 12:33 PM ({1}) and create a new version record."`
- Expected: `"This will restore the article content from version #1 (Mar 24, 2026 12:33 PM) and create a new version record."`
- Screenshot: `task-43-revert-dialog-broken-interpolation.png`
- Same root cause as AC3 header bug.

---

## Bugs Found

### BUG-1 (P1): Broken `__()` string interpolation in ArticleVersionHistory.vue

**Severity:** P1 — UI text garbled in diff header and revert confirmation dialog (functional behavior is correct)

**Root cause:** `ArticleVersionHistory.vue` passes arrays to `__()` translation function, but `translation.ts:translate()` uses rest parameters (`...args`). When called with `__("text {0} {1}", [val0, val1])`, `args` becomes `[[val0, val1]]` — so `{0}` gets the stringified array and `{1}` is undefined.

**Affected locations (4 total in `desk/src/components/knowledge-base/ArticleVersionHistory.vue`):**

1. **Line 42:** `__("{0} versions selected", [selectedVersions.length])` — works accidentally (single element array)
2. **Line 171:** `__("Compare v{0} ({1}) vs v{2} ({3})", [...])` — **BROKEN** (4 args)
3. **Line 334:** `__("This will restore the article content from version #{0} ({1})...", [...])` — **BROKEN** (2 args)
4. **Line 350:** `__("Article reverted to version #{0}", [v.version_number])` — works accidentally (single element)

**Fix:** Change array arguments to spread syntax in all 4 locations:
- Line 42: `__("{0} versions selected", selectedVersions.length)` (or keep as-is, single element works)
- Line 171: `__("Compare v{0} ({1}) vs v{2} ({3})", diffVersions[0].version_number, formatTs(diffVersions[0].timestamp), diffVersions[1].version_number, formatTs(diffVersions[1].timestamp))`
- Line 334: `__("This will restore...", v.version_number, formatTs(v.timestamp))`
- Line 350: `__("Article reverted to version #{0}", v.version_number)` (or keep as-is)

---

## P2/P3 Notes (No Fix Task Required)

### P3: `revert_article_to_version` returns version number via fragile pattern

`knowledge_base.py:351` — `HDArticleVersion.get_next_version_number(article) - 1` relies on the version already being created by `doc.save()` → `on_update`. Works correctly but is fragile. The return value is only informational (used in toast), so no functional impact.

---

## Console Errors

**Feature-specific errors:** None
**Pre-existing errors:**
- socket.io connection refused (socket.io server not running — infrastructure, not feature-related)
- indexedDB backing store errors (headless Chrome environment artifact)
- Vue prop type warnings (pre-existing, not related to this feature)

---

## Regression Check

- Existing article CRUD operations unaffected
- `on_update` hook correctly skips version creation when `skip_version_creation` flag is set
- Article workflow transitions (status changes) do not create spurious versions unless content/title/category changes
- Knowledge Base list view loads correctly with Version History button not interfering

---

## Screenshots

| File | Description |
|------|-------------|
| `task-43-article-page-with-version-history-btn.png` | Article page showing Version History button |
| `task-43-version-history-drawer.png` | Version History drawer with 6 versions listed |
| `task-43-version-preview-panel.png` | Version preview panel with content displayed |
| `task-43-diff-view-broken-header.png` | Side-by-side diff with broken header interpolation |
| `task-43-revert-dialog-broken-interpolation.png` | Revert dialog with broken message interpolation |
| `task-43-revert-success-toast.png` | Successful revert with toast and updated version list |
