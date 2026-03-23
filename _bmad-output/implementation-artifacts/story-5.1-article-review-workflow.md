# Story 5.1: Article Review Workflow

Status: ready-for-dev

## Story

As a KB author,
I want articles to go through a review workflow before publication,
so that only vetted content reaches customers.

## Acceptance Criteria

1. **[Lifecycle States — Schema]** Given the HD Article DocType, when a developer inspects the `status` field, then it has four options: `Draft`, `In Review`, `Published`, `Archived` (adding `In Review` to the existing three), and `Draft` remains the default for all new articles.

2. **[Frappe Workflow Configuration]** Given the HD Article DocType, when a Frappe Workflow named `HD Article Review Workflow` is configured and saved, then state transitions are governed exclusively by that workflow engine with the following allowed transitions:
   - `Draft` → `In Review` (action: "Submit for Review"; allowed roles: Agent, HD Agent, System Manager)
   - `In Review` → `Published` (action: "Approve"; allowed roles: HD Admin, System Manager)
   - `In Review` → `Draft` (action: "Request Changes"; allowed roles: HD Admin, System Manager)
   - `In Review` → `Archived` (action: "Reject"; allowed roles: HD Admin, System Manager)
   - `Published` → `Archived` (action: "Archive"; allowed roles: HD Admin, System Manager)

3. **[Submit for Review — Email Notification]** Given an author clicks "Submit for Review" and the article transitions from `Draft` to `In Review`, when the transition completes, then all configured reviewers receive an email notification containing the article title, author name, and a direct link to the article in the agent workspace.

4. **[Reviewer Configuration]** Given an administrator opens HD Settings, when they view the "Knowledge Base" section, then they can configure a list of reviewer users (Link to User) who receive notifications when articles are submitted for review. The field is named `kb_reviewers` and accepts a child table of User links.

5. **[Reviewer Actions — Email to Author]** Given a reviewer approves, requests changes, or rejects an article in `In Review` state, when the transition completes, then the original article author receives an email notification with:
   - Approval: "Your article '[title]' has been published."
   - Request Changes: "Changes requested for '[title]': [reviewer comment]"
   - Rejection: "Your article '[title]' has been archived (rejected)."

6. **[Reviewer Comment on Request Changes]** Given a reviewer clicks "Request Changes", when they execute the action, then a prompt (dialog or inline field) collects a required comment/reason, and that comment is stored on the article as `reviewer_comment` (Text field) and included in the author notification email.

7. **[Customer Portal Visibility — Published Only]** Given articles exist in various states (`Draft`, `In Review`, `Published`, `Archived`), when a customer (guest or non-agent user) calls any knowledge base API endpoint (`get_article`, `get_categories`, `get_category_articles`, portal search), then only `Published` articles are returned. Non-published articles must never appear in portal output. (The existing `get_article` check and `get_category_articles` filter already enforce this — this AC confirms those filters remain intact and extend to all new endpoints.)

8. **[Agent Visibility of In Review Articles]** Given an agent is logged in, when they search the knowledge base or navigate the agent KB section, then `In Review` articles are visible with an "In Review" state indicator, allowing agents to preview pending content for internal reference before it is published.

9. **[Lifecycle State Badges — Article List View]** Given the agent KB article list view (`/helpdesk/knowledge-base`), when articles with different statuses are displayed, then each article row shows a color-coded status badge:
   - `Draft` — gray badge
   - `In Review` — yellow/amber badge
   - `Published` — green badge
   - `Archived` — red badge
   These badges follow `frappe-ui` Badge component conventions and UX-DR-10.

10. **[Unit Tests — Workflow Transitions]** Given the workflow configuration, when the test suite runs, then unit tests pass covering: (a) Draft → In Review transition triggers reviewer notification, (b) In Review → Published sets `published_on`, (c) In Review → Draft with comment stores `reviewer_comment` and notifies author, (d) only Published articles are returned from customer-facing API endpoints. Minimum 80% coverage on new controller methods (NFR-M-01).

11. **[Migration Patch — Add `In Review` Status]** Given a pre-existing Frappe Helpdesk installation with HD Article records, when the Phase 1 migration patch runs, then the `status` field options are updated to include `In Review` without altering any existing `Draft`, `Published`, or `Archived` article records.

## Tasks / Subtasks

