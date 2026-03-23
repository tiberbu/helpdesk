---
stepsCompleted: [1, 2, 3, 4]
inputDocuments:
  - _bmad-output/planning-artifacts/prd.md
  - _bmad-output/planning-artifacts/architecture.md
  - _bmad-output/planning-artifacts/ux-design-specification.md
status: complete
completedAt: '2026-03-23'
project_name: 'Frappe Helpdesk Phase 1'
---

# Frappe Helpdesk Phase 1 - Epic Breakdown

## Overview

This document provides the complete epic and story breakdown for Frappe Helpdesk Phase 1 (ITIL Foundation & Platform Transformation), decomposing the requirements from the PRD, UX Design specification, and Architecture decisions into 6 implementable epics with ordered stories.

## Requirements Inventory

### Functional Requirements

FR-IM-01: Impact and urgency fields on HD Ticket with auto-calculated priority from configurable ITIL matrix, Simple/ITIL mode toggle
FR-IM-02: Multi-level categorization with Category and Sub-category fields, admin-configurable hierarchy, required on resolution
FR-IM-03: Incident models/templates with pre-set fields, checklist items, and auto-actions for common incident types
FR-IM-04: Related incidents linking with bidirectional links, link types (Related/Caused by/Duplicate), auto-close duplicates
FR-IM-05: Major incident flag with expedited workflow, management notification, linked ticket updates, post-incident review
FR-IM-06: MTTR and incident reporting with per-priority/team/category metrics, trend charts, category distribution
FR-IN-01: Private agent notes visible only to agents, @mention support, visually distinct, rich text and attachments
FR-CS-01: Post-resolution CSAT email survey with 1-5 star one-click rating, frequency limits, unsubscribe, per-brand templates
FR-CS-02: CSAT dashboard with scores by agent/team/period/category, drill-down, trend charts, negative feedback alerts
FR-LC-01: Embeddable chat widget with custom branding, agent availability, pre-chat form, file attachments, responsive, <50KB
FR-LC-02: Real-time chat with <200ms latency, typing indicators, message status, session persistence, timeout handling
FR-LC-03: Chat-to-ticket conversion with full transcript, follow-up via email, SLA tracking
FR-LC-04: Agent chat interface with concurrent sessions (up to 5), transfer, availability toggle, desktop notifications
FR-WA-01: Visual automation rule builder with 10+ triggers, 10+ actions, AND/OR conditions, priority ordering, dry-run
FR-WA-02: Automation rule execution logging with per-rule stats, failure tracking, 30-day retention
FR-WA-03: SLA-based automation triggers at configurable warning thresholds with agent/manager notifications
FR-CR-01: Custom report builder with data source selection, drag-and-drop fields, filters, group-by, chart types, real-time preview
FR-CR-02: Report scheduling (daily/weekly/monthly) with email delivery and CSV/Excel export
FR-SL-01: Business hours SLA calculation with per-team working hours, multi-timezone, holiday calendars, pause on status
FR-SL-02: Proactive SLA breach alerts at configurable thresholds with in-app and email notifications, color-coded dashboard
FR-SL-03: SLA compliance dashboard with real-time metrics, drill-down by team/agent/priority, trend charts, period comparison
FR-SL-04: OLA/UC field preparation with agreement_type Select field on HD SLA (informational only in Phase 1)
FR-KB-01: Article review workflow (Draft > In Review > Published > Archived) via Frappe Workflow, reviewer notifications
FR-KB-02: Article versioning with content snapshots, change summaries, side-by-side diff, revert capability
FR-KB-03: Review dates with auto-set on publication, email reminders, dashboard widget for overdue articles
FR-KB-04: Ticket-article linking with bidirectional links, "Create Article from Ticket" action, sidebar display
FR-KB-05: Internal-only articles visible to agents only, excluded from customer portal, visually distinguished
FR-MB-01: Multi-brand support with separate portals, email routing, KB, teams per brand, configurable widget
FR-TT-01: Per-ticket time logging with manual entry, timer mode, billable/non-billable, summary on ticket view
FR-TT-02: Time reporting by agent/team/period with billable breakdown, ERPNext Projects integration (optional)

### Non-Functional Requirements

NFR-P-01: Agent workspace page load < 2 seconds on standard hardware
NFR-P-02: Ticket search response < 500ms for full-text search across 100K tickets
NFR-P-03: Live chat message delivery < 200ms end-to-end (95th percentile)
NFR-P-04: SLA recalculation < 5 seconds per 1000 tickets (background)
NFR-P-05: Chat widget bundle size < 50KB gzipped
NFR-P-06: Automation rule evaluation < 100ms per rule per ticket event
NFR-P-07: Dashboard widget load < 1 second per widget
NFR-S-01: Support 500 concurrent agents on single instance
NFR-S-02: Support 200 simultaneous chat sessions
NFR-S-03: Handle 100K tickets/month without degradation
NFR-S-04: Process 1000 rule evaluations/minute
NFR-SE-01: Internal notes NEVER exposed via customer portal, API, or email
NFR-SE-02: Chat sessions authenticated via token; no cross-customer data access
NFR-SE-03: CSAT survey links contain single-use HMAC tokens
NFR-SE-04: Automation rules restricted to System Manager or HD Admin role
NFR-SE-05: Custom reports respect Frappe permission model
NFR-SE-06: All chat messages sanitized server-side before storage
NFR-U-01: Progressive disclosure for ITIL fields (Simple/ITIL mode toggle)
NFR-U-02: Agent onboarding within 30 minutes
NFR-U-03: Chat widget fully functional on mobile browsers
NFR-U-04: WCAG 2.1 AA compliance for all new UI components
NFR-U-05: Full keyboard navigation for all new features
NFR-A-01: Core ticketing unaffected by chat or automation failures
NFR-A-02: Chat widget graceful degradation to "Leave a message" form
NFR-A-03: Auto-disable automation rules after 10 consecutive failures
NFR-M-01: Minimum 80% unit test coverage on all new backend code
NFR-M-02: All new DocTypes accessible via REST API
NFR-M-03: Chat uses abstract channel interface for future extensibility
NFR-M-04: All ITIL features toggleable via HD Settings without code deployment

