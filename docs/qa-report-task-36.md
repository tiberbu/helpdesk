# QA Report: Task #36 — Story 3.7: CSAT Survey Infrastructure and Delivery

**QA Date**: 2026-03-24
**QA Depth**: 1/1 (final — max depth reached)
**Tester**: Claude Opus 4.6 (automated QA)
**Test Method**: Playwright MCP browser testing, unit tests (31 tests), bench console integration tests, code review

---

## Summary

**Overall Result: PASS with 1 P1 issue**

All 6 acceptance criteria verified at infrastructure level. 31 unit tests pass. Browser testing via Playwright MCP confirms the full CSAT flow works end-to-end: rating submission via star link, single-use token enforcement, unsubscribe page, dashboard API. However, the **optional comment submission on the thank-you page fails for guest users** due to a CSRF token error (P1).

---

## Acceptance Criteria Results

### AC1: Admin enables CSAT in HD Settings with configurable delay (default 24h) and frequency limit (default 7 days)
**Result: PASS**

- **Browser test**: Navigated to `http://help.frappe.local/app/hd-settings/HD Settings` — CSAT settings visible in "ITIL & Features" tab
- "Enable CSAT Surveys" checkbox present and checked in Feature Flags section
- Toggling checkbox hides/shows "CSAT Survey Settings" section (depends_on works)
- "Survey Delay (hours)": default 24, with help text
- "Frequency Limit (days)": default 7, with help text
- "Survey Link Expiry (days)": default 7, with help text
- Settings saved successfully (green "Saved" toast)

**Evidence**: Screenshots `task-36-hd-settings-csat-fields.png`, `task-36-csat-survey-settings.png`

### AC2: On ticket resolution + delay, CSAT email sent with 1-5 star one-click rating links
**Result: PASS**

- Email template at `helpdesk/templates/csat_survey.html` renders 5 star links as GET URLs
- Each star link: `/api/method/helpdesk.api.csat.submit_rating?token={{token}}&rating={{n}}`
- Unsubscribe link in footer
- Scheduler hook in `hooks.py`: `"0 */1 * * *"` (hourly cron)
- `send_pending_surveys()` correctly queries resolved tickets past delay, checks frequency limits, generates HMAC tokens

### AC3: Click star submits rating via single click, thank-you page confirms with optional comment field
**Result: PARTIAL PASS (P1 issue with comment submission)**

- **Browser test**: Navigated to `submit_rating?token=...&rating=4` with valid HMAC token
- Thank-you page rendered: 4 stars (⭐⭐⭐⭐), "Thank you!" heading, comment textarea, "Submit Comment" button
- Rating correctly stored in DB (verified via bench console)
- **P1 BUG**: Clicking "Submit Comment" on thank-you page → **HTTP 400 CSRFTokenError**
  - The JS sends `X-Frappe-CSRF-Token: 'fetch'` but the page is a guest web page with no CSRF context
  - Confirmed via Playwright: `fetch()` POST to `submit_comment` returns `{"exc_type":"CSRFTokenError"}`
  - Root cause: `@frappe.whitelist(allow_guest=True)` on `submit_comment` still requires CSRF; needs `xss_safe=True`

**Evidence**: Screenshot `task-36-thankyou-page.png`

### AC4: Frequency limit: no survey if customer received one in last 7 days
**Result: PASS**

- Unit test `test_frequency_limit_skips_recent_recipient` passes — mocks DB to simulate recent survey, verifies skip
- `csat_scheduler.py` lines 88-98: queries for recent surveys per customer_email and skips if found
- `csat_frequency_days` setting controls the limit (default 7)

### AC5: Unsubscribe link marks customer as unsubscribed
**Result: PASS**

- **Browser test**: Navigated to `unsubscribe?token=...` with valid token
- Page title: "Unsubscribed" (HTTP 200)
- Shows "john@example.com has been unsubscribed from future CSAT surveys."
- Backend verified: `is_unsubscribed()` returns `True` after unsubscribe
- Unsubscribed emails stored as JSON list in `HD Settings.csat_unsubscribed_emails`
- Unit tests pass: `test_mark_unsubscribed_adds_email`, `test_mark_unsubscribed_idempotent`

**Evidence**: Screenshot `task-36-unsubscribe-page.png`

### AC6: HMAC-signed single-use tokens for survey links
**Result: PASS**

- Token format: `base64url(ticket_id:email:expiry_ts).hmac_sha256_hex`
- **Browser test**: Second rating submission with same token → "Survey Link Issue" page: "This survey link has already been used or is invalid."
- All 13 token unit tests pass: tamper detection, wrong ticket/email rejection, expiry detection, garbage token rejection
- Constant-time comparison via `hmac.compare_digest`
- Dashboard API (`get_dashboard_data`): correctly returns 403 for guests, valid JSON for authenticated users

