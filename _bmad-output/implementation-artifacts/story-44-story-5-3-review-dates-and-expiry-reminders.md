# Story: Story 5.3: Review Dates and Expiry Reminders

Status: done
Task ID: mn2gcxurpjmy4n
Task Number: #44
Workflow: dev-story
Model: sonnet
Created: 2026-03-24T01:05:58.153Z

## Description

## Story 5.3: Review Dates and Expiry Reminders

As a KB manager, I want review dates on articles with automated reminders.

### Acceptance Criteria

- review_date auto-set to 90 days from publication (configurable) on Published transition
- Daily review reminder job sends email to article author when review_date has passed
- Dashboard widget shows overdue and upcoming-within-7-days articles with quick actions (Mark Reviewed, Edit, Archive)

### Tasks
- Add review_date and reviewed_by fields to HD Article DocType JSON
- Implement auto-set of review_date on Published transition
- Implement daily review reminder background job
- Add scheduler event in hooks.py for daily reminders
- Create Articles Due for Review dashboard widget
- Create migration patch for new article fields
- Write unit tests for review date logic and reminder scheduling

## Acceptance Criteria

- [x] review_date auto-set to 90 days from publication (configurable) on Published transition
- [x] Daily review reminder job sends email to article author when review_date has passed
- [x] Dashboard widget shows overdue and upcoming-within-7-days articles with quick actions (Mark Reviewed, Edit, Archive)

## Tasks / Subtasks

- [x] Add review_date and reviewed_by fields to HD Article DocType JSON
- [x] Implement auto-set of review_date on Published transition
- [x] Implement daily review reminder background job
- [x] Add scheduler event in hooks.py for daily reminders
- [x] Create Articles Due for Review dashboard widget
- [x] Create migration patch for new article fields
- [x] Write unit tests for review date logic and reminder scheduling

## Dev Notes



### References

- Task source: Claude Code Studio task #44

## Dev Agent Record

### Agent Model Used

sonnet

### Completion Notes List

- All 29 unit tests pass (including 8 new tests in `TestHDArticleReviewDates`)
- Key fix: `on_workflow_action` is called after doc save, so `_set_review_date()` must use `frappe.db.set_value` to persist — setting `self.review_date` in-memory only is insufficient
- `HD Settings` is a Single DocType (tabSingles) — the patch cannot use `has_column`/`add_column`; only `frappe.reload_doc` + `frappe.db.set_single_value` is needed
- `hooks.py` already had the scheduler entry from prior story work — no change needed
- Frontend build: 103 precache entries (up from 102), confirming new components included
- `last_reminder_sent != today_str` filter in Frappe DB also matches NULL rows in MariaDB, correctly capturing "never sent" articles

### Change Log

- 2026-03-24: Full implementation complete. All ACs satisfied. 29/29 tests pass.

### File List

**Backend (Python)**
- `helpdesk/helpdesk/doctype/hd_article/hd_article.json` — Added review_date, reviewed_by, last_reminder_sent fields + section break; search_index on status and review_date
- `helpdesk/helpdesk/doctype/hd_article/hd_article.py` — Extended `on_workflow_action` + added `_set_review_date()` using `frappe.db.set_value`
- `helpdesk/helpdesk/doctype/hd_article/review_reminder.py` — Implemented `send_review_reminders()` daily job
- `helpdesk/helpdesk/doctype/hd_article/test_hd_article.py` — Added `TestHDArticleReviewDates` with 8 tests
- `helpdesk/helpdesk/doctype/hd_settings/hd_settings.json` — Added `kb_review_period_days` Int field
- `helpdesk/helpdesk/doctype/hd_settings/hd_settings.py` — Added `get_kb_review_period_days()` method
- `helpdesk/api/kb_review.py` — New file: `get_articles_due_for_review`, `mark_article_reviewed`, `archive_article_from_widget`
- `helpdesk/patches/v1_phase1/add_review_date_fields_to_hd_article.py` — New migration patch
- `helpdesk/patches/v1_phase1/add_kb_review_settings_to_hd_settings.py` — New migration patch (Single DocType safe)
- `helpdesk/patches.txt` — Appended two new patch entries

**Frontend (Vue)**
- `desk/src/components/knowledge-base/ArticlesDueForReview.vue` — New dashboard widget component
- `desk/src/components/knowledge-base/ArticleReviewRow.vue` — New article row component with Mark Reviewed / Edit / Archive actions
- `desk/src/pages/dashboard/Dashboard.vue` — Added `<ArticlesDueForReview />` widget at bottom of charts
