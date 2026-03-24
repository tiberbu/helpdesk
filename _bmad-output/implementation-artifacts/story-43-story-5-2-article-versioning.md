# Story: Story 5.2: Article Versioning

Status: review
Task ID: mn2gcxty59r6iq
Task Number: #43
Workflow: dev-story
Model: sonnet
Created: 2026-03-24T00:48:27.439Z

## Description

## Story 5.2: Article Versioning

As a KB author, I want to see change history and revert to previous versions.

### Acceptance Criteria

- Each save creates HD Article Version record with content snapshot, author, timestamp, change_summary
- Version History shows all versions with dates and authors in a drawer
- Compare: side-by-side diff highlighting changes between two selected versions
- Revert: restores content from previous version (creating new version record)

### Tasks
- Create HD Article Version DocType
- Implement version creation on HD Article save (via on_update hook)
- Create ArticleVersionHistory.vue component with version list drawer
- Implement side-by-side diff view
- Implement revert functionality
- Write unit tests for version creation, comparison, and revert

## Acceptance Criteria

- [x] Each save creates HD Article Version record with content snapshot, author, timestamp, change_summary
- [x] Version History shows all versions with dates and authors in a drawer
- [x] Compare: side-by-side diff highlighting changes between two selected versions
- [x] Revert: restores content from previous version (creating new version record)

## Tasks / Subtasks

- [x] Create HD Article Version DocType
- [x] Implement version creation on HD Article save (via on_update hook)
- [x] Create ArticleVersionHistory.vue component with version list drawer
- [x] Implement side-by-side diff view
- [x] Implement revert functionality
- [x] Write unit tests for version creation, comparison, and revert

## Dev Notes



### References

- Task source: Claude Code Studio task #43

## Dev Agent Record

### Agent Model Used

sonnet

### Completion Notes List

- All 7 unit tests pass (TimestampMismatchError fixed by reloading doc before each save in tests)
- Fixed `format_datetime` locale bug in `_create_version` — replaced with `now_datetime().strftime("%Y-%m-%d %H:%M")` to avoid Frappe locale lookup failure for users without a language setting
- Browser-verified: Version History button, drawer with version list, preview panel, side-by-side diff view, and revert confirmation dialog all work correctly
- `get_article_versions` and `revert_article_to_version` whitelisted APIs restricted to agents only (PermissionError for guests)
- Version creation skipped when content/title/category unchanged (no spurious versions)
- Sequential version numbers enforced via `MAX(version_number) + 1` query

### Change Log

- 2026-03-24: Created HD Article Version DocType (JSON, Python, __init__.py)
- 2026-03-24: Added `on_update` and `_create_version` methods to hd_article.py
- 2026-03-24: Added `get_article_versions` and `revert_article_to_version` to knowledge_base.py
- 2026-03-24: Created ArticleVersionHistory.vue (drawer + preview + diff + revert)
- 2026-03-24: Created articleVersionDiff.ts (LCS-based HTML diff utility)
- 2026-03-24: Integrated Version History button into Article.vue
- 2026-03-24: Fixed format_datetime locale bug; re-ran tests (7/7 pass)

### File List

**Created:**
- `helpdesk/helpdesk/doctype/hd_article_version/__init__.py`
- `helpdesk/helpdesk/doctype/hd_article_version/hd_article_version.json`
- `helpdesk/helpdesk/doctype/hd_article_version/hd_article_version.py`
- `helpdesk/helpdesk/doctype/hd_article_version/test_hd_article_version.py`
- `desk/src/components/knowledge-base/ArticleVersionHistory.vue`
- `desk/src/components/knowledge-base/articleVersionDiff.ts`

**Modified:**
- `helpdesk/helpdesk/doctype/hd_article/hd_article.py` — added on_update, _create_version
- `helpdesk/api/knowledge_base.py` — added get_article_versions, revert_article_to_version
- `desk/src/pages/knowledge-base/Article.vue` — added Version History button and drawer integration
