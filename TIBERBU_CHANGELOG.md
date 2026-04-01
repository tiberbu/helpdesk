# ServiceDesk by Tiberbu — Changelog

> **Fork**: [tiberbu/helpdesk](https://github.com/tiberbu/helpdesk) (from [frappe/helpdesk](https://github.com/frappe/helpdesk))  
> **Base version**: Frappe Helpdesk v1.15.1+ (upstream `main`)  
> **Branch**: `master`

This document describes all features, enhancements, and fixes added by Tiberbu on top of the upstream Frappe Helpdesk.

---

## Table of Contents

1. [Branding & UI Overhaul](#1-branding--ui-overhaul)
2. [Epic 1: ITIL Foundations](#2-epic-1-itil-foundations)
3. [Epic 2: Automation Engine](#3-epic-2-automation-engine)
4. [Epic 3: Live Chat & Omnichannel](#4-epic-3-live-chat--omnichannel)
5. [Epic 4: SLA Management](#5-epic-4-sla-management)
6. [Epic 5: Knowledge Base Advanced](#6-epic-5-knowledge-base-advanced)
7. [Kenya County Hierarchical Support](#7-kenya-county-hierarchical-support)
8. [Bug Fixes & QA](#8-bug-fixes--qa)
9. [Planning & Documentation](#9-planning--documentation)
10. [New DocTypes](#10-new-doctypes)
11. [Migration Patches](#11-migration-patches)
12. [Setup & Installation](#12-setup--installation)

---

## 1. Branding & UI Overhaul

### Rebrand: Helpdesk → ServiceDesk
- All user-facing text changed from "Helpdesk" to "ServiceDesk" across the entire frontend
- New professional sidebar icon (modern headset SVG)
- Logo and product name updated for visibility on dark sidebar
- Frappe Desk workspace JSON updated

### Professional Dark Sidebar Theme
- Dark charcoal sidebar (`#1A1D21`) with teal accent (`#0891B2`)
- Light gray content area (`#F8F9FA`)
- Status badges with distinct colors per state
- Benchmarked against Zendesk, Intercom, Front, and Linear
- User menu improved for dark background contrast

### Critical UI Audit & Fixes
- Fixed scroll and overflow issues across all Phase 1 components
- Automation Rule Builder: restored scrollability, fixed conditions/actions panels
- Linked ticket search: fixed Autocomplete component breaking search
- All panels properly contained within viewport

---

## 2. Epic 1: ITIL Foundations

**6 stories implemented, QA'd, and fixes applied.**

### Story 1.1: Feature Flag Infrastructure for ITIL Mode
- `HD Settings` extended with ITIL mode toggle
- Feature flags control ITIL-specific UI elements
- Backward compatible — existing installations unaffected

### Story 1.2: Impact and Urgency Fields with Priority Matrix
- New `impact` and `urgency` fields on HD Ticket
- Automatic priority calculation via configurable matrix
- UI controls in ticket detail sidebar

### Story 1.3: Multi-Level Ticket Categorization
- Category, sub-category, and item fields on HD Ticket
- Hierarchical category structure (HD Ticket Category DocType)
- Default categories seeded on install

### Story 1.4: Internal Notes on Tickets
- `is_internal` flag on HD Ticket Comment
- Internal notes visible only to agents, hidden from customers
- Toggle in comment editor

### Story 1.5: @Mention Notifications in Internal Notes
- Mention agents with `@username` in comments
- Real-time notifications via Frappe notification system
- Fixed duplicate notification on comment edit

### Story 1.6: Related Ticket Linking
- Link tickets as related, duplicate, or parent/child
- Bidirectional linking (linking A→B also creates B→A)
- UI in ticket detail sidebar

### Story 1.7: Per-Ticket Time Tracking
- `HD Time Entry` DocType for logging time per ticket
- `TimeTracker.vue` component in ticket detail
- Start/stop timer, manual entry, time totals
- Agent Manager and Admin permissions

### Story 1.8: Major Incident Flag and Workflow
- Major incident flag on HD Ticket
- `HD Incident Model` DocType for incident templates
- Post-incident review workflow

### Story 1.9: Incident Models / Templates
- Pre-defined incident templates for common scenarios
- Template application to new tickets
- ITIL mode gating

---

## 3. Epic 2: Automation Engine

**4 stories implemented with comprehensive QA.**

### Story 2.1: Automation Rule DocType and Engine Core
- `HD Automation Rule` DocType with trigger types (on_create, on_update, on_status_change, time_based)
- Nested AND/OR condition groups
- Actions: set_field, assign, send_email, add_comment, escalate
- Background evaluation engine

### Story 2.2: Automation Rule Builder UI
- Visual rule builder with drag-and-drop condition groups
- WHEN (trigger) → IF (conditions) → THEN (actions) layout
- Save/load rules, validation, scrollable panels

### Story 2.3: SLA-Based Automation Triggers
- Automation rules triggered by SLA breach/warning thresholds
- Warning deduplication to prevent alert floods
- Configurable thresholds in HD Settings

### Story 2.4: Automation Execution Logging
- `HD Automation Log` DocType tracks every rule execution
- Success/failure status, execution time, matched conditions
- Admin-accessible log viewer

---

## 4. Epic 3: Live Chat & Omnichannel

**8 stories implemented.**

### Story 3.1: Channel Abstraction Layer
- Unified channel interface for email, chat, portal, API
- `is_internal` normalization across all channels
- Extensible for future WhatsApp/SMS integration

### Story 3.2: Chat Session Management Backend
- `HD Chat Session` DocType for managing live chat sessions
- Session lifecycle: open → active → waiting → resolved → closed
- Agent assignment and routing

### Story 3.3: Embeddable Chat Widget
- JavaScript widget embeddable on any website
- Offline ticket creation when no agents available
- `process.env.NODE_ENV` correctly replaced for production builds

### Story 3.4: Real-Time Chat Communication
- Socket.io integration for real-time messaging
- `ChatView.vue` component with message threading
- Typing indicators and read receipts

### Story 3.5: Agent Chat Interface
- Agent-side chat dashboard
- Queue management with accept/transfer/close actions
- JWT authentication for agent endpoints

### Story 3.6: Chat-to-Ticket Transcript and Follow-up
- Convert chat sessions to tickets with full transcript
- Follow-up creation from resolved chats

### Story 3.7: CSAT Survey Infrastructure and Delivery
- `HD CSAT Response` and `HD CSAT Survey Template` DocTypes
- Post-resolution survey delivery
- Guest user CSRF fix for comment/survey submission

### Story 3.8: Multi-Brand Configuration
- `HD Brand` DocType for multi-brand support
- Brand field on HD Ticket
- Brand-specific portal customization

---

## 5. Epic 4: SLA Management

**4 stories implemented.**

### Story 4.1: Business Hours SLA Calculation Engine
- SLA calculation respects business hours and holidays
- `HD Service Holiday List` support
- Working hours per day configuration in SLA

### Story 4.2: Proactive SLA Breach Alerts
- Color-coded SLA badges on tickets (green/yellow/red)
- Warning thresholds configurable per SLA
- Real-time badge updates

### Story 4.3: SLA Compliance Dashboard
- Dashboard showing SLA compliance metrics
- Breach rates by team, priority, category
- Time-series charts for trend analysis

### Story 4.4: OLA/UC Agreement Type Preparation
- `agreement_type` field on HD Service Level Agreement
- Support for SLA (customer-facing), OLA (internal), and UC (underpinning contract)
- Foundation for multi-tier SLA management

---

## 6. Epic 5: Knowledge Base Advanced

**5 stories implemented.**

### Story 5.1: Article Review Workflow
- Review states: Draft → In Review → Approved → Published → Archived
- Reviewer assignment and approval flow
- Email notifications on state changes

### Story 5.2: Article Versioning
- Version history for knowledge base articles
- Diff viewer between versions
- Restore previous versions

### Story 5.3: Review Dates and Expiry Reminders
- Review date field on articles
- Expiry reminders via scheduled job
- Dashboard widget for articles due for review

### Story 5.4: Ticket-Article Linking
- Link relevant KB articles to tickets
- Search dialog for finding articles
- "Create Article from Ticket" flow

### Story 5.5: Internal-Only Articles
- `is_internal` flag on HD Article
- Internal articles visible only to agents
- Filtered from customer portal

---

## 7. Kenya County Hierarchical Support

**Full 7-story epic for tiered county support.**

### Backend — DocTypes & Logic

#### HD Support Level DocType (Story County-1)
- Configurable support tiers (not hardcoded)
- Fields: `level_name`, `level_order`, `allow_escalation_to_next`, `auto_escalate_minutes`, `description`
- Default levels: L0 (Sub-County), L1 (County), L2 (National), L3 (Engineering)
- Levels can be renamed (e.g., L0 → "Facility In-Charge")

#### HD Team Hierarchy Fields (Story County-1)
- `support_level` (Link to HD Support Level) on HD Team
- `parent_team` (Link to HD Team) — tree structure
- `territory` (Data) — county/sub-county name

#### HD Facility Mapping DocType (Story County-2)
- Maps facilities to county → sub-county → L0/L1/L2 teams
- CSV import template included
- Auto-routing engine in `hd_ticket.py` `before_insert`

#### Hierarchical Visibility & Permission Scoping (Story County-3)
- `permission_query_conditions` on HD Ticket
- L0 sees sub-county tickets only
- L1 sees all tickets in their county
- L2 sees all tickets nationally
- Agents see tickets based on their team's support level

#### Escalation Chain + SLA Auto-Escalation (Story County-4)
- `helpdesk/api/escalation.py` — escalate/de-escalate API
- `escalation_scheduler.py` — background job every 5 minutes
- Auto-escalate if no response within `auto_escalate_minutes` per tier
- Escalation restrictions: `allow_escalation_to_next` flag per level
- Engineering (L3) is terminal — cannot escalate further
- Escalation history logged as ticket activity

### Frontend — UI Components

#### County + Sub-County Picker (Task #354)
- County and Sub-County dropdowns on ticket creation form
- Sub-County cascading filter based on selected County
- Auto-remember per contact — subsequent tickets pre-fill location
- Works on both agent and customer portal

#### Team Hierarchy UI (Task #355)
- Support Level, Parent Team, and Territory fields in team creation/edit
- Team list shows hierarchy information

#### Escalation UI (Task #356)
- Escalate/de-escalate buttons on ticket detail
- `EscalationDialog.vue` with reason input
- `EscalationEvent.vue` in activity feed
- Support Level badge on ticket sidebar

#### Tier Dashboards (Tasks #342, #357)
- `L0DashboardView.vue` — sub-county view
- `L1DashboardView.vue` — county view with drill-down
- `L2DashboardView.vue` — national view with county drill-down
- `L3DashboardView.vue` — engineering view
- `CountyDashboardPage.vue` — route and page wrapper
- Wired into sidebar navigation

#### Support Level Management (Task #358)
- CRUD page for HD Support Level in Settings
- Visual hierarchy display

#### Ticket List Enhancements (Task #359)
- Support Level and County columns on ticket list
- Filter by Support Level and County

### Seed Data — Kenya (Story County-7)

#### Teams Created
- 1 National Support Team (L2)
- 1 Engineering Team (L3)
- 47 County teams (L1) — all 47 Kenya counties
- ~304 Sub-County teams (L0) — all gazetted sub-counties
- Full parent-child hierarchy

#### SLA Configurations
- L0 Sub-County SLA: 30min first response, 4hr resolution
- L1 County SLA: 1hr first response, 8hr resolution
- L2 National SLA: 2hr first response, 24hr resolution
- L3 Engineering SLA: 4hr first response, 72hr resolution
- Kenya Default Holiday List (10 public holidays)
- 24/7 working hours for all tiers

---

## 8. Bug Fixes & QA

Every story went through automated QA (Playwright browser testing) and adversarial code review. Key fixes:

- **Automation Builder**: Fixed completely broken scroll, conditions not addable, actions cut off
- **Article Versioning**: Fixed broken `__()` string interpolation in version diff
- **Ticket-Article Linking**: Fixed empty search results, create article routing
- **SLA Badges**: Fixed color-coded badges not rendering
- **Chat Widget**: Fixed `process.env.NODE_ENV` not replaced in production builds
- **CSAT Survey**: Fixed CSRF error for guest user comment submission
- **Time Tracking**: Fixed N+1 query, started_at validation, timezone-aware crash
- **Major Incident**: Fixed missing post-incident review, permission gaps
- **Delete Entry**: Fixed ownership bypass, HD Admin permission
- **Customer Portal**: Fixed Internal Server Error on ticket creation
- **Linked Ticket Search**: Fixed Autocomplete component breaking search

---

## 9. Planning & Documentation

### BMAD Phase 2-4 Planning
- **Competitive Gap Analysis**: Benchmarked against Zendesk, Freshdesk, Intercom, Jira Service Management, ServiceNow
- **Product Requirements Documents**: Phase 2 (AI & Omnichannel), Phase 3 (Enterprise & Automation), Phase 4 (Innovation)
- **Technical Architecture**: Full architecture for AI agent, change management, VoIP, video support
- **Sprint Planning**: 35 stories across 6 epics for Phase 1, Phase 2-4 epics and stories defined

### Key Documents (in `docs/`)
- `feature-roadmap-brd.md` — Feature roadmap and BRD
- `competitive-gap-analysis.md` — Competitive analysis
- `phase-2-prd.md`, `phase-3-prd.md`, `phase-4-prd.md` — Phase PRDs
- `technical-architecture.md` — Technical architecture
- `sprint-plan.md` — Sprint planning

---

## 10. New DocTypes

| DocType | Purpose |
|---------|---------|
| `HD Support Level` | Configurable support tiers (L0-L3) |
| `HD Facility Mapping` | Maps facilities → county → teams |
| `HD Time Entry` | Per-ticket time tracking |
| `HD Automation Rule` | Automation rule definitions |
| `HD Automation Log` | Automation execution logs |
| `HD Chat Session` | Live chat session management |
| `HD Chat Message` | Chat messages within sessions |
| `HD CSAT Response` | Customer satisfaction survey responses |
| `HD CSAT Survey Template` | CSAT survey templates |
| `HD Brand` | Multi-brand configuration |
| `HD Incident Model` | Incident templates |
| `HD Ticket Category` | Hierarchical ticket categories |
| `HD Comment Reaction` | Comment reactions (emoji) |
| `HD Saved Reply` | Reusable reply templates (renamed from Canned Response) |
| `HD Service Holiday List` | Holiday list for SLA calculation |
| `HD Field Layout` | Custom field layout configuration |

---

## 11. Migration Patches

All patches are in `helpdesk/patches/` and run automatically during `bench migrate`:

### Phase 1 Patches (`v1_phase1/`)
- `add_itil_feature_flags` — ITIL mode settings
- `add_impact_urgency_to_hd_ticket` — Impact/urgency fields
- `add_category_fields_to_hd_ticket` — Category hierarchy
- `create_default_categories` — Seed default categories
- `add_is_internal_to_hd_ticket_comment` — Internal notes flag
- `add_related_ticket_linking` — Related ticket fields
- `add_major_incident_fields` — Major incident flag
- `add_incident_model_doctypes` — Incident model DocType
- `create_hd_time_entry` — Time tracking DocType
- `create_hd_chat_session` / `create_hd_chat_message` — Chat DocTypes
- `add_chat_realtime_fields` / `add_chat_availability_to_agent` — Chat fields
- `add_source_field_to_hd_ticket` — Source channel field
- `add_csat_settings_fields` — CSAT settings
- `create_hd_csat_response` / `create_hd_csat_survey_template` — CSAT DocTypes
- `create_hd_brand` / `add_brand_field_to_hd_ticket` — Multi-brand
- `add_business_hours_to_sla` — Business hours fields
- `add_sla_manager_to_hd_team` / `add_sla_agreement_type` — SLA enhancements
- `add_in_review_status_to_hd_article` — Article review status
- `add_kb_settings_to_hd_settings` / `add_kb_review_settings` — KB settings
- `add_review_date_fields_to_hd_article` — Review dates
- `add_linked_articles_to_hd_ticket` — Article linking
- `add_internal_only_to_hd_article` — Internal articles
- `add_hd_support_level` — Support Level DocType + seed data
- `add_escalation_fields_to_hd_ticket` — Escalation fields
- `add_hd_facility_mapping` — Facility Mapping DocType

### County Patches (`v1_county/`)
- `seed_kenya_teams` — 47 counties, ~304 sub-counties, national + engineering teams
- `seed_sla_configs` — Per-tier SLA configurations + Kenya holidays

---

## 12. Setup & Installation

### Fresh Install
```bash
# Standard Frappe bench install
bench get-app https://github.com/tiberbu/helpdesk.git
bench --site your-site.local install-app helpdesk
bench --site your-site.local migrate
```

The `after_install` hook and migration patches automatically:
1. Create all new DocTypes
2. Seed HD Support Levels (L0-L3)
3. Seed Kenya county/sub-county teams (350+ teams)
4. Create default SLA configurations per tier
5. Create Kenya Default Holiday List
6. Seed default ticket categories

### Build Frontend
```bash
cd /path/to/helpdesk/desk
yarn install
yarn build
```

### Requirements
- Frappe v15+ (v16 supported)
- ERPNext (optional, not required)
- Python 3.12+
- Node.js 18+

---

## Summary of Scale

| Metric | Count |
|--------|-------|
| Stories implemented | 35 (Phase 1) |
| Epics completed | 6 of 6 (Phase 1) |
| New DocTypes | 16 |
| Migration patches | 30+ |
| QA tasks completed | 35+ |
| Bug fix tasks | 80+ |
| Kenya teams seeded | ~352 |
| Total commits (over upstream) | 1,344 |

---

*Last updated: April 1, 2026*  
*Maintained by Tiberbu HealthNet Limited*