### Additional Requirements

AR-01: Channel abstraction layer must be implemented before live chat (architecture decision ADR-07)
AR-02: All new DocTypes follow HD prefix naming convention and standard Frappe DocType structure
AR-03: Background jobs use Frappe's Redis Queue with appropriate queue priority (short/default/long)
AR-04: All new fields added to existing DocTypes via DocType JSON modification (not Custom Fields)
AR-05: Migration patches in helpdesk/patches/v1_phase1/ for all schema changes
AR-06: Feature flags (itil_mode_enabled, chat_enabled, csat_enabled, automation_enabled) in HD Settings
AR-07: Socket.IO room naming convention: ticket:{id}, chat:{session_id}, agent:{email}, team:{name}
AR-08: Separate Vite build for chat widget (widget/ directory) producing IIFE bundle with Shadow DOM

### UX Design Requirements

UX-DR-01: ITIL fields (impact, urgency, category) use progressive disclosure - hidden in Simple Mode, revealed in ITIL Mode
UX-DR-02: Internal notes visually distinct with amber-50 background, amber-400 left border, "Internal Note" badge, lock icon
UX-DR-03: Chat widget supports custom branding (primary color, logo, greeting, position) and responsive design (400px desktop, full-screen mobile)
UX-DR-04: Time tracker component with start/stop timer button and manual entry option in ticket sidebar
UX-DR-05: CSAT survey email uses one-click-to-rate design (clicking star in email submits rating)
UX-DR-06: SLA breach color coding on agent dashboard: yellow (>30min), orange (15-30min), red (<15min)
UX-DR-07: Automation rule builder uses visual if-then-else interface with WHEN/IF/THEN sections
UX-DR-08: Report builder with drag-and-drop field selection, real-time preview, and chart type selector (bar/line/pie/table)
UX-DR-09: Major incident banner displayed prominently on ticket view with elapsed time and linked ticket count
UX-DR-10: Article lifecycle badges (Draft/In Review/Published/Archived) with color-coded status indicators
UX-DR-11: All new UI components follow frappe-ui patterns and WCAG 2.1 AA accessibility standards
UX-DR-12: Chat agent interface shows concurrent sessions list with unread badges and quick-switch

### FR Coverage Map

FR-IM-01: Epic 1 - ITIL Incident Management (Impact/Urgency/Priority Matrix)
FR-IM-02: Epic 1 - ITIL Incident Management (Category/Sub-category)
FR-IM-03: Epic 1 - ITIL Incident Management (Incident Models)
FR-IM-04: Epic 1 - ITIL Incident Management (Related Linking)
FR-IM-05: Epic 1 - ITIL Incident Management (Major Incidents)
FR-IM-06: Epic 6 - Reporting (MTTR/Incident Reports)
FR-IN-01: Epic 1 - ITIL Incident Management (Internal Notes)
FR-CS-01: Epic 3 - Omnichannel (CSAT Surveys)
FR-CS-02: Epic 6 - Reporting (CSAT Dashboard)
FR-LC-01: Epic 3 - Omnichannel (Chat Widget)
FR-LC-02: Epic 3 - Omnichannel (Real-time Chat)
FR-LC-03: Epic 3 - Omnichannel (Chat-to-Ticket)
FR-LC-04: Epic 3 - Omnichannel (Agent Chat Interface)
FR-WA-01: Epic 2 - AI Agent (Automation Rule Builder)
FR-WA-02: Epic 2 - AI Agent (Execution Logging)
FR-WA-03: Epic 2 - AI Agent (SLA Triggers)
FR-CR-01: Epic 6 - Reporting (Report Builder)
FR-CR-02: Epic 6 - Reporting (Report Scheduling)
FR-SL-01: Epic 4 - SLA (Business Hours Calculation)
FR-SL-02: Epic 4 - SLA (Proactive Breach Alerts)
FR-SL-03: Epic 4 - SLA (Compliance Dashboard)
FR-SL-04: Epic 4 - SLA (OLA/UC Preparation)
FR-KB-01: Epic 5 - Knowledge Base (Article Workflow)
FR-KB-02: Epic 5 - Knowledge Base (Versioning)
FR-KB-03: Epic 5 - Knowledge Base (Review Dates)
FR-KB-04: Epic 5 - Knowledge Base (Ticket-Article Linking)
FR-KB-05: Epic 5 - Knowledge Base (Internal Articles)
FR-MB-01: Epic 3 - Omnichannel (Multi-Brand)
FR-TT-01: Epic 1 - ITIL Incident Management (Time Tracking)
FR-TT-02: Epic 6 - Reporting (Time Reports)

## Epic List

### Epic 1: ITIL Incident Management
Establish a complete ITIL-aligned incident management foundation -- impact/urgency classification, multi-level categorization, internal collaboration through private notes, related ticket linking, per-ticket time tracking, major incident workflows, and incident model templates -- while preserving simplicity for teams not yet ready for ITIL complexity.
**FRs covered:** FR-IM-01, FR-IM-02, FR-IM-03, FR-IM-04, FR-IM-05, FR-IN-01, FR-TT-01
**Dependencies:** None (foundational epic)
**Complexity:** High

