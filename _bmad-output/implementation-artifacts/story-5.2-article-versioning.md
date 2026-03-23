# Story 5.2: Article Versioning

Status: ready-for-dev

## Story

As a KB author,
I want to see the history of changes to an article and revert if needed,
so that content quality is maintained over time.

## Acceptance Criteria

1. **[Version Record on Save — Schema & Hook]** Given an HD Article exists and is saved with changed `content`, `title`, or `category`, when the `on_update` hook fires, then an `HD Article Version` record is created containing: `article` (Link → HD Article), `version_number` (Int, auto-incremented), `content` (Long Text, full HTML snapshot), `title` (Data, snapshot), `author` (Link → User, the saving user), `timestamp` (Datetime, now), and `change_summary` (Small Text, optional free-text entered by the author or auto-generated as "Updated by {user} on {date}"). No version is created if neither `content` nor `title` nor `category` changed from the previous save.

2. **[Version History Drawer — UI]** Given an HD Article detail page in the agent workspace (`/helpdesk/knowledge-base/{article}`), when the author clicks the "Version History" button (or "View Versions" from the article list action menu), then a right-side drawer opens showing a scrollable list of all `HD Article Version` records for that article, ordered newest-first, each entry displaying: version number, author avatar + name, relative timestamp (e.g. "2 hours ago"), and change summary (truncated to 80 chars). The drawer must be non-blocking (article still readable behind it).

3. **[Version History — Empty State]** Given an HD Article that has never been saved with a content change (i.e., zero version records), when the author opens the Version History drawer, then an empty state message is displayed: "No version history yet. Versions are created each time the article content is updated."

4. **[Side-by-Side Diff View]** Given the Version History drawer is open and two version entries are selected (via checkboxes), when the author clicks "Compare", then a full-screen modal or expanded panel opens showing a side-by-side diff of the `content` fields: left side = older version (labeled with version number and timestamp), right side = newer version (labeled with version number and timestamp). Changed lines/paragraphs must be highlighted — additions in green, deletions in red. The diff must handle HTML content correctly (strip tags for comparison but render highlighted HTML in the view). A "Close" button dismisses the diff view and returns to the drawer.

5. **[Single Version Preview]** Given the Version History drawer is open, when the author clicks on a single version entry (not selecting for comparison), then a read-only preview panel shows the full rendered HTML content of that version, with the version metadata (author, timestamp, change summary) shown in a header bar above the content.

