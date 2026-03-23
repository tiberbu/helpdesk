---
documentType: PRD
version: "1.0"
date: 2026-03-22
author: Mwogi
projectName: Frappe Helpdesk Phase 1 - ITIL Foundation & Platform Transformation
status: Draft
classification:
  domain: saas_b2b
  projectType: web_app
  complexity: high
inputDocuments:
  - _bmad-output/planning-artifacts/product-brief.md
  - docs/BRD.md
  - docs/feature-roadmap.md
  - _bmad-output/planning-artifacts/research.md
  - docs/itil-compliance-research.md
  - docs/competitive-analysis.md
stepsCompleted: [1, 2, 3, 4, 5, 6, 7, 8, 9]
---

# Product Requirements Document: Frappe Helpdesk Phase 1

## Executive Summary

### Vision

Transform Frappe Helpdesk from a basic ticketing system into an ITIL-aligned, multi-channel support platform that competes with Freshdesk and Zoho Desk for SMB use cases -- while preserving open-source freedom, zero per-agent pricing, and native Frappe/ERPNext integration.

### Phase 1 Objective

Phase 1 ("Foundation") delivers the minimum viable transformation over 6 months with 2-3 developers. It closes 14 remaining critical feature gaps, establishes CSAT measurement, adds live chat as a second real-time channel, enhances SLA management toward ITIL compliance, improves the knowledge base with article lifecycle workflows, and builds the reporting and automation infrastructure required for Phase 2 AI capabilities.

### Target Outcome

By end of Phase 1, Frappe Helpdesk achieves 70%+ feature parity with Freshdesk, supports 4 ITIL practices at PinkVERIFY-alignment level, and establishes measurable baselines for agent productivity, customer satisfaction, and SLA compliance.

### Key Differentiators Preserved

- Zero per-agent pricing ($33K-$101K/year savings vs Zendesk at 50 agents)
- Full data sovereignty (self-hosted, GDPR/HIPAA-compliant by architecture)
- Native ERPNext integration (customer orders, invoices, assets visible in agent context)
- Open-source extensibility (DocType system, auto-generated REST APIs, plugin architecture)

### What Already Exists (Post March 2026 Upstream Sync)

The following P0 capabilities are already implemented and serve as the foundation:

- **Saved Replies** -- HD Saved Reply DocType with team sharing and autocomplete
- **Collision Detection** -- Socket.IO active viewer tracking and typing indicators
- **Keyboard Shortcuts** -- Full navigation (T, P, A, S, R, C, Ctrl+K command palette)
- **Agent Dashboard** -- Customizable home page with SLA metrics, feedback trends, performance data
- **i18n** -- 25+ language translations with runtime plugin
- **Telemetry** -- PostHog event tracking for usage analytics
- **Comment Reactions** -- Emoji reactions on ticket comments

---

## Success Criteria

All success criteria are SMART: Specific, Measurable, Attainable, Relevant, and Traceable to business objectives.

| ID | Criterion | Metric | Baseline | Target | Measurement Method | Traces To |
|----|-----------|--------|----------|--------|-------------------|-----------|
| SC-01 | CSAT baseline established | CSAT response rate on resolved tickets | 0% | >60% | CSAT survey responses / resolved tickets (30-day rolling) | BO-3 |
| SC-02 | CSAT score measurable | Average CSAT score | Unmeasured | 3.5/5 baseline | Average of all CSAT ratings (30-day rolling) | BO-3 |
| SC-03 | Live chat operational | % new tickets via live chat | 0% | >10% | Live chat tickets / total new tickets (30-day) | BO-4 |
| SC-04 | SLA improvement | SLA breach rate change | Current rate (unmeasured) | -15% from baseline | (Breached SLAs / total SLAs) comparison month-over-month | BO-1 |
| SC-05 | Custom reports adopted | Reports created by managers | 0 | >20 | Count of HD Custom Report records with >1 execution | BO-1 |
| SC-06 | Agent productivity measurable | Time tracking data coverage | 0% | >80% of resolved tickets | Tickets with time entries / resolved tickets | BO-2 |
| SC-07 | ITIL foundation established | ITIL-compliant fields on tickets | 0 fields | Impact, urgency, category, sub-category on 100% of new tickets | Field fill rate on HD Ticket (30-day) | BO-7 |
| SC-08 | KB article lifecycle active | Articles with review workflow | 0% | >50% of published articles | Articles with status != Draft and review_date set / total published | BO-7 |
| SC-09 | Workflow automation adopted | Active automation rules | 0 | >10 active rules | Count of HD Automation Rule records with enabled=True | BO-1 |
| SC-10 | Competitive viability | Feature parity score vs Freshdesk | ~55% | 70%+ | Feature checklist comparison (quarterly assessment) | BO-1 |

**Decision Gate:** If SC-01, SC-03, SC-04, and SC-07 are met, proceed to Phase 2 (Intelligence). If not, iterate on Phase 1 before advancing.

---

## Product Scope

### In Scope (Phase 1 -- Months 1-6)

| Area | Capabilities |
|------|-------------|
| **Enhanced Incident Management** | Impact/urgency fields, calculated priority matrix, multi-level categorization (category > sub-category), major incident flag and workflow, related incident linking, incident models/templates, MTTR reporting |
| **CSAT Surveys** | Post-resolution email surveys, 1-5 star rating + comment, per-agent/team dashboards, unsubscribe management |
| **Live Chat Widget** | Embeddable JS widget, typing indicators, agent availability, chat-to-ticket conversion, customizable branding |
| **Advanced Workflow Automation** | Visual if-then-else rule builder, 10+ trigger types, 10+ action types, condition-based routing |
| **Custom Report Builder** | Drag-and-drop reports, filters, group-by, scheduled delivery, CSV/Excel export, bar/line/pie/table charts |
| **Enhanced SLA Management** | Business-hours-only calculation, holiday calendars, multi-timezone, proactive breach alerts, OLA/UC field preparation, SLA compliance dashboard |
| **Knowledge Base Improvements** | Article review/approval workflow (Draft > Review > Published > Archived), versioning, review dates, ticket-article linking, internal-only articles |
| **Multi-Brand Support** | Multiple branded portals, separate email/KB/teams per brand |
| **Time Tracking** | Per-ticket time logging, billable/non-billable, ERPNext Projects integration |
| **Internal Notes** | Private agent notes on tickets, @mentions, visually distinct from customer replies |

