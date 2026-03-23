# Story 5.3: Review Dates and Expiry Reminders

Status: ready-for-dev

## Story

As a KB manager,
I want review dates on articles with automated reminders,
so that content is periodically verified for accuracy.

## Acceptance Criteria

1. **[review_date Auto-Set on Published Transition — Schema]** Given the HD Article DocType, when a developer inspects the schema, then a `review_date` field of type `Date` (label: "Review Date") and a `reviewed_by` field of type `Link → User` (label: "Reviewed By") exist on the DocType. The `review_date` field is not required and is editable by KB managers and admins.

2. **[review_date Auto-Set on Published Transition — Logic]** Given an article transitions to `Published` state via the HD Article Review Workflow (Story 5.1), when the `on_workflow_action` handler fires with action `"Approve"`, then `review_date` is automatically set to 90 days from the publication date (i.e., `frappe.utils.add_days(frappe.utils.today(), 90)`). The 90-day interval must be configurable via a new `kb_review_period_days` Int field (default: 90) in HD Settings under the "Knowledge Base" section.

3. **[review_date Configurable via HD Settings]** Given an administrator opens HD Settings and navigates to the "Knowledge Base" section, when they change `kb_review_period_days` to a different integer (e.g., 60 or 180), then subsequent article publications set `review_date` to `today + kb_review_period_days` days. The field must have a minimum value of 1 and default of 90.

4. **[Daily Review Reminder Job — Overdue Articles]** Given articles exist whose `review_date` has passed (i.e., `review_date < today`) and whose `status` is `Published`, when the daily review reminder background job runs, then the article's author (`HD Article.author` field, Link → User) receives an email notification containing:
   - Subject: "KB Article Review Reminder: [article title]"
   - Body: article title, review_date, a direct link to the article in the agent workspace
   - The email must use `frappe.sendmail()` with translatable strings via `frappe._()`.

5. **[Daily Review Reminder Job — Scheduler Registration]** Given the daily review reminder function is implemented at `helpdesk.helpdesk.doctype.hd_article.review_reminder.send_review_reminders`, when `hooks.py` scheduler events are inspected, then a `daily` entry for that function is present so it runs once per day automatically.

6. **[Daily Review Reminder Job — No Duplicate Emails]** Given an article is overdue for review and a reminder email was already sent today, when the daily job runs again (e.g., if manually triggered), then no duplicate email is sent. The implementation must track the last reminder sent date (a `last_reminder_sent` Date field on HD Article, hidden, not in list view) and skip articles where `last_reminder_sent == today`.

7. **[Dashboard Widget — Articles Due for Review]** Given overdue or upcoming-within-7-days articles exist (i.e., `review_date <= today + 7 days` and `status == "Published"`), when a manager views the "Articles Due for Review" dashboard widget, then the widget displays:
   - A list of articles grouped or sorted by urgency (overdue first, then upcoming)
   - For each article: title, review_date, author name, and days overdue/days remaining
   - Quick action buttons: "Mark Reviewed" (resets review_date to today + kb_review_period_days and sets reviewed_by to current user), "Edit" (navigates to the article edit page), "Archive" (triggers the Published → Archived workflow transition)

8. **[Dashboard Widget — Mark Reviewed Action]** Given a manager clicks "Mark Reviewed" on an article in the dashboard widget, when the action completes, then:
   - `review_date` is updated to `today + kb_review_period_days` days
   - `reviewed_by` is set to the currently logged-in user
   - `last_reminder_sent` is cleared (set to null)
   - The article disappears from the widget immediately (optimistic UI update or refresh)

9. **[Dashboard Widget — Performance]** Given up to 1000 published articles exist, when the dashboard widget data API is called, then it responds within 1 second (NFR-P-07). The query must use indexed fields (`status`, `review_date`) and limit results to articles where `review_date` is not null and `review_date <= today + 7 days`.

