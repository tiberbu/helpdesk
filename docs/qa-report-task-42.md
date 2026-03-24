# QA Report: Task #42 — Story 5.1: Article Review Workflow

**QA Date:** 2026-03-24
**QA Depth:** 1/1 (max depth)
**Story File:** `_bmad-output/implementation-artifacts/story-42-story-5-1-article-review-workflow.md`

## Test Environment

- Site: helpdesk.localhost:8004
- User: Administrator (password: admin)
- Unit tests: 21/21 passing
- Playwright MCP: Not available in environment; API-based and code review testing used

## Acceptance Criteria Results

### AC1: Article lifecycle: Draft > In Review > Published > Archived via Frappe Workflow
**Result: PASS**

Tested full lifecycle via API:
- `submit_for_review`: Draft -> In Review (returns `{"status": "In Review"}`)
- `approve_article`: In Review -> Published (DB confirmed status=Published)
- `archive_article`: Published -> Archived (returns `{"status": "Archived"}`)
- `request_changes`: In Review -> Draft with comment (DB confirmed status=Draft, reviewer_comment set)

Status field has all four options: `Draft\nIn Review\nPublished\nArchived`

21 unit tests pass covering all transitions and edge cases.

### AC2: Submit for Review moves Draft to In Review, configured reviewers receive email notification
**Result: PASS (with caveat — see P1 below)**

- `submit_for_review` API correctly transitions Draft -> In Review
- `reviewer_comment` is cleared on re-submit
- Email notification code exists in `_notify_reviewers_for_review()` and correctly reads from `HD Settings.kb_reviewers`
- When no reviewers configured, notification is skipped gracefully (no crash)
- `HD KB Reviewer` child DocType created with `user` Link field to User

### AC3: Reviewer can Approve (Published), Request Changes (Draft with comments), Reject (Archived)
**Result: PARTIAL PASS — P1 issue with email notifications crashing API responses**

- **Approve**: State correctly changes to Published. API returns HTTP 500 due to email crash, but DB state is committed.
- **Request Changes**: State correctly changes to Draft. `reviewer_comment` is set. API returns HTTP 500 due to email crash, but DB state is committed.
- **Reject**: State correctly changes to Archived. API returns HTTP 500 due to email crash, but DB state is committed.
- Permission checks work: `_require_reviewer_role()` enforces HD Admin or System Manager role.
- Validation works: empty comment rejected, wrong-state transitions rejected.
- Frontend correctly shows reviewer feedback box (amber) for Draft articles with `reviewer_comment`.

### AC4: Only Published articles appear in customer portal and public KB
**Result: PASS**

- `get_category_articles()` filters by `status: "Published"` — verified returns 1 article when Published, 0 when Archived or In Review
- `get_categories()` counts only Published articles
- `get_article()` denies non-agent access to non-Published articles (unit test: `test_get_article_denies_non_agent_access_to_in_review`)
- `get_article()` allows agent access to In Review (unit test: `test_get_article_allows_agent_access_to_in_review`)

### AC5: In Review articles visible to agents for internal reference
**Result: PASS**

- `get_agent_articles()` returns all non-Archived articles including In Review
- Verified via API: agent sees `[{"name": "o7cqrsuh30", "title": "Introduction", "status": "In Review"}]`
- Permission check: requires `is_agent()` (unit test: `test_get_agent_articles_requires_agent`)
- Excludes Archived (unit test: `test_get_agent_articles_excludes_archived`)

## Frontend Review

- **Article.vue**: Workflow-aware buttons: "Submit for Review" (Draft), "Approve/Request Changes/Reject" (In Review, admin only), "Archive" (Published, admin only). All have `onError` handlers for toast messages.
- **KnowledgeBaseAgent.vue**: `statusMap` includes all four statuses with color-coded badges (green=Published, orange=Draft, yellow=In Review, gray=Archived).
- **Reviewer feedback**: Amber feedback box shown when `reviewer_comment` is present on Draft articles.
- **Request Changes dialog**: Inline textarea form with submit/cancel buttons.
- **Reject/Archive**: Confirmation dialog before action.

## Issues Found

### P1: Email notification crashes API response for Approve, Request Changes, Reject, and Archive

**Severity: P1 (High)** — API returns HTTP 500 to frontend even though the DB state change succeeded.

**Root Cause:** The notification methods (`_notify_author_approved`, `_notify_author_changes_requested`, `_notify_author_rejected`) call `frappe.sendmail(delayed=False)` which raises `frappe.exceptions.ValidationError: Invalid Outgoing Mail Server or Port: [Errno 111] Connection refused` when no outgoing email account is configured.

The API pattern is:
```python
doc.save(ignore_permissions=True)  # <-- commits to DB
doc.on_workflow_action(ACTION)     # <-- sends email, crashes here
return {"status": doc.status}      # <-- never reached
```

**Impact:** The frontend `onError` handler shows an error toast even though the action succeeded. User must refresh to see the correct state. This will confuse users.

**Files affected:**
- `helpdesk/api/knowledge_base.py` — lines 203, 226, 245, 264 (all `on_workflow_action` calls)
- `helpdesk/helpdesk/doctype/hd_article/hd_article.py` — lines 150, 169, 205 (`frappe.sendmail(delayed=False)`)

**Fix options:**
1. Wrap `on_workflow_action` calls in try/except at the API level
2. Change `delayed=False` to `delayed=True` in all notification helpers (preferred — queues email for background sending)

## Unit Test Results

```
Ran 21 tests in 1.051s — OK

All tests passing:
- test_new_article_defaults_to_draft
- test_submit_for_review_transitions_to_in_review
- test_submit_for_review_requires_draft_status
- test_submit_for_review_requires_agent
- test_submit_for_review_clears_reviewer_comment
- test_approve_transitions_to_published
- test_approve_requires_in_review_status
- test_approve_requires_reviewer_role
- test_request_changes_transitions_to_draft_with_comment
- test_request_changes_requires_non_empty_comment
- test_request_changes_requires_reviewer_role
- test_reject_transitions_to_archived
- test_reject_requires_reviewer_role
- test_archive_transitions_to_archived
- test_archive_requires_published_status
- test_get_agent_articles_includes_in_review
- test_get_agent_articles_excludes_archived
- test_get_agent_articles_requires_agent
- test_get_article_allows_agent_access_to_in_review
- test_get_article_denies_non_agent_access_to_in_review
- test_get_category_articles_returns_only_published
```

## Summary

| AC | Result | Notes |
|----|--------|-------|
| AC1: Lifecycle states | PASS | All transitions work, 21 unit tests pass |
| AC2: Submit for Review | PASS | Correct transition, notification code present |
| AC3: Approve/Changes/Reject | PARTIAL PASS (P1) | State changes work; email crashes API response |
| AC4: Portal visibility | PASS | Only Published shown to non-agents |
| AC5: Agent In Review visibility | PASS | get_agent_articles includes In Review |

**Overall: PARTIAL PASS — 1 P1 issue found requiring fix**
