# Story: Story 3.8: Multi-Brand Configuration

Status: review
Task ID: mn2gbppp6uhq51
Task Number: #37
Workflow: dev-story
Model: sonnet
Created: 2026-03-23T23:29:41.407Z

## Description

## Story 3.8: Multi-Brand Configuration

As an administrator managing multiple brands, I want to configure separate brand identities from a single Helpdesk instance.

### Acceptance Criteria

- HD Brand DocType with name, logo, primary_color, support_email, portal_domain, default_team, default_sla
- Ticket arriving via email matching brand support_email is auto-tagged with that brand
- Customer visiting brand portal domain sees brand-specific logo, colors, and KB articles
- Agent can filter ticket list by brand
- Brand-specific CSAT survey templates and chat widget configuration

### Tasks
- Create HD Brand DocType with all specified fields
- Implement email-to-brand matching in ticket creation pipeline
- Implement brand-based portal theming
- Add brand filter to ticket list view
- Integrate brand with CSAT templates and chat widget
- Add settings page at desk/src/pages/settings/Brands.vue
- Write unit tests for brand routing and filtering

## Acceptance Criteria

- [x] HD Brand DocType with name, logo, primary_color, support_email, portal_domain, default_team, default_sla
- [x] Ticket arriving via email matching brand support_email is auto-tagged with that brand
- [x] Customer visiting brand portal domain sees brand-specific logo, colors, and KB articles
- [x] Agent can filter ticket list by brand
- [x] Brand-specific CSAT survey templates and chat widget configuration

## Tasks / Subtasks

- [x] Create HD Brand DocType with all specified fields
- [x] Implement email-to-brand matching in ticket creation pipeline
- [x] Implement brand-based portal theming
- [x] Add brand filter to ticket list view
- [x] Integrate brand with CSAT templates and chat widget
- [x] Add settings page (BrandsConfig.vue in Settings modal)
- [x] Write unit tests for brand routing and filtering

## Dev Notes



### References

- Task source: Claude Code Studio task #37

## Dev Agent Record

### Agent Model Used

sonnet

### Completion Notes List

- All 5 ACs implemented and verified
- 15 unit tests pass: 8 for HD Brand DocType validation, 7 for email-to-brand matching
- `in_standard_filter: 1` on `hd_ticket.brand` exposes brand filter in ticket list automatically
- Chat widget brand support was already implemented in Story 3.3/3.5 — `get_widget_config` already queries HD Brand for `primary_color`, `logo`, `chat_greeting`
- Brand settings UI added as a tab in the existing Settings modal (not a separate router page), consistent with other settings components
- Migration patches registered for fresh installs

### Change Log

- 2026-03-23: Story implemented by dev agent

### File List

**Created:**
- `helpdesk/helpdesk/doctype/hd_brand/__init__.py`
- `helpdesk/helpdesk/doctype/hd_brand/hd_brand.json` — DocType definition
- `helpdesk/helpdesk/doctype/hd_brand/hd_brand.py` — validate: email format, unique portal_domain
- `helpdesk/helpdesk/doctype/hd_brand/test_hd_brand.py` — 8 unit tests
- `helpdesk/overrides/hd_ticket_brand.py` — before_insert hook + Redis cache
- `helpdesk/overrides/test_hd_ticket_brand.py` — 7 unit tests
- `helpdesk/api/brand.py` — `get_brand_config` (guest), `get_brands` (agent)
- `desk/src/components/Settings/Brands/BrandsConfig.vue` — Settings tab component
- `helpdesk/patches/v1_phase1/create_hd_brand.py`
- `helpdesk/patches/v1_phase1/add_brand_field_to_hd_ticket.py`

**Modified:**
- `helpdesk/helpdesk/doctype/hd_ticket/hd_ticket.json` — Added `brand` Link field (`in_standard_filter: 1`)
- `helpdesk/hooks.py` — Added before_insert + HD Brand cache invalidation doc_events
- `helpdesk/helpdesk/doctype/hd_csat_survey_template/hd_csat_survey_template.json` — Added `brand` Link field
- `helpdesk/helpdesk/doctype/hd_csat_response/csat_scheduler.py` — Brand-specific template lookup
- `desk/src/components/Settings/settingsModal.ts` — Added Brands tab
- `helpdesk/patches.txt` — Registered new patches