### Out of Scope (Deferred to Phase 2+)

| Feature | Phase | Rationale |
|---------|-------|-----------|
| AI Copilot (draft suggestions, summarization) | Phase 2 | Requires LLM integration infrastructure not yet built |
| AI Agent (autonomous resolution, 40%+ deflection) | Phase 3 | Requires Phase 2 AI Copilot foundation and action integrations |
| WhatsApp/SMS/Social channels | Phase 2 | Lower priority than live chat; requires channel abstraction layer built in Phase 1 |
| Problem Management (RCA, KEDB) | Phase 2-3 | New ITIL practice; depends on enhanced incident management from Phase 1 |
| Change Enablement (RFC, CAB) | Phase 3 | Enterprise ITIL; requires workflow automation maturity from Phase 1 |
| CMDB / IT Asset Management | Phase 3 | Enterprise ITIL; high implementation effort; depends on ERPNext Asset integration |
| Skills-based / language-based routing | Phase 2 | Requires AI triage capabilities |
| Voice/Phone (WebRTC) | Phase 4 | Very high effort |
| Local LLM Marketplace | Phase 4 | Innovation phase |

### Phase 1 Architectural Decisions

1. **Extend HD Ticket** with `record_type` (Incident/Service Request), `impact`, `urgency`, `category`, `sub_category` fields rather than creating separate DocTypes -- maintains backward compatibility
2. **Channel abstraction layer** -- normalize all messages (email, chat) into unified format to enable future channel additions (WhatsApp, SMS) in Phase 2
3. **Feature flags** -- all new ITIL fields use progressive disclosure; "Simple Mode" (single priority field) is default, "ITIL Mode" toggle reveals impact/urgency/category
4. **Leverage Frappe Workflow engine** for article review lifecycle and future approval workflows
5. **SLA OLA/UC preparation** -- add `agreement_type` field to HD Service Level Agreement now; full OLA/UC tracking deferred to Phase 2

---

## User Journeys

### UJ-01: Agent Handles Ticket with ITIL Context

**Persona:** Amara (Support Agent)
**Trigger:** New ticket arrives via email
**ITIL Practice:** Incident Management

1. Amara sees new ticket in her queue with auto-calculated priority (from impact x urgency matrix)
2. System has auto-categorized the ticket based on ticket type template (Category: "Billing", Sub-category: "Invoice Dispute")
3. Amara opens the ticket; sidebar shows customer's ERPNext order history and recent tickets
4. She adds an internal note: "@Rajesh - this is the third invoice dispute from this customer this week, flagging for review"
5. Rajesh receives @mention notification
6. Amara drafts a response using a saved reply template, customizes it, and sends
7. She logs 15 minutes of time (billable) on the ticket
8. On resolution, customer receives CSAT survey email within 24 hours

**Functional Requirements Traced:** FR-IM-01, FR-IM-02, FR-IM-03, FR-IM-04, FR-IN-01, FR-TT-01, FR-CS-01

### UJ-02: Manager Reviews Team Performance

**Persona:** Rajesh (Support Team Manager)
**Trigger:** Weekly performance review
**ITIL Practice:** Continual Improvement, Service Level Management

1. Rajesh opens the SLA compliance dashboard; sees 87% compliance this week (up from 82%)
2. Drills down by agent to find two agents below 80% compliance
3. Opens CSAT dashboard; overall score is 3.7/5, up from 3.4 last month
4. Creates a custom report: "Tickets by Category, grouped by Priority, filtered to last 30 days"
5. Schedules this report for weekly email delivery to his VP
6. Exports the data to Excel for the quarterly business review
7. Reviews time tracking summary: average resolution effort is 22 minutes, billable ratio 65%

**Functional Requirements Traced:** FR-SL-01, FR-SL-02, FR-CS-02, FR-CR-01, FR-CR-02, FR-TT-02

### UJ-03: Customer Gets Help via Live Chat

**Persona:** Maria (End Customer)
**Trigger:** Maria visits the company website and needs help
**ITIL Practice:** Service Desk

1. Maria clicks the chat widget on the company's website
2. Widget shows "Support is online" with estimated wait time
3. Maria types her question; typing indicator shows on agent side
4. Agent Amara picks up the chat; sees Maria's customer profile and recent orders in sidebar
5. Amara resolves the issue in real-time via chat
6. Chat automatically converts to an HD Ticket record with full transcript
7. Maria receives CSAT survey after resolution
8. If Amara is unavailable, widget shows "Leave a message" form that creates an email ticket

**Functional Requirements Traced:** FR-LC-01, FR-LC-02, FR-LC-03, FR-LC-04, FR-CS-01

### UJ-04: Agent Manages Major Incident

**Persona:** Amara (Support Agent) + Rajesh (Manager)
**Trigger:** Critical service outage affecting multiple customers
**ITIL Practice:** Incident Management (Major Incident)

1. Multiple tickets arrive about the same issue; Amara flags the first as "Major Incident"
2. System activates major incident workflow: auto-notifies Rajesh (manager) and escalation contacts
3. Rajesh links 5 related tickets to the major incident ticket
4. Major incident dashboard shows all linked tickets, affected customers count, and elapsed time
5. Amara posts status updates on the major incident; all linked tickets receive the update
6. On resolution, system prompts for post-incident review notes
7. MTTR report captures total duration from first report to resolution

**Functional Requirements Traced:** FR-IM-05, FR-IM-06, FR-IM-07, FR-IM-08

### UJ-05: KB Author Manages Article Lifecycle

**Persona:** Amara (Agent, also KB contributor)
**Trigger:** Amara resolves a frequently-asked question and wants to create a KB article
**ITIL Practice:** Knowledge Management