10. **[Migration Patch — New Article Fields]** Given a pre-existing Frappe Helpdesk installation with HD Article records, when the Phase 1 migration patch runs, then the `review_date`, `reviewed_by`, and `last_reminder_sent` fields are added to the HD Article schema without altering any existing article content. No `review_date` is back-filled for existing articles (they start with null review_date and receive one only upon next publish/mark-reviewed action).

11. **[Unit Tests — Review Date Logic and Reminder Scheduling]** Given the implementation is complete, when the test suite runs, then unit tests pass covering:
   - (a) Publishing an article sets `review_date` to today + `kb_review_period_days`
   - (b) Changing `kb_review_period_days` to 60 causes a newly published article to get `review_date = today + 60`
   - (c) `send_review_reminders` sends email to the author of each overdue Published article
   - (d) `send_review_reminders` skips articles where `last_reminder_sent == today`
   - (e) `send_review_reminders` skips articles that are not `Published` (Draft, In Review, Archived)
   - (f) "Mark Reviewed" API updates `review_date`, sets `reviewed_by`, clears `last_reminder_sent`
   - (g) Dashboard widget API returns only Published articles with `review_date <= today + 7 days`
   Minimum 80% coverage on all new controller methods and API functions (NFR-M-01).

## Tasks / Subtasks