### Epic 2: AI Agent (Workflow Automation)
Enable intelligent, automated ticket handling through a visual rule builder with 10+ triggers and 10+ actions, condition-based routing, SLA-aware automation triggers, execution logging, and safety mechanisms -- creating the automation backbone for future AI-powered capabilities.
**FRs covered:** FR-WA-01, FR-WA-02, FR-WA-03
**Dependencies:** Epic 1 (ticket fields for conditions), Epic 4 (SLA events for triggers)
**Complexity:** High

### Epic 3: Omnichannel
Expand support beyond email with live chat as a second real-time channel (embeddable widget, agent chat interface, chat-to-ticket conversion), post-resolution CSAT surveys for customer feedback measurement, and multi-brand portal support -- creating a unified multi-channel customer experience.
**FRs covered:** FR-LC-01, FR-LC-02, FR-LC-03, FR-LC-04, FR-CS-01, FR-MB-01
**Dependencies:** Epic 1 (ticket infrastructure for chat-to-ticket)
**Complexity:** High

### Epic 4: SLA
Transform SLA management with business-hours-only calculation, holiday calendars, multi-timezone support, proactive breach alerting with color-coded warnings, a real-time SLA compliance dashboard, and OLA/UC field preparation for Phase 2.
**FRs covered:** FR-SL-01, FR-SL-02, FR-SL-03, FR-SL-04
**Dependencies:** Epic 1 (priority/category fields for drill-down)
**Complexity:** Medium

### Epic 5: Knowledge Base
Elevate the knowledge base with article lifecycle management (Draft > Review > Published > Archived), content versioning with diff and revert, scheduled review reminders, bidirectional ticket-article linking, and internal-only articles -- enabling knowledge-centered service practices.
**FRs covered:** FR-KB-01, FR-KB-02, FR-KB-03, FR-KB-04, FR-KB-05
**Dependencies:** Epic 1 (ticket-article linking requires ticket sidebar)
**Complexity:** Medium

### Epic 6: Reporting
Deliver actionable insights through a custom drag-and-drop report builder, scheduled report delivery, CSAT analytics dashboard, MTTR and incident trend reporting, and time tracking reports with optional ERPNext integration.
**FRs covered:** FR-IM-06, FR-CS-02, FR-CR-01, FR-CR-02, FR-TT-02
**Dependencies:** Epic 1 (incident data for MTTR), Epic 3 (CSAT data), Epic 4 (SLA data)
**Complexity:** Medium

---

## Epic 1: ITIL Incident Management

Establish a complete ITIL-aligned incident management foundation -- impact/urgency classification, multi-level categorization, internal collaboration through private notes, related ticket linking, per-ticket time tracking, major incident workflows, and incident model templates -- while preserving simplicity for teams not yet ready for ITIL complexity.

### Story 1.1: Feature Flag Infrastructure for ITIL Mode

As an administrator,
I want to toggle between Simple Mode and ITIL Mode in HD Settings,
So that my team can adopt ITIL fields gradually without being overwhelmed.

**Acceptance Criteria:**

**Given** an administrator opens HD Settings
**When** they toggle the `itil_mode_enabled` checkbox
**Then** the setting is saved and available to all ticket forms
**And** the setting defaults to OFF (Simple Mode) for backward compatibility

**Given** ITIL Mode is disabled (Simple Mode)
**When** an agent opens a ticket form
**Then** the priority field is shown as a simple dropdown (existing behavior)
**And** impact, urgency, category, and sub-category fields are hidden

**Given** ITIL Mode is enabled
**When** an agent opens a ticket form
**Then** impact, urgency, category, and sub-category fields are visible
**And** priority is shown as read-only (auto-calculated)

### Story 1.2: Impact and Urgency Fields with Priority Matrix

As a support agent in ITIL Mode,
I want to set impact and urgency on a ticket so that priority is calculated automatically from the ITIL priority matrix,
So that ticket prioritization is consistent and objective.

**Acceptance Criteria:**

**Given** ITIL Mode is enabled
**When** an agent sets Impact to "High" and Urgency to "High" on a ticket
**Then** the Priority field auto-calculates to "Urgent" (P1 Critical) per the default matrix
**And** the priority field is read-only and shows the calculated value

**Given** an administrator opens HD Settings
**When** they edit the priority matrix JSON configuration
**Then** the matrix is validated (all 9 combinations must be mapped)
**And** future priority calculations use the updated matrix

**Given** a legacy ticket created before ITIL Mode was enabled
**When** an agent opens the ticket
**Then** the manually-set priority is retained (impact/urgency show as empty)
**And** the agent can optionally set impact/urgency to switch to calculated priority

### Story 1.3: Multi-Level Ticket Categorization

As a support agent,
I want to categorize tickets with Category and Sub-category,
So that reporting and routing can use granular classification.

**Acceptance Criteria:**

**Given** an administrator creates HD Ticket Category records
**When** they create a category with a parent_category reference
**Then** a hierarchical Category > Sub-category structure is established

**Given** an agent opens a ticket form
**When** they select a Category
**Then** the Sub-category dropdown filters to show only children of the selected Category

**Given** a category hierarchy exists (e.g., Billing > Invoice Dispute, Billing > Refund Request)
**When** an agent selects Category "Billing"
**Then** Sub-category shows "Invoice Dispute" and "Refund Request" only

**Given** an administrator configures "Category required on resolution" in HD Settings
**When** an agent attempts to resolve a ticket without a category
**Then** a validation error prevents resolution until category is set