1. From the ticket view, Amara clicks "Create KB Article from Ticket"
2. System pre-fills article with ticket subject and resolution details
3. Amara edits the article, selects category, and submits as "Draft"
4. Article enters review workflow; Rajesh (reviewer) receives notification
5. Rajesh reviews, suggests edits, approves; article status changes to "Published"
6. System sets review date to 90 days from publication
7. Article appears in customer-facing knowledge base and is linked to the originating ticket
8. When review date arrives, author receives reminder to verify article accuracy

**Functional Requirements Traced:** FR-KB-01, FR-KB-02, FR-KB-03, FR-KB-04, FR-KB-05

### UJ-06: Admin Configures Workflow Automation

**Persona:** Chen (IT Administrator)
**Trigger:** Chen wants to automate ticket routing and escalation
**ITIL Practice:** Incident Management, Service Level Management

1. Chen opens the Automation Rule builder
2. Creates rule: "IF ticket priority = Critical AND team = unassigned THEN assign to On-Call Team AND notify #urgent-support Slack channel AND set SLA to Critical-SLA"
3. Creates another rule: "IF SLA breach warning at 15 minutes THEN escalate to team manager AND send email alert"
4. Tests rules with sample ticket data before activating
5. Dashboard shows rule execution statistics: how many times each rule fired, success rate

**Functional Requirements Traced:** FR-WA-01, FR-WA-02, FR-WA-03, FR-SL-03

---

## Functional Requirements

Requirements use MoSCoW priority: **Must** (required for Phase 1 success), **Should** (high value, implement if capacity allows), **Could** (desirable, can defer), **Won't** (explicitly out of Phase 1).

### FR-IM: Incident Management Enhancement

#### FR-IM-01: Impact and Urgency Fields

**Priority:** Must
**User Story:** As a support agent, I can set impact (High/Medium/Low) and urgency (High/Medium/Low) on a ticket so that priority is calculated automatically from the ITIL priority matrix.
**Acceptance Criteria:**
- Impact field added to HD Ticket with values: High, Medium, Low
- Urgency field added to HD Ticket with values: High, Medium, Low
- Priority auto-calculated from Impact x Urgency matrix (e.g., High Impact + High Urgency = P1 Critical)
- Priority matrix is configurable by admin via HD Settings
- Legacy tickets without impact/urgency retain their manually-set priority
- "Simple Mode" (default): single priority dropdown; "ITIL Mode": reveals impact + urgency with auto-calculated priority
- Mode toggle available per-organization in HD Settings

**Dependencies:** None
**Success Metric:** >90% of new tickets have impact and urgency set within 60 days of launch

#### FR-IM-02: Multi-Level Categorization

**Priority:** Must
**User Story:** As a support agent, I can categorize tickets with Category and Sub-category so that reporting and routing can use granular classification.
**Acceptance Criteria:**
- Category field (Link to new HD Ticket Category DocType) added to HD Ticket
- Sub-category field (filtered by selected Category) added to HD Ticket
- Admin can configure category > sub-category hierarchy
- Category is required on ticket resolution (configurable)
- Existing HD Ticket Type field retained for backward compatibility; category is additive
- Reports can filter and group by category and sub-category

**Dependencies:** None
**Success Metric:** >80% of resolved tickets have category assigned within 90 days

#### FR-IM-03: Incident Models/Templates

**Priority:** Should
**User Story:** As an admin, I can create incident models (predefined templates with pre-set fields) so that common incident types are logged consistently.
**Acceptance Criteria:**
- HD Incident Model DocType with fields: name, description, default_category, default_sub_category, default_priority, default_team, checklist_items, auto_actions
- When agent selects an incident model during ticket creation, all predefined fields populate automatically
- At least 5 incident models ship as defaults (e.g., Password Reset, System Outage, Access Request, Hardware Failure, Software Bug)
- Models can include checklist items that agents must complete before resolution

**Dependencies:** FR-IM-02 (categorization)
**Success Metric:** >30% of new tickets created using an incident model within 90 days

#### FR-IM-04: Related Incidents Linking

**Priority:** Must
**User Story:** As a support agent, I can link related tickets together so that patterns are visible and updates can propagate.
**Acceptance Criteria:**
- "Related Tickets" child table added to HD Ticket
- Bidirectional linking: linking Ticket A to Ticket B also shows the link on Ticket B
- Link types: "Related to", "Caused by", "Duplicate of"
- "Duplicate of" link auto-closes the duplicate with reference to the primary ticket
- Agent can view all linked tickets in a sidebar panel

**Dependencies:** None
**Success Metric:** >15% of tickets linked to at least one other ticket within 90 days

#### FR-IM-05: Major Incident Flag and Workflow

**Priority:** Must
**User Story:** As a support agent, I can flag a ticket as a Major Incident to trigger an expedited response process with management notification.
**Acceptance Criteria:**
- `is_major_incident` checkbox on HD Ticket
- When checked, system sends immediate notification to configured escalation contacts (email + in-app)
- Major Incident dashboard view: lists all active major incidents with elapsed time, linked ticket count, affected customer count
- Status updates on a major incident can optionally propagate to all linked tickets
- Post-incident review fields appear on resolution: root_cause_summary, corrective_actions, prevention_measures
- Major incidents are excluded from standard SLA and tracked against a separate Major Incident SLA

**Dependencies:** FR-IM-04 (related incidents linking)
**Success Metric:** 100% of major incidents have post-incident review completed within 48 hours

#### FR-IM-06: MTTR and Incident Reporting

**Priority:** Must
**User Story:** As a team manager, I can view Mean Time to Resolve (MTTR), incident volume trends, and category distribution so that I can identify improvement areas.
**Acceptance Criteria:**
- MTTR calculated per priority level, per team, per category (30/60/90-day rolling)
- Incident volume trend chart (daily/weekly/monthly) with comparison to prior period
- Category distribution pie chart showing top 10 categories by volume
- All metrics available as dashboard widgets and as exportable reports
- MTTR excludes time in "Waiting on Customer" status