- [ ] Task 1 — Update HD Article DocType schema to add `In Review` status and reviewer comment field (AC: #1, #6, #11)
  - [ ] 1.1 Open `helpdesk/helpdesk/doctype/hd_article/hd_article.json`
  - [ ] 1.2 Update the `status` field `options` from `"Published\nDraft\nArchived"` to `"Draft\nIn Review\nPublished\nArchived"` (re-order so Draft is first/default consistent with `default: "Draft"`)
  - [ ] 1.3 Add `Text` field `reviewer_comment` (label: "Reviewer Comment", description: "Comment from reviewer when requesting changes", read_only: 1)
  - [ ] 1.4 Add `Section Break` before `reviewer_comment` with `depends_on: "eval:doc.reviewer_comment"` so it only shows when populated
  - [ ] 1.5 Create migration patch `helpdesk/patches/v1_phase1/add_in_review_status_to_hd_article.py` with `execute()` that safely adds `In Review` to the status field options without touching existing records
  - [ ] 1.6 Register the patch in `helpdesk/patches.txt`

- [ ] Task 2 — Create Frappe Workflow JSON for HD Article lifecycle (AC: #2)
  - [ ] 2.1 Create `helpdesk/helpdesk/doctype/hd_article/hd_article_review_workflow.json` (or in `helpdesk/fixtures/`) as a Frappe Workflow document with `doctype: "Workflow"` and `document_type: "HD Article"`
  - [ ] 2.2 Define workflow states: `Draft` (doc_status=0), `In Review` (doc_status=0), `Published` (doc_status=1), `Archived` (doc_status=2)
  - [ ] 2.3 Define transitions: Draft→In Review (Submit for Review, Agent/HD Agent/System Manager), In Review→Published (Approve, HD Admin/System Manager), In Review→Draft (Request Changes, HD Admin/System Manager), In Review→Archived (Reject, HD Admin/System Manager), Published→Archived (Archive, HD Admin/System Manager)
  - [ ] 2.4 Set the workflow state field to use the existing `status` field on HD Article (`workflow_state_field: "status"`)
  - [ ] 2.5 Register the workflow fixture in `hooks.py` fixtures list (if using fixtures approach) or create via a setup/install script
  - [ ] 2.6 Verify the workflow is applied and existing articles in `Draft`/`Published`/`Archived` state are not broken (regression check)

- [ ] Task 3 — Add reviewer configuration to HD Settings (AC: #4)
  - [ ] 3.1 Create a new child DocType `HD KB Reviewer` with fields: `user` (Link → User, reqd: 1, in_list_view: 1)
  - [ ] 3.2 Add `Section Break` "Knowledge Base" to `hd_settings.json`
  - [ ] 3.3 Add a `Table` field `kb_reviewers` (label: "Article Reviewers", options: "HD KB Reviewer") to HD Settings
  - [ ] 3.4 Add helper method to `hd_settings.py`: `get_kb_reviewer_emails()` → returns list of email addresses from `kb_reviewers` child table
  - [ ] 3.5 Create migration patch for the new Settings fields: `helpdesk/patches/v1_phase1/add_kb_settings_to_hd_settings.py`

- [ ] Task 4 — Implement workflow transition notification logic (AC: #3, #5, #6)
  - [ ] 4.1 Add `on_workflow_action` hook in `hd_article.py` → `HDArticle.on_workflow_action(self, action)`
  - [ ] 4.2 Implement `_notify_reviewers_for_review(self)`: fetch `kb_reviewers` from HD Settings, send email to each with article title, author, and link (`/helpdesk/knowledge-base/{article_name}`)
  - [ ] 4.3 Implement `_notify_author_approved(self)`: email to `self.author` with subject "Your article '[title]' has been published"
  - [ ] 4.4 Implement `_notify_author_changes_requested(self, comment)`: email to `self.author` with subject "Changes requested for '[title]'" and reviewer comment in body; set `self.reviewer_comment = comment` before save
  - [ ] 4.5 Implement `_notify_author_rejected(self)`: email to `self.author` with subject "Your article '[title]' has been archived (rejected)"
  - [ ] 4.6 Route `on_workflow_action` to correct notification method based on `action` string: `"Submit for Review"` → `_notify_reviewers_for_review`, `"Approve"` → `_notify_author_approved`, `"Request Changes"` → `_notify_author_changes_requested`, `"Reject"` → `_notify_author_rejected`
  - [ ] 4.7 For "Request Changes" action: add a `before_workflow_action` hook that captures the reviewer comment from the workflow action dialog via `frappe.form_dict` or workflow action metadata; validate comment is non-empty
  - [ ] 4.8 Ensure all email sending uses `frappe.sendmail()` with translatable subject/body strings

- [ ] Task 5 — Verify and harden customer portal visibility filter (AC: #7, #8)
  - [ ] 5.1 Review `helpdesk/api/knowledge_base.py` → confirm `get_article()` already throws PermissionError for non-agents accessing non-Published articles (it does — verify this remains intact)
  - [ ] 5.2 Confirm `get_category_articles()` already filters `status: "Published"` (it does — verify intact)
  - [ ] 5.3 Confirm `get_categories()` already counts only `status: "Published"` articles (it does — verify intact)
  - [ ] 5.4 Review `helpdesk/search.py` — confirm or update article search to exclude `In Review`, `Draft`, and `Archived` results for guest/non-agent callers
  - [ ] 5.5 Confirm agent-facing KB API (`get_article` with `is_agent()` check) allows access to `In Review` articles — no change needed but verify
  - [ ] 5.6 Add a dedicated `get_agent_articles()` whitelisted method (or confirm existing agent KB list query) that returns all non-Archived articles for agents including `In Review` ones

- [ ] Task 6 — Add color-coded lifecycle badges to the article list view (AC: #9)
  - [ ] 6.1 Open `desk/src/pages/knowledge-base/Articles.vue` (or relevant list component)
  - [ ] 6.2 Identify where article status is rendered in the list; currently the `default_list_data()` in `hd_article.py` includes a `status` column of type `"status"`
  - [ ] 6.3 Create or extend a `ArticleStatusBadge.vue` component (in `desk/src/components/knowledge-base/`) using `frappe-ui` `Badge` component with props for `status` string and returning appropriate color: `Draft` → gray, `In Review` → amber/yellow, `Published` → green, `Archived` → red
  - [ ] 6.4 Integrate `ArticleStatusBadge.vue` into the article list rows so each article displays the color-coded badge
  - [ ] 6.5 Ensure badge is also visible on the article detail page header area in the agent workspace
  - [ ] 6.6 Follow UX-DR-10 specification: "Article lifecycle badges (Draft/In Review/Published/Archived) with color-coded status indicators"
  - [ ] 6.7 Follow frappe-ui patterns and WCAG 2.1 AA accessibility (NFR-U-04): include ARIA labels on badges

- [ ] Task 7 — Write unit tests for workflow transitions and visibility rules (AC: #10)
  - [ ] 7.1 Open (or create) `helpdesk/helpdesk/doctype/hd_article/test_hd_article.py`
  - [ ] 7.2 Write `test_article_default_status_is_draft` — assert new article defaults to `Draft`
  - [ ] 7.3 Write `test_submit_for_review_notifies_reviewers` — mock `frappe.sendmail`, trigger "Submit for Review" workflow action, assert sendmail called with reviewer emails
  - [ ] 7.4 Write `test_approve_publishes_article_and_notifies_author` — trigger "Approve" action from `In Review`, assert `status == "Published"` and `published_on` is set, assert author notification sent
  - [ ] 7.5 Write `test_request_changes_returns_to_draft_with_comment` — trigger "Request Changes" with a comment, assert `status == "Draft"`, `reviewer_comment` is set, author notification sent
  - [ ] 7.6 Write `test_reject_archives_article` — trigger "Reject", assert `status == "Archived"`
  - [ ] 7.7 Write `test_non_agent_cannot_access_in_review_article` — call `get_article()` as guest user for an `In Review` article, assert `frappe.PermissionError` raised
  - [ ] 7.8 Write `test_agent_can_access_in_review_article` — call `get_article()` as agent user for an `In Review` article, assert it returns successfully
  - [ ] 7.9 Write `test_get_category_articles_returns_only_published` — create Draft, In Review, Published, Archived articles in same category, call `get_category_articles()`, assert only Published is in results
  - [ ] 7.10 Run tests with: `bench --site <site> run-tests --module helpdesk.helpdesk.doctype.hd_article.test_hd_article`

## Dev Notes

### Architecture Patterns

- **Frappe Workflow Integration:** Frappe Workflow is the mandated mechanism for HD Article lifecycle (FR-KB-01). Create a `Workflow` document JSON in the `helpdesk/fixtures/` directory (preferred) so it is auto-imported on `bench migrate` via the `fixtures` list in `hooks.py`. Alternatively, create it in the DocType folder. Do NOT manually manipulate the `status` field via Python logic for state transitions — let the Frappe Workflow engine govern transitions.
  - Frappe Workflow JSON structure: `doctype: "Workflow"`, `document_type: "HD Article"`, `workflow_state_field: "status"`, `states: [...]`, `transitions: [...]`
  - Workflow `doc_status` values: 0 = saved (Draft/In Review), 1 = submitted (Published), 2 = cancelled (Archived)

- **`on_workflow_action` Hook Pattern:** Use the `on_workflow_action` controller method (called by Frappe after a workflow transition) to trigger notifications. The signature is `def on_workflow_action(self, action: str)`. The `action` string matches the transition action label (e.g., `"Submit for Review"`, `"Approve"`, `"Request Changes"`, `"Reject"`).

- **Email Notifications via `frappe.sendmail()`:** All notification emails must use `frappe.sendmail()` with translatable strings. Use `frappe._()` for message strings. Do not use hardcoded HTML templates for MVP — plain-text or simple HTML via `frappe.render_template()` is acceptable.

- **HD Settings Single DocType Pattern:** HD Settings is a Single DocType — use `frappe.get_single("HD Settings")` on the backend to read the `kb_reviewers` child table. Never use `frappe.get_doc("HD Settings", "HD Settings")`. See AR-06 and existing pattern in `hd_settings.py`.

- **Child DocType for Reviewers:** The `HD KB Reviewer` child DocType enables a configurable list of reviewers. This is the simplest approach for Phase 1 vs. per-category reviewers (simpler to configure, no per-category complexity). Per-category reviewer assignment is deferred to Phase 2.

- **Customer Portal Filtering (Already Implemented):** The `knowledge_base.py` API already correctly filters portal responses to `Published` only — `get_article()` throws `PermissionError` for non-Published articles when caller is not an agent, and `get_category_articles()` / `get_categories()` explicitly filter `status == "Published"`. Story 5.1 must verify these filters extend to `In Review` (they will, as `In Review != Published`). No new filter logic needed for existing endpoints, only for `search.py`.

- **ADR-01 (Extend HD Article, not new DocType):** All additions (`reviewer_comment` field, `kb_reviewers` in Settings) follow the additive pattern — no breaking changes to existing HD Article records.

- **AR-04 (Modify DocType JSON directly, not Custom Fields):** All field additions to `hd_article.json` and `hd_settings.json` must be made in the source JSON files, not via the Frappe UI Custom Fields mechanism.

- **AR-05 (Patches in `helpdesk/patches/v1_phase1/`):** Both the `add_in_review_status_to_hd_article` and `add_kb_settings_to_hd_settings` patches must be placed in this directory.

### Files to Create / Modify

| Action | Path | Notes |
|--------|------|-------|
| Modify | `helpdesk/helpdesk/doctype/hd_article/hd_article.json` | Add `In Review` to status options; add `reviewer_comment` Text field |
| Modify | `helpdesk/helpdesk/doctype/hd_article/hd_article.py` | Add `on_workflow_action`, notification helper methods |
| Create | `helpdesk/helpdesk/doctype/hd_article/hd_article_review_workflow.json` | Frappe Workflow definition (or place in `fixtures/`) |
| Create | `helpdesk/helpdesk/doctype/hd_kb_reviewer/` | New child DocType: `__init__.py`, `hd_kb_reviewer.json`, `hd_kb_reviewer.py` |
| Modify | `helpdesk/helpdesk/doctype/hd_settings/hd_settings.json` | Add KB section with `kb_reviewers` Table field |
| Modify | `helpdesk/helpdesk/doctype/hd_settings/hd_settings.py` | Add `get_kb_reviewer_emails()` helper |
| Modify | `helpdesk/api/knowledge_base.py` | Verify/extend portal filters; review `search.py` for article search |
| Modify | `helpdesk/search.py` | Ensure article search excludes non-Published for non-agents |
| Create | `desk/src/components/knowledge-base/ArticleStatusBadge.vue` | Color-coded badge component |
| Modify | `desk/src/pages/knowledge-base/Articles.vue` | Integrate ArticleStatusBadge |
| Modify | `desk/src/pages/knowledge-base/Article.vue` | Show badge on article detail |
| Create | `helpdesk/patches/v1_phase1/add_in_review_status_to_hd_article.py` | Migration patch |
| Create | `helpdesk/patches/v1_phase1/add_kb_settings_to_hd_settings.py` | Migration patch |
| Modify | `helpdesk/patches.txt` | Register both new patches |
| Modify | `helpdesk/hooks.py` | Add `fixtures` entry for workflow (if using fixtures approach); add scheduler event if needed |
| Modify | `helpdesk/helpdesk/doctype/hd_article/test_hd_article.py` | Add workflow transition unit tests |

### Testing Standards

- Minimum 80% unit test coverage on all new controller methods (NFR-M-01).
- Use `frappe.tests.utils.FrappeTestCase` as base class.
- Mock `frappe.sendmail` in notification tests using `unittest.mock.patch`.
- Tests must clean up created HD Article records and reset HD Settings `kb_reviewers` via `addCleanup`.
- Run full test module: `bench --site <site> run-tests --module helpdesk.helpdesk.doctype.hd_article.test_hd_article`

### Constraints

- **Do NOT break existing articles** — `Draft`, `Published`, and `Archived` records must continue to function identically after migration (AR-04 additive-only rule).
- **Do NOT bypass Frappe Workflow transitions** — the `status` field must ONLY be changed via workflow actions, not via direct `frappe.db.set_value("HD Article", name, "status", ...)` in new code.
- **Backward compatibility:** The Frappe Workflow must handle articles already in `Published` state (workflow state must be set to `Published` on existing records during migration if `is_active=1` workflow is applied).
- **i18n:** All user-facing labels, button text, and email subjects must use `frappe._()` in Python and `__()` in JS (Architecture Enforcement Guideline #7).
- **Security:** `In Review` articles must NEVER appear in customer portal or guest-accessible API responses (NFR-SE-01 spirit, applied to KB).

### Project Structure Notes

- **DocType module pattern:** New `HD KB Reviewer` child DocType follows the standard path: `helpdesk/helpdesk/doctype/hd_kb_reviewer/hd_kb_reviewer.{json|py}` [Source: architecture.md#Naming Patterns]
- **Fixtures approach for Workflow:** Frappe Workflow documents can be exported as fixtures (`bench export-fixtures`) and placed in `helpdesk/fixtures/`. Add `{"dt": "Workflow", "filters": [["document_type", "=", "HD Article"]]}` to the `fixtures` list in `hooks.py` to auto-import on `bench migrate`. [Source: Frappe Framework docs — Fixtures]
- **Frontend component placement:** New `ArticleStatusBadge.vue` goes in `desk/src/components/knowledge-base/` alongside existing `ArticleCard.vue` and `CategoryFolder.vue` [Source: architecture.md#ADR-09, existing codebase structure]
- **Existing status column in `default_list_data()`:** The `hd_article.py` already returns `"type": "status"` column for the list view — the badge rendering may already be partially handled by frappe-ui's `ListView`; verify whether a custom `ArticleStatusBadge.vue` is needed or if configuring the existing status column with color mappings is sufficient.
- **No conflicts detected:** Story 5.1 is self-contained within the KB epic. Story 5.2 (Article Versioning) will create `HD Article Version` DocType separately. Story 5.3 (Review Dates) will add `review_date` field to HD Article after this story ships.

### References

- FR-KB-01 (Article review workflow): [Source: _bmad-output/planning-artifacts/epics.md#Story 5.1]
- UX-DR-10 (Article lifecycle badges): [Source: _bmad-output/planning-artifacts/epics.md#UX Design Requirements]
- NFR-M-01 (80% unit test coverage): [Source: _bmad-output/planning-artifacts/epics.md#Non-Functional Requirements]
- NFR-U-04 (WCAG 2.1 AA): [Source: _bmad-output/planning-artifacts/epics.md#Non-Functional Requirements]
- ADR-02 (HD Article with `workflow_state` / `HD Article Version` DocType): [Source: _bmad-output/planning-artifacts/architecture.md#ADR-02]
- AR-04 (Modify DocType JSON directly): [Source: _bmad-output/planning-artifacts/epics.md#Additional Requirements]
- AR-05 (Migration patches in `helpdesk/patches/v1_phase1/`): [Source: _bmad-output/planning-artifacts/epics.md#Additional Requirements]
- AR-06 (Feature flags in HD Settings): [Source: _bmad-output/planning-artifacts/epics.md#Additional Requirements]
- Scheduler event for review reminders: [Source: _bmad-output/planning-artifacts/architecture.md#ADR-12 — `helpdesk.helpdesk.doctype.hd_article.review_reminder.send_review_reminders`]
- HD Article existing implementation: `helpdesk/helpdesk/doctype/hd_article/hd_article.{json|py}`
- Knowledge Base API: `helpdesk/api/knowledge_base.py`
- HD Settings DocType: `helpdesk/helpdesk/doctype/hd_settings/hd_settings.{json|py}`
- Frontend KB components: `desk/src/pages/knowledge-base/`, `desk/src/components/knowledge-base/`

## Dev Agent Record

### Agent Model Used

Claude Sonnet 4.5 (create-story workflow)

### Debug Log References

_None — story creation phase_

### Completion Notes List

_To be filled by implementing dev agent_

### File List

_To be filled by implementing dev agent upon completion_