### Story 1.4: Internal Notes on Tickets

As a support agent,
I want to add private notes on a ticket that are visible only to other agents,
So that I can collaborate internally without exposing information to customers.

**Acceptance Criteria:**

**Given** an agent is viewing a ticket
**When** they click "Add Internal Note" (or press keyboard shortcut)
**Then** a note editor opens that is visually distinct (amber-50 background, amber-400 left border, "Internal Note" badge, lock icon)
**And** the note supports rich text (bold, italic, links, code blocks) and file attachments

**Given** an internal note exists on a ticket
**When** a customer views the ticket in the customer portal
**Then** the internal note is NOT visible
**And** the internal note is NOT included in any customer-facing email

**Given** an internal note exists on a ticket
**When** the ticket data is fetched via API without Agent role
**Then** internal notes are excluded from the response (server-side permission check)

### Story 1.5: @Mention Notifications in Internal Notes

As a support agent,
I want to @mention other agents in internal notes,
So that they are notified and can quickly find the relevant ticket.

**Acceptance Criteria:**

**Given** an agent is typing an internal note
**When** they type "@" followed by characters
**Then** an autocomplete dropdown shows matching agent names

**Given** an agent submits a note mentioning "@Rajesh"
**When** the note is saved
**Then** Rajesh receives an in-app notification with link to the ticket
**And** the notification shows the note content preview

### Story 1.6: Related Ticket Linking

As a support agent,
I want to link related tickets together,
So that patterns are visible and updates can propagate between related issues.

**Acceptance Criteria:**

**Given** an agent is viewing Ticket A
**When** they click "Link Ticket" and select Ticket B with type "Related to"
**Then** Ticket B appears in Ticket A's "Related Tickets" sidebar panel
**And** Ticket A appears in Ticket B's "Related Tickets" sidebar panel (bidirectional)

**Given** an agent links Ticket A to Ticket B with type "Duplicate of"
**When** the link is saved
**Then** Ticket A is automatically closed with status "Duplicate"
**And** a comment is added: "Closed as duplicate of [Ticket B link]"

**Given** link types "Related to", "Caused by", and "Duplicate of" are available
**When** an agent creates a link
**Then** they must select one of the three link types

### Story 1.7: Per-Ticket Time Tracking

As a support agent,
I want to log time spent on a ticket with both manual entry and timer mode,
So that effort is tracked for reporting and billing.

**Acceptance Criteria:**

**Given** an agent is viewing a ticket
**When** they click the timer "Start" button in the sidebar
**Then** a timer starts counting and is visible in the UI (monospace font, persists in localStorage across navigation)
**When** they click "Stop"
**Then** an HD Time Entry is created with the calculated duration and a description prompt appears

**Given** an agent wants to log time manually
**When** they enter duration (hours/minutes), description, and billable checkbox in the Time Entry Modal
**Then** an HD Time Entry is created linked to the ticket and agent

**Given** a ticket has multiple time entries
**When** viewing the ticket sidebar
**Then** a time summary shows: total time, billable time, and entry list with agent/date/description

### Story 1.8: Major Incident Flag and Workflow

As a support agent,
I want to flag a ticket as a Major Incident to trigger an expedited response process,
So that critical issues affecting multiple customers receive immediate management attention.

**Acceptance Criteria:**

**Given** an agent is viewing a ticket with related tickets linked (Story 1.6)
**When** they check the `is_major_incident` checkbox
**Then** a confirmation dialog appears: "This will notify escalation contacts. Continue?"
**And** on confirmation, the system sends immediate notifications to configured escalation contacts (email + in-app)
**And** a prominent red banner appears on the ticket view showing elapsed time

**Given** a ticket is flagged as major incident
**When** the agent posts a status update
**Then** they can optionally propagate the update to all linked tickets

**Given** a major incident is resolved
**When** the agent closes the ticket
**Then** post-incident review fields appear: root_cause_summary, corrective_actions, prevention_measures

**Given** major incidents exist
**When** a manager views the Major Incident dashboard (`/helpdesk/major-incidents`)
**Then** they see: all active major incidents as cards with elapsed time, linked ticket count, affected customer count

### Story 1.9: Incident Models / Templates

As an administrator,
I want to create incident models with predefined fields,
So that common incident types are logged consistently.

**Acceptance Criteria:**

**Given** the HD Incident Model DocType exists
**When** an administrator creates a model
**Then** they can configure: name, description, default_category, default_sub_category, default_priority, default_team, checklist_items

**Given** an agent selects an incident model during ticket creation
**When** the model is applied
**Then** all predefined fields auto-populate on the ticket form

**Given** an incident model includes checklist items
**When** the agent views the ticket
**Then** checklist items are displayed and must be completed before resolution

**Given** the system ships with defaults
**When** a fresh installation occurs
**Then** at least 5 default models are available (e.g., Password Reset, System Outage, Access Request, Hardware Failure, Software Bug)

---

## Epic 2: AI Agent (Workflow Automation)

Enable intelligent, automated ticket handling through a visual rule builder with 10+ triggers and 10+ actions, condition-based routing, SLA-aware automation triggers, execution logging, and safety mechanisms -- creating the automation backbone for future AI-powered capabilities.

### Story 2.1: Automation Rule DocType and Engine Core

As an administrator,
I want to create automation rules with triggers, conditions, and actions,
So that routine ticket operations happen automatically.

**Acceptance Criteria:**

**Given** the HD Automation Rule DocType exists
**When** an administrator creates a rule
**Then** they can configure: name, description, enabled, trigger type, conditions (JSON), actions (JSON), priority order