**Dependencies:** FR-IM-01, FR-IM-02
**Success Metric:** Manager accesses incident reports at least weekly (measured via telemetry)

---

### FR-IN: Internal Notes

#### FR-IN-01: Private Agent Notes

**Priority:** Must
**User Story:** As a support agent, I can add private notes on a ticket that are visible only to other agents, so that I can collaborate internally without exposing information to customers.
**Acceptance Criteria:**
- Internal note type added to HD Ticket communication (distinct from Reply and Comment)
- Notes are visually distinct: different background color, "Internal Note" badge, lock icon
- Notes are NEVER visible in customer portal or customer emails
- @mention support: typing "@" shows agent list; mentioned agents receive in-app notification
- Notes support rich text (bold, italic, links, code blocks) and file attachments
- Permission check: only users with Agent role can view internal notes

**Dependencies:** None
**Success Metric:** >50% of tickets have at least one internal note within 60 days

---

### FR-CS: CSAT Surveys

#### FR-CS-01: Post-Resolution CSAT Survey

**Priority:** Must
**User Story:** As a customer, I receive a satisfaction survey after my ticket is resolved so that the support team can measure and improve service quality.
**Acceptance Criteria:**
- Email survey sent automatically within configurable window (default: 24 hours) after ticket resolution
- Survey contains 1-5 star rating + optional free-text comment field
- Survey link is a one-click-to-rate design (clicking a star in the email submits the rating)
- Survey response stored in new HD CSAT Response DocType linked to HD Ticket
- Unsubscribe link in survey email; unsubscribed customers do not receive future surveys
- Survey frequency limit: maximum 1 survey per customer per 7 days (configurable)
- Survey template is customizable per brand (subject line, body text, branding)

**Dependencies:** Multi-brand support (FR-MB-01) for per-brand templates; works without it using default template
**Success Metric:** >60% CSAT response rate within 90 days (SC-01)

#### FR-CS-02: CSAT Dashboard

**Priority:** Must
**User Story:** As a team manager, I can view CSAT scores by agent, team, time period, and category so that I can identify satisfaction trends and coaching opportunities.
**Acceptance Criteria:**
- Dashboard showing: overall CSAT score (30-day rolling), score by agent, score by team, score trend over time
- Drill-down from score to individual survey responses
- Filter by date range, team, agent, category, priority
- Rating distribution chart (count of 1-star, 2-star, etc.)
- Negative feedback alert: scores of 1-2 stars trigger notification to team manager
- Dashboard accessible from agent home page as optional widget

**Dependencies:** FR-CS-01
**Success Metric:** CSAT dashboard viewed by managers at least weekly

---

### FR-LC: Live Chat Widget

#### FR-LC-01: Embeddable Chat Widget

**Priority:** Must
**User Story:** As a website visitor, I can open a chat widget on the company's website to get real-time support without leaving the page.
**Acceptance Criteria:**
- JavaScript snippet (single `<script>` tag) installs widget on any website
- Widget supports custom branding: primary color, logo, greeting message, position (bottom-right/bottom-left)
- Widget shows agent availability status: "Online" (agents available), "Away" (outside business hours), "Busy" (all agents occupied)
- Pre-chat form collects: name, email, subject (all configurable as required/optional/hidden)
- Chat supports: text messages, file attachments (images, documents up to 10MB), links
- Widget is responsive: works on desktop (400px wide panel) and mobile (full-screen)
- Widget loads asynchronously; does not block host page rendering; total bundle size < 50KB gzipped

**Dependencies:** Socket.IO infrastructure (already exists in Frappe)
**Success Metric:** >10% of new tickets via live chat within 90 days (SC-03)

#### FR-LC-02: Real-Time Chat Experience

**Priority:** Must
**User Story:** As a customer chatting live, I see typing indicators, read receipts, and receive responses in real-time so that the experience feels like a modern messaging app.
**Acceptance Criteria:**
- Message delivery latency < 200ms end-to-end (95th percentile)
- Typing indicator shown to both customer and agent
- Message status indicators: sent, delivered, read
- Agent can see customer's previous tickets and profile in sidebar during chat
- Chat session persists across page navigation on the customer's website (via localStorage)
- If no agent responds within configurable timeout (default: 2 minutes), auto-message: "We're experiencing high volume. You can wait or leave a message and we'll email you."

**Dependencies:** FR-LC-01
**Success Metric:** Average chat response time < 60 seconds

#### FR-LC-03: Chat-to-Ticket Conversion

**Priority:** Must
**User Story:** As a support agent, every chat conversation automatically creates an HD Ticket record so that all interactions are tracked and reportable.
**Acceptance Criteria:**
- Chat creates HD Ticket with source="Chat" on first customer message
- Full chat transcript stored as ticket communications (each message as a separate entry)
- If customer leaves without resolution, ticket remains open for follow-up via email
- Agent can continue conversation via email after chat ends
- Chat tickets follow same SLA rules as email tickets (with separate SLA targets configurable)

**Dependencies:** FR-LC-01, FR-LC-02
**Success Metric:** 100% of chat conversations have corresponding HD Ticket record

#### FR-LC-04: Agent Chat Interface

**Priority:** Must
**User Story:** As a support agent, I can handle multiple simultaneous chat conversations from within my existing agent workspace.
**Acceptance Criteria:**
- Chat queue visible in agent workspace alongside ticket list
- Agent can handle up to 5 concurrent chats (configurable per agent)
- Unread message count badge on each active chat
- Agent can transfer chat to another agent or team with context preserved
- Agent can toggle availability: Online, Away, Offline
- Agent receives desktop notification for new chat assignments

**Dependencies:** FR-LC-01, FR-LC-02
**Success Metric:** Agents handle average 3+ concurrent chats

---

### FR-WA: Workflow Automation

#### FR-WA-01: Visual Rule Builder