6. **[Revert to Previous Version]** Given the Version History drawer is open and the author is viewing a previous version (via preview, AC #5), when they click "Revert to This Version", then:
   - A confirmation dialog appears: "Revert article to version #{n} from {date}? This will create a new version record with the reverted content."
   - On confirmation, the article's `content` and `title` are updated from the selected version's snapshot
   - A new `HD Article Version` record is created with `change_summary` = "Reverted to version #{n} by {user}"
   - The article is saved and the Version History drawer refreshes to show the new version at the top
   - On cancel, no changes are made

7. **[Revert Preserves Workflow State]** Given an article is in any workflow state (`Draft`, `In Review`, `Published`, `Archived`), when a revert operation is executed (AC #6), then the article's `status` / `workflow_state` is NOT changed. Only `content` and `title` fields are restored. The revert does not bypass the review workflow.

8. **[Version Number Auto-Increment]** Given multiple save events occur on the same HD Article, when each save creates a new version, then `version_number` is auto-incremented sequentially starting from 1. The current live article content implicitly represents the "current" version; the most recent HD Article Version record's `version_number` reflects the total number of versions. No gaps or duplicates in `version_number` are permitted per article.

9. **[API — Get Article Versions]** Given the `HD Article Version` DocType exists, when an agent calls `GET /api/resource/HD Article Version?filters=[["article","=","{article_name}"]]&order_by=version_number desc`, then the list of versions is returned via the standard Frappe REST API. Additionally, a `@frappe.whitelist()` method `helpdesk.api.knowledge_base.get_article_versions(article)` exists that returns the version list with author full name resolved, for use by the Vue frontend.

10. **[Security — Agent-Only Access]** Given `HD Article Version` records exist, when a guest user or non-agent customer calls any HD Article Version endpoint (REST or whitelisted method), then a `frappe.PermissionError` is raised and no version data is returned. Version history is an internal authoring tool and must never be exposed in the customer portal.

11. **[Unit Tests — Version Creation, Comparison, and Revert]** Given the test suite runs, when executing `bench --site <site> run-tests --module helpdesk.helpdesk.doctype.hd_article_version.test_hd_article_version`, then all of the following tests pass:
    - `test_version_created_on_content_change` — save article with changed content, assert 1 version record created with correct snapshot
    - `test_no_version_on_unchanged_save` — save article with no field changes, assert no new version record created
    - `test_version_number_increments` — save article 3 times with changes, assert version_numbers are 1, 2, 3
    - `test_revert_creates_new_version` — revert to version 1 from version 3, assert version 4 created with reverted content and correct change_summary
    - `test_revert_does_not_change_status` — revert on a Published article, assert `status` remains "Published"
    - `test_guest_cannot_access_versions` — call `get_article_versions()` as guest, assert `frappe.PermissionError`
    - `test_agent_can_access_versions` — call `get_article_versions()` as agent, assert list returned
    Minimum 80% coverage on new controller methods (NFR-M-01).

## Tasks / Subtasks

- [ ] Task 1 — Create HD Article Version DocType (AC: #1, #8, #10)
  - [ ] 1.1 Create directory `helpdesk/helpdesk/doctype/hd_article_version/` with `__init__.py`
  - [ ] 1.2 Create `hd_article_version.json` with fields:
    - `article` (Link → HD Article, reqd: 1, in_list_view: 1, label: "Article")
    - `version_number` (Int, reqd: 1, in_list_view: 1, label: "Version", read_only: 1)
    - `title` (Data, label: "Article Title at Version")
    - `content` (Long Text, label: "Content Snapshot")
    - `author` (Link → User, reqd: 1, in_list_view: 1, label: "Author")
    - `timestamp` (Datetime, reqd: 1, in_list_view: 1, label: "Saved At")
    - `change_summary` (Small Text, label: "Change Summary")
  - [ ] 1.3 Set DocType permissions: Read/Write/Create for "HD Agent" and "System Manager" roles; explicitly deny all permissions for "Guest" role
  - [ ] 1.4 Create `hd_article_version.py` with `HDArticleVersion` class (extend `Document`); add `get_next_version_number(article_name)` static helper method that queries `MAX(version_number)` for the article and returns `max + 1` (or 1 if no versions exist)
  - [ ] 1.5 Set `sort_field: "version_number"` and `sort_order: "DESC"` in the DocType JSON so list views default to newest-first

- [ ] Task 2 — Implement version creation on HD Article save via `on_update` hook (AC: #1, #8)
  - [ ] 2.1 Open `helpdesk/helpdesk/doctype/hd_article/hd_article.py`
  - [ ] 2.2 Add method `HDArticle.on_update(self)` (or extend existing if present)
  - [ ] 2.3 Implement change detection: compare `self.content`, `self.title`, `self.category` with `self.get_doc_before_save()` values; if any differ (or if no `_doc_before_save` exists, i.e., first save), proceed to create version
  - [ ] 2.4 Implement `_create_version(self)`: instantiate a new `HD Article Version` doc with `article=self.name`, `version_number=HDArticleVersion.get_next_version_number(self.name)`, `content=self.content`, `title=self.title`, `author=frappe.session.user`, `timestamp=frappe.utils.now_datetime()`, `change_summary` (from `frappe.form_dict.get("change_summary", "")` if provided, else auto-generate as `f"Updated by {frappe.session.user} on {frappe.utils.format_datetime(frappe.utils.now_datetime())}"`)
  - [ ] 2.5 Call `version_doc.insert(ignore_permissions=True)` to save the version record
  - [ ] 2.6 Ensure version creation does NOT re-trigger the `on_update` hook (use `flags.ignore_version` guard or verify HD Article Version has no `on_update` that touches HD Article)
  - [ ] 2.7 Add `get_doc_before_save` enablement: ensure `self.flags.ignore_version` is checked so revert logic (Task 4) can suppress duplicate version creation when needed

- [ ] Task 3 — Add `get_article_versions` whitelisted API method (AC: #9, #10)
  - [ ] 3.1 Open `helpdesk/api/knowledge_base.py`
  - [ ] 3.2 Add `@frappe.whitelist()` method `get_article_versions(article)`:
    - Validate caller is an agent using existing `is_agent()` utility; raise `frappe.PermissionError` if not
    - Query `HD Article Version` filtered by `article = article`, ordered by `version_number DESC`
    - For each version, resolve `author` to full name via `frappe.get_value("User", author, "full_name")`
    - Return list of dicts: `{name, version_number, title, author, author_full_name, timestamp, change_summary}`
  - [ ] 3.3 Add `@frappe.whitelist()` method `revert_article_to_version(article, version_name)`:
    - Validate caller is agent; raise `frappe.PermissionError` if not
    - Fetch the `HD Article Version` doc by `version_name`
    - Validate the version's `article` field matches the provided `article` param (prevent cross-article revert)
    - Load the HD Article doc; set `doc.content = version_doc.content`, `doc.title = version_doc.title`
    - Set `doc.flags.revert_change_summary = f"Reverted to version #{version_doc.version_number} by {frappe.session.user}"` for use in `on_update`
    - Call `doc.save()` — this triggers `on_update` which creates the new version record
    - Return `{"success": True, "new_version_number": <latest version number>}`

- [ ] Task 4 — Handle revert change summary in `on_update` (AC: #6, #7)
  - [ ] 4.1 In `HDArticle._create_version()`, check `self.flags.revert_change_summary`; if set, use it as the `change_summary` instead of the auto-generated string
  - [ ] 4.2 Verify that `status`/`workflow_state` field is NOT included in the version snapshot fields being restored by `revert_article_to_version` — only `content` and `title` are restored, preserving workflow state (AC #7)
  - [ ] 4.3 Add guard: in `on_update`, skip version creation if `self.flags.skip_version_creation` is set (for internal patch/migration use)

- [ ] Task 5 — Create ArticleVersionHistory.vue frontend component (AC: #2, #3, #5)
  - [ ] 5.1 Create `desk/src/components/kb/ArticleVersionHistory.vue`:
    - Accept prop `articleName` (String, required)
    - On mount, fetch versions via `createResource` calling `helpdesk.api.knowledge_base.get_article_versions`
    - Render a side drawer (use `frappe-ui` Dialog or a custom `<div>` with transition) sliding in from the right
    - Emit `close` event on drawer close button click
    - List versions newest-first; each row: version number badge, author avatar (use existing `Avatar` component), author name, relative timestamp (use `frappe.datetime.prettyDate` or dayjs), change summary (truncated)
    - Each row has a checkbox (for comparison selection, max 2 selectable) and a "Preview" click action
    - "Compare" button enabled only when exactly 2 versions are selected; disabled + tooltip "Select 2 versions to compare" otherwise
    - Empty state: show message per AC #3 when versions list is empty
  - [ ] 5.2 Add loading skeleton while versions are fetching (use `frappe-ui` skeleton loader or simple spinner)
  - [ ] 5.3 Follow WCAG 2.1 AA: drawer has `role="dialog"`, `aria-label="Version History"`, focus trap on open, returns focus on close (NFR-U-04, NFR-U-05)

- [ ] Task 6 — Implement side-by-side diff view (AC: #4)
  - [ ] 6.1 Add a `showDiff` computed state to `ArticleVersionHistory.vue` triggered when "Compare" is clicked with 2 selected versions
  - [ ] 6.2 Implement `computeDiff(htmlA, htmlB)` utility function in `desk/src/utils/diff.js`:
    - Strip HTML tags from both inputs (use a DOM parser or simple regex) to get plain text lines
    - Apply a line-by-line diff algorithm (implement a simple LCS-based diff or use `diff` npm library if already in dependencies; check `package.json` first)
    - Return a structured diff result: array of `{type: 'unchanged'|'added'|'removed', content: string}` line objects
  - [ ] 6.3 Render diff in a full-width modal with two columns: left = older version (red highlights for removed lines), right = newer version (green highlights for added lines); unchanged lines shown in both columns without highlight
  - [ ] 6.4 Modal header shows: "Compare Version #{n} (left) vs Version #{m} (right)" with author and timestamp for each
  - [ ] 6.5 "Close" button and `Escape` key dismiss the diff modal and return focus to the drawer
  - [ ] 6.6 If HTML content contains images or tables, strip them gracefully for the diff view (do not crash on complex HTML)

- [ ] Task 7 — Implement revert functionality in UI (AC: #6, #7)
  - [ ] 7.1 In the single-version preview panel (shown on row click, AC #5), add a "Revert to This Version" button (visible only to users with write permission on HD Article)
  - [ ] 7.2 On button click, show a `frappe-ui` Dialog confirmation: title "Revert Article?", body "This will restore the article content from version #{n} ({timestamp}) and create a new version record. The article status will not change.", confirm button "Revert", cancel button "Cancel"
  - [ ] 7.3 On confirm, call `createResource` POST to `helpdesk.api.knowledge_base.revert_article_to_version` with `{article: articleName, version_name: selectedVersion.name}`
  - [ ] 7.4 On success: show success toast "Article reverted to version #{n}", refresh the versions list resource, close the preview panel, keep drawer open so author sees updated history
  - [ ] 7.5 On error: show error toast with the error message returned by the server; do NOT close the drawer

- [ ] Task 8 — Integrate Version History button into Article detail page (AC: #2)
  - [ ] 8.1 Open `desk/src/pages/knowledge-base/Article.vue` (or the equivalent article detail component)
  - [ ] 8.2 Add "Version History" button to the article action bar / toolbar area (secondary/outline style button with a clock/history icon from Lucide: `<History />` icon)
  - [ ] 8.3 Wire button click to toggle a `showVersionHistory` reactive ref
  - [ ] 8.4 Conditionally render `<ArticleVersionHistory :article-name="articleName" @close="showVersionHistory = false" />` when `showVersionHistory` is true
  - [ ] 8.5 Import and register `ArticleVersionHistory` component in Article.vue

- [ ] Task 9 — Write unit tests (AC: #11)
  - [ ] 9.1 Create `helpdesk/helpdesk/doctype/hd_article_version/test_hd_article_version.py`
  - [ ] 9.2 Implement test setup: create a test HD Article with known content; define `tearDown` to delete all test HD Article Version records and the test article
  - [ ] 9.3 `test_version_created_on_content_change` — update article content, call `article.save()`, assert `frappe.db.count("HD Article Version", {"article": article.name}) == 1`, assert version `content` matches new content
  - [ ] 9.4 `test_no_version_on_unchanged_save` — save article twice without changing content, assert still only 1 version (from first save)
  - [ ] 9.5 `test_version_number_increments` — save with 3 content changes, assert version_numbers 1, 2, 3 in sequence
  - [ ] 9.6 `test_revert_creates_new_version` — create 3 versions, call `revert_article_to_version(article.name, version_1.name)`, assert 4th version exists with `change_summary` containing "Reverted to version #1" and `content` matching version 1's content
  - [ ] 9.7 `test_revert_does_not_change_status` — set article status to "Published", revert to version 1, assert `frappe.db.get_value("HD Article", article.name, "status") == "Published"`
  - [ ] 9.8 `test_guest_cannot_access_versions` — use `frappe.set_user("Guest")`, call `get_article_versions(article.name)`, assert `frappe.PermissionError` raised; restore user in `addCleanup`
  - [ ] 9.9 `test_agent_can_access_versions` — create a test user with "HD Agent" role, `frappe.set_user(agent_user)`, call `get_article_versions(article.name)`, assert non-empty list returned
  - [ ] 9.10 Run tests: `bench --site <site> run-tests --module helpdesk.helpdesk.doctype.hd_article_version.test_hd_article_version`

## Dev Notes

### Architecture Patterns

- **HD Article Version DocType (ADR-02):** `HD Article Version` is explicitly listed in the new DocTypes to create for Phase 1 (architecture.md ADR-02). It follows the standard Frappe DocType pattern: `helpdesk/helpdesk/doctype/hd_article_version/` with `.json`, `.py`, `__init__.py`. It is a standalone DocType (not a child table) to allow direct querying and independent permissions. [Source: architecture.md#ADR-02]

- **`on_update` Hook Pattern (ADR-01):** Version creation is triggered via the `on_update` controller method on `HDArticle`, consistent with the project pattern for post-save side effects. Use `self.get_doc_before_save()` (Frappe built-in) to compare field values before and after. This method is available in Frappe v15+ and returns the pre-save document or `None` for new docs. [Source: architecture.md#ADR-01]

- **Change Detection:** Frappe's `get_doc_before_save()` returns `None` for new inserts (first save). In that case, always create a version. For subsequent saves, compare `content`, `title`, `category` fields. Do NOT compare all fields (ignore metadata like `views`, `published_on`).

- **Revert via Public Method (ADR-08):** The revert operation is exposed as a `@frappe.whitelist()` method in `helpdesk/api/knowledge_base.py` (consistent with existing KB API module). It does NOT use a separate `helpdesk/api/versioning.py` — keep KB operations co-located. [Source: architecture.md#ADR-08]

- **Diff Algorithm:** Check `helpdesk/package.json` for existing `diff` or similar npm package. If absent, implement a simple Myers diff or use the browser's native `DOMParser` + line comparison. The `diff` npm package (jsdiff) is widely used and minimal if needed. The diff utility function belongs in `desk/src/utils/diff.js` as a pure function, not inside the Vue component.

- **Frontend Component Location (ADR-09):** `ArticleVersionHistory.vue` is explicitly listed in the architecture as `desk/src/components/kb/ArticleVersionHistory.vue`. Place it in `desk/src/components/kb/` alongside `ArticleLinkDialog.vue`. [Source: architecture.md#ADR-09]

- **frappe-ui Patterns:** Use `createResource` for API calls with `auto: true` for initial fetch and manual trigger for revert. Use `frappe-ui` `Dialog` component for confirmation dialogs. Use `frappe-ui` `Badge` for version number display. Do NOT use `axios` or `fetch` directly — use `createResource` throughout. [Source: architecture.md — Frontend Architecture]

- **Permissions (ADR-04):** HD Article Version requires agent-only access. Set DocType permissions to allow HD Agent + System Manager roles. The `get_article_versions` and `revert_article_to_version` whitelisted methods must call `is_agent()` and raise `frappe.PermissionError` for non-agents. Never expose version content to guest/customer roles. [Source: architecture.md#ADR-04]

- **AR-04 (Additive schema changes only):** No changes are made to existing HD Article fields beyond adding the `on_update` logic. The `HD Article Version` DocType is entirely new. No breaking changes to existing article records. [Source: epics.md#Additional Requirements AR-04]

- **AR-05 (No patch needed for new DocType):** A migration patch is NOT required for creating a new DocType (Frappe auto-creates the DB table on `bench migrate`). A patch IS required only if modifying an existing DocType's fields. This story creates only a new DocType, so no patch file is needed. [Source: epics.md#Additional Requirements AR-05]

- **NFR-M-02 (REST API coverage):** HD Article Version is a standard Frappe DocType and therefore automatically exposes `/api/resource/HD Article Version` REST endpoints. No extra work required for basic CRUD API coverage. [Source: epics.md#Non-Functional Requirements]

### Files to Create / Modify

| Action | Path | Notes |
|--------|------|-------|
| Create | `helpdesk/helpdesk/doctype/hd_article_version/__init__.py` | Empty init file |
| Create | `helpdesk/helpdesk/doctype/hd_article_version/hd_article_version.json` | DocType definition with all fields and permissions |
| Create | `helpdesk/helpdesk/doctype/hd_article_version/hd_article_version.py` | `HDArticleVersion` class with `get_next_version_number()` helper |
| Create | `helpdesk/helpdesk/doctype/hd_article_version/test_hd_article_version.py` | Unit tests (7 test methods) |
| Modify | `helpdesk/helpdesk/doctype/hd_article/hd_article.py` | Add `on_update()` and `_create_version()` methods |
| Modify | `helpdesk/api/knowledge_base.py` | Add `get_article_versions()` and `revert_article_to_version()` whitelisted methods |
| Create | `desk/src/components/kb/ArticleVersionHistory.vue` | Version history drawer with list, preview, compare, and revert |
| Create | `desk/src/utils/diff.js` | Pure diff utility function for HTML content comparison |
| Modify | `desk/src/pages/knowledge-base/Article.vue` | Add "Version History" button and integrate `ArticleVersionHistory` component |

### Testing Standards

- Minimum 80% unit test coverage on all new controller methods (NFR-M-01).
- Use `frappe.tests.utils.FrappeTestCase` as base class for all test classes.
- Use `unittest.mock.patch` to mock `frappe.sendmail` if any notification side effects appear in tests.
- Use `frappe.set_user()` in permission tests; always restore with `frappe.set_user("Administrator")` in `addCleanup`.
- Tests must use `ignore_permissions=True` for setup data creation, not for the method under test.
- Run full test module: `bench --site <site> run-tests --module helpdesk.helpdesk.doctype.hd_article_version.test_hd_article_version`

### Constraints

- **Do NOT version every save** — only saves with actual `content`, `title`, or `category` changes create version records. Silent metadata saves (e.g., incrementing `views`) must not bloat the version history.
- **Do NOT change article status on revert** — the revert only restores `content` and `title`. The Frappe Workflow state is preserved (AC #7). This is critical to avoid bypassing the review workflow (Story 5.1).
- **Do NOT use Custom Fields** — all new DocTypes and field additions must be in source JSON files per AR-04.
- **Long Text for content snapshot** — use `Long Text` fieldtype (not `Text Editor`) for the version `content` field. `Text Editor` is an input widget; `Long Text` is the plain storage type. The HD Article itself uses `Text Editor` for input, but the stored value is HTML text — copy it as-is into `Long Text`.
- **Concurrency safety** — `get_next_version_number()` should use `frappe.db.sql` with `SELECT MAX(version_number) FOR UPDATE` or rely on Frappe's DocType insert locking. For Phase 1 scale (not high-concurrency authoring), a simple `MAX` query is sufficient.
- **i18n** — all user-facing strings in Python use `frappe._()` and in JS/Vue use `__()`.
- **Security** — version `content` may contain sensitive knowledge base information. Enforce agent-only access strictly. (NFR-SE-01 spirit)

### Project Structure Notes

- **DocType naming convention:** `HD Article Version` follows the `HD` prefix convention (AR-02). File path follows Frappe convention: `helpdesk/helpdesk/doctype/hd_article_version/`. [Source: epics.md#Additional Requirements AR-02]
- **Component placement:** `ArticleVersionHistory.vue` goes in `desk/src/components/kb/` consistent with `ArticleLinkDialog.vue` location specified in ADR-09. [Source: architecture.md#ADR-09]
- **No new Pinia store required:** Version history is fetched on demand (drawer open) and does not need persistent global state. `createResource` local to the component is sufficient. Only the `revert` action mutates server state, triggering a resource refresh in the same component scope.
- **Story 5.1 dependency:** This story assumes the `status` field on HD Article already includes `In Review` (added by Story 5.1). However, story 5.2 does NOT depend on the workflow being active — version creation via `on_update` works regardless of article status. The two stories can be developed independently.
- **No conflicts with Story 5.3:** Story 5.3 (Review Dates) adds `review_date` field to HD Article. That field should NOT be included in the version snapshot (it's metadata, not content). Ensure `_create_version()` only snapshots `content`, `title`, `category`.

### References

- FR-KB-02 (Article versioning): [Source: _bmad-output/planning-artifacts/epics.md#Story 5.2]
- ADR-02 (HD Article Version DocType in new DocType list): [Source: _bmad-output/planning-artifacts/architecture.md#ADR-02]
- ADR-01 (`on_update` hook for HD Article): [Source: _bmad-output/planning-artifacts/architecture.md#ADR-01]
- ADR-04 (Permission model — agent-only for version history): [Source: _bmad-output/planning-artifacts/architecture.md#ADR-04]
- ADR-08 (API design — `@frappe.whitelist()` in `helpdesk/api/knowledge_base.py`): [Source: _bmad-output/planning-artifacts/architecture.md#ADR-08]
- ADR-09 (Frontend component organization — `desk/src/components/kb/`): [Source: _bmad-output/planning-artifacts/architecture.md#ADR-09]
- NFR-M-01 (80% unit test coverage): [Source: _bmad-output/planning-artifacts/epics.md#Non-Functional Requirements]
- NFR-M-02 (REST API coverage): [Source: _bmad-output/planning-artifacts/epics.md#Non-Functional Requirements]
- NFR-SE-01 (Security — internal data not exposed to customers): [Source: _bmad-output/planning-artifacts/epics.md#Non-Functional Requirements]
- AR-02 (HD prefix DocType naming): [Source: _bmad-output/planning-artifacts/epics.md#Additional Requirements]
- AR-04 (Modify DocType JSON directly, not Custom Fields): [Source: _bmad-output/planning-artifacts/epics.md#Additional Requirements]
- HD Article existing implementation: `helpdesk/helpdesk/doctype/hd_article/hd_article.{json|py}`
- Knowledge Base API: `helpdesk/api/knowledge_base.py`
- Frontend KB pages: `desk/src/pages/knowledge-base/Article.vue`
- Frontend KB components: `desk/src/components/kb/`
- Story 5.1 (Article Review Workflow — workflow state preservation): `_bmad-output/implementation-artifacts/story-5.1-article-review-workflow.md`

## Dev Agent Record

### Agent Model Used

Claude Sonnet 4.5 (create-story workflow)

### Debug Log References

_None — story creation phase_

### Completion Notes List

_To be filled by implementing dev agent_

### File List

_To be filled by implementing dev agent upon completion_