**Given** a rule with trigger "ticket_created" and conditions [priority equals "Urgent"]
**When** a new Urgent ticket is created
**Then** the rule's conditions are evaluated within 100ms (NFR-P-06)
**And** if conditions match, actions are executed

**Given** the automation engine processes rules
**When** multiple rules match a ticket event
**Then** rules execute in priority order (lower number = higher priority)

**Given** a rule triggers another rule (cascading)
**When** more than 5 executions occur for the same ticket within 1 minute
**Then** the loop detection stops execution and logs a warning

### Story 2.2: Automation Rule Builder UI

As an administrator,
I want to build automation rules using a visual interface,
So that I can configure complex rules without writing code.

**Acceptance Criteria:**

**Given** an administrator opens the Automation Builder page (`/helpdesk/automation-rules/new`)
**When** they configure the WHEN (Trigger) section
**Then** available triggers include: ticket_created, ticket_updated, ticket_assigned, ticket_resolved, ticket_reopened, sla_warning, sla_breached, csat_received, chat_started, chat_ended (minimum 10)

**Given** the administrator configures the IF (Conditions) section
**When** they add conditions with field, operator, and value
**Then** conditions support AND/OR grouping with operators: equals, not_equals, contains, greater_than, less_than, is_set, is_not_set

**Given** the administrator configures the THEN (Actions) section
**When** they select action types
**Then** available actions include: assign_to_agent, assign_to_team, set_priority, set_status, set_category, add_tag, send_email, send_notification, add_internal_note, trigger_webhook (minimum 10)

**Given** a rule is configured
**When** the administrator clicks "Test Rule" (dry-run)
**Then** a modal shows the rule evaluated against a sample ticket: which conditions match and which actions would execute, without actually executing

### Story 2.3: SLA-Based Automation Triggers

As an administrator,
I want to trigger automations based on SLA events (warnings, breaches),
So that at-risk tickets get proactive attention automatically.

**Acceptance Criteria:**

**Given** an SLA has warning thresholds configured (default: 30, 15, 5 minutes before breach)
**When** a ticket approaches a warning threshold
**Then** the `sla_warning` trigger fires and matching automation rules are evaluated

**Given** an SLA breach occurs
**When** the resolution_by time is exceeded
**Then** the `sla_breached` trigger fires and matching automation rules are evaluated

**Given** an automation rule has trigger "sla_warning" and action "assign_to_team: Escalation"
**When** a ticket's SLA warning fires
**Then** the ticket is automatically reassigned to the Escalation team

**Given** SLA triggers are connected to the notification system
**When** an sla_warning fires
**Then** the assigned agent receives an in-app notification (toast + badge)

### Story 2.4: Automation Execution Logging

As an administrator,
I want to see a log of every automation rule execution,
So that I can debug and optimize my rules.

**Acceptance Criteria:**

**Given** an automation rule executes
**When** it completes (success or failure)
**Then** an HD Automation Log record is created with: rule_name, ticket, trigger_event, conditions_evaluated, actions_executed, execution_time_ms, status, timestamp

**Given** an administrator views the automation list page
**When** they check rule execution statistics
**Then** they see per-rule: execution count, last fired time, failure rate

**Given** a rule fails 10 consecutive times
**When** the safety module detects this
**Then** the rule is automatically disabled
**And** the rule creator receives a notification

**Given** automation logs are older than 30 days (configurable)
**When** the daily cleanup job runs
**Then** old logs are purged

---

## Epic 3: Omnichannel

Expand support beyond email with live chat as a second real-time channel (embeddable widget, agent chat interface, chat-to-ticket conversion), post-resolution CSAT surveys for customer feedback measurement, and multi-brand portal support -- creating a unified multi-channel customer experience.

### Story 3.1: Channel Abstraction Layer

As a developer,
I want a channel abstraction layer that normalizes messages from all channels into a unified format,
So that adding new channels (WhatsApp, SMS) in Phase 2 requires minimal core changes.

**Acceptance Criteria:**

**Given** the channel abstraction module exists at `helpdesk/helpdesk/channels/`
**When** a message arrives from any channel (email, chat)
**Then** it is normalized into a ChannelMessage format with: source, sender_email, sender_name, subject, content, attachments, metadata, ticket_id, is_internal, timestamp

**Given** the existing email processing logic
**When** it is refactored into an email_adapter
**Then** all existing email functionality continues to work identically (regression-safe)

**Given** a new channel adapter is registered via the registry
**When** messages arrive from that channel
**Then** they are processed through the normalizer into HD Ticket communications

### Story 3.2: Chat Session Management Backend

As a developer,
I want chat session lifecycle management,
So that chat conversations are properly tracked and cleaned up.

**Acceptance Criteria:**

**Given** the HD Chat Session and HD Chat Message DocTypes exist
**When** a customer submits the pre-chat form
**Then** a session is created with: customer email, status (waiting/active/ended), started_at, agent (null until assigned)
**And** a JWT session token is generated and returned for Socket.IO authentication

**Given** a chat session is created
**When** the first customer message is sent
**Then** an HD Ticket is created with source="Chat" via the channel normalizer

**Given** a chat session has been inactive for configurable timeout (default 30 minutes)
**When** the session cleanup background job runs
**Then** the session status is set to "ended"
**And** the customer receives a system message: "This chat has ended"

### Story 3.3: Embeddable Chat Widget

As a website visitor,
I want to open a chat widget on the company's website to get real-time support,
So that I can get help without leaving the page.

**Acceptance Criteria:**

**Given** a single `<script>` tag with data attributes (site URL, brand, position)
**When** loaded on any website
**Then** a chat widget button appears at the configured position (bottom-right/bottom-left)
**And** the widget loads asynchronously without blocking page rendering
**And** total bundle size is < 50KB gzipped (NFR-P-05)