**Priority:** Must
**User Story:** As an admin, I can create automation rules using a visual if-then-else interface so that routine ticket operations happen automatically.
**Acceptance Criteria:**
- HD Automation Rule DocType with: name, description, enabled, trigger, conditions[], actions[]
- **Triggers (minimum 10):** ticket_created, ticket_updated, ticket_assigned, ticket_resolved, ticket_reopened, sla_warning, sla_breached, csat_received, chat_started, chat_ended
- **Conditions:** any HD Ticket field (priority, status, category, team, agent, customer, source, custom fields) with operators (equals, not_equals, contains, greater_than, less_than, is_set, is_not_set)
- **Actions (minimum 10):** assign_to_agent, assign_to_team, set_priority, set_status, set_category, add_tag, send_email, send_notification, add_internal_note, trigger_webhook
- Conditions support AND/OR logic with grouping
- Rule execution order configurable via drag-and-drop priority
- Dry-run mode: test rule against sample ticket without executing actions

**Dependencies:** None
**Success Metric:** >10 active automation rules within 90 days (SC-09)

#### FR-WA-02: Rule Execution Logging

**Priority:** Should
**User Story:** As an admin, I can see a log of every automation rule execution so that I can debug and optimize my rules.
**Acceptance Criteria:**
- HD Automation Log DocType: rule_name, ticket, trigger_event, conditions_evaluated, actions_executed, execution_time_ms, status (success/failure/skipped), timestamp
- Log retention: configurable, default 30 days
- Dashboard showing: rules fired per day, top 10 most-fired rules, failure rate per rule

**Dependencies:** FR-WA-01
**Success Metric:** <1% rule execution failure rate

#### FR-WA-03: SLA-Based Automation Triggers

**Priority:** Must
**User Story:** As an admin, I can trigger automations based on SLA events (warning thresholds, breaches) so that at-risk tickets get proactive attention.
**Acceptance Criteria:**
- SLA warning trigger fires at configurable thresholds: 30, 15, and 5 minutes before breach (configurable per SLA)
- SLA breach trigger fires when SLA target is exceeded
- Triggers can be used as conditions in automation rules (e.g., "IF sla_warning AND priority=Critical THEN escalate")
- Agent receives in-app and email notification for SLA warnings on their assigned tickets

**Dependencies:** FR-WA-01, FR-SL-01
**Success Metric:** SLA breach rate decreases by 15% (SC-04)

---

### FR-CR: Custom Report Builder

#### FR-CR-01: Report Builder Interface

**Priority:** Must
**User Story:** As a team manager, I can build custom reports by selecting data source, fields, filters, and grouping so that I get exactly the data I need without developer help.
**Acceptance Criteria:**
- HD Custom Report DocType: name, description, data_source (HD Ticket, HD CSAT Response, HD Article, HD Time Entry), fields[], filters[], group_by, sort_by, chart_type
- Drag-and-drop field selection from available columns
- Filter builder with same operators as automation rules
- Group-by with up to 3 levels
- Chart types: bar, line, pie, table (raw data)
- Report preview updates in real-time as builder configuration changes
- Save and name reports for reuse

**Dependencies:** None
**Success Metric:** >20 custom reports created within 90 days (SC-05)

#### FR-CR-02: Report Scheduling and Export

**Priority:** Should
**User Story:** As a team manager, I can schedule reports for automatic email delivery and export data to CSV/Excel so that I can share insights with stakeholders.
**Acceptance Criteria:**
- Schedule options: daily, weekly (select day), monthly (select date)
- Email delivery to configurable recipient list with report attached
- Export formats: CSV, Excel (.xlsx)
- Exported data includes all filters and grouping applied
- Report links are shareable (with permission check)

**Dependencies:** FR-CR-01
**Success Metric:** >5 scheduled reports active within 90 days

---

### FR-SL: Enhanced SLA Management

#### FR-SL-01: Business Hours and Holiday Calendars

**Priority:** Must
**User Story:** As an admin, I can configure SLA timers to only count during business hours and exclude holidays so that SLA targets reflect actual working time.
**Acceptance Criteria:**
- Business hours configurable per team (e.g., Mon-Fri 9:00-18:00)
- Multiple timezone support: each team can have its own timezone
- Holiday calendar (HD Service Holiday List) linked to SLA; SLA pauses on holidays
- SLA timer pauses outside business hours and resumes at next business hour start
- Existing SLA pause-on-status functionality preserved (e.g., pause when "Waiting on Customer")
- SLA recalculation runs as background job, not blocking ticket operations

**Dependencies:** None (enhances existing HD Service Level Agreement)
**Success Metric:** SLA breach rate decreases by 15% (SC-04)

#### FR-SL-02: Proactive Breach Alerts

**Priority:** Must
**User Story:** As a support agent, I receive warnings before an SLA is about to breach so that I can take action to prevent the breach.
**Acceptance Criteria:**
- Warning thresholds configurable per SLA priority level (default: 30, 15, 5 minutes before breach)
- Alert channels: in-app notification (toast + badge), email (optional)
- Alert recipients: assigned agent, team manager (configurable)
- Agent dashboard highlights tickets approaching SLA breach with color coding: yellow (>30 min), orange (15-30 min), red (<15 min)
- Breach alerts can trigger automation rules (FR-WA-03)

**Dependencies:** FR-SL-01
**Success Metric:** >50% of SLA warnings result in action before breach

#### FR-SL-03: SLA Compliance Dashboard

**Priority:** Must
**User Story:** As a team manager, I can view real-time SLA compliance metrics with drill-down capability so that I can monitor service quality.
**Acceptance Criteria:**
- Overall SLA compliance percentage (response and resolution) for configurable time period
- Drill-down by: team, agent, priority, category
- Trend chart: SLA compliance over time (daily/weekly/monthly)
- Breach analysis: top reasons for breach (by category, by time-of-day)
- Comparison view: this period vs last period
- Dashboard is a configurable widget on agent home page

**Dependencies:** FR-SL-01, FR-IM-01 (for priority-based drill-down)
**Success Metric:** Managers view SLA dashboard at least weekly

#### FR-SL-04: OLA/UC Field Preparation

