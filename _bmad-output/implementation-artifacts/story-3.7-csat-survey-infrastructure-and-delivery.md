# Story 3.7: CSAT Survey Infrastructure and Delivery

Status: ready-for-dev

## Story

As an administrator,
I want automated post-resolution CSAT surveys,
So that customer satisfaction is measurable.

## Acceptance Criteria

1. **Admin configuration** — Admin can enable `csat_enabled` in HD Settings with configurable `csat_delay_hours` (default 24h) and `csat_frequency_days` (default 7 days).
2. **Survey dispatch** — On ticket resolution + delay expiry, a CSAT survey email is sent to the ticket requester with 1-5 star one-click rating links (each star is a distinct URL).
3. **One-click rating** — Clicking a star link submits the rating in a single HTTP request (no form required); a thank-you page is displayed confirming submission with an optional comment field.
4. **Comment submission** — The thank-you page allows the customer to optionally submit a free-text comment via a short form POST; the comment is saved on the HD CSAT Response record.
5. **Frequency limit** — If the customer (identified by email) already received a CSAT survey within the last `csat_frequency_days` days, no survey is sent for this ticket.
6. **Unsubscribe** — Each survey email contains an unsubscribe link; clicking it marks the customer as unsubscribed in HD Settings / customer record and sends no future surveys.
7. **HMAC token security** — Survey links contain HMAC-SHA256 signed single-use tokens encoding `ticket_id:customer_email:expiry_timestamp`; a used token cannot be reused (single-use enforcement via token_used flag on HD CSAT Response).
8. **Token expiry** — Tokens expire after a configurable period (default 7 days); submitting with an expired token returns a graceful error page.
9. **Survey scheduling background job** — An hourly cron job (`send_pending_surveys`) enqueues survey emails for all resolved tickets whose delay has elapsed and where no survey has been sent yet.
10. **HD CSAT Response DocType** — Records each survey response with fields: ticket, customer_email, rating (1-5), comment, token, token_used (Check), survey_sent_at, responded_at, brand.
11. **HD CSAT Survey Template DocType** — Supports per-brand survey email customization: subject, intro_text, brand logo URL, primary_color; falls back to default if no brand template exists.
12. **Unit tests** — Token generation/validation, frequency limit enforcement, and unsubscribe logic are covered by unit tests with ≥80% coverage on new backend code (NFR-M-01).

## Tasks / Subtasks