**Given** agents are available
**When** the customer opens the widget
**Then** it shows "Support is online" with a pre-chat form (name, email, subject)

**Given** no agents are available
**When** the customer opens the widget
**Then** it shows "Leave a message" form that creates an email ticket

**Given** the widget uses Shadow DOM isolation
**When** the host page has conflicting CSS
**Then** the widget rendering is not affected

**Given** the widget is opened on a mobile device
**When** the chat panel expands
**Then** it fills the full screen instead of the 400px desktop panel

### Story 3.4: Real-Time Chat Communication

As a customer chatting live,
I want real-time message delivery with typing indicators,
So that the experience feels like a modern messaging app.

**Acceptance Criteria:**

**Given** a customer and agent are in an active chat session
**When** either party sends a message
**Then** it is delivered within 200ms end-to-end (NFR-P-03)
**And** message status shows: sent (single check), delivered (double check), read (blue double check)

**Given** either party starts typing
**When** keystrokes are detected
**Then** the other party sees a typing indicator (three animated dots)
**And** the indicator auto-clears after 10 seconds of inactivity

**Given** a customer navigates to a different page on the same website
**When** they return to the page with the widget
**Then** the chat session is preserved (via localStorage)

**Given** no agent responds within configurable timeout (default 2 minutes)
**When** the timeout is reached
**Then** auto-message shown: "We're experiencing high volume. You can wait or leave a message and we'll email you."

### Story 3.5: Agent Chat Interface

As a support agent,
I want to handle multiple simultaneous chat conversations from my workspace,
So that I can efficiently serve chat customers alongside ticket work.

**Acceptance Criteria:**

**Given** an agent is online and available
**When** a new chat request arrives
**Then** they see it in their chat queue with desktop notification and unread badge
**And** they can accept the chat

**Given** an agent has multiple active chats (up to 5 configurable)
**When** a new message arrives in any chat
**Then** an unread count badge is shown on that chat
**And** the agent can switch between chats with quick-switch

**Given** an agent is handling a chat
**When** they need to transfer to another agent or team
**Then** the chat can be transferred with full context preserved

**Given** an agent sets their availability to "Away" or "Offline"
**When** new chat requests arrive
**Then** they are not routed to this agent

### Story 3.6: Chat-to-Ticket Transcript and Follow-up

As a support agent,
I want every chat to have a complete HD Ticket with full transcript,
So that all interactions are tracked and reportable.

**Acceptance Criteria:**

**Given** a chat session is active
**When** messages are exchanged
**Then** each message is stored as a ticket communication via the channel adapter

**Given** a chat session ends without resolution
**When** the customer leaves or the session times out
**Then** the ticket remains open for follow-up via email

**Given** a chat session has ended
**When** the agent replies to the associated ticket
**Then** the response is sent via email to the customer (standard ticket flow)

### Story 3.7: CSAT Survey Infrastructure and Delivery

As an administrator,
I want automated post-resolution CSAT surveys,
So that customer satisfaction is measurable.

**Acceptance Criteria:**

**Given** an administrator enables CSAT in HD Settings and configures: delay (default 24h), frequency limit (default 7 days)
**When** a ticket is resolved and the delay passes
**Then** a CSAT survey email is sent with 1-5 star one-click rating links

**Given** a CSAT email is received
**When** the customer clicks a star (e.g., 4 stars)
**Then** the rating is submitted via single click (one-click-to-rate design)
**And** a thank-you page confirms the submission and offers optional comment field

**Given** a customer has already received a CSAT survey in the last 7 days (configurable)
**When** another ticket is resolved
**Then** no survey is sent for this ticket (frequency limit)

**Given** a customer clicks "Unsubscribe" in the survey email
**When** the unsubscribe is processed
**Then** the customer is marked as unsubscribed and receives no future surveys

**Given** the survey link contains an HMAC-signed single-use token
**When** the token is used once
**Then** it cannot be reused (single-use enforcement)

### Story 3.8: Multi-Brand Configuration

As an administrator managing multiple brands,
I want to configure separate brand identities from a single Helpdesk instance,
So that each brand has its own portal appearance, email, and support team.

**Acceptance Criteria:**

**Given** the HD Brand DocType exists
**When** an administrator creates a brand
**Then** they can configure: name, logo, primary_color, support_email, portal_domain, default_team, default_sla

**Given** a ticket arrives via email
**When** the receiving email matches a brand's support_email
**Then** the ticket is auto-tagged with that brand

**Given** a customer visits a brand's portal domain
**When** the portal loads
**Then** it shows brand-specific logo, colors, and KB articles

**Given** an agent views the ticket list
**When** they filter by brand
**Then** only tickets for the selected brand are shown

**Given** a brand has CSAT survey template and chat widget configured
**When** surveys are sent or chat widget is embedded for that brand
**Then** brand-specific templates, logos, colors, and greetings are used

---

## Epic 4: SLA

Transform SLA management with business-hours-only calculation, holiday calendars, multi-timezone support, proactive breach alerting with color-coded warnings, a real-time SLA compliance dashboard, and OLA/UC field preparation for Phase 2.

### Story 4.1: Business Hours SLA Calculation Engine

As an administrator,
I want SLA timers to count only during business hours and exclude holidays,
So that SLA targets reflect actual working time.

**Acceptance Criteria:**

**Given** a team has business hours configured as Mon-Fri 9:00-18:00 in timezone US/Eastern
**When** a ticket is created at Friday 17:00
**Then** SLA timer counts 1 hour of business time for Friday
**And** pauses over the weekend
**And** resumes at Monday 09:00