**Priority:** Could
**User Story:** As an admin, I can tag an SLA as type SLA, OLA, or UC so that the system is ready for full OLA/UC tracking in Phase 2.
**Acceptance Criteria:**
- `agreement_type` Select field added to HD Service Level Agreement: values "SLA" (default), "OLA", "UC"
- `internal_team` Link field (for OLA) and `vendor` Data field (for UC) added
- No enforcement logic in Phase 1; fields are informational only
- UI shows agreement type badge on SLA list view

**Dependencies:** None
**Success Metric:** N/A (preparation for Phase 2)

---

### FR-KB: Knowledge Base Improvements

#### FR-KB-01: Article Review Workflow

**Priority:** Must
**User Story:** As a KB author, I submit articles for review before publication so that only vetted content reaches customers.
**Acceptance Criteria:**
- Article lifecycle states: Draft > In Review > Published > Archived
- State transitions governed by Frappe Workflow engine
- "Submit for Review" action on Draft articles; assigns to configured reviewer(s)
- Reviewer can: Approve (moves to Published), Request Changes (returns to Draft with comments), Reject (moves to Archived)
- Email notification to author on each state transition
- Only Published articles appear in customer-facing knowledge base
- Articles in "In Review" are visible to agents for internal reference

**Dependencies:** None (enhances existing HD Article)
**Success Metric:** >50% of published articles have gone through review workflow (SC-08)

#### FR-KB-02: Article Versioning

**Priority:** Should
**User Story:** As a KB author, I can see the history of changes to an article and revert to a previous version if needed.
**Acceptance Criteria:**
- Each save of an HD Article creates a version record (HD Article Version)
- Version record stores: content snapshot, author, timestamp, change summary
- Version comparison view: side-by-side diff of any two versions
- Revert action: restore article content from any previous version
- Version count displayed on article detail view

**Dependencies:** FR-KB-01
**Success Metric:** >20% of articles have 2+ versions within 6 months

#### FR-KB-03: Review Dates and Expiry

**Priority:** Should
**User Story:** As a KB manager, I can set review dates on articles so that content is periodically verified for accuracy.
**Acceptance Criteria:**
- `review_date` field on HD Article (auto-set to 90 days from publication, configurable)
- `reviewed_by` field tracking last reviewer
- When review_date passes, article author receives email reminder
- Dashboard widget: "Articles Due for Review" showing overdue and upcoming reviews
- Overdue articles flagged with visual indicator in article list view

**Dependencies:** FR-KB-01
**Success Metric:** <10% of articles overdue for review at any time

#### FR-KB-04: Ticket-Article Linking

**Priority:** Must
**User Story:** As a support agent, I can link a KB article to a ticket so that the resolution knowledge is connected to the incidents it addresses.
**Acceptance Criteria:**
- "Link Article" action on ticket view; search and select from published articles
- "Create Article from Ticket" action that pre-fills article with ticket subject and resolution content
- Linked articles shown in ticket sidebar
- Article detail view shows list of linked tickets (count and recent 10)
- Linking is bidirectional and stored in a child table

**Dependencies:** None
**Success Metric:** >10% of resolved tickets linked to a KB article within 90 days

#### FR-KB-05: Internal-Only Articles

**Priority:** Should
**User Story:** As a KB author, I can mark articles as internal-only so that sensitive procedures are available to agents but hidden from customers.
**Acceptance Criteria:**
- `internal_only` checkbox on HD Article
- Internal articles visible in agent workspace KB search
- Internal articles excluded from customer portal and public knowledge base
- Internal articles visually distinguished (badge/icon) in agent view

**Dependencies:** None
**Success Metric:** >10 internal-only articles created within 90 days

---

### FR-MB: Multi-Brand Support

#### FR-MB-01: Branded Portals

**Priority:** Should
**User Story:** As an admin managing multiple brands, I can configure separate portals with distinct branding, email addresses, and KB content per brand from a single Helpdesk instance.
**Acceptance Criteria:**
- HD Brand DocType: name, logo, primary_color, support_email, portal_domain, default_team, default_sla
- Tickets auto-tagged with brand based on receiving email address or portal domain
- Customer portal shows brand-specific logo, colors, and KB articles
- Agents can filter ticket list by brand
- CSAT survey emails use brand-specific template
- Live chat widget configurable per brand (separate snippet per brand)

**Dependencies:** None
**Success Metric:** >2 brands configured for organizations with multi-brand needs

---

### FR-TT: Time Tracking

#### FR-TT-01: Per-Ticket Time Logging

**Priority:** Must
**User Story:** As a support agent, I can log time spent on a ticket so that effort is tracked for reporting and billing.
**Acceptance Criteria:**
- HD Time Entry DocType: ticket (Link), agent (Link), duration_minutes, billable (checkbox), description, timestamp
- Manual entry: agent enters duration and description
- Timer mode: start/stop timer with automatic duration calculation
- Multiple time entries per ticket
- Time summary on ticket view: total time, billable time, entry list

**Dependencies:** None
**Success Metric:** >80% of resolved tickets have time entries within 90 days (SC-06)

#### FR-TT-02: Time Reporting and ERPNext Integration

**Priority:** Should
**User Story:** As a team manager, I can view time reports by agent, team, and period, and sync billable time to ERPNext Projects for invoicing.
**Acceptance Criteria:**
- Time report: hours by agent per period, billable vs non-billable breakdown
- Average time per ticket by category and priority
- ERPNext Projects integration: sync billable time entries as Timesheet records (if ERPNext installed)
- Integration is optional and configurable; works without ERPNext

**Dependencies:** FR-TT-01
**Success Metric:** Time data used in at least 5 custom reports

---

## Non-Functional Requirements

### NFR-P: Performance

| ID | Requirement | Target | Measurement |
|----|-------------|--------|-------------|
| NFR-P-01 | Agent workspace page load | < 2 seconds on standard hardware (4-core, 8GB RAM) | Lighthouse performance score or browser DevTools |
| NFR-P-02 | Ticket search response | < 500ms for full-text search across 100K tickets | API response time measured by APM |
| NFR-P-03 | Live chat message delivery | < 200ms end-to-end (95th percentile) | Socket.IO latency measurement |
| NFR-P-04 | SLA recalculation (background) | < 5 seconds per 1000 tickets | Background job execution time |
| NFR-P-05 | Chat widget bundle size | < 50KB gzipped | Build output measurement |
| NFR-P-06 | Automation rule evaluation | < 100ms per rule per ticket event | Background job metrics |
| NFR-P-07 | Dashboard widget load | < 1 second per widget | Frontend performance monitoring |

