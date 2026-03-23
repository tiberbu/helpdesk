# QA Report: Task #36 — Story 3.7: CSAT Survey Infrastructure and Delivery

**QA Date**: 2026-03-23
**QA Depth**: 1/1 (final)
**Tester**: Claude Opus 4.6 (automated QA)
**Test Method**: Unit tests (31 tests), bench console integration tests, code review

---

## Summary

**Overall Result: PASS**

All 6 acceptance criteria verified. 31 unit tests pass. Integration testing via bench console confirms the full CSAT flow: token generation, rating submission, single-use enforcement, comment submission, unsubscribe, and dashboard data aggregation. No P0 or P1 issues found.

---

## Acceptance Criteria Results

### AC1: Admin enables CSAT in HD Settings with configurable delay (default 24h) and frequency limit (default 7 days)
**Result: PASS**

- **Evidence**: `hd_settings.json` contains fields: `csat_enabled` (Check, default 0), `csat_delay_hours` (Int, default 24), `csat_frequency_days` (Int, default 7), `csat_token_expiry_days` (Int, default 7)
- `csat_survey_section` has `depends_on: "eval:doc.csat_enabled==1"` — settings are hidden when CSAT is disabled
- Verified via bench console: `frappe.db.get_single_value("HD Settings", "csat_enabled")` returns `1` (enabled on test site)
- `csat_unsubscribed_emails` field is JSON type, read-only — managed automatically

### AC2: On ticket resolution + delay, CSAT email sent with 1-5 star one-click rating links
**Result: PASS**

- **Evidence**: `csat_scheduler.py:send_pending_surveys()` correctly:
  - Reads `csat_delay_hours` and computes cutoff datetime (line 36)
  - Queries resolved tickets modified before the cutoff (lines 47-64)
  - Generates HMAC token and creates `HD CSAT Response` record (lines 101-118)
  - Enqueues `_send_csat_email` via `frappe.enqueue` (long queue) (lines 121-127)
- Email template `csat_survey.html` renders 5 star links (lines 45-49): `<a href="{{base_url}}/api/method/helpdesk.api.csat.submit_rating?token={{token}}&rating={{n}}">`
- Hourly cron registered in `hooks.py`: `"0 */1 * * *"` (line 53)

### AC3: Click star submits rating via single click, thank-you page confirms with optional comment field
**Result: PASS**

- **Evidence (bench console test)**:
  - Created HD CSAT Response with token, called `submit_rating(token, "4")` → rendered thank-you page
  - Verified rating stored: `frappe.db.get_value("HD CSAT Response", name, "rating")` → `4`
  - Thank-you page HTML includes textarea for optional comment and JS `sendComment()` function
  - `submit_comment(token, "Great support, thank you!")` → `{"message": "Thank you for your feedback!"}`
  - Verified comment stored: `frappe.db.get_value("HD CSAT Response", name, "comment")` → `"Great support, thank you!"`
- Star links use GET method, which is allowed (Frappe default whitelist allows GET/POST/PUT/DELETE)

### AC4: Frequency limit: no survey if customer received one in last 7 days
**Result: PASS**

- **Evidence**: `csat_scheduler.py` lines 88-98: queries `HD CSAT Response` for `customer_email` with `survey_sent_at > frequency_cutoff` and skips if found
- Unit test `test_frequency_limit_skips_recent_recipient` passes — mocks DB to simulate recent survey and verifies no new response is created
- `csat_frequency_days` is configurable (default 7)

### AC5: Unsubscribe link marks customer as unsubscribed
**Result: PASS**

- **Evidence (bench console test)**:
  - Called `unsubscribe(token)` → rendered confirmation page
  - `is_unsubscribed(email)` → `True`
  - `csat_unsubscribed_emails` in HD Settings updated to include the email
- `csat_scheduler.py` line 77: `if customer_email in unsubscribed_emails: continue` — skips unsubscribed customers
- Email template includes unsubscribe link in footer (line 63)
- Unit tests: `test_mark_unsubscribed_adds_email`, `test_mark_unsubscribed_idempotent`, `test_is_unsubscribed_*` — all pass

### AC6: HMAC-signed single-use tokens for survey links
**Result: PASS**

- **Evidence**: `helpdesk/utils.py` implements:
  - `generate_csat_token()`: creates `base64url(ticket:email:expiry).hmac_sha256_hex` token
  - `validate_csat_token()`: verifies HMAC signature (constant-time compare via `hmac.compare_digest`), checks expiry, validates ticket_id and email match
  - `_get_csat_secret()`: uses `frappe.local.conf.secret` or `get_encryption_key()` — matches Frappe's own pattern