**Given** a holiday calendar (HD Service Holiday List) is linked to the SLA
**When** a holiday falls on a weekday
**Then** SLA timer pauses for the entire holiday

**Given** existing SLA pause-on-status functionality (e.g., "Waiting on Customer")
**When** ticket status changes to a pause status
**Then** both business hours and pause-on-status logic work together correctly

**Given** the SLA recalculation background job runs
**When** processing 1000 tickets
**Then** it completes within 5 seconds (NFR-P-04)
**And** service day/holiday data is cached in Redis to avoid repeated DB queries

### Story 4.2: Proactive SLA Breach Alerts

As a support agent,
I want to receive warnings before an SLA is about to breach,
So that I can take action to prevent the breach.

**Acceptance Criteria:**

**Given** an SLA has warning thresholds configured (default: 30, 15, 5 minutes before breach)
**When** a ticket approaches the 30-minute threshold
**Then** the assigned agent receives an in-app notification (toast + badge)
**And** the ticket is highlighted yellow on the agent dashboard

**Given** a ticket reaches the 15-minute SLA warning threshold
**When** the SLA monitor cron job runs (every 5 minutes)
**Then** the agent receives an orange-coded warning
**And** the team manager receives a notification (if configured)

**Given** an SLA breach occurs
**When** the resolution_by time is exceeded
**Then** the ticket is highlighted red on the dashboard
**And** the SLA countdown badge on the ticket list shows red

**Given** SLA breach events need to trigger automations
**When** the sla_warning or sla_breached event fires
**Then** the automation engine (Epic 2) evaluates matching rules

### Story 4.3: SLA Compliance Dashboard

As a team manager,
I want real-time SLA compliance metrics with drill-down capability,
So that I can monitor service quality and identify improvement areas.

**Acceptance Criteria:**

**Given** SLA data exists with business hours calculations
**When** a manager opens the SLA compliance dashboard (`/helpdesk/dashboard/sla`)
**Then** they see: overall compliance % (response and resolution), with large number cards for each metric

**Given** the SLA dashboard is displayed
**When** the manager selects filters (date range, team, priority)
**Then** they can drill-down by team, agent, priority, and category

**Given** the SLA dashboard shows trend data
**When** the manager toggles between daily/weekly/monthly
**Then** a compliance trend line chart is displayed with comparison to prior period

**Given** breach analysis data exists
**When** viewing the dashboard
**Then** top reasons for breach are shown (by category, by time-of-day)

**Given** the SLA dashboard is available as a widget
**When** an agent configures their home page
**Then** the SLA compliance widget can be added showing gauge/percentage display

### Story 4.4: OLA/UC Agreement Type Preparation

As an administrator,
I want to tag SLA agreements as SLA, OLA, or UC type,
So that the system is prepared for full OLA/UC tracking in Phase 2.

**Acceptance Criteria:**

**Given** an administrator opens an HD Service Level Agreement
**When** they see the new `agreement_type` Select field
**Then** it shows options: "SLA" (default), "OLA", "UC"

**Given** the agreement type is set to "OLA"
**When** the administrator views the SLA list
**Then** the agreement type badge is displayed on the list view

**Given** new fields `internal_team` (Link) and `vendor` (Data) are added
**When** agreement_type is "OLA"
**Then** `internal_team` field is visible
**When** agreement_type is "UC"
**Then** `vendor` field is visible

---

## Epic 5: Knowledge Base

Elevate the knowledge base with article lifecycle management (Draft > Review > Published > Archived), content versioning with diff and revert, scheduled review reminders, bidirectional ticket-article linking, and internal-only articles -- enabling knowledge-centered service practices.

### Story 5.1: Article Review Workflow

As a KB author,
I want articles to go through a review workflow before publication,
So that only vetted content reaches customers.

**Acceptance Criteria:**

**Given** the article lifecycle states are: Draft > In Review > Published > Archived
**When** a Frappe Workflow is configured for HD Article
**Then** state transitions are governed by the workflow engine

**Given** an author has a Draft article
**When** they click "Submit for Review"
**Then** the article moves to "In Review" and configured reviewer(s) receive email notification

**Given** a reviewer has an article in "In Review"
**When** they approve the article
**Then** it moves to "Published" and the author receives notification
**When** they request changes
**Then** it returns to "Draft" with reviewer comments
**When** they reject
**Then** it moves to "Archived"

**Given** an article is in any state
**When** checking customer-facing visibility
**Then** only "Published" articles appear in the customer portal and public KB
**And** "In Review" articles are visible to agents for internal reference

### Story 5.2: Article Versioning

As a KB author,
I want to see the history of changes to an article and revert if needed,
So that content quality is maintained over time.

**Acceptance Criteria:**

**Given** an HD Article is saved
**When** content changes are detected
**Then** an HD Article Version record is created with: content snapshot, author, timestamp, change_summary

**Given** an article has multiple versions
**When** the author clicks "Version History" (or "View Versions" from list)
**Then** they see a list of all versions with dates and authors in a drawer

**Given** two versions are selected for comparison
**When** the author clicks "Compare"
**Then** a side-by-side diff is displayed highlighting changes

**Given** the author wants to revert
**When** they select a previous version and click "Revert"
**Then** the article content is restored from that version (creating a new version record)

### Story 5.3: Review Dates and Expiry Reminders

As a KB manager,
I want review dates on articles with automated reminders,
So that content is periodically verified for accuracy.

**Acceptance Criteria:**

**Given** an article is published
**When** it transitions to "Published" state
**Then** `review_date` is auto-set to 90 days from publication (configurable)