### NFR-S: Scalability

| ID | Requirement | Target | Measurement |
|----|-------------|--------|-------------|
| NFR-S-01 | Concurrent agents | Support 500 concurrent agents on single instance | Load testing with k6 or Locust |
| NFR-S-02 | Concurrent chat sessions | Support 200 simultaneous chat sessions | Socket.IO connection monitoring |
| NFR-S-03 | Monthly ticket volume | Handle 100K tickets/month without degradation | Database query performance monitoring |
| NFR-S-04 | Automation throughput | Process 1000 rule evaluations/minute | Redis Queue metrics |

### NFR-SE: Security

| ID | Requirement | Target |
|----|-------------|--------|
| NFR-SE-01 | Internal notes isolation | Internal notes NEVER exposed via customer portal, API (without Agent role), or email |
| NFR-SE-02 | Chat widget authentication | Chat sessions authenticated via token; no access to other customers' data |
| NFR-SE-03 | CSAT survey security | Survey links contain single-use token; cannot be reused or enumerated |
| NFR-SE-04 | Automation rule permissions | Only users with System Manager or Helpdesk Admin role can create/edit automation rules |
| NFR-SE-05 | Report data access | Custom reports respect existing Frappe permission model; agents see only permitted data |
| NFR-SE-06 | XSS prevention in chat | All chat messages sanitized server-side before storage and display |

### NFR-U: Usability

| ID | Requirement | Target |
|----|-------------|--------|
| NFR-U-01 | Progressive disclosure | ITIL fields (impact, urgency, category) hidden by default in "Simple Mode"; visible in "ITIL Mode" |
| NFR-U-02 | Agent onboarding | New agent productive within 30 minutes of first login |
| NFR-U-03 | Mobile chat widget | Chat widget fully functional on mobile browsers (iOS Safari, Chrome Android) |
| NFR-U-04 | Accessibility | WCAG 2.1 AA compliance for all new UI components |
| NFR-U-05 | Keyboard navigation | All new features accessible via keyboard; no mouse-only interactions |

### NFR-A: Availability

| ID | Requirement | Target |
|----|-------------|--------|
| NFR-A-01 | Core ticketing availability | Core ticket operations (create, update, resolve) unaffected by chat or automation failures |
| NFR-A-02 | Graceful degradation | If Socket.IO is unavailable, chat widget shows "Leave a message" form; no error displayed |
| NFR-A-03 | Automation failure isolation | A failing automation rule does not block ticket operations; failure logged and rule auto-disabled after 10 consecutive failures |

### NFR-M: Maintainability

| ID | Requirement | Target |
|----|-------------|--------|
| NFR-M-01 | Test coverage | Minimum 80% unit test coverage on all new backend code |
| NFR-M-02 | API coverage | All new DocTypes accessible via REST API with standard Frappe CRUD |
| NFR-M-03 | Channel abstraction | Chat implementation uses abstract channel interface to enable future WhatsApp/SMS/social channel additions without modifying core ticket logic |
| NFR-M-04 | Feature flags | All ITIL-specific features toggleable via HD Settings without code deployment |

---

## Dependencies

### Technical Dependencies

| Dependency | Required By | Risk | Mitigation |
|-----------|------------|------|-----------|
| Frappe Framework v15+ | All features | Low | Internally controlled |
| Socket.IO (in Frappe) | Live chat, collision detection | Low | Already integrated |
| Redis/RQ (in Frappe) | Automation rules, SLA recalculation, background jobs | Low | Already integrated |
| Vue 3 + Frappe UI | All frontend components | Low | Already in use |
| Frappe Workflow engine | KB article lifecycle | Low | Built-in Frappe feature |
| ERPNext (optional) | Time tracking sync, customer context | Low | Features work without ERPNext; integration is additive |

### Internal Feature Dependencies

| Feature | Depends On | Blocking? |
|---------|-----------|-----------|
| FR-IM-03 (Incident Models) | FR-IM-02 (Categorization) | No -- can ship without but less useful |
| FR-IM-05 (Major Incidents) | FR-IM-04 (Related Linking) | Yes -- major incidents require linking |
| FR-IM-06 (Reporting) | FR-IM-01, FR-IM-02 | Yes -- reports need impact/urgency/category data |
| FR-CS-02 (CSAT Dashboard) | FR-CS-01 (CSAT Surveys) | Yes -- no data without surveys |
| FR-LC-02 (Chat Experience) | FR-LC-01 (Widget) | Yes -- sequential |
| FR-LC-03 (Chat-to-Ticket) | FR-LC-01, FR-LC-02 | Yes -- sequential |
| FR-WA-03 (SLA Triggers) | FR-WA-01, FR-SL-01 | Yes -- depends on both |
| FR-CR-02 (Scheduling) | FR-CR-01 (Builder) | Yes -- sequential |
| FR-SL-02 (Breach Alerts) | FR-SL-01 (Business Hours) | Yes -- accurate alerts need business hours |
| FR-SL-03 (SLA Dashboard) | FR-SL-01 | Yes -- dashboard needs accurate SLA data |
| FR-KB-02 (Versioning) | FR-KB-01 (Workflow) | No -- independent but complementary |
| FR-TT-02 (Time Reports) | FR-TT-01 (Time Logging) | Yes -- no data without logging |

### Recommended Implementation Order

