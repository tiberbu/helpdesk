# QA Report: Story 1.5 — @Mention Notifications in Internal Notes

**Task:** #21 (Story 1.5)
**QA Task:** #53
**Reviewer Model:** Opus (adversarial review)
**Date:** 2026-03-23
**Verdict:** CONDITIONAL PASS — core ACs work, but 14 issues found (2x P1, 5x P2, 7x P3)

---

## Acceptance Criteria Verification

### AC-1: @mention autocomplete dropdown shows matching agent names
**Result:** PASS (with caveats — see Issue #6)

**Evidence:** The `InternalNoteTextEditor.vue` component passes `:mentions="dropdown"` (line 30) sourced from `useAgentStore().dropdown`, which provides `{label: agent_name, value: email}` objects. The Tiptap editor's built-in mention extension renders the autocomplete. This was already implemented in Story 1.4.

### AC-2: Saving a note mentioning @Agent creates an in-app notification with ticket link and content preview
**Result:** PASS

**Evidence:**
- `HasMentions.notify_mentions()` (in `helpdesk/mixins/mentions.py`) extracts mention spans, creates `HD Notification` docs with `notification_type="Mention"`, `reference_ticket`, `reference_comment`, and `message` (content preview).
- `HDNotification.get_url()` returns a URL containing `/helpdesk/tickets/{ticket_id}#{comment_id}`.
- All 12 unit tests pass (verified via `bench run-tests`):
  ```
  Ran 12 tests in 6.982s — OK
  ```
- API-level verification confirms: `HDNotification.after_insert` includes `publish_realtime("helpdesk:new-notification", ...)` for real-time bell updates.

---

## Issues Found

### P1 — High Severity

#### Issue #1: Frontend bench copy NOT synced — real-time bell update is broken in deployed app
**Severity:** P1
**File:** `desk/src/stores/notification.ts`
**Description:** The `helpdesk:new-notification` socket listener added in Story 1.5 exists in the dev copy (`/home/ubuntu/bmad-project/helpdesk/desk/src/stores/notification.ts`, lines 72-75) but is **missing** from the deployed bench copy (`/home/ubuntu/frappe-bench/apps/helpdesk/desk/src/stores/notification.ts`). The diff confirms 7 lines are missing. This means the real-time notification bell update — the only new frontend code in this story — is not deployed.
**Steps to reproduce:** `diff` the two files.
**Expected:** Both copies are identical.
**Actual:** Bench copy is missing the socket listener.

#### Issue #2: Mention notifications fire for ALL comments, not just internal notes — scope creep / security concern
**Severity:** P1
**File:** `helpdesk/helpdesk/doctype/hd_ticket_comment/hd_ticket_comment.py`
**Description:** The `after_insert()` and `on_update()` hooks call `self.notify_mentions()` unconditionally — there is no check for `self.is_internal`. This means @mentions in **public comments** also generate `HD Notification` records. While arguably useful, the story is titled "**@Mention Notifications in Internal Notes**" and the ACs specifically say "internal note." If a customer's name accidentally matches a mention span in a public comment, they could receive a notification containing the full comment content. More critically, there is no gate ensuring only internal notes trigger the mention workflow, which contradicts the story scope.

### P2 — Medium Severity

#### Issue #3: Mentioned user is not validated as an agent — internal note content can leak to non-agents
**Severity:** P2
**File:** `helpdesk/mixins/mentions.py`
**Description:** `HasMentions.notify_mentions()` creates an `HD Notification` for any email found in `data-id` attributes. There is no check that the mentioned user is actually an agent. If a crafted mention span references a customer email, an `HD Notification` is created for that customer containing the full internal note content in the `message` field. This violates the NFR-SE-01 permission boundary established in Story 1.4 — internal notes should never be visible to non-agents.

#### Issue #4: Internal note content duplicated into HD Notification without access control
**Severity:** P2
**File:** `helpdesk/mixins/mentions.py`, line 30
**Description:** `values.message = self.content` copies the full HTML of the internal note into the notification doc. The `HD Notification` doctype has no `is_internal` field or agent-only permission restriction. Any user who can query `HD Notification` (e.g., via standard Frappe list API with their `user_to` filter) can read the full internal note content, even if the original comment is filtered by `is_internal` in `get_comments()`.

#### Issue #5: Mutable default argument in `new_internal_note()`
**Severity:** P2
**File:** `helpdesk/helpdesk/doctype/hd_ticket/hd_ticket.py`, line 627
**Description:** `def new_internal_note(self, content: str, attachments: list[str] = [])` uses a mutable default argument — a classic Python footgun. If any code path mutates this list, the mutation persists across all future calls. Should be `attachments: list[str] | None = None` with `attachments = attachments or []` in the body.

#### Issue #6: No test for autocomplete dropdown actually rendering in the browser
**Severity:** P2
**Description:** AC-1 ("autocomplete dropdown shows matching agent names") is verified only by code inspection — there is no unit test or integration test that confirms the Tiptap mention extension actually renders a dropdown. The 12 tests only cover backend notification creation and `extract_mentions()`. The frontend behavior is untested and relies entirely on the upstream `frappe-ui` TextEditor component working correctly with the `:mentions` prop.

#### Issue #7: Email notification subject is generic and unhelpful
**Severity:** P2
**File:** `helpdesk/helpdesk/doctype/hd_notification/hd_notification.py`, line 70
**Description:** `subject="New notification"` is sent as the email subject. This is unprofessional — the user has no idea which ticket or who mentioned them without opening the email. Should include the ticket ID and mentioner's name, e.g., "Agent X mentioned you in ticket #123."

### P3 — Low Severity

#### Issue #8: No socket listener cleanup in notification store
**Severity:** P3
**File:** `desk/src/stores/notification.ts`, lines 65-75
**Description:** Both `$socket.on("helpdesk:comment-reaction-update", ...)` and `$socket.on("helpdesk:new-notification", ...)` are registered without corresponding cleanup (`$socket.off(...)`). While Pinia stores are typically singletons and survive the app lifecycle, this is a hygiene issue. If the store were ever re-initialized (e.g., HMR during development), duplicate listeners would accumulate.

#### Issue #9: No rate limiting on mention notifications
**Severity:** P3
**File:** `helpdesk/mixins/mentions.py`
**Description:** There is no throttle or rate limit on mention notifications. An agent could rapidly create many comments, each mentioning the same colleague, generating a flood of notifications and (if `skip_email_workflow` is off) emails. The dedup logic only prevents duplicates within the **same comment**, not across comments.

#### Issue #10: `extract_mentions()` does not validate email format
**Severity:** P3
**File:** `helpdesk/utils.py`, lines 117-126
**Description:** The `data-id` attribute is trusted as an email address without any validation. Empty strings, malformed values, or even XSS payloads in `data-id` would be stored as `mention.email` and used to create notification records with invalid `user_to` values.

#### Issue #11: Test tearDown is fragile — no try/except around cleanup steps
**Severity:** P3
**File:** `helpdesk/helpdesk/doctype/hd_ticket/test_mention_notifications.py`, lines 50-79
**Description:** The `tearDown` method deletes notifications, comments, tickets, and users sequentially. If any deletion fails (e.g., due to linked documents or permission errors), all subsequent cleanup steps are skipped, polluting the test database for subsequent test runs.

#### Issue #12: `get_url()` uses naive string concatenation for URL building
**Severity:** P3
**File:** `helpdesk/helpdesk/doctype/hd_notification/hd_notification.py`, lines 24-30
**Description:** `"/helpdesk/tickets/" + str(self.reference_ticket)` builds URLs via string concatenation without URL encoding. While ticket IDs are typically numeric, this is fragile. The `#` fragment for `reference_comment` is also appended raw.

#### Issue #13: Real-time event may arrive before DB commit propagates
**Severity:** P3
**File:** `helpdesk/helpdesk/doctype/hd_notification/hd_notification.py`, line 59; `desk/src/stores/notification.ts`, line 74
**Description:** The `publish_realtime` uses `after_commit=True`, but the frontend `resource.reload()` fires immediately on socket receipt with no debounce. In high-concurrency scenarios (multiple mentions in rapid succession), multiple reload calls could race, potentially causing excessive API calls or stale data display.

#### Issue #14: `after_insert` real-time event only fires for "Mention" type — inconsistent with Reaction notifications
**Severity:** P3
**File:** `helpdesk/helpdesk/doctype/hd_notification/hd_notification.py`, line 52
**Description:** The `after_insert` method only emits `helpdesk:new-notification` for `notification_type == "Mention"`. Reaction notifications (created via `notify_reaction` in `hd_ticket_comment.py`) use a different event path (`helpdesk:comment-reaction-update`) published from the comment module, not the notification module. This means if new notification types are added in the future, developers must remember to add real-time events case-by-case rather than having a generic mechanism.

---

## Regression Check

| Area | Status | Notes |
|------|--------|-------|
| Internal note creation (Story 1.4) | OK | `new_internal_note()` still sets `is_internal=True` correctly |
| Internal note visibility to non-agents | CONCERN | See Issue #3/#4 — notification leaks content |
| Comment reactions | OK | Existing reaction code unchanged |
| Public comment mentions | N/A | Mentions fire for all comments (Issue #2) |

## Console Errors

Playwright browser testing was not available (no MCP tools loaded). API-level verification was performed via bench console. No errors encountered during unit test run or API checks.

## Unit Test Results

```
Ran 12 tests in 6.982s — OK

Tests passed:
 - test_extract_mentions_returns_mentioned_email
 - test_extract_mentions_empty_content
 - test_extract_mentions_multiple
 - test_mention_in_internal_note_creates_hd_notification
 - test_mention_notification_includes_ticket_link
 - test_mention_notification_content_preview
 - test_no_notification_for_self_mention_in_internal_note
 - test_duplicate_mention_creates_only_one_notification
 - test_multiple_agents_each_get_notification
 - test_editing_note_notifies_only_new_mentions
 - test_new_internal_note_method_triggers_mention_notification
 - test_notification_format_message_for_mention
```

## Summary

The core functionality works: @mention autocomplete is wired via Tiptap's mention extension, `HasMentions` mixin correctly creates `HD Notification` docs, deduplication and self-mention prevention work, and real-time events are emitted. However, there are significant gaps:

1. **The frontend bench copy is out of sync** (P1) — the only new frontend code isn't deployed.
2. **Mention notifications are not scoped to internal notes** (P1) — they fire for all comments, contradicting the story scope.
3. **Internal note content can leak to non-agents via notifications** (P2) — no validation that mentioned users are agents, and no access control on notification content.
4. **Mutable default argument** in `new_internal_note()` (P2) — a latent bug.

The implementation took a shortcut by relying on pre-existing infrastructure (which is fine) but failed to add the guardrails that the "internal notes" scope demands.