**Given** an article's review_date has passed
**When** the daily review reminder job runs
**Then** the article author receives an email reminder to review the article

**Given** overdue articles exist
**When** a manager views the "Articles Due for Review" dashboard widget
**Then** they see overdue and upcoming-within-7-days articles listed
**And** quick actions available: "Mark Reviewed", "Edit", "Archive"

### Story 5.4: Ticket-Article Linking

As a support agent,
I want to link KB articles to tickets and create articles from tickets,
So that resolution knowledge is connected to the incidents it addresses.

**Acceptance Criteria:**

**Given** an agent is viewing a ticket
**When** they click "Link Article" in the sidebar
**Then** a search dialog appears to find and select from published articles

**Given** an article is linked to a ticket
**When** the agent views the ticket sidebar
**Then** linked articles are shown with title and click-through link

**Given** an agent is viewing a resolved ticket
**When** they click "Create Article from Ticket"
**Then** a new article is pre-filled with the ticket subject and resolution details

**Given** an article has been linked to multiple tickets
**When** viewing the article detail
**Then** a list of linked tickets is shown (count and recent 10)

### Story 5.5: Internal-Only Articles

As a KB author,
I want to mark articles as internal-only,
So that sensitive procedures are available to agents but hidden from customers.

**Acceptance Criteria:**

**Given** an `internal_only` checkbox is added to HD Article
**When** an author checks "Internal Only" on an article
**Then** the article is excluded from the customer portal and public knowledge base

**Given** an internal article exists
**When** an agent searches the KB from the agent workspace
**Then** the internal article appears in results with a visual badge ("Internal" badge with lock icon)

---

## Epic 6: Reporting

Deliver actionable insights through a custom drag-and-drop report builder, scheduled report delivery, CSAT analytics dashboard, MTTR and incident trend reporting, and time tracking reports with optional ERPNext integration.

### Story 6.1: Custom Report Builder

As a team manager,
I want to build custom reports by selecting data source, fields, filters, and grouping,
So that I get exactly the data I need without developer help.

**Acceptance Criteria:**

**Given** the HD Custom Report DocType exists
**When** a manager creates a new report at `/helpdesk/reports/new`
**Then** they can select data source (HD Ticket, HD CSAT Response, HD Article, HD Time Entry)
**And** drag-and-drop fields from available columns
**And** configure filters with operators (equals, not_equals, contains, greater_than, etc.)
**And** set group-by with up to 3 levels
**And** choose chart type (bar, line, pie, table)

**Given** a report configuration is being built
**When** any setting changes
**Then** the report preview updates in real-time in the right panel

**Given** a report is complete
**When** the manager clicks "Save"
**Then** the report is saved for reuse with name and description

### Story 6.2: Report Scheduling and Export

As a team manager,
I want to schedule reports for email delivery and export to CSV/Excel,
So that I can share insights with stakeholders automatically.

**Acceptance Criteria:**

**Given** a saved report exists
**When** the manager configures a schedule (daily, weekly with day, monthly with date)
**Then** the report runs automatically at the scheduled time via background job
**And** results are emailed to configured recipients as an attachment

**Given** a report is displaying results
**When** the manager clicks "Export"
**Then** they can download as CSV or Excel (.xlsx)
**And** exported data includes all applied filters and grouping

### Story 6.3: CSAT Analytics Dashboard

As a team manager,
I want to view CSAT scores by agent, team, time period, and category,
So that I can identify satisfaction trends and coaching opportunities.

**Acceptance Criteria:**

**Given** CSAT response data exists (from Epic 3 Story 3.7)
**When** a manager opens the CSAT dashboard (`/helpdesk/dashboard/csat`)
**Then** they see: overall CSAT score (30-day rolling), response rate %, rating distribution bar chart, score by agent table, score trend line chart

**Given** the CSAT dashboard is displayed
**When** the manager clicks on a specific score
**Then** they can drill down to individual survey responses with ticket links

**Given** a CSAT rating of 1-2 stars is submitted
**When** the response is processed
**Then** the team manager receives a negative feedback alert notification

**Given** the CSAT dashboard is available as a widget
**When** an agent configures their home page
**Then** the CSAT score widget shows star average with trend arrow

### Story 6.4: MTTR and Incident Reporting

As a team manager,
I want to view Mean Time to Resolve, incident volume trends, and category distribution,
So that I can identify improvement areas.

**Acceptance Criteria:**

**Given** resolved tickets with time data exist (from Epic 1 categorization and time tracking)
**When** viewing the MTTR report
**Then** MTTR is shown per priority level, per team, per category (30/60/90-day rolling)
**And** MTTR excludes time in "Waiting on Customer" status

**Given** incident volume data exists
**When** viewing the trend chart
**Then** daily/weekly/monthly volume is shown with comparison to prior period

**Given** categorized tickets exist
**When** viewing the category distribution
**Then** a pie chart shows top 10 categories by volume

### Story 6.5: Time Tracking Reports

As a team manager,
I want time reports by agent, team, and period with billable breakdown,
So that I can track effort and manage billing.

**Acceptance Criteria:**

**Given** HD Time Entry records exist (from Epic 1 Story 1.7)
**When** viewing the time report
**Then** hours by agent per period are shown with billable vs non-billable breakdown
**And** average time per ticket by category and priority is shown

**Given** ERPNext is installed and integration is enabled
**When** billable time entries are synced
**Then** they appear as Timesheet records in ERPNext Projects

**Given** ERPNext is not installed
**When** the time tracking feature is used
**Then** all features work normally without ERPNext (integration is optional)