**Sprint 1-2 (Weeks 1-4):** FR-IN-01 (Internal Notes), FR-IM-01 (Impact/Urgency), FR-IM-02 (Categorization), FR-TT-01 (Time Tracking)
**Sprint 3-4 (Weeks 5-8):** FR-CS-01 (CSAT Surveys), FR-IM-04 (Related Linking), FR-SL-01 (Business Hours SLA), FR-KB-01 (Article Workflow)
**Sprint 5-6 (Weeks 9-12):** FR-WA-01 (Automation Builder), FR-IM-05 (Major Incidents), FR-SL-02 (Breach Alerts), FR-KB-04 (Ticket-Article Linking)
**Sprint 7-8 (Weeks 13-16):** FR-LC-01 through FR-LC-04 (Live Chat), FR-CS-02 (CSAT Dashboard)
**Sprint 9-10 (Weeks 17-20):** FR-CR-01 (Report Builder), FR-SL-03 (SLA Dashboard), FR-IM-06 (Incident Reporting)
**Sprint 11-12 (Weeks 21-24):** FR-MB-01 (Multi-Brand), FR-CR-02 (Report Scheduling), FR-KB-02/03/05 (Versioning, Reviews, Internal), FR-IM-03 (Incident Models), FR-WA-02 (Rule Logging)

---

## New DocTypes Required

| DocType | Purpose | Key Fields |
|---------|---------|-----------|
| HD Ticket Category | Multi-level ticket categorization | name, parent_category, description, is_active |
| HD CSAT Response | Customer satisfaction survey responses | ticket (Link), rating (Int 1-5), comment (Text), customer, agent, team, timestamp |
| HD CSAT Survey Template | Per-brand survey templates | brand, subject, body, enabled |
| HD Automation Rule | Workflow automation rules | name, description, enabled, trigger, conditions (JSON), actions (JSON), priority |
| HD Automation Log | Rule execution audit trail | rule (Link), ticket (Link), trigger_event, actions_executed, status, timestamp |
| HD Time Entry | Per-ticket time tracking | ticket (Link), agent (Link), duration_minutes, billable, description, timestamp |
| HD Incident Model | Predefined incident templates | name, description, default_category, default_priority, default_team, checklist_items |
| HD Article Version | KB article version history | article (Link), content, author, timestamp, change_summary |
| HD Brand | Multi-brand configuration | name, logo, primary_color, support_email, portal_domain, default_team, default_sla |
| HD Chat Session | Live chat session tracking | ticket (Link), customer, agent, status, started_at, ended_at, message_count |

## Existing DocType Modifications

| DocType | New Fields | Purpose |
|---------|-----------|---------|
| HD Ticket | impact, urgency, category (Link), sub_category, is_major_incident, record_type, related_tickets (Table), post_incident_review, root_cause_summary, corrective_actions | ITIL incident management |
| HD Article | review_date, reviewed_by, internal_only, version_count | KB lifecycle management |
| HD Service Level Agreement | agreement_type, internal_team, vendor | OLA/UC preparation |
| HD Settings | itil_mode_enabled, simple_mode_default, csat_enabled, chat_enabled, automation_enabled, major_incident_contacts | Feature flags and configuration |

---

## Risks and Mitigations

| Risk | Likelihood | Impact | Mitigation |
|------|-----------|--------|-----------|
| WebSocket scalability for live chat at volume | Medium | High | Load test at 1000 concurrent connections in Sprint 6; implement Socket.IO horizontal clustering if needed |
| Agent overwhelm from ITIL field complexity | Medium | High | Progressive disclosure ("Simple Mode" default); auto-calculate priority from matrix; make category optional initially |
| CSAT survey fatigue (low response rate) | Medium | Medium | One-click rating in email; frequency limits; concise survey design |
| Automation rule infinite loops | Low | High | Loop detection: max 5 rule executions per ticket per minute; auto-disable looping rules |
| Phase 1 scope too ambitious for 2-3 devs in 6 months | Medium | High | MoSCoW prioritization; "Should" and "Could" items deferred if behind schedule; decision gate at Sprint 6 |
| Chat widget performance impact on host sites | Low | High | Async loading; shadow DOM isolation; <50KB bundle; performance testing on slow connections |
| Data migration for existing tickets lacking ITIL fields | Low | Medium | Legacy tickets retain manual priority; impact/urgency default to null; no forced backfill |

---

## Appendix A: Priority Matrix Configuration (Default)

| | High Urgency | Medium Urgency | Low Urgency |
|---|---|---|---|
| **High Impact** | P1 - Critical | P2 - High | P3 - Medium |
| **Medium Impact** | P2 - High | P3 - Medium | P4 - Low |
| **Low Impact** | P3 - Medium | P4 - Low | P5 - Planning |

## Appendix B: ITIL Practice Coverage After Phase 1

| ITIL Practice | Pre-Phase 1 | Post-Phase 1 | Key Additions |
|--------------|-------------|-------------|---------------|
| Incident Management | 40% | 75% | Impact/urgency, categorization, major incidents, related linking, MTTR reporting |
| Service Desk | 75% | 90% | Live chat, internal notes, CSAT surveys, time tracking |
| Service Level Management | 55% | 80% | Business hours, breach alerts, compliance dashboard, OLA/UC fields |
| Knowledge Management | 40% | 70% | Article lifecycle, versioning, review dates, ticket linking, internal articles |
| Continual Improvement | 10% | 35% | CSAT measurement, custom reports, time tracking data, incident trend analysis |

## Appendix C: Traceability Matrix

| Business Objective | Success Criteria | Functional Requirements |
|-------------------|-----------------|----------------------|
| BO-1: Close feature gaps | SC-05, SC-09, SC-10 | FR-CR-01, FR-WA-01, FR-LC-01, FR-IN-01 |
| BO-2: Agent productivity | SC-06 | FR-TT-01, FR-WA-01, FR-IN-01, FR-LC-04 |
| BO-3: CSAT measurement | SC-01, SC-02 | FR-CS-01, FR-CS-02 |
| BO-4: Expand channels | SC-03 | FR-LC-01, FR-LC-02, FR-LC-03, FR-LC-04 |
| BO-7: ITIL compliance | SC-07, SC-08 | FR-IM-01 through FR-IM-06, FR-KB-01 through FR-KB-05, FR-SL-01 through FR-SL-04 |
