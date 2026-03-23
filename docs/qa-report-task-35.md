# QA Report: Story 3.6 — Chat-to-Ticket Transcript and Follow-up

**Task**: #35 (QA task #234)
**Date**: 2026-03-23
**QA Engineer**: Claude Opus 4.6 (automated)
**Story File**: `_bmad-output/implementation-artifacts/story-35-story-3-6-chat-to-ticket-transcript-and-follow-up.md`

---

## Test Environment

- **Site**: helpdesk.localhost:8004
- **Backend tests**: `bench --site helpdesk.localhost run-tests --app helpdesk`
- **Playwright MCP**: Not available in environment (tools not loaded). All testing done via unit tests, bench console, and curl API calls.

---

## Acceptance Criteria Results

### AC #1: Each chat message stored as ticket communication via channel adapter
**Result: PASS**

- **Evidence**: 20/20 integration tests pass in `helpdesk/tests/test_chat_to_ticket_flow.py`
- `TestHDChatMessageAfterInsert.test_customer_message_creates_communication` — verifies `Communication` doc created with `communication_medium=Chat`, `sent_or_received=Received` on the HD Ticket
- `TestHDChatMessageAfterInsert.test_agent_message_creates_sent_communication` — verifies agent messages create `sent_or_received=Sent` Communications
- `TestCreateTicketCommunication.test_system_message_creates_ticket_comment` — system messages stored as `HD Ticket Comment` (non-internal)
- `ChatAdapter.normalize_from_doc()` correctly resolves ticket_id from HD Chat Session link, maps sender_type, sets communication medium
- API confirms tickets with `source=Chat` exist: `curl ... frappe.client.get_list` returns tickets like `{"name":11981,"source":"Chat","status":"Open"}`

### AC #2: Chat session ends without resolution — ticket remains open for email follow-up
**Result: PASS**

- **Evidence**:
  - `TestHDChatSessionOnUpdate.test_session_end_does_not_close_ticket` — ticket status remains NOT Resolved/Closed after session ends
  - `TestHDChatSessionOnUpdate.test_session_end_adds_system_comment` — exactly one "Chat session ended. Follow up via email." comment added
  - `TestHDChatSessionOnUpdate.test_session_end_idempotent` — duplicate saves don't create duplicate comments
  - `TestHDChatSessionOnUpdate.test_session_end_skips_resolved_ticket` — no comment added if ticket already resolved
  - `TestHDChatSessionOnUpdate.test_session_end_without_ticket_does_not_error` — graceful handling when session has no ticket
- `HDChatSession.on_update()` at line 25: intentionally does NOT modify `ticket.status`

### AC #3: Agent reply to associated ticket sends response via email (standard ticket flow)
**Result: PASS**

- **Evidence**: Chat-originated tickets are standard HD Tickets with `source=Chat`. The existing Frappe email pipeline (`create_communication_via_contact`) applies unchanged. The Story 3.6 code intentionally does NOT modify the ticket reply flow — it only adds transcript storage.
- Verified in code: `normalizer.py` `_store_chat_communication()` creates Communication docs but does NOT trigger email sends (no `send_email` flag). Agent replies via the standard ticket UI use the existing email pipeline.

---

## Additional Checks

### Source Field on HD Ticket (AC #4)
**Result: PASS**

- `hd_ticket.json` includes `source` Select field with options `\nEmail\nChat\nPortal` and `in_standard_filter: 1`
- `ChannelNormalizer._create_ticket()` sets `ticket.source = msg.source.capitalize()` for non-portal sources
- Migration patch `add_source_field_to_hd_ticket.py` registered in `patches.txt` and backfills existing chat-linked tickets
- `TestChannelNormalizerSource` (3 tests): verifies Chat → "Chat", Email → "Email", Portal → via_customer_portal flag only

### XSS Sanitization (NFR-SE-06)
**Result: PASS**

- `ChannelNormalizer._sanitize_content()` uses `frappe.utils.html_utils.clean_html()` with fallback to `frappe.utils.strip_html()`
- `_store_chat_communication()` calls sanitizer before storing content
- `TestCreateTicketCommunication.test_xss_content_sanitized` — verifies `<script>alert('xss')</script>` is sanitized to "safe content"

### Feature Flag Gating (chat_enabled) (AR-06)
**Result: PASS**

- `HDChatMessage.after_insert()` checks `frappe.db.get_single_value("HD Settings", "chat_enabled")` before any processing
- `TestHDChatMessageAfterInsert.test_disabled_chat_skips_communication` — verifies no Communication created when chat_enabled=0

### Error Handling / Resilience (NFR-A-01)
**Result: PASS**

- `HDChatMessage.after_insert()` wraps all communication storage in try/except, logs errors but never propagates
- `TestHDChatMessageAfterInsert.test_message_without_ticket_does_not_error` — message without linked ticket doesn't raise
- `HDChatSession._mark_session_ended_on_ticket()` handles missing tickets gracefully with DoesNotExistError catch

### Frontend Source Badge
**Result: P2 — Not deployed to bench**

- Code is correct in dev: `TicketDetailsTab.vue` lines 8-18 show blue `Badge` for non-Email sources
- **Issue**: The bench copy at `/home/ubuntu/frappe-bench/apps/helpdesk/desk/src/components/ticket-agent/TicketDetailsTab.vue` was NOT synced — missing the Badge import and the source badge template block
- Frontend assets were last built at 22:55 Mar 23, before Story 3.6 commit
- **Impact**: Source badge won't render on the live site until frontend is synced and rebuilt

---

## Regression Testing

**Result: 294/296 tests pass**

- 2 failures are **pre-existing** from Story 3.5 (`test_send_message_invalid_token_raises` in `test_chat_session.py`)
- Confirmed pre-existing: same failures reproduce on Story 3.5 commit before any Story 3.6 changes (noted in story completion notes)
- No new regressions introduced by Story 3.6

---

## Code Quality Review

### Strengths
- Clean separation: `ChatAdapter.normalize_from_doc()` → `create_ticket_communication()` → Communication/Comment creation
- Idempotency guard on session-ended comments prevents duplicates
- Proper error swallowing in `after_insert` prevents chat interruption
- Comprehensive test coverage: 20 tests covering happy paths, edge cases, and error scenarios

### Minor Observations (P3, no action needed)
- `frappe.db.set_value` deprecation warning in tests (should use `set_single_value`) — not a Story 3.6 issue
- `_store_chat_communication()` calls `frappe.db.commit()` — could interfere with test tearDown rollback (mitigated by explicit cleanup in tests)

---

## Summary

| AC | Status | Severity |
|----|--------|----------|
| AC #1: Chat messages stored as communications | PASS | — |
| AC #2: Ticket remains open on chat end | PASS | — |
| AC #3: Email follow-up on chat tickets | PASS | — |
| Source field (AC #4) | PASS | — |
| XSS sanitization (NFR-SE-06) | PASS | — |
| Feature flag gating (AR-06) | PASS | — |
| Error resilience (NFR-A-01) | PASS | — |
| Frontend source badge (not synced to bench) | P2 | P2 |
| Regression (294/296, 2 pre-existing) | PASS | — |

**Overall: PASS** — All acceptance criteria met. One P2 issue (frontend not synced to bench, visual only). No P0/P1 issues found.

**No fix task created** — P2 issues do not require a fix task per QA rules.