- Single-use enforcement: `submit_rating()` checks `token_used=0` in DB, sets `token_used=1` after rating
- Bench console: second call to `submit_rating` with same token → "This survey link has already been used" error page
- 13 token unit tests pass: tamper detection, wrong ticket/email rejection, expiry detection, garbage token rejection

---

## Unit Test Results

| Test Module | Tests | Result |
|---|---|---|
| `helpdesk.tests.test_csat_token` | 13 | All PASS |
| `helpdesk.tests.test_hd_csat_response` | 9 | All PASS |
| `helpdesk.tests.test_csat_scheduler` | 9 | All PASS |
| **Total** | **31** | **All PASS** |

---

## Integration Test Results (bench console)

| Test | Result | Evidence |
|---|---|---|
| Token generation | PASS | Token has correct `payload.signature` format |
| Token validation (happy path) | PASS | `valid=True, expired=False` |
| Rating submission | PASS | Rating stored, token_used set to 1 |
| Single-use token enforcement | PASS | Second submit renders error page, rating unchanged |
| Comment submission | PASS | Comment stored, returns success message |
| Unsubscribe flow | PASS | Email added to unsubscribed list |
| Dashboard data API | PASS | Returns overall_score, response_count, rating_distribution |
| Invalid rating rejection | PASS | "abc" → ValidationError: "Invalid rating value" |
| DocType tables exist | PASS | HD CSAT Response and HD CSAT Survey Template tables confirmed |

---

## Code Review Findings

### P3: submit_comment does not re-validate HMAC token (informational)
- **File**: `helpdesk/api/csat.py:91`
- **Description**: `submit_comment()` only looks up the CSAT Response by token string without re-validating the HMAC signature. Since tokens are cryptographic (base64url + HMAC-SHA256), they cannot be guessed, and this endpoint is only useful after `submit_rating` has already validated the token. Risk is minimal.
- **Severity**: P3 (informational, no action needed)

### P3: Email star links render same emoji for all ratings
- **File**: `helpdesk/templates/csat_survey.html:48`
- **Description**: All 5 star links display the same single star emoji. While the hover title shows "1 star", "2 stars" etc., the visual doesn't differentiate ratings. This is a UX nit, not a functional issue — customers still click the correct rating via the link.
- **Severity**: P3 (cosmetic)

---

## Security Assessment

| Check | Result |
|---|---|
| HMAC token tamper detection | PASS — constant-time compare via `hmac.compare_digest` |
| Token expiry enforcement | PASS — expired tokens rejected with graceful error page |
| Single-use enforcement | PASS — `token_used` flag prevents replay |
| XSS protection | PASS — error/unsubscribe pages use `escape_html()`, token format is base64url-safe |
| Input validation | PASS — rating bounds checked (1-5), comment capped at 2000 chars |
| Guest endpoint security | PASS — all guest endpoints require valid token lookup |
| Permission checks | PASS — `get_dashboard_data` requires `HD CSAT Response` read permission |

---

## Files Reviewed

**Created (15 files)**:
- `helpdesk/helpdesk/doctype/hd_csat_response/hd_csat_response.json` — DocType definition
- `helpdesk/helpdesk/doctype/hd_csat_response/hd_csat_response.py` — Controller with rating validation
- `helpdesk/helpdesk/doctype/hd_csat_response/csat_scheduler.py` — Background job
- `helpdesk/helpdesk/doctype/hd_csat_response/__init__.py`
- `helpdesk/helpdesk/doctype/hd_csat_survey_template/hd_csat_survey_template.json`
- `helpdesk/helpdesk/doctype/hd_csat_survey_template/hd_csat_survey_template.py`
- `helpdesk/helpdesk/doctype/hd_csat_survey_template/__init__.py`
- `helpdesk/api/csat.py` — API endpoints
- `helpdesk/templates/csat_survey.html` — Email template
- `helpdesk/patches/v1_phase1/add_csat_settings_fields.py`
- `helpdesk/patches/v1_phase1/create_hd_csat_response.py`
- `helpdesk/patches/v1_phase1/create_hd_csat_survey_template.py`
- `helpdesk/tests/test_csat_token.py` — 13 tests
- `helpdesk/tests/test_hd_csat_response.py` — 9 tests
- `helpdesk/tests/test_csat_scheduler.py` — 9 tests

**Modified (4 files)**:
- `helpdesk/helpdesk/doctype/hd_settings/hd_settings.json` — CSAT config fields
- `helpdesk/utils.py` — HMAC token utilities
- `helpdesk/hooks.py` — Hourly cron entry
- `helpdesk/patches.txt` — 3 new patch entries

---

## Conclusion

All acceptance criteria pass. The implementation is solid with good test coverage (31 tests), proper security measures (HMAC tokens, single-use enforcement, input validation, XSS protection), and clean code organization. No P0 or P1 issues found — no fix task required.