**Evidence**: Screenshot `task-36-single-use-token.png`

---

## P1 Issue Detail

### CSRF Token Error on Comment Submission from Thank-You Page

| Field | Value |
|---|---|
| **Severity** | P1 — Feature partially broken for all guest users |
| **File** | `helpdesk/api/csat.py` line 82 |
| **Current code** | `@frappe.whitelist(allow_guest=True)` |
| **Expected code** | `@frappe.whitelist(allow_guest=True, xss_safe=True)` |
| **Symptom** | Clicking "Submit Comment" on thank-you page returns HTTP 400 CSRFTokenError |
| **Root Cause** | The thank-you page is rendered via `frappe.respond_as_web_page()` as a guest page. The embedded JS `fetch()` sends `X-Frappe-CSRF-Token: 'fetch'` but Frappe cannot validate it because no CSRF cookie exists in the guest context. Adding `xss_safe=True` bypasses CSRF validation for this endpoint, which is safe because the endpoint already validates the survey token. |
| **Impact** | Optional comment feature is 100% broken for all CSAT respondents. Rating submission itself works fine (GET request, no CSRF needed). |
| **Verify fix** | Navigate to `submit_rating?token=...&rating=4` in browser, type a comment, click "Submit Comment" — should show "Comment saved!" |

---

## Unit Test Results

| Test Module | Tests | Result |
|---|---|---|
| `helpdesk.tests.test_csat_token` | 13 | All PASS |
| `helpdesk.tests.test_hd_csat_response` | 9 | All PASS |
| `helpdesk.tests.test_csat_scheduler` | 9 | All PASS |
| **Total** | **31** | **All PASS** |

---

## Browser Test Results (Playwright MCP)

| Test | Result | Evidence |
|---|---|---|
| HD Settings CSAT fields visible | PASS | `task-36-hd-settings-csat-fields.png` |
| CSAT Survey Settings section toggle | PASS | Hides when unchecked, shows when checked |
| Default values (24h, 7d, 7d) | PASS | `task-36-csat-survey-settings.png` |
| Rating submission via star link (GET) | PASS | Thank-you page with correct stars |
| Thank-you page layout | PASS | `task-36-thankyou-page.png` |
| Comment submission (POST) | **FAIL (P1)** | CSRFTokenError 400 |
| Single-use token enforcement | PASS | `task-36-single-use-token.png` |
| Unsubscribe page | PASS | `task-36-unsubscribe-page.png` |
| Dashboard API (guest) | PASS | Returns 403 "Not Permitted" |
| Dashboard API (authenticated) | PASS | Returns valid JSON with overall_score |
| Invalid rating rejection | PASS | Returns 417 validation error |
| No CSAT-related console errors on helpdesk | PASS | Only pre-existing socket.io errors |

---

## Console Errors

- **CSAT-related**: 1 error — CSRFTokenError on `submit_comment` POST (P1, documented above)
- **Pre-existing**: socket.io `ERR_CONNECTION_REFUSED` (socketio server not running), Vue warnings — not related to this story

---

## Security Assessment

| Check | Result |
|---|---|
| HMAC token tamper detection | PASS — constant-time compare via `hmac.compare_digest` |
| Token expiry enforcement | PASS — expired tokens rejected with graceful error page |
| Single-use enforcement | PASS — `token_used` flag prevents replay |
| XSS protection | PASS — error/unsubscribe pages use `escape_html()` |
| Input validation | PASS — rating bounds checked (1-5), comment capped at 2000 chars |
| Guest endpoint security | PASS — all guest endpoints require valid token lookup |
| Permission checks | PASS — `get_dashboard_data` requires authentication (403 for guests) |

---

## Screenshots

| File | Description |
|---|---|
| `task-36-hd-settings-csat-fields.png` | HD Settings page with CSAT checkbox in Feature Flags |
| `task-36-csat-survey-settings.png` | CSAT Survey Settings section with delay/frequency/expiry fields |
| `task-36-thankyou-page.png` | Thank-you page after 4-star rating submission |
| `task-36-single-use-token.png` | Error page when reusing already-used token |
| `task-36-unsubscribe-page.png` | Unsubscribe confirmation page |

---

## Code Review Findings (P3 — informational only)

### P3: Email star links render same emoji for all ratings
- **File**: `helpdesk/templates/csat_survey.html:48`
- All 5 star links display the same single star emoji. Hover title differentiates. Cosmetic nit.

### P3: submit_comment does not re-validate HMAC token
- **File**: `helpdesk/api/csat.py:91`
- Looks up by token string only. Risk is minimal since tokens are cryptographic.

---

## Conclusion

5 of 6 acceptance criteria fully pass. AC3 partially passes — rating + thank-you page work but optional comment POST fails due to CSRF (P1). A fix task has been created for the one-line fix (`xss_safe=True` on `submit_comment`).