- [ ] **Task 1 — HD Settings additions** (AC: #1)
  - [ ] 1.1 Add `csat_enabled` (Check, default 0) to `hd_settings` DocType JSON
  - [ ] 1.2 Add `csat_delay_hours` (Int, default 24) to HD Settings
  - [ ] 1.3 Add `csat_frequency_days` (Int, default 7) to HD Settings
  - [ ] 1.4 Add `csat_token_expiry_days` (Int, default 7) to HD Settings
  - [ ] 1.5 Write migration patch `helpdesk/patches/v1_phase1/add_csat_settings_fields.py`

- [ ] **Task 2 — HD CSAT Response DocType** (AC: #10)
  - [ ] 2.1 Create `helpdesk/helpdesk/doctype/hd_csat_response/` directory with `__init__.py`
  - [ ] 2.2 Create `hd_csat_response.json` schema with fields: `ticket` (Link→HD Ticket), `customer_email` (Data), `rating` (Int, 1-5), `comment` (Long Text), `token` (Data), `token_used` (Check, default 0), `survey_sent_at` (Datetime), `responded_at` (Datetime), `brand` (Link→HD Brand, optional)
  - [ ] 2.3 Create `hd_csat_response.py` controller with `validate()` ensuring rating is 1-5 and token integrity
  - [ ] 2.4 Create `test_hd_csat_response.py` with tests for controller validation

- [ ] **Task 3 — HD CSAT Survey Template DocType** (AC: #11)
  - [ ] 3.1 Create `helpdesk/helpdesk/doctype/hd_csat_survey_template/` directory with `__init__.py`
  - [ ] 3.2 Create `hd_csat_survey_template.json` schema with fields: `brand` (Link→HD Brand, optional), `subject` (Data), `intro_text` (Long Text), `logo_url` (Data), `primary_color` (Color)
  - [ ] 3.3 Create `hd_csat_survey_template.py` controller (minimal; fetch defaults helper)
  - [ ] 3.4 Create `test_hd_csat_survey_template.py`

- [ ] **Task 4 — HMAC Token Utility** (AC: #7, #8)
  - [ ] 4.1 Create `helpdesk/utils/token.py` with:
    - `generate_csat_token(ticket_id, customer_email, expiry_days) -> str`
    - `validate_csat_token(token, ticket_id, customer_email) -> dict` — returns `{valid, expired, payload}`
  - [ ] 4.2 Use `hmac.new(key=frappe.utils.get_site_secret(), msg=..., digestmod="sha256").hexdigest()` as per ADR-06
  - [ ] 4.3 Add `helpdesk/utils/__init__.py` if not present
  - [ ] 4.4 Write unit tests in `helpdesk/utils/test_token.py` covering: valid token, expired token, tampered token, single-use enforcement

- [ ] **Task 5 — CSAT Survey Email Template** (AC: #2, #3)
  - [ ] 5.1 Create `helpdesk/templates/csat_survey.html` — Jinja2 email template
  - [ ] 5.2 Template must include: greeting, intro text, 1-5 star one-click links (each `?token={token}&rating={n}`), unsubscribe link, brand logo/color support
  - [ ] 5.3 Follow UX-DR-05: one-click-to-rate design — clicking a star directly submits the rating without a separate form
  - [ ] 5.4 Stars are rendered as linked emoji or image elements; clicking any star is a GET to `submit_rating`

- [ ] **Task 6 — CSAT API Module** (AC: #3, #4, #6, #7, #8)
  - [ ] 6.1 Create `helpdesk/api/csat.py` with:
    - `submit_rating(token, rating)` — `@frappe.whitelist(allow_guest=True)` — validates token, creates/updates HD CSAT Response, marks token used, renders thank-you page
    - `submit_comment(token, comment)` — `@frappe.whitelist(allow_guest=True)` — appends comment to existing response (same token, idempotent)
    - `unsubscribe(token)` — `@frappe.whitelist(allow_guest=True)` — marks customer as unsubscribed
    - `get_dashboard_data(filters)` — `@frappe.whitelist()` — returns aggregated CSAT data for Epic 6 Story 6.3
  - [ ] 6.2 `submit_rating` must: check token validity → check expiry → check single-use → record response → mark token_used = 1
  - [ ] 6.3 All guest endpoints sanitize inputs; no sensitive data in responses
  - [ ] 6.4 Return redirect/render to thank-you page HTML after successful rating submission

- [ ] **Task 7 — Survey Scheduling Background Job** (AC: #5, #9)
  - [ ] 7.1 Create `helpdesk/helpdesk/doctype/hd_csat_response/csat_scheduler.py`
  - [ ] 7.2 Implement `send_pending_surveys()`:
    - Query resolved tickets where `modified >= NOW() - csat_delay_hours` and no HD CSAT Response with `survey_sent_at` set exists for the ticket
    - Check frequency limit: skip if customer received a survey in the last `csat_frequency_days` days
    - Check `csat_enabled` flag in HD Settings; skip if disabled
    - Skip if customer is marked unsubscribed
    - Generate HMAC token, create HD CSAT Response record (token stored, token_used=0, survey_sent_at=now)
    - Enqueue email send via `frappe.enqueue` (queue="long")
  - [ ] 7.3 Create helper `_send_csat_email(ticket_id, csat_response_name)` that: fetches template (brand-specific fallback to default), renders `csat_survey.html`, sends via `frappe.sendmail`

- [ ] **Task 8 — Scheduler Hook Registration** (AC: #9)
  - [ ] 8.1 Add to `hooks.py` `scheduler_events`:
    ```python
    "cron": {
        "0 */1 * * *": [
            "helpdesk.helpdesk.doctype.hd_csat_response.csat_scheduler.send_pending_surveys"
        ]
    }
    ```
  - [ ] 8.2 Verify existing `scheduler_events` dict structure and merge correctly (do not overwrite existing cron entries)

- [ ] **Task 9 — Unsubscribe Handling** (AC: #6)
  - [ ] 9.1 Add `csat_unsubscribed` (Check, default 0) field to `hd_contact` or relevant customer DocType, OR store unsubscribed emails in HD Settings as a JSON list — document the chosen approach
  - [ ] 9.2 `unsubscribe()` API marks the customer record; `send_pending_surveys()` checks this flag before enqueueing
  - [ ] 9.3 Unsubscribe link in email: `?token={token}&action=unsubscribe` or dedicated endpoint
  - [ ] 9.4 Confirmation page displayed after unsubscribe

- [ ] **Task 10 — Unit Tests** (AC: #12)
  - [ ] 10.1 `helpdesk/utils/test_token.py` — token generation, validation, expiry, tamper detection
  - [ ] 10.2 `helpdesk/helpdesk/doctype/hd_csat_response/test_hd_csat_response.py` — single-use enforcement, rating bounds
  - [ ] 10.3 `helpdesk/helpdesk/doctype/hd_csat_response/test_csat_scheduler.py` — frequency limit logic, csat_enabled guard, unsubscribe skip
  - [ ] 10.4 Run tests with `bench run-tests --app helpdesk --module helpdesk.utils.test_token` and verify ≥80% pass

## Dev Notes

### Architecture Patterns

- **Feature Flag:** The entire CSAT feature is gated by `csat_enabled` in HD Settings (AR-06). Check this flag at the start of `send_pending_surveys()` and return early if disabled.
- **HMAC Token (ADR-06):** Use `frappe.utils.get_site_secret()` as the HMAC key. Token payload format: `{ticket_id}:{customer_email}:{expiry_unix_timestamp}`. Sign with `hmac.new(..., digestmod="sha256").hexdigest()`. Include the raw payload + signature in the URL as `base64(payload):signature` or as separate query params — choose a consistent, URL-safe encoding.
- **Single-Use Tokens (NFR-SE-03):** After `submit_rating()` succeeds, set `token_used = 1` on the HD CSAT Response record immediately. Subsequent calls with the same token check this flag and return an "already used" response.
- **Background Jobs (ADR-12):** `send_pending_surveys` should use `frappe.enqueue` with `queue="long"` for the actual email sending per ticket. The scheduler function itself is lightweight — it only fetches candidates and enqueues individual email jobs.
- **Guest API (ADR-04):** `submit_rating`, `submit_comment`, and `unsubscribe` must use `@frappe.whitelist(allow_guest=True)` since customers click links without being logged in.
- **Frequency Limit Logic:** In `send_pending_surveys()`, before creating a new HD CSAT Response, run:
  ```python
  recent = frappe.db.get_all("HD CSAT Response",
      filters={"customer_email": email, "survey_sent_at": [">", cutoff_date]},
      limit=1)
  if recent:
      continue  # skip this ticket
  ```
- **Per-Brand Templates:** `HD CSAT Survey Template` is linked via `HD Brand.csat_template` (see ADR-02 schema). When sending, look up the ticket's brand, then fetch the template. Fall back to a default template if none configured.
- **Scheduler Cron (ADR-12):** The hourly cron is defined in `hooks.py` as `"0 */1 * * *"`. Ensure the merge with any existing `cron` dict in `scheduler_events` is additive (not a full replacement).
- **Error Handling:** Backend errors in `send_pending_surveys` should use `frappe.log_error(title="CSAT Survey Error")` per ADR error handling pattern. Never surface raw errors to the customer on the survey pages.

### Existing Code Reference

- `hooks.py` location: `helpdesk/hooks.py` — add cron entry to `scheduler_events`
- Existing scheduler pattern example: See `hd_service_level_agreement` sla_monitor for cron job pattern
- `frappe.sendmail` usage: See existing notification email sends in `helpdesk/helpdesk/overrides/`
- HD Settings DocType: `helpdesk/helpdesk/doctype/hd_settings/hd_settings.json` — add new fields here

### Project Structure Notes

**New files to create:**
```
helpdesk/
├── helpdesk/
│   ├── api/
│   │   └── csat.py                                   # NEW: CSAT API endpoints
│   ├── helpdesk/
│   │   └── doctype/
│   │       ├── hd_csat_response/
│   │       │   ├── __init__.py
│   │       │   ├── hd_csat_response.json              # NEW: DocType schema
│   │       │   ├── hd_csat_response.py                # NEW: Controller
│   │       │   ├── csat_scheduler.py                  # NEW: Background job
│   │       │   ├── test_hd_csat_response.py           # NEW: Unit tests
│   │       │   └── test_csat_scheduler.py             # NEW: Scheduler tests
│   │       └── hd_csat_survey_template/
│   │           ├── __init__.py
│   │           ├── hd_csat_survey_template.json       # NEW: DocType schema
│   │           ├── hd_csat_survey_template.py         # NEW: Controller
│   │           └── test_hd_csat_survey_template.py    # NEW: Unit tests
│   ├── templates/
│   │   └── csat_survey.html                           # NEW: Survey email template
│   └── utils/
│       ├── __init__.py                                # NEW if not exists
│       ├── token.py                                   # NEW: HMAC token utils
│       └── test_token.py                              # NEW: Token unit tests
└── hooks.py                                           # MODIFIED: add cron entry
```

**Modified files:**
```
helpdesk/
├── helpdesk/
│   └── doctype/
│       └── hd_settings/
│           └── hd_settings.json                       # MODIFIED: add csat_* fields
└── patches/
    └── v1_phase1/
        └── add_csat_settings_fields.py                # NEW: migration patch
```

**Alignment with architecture:**
- DocType naming follows `HD ` prefix convention (AR-02)
- DocType folder: `hd_csat_response/`, `hd_csat_survey_template/` (snake_case)
- API module at `helpdesk/api/csat.py` (matches ADR-08 API Design table)
- Utils at `helpdesk/utils/token.py` (matches architecture project structure)
- Template at `helpdesk/templates/csat_survey.html` (matches architecture project structure)
- Migration patch in `helpdesk/patches/v1_phase1/` (AR-05)

### References

- [Source: _bmad-output/planning-artifacts/architecture.md#ADR-06: CSAT Survey Token Security]
- [Source: _bmad-output/planning-artifacts/architecture.md#ADR-02: New DocType Schema for Phase 1]
- [Source: _bmad-output/planning-artifacts/architecture.md#ADR-08: API Design for New Features]
- [Source: _bmad-output/planning-artifacts/architecture.md#ADR-12: Background Job Architecture]
- [Source: _bmad-output/planning-artifacts/architecture.md#Project Structure — Complete Directory Structure]
- [Source: _bmad-output/planning-artifacts/epics.md#Story 3.7: CSAT Survey Infrastructure and Delivery]
- [Source: _bmad-output/planning-artifacts/epics.md#FR-CS-01: Post-resolution CSAT email survey]
- [Source: _bmad-output/planning-artifacts/epics.md#NFR-SE-03: CSAT survey links contain single-use HMAC tokens]
- [Source: _bmad-output/planning-artifacts/epics.md#NFR-M-01: Minimum 80% unit test coverage on all new backend code]
- [Source: _bmad-output/planning-artifacts/epics.md#AR-06: Feature flags in HD Settings]
- [Source: _bmad-output/planning-artifacts/epics.md#UX-DR-05: CSAT survey email uses one-click-to-rate design]
- [Source: _bmad-output/planning-artifacts/prd.md#CSAT Surveys — In Scope Phase 1]

## Dev Agent Record

### Agent Model Used

claude-sonnet-4-5

### Debug Log References

### Completion Notes List

### File List
