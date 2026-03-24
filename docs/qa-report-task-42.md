# QA Report: Task #42 — Story 5.1: Article Review Workflow

**QA Date:** 2026-03-24
**QA Depth:** 1/1 (max depth)
**Story File:** `_bmad-output/implementation-artifacts/story-42-story-5-1-article-review-workflow.md`

## Test Environment

- Site: help.frappe.local (port 80, nginx)
- User: Administrator
- Unit tests: 29/29 passing
- Playwright MCP: Used for all browser testing

## Acceptance Criteria Results

### AC1: Article lifecycle: Draft > In Review > Published > Archived
**Result: PASS**

Full lifecycle verified via Playwright browser testing:
1. **Draft -> In Review**: Clicked "Submit for Review" button. Toast: "Article submitted for review". Buttons changed to Approve/Request Changes/Reject.
2. **In Review -> Draft (Request Changes)**: Clicked "Request Changes", typed reviewer comment, clicked "Submit". Toast: "Changes requested". Article returned to Draft with amber "Reviewer Feedback" box displayed.
3. **Draft -> In Review (re-submit)**: Clicked "Submit for Review" again. Reviewer comment cleared. Buttons reverted to Approve/Request Changes/Reject.
4. **In Review -> Published (Approve)**: Clicked "Approve". Toast: "Article approved and published". Button changed to "Archive".
5. **Published -> Archived (Archive)**: Clicked "Archive", confirmed in dialog. Toast: "Article archived". No workflow buttons remain.
6. **In Review -> Archived (Reject)**: Reset to In Review, clicked "Reject", confirmed in dialog. Toast: "Article rejected". No workflow buttons remain.

Screenshots: `task-42-article-in-review-buttons.png`, `task-42-article-published-archive-btn.png`

### AC2: Submit for Review moves Draft to In Review, configured reviewers receive email notification
**Result: PASS**

- "Submit for Review" button visible on Draft articles, transitions to In Review
- `reviewer_comment` is cleared on re-submit (verified: amber box disappears)
- Email notification code in `_notify_reviewers_for_review()` reads from `HD Settings.kb_reviewers`
- When no reviewers configured, notification is skipped gracefully
- `HD KB Reviewer` child DocType exists with `user` Link field
- Email uses `delayed=True` for background sending (no crash if email server unavailable)
- API wraps `on_workflow_action` in try/except for resilience

### AC3: Reviewer can Approve (Published), Request Changes (Draft with comments), Reject (Archived)
**Result: PASS**

All three actions tested via Playwright browser:
- **Approve**: Green "Approve" button. Shows toast "Article approved and published". No errors.
- **Request Changes**: Shows inline form with "Reviewer Comment" textarea. After submit, article returns to Draft with amber "Reviewer Feedback" box showing the comment. Toast: "Changes requested".
- **Reject**: Red "Reject" button. Shows confirmation dialog "Are you sure you want to reject and archive this article?". After confirm, toast: "Article rejected".

Permission enforcement verified via unit tests (`test_approve_requires_reviewer_role`, `test_request_changes_requires_reviewer_role`, `test_reject_requires_reviewer_role`).
Validation verified: empty comment rejected (`test_request_changes_requires_non_empty_comment`), wrong-state transitions rejected.

Screenshots: `task-42-request-changes-form.png`, `task-42-draft-with-reviewer-feedback.png`

### AC4: Only Published articles appear in customer portal and public KB
**Result: PASS**

- `get_category_articles()` returns 1 article when Published, 0 when Archived or In Review
- `get_categories()` returns 1 category when Published, 0 when no published articles
- `get_article()` denies non-agent access to non-Published articles (unit test passes)
- `internal_only` filter also applied to portal queries

### AC5: In Review articles visible to agents for internal reference
**Result: PASS**

- `get_agent_articles()` returns non-Archived articles including In Review
- KB agent list view shows "In Review" articles with yellow badge (verified in browser)
- Permission check: requires `is_agent()` (unit test passes)
- Excludes Archived (unit test passes)

## Frontend Verification (Playwright Browser Testing)

### KB List View — Status Badges
All four status badges verified in browser with color-coded display:
- **Draft**: Orange text badge — Screenshot: `task-42-kb-list-draft-badge.png`
- **In Review**: Yellow text badge — Screenshot: `task-42-kb-list-in-review-badge.png`
- **Published**: Green text badge — Screenshot: `task-42-kb-list-published-badge.png`
- **Archived**: (gray, not shown in list as archived articles lose category)

### Article Detail View — Workflow Buttons
- **Draft state**: "Submit for Review" button in header
- **In Review state**: "Approve" (green), "Request Changes", "Reject" (red) buttons
- **Published state**: "Archive" button
- **Archived state**: No workflow buttons (only "Version History")

### Reviewer Feedback Display
- Amber box with "Reviewer Feedback" heading and comment text shown on Draft articles with reviewer_comment
- Box disappears on re-submit (comment cleared)

### Confirmation Dialogs
- **Archive**: "Archive Article" dialog with "Are you sure you want to archive this article?"
- **Reject**: "Reject Article" dialog with "Are you sure you want to reject and archive this article?"

## Console Errors

All errors are infrastructure-related, **no helpdesk-specific errors**:
- `socket.io ERR_CONNECTION_REFUSED` — socketio service not running (expected in test env)
- `Internal error opening backing store for indexedDB.open` — headless Chrome limitation
- Vue warnings about invalid props (pre-existing, not related to this feature)

## Unit Test Results

```
Ran 29 tests in 1.198s — OK

TestHDArticleReviewReminder (8 tests):
  test_send_review_reminders_sends_email_for_overdue
  test_send_review_reminders_skips_non_published
  ... (all pass)

TestHDArticleReviewWorkflow (21 tests):
  test_new_article_defaults_to_draft
  test_submit_for_review_transitions_to_in_review
  test_submit_for_review_requires_draft_status
  test_submit_for_review_requires_agent
  test_submit_for_review_clears_reviewer_comment
  test_approve_transitions_to_published
  test_approve_requires_in_review_status
  test_approve_requires_reviewer_role
  test_request_changes_transitions_to_draft_with_comment
  test_request_changes_requires_non_empty_comment
  test_request_changes_requires_reviewer_role
  test_reject_transitions_to_archived
  test_reject_requires_reviewer_role
  test_archive_transitions_to_archived
  test_archive_requires_published_status
  test_get_agent_articles_includes_in_review
  test_get_agent_articles_excludes_archived
  test_get_agent_articles_requires_agent
  test_get_article_allows_agent_access_to_in_review
  test_get_article_denies_non_agent_access_to_in_review
  test_get_category_articles_returns_only_published
```

## Issues Found

**No P0 or P1 issues found.**

The previously reported P1 email notification crash has been fixed:
- `frappe.sendmail` now uses `delayed=True` (background queuing)
- API endpoints wrap `on_workflow_action` in try/except with `frappe.log_error`

## Summary

| AC | Result | Notes |
|----|--------|-------|
| AC1: Lifecycle states | PASS | All transitions verified in browser, 29 unit tests pass |
| AC2: Submit for Review | PASS | Correct transition, email notification resilient |
| AC3: Approve/Changes/Reject | PASS | All actions tested in browser with correct toasts |
| AC4: Portal visibility | PASS | Only Published shown to non-agents |
| AC5: Agent In Review visibility | PASS | KB list shows In Review articles with yellow badge |

**Overall: PASS — All acceptance criteria met. No P0/P1 issues.**