- [ ] Task 1 — Add `review_date`, `reviewed_by`, and `last_reminder_sent` fields to HD Article DocType JSON (AC: #1, #6, #10)
  - [ ] 1.1 Open `helpdesk/helpdesk/doctype/hd_article/hd_article.json`
  - [ ] 1.2 Add a `Section Break` field (label: "Review Information") before the new fields, with `collapsible: 1`
  - [ ] 1.3 Add `Date` field `review_date` (label: "Review Date", in_list_view: 0, bold: 0, no_copy: 1)
  - [ ] 1.4 Add `Link` field `reviewed_by` (label: "Reviewed By", options: "User", read_only: 1, no_copy: 1)
  - [ ] 1.5 Add `Date` field `last_reminder_sent` (label: "Last Reminder Sent", hidden: 1, no_copy: 1) — used internally to prevent duplicate reminders
  - [ ] 1.6 Create migration patch `helpdesk/patches/v1_phase1/add_review_date_fields_to_hd_article.py` with `execute()` that safely adds the new columns without altering existing records
  - [ ] 1.7 Register the patch in `helpdesk/patches.txt` after the Story 5.1 and 5.2 patches

- [ ] Task 2 — Add `kb_review_period_days` setting to HD Settings (AC: #2, #3)
  - [ ] 2.1 Open `helpdesk/helpdesk/doctype/hd_settings/hd_settings.json`
  - [ ] 2.2 Locate the "Knowledge Base" section added by Story 5.1 (containing `kb_reviewers`)
  - [ ] 2.3 Add `Int` field `kb_review_period_days` (label: "Article Review Period (Days)", default: 90, description: "Number of days after publication before an article is due for review")
  - [ ] 2.4 Open `helpdesk/helpdesk/doctype/hd_settings/hd_settings.py` and add a helper method `get_kb_review_period_days()` → returns `frappe.get_single("HD Settings").kb_review_period_days or 90`
  - [ ] 2.5 Create (or extend) migration patch for HD Settings: `helpdesk/patches/v1_phase1/add_kb_review_settings_to_hd_settings.py` with `execute()` that adds the `kb_review_period_days` field to the live Settings record with default 90 if it does not already exist

- [ ] Task 3 — Implement auto-set of `review_date` on Published transition (AC: #2)
  - [ ] 3.1 Open `helpdesk/helpdesk/doctype/hd_article/hd_article.py`
  - [ ] 3.2 Locate the `on_workflow_action(self, action)` method added by Story 5.1
  - [ ] 3.3 Add a branch for `action == "Approve"` (the Published transition): call `self._set_review_date()`
  - [ ] 3.4 Implement `_set_review_date(self)`: fetch `kb_review_period_days` from `hd_settings.get_kb_review_period_days()`, compute `review_date = frappe.utils.add_days(frappe.utils.today(), period)`, set `self.review_date = review_date`, do NOT `self.save()` (the workflow engine will save the document after the action)
  - [ ] 3.5 Ensure `last_reminder_sent` is NOT reset here (it only resets on "Mark Reviewed")

- [ ] Task 4 — Implement the daily review reminder background job (AC: #4, #5, #6)
  - [ ] 4.1 Create module file `helpdesk/helpdesk/doctype/hd_article/review_reminder.py`
  - [ ] 4.2 Implement `send_review_reminders()` function:
    - [ ] 4.2.1 Query all HD Article records where `status = "Published"`, `review_date IS NOT NULL`, `review_date < CURDATE()` (or use `frappe.utils.today()`), and (`last_reminder_sent IS NULL` OR `last_reminder_sent != today`)
    - [ ] 4.2.2 For each result, fetch the author's email via `frappe.get_value("User", article.author, "email")` (or the author field directly if it is already an email)
    - [ ] 4.2.3 Send reminder email using `frappe.sendmail(recipients=[author_email], subject=frappe._("KB Article Review Reminder: {0}").format(article.title), message=<rendered body with article title, review_date, link>)`
    - [ ] 4.2.4 Update `last_reminder_sent` to today via `frappe.db.set_value("HD Article", article.name, "last_reminder_sent", frappe.utils.today())` to prevent duplicate sends
    - [ ] 4.2.5 Wrap entire function in try/except to prevent one failing article from blocking reminders for others; log errors with `frappe.log_error()`
  - [ ] 4.3 Open `helpdesk/hooks.py` and add an entry under `scheduler_events["daily"]` for `"helpdesk.helpdesk.doctype.hd_article.review_reminder.send_review_reminders"` (Architecture ADR-12 daily scheduler pattern)

- [ ] Task 5 — Create the "Articles Due for Review" dashboard widget backend API (AC: #7, #8, #9)
  - [ ] 5.1 Create `helpdesk/api/kb_review.py` module (or add to existing `helpdesk/api/article.py` if present)
  - [ ] 5.2 Implement `@frappe.whitelist() get_articles_due_for_review()`:
    - [ ] 5.2.1 Compute `cutoff_date = frappe.utils.add_days(frappe.utils.today(), 7)` (articles due within 7 days or already overdue)
    - [ ] 5.2.2 Query `frappe.db.get_all("HD Article", filters={"status": "Published", "review_date": ["<=", cutoff_date]}, fields=["name", "title", "review_date", "author", "reviewed_by"], order_by="review_date asc", ignore_permissions=False)` — exclude null `review_date` rows with an additional filter
    - [ ] 5.2.3 Compute `days_overdue` / `days_remaining` for each article based on `(today - review_date).days`
    - [ ] 5.2.4 Return `{"overdue": [...], "upcoming": [...]}` split on whether `review_date < today`
    - [ ] 5.2.5 Add `frappe.has_permission("HD Article", "read", throw=True)` at function entry
  - [ ] 5.3 Implement `@frappe.whitelist() mark_article_reviewed(article_name: str)`:
    - [ ] 5.3.1 Validate the article exists and caller has Write permission on it
    - [ ] 5.3.2 Fetch `kb_review_period_days` from HD Settings
    - [ ] 5.3.3 Update `review_date = today + period`, `reviewed_by = frappe.session.user`, `last_reminder_sent = None` via `frappe.db.set_value()` (bulk set_value to avoid triggering unnecessary workflow hooks)
    - [ ] 5.3.4 Return updated article data
  - [ ] 5.4 Implement `@frappe.whitelist() archive_article(article_name: str)`:
    - [ ] 5.4.1 Load the article doc and apply the `"Archive"` workflow action via `frappe.model.workflow.apply_workflow(doc, "Archive")` (requires Published → Archived transition from Story 5.1 workflow)
    - [ ] 5.4.2 Return `{"success": True}`

- [ ] Task 6 — Create the "Articles Due for Review" frontend dashboard widget (AC: #7, #8, #9)
  - [ ] 6.1 Create `desk/src/components/kb/ArticlesDueForReview.vue` widget component
  - [ ] 6.2 Implement data fetching using `createResource` calling `helpdesk.api.kb_review.get_articles_due_for_review`
  - [ ] 6.3 Render two sections: "Overdue" (red/orange badge) and "Due Within 7 Days" (yellow badge)
  - [ ] 6.4 For each article row, display: title (linked to agent KB article page), review_date formatted via dayjs, author name, days overdue (negative) or days remaining (positive)
  - [ ] 6.5 Implement "Mark Reviewed" button: calls `mark_article_reviewed` API, optimistically removes the article from the list, shows success toast
  - [ ] 6.6 Implement "Edit" button: navigates to `/helpdesk/knowledge-base/{article_name}/edit` (or equivalent agent workspace article edit route)
  - [ ] 6.7 Implement "Archive" button: calls `archive_article` API with confirmation dialog ("Archive this article?"), removes from list on success, shows toast
  - [ ] 6.8 Show empty state ("All articles are up to date") when no overdue/upcoming articles exist
  - [ ] 6.9 Handle loading state with frappe-ui skeleton loader; handle error state with a retry button
  - [ ] 6.10 Follow frappe-ui component patterns (Button, Badge, Tooltip), WCAG 2.1 AA (NFR-U-04), keyboard navigation (NFR-U-05)
  - [ ] 6.11 Register the widget in the agent workspace dashboard page (add to the list of available widgets in the home/dashboard page configuration)

- [ ] Task 7 — Write unit tests for review date logic and reminder scheduling (AC: #11)
  - [ ] 7.1 Open (or create) `helpdesk/helpdesk/doctype/hd_article/test_hd_article.py` (extends existing tests from Stories 5.1/5.2)
  - [ ] 7.2 Write `test_publish_sets_review_date_to_default_period` — trigger "Approve" workflow action on an In Review article, assert `review_date == today + 90`
  - [ ] 7.3 Write `test_publish_uses_custom_review_period` — set `kb_review_period_days = 60` in HD Settings, trigger "Approve", assert `review_date == today + 60`; restore Settings in `addCleanup`
  - [ ] 7.4 Write `test_send_review_reminders_emails_overdue_authors` — create a Published article with `review_date = yesterday`, call `send_review_reminders()`, assert `frappe.sendmail` was called with the author's email; assert `last_reminder_sent` is set to today
  - [ ] 7.5 Write `test_send_review_reminders_skips_if_sent_today` — create a Published article with `review_date = yesterday` and `last_reminder_sent = today`, call `send_review_reminders()`, assert `frappe.sendmail` was NOT called
  - [ ] 7.6 Write `test_send_review_reminders_skips_non_published` — create Draft and Archived articles with past `review_date`, call `send_review_reminders()`, assert no email sent
  - [ ] 7.7 Write `test_mark_article_reviewed_resets_review_date` — call `mark_article_reviewed(article_name)`, assert `review_date == today + kb_review_period_days`, `reviewed_by == frappe.session.user`, `last_reminder_sent == None`
  - [ ] 7.8 Write `test_get_articles_due_for_review_returns_correct_articles` — create: (a) Published, overdue, (b) Published, due in 5 days, (c) Published, due in 10 days, (d) Draft, overdue; call `get_articles_due_for_review()`; assert (a) and (b) are in results, (c) and (d) are NOT
  - [ ] 7.9 Run tests with: `bench --site <site> run-tests --module helpdesk.helpdesk.doctype.hd_article.test_hd_article`

## Dev Notes

### Architecture Patterns

- **Dependency on Story 5.1 (Article Review Workflow):** Story 5.3 depends on Story 5.1 being complete. The `on_workflow_action` method in `hd_article.py` must already exist (Story 5.1 added it for reviewer notifications). Story 5.3 extends that same method with a branch for the "Approve" action to set `review_date`. Do NOT duplicate the method — add to the existing one.

- **Story 5.2 Coexistence (Article Versioning):** Story 5.2 creates `HD Article Version` snapshots on content changes. The `review_date`, `reviewed_by`, and `last_reminder_sent` fields are metadata fields — they should NOT trigger a version snapshot by themselves. If the versioning logic (Story 5.2) snapshots all field changes, exclude these metadata fields from version comparison criteria.

- **`on_workflow_action` Extension Pattern:**
  ```python
  # hd_article.py — extend existing method from Story 5.1
  def on_workflow_action(self, action: str):
      if action == "Submit for Review":
          self._notify_reviewers_for_review()
      elif action == "Approve":
          self._notify_author_approved()
          self._set_review_date()          # Story 5.3 addition
      elif action == "Request Changes":
          self._notify_author_changes_requested(...)
      elif action == "Reject":
          self._notify_author_rejected()

  def _set_review_date(self):
      from helpdesk.helpdesk.doctype.hd_settings.hd_settings import get_kb_review_period_days
      period = get_kb_review_period_days()
      self.review_date = frappe.utils.add_days(frappe.utils.today(), period)
  ```

- **Scheduler Event Registration (ADR-12):** The architecture document explicitly names the daily scheduler path: `helpdesk.helpdesk.doctype.hd_article.review_reminder.send_review_reminders`. Create the module at exactly this path. The `hooks.py` `scheduler_events` dict already includes a `"daily"` list (per ADR-12) — append to it rather than creating a new key.
  ```python
  # hooks.py (existing structure from architecture.md ADR-12)
  scheduler_events = {
      "cron": { ... },
      "daily": [
          "helpdesk.helpdesk.doctype.hd_automation_log.cleanup.purge_old_logs",
          "helpdesk.helpdesk.doctype.hd_article.review_reminder.send_review_reminders"  # Story 5.3
      ]
  }
  ```

- **HD Settings Single DocType Pattern:** Use `frappe.get_single("HD Settings")` (NOT `frappe.get_doc("HD Settings", "HD Settings")`) to read `kb_review_period_days`. See Story 5.1 notes. The `kb_review_period_days` field should be placed in the existing "Knowledge Base" section of HD Settings (added by Story 5.1 for `kb_reviewers`).

- **`frappe.db.set_value` vs `doc.save()` for Metadata Updates:** When updating `review_date`, `reviewed_by`, and `last_reminder_sent` in the `mark_article_reviewed` API and in the `send_review_reminders` job, use `frappe.db.set_value()` rather than loading the full document and calling `doc.save()`. This avoids triggering `validate`, `on_update`, and version snapshot hooks unnecessarily, and is more performant for bulk updates in the reminder job.

- **Dashboard Widget Architecture:** The widget follows the standard Frappe Helpdesk dashboard widget pattern used by other widgets (e.g., SLA compliance widget from Story 4.3). Register it by adding a widget entry to the home page dashboard configuration in the frontend router/page setup. Use `createResource` for SWR-like caching and auto-refresh. The widget should poll or refresh on user action, not via WebSocket, since review dates are not real-time events.

- **AR-04 (Modify DocType JSON directly):** All new fields on `hd_article.json` and `hd_settings.json` must be added directly in the source JSON, not via Frappe UI Custom Fields.

- **AR-05 (Migration patches in `helpdesk/patches/v1_phase1/`):** Both `add_review_date_fields_to_hd_article.py` and `add_kb_review_settings_to_hd_settings.py` patches must go in this directory and be registered in `helpdesk/patches.txt`.

- **Email Template:** Use inline HTML in `frappe.sendmail()` for the reminder email for MVP simplicity (consistent with Story 5.1's approach). The email body should include the article title, review_date formatted as a human-readable date, and a clickable link to the agent workspace article page: `{frappe.utils.get_url()}/helpdesk/knowledge-base/{article.name}`.

- **Index Consideration:** The `review_date` and `status` fields on HD Article should be indexed in MariaDB for the dashboard widget query to meet the 1-second response time (NFR-P-07). Add `"search_index": 1` to these fields in `hd_article.json` if not already indexed.

### Files to Create / Modify

| Action | Path | Notes |
|--------|------|-------|
| Modify | `helpdesk/helpdesk/doctype/hd_article/hd_article.json` | Add `review_date` (Date), `reviewed_by` (Link→User), `last_reminder_sent` (Date, hidden) fields; add search_index to `review_date` and `status` |
| Modify | `helpdesk/helpdesk/doctype/hd_article/hd_article.py` | Extend `on_workflow_action` to call `_set_review_date()` on "Approve"; add `_set_review_date()` method |
| Create | `helpdesk/helpdesk/doctype/hd_article/review_reminder.py` | Daily reminder job: `send_review_reminders()` function |
| Modify | `helpdesk/helpdesk/doctype/hd_settings/hd_settings.json` | Add `kb_review_period_days` Int field in "Knowledge Base" section |
| Modify | `helpdesk/helpdesk/doctype/hd_settings/hd_settings.py` | Add `get_kb_review_period_days()` helper method |
| Create | `helpdesk/api/kb_review.py` | Whitelisted API: `get_articles_due_for_review`, `mark_article_reviewed`, `archive_article` |
| Create | `desk/src/components/kb/ArticlesDueForReview.vue` | Dashboard widget component |
| Modify | `desk/src/pages/home/` (dashboard page) | Register `ArticlesDueForReview` widget in dashboard widget list |
| Create | `helpdesk/patches/v1_phase1/add_review_date_fields_to_hd_article.py` | Migration patch for new article fields |
| Create | `helpdesk/patches/v1_phase1/add_kb_review_settings_to_hd_settings.py` | Migration patch for HD Settings field |
| Modify | `helpdesk/patches.txt` | Register both new patches (after Story 5.1 and 5.2 patches) |
| Modify | `helpdesk/hooks.py` | Add `send_review_reminders` to `scheduler_events["daily"]` list |
| Modify | `helpdesk/helpdesk/doctype/hd_article/test_hd_article.py` | Add review date and reminder scheduling unit tests |

### Testing Standards

- Minimum 80% unit test coverage on all new controller methods and API functions (NFR-M-01).
- Use `frappe.tests.utils.FrappeTestCase` as base class for all test classes.
- Mock `frappe.sendmail` in reminder tests using `unittest.mock.patch("frappe.sendmail")`.
- Use `unittest.mock.patch.object(frappe.utils, "today", return_value="2026-03-23")` to freeze dates in tests where date math is asserted.
- Tests must clean up created HD Article records and restored HD Settings via `addCleanup`.
- Run: `bench --site <site> run-tests --module helpdesk.helpdesk.doctype.hd_article.test_hd_article`

### Constraints

- **Do NOT set `review_date` directly via `frappe.db.set_value` during the workflow transition** — always go through `_set_review_date()` on `self` so the value is part of the document save triggered by the workflow engine.
- **Do NOT backfill `review_date`** for existing articles in the migration patch — null is intentional for legacy articles. They will get a `review_date` only when next re-published or when manually set via "Mark Reviewed".
- **Do NOT break Story 5.1 notifications** — the `_set_review_date()` call is an addition to the existing "Approve" handler, not a replacement for `_notify_author_approved()`.
- **Do NOT create a separate workflow for review reminders** — review reminders are a background scheduler job, not a Frappe Workflow state machine.
- **i18n:** All user-facing labels, email subjects, and widget text must use `frappe._()` in Python and `__()` in JS (Architecture Enforcement Guideline #7).
- **Security:** The `get_articles_due_for_review` and related APIs must check HD Article read permission before returning data. Agents should see all articles due for review; customers (non-agents) must NOT access this API.

### Project Structure Notes

- **`review_reminder.py` module path:** Must match the path registered in `hooks.py` exactly: `helpdesk/helpdesk/doctype/hd_article/review_reminder.py` → Python path `helpdesk.helpdesk.doctype.hd_article.review_reminder`. [Source: architecture.md#ADR-12]
- **API module location:** `helpdesk/api/kb_review.py` follows the existing pattern of `helpdesk/api/{feature}.py` API modules. [Source: architecture.md#ADR-08]
- **Frontend widget component placement:** `desk/src/components/kb/ArticlesDueForReview.vue` follows the `components/{domain}/` pattern. [Source: architecture.md#ADR-09]
- **HD Settings dependency:** Story 5.3 assumes Story 5.1 has already added the "Knowledge Base" section to HD Settings (with `kb_reviewers`). The `kb_review_period_days` field is added to that same section. If Story 5.1 has not shipped yet, the developer must add the section as part of this story as well.
- **Scheduler daily list:** Architecture ADR-12 defines the `scheduler_events` shape in `hooks.py`. The `"daily"` key accepts a list of Python module paths. Append the review reminder path to the list — do not replace or duplicate the key.
- **Index fields for performance:** Both `status` and `review_date` on `hd_article.json` should have `"search_index": 1`. The `status` field may already be indexed from prior stories — verify before adding a duplicate.

### References

- FR-KB-03 (Review dates with auto-set on publication, email reminders, dashboard widget): [Source: _bmad-output/planning-artifacts/epics.md#Requirements Inventory]
- Story 5.3 Epic AC: [Source: _bmad-output/planning-artifacts/epics.md#Story 5.3: Review Dates and Expiry Reminders]
- ADR-12 (Background Job Architecture / Scheduler Events): [Source: _bmad-output/planning-artifacts/architecture.md#ADR-12]
- ADR-08 (API Design for New Features): [Source: _bmad-output/planning-artifacts/architecture.md#ADR-08]
- ADR-09 (Frontend Component Organization): [Source: _bmad-output/planning-artifacts/architecture.md#ADR-09]
- AR-04 (Modify DocType JSON directly, not Custom Fields): [Source: _bmad-output/planning-artifacts/epics.md#Additional Requirements]
- AR-05 (Migration patches in `helpdesk/patches/v1_phase1/`): [Source: _bmad-output/planning-artifacts/epics.md#Additional Requirements]
- NFR-M-01 (80% unit test coverage): [Source: _bmad-output/planning-artifacts/epics.md#Non-Functional Requirements]
- NFR-P-07 (Dashboard widget load < 1 second): [Source: _bmad-output/planning-artifacts/epics.md#Non-Functional Requirements]
- NFR-U-04 (WCAG 2.1 AA): [Source: _bmad-output/planning-artifacts/epics.md#Non-Functional Requirements]
- NFR-U-05 (Full keyboard navigation): [Source: _bmad-output/planning-artifacts/epics.md#Non-Functional Requirements]
- Daily scheduler path: `helpdesk.helpdesk.doctype.hd_article.review_reminder.send_review_reminders` [Source: _bmad-output/planning-artifacts/architecture.md#ADR-12]
- HD Article existing DocType: `helpdesk/helpdesk/doctype/hd_article/hd_article.{json|py}`
- HD Settings DocType: `helpdesk/helpdesk/doctype/hd_settings/hd_settings.{json|py}`
- Story 5.1 dependency (Workflow `on_workflow_action`): `helpdesk/helpdesk/doctype/hd_article/hd_article.py`
- Knowledge Base API: `helpdesk/api/knowledge_base.py`
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
