# Product Requirements Document: Frappe Helpdesk Phase 3
## Enterprise & Automation — AI Agent, Change Enablement, CMDB, Service Catalog

**Version:** 1.0
**Date:** 2026-03-27
**Author:** BMAD Dev Agent (Amelia)
**Status:** Draft
**Phase:** 3 — Excellence (Months 15–24)
**Depends On:**
- `docs/phase-2-4-competitive-analysis.md` — gap analysis driving Phase 3 scope
- `docs/phase-2-4-architecture.md` — technical architecture decisions
- `_bmad-output/planning-artifacts/prd.md` — Phase 1 PRD (foundation)

---

## Executive Summary

### Vision

Phase 3 ("Excellence") transforms Frappe Helpdesk into a full ITSM platform competing directly with ServiceNow and Jira Service Management for enterprise IT departments — while the autonomous AI Agent makes it the most cost-effective deflection platform on the market at $0/resolution for self-hosted deployments.

### Phase 3 Objective

Deliver 8 capability clusters over Months 15–24 (2 developers, 10 sprints):

1. **Autonomous AI Agent** — 40%+ ticket deflection via self-service resolution
2. **Change Enablement** — RFC lifecycle, CAB approval, change calendar, risk matrix
3. **CMDB / IT Asset Management** — Configuration items, relationships, impact analysis
4. **Service Catalog** — Structured request catalog with approval workflows and SLA per item
5. **Workforce Management** — Agent scheduling, capacity planning, forecasting
6. **Quality Assurance Scoring** — Ticket audits, agent scorecards, coaching workflows
7. **Sandbox Environments** — Safe test environments for configuration changes
8. **Comprehensive Audit Logging** — Full activity trail for compliance and forensics

### Target Outcome

By end of Phase 3, Frappe Helpdesk achieves:
- ~95% feature parity vs. Freshdesk
- ~80% feature parity vs. Zendesk
- ~60% feature parity vs. ServiceNow (target: ITSM enterprise deals)
- 40%+ ticket deflection rate with AI Agent enabled
- ITIL v4 alignment for all 4 ITIL management practices (Incident, Problem, Change, Service Request)

### Key Differentiators Delivered

- **$0/AI resolution** vs. $1.00/resolution (Zendesk) — at 10,000 AI resolutions/month = $10,000/month saved
- **ERPNext-aware AI Actions** — AI Agent can query orders, invoices, assets natively (no competitor can match)
- **Full ITIL v4 coverage** — Incident + Problem + Change + Service Catalog in a single open-source platform
- **True data sovereignty** — AI inference stays on-premise; no data sent to third-party LLM if Ollama configured

---

## Success Criteria

| ID | Criterion | Metric | Baseline | Target | Measurement Method |
|----|-----------|--------|----------|--------|-------------------|
| SC-P3-01 | AI Agent deflection | % tickets resolved without agent | 0% | ≥40% | AI-resolved tickets / total new tickets (30-day rolling) |
| SC-P3-02 | AI Agent accuracy | % AI-resolved tickets not re-opened | N/A | ≥85% | Re-opened tickets / AI-resolved tickets |
| SC-P3-03 | Change success rate | % changes implemented without incident | Unmeasured | ≥95% | Changes with no linked incident / total changes (30-day) |
| SC-P3-04 | Service Catalog adoption | % service requests via catalog | 0% | ≥60% | Catalog-sourced tickets / total service requests |
| SC-P3-05 | CMDB coverage | % CIs with relationship mapping | 0% | ≥70% of registered CIs | CIs with ≥1 relationship / total CIs |
| SC-P3-06 | QA coverage | % resolved tickets with QA score | 0% | ≥80% | Scored tickets / resolved tickets (30-day) |
| SC-P3-07 | Audit log completeness | % user actions captured | ~40% (Frappe native) | ≥95% | Audit log events / action types tracked |
| SC-P3-08 | WFM forecast accuracy | Predicted vs. actual ticket volume error | Unmeasured | ≤15% MAPE | Mean Absolute Percentage Error on 7-day forecasts |

**Decision Gate:** If SC-P3-01 (≥40% deflection) and SC-P3-03 (≥95% change success) are met, proceed to Phase 4. If not, iterate.

---

## Feature 1: Autonomous AI Agent

### Overview

A fully autonomous AI Agent that can independently resolve customer requests without agent intervention. The agent uses intent detection, knowledge base retrieval (RAG), ERPNext API actions, and a configurable decision framework to handle 40–60% of incoming tickets. Human handoff is seamless when confidence is low or escalation is triggered.

**Competitive benchmark:** Intercom Fin (best-in-class), Zendesk AI Agent, Freshdesk Freddy Self-Service
**Frappe differentiator:** ERPNext-native actions (order lookups, invoice status, asset queries) that no SaaS competitor can replicate

### User Stories

#### AI-Agent-01: Autonomous Ticket Resolution

**As a** support manager,
**I want** an AI Agent to automatically resolve incoming tickets using knowledge base articles and ERPNext data,
**So that** agents focus only on complex issues requiring human judgment.

**Acceptance Criteria:**

| ID | Criterion |
|----|-----------|
| AA-01-AC-1 | AI Agent evaluates every new ticket and assigns a `resolution_confidence` score (0.0–1.0) |
| AA-01-AC-2 | Tickets with confidence ≥ configurable threshold (default: 0.80) are auto-resolved by the agent |
| AA-01-AC-3 | Auto-resolved tickets receive a reply drafted from KB articles and/or ERPNext data with source citations |
| AA-01-AC-4 | Customer can respond "this didn't help" to reopen the ticket and route to human agent |
| AA-01-AC-5 | AI Agent adds internal note with reasoning: intent detected, articles used, confidence score, ERPNext data queried |
| AA-01-AC-6 | All AI actions are logged to `HD AI Agent Log` with timestamp, action type, tokens used, cost estimate |
| AA-01-AC-7 | Deflection rate dashboard widget visible to managers (7-day, 30-day, all-time) |
| AA-01-AC-8 | Agent can manually flag any AI-resolved ticket as "incorrectly resolved" to feed back into QA system |

#### AI-Agent-02: Intent Detection and Classification

**As an** agent,
**I want** every incoming ticket automatically classified by intent, urgency, and sentiment,
**So that** tickets are routed accurately and prioritized without manual triage.

**Acceptance Criteria:**

| ID | Criterion |
|----|-----------|
| AA-02-AC-1 | Intent classification runs within 10 seconds of ticket creation |
| AA-02-AC-2 | Detected intent is stored in `HD Ticket.ai_intent` field (multi-select: Billing, Technical, Account, Returns, Complaint, Other) |
| AA-02-AC-3 | Sentiment score stored in `HD Ticket.ai_sentiment` (-1.0 to 1.0) |
| AA-02-AC-4 | AI-suggested priority stored in `HD Ticket.ai_suggested_priority` (separate from human-set priority) |
| AA-02-AC-5 | Auto-categorization fills `category` and `sub_category` if confidence ≥ 0.75 and fields are empty |
| AA-02-AC-6 | Agent can override any AI classification; override is tracked for feedback loop |
| AA-02-AC-7 | Classification errors rate tracked in AI Quality dashboard |

#### AI-Agent-03: ERPNext-Aware AI Actions

**As a** customer,
**I want** the AI Agent to look up my order status, invoice, or asset without involving a human,
**So that** I get instant answers to data lookup questions 24/7.

**Acceptance Criteria:**

| ID | Criterion |
|----|-----------|
| AA-03-AC-1 | AI Agent can query ERPNext `Sales Order` by order number extracted from ticket content |
| AA-03-AC-2 | AI Agent can query `Sales Invoice` status and outstanding balance |
| AA-03-AC-3 | AI Agent can query `Asset` ownership and warranty details |
| AA-03-AC-4 | AI Agent can check `Delivery Note` shipment status |
| AA-03-AC-5 | All ERPNext actions require customer identity verification (ticket contact email matches ERPNext Customer primary email) |
| AA-03-AC-6 | ERPNext action results are included in AI reply with "as of [timestamp]" freshness note |
| AA-03-AC-7 | ERPNext integration can be disabled per-site if not using ERPNext |
| AA-03-AC-8 | ERPNext queries never expose data from other customers (row-level check by contact) |

#### AI-Agent-04: Human Handoff Protocol

**As an** agent,
**I want** the AI Agent to hand off conversations to me seamlessly when it cannot resolve them,
**So that** customers never feel stuck in a bot loop.

**Acceptance Criteria:**

| ID | Criterion |
|----|-----------|
| AA-04-AC-1 | Handoff is triggered when: confidence < threshold, customer explicitly asks for human, 3 failed resolution attempts, or urgent/angry sentiment detected |
| AA-04-AC-2 | On handoff, agent receives full AI conversation transcript and reasoning summary as internal note |
| AA-04-AC-3 | AI Agent sends customer a message: "I'm connecting you with a support agent who will follow up shortly" |
| AA-04-AC-4 | Ticket status changes to "Open" and enters normal assignment queue on handoff |
| AA-04-AC-5 | Handoff reason is recorded in `HD AI Agent Log` (low_confidence / customer_request / failed_resolution / urgent) |
| AA-04-AC-6 | Max AI interaction turns before forced handoff is configurable in HD Settings (default: 5) |

### Frappe DocType Design

#### HD AI Agent Config (Single DocType)
```
Fields:
- ai_agent_enabled: Check (default: 0)
- resolution_confidence_threshold: Float (default: 0.80)
- max_interaction_turns: Int (default: 5)
- auto_resolve_enabled: Check (default: 0)
- erpnext_actions_enabled: Check (default: 0)
- handoff_on_negative_sentiment: Check (default: 1)
- sentiment_handoff_threshold: Float (default: -0.5)
- deflection_target_pct: Float (default: 40.0)
- allowed_intents: Table → HD AI Agent Intent (intent_name, enabled, confidence_min)
```

#### HD AI Agent Log (Standard DocType)
```
Fields:
- ticket: Link → HD Ticket
- session_id: Data (unique per conversation)
- action_type: Select (intent_classify / kb_search / erpnext_query / reply_draft / auto_resolve / handoff)
- input_summary: Small Text
- output_summary: Small Text
- confidence_score: Float
- tokens_used: Int
- estimated_cost_usd: Currency
- action_outcome: Select (success / low_confidence / customer_rejected / error)
- erpnext_doctype: Data (if ERPNext action)
- erpnext_record: Data
- creation: Datetime (auto)
```

#### HD Ticket additions
```
New fields on HD Ticket:
- ai_intent: Small Text (JSON list of detected intents)
- ai_sentiment: Float (-1.0 to 1.0)
- ai_suggested_priority: Select (Low/Medium/High/Urgent)
- ai_resolution_confidence: Float
- ai_resolved: Check
- ai_resolved_at: Datetime
- ai_handoff_reason: Select (low_confidence/customer_request/failed_resolution/urgent)
- ai_resolution_marked_incorrect: Check
```

### API Requirements

```python
# helpdesk/api/ai_agent.py
@frappe.whitelist()
def process_new_ticket(ticket_name: str) -> dict:
    """Classify intent, sentiment, and attempt resolution. Returns action taken."""

@frappe.whitelist()
def attempt_resolution(ticket_name: str) -> dict:
    """Build RAG context, call LLM, return draft reply and confidence score."""

@frappe.whitelist()
def execute_erpnext_action(ticket_name: str, action: str, params: dict) -> dict:
    """Execute an ERPNext lookup action on behalf of AI Agent."""

@frappe.whitelist()
def trigger_handoff(ticket_name: str, reason: str) -> dict:
    """Transition ticket from AI to human queue."""

@frappe.whitelist()
def get_deflection_stats(period: str = "30d") -> dict:
    """Return deflection rate, accuracy, handoff breakdown for dashboard."""

@frappe.whitelist()
def mark_ai_resolution_incorrect(ticket_name: str) -> dict:
    """Flag an AI-resolved ticket as incorrect; feeds QA system."""
```

### Integration Points

- **Phase 2 LLM Layer** (`helpdesk/ai/`) — AI Agent builds on the LLM provider abstraction
- **Phase 2 RAG Pipeline** — uses vector search over HD Article for knowledge retrieval
- **ERPNext** — direct frappe.db or REST API calls (same-site or cross-site)
- **HD Automation Engine** — AI Agent actions implemented as new automation action types

---

## Feature 2: Change Enablement

### Overview

Full ITIL v4 Change Enablement practice: Request for Change (RFC) lifecycle, Change Advisory Board (CAB) approval workflow, change calendar for conflict detection, and risk/impact assessment matrix. Links changes to incidents, problems, CIs, and service catalog items.

**Competitive benchmark:** ServiceNow Change Management (gold standard), Jira Service Management Change
**Gap closed:** Phase 1 ITIL coverage was Incident-only (~35%); Change Enablement adds the second major ITIL practice

### User Stories

#### CE-01: Request for Change Lifecycle

**As a** change manager,
**I want** a structured RFC process with risk assessment and approval workflow,
**So that** all changes are reviewed, risk-scored, and approved before implementation.

**Acceptance Criteria:**

| ID | Criterion |
|----|-----------|
| CE-01-AC-1 | `HD Change Request` DocType supports full RFC fields: title, description, change_type (Standard/Normal/Emergency), risk_level (Low/Medium/High/Critical), implementation_plan, rollback_plan, test_plan |
| CE-01-AC-2 | RFC lifecycle states: Draft → Submitted → CAB Review → Approved/Rejected → Scheduled → Implementing → Implemented/Failed → Closed |
| CE-01-AC-3 | Risk matrix auto-calculates `risk_level` from impact × likelihood scores (both 1–5) |
| CE-01-AC-4 | Standard changes (pre-approved type) bypass CAB review and move directly to Scheduled |
| CE-01-AC-5 | Emergency changes have expedited CAB review (single approver sufficient) |
| CE-01-AC-6 | Rejected RFCs require rejection reason; submitter notified by email |
| CE-01-AC-7 | Each RFC has a `planned_start` and `planned_end` datetime for change calendar |
| CE-01-AC-8 | RFC can be linked to: HD Ticket (incident it resolves), HD Problem, HD Configuration Item (CIs affected) |

#### CE-02: CAB Approval Workflow

**As a** CAB member,
**I want** to review and vote on RFCs with full context before approving,
**So that** changes are only approved when risk is understood and plan is adequate.

**Acceptance Criteria:**

| ID | Criterion |
|----|-----------|
| CE-02-AC-1 | CAB members are defined in `HD CAB Member` DocType (user, role: Chair/Member/Technical Advisor) |
| CE-02-AC-2 | Normal changes require CAB quorum: configurable minimum % of members must vote (default: 51%) |
| CE-02-AC-3 | Each CAB member can vote: Approve, Approve with Conditions, Reject, Abstain |
| CE-02-AC-4 | CAB members receive email notification when RFC enters CAB Review state |
| CE-02-AC-5 | CAB dashboard shows all RFCs pending review with risk scores, timeline, and conflict indicators |
| CE-02-AC-6 | Approved with Conditions requires change owner to document how conditions are addressed |
| CE-02-AC-7 | Voting deadline is configurable per RFC (default: 48 hours); reminder sent 24 hours before deadline |
| CE-02-AC-8 | Full vote history stored on RFC; immutable after decision |

#### CE-03: Change Calendar

**As a** change manager,
**I want** a calendar view of all scheduled and planned changes,
**So that** I can detect conflicts and freeze windows before approving new changes.

**Acceptance Criteria:**

| ID | Criterion |
|----|-----------|
| CE-03-AC-1 | Calendar view shows all RFCs in Scheduled state by `planned_start`/`planned_end` |
| CE-03-AC-2 | Freeze windows can be defined in `HD Change Freeze Window` (name, start, end, scope: all/team/service) |
| CE-03-AC-3 | RFC submission blocked (with override option for Emergency) if planned window overlaps a freeze window |
| CE-03-AC-4 | Conflict detection: system warns when two RFCs affect the same CI in overlapping windows |
| CE-03-AC-5 | Calendar supports week/month/list views; filterable by change_type and risk_level |
| CE-03-AC-6 | Export calendar to iCal format for integration with Outlook/Google Calendar |

#### CE-04: Post-Implementation Review

**As a** change manager,
**I want** every implemented change to have a post-implementation review (PIR),
**So that** we learn from successful and failed changes to improve future risk assessments.

**Acceptance Criteria:**

| ID | Criterion |
|----|-----------|
| CE-04-AC-1 | PIR tab on RFC: actual_impact, deviations_from_plan, lessons_learned, recommendation_for_future |
| CE-04-AC-2 | Failed changes automatically trigger creation of an HD Ticket (incident) linked to the RFC |
| CE-04-AC-3 | PIR completion required before RFC can be Closed |
| CE-04-AC-4 | PIR data feeds Change analytics: success rate by change_type, risk_level, team |

### Frappe DocType Design

#### HD Change Request (Standard DocType)
```
Fields:
- title: Data (required)
- change_type: Select (Standard/Normal/Emergency)
- status: Select (Draft/Submitted/CAB Review/Approved/Rejected/Scheduled/Implementing/Implemented/Failed/Closed)
- risk_level: Select (Low/Medium/High/Critical) — auto-calculated
- impact_score: Int (1-5)
- likelihood_score: Int (1-5)
- priority: Select (Low/Medium/High/Critical)
- description: Long Text Editor
- justification: Long Text Editor
- implementation_plan: Long Text Editor
- rollback_plan: Long Text Editor
- test_plan: Long Text Editor
- requester: Link → User
- owner_team: Link → HD Team
- planned_start: Datetime
- planned_end: Datetime
- actual_start: Datetime
- actual_end: Datetime
- linked_incident: Link → HD Ticket
- linked_problem: Link → HD Problem
- affected_cis: Table → HD Change CI (ci_name, ci_type, impact_type)
- cab_votes: Table → HD CAB Vote (member, vote, comments, voted_at)
- pir_actual_impact: Long Text Editor
- pir_deviations: Long Text Editor
- pir_lessons_learned: Long Text Editor
- pir_recommendation: Long Text Editor
```

#### HD CAB Member (Standard DocType)
```
Fields:
- user: Link → User
- role: Select (Chair/Member/Technical Advisor/Observer)
- team: Link → HD Team
- active: Check
- change_types: Table → HD CAB Member Change Type (change_type)
```

#### HD Change Freeze Window (Standard DocType)
```
Fields:
- title: Data
- start_datetime: Datetime
- end_datetime: Datetime
- scope: Select (All/Team/Service)
- team: Link → HD Team (if scope=Team)
- service: Link → HD Service Catalog Item (if scope=Service)
- reason: Small Text
- created_by: Link → User
```

### API Requirements

```python
# helpdesk/api/change_management.py
@frappe.whitelist()
def submit_rfc(change_name: str) -> dict:
    """Submit RFC for CAB review. Validates required fields."""

@frappe.whitelist()
def cast_cab_vote(change_name: str, vote: str, comments: str = "") -> dict:
    """Record CAB member vote. Checks quorum and triggers state transition if met."""

@frappe.whitelist()
def check_change_conflicts(planned_start: str, planned_end: str, ci_names: list) -> dict:
    """Check for freeze windows and CI conflicts for proposed change window."""

@frappe.whitelist()
def get_change_calendar(start: str, end: str, filters: dict = None) -> list:
    """Return RFCs scheduled in date range for calendar view."""

@frappe.whitelist()
def complete_pir(change_name: str, pir_data: dict) -> dict:
    """Save PIR data and close RFC."""

@frappe.whitelist()
def get_change_analytics(period: str = "30d") -> dict:
    """Return change success rate, MTTR, risk distribution metrics."""
```

---

## Feature 3: CMDB / IT Asset Management

### Overview

Configuration Management Database (CMDB) with Configuration Items (CIs), relationship mapping, impact analysis, and ERPNext Asset integration. Enables IT teams to understand dependencies when incidents or changes occur — "which services does this server failure affect?"

**Competitive benchmark:** ServiceNow CMDB (undisputed leader), Jira SM Assets
**Frappe differentiator:** Native ERPNext Asset bootstrap — existing asset records become CIs instantly

### User Stories

#### CMDB-01: Configuration Item Registry

**As an** IT manager,
**I want** to register and maintain a catalog of all IT assets and services as Configuration Items,
**So that** I have a single source of truth for my IT estate.

**Acceptance Criteria:**

| ID | Criterion |
|----|-----------|
| CMDB-01-AC-1 | `HD Configuration Item` DocType supports CI types: Server, Application, Database, Network Device, Service, Endpoint, Cloud Resource, Virtual Machine |
| CMDB-01-AC-2 | Core CI attributes: name, ci_type, status (Active/Inactive/Decommissioned), owner_team, environment (Prod/Staging/Dev/DR), location, vendor, version, ip_address, hostname |
| CMDB-01-AC-3 | CI records link to ERPNext `Asset` record if applicable (one-to-one) |
| CMDB-01-AC-4 | CI bulk import from ERPNext Assets: one-click import creates CI record for each active Asset |
| CMDB-01-AC-5 | Each CI has a change history log (who changed what, when) |
| CMDB-01-AC-6 | CIs can have custom attributes via `HD CI Attribute` child table (key/value pairs) |
| CMDB-01-AC-7 | CI list view filterable by ci_type, status, environment, owner_team |

#### CMDB-02: CI Relationship Mapping

**As a** systems administrator,
**I want** to map dependencies between CIs (e.g., "Web App runs on Server A, depends on Database B"),
**So that** I can visualize the service dependency graph.

**Acceptance Criteria:**

| ID | Criterion |
|----|-----------|
| CMDB-02-AC-1 | `HD CI Relationship` DocType: source_ci, relationship_type, target_ci |
| CMDB-02-AC-2 | Relationship types: Runs On, Depends On, Hosts, Connected To, Backed Up By, Monitored By, Replicated To |
| CMDB-02-AC-3 | Relationship graph visualized as interactive node-graph on CI detail page (Vue + vis.js or D3) |
| CMDB-02-AC-4 | Graph traversal: expand upstream/downstream dependencies N levels deep |
| CMDB-02-AC-5 | Relationships are bidirectional: adding "A Depends On B" creates the inverse "B is depended on by A" |
| CMDB-02-AC-6 | Graph exported as PNG for incident reports |

#### CMDB-03: Impact Analysis

**As an** incident manager,
**I want** to see which services and users are impacted when a CI fails,
**So that** I can prioritize incident resolution and communicate to affected parties.

**Acceptance Criteria:**

| ID | Criterion |
|----|-----------|
| CMDB-03-AC-1 | Impact analysis triggered from HD Ticket detail page: "Analyze CI Impact" button when `linked_ci` is set |
| CMDB-03-AC-2 | Analysis traverses CI dependency graph to identify all downstream affected CIs |
| CMDB-03-AC-3 | Impact summary shows: affected services, affected users (via service subscriptions), estimated user count |
| CMDB-03-AC-4 | Impact severity score calculated: Critical (core service down), High (partial service degraded), Medium (non-core affected) |
| CMDB-03-AC-5 | Impact analysis result stored on HD Ticket and visible in ticket sidebar |
| CMDB-03-AC-6 | Affected users optionally notified via email template (configurable toggle) |

#### CMDB-04: CI Service Subscription

**As a** helpdesk admin,
**I want** to track which teams and customers subscribe to which CIs/services,
**So that** impact analysis can calculate affected user counts accurately.

**Acceptance Criteria:**

| ID | Criterion |
|----|-----------|
| CMDB-04-AC-1 | `HD CI Subscriber` child table on CI: subscriber_type (Team/Customer/User), subscriber_ref, notification_enabled |
| CMDB-04-AC-2 | Subscriber count shown on CI record and included in impact analysis |
| CMDB-04-AC-3 | Bulk subscriber import from CSV |

### Frappe DocType Design

#### HD Configuration Item (Standard DocType)
```
Fields:
- ci_name: Data (required, unique)
- ci_type: Select (Server/Application/Database/Network Device/Service/Endpoint/Cloud Resource/Virtual Machine/Other)
- status: Select (Active/Inactive/Decommissioned/Planned)
- environment: Select (Production/Staging/Development/Disaster Recovery)
- description: Small Text
- owner_team: Link → HD Team
- vendor: Data
- version: Data
- hostname: Data
- ip_address: Data
- location: Data
- erpnext_asset: Link → Asset (if ERPNext present)
- erpnext_asset_category: Data (fetch from asset)
- custom_attributes: Table → HD CI Attribute (key, value)
- subscribers: Table → HD CI Subscriber (subscriber_type, subscriber_ref, notification_enabled)
- relationships: (read via HD CI Relationship query)
```

#### HD CI Relationship (Standard DocType)
```
Fields:
- source_ci: Link → HD Configuration Item (required)
- relationship_type: Select (Runs On/Depends On/Hosts/Connected To/Backed Up By/Monitored By/Replicated To)
- target_ci: Link → HD Configuration Item (required)
- description: Small Text
- created_by: Link → User
```

#### HD CI Impact Analysis (Standard DocType — log of analyses)
```
Fields:
- ticket: Link → HD Ticket
- root_ci: Link → HD Configuration Item
- analysis_at: Datetime
- affected_ci_count: Int
- affected_service_count: Int
- affected_user_count: Int
- severity: Select (Critical/High/Medium/Low)
- affected_cis_json: Long Text (JSON list of affected CIs)
- notifications_sent: Check
```

### API Requirements

```python
# helpdesk/api/cmdb.py
@frappe.whitelist()
def import_from_erpnext_assets() -> dict:
    """Create HD CI records from all active ERPNext Assets. Returns import summary."""

@frappe.whitelist()
def get_ci_graph(ci_name: str, depth: int = 3) -> dict:
    """Return CI dependency graph nodes and edges up to N levels deep."""

@frappe.whitelist()
def run_impact_analysis(ticket_name: str, ci_name: str) -> dict:
    """Traverse graph, calculate impact, store result, return summary."""

@frappe.whitelist()
def get_affected_subscribers(ci_name: str, depth: int = 3) -> list:
    """Return list of all subscribers of affected CIs for notification."""

@frappe.whitelist()
def add_ci_relationship(source: str, rel_type: str, target: str) -> dict:
    """Add bidirectional CI relationship."""

@frappe.whitelist()
def search_cis(query: str, ci_type: str = None) -> list:
    """Search CIs by name/hostname/IP for ticket linking."""
```

---

## Feature 4: Service Catalog

### Overview

Structured catalog of available IT, HR, and facilities services with request forms, multi-stage approval workflows, SLA targets per item, and fulfillment step tracking. Replaces ad-hoc ticket creation with guided, consistent service request fulfillment.

**Competitive benchmark:** ServiceNow Service Catalog (gold standard), Jira SM Request Types
**Phase impact:** Drives SC-P3-04 (60%+ service requests via catalog)

### User Stories

#### SC-01: Service Catalog Item Management

**As an** IT admin,
**I want** to create and publish service catalog items with custom request forms,
**So that** customers and employees can submit well-structured requests.

**Acceptance Criteria:**

| ID | Criterion |
|----|-----------|
| SC-01-AC-1 | `HD Service Catalog Item` DocType: name, category, description, icon, availability (who can request), sla_policy, estimated_fulfillment_hours, approval_required |
| SC-01-AC-2 | Each catalog item has a custom request form: configurable fields (text, select, date, file upload, user lookup) |
| SC-01-AC-3 | Items grouped into `HD Service Catalog Category` (IT/HR/Facilities/Finance/Other) |
| SC-01-AC-4 | Items have availability rules: All Users, Agents Only, Specific Teams, Specific Roles |
| SC-01-AC-5 | Catalog published at `/support/catalog` in customer portal; agents see full catalog in helpdesk |
| SC-01-AC-6 | Items can be marked `popular` to appear in portal homepage widget |
| SC-01-AC-7 | Item can be deactivated without deletion (hidden from catalog, existing requests unaffected) |

#### SC-02: Service Request Fulfillment

**As a** customer,
**I want** to submit service requests from a catalog and track fulfillment progress,
**So that** I know what to expect and when my request will be completed.

**Acceptance Criteria:**

| ID | Criterion |
|----|-----------|
| SC-02-AC-1 | Submitting a catalog item creates an `HD Ticket` of type `Service Request` with catalog item reference |
| SC-02-AC-2 | SLA for the ticket uses the catalog item's `sla_policy` override (if set) |
| SC-02-AC-3 | Request form data stored as `HD Service Request Data` child table on ticket |
| SC-02-AC-4 | Customer sees request status with fulfillment step progress bar in portal |
| SC-02-AC-5 | Estimated completion date shown based on `estimated_fulfillment_hours` |
| SC-02-AC-6 | Customer notified at each fulfillment step completion |

#### SC-03: Approval Workflows

**As a** manager,
**I want** to configure multi-stage approval workflows for service requests,
**So that** requests requiring authorization are properly reviewed before fulfillment begins.

**Acceptance Criteria:**

| ID | Criterion |
|----|-----------|
| SC-03-AC-1 | Catalog items can have approval_workflow: None, Single Approver, Sequential, Parallel, Conditional |
| SC-03-AC-2 | Approvers defined per catalog item: Role, Specific User, Requester's Manager (via HR module if ERPNext) |
| SC-03-AC-3 | Approver receives email with request details and Approve/Reject links (one-click from email) |
| SC-03-AC-4 | Rejected requests require rejection reason; requester notified |
| SC-03-AC-5 | Approval history stored on ticket: who approved/rejected, when, comments |
| SC-03-AC-6 | Configurable approval deadline; auto-escalates to next approver if not actioned |
| SC-03-AC-7 | Conditional approval: if request cost > threshold → requires finance approval in addition |

#### SC-04: Fulfillment Step Tracking

**As a** fulfillment agent,
**I want** predefined fulfillment steps for each catalog item,
**So that** complex requests are completed consistently and progress is visible to customers.

**Acceptance Criteria:**

| ID | Criterion |
|----|-----------|
| SC-04-AC-1 | Catalog items have `HD Fulfillment Step Template` child table: step_name, assigned_team, estimated_hours, order |
| SC-04-AC-2 | On request creation, fulfillment steps instantiated as `HD Fulfillment Step` records on the ticket |
| SC-04-AC-3 | Each step can be assigned to different teams (e.g., Step 1: IT Provisioning, Step 2: Security, Step 3: Asset Delivery) |
| SC-04-AC-4 | Steps must be completed in order (sequential) unless marked parallel |
| SC-04-AC-5 | Step completion recorded with: completed_by, completed_at, notes |
| SC-04-AC-6 | Ticket auto-closes when all steps completed |

### Frappe DocType Design

#### HD Service Catalog Category (Standard DocType)
```
Fields:
- category_name: Data (required)
- description: Small Text
- icon: Data
- order: Int
- active: Check
```

#### HD Service Catalog Item (Standard DocType)
```
Fields:
- item_name: Data (required)
- category: Link → HD Service Catalog Category
- description: Long Text Editor
- icon: Attach Image
- availability: Select (All Users/Agents Only/Specific Roles)
- allowed_roles: Table → HD Catalog Item Role (role)
- sla_policy: Link → HD SLA Policy
- estimated_fulfillment_hours: Float
- approval_required: Check
- approval_workflow: Select (None/Single Approver/Sequential/Parallel)
- approvers: Table → HD Catalog Approver (approver_type, approver_ref, order)
- form_fields: Table → HD Catalog Form Field (field_name, field_type, required, options, order)
- fulfillment_steps: Table → HD Fulfillment Step Template (step_name, team, estimated_hours, order, is_parallel)
- popular: Check
- active: Check
```

#### HD Fulfillment Step (Child DocType of HD Ticket)
```
Fields:
- step_name: Data
- order: Int
- is_parallel: Check
- assigned_team: Link → HD Team
- status: Select (Pending/In Progress/Completed/Skipped)
- estimated_hours: Float
- completed_by: Link → User
- completed_at: Datetime
- notes: Small Text
```

### API Requirements

```python
# helpdesk/api/service_catalog.py
@frappe.whitelist()
def get_catalog(for_portal: bool = False) -> list:
    """Return available catalog items for current user (filtered by availability rules)."""

@frappe.whitelist()
def submit_request(catalog_item: str, form_data: dict) -> dict:
    """Create HD Ticket from catalog item. Initialize approval workflow and fulfillment steps."""

@frappe.whitelist()
def process_approval(ticket_name: str, decision: str, comments: str = "") -> dict:
    """Record approval/rejection. Advance workflow or reject."""

@frappe.whitelist()
def complete_fulfillment_step(ticket_name: str, step_name: str, notes: str = "") -> dict:
    """Mark a fulfillment step complete. Advance to next step or close ticket."""

@frappe.whitelist()
def get_request_status(ticket_name: str) -> dict:
    """Return approval status and fulfillment progress for customer portal."""
```

---

## Feature 5: Workforce Management

### Overview

Agent scheduling, shift management, capacity planning, and ticket volume forecasting. Enables support managers to ensure adequate staffing during peak periods and measure agent utilization.

**Competitive benchmark:** Zendesk Workforce Management (Tymeshift), ServiceNow WFM
**Target:** 50+ agent teams; smaller teams benefit from forecasting alone

### User Stories

#### WFM-01: Agent Scheduling and Shifts

**As a** support manager,
**I want** to define agent work schedules and shifts,
**So that** I can plan coverage and track when agents are available.

**Acceptance Criteria:**

| ID | Criterion |
|----|-----------|
| WFM-01-AC-1 | `HD Agent Schedule` DocType: agent, effective_from, effective_to, schedule_type (Fixed/Rotating) |
| WFM-01-AC-2 | Weekly schedule grid: Mon–Sun, each day has start_time, end_time, break_minutes |
| WFM-01-AC-3 | Agents can mark themselves available/unavailable from their profile |
| WFM-01-AC-4 | Manager can view team coverage calendar: who is on shift at any given time |
| WFM-01-AC-5 | Schedule-based SLA business hours: agent availability (not just HD Business Hours) drives routing |
| WFM-01-AC-6 | Shift handover notes: outgoing agent leaves summary for incoming agent on open tickets |

#### WFM-02: Capacity Planning

**As a** support manager,
**I want** to compare forecasted ticket volume against available agent capacity,
**So that** I can identify understaffing before it causes SLA breaches.

**Acceptance Criteria:**

| ID | Criterion |
|----|-----------|
| WFM-02-AC-1 | Capacity dashboard: forecasted tickets (from WFM-03) vs. scheduled agent-hours per day/week |
| WFM-02-AC-2 | Capacity utilization % shown per team: (forecasted_hours_needed / scheduled_agent_hours) × 100 |
| WFM-02-AC-3 | Red/amber/green status: >90% = red (understaffed), 70–90% = amber, <70% = green |
| WFM-02-AC-4 | Alert sent to manager when forecasted utilization exceeds threshold for next 7 days |
| WFM-02-AC-5 | "Add coverage" action from capacity dashboard opens scheduling UI for the flagged day |

#### WFM-03: Ticket Volume Forecasting

**As a** support manager,
**I want** the system to forecast expected ticket volume based on historical patterns,
**So that** I can staff appropriately for anticipated peaks.

**Acceptance Criteria:**

| ID | Criterion |
|----|-----------|
| WFM-03-AC-1 | Forecast generated daily using 90-day rolling historical ticket volume data |
| WFM-03-AC-2 | Forecast uses weighted moving average with day-of-week seasonality adjustments |
| WFM-03-AC-3 | Forecast accuracy tracked: predicted vs. actual MAPE displayed in WFM dashboard |
| WFM-03-AC-4 | Forecast stored in `HD WFM Forecast` DocType; historic forecasts preserved |
| WFM-03-AC-5 | Manager can adjust forecast manually (add % uplift for planned campaigns, launches) |
| WFM-03-AC-6 | Forecast exported to CSV for external workforce planning tools |

### Frappe DocType Design

#### HD Agent Schedule (Standard DocType)
```
Fields:
- agent: Link → HD Agent
- effective_from: Date
- effective_to: Date
- schedule_type: Select (Fixed/Rotating)
- schedule_days: Table → HD Schedule Day (day_of_week, start_time, end_time, break_minutes, is_off)
```

#### HD WFM Forecast (Standard DocType)
```
Fields:
- forecast_date: Date (required, unique)
- forecasted_tickets: Int
- actual_tickets: Int (filled retrospectively)
- forecast_error_pct: Float (auto-calculated)
- forecast_method: Select (Weighted Moving Average/Manual)
- manual_adjustment_pct: Float
- generated_at: Datetime
```

### API Requirements

```python
# helpdesk/api/workforce.py
@frappe.whitelist()
def get_team_coverage(start_date: str, end_date: str, team: str = None) -> dict:
    """Return scheduled agent-hours per day for coverage calendar."""

@frappe.whitelist()
def get_capacity_dashboard(period_days: int = 14) -> dict:
    """Return forecast vs. capacity comparison with utilization %."""

@frappe.whitelist()
def generate_forecast(period_days: int = 14) -> list:
    """Run WMA forecast for next N days. Store in HD WFM Forecast."""

@frappe.whitelist()
def update_forecast_adjustment(forecast_date: str, adjustment_pct: float) -> dict:
    """Apply manual adjustment to forecast for a specific date."""
```

---

## Feature 6: Quality Assurance Scoring

### Overview

AI-assisted QA scoring system that evaluates every resolved ticket against a configurable rubric, generates agent scorecards, and enables coaching workflows. Closes the agent performance loop that CSAT alone cannot cover (CSAT response rate is typically 10–30%).

**Competitive benchmark:** Klaus (acquired by Zendesk), Front Smart QA, Dixa QA
**Key insight:** AI QA achieves 100% conversation coverage vs. 10–30% manual review coverage

### User Stories

#### QA-01: Automated Ticket Scoring

**As a** QA manager,
**I want** every resolved ticket automatically scored against a quality rubric,
**So that** I have 100% conversation coverage for agent quality measurement.

**Acceptance Criteria:**

| ID | Criterion |
|----|-----------|
| QA-01-AC-1 | QA score generated within 5 minutes of ticket resolution for all closed tickets |
| QA-01-AC-2 | Scoring rubric defined in `HD QA Rubric` DocType: up to 10 criteria, each with weight (sum = 100) |
| QA-01-AC-3 | Default rubric includes: Greeting (10%), Issue Understanding (20%), Resolution Quality (30%), Communication Tone (20%), Policy Adherence (10%), Resolution Speed (10%) |
| QA-01-AC-4 | LLM evaluates each rubric criterion against full ticket conversation; assigns score 1–5 with brief reasoning |
| QA-01-AC-5 | Composite QA score = weighted average; stored in `HD QA Score` DocType |
| QA-01-AC-6 | QA scoring can be disabled per team or per ticket type |
| QA-01-AC-7 | Scoring tokens/cost tracked in AI log |

#### QA-02: Agent Scorecards

**As an** agent,
**I want** to see my QA scorecard showing my performance trends and areas for improvement,
**So that** I can understand what good looks like and improve my customer interactions.

**Acceptance Criteria:**

| ID | Criterion |
|----|-----------|
| QA-02-AC-1 | Agent scorecard page: overall QA score trend (last 30/90 days), per-criterion breakdown |
| QA-02-AC-2 | Score percentile ranking within team (anonymized peer comparison) |
| QA-02-AC-3 | Lowest-scoring criterion highlighted with linked example tickets |
| QA-02-AC-4 | Agent can dispute a QA score; dispute creates a review task for QA manager |
| QA-02-AC-5 | Score trend: is agent improving or declining? (7-day moving average arrow) |

#### QA-03: QA Manager Dashboard and Coaching

**As a** QA manager,
**I want** a dashboard showing team quality trends and individual coaching needs,
**So that** I can focus coaching efforts where they will have the most impact.

**Acceptance Criteria:**

| ID | Criterion |
|----|-----------|
| QA-03-AC-1 | Team QA dashboard: average score by team, by criterion, by period |
| QA-03-AC-2 | Agents ranked by QA score (configurable: show rank, hide rank) |
| QA-03-AC-3 | "Needs Coaching" auto-flag: agents with score below threshold for 7+ consecutive days |
| QA-03-AC-4 | Coaching session DocType: `HD Coaching Session` linked to agent, with target criteria, session notes, action items |
| QA-03-AC-5 | QA score improvement tracked post-coaching: before/after comparison |
| QA-03-AC-6 | QA insights: top failure patterns across team (e.g., "Tone issues up 15% this week") |

### Frappe DocType Design

#### HD QA Rubric (Standard DocType)
```
Fields:
- rubric_name: Data (required)
- active: Check
- criteria: Table → HD QA Criterion (criterion_name, description, weight, scoring_guidance)
```

#### HD QA Score (Standard DocType)
```
Fields:
- ticket: Link → HD Ticket (required)
- agent: Link → HD Agent
- rubric: Link → HD QA Rubric
- composite_score: Float (1.0–5.0)
- criterion_scores: Table → HD QA Criterion Score (criterion, score, reasoning, tokens_used)
- scored_at: Datetime
- scored_by: Select (AI/Manual)
- disputed: Check
- dispute_notes: Small Text
- dispute_resolved_by: Link → User
- dispute_resolved_at: Datetime
- dispute_outcome: Select (Score Upheld/Score Revised)
- final_score: Float (after dispute resolution)
```

#### HD Coaching Session (Standard DocType)
```
Fields:
- agent: Link → HD Agent (required)
- manager: Link → User
- session_date: Date
- focus_criteria: Table → HD Coaching Focus (criterion, target_score)
- session_notes: Long Text Editor
- action_items: Table → HD Coaching Action (action, due_date, status)
- pre_session_avg_score: Float
- post_session_avg_score: Float (filled 30 days later)
```

### API Requirements

```python
# helpdesk/api/qa.py
@frappe.whitelist()
def score_ticket(ticket_name: str, rubric_name: str = None) -> dict:
    """Run LLM scoring on resolved ticket. Store HD QA Score. Return composite score."""

@frappe.whitelist()
def get_agent_scorecard(agent_email: str, period_days: int = 30) -> dict:
    """Return QA score history, criterion breakdown, trend, percentile rank."""

@frappe.whitelist()
def get_team_qa_dashboard(team: str = None, period_days: int = 30) -> dict:
    """Return team-level QA metrics: averages, trends, needs-coaching flags."""

@frappe.whitelist()
def dispute_qa_score(qa_score_name: str, notes: str) -> dict:
    """Record agent dispute. Create review task for QA manager."""

@frappe.whitelist()
def resolve_dispute(qa_score_name: str, outcome: str, revised_score: float = None) -> dict:
    """Manager resolves dispute. Optionally updates score."""

@frappe.whitelist()
def get_qa_insights(period_days: int = 7) -> dict:
    """Return top failure patterns, improvement trends, coaching recommendations."""
```

---

## Feature 7: Sandbox Environments

### Overview

Dedicated sandbox (test) environment capability for safely testing automation rules, SLA policies, workflow changes, and catalog items before deploying to production. Leverages Frappe's multi-site architecture.

**Competitive benchmark:** Zendesk Sandbox, ServiceNow Developer Instance
**Frappe advantage:** Multi-site architecture makes this technically straightforward

### User Stories

#### SB-01: Sandbox Provisioning

**As an** IT admin,
**I want** to provision a sandbox environment that mirrors my production configuration,
**So that** I can test changes safely before they affect live agents and customers.

**Acceptance Criteria:**

| ID | Criterion |
|----|-----------|
| SB-01-AC-1 | Sandbox management available under HD Settings → Sandbox Environments |
| SB-01-AC-2 | Provision new sandbox: copies HD Settings, SLA Policies, Automation Rules, Catalog Items, Teams (no ticket data) |
| SB-01-AC-3 | Sandbox URL clearly labeled (e.g., sandbox.helpdesk.company.com) with a persistent red "SANDBOX" banner |
| SB-01-AC-4 | Email sending disabled in sandbox by default (configurable) |
| SB-01-AC-5 | Sandbox can be reset to latest production configuration snapshot |
| SB-01-AC-6 | Sandbox access restricted to Admins and designated testers by default |
| SB-01-AC-7 | Changes tested in sandbox can be "promoted" to production via configuration export/import |

#### SB-02: Configuration Promotion

**As an** IT admin,
**I want** to promote tested configuration changes from sandbox to production,
**So that** I can deploy with confidence after validation.

**Acceptance Criteria:**

| ID | Criterion |
|----|-----------|
| SB-02-AC-1 | Export sandbox configuration as JSON (scoped: Automation Rules, SLA Policies, Catalog Items, QA Rubrics) |
| SB-02-AC-2 | Import configuration JSON to production with conflict detection (warn if record already exists) |
| SB-02-AC-3 | Import preview: show diff between sandbox and production before applying |
| SB-02-AC-4 | Import logged in audit trail with imported_by, source_sandbox, affected_records |

### Frappe DocType Design

#### HD Sandbox (Standard DocType)
```
Fields:
- sandbox_name: Data (required)
- site_name: Data (Frappe site name)
- status: Select (Provisioning/Active/Suspended/Archived)
- production_site: Data
- created_by: Link → User
- provisioned_at: Datetime
- last_reset_at: Datetime
- email_disabled: Check (default: 1)
- allowed_users: Table → HD Sandbox User (user)
```

### API Requirements

```python
# helpdesk/api/sandbox.py
@frappe.whitelist()
def provision_sandbox(sandbox_name: str) -> dict:
    """Create new Frappe site as sandbox. Copy production config. Return site URL."""

@frappe.whitelist()
def reset_sandbox(sandbox_name: str) -> dict:
    """Re-sync sandbox config from production. Preserve sandbox ticket data."""

@frappe.whitelist()
def export_sandbox_config(sandbox_name: str, scope: list) -> dict:
    """Export selected configuration as JSON for promotion."""

@frappe.whitelist()
def import_config(config_json: str, dry_run: bool = True) -> dict:
    """Import configuration to current site. dry_run=True returns diff only."""
```

---

## Feature 8: Comprehensive Audit Logging

### Overview

Full activity audit trail for all helpdesk operations: ticket actions, configuration changes, user access events, data exports, and admin operations. Meets SOC2, HIPAA, and ISO 27001 requirements for audit trail completeness.

**Competitive benchmark:** Zendesk Audit Log, ServiceNow Audit Trail
**Gap from Phase 1:** Frappe's built-in version tracking captures field changes but misses access events, failed logins, data exports, and admin configuration changes

### User Stories

#### AL-01: Comprehensive Action Logging

**As a** compliance officer,
**I want** every significant helpdesk action logged with actor, timestamp, and before/after state,
**So that** I can meet audit requirements and investigate incidents.

**Acceptance Criteria:**

| ID | Criterion |
|----|-----------|
| AL-01-AC-1 | `HD Audit Log` DocType captures: actor (user/IP), action_type, resource_type, resource_id, before_state (JSON), after_state (JSON), timestamp, session_id, source (UI/API/System) |
| AL-01-AC-2 | Captured action types: ticket_create, ticket_update, ticket_assign, ticket_close, ticket_reopen, ticket_delete, comment_add, internal_note_add, attachment_upload, attachment_delete |
| AL-01-AC-3 | Admin actions captured: user_create, user_deactivate, role_assign, settings_change, sla_policy_change, automation_rule_change, api_key_create, api_key_revoke |
| AL-01-AC-4 | Access events captured: login_success, login_failure, logout, password_change, mfa_enroll, mfa_disable |
| AL-01-AC-5 | Data events captured: bulk_export, data_deletion (GDPR), report_run, sandbox_config_export |
| AL-01-AC-6 | Audit log entries are immutable: no update/delete via UI or API; only append |
| AL-01-AC-7 | Audit log retention period configurable in HD Settings (default: 2 years); auto-archive to storage after retention period |

#### AL-02: Audit Log Search and Export

**As a** compliance officer,
**I want** to search, filter, and export audit log entries,
**So that** I can respond to compliance requests and investigate incidents efficiently.

**Acceptance Criteria:**

| ID | Criterion |
|----|-----------|
| AL-02-AC-1 | Audit log UI: searchable by actor, action_type, resource_id, date range |
| AL-02-AC-2 | Filter by action category (ticket / admin / access / data) |
| AL-02-AC-3 | Export filtered results to CSV and JSON |
| AL-02-AC-4 | Full-text search on before/after state JSON (resource details) |
| AL-02-AC-5 | Individual resource audit trail: "show all audit log entries for Ticket #1234" |
| AL-02-AC-6 | Suspicious activity detection: >10 failed logins in 5 minutes triggers alert to admin |

#### AL-03: Audit Log API

**As a** security team member,
**I want** audit log data available via API for SIEM integration,
**So that** helpdesk events can be correlated with other security data.

**Acceptance Criteria:**

| ID | Criterion |
|----|-----------|
| AL-03-AC-1 | REST API endpoint: `GET /api/method/helpdesk.api.audit.get_logs` with filters (date_from, date_to, actor, action_type) |
| AL-03-AC-2 | API requires `System Manager` or `Audit Log Viewer` role |
| AL-03-AC-3 | Webhook support: push new audit log entries to SIEM endpoint in real-time (configurable URL in HD Settings) |
| AL-03-AC-4 | Log format compatible with CEF (Common Event Format) for SIEM import |

### Frappe DocType Design

#### HD Audit Log (Standard DocType — append-only)
```
Fields:
- log_id: Data (UUID, auto-generated)
- actor: Link → User
- actor_ip: Data
- session_id: Data
- action_type: Select (50+ action types as defined in AC-2,3,4,5)
- action_category: Select (Ticket/Comment/Admin/Access/Data/AI/Integration)
- resource_type: Data (DocType name)
- resource_id: Data
- resource_name: Data
- before_state: Long Text (JSON, compressed)
- after_state: Long Text (JSON, compressed)
- source: Select (Web UI/API/Background Job/System/Webhook)
- timestamp: Datetime (auto, indexed)
- severity: Select (Info/Warning/Critical)

Permissions: No write/update/delete for any role. Insert-only via system.
```

#### HD Audit SIEM Config (Child table in HD Settings)
```
Fields:
- siem_enabled: Check
- webhook_url: Data
- webhook_secret: Password
- format: Select (JSON/CEF)
- min_severity: Select (Info/Warning/Critical)
- action_categories: Table → HD Audit SIEM Category (action_category)
```

### API Requirements

```python
# helpdesk/api/audit.py
@frappe.whitelist()
def get_logs(filters: dict = None, limit: int = 100, offset: int = 0) -> list:
    """Search audit log with filters. Requires Audit Log Viewer role."""

@frappe.whitelist()
def get_resource_history(resource_type: str, resource_id: str) -> list:
    """All audit log entries for a specific resource."""

@frappe.whitelist()
def export_logs(filters: dict, format: str = "csv") -> dict:
    """Export filtered logs to CSV/JSON. Returns download URL."""

# Internal utility (not whitelisted)
def log_action(action_type: str, resource_type: str, resource_id: str,
               before_state: dict = None, after_state: dict = None,
               severity: str = "Info") -> None:
    """Append-only audit log writer. Called internally from all action handlers."""
```

---

## Technical Architecture Summary

### New DocTypes (Phase 3)

| DocType | Module | Type | Phase Feature |
|---------|--------|------|---------------|
| HD AI Agent Config | Helpdesk | Single | AI Agent |
| HD AI Agent Log | Helpdesk | Standard | AI Agent |
| HD Change Request | Helpdesk | Standard | Change Enablement |
| HD CAB Member | Helpdesk | Standard | Change Enablement |
| HD Change Freeze Window | Helpdesk | Standard | Change Enablement |
| HD Configuration Item | Helpdesk | Standard | CMDB |
| HD CI Relationship | Helpdesk | Standard | CMDB |
| HD CI Impact Analysis | Helpdesk | Standard | CMDB |
| HD Service Catalog Category | Helpdesk | Standard | Service Catalog |
| HD Service Catalog Item | Helpdesk | Standard | Service Catalog |
| HD Fulfillment Step | Helpdesk | Child (HD Ticket) | Service Catalog |
| HD Agent Schedule | Helpdesk | Standard | WFM |
| HD WFM Forecast | Helpdesk | Standard | WFM |
| HD QA Rubric | Helpdesk | Standard | QA |
| HD QA Score | Helpdesk | Standard | QA |
| HD Coaching Session | Helpdesk | Standard | QA |
| HD Sandbox | Helpdesk | Standard | Sandbox |
| HD Audit Log | Helpdesk | Standard (append-only) | Audit |

### HD Ticket Additions (Phase 3)
```python
# New fields on HD Ticket
ai_intent, ai_sentiment, ai_suggested_priority, ai_resolution_confidence,
ai_resolved, ai_resolved_at, ai_handoff_reason, ai_resolution_marked_incorrect,
ticket_type,  # extend to include "Service Request"
catalog_item, service_request_data,
linked_change_request, linked_problem, linked_ci
```

### API Modules (Phase 3)
```
helpdesk/api/ai_agent.py    — Autonomous AI Agent
helpdesk/api/change_management.py — RFC lifecycle + CAB
helpdesk/api/cmdb.py        — CI registry + impact analysis
helpdesk/api/service_catalog.py — Catalog + fulfillment
helpdesk/api/workforce.py   — Scheduling + forecasting
helpdesk/api/qa.py          — QA scoring + scorecards
helpdesk/api/sandbox.py     — Sandbox management
helpdesk/api/audit.py       — Audit log search + export
```

### Frontend Components (Phase 3)

| Component | Location | Feature |
|-----------|----------|---------|
| AIAgentStatusBadge.vue | desk/src/components/ticket/ | AI Agent |
| AIAgentDeflectionWidget.vue | desk/src/pages/home/ | AI Agent |
| ChangeRequestList.vue | desk/src/pages/changes/ | Change Enablement |
| ChangeRequestDetail.vue | desk/src/pages/changes/ | Change Enablement |
| ChangeCalendar.vue | desk/src/pages/changes/ | Change Enablement |
| CABVotePanel.vue | desk/src/components/change/ | Change Enablement |
| CIRegistry.vue | desk/src/pages/cmdb/ | CMDB |
| CIRelationshipGraph.vue | desk/src/components/cmdb/ | CMDB |
| ImpactAnalysisPanel.vue | desk/src/components/ticket/ | CMDB |
| ServiceCatalog.vue | desk/src/pages/catalog/ + portal | Service Catalog |
| CatalogItemForm.vue | desk/src/pages/catalog/ | Service Catalog |
| FulfillmentProgress.vue | desk/src/components/ticket/ | Service Catalog |
| WFMCapacityDashboard.vue | desk/src/pages/workforce/ | WFM |
| AgentScheduleGrid.vue | desk/src/pages/workforce/ | WFM |
| QAScorecard.vue | desk/src/pages/qa/ | QA |
| QATeamDashboard.vue | desk/src/pages/qa/ | QA |
| CoachingSessionForm.vue | desk/src/pages/qa/ | QA |
| AuditLogViewer.vue | desk/src/pages/admin/ | Audit |
| SandboxManager.vue | desk/src/pages/admin/ | Sandbox |

---

## Phase 3 Sprint Plan

### Sprint 1–2: Audit Logging + Sandbox (Foundation for Compliance)
- HD Audit Log DocType (append-only); log_action() utility
- Instrument all existing ticket/admin/access actions
- SIEM webhook integration
- HD Sandbox DocType + provisioning flow
- Config export/import JSON format
- **Rationale:** Compliance infrastructure needed before any Phase 3 feature ships

### Sprint 3–4: Change Enablement
- HD Change Request, HD CAB Member, HD Change Freeze Window DocTypes
- RFC lifecycle state machine + Frappe Workflow
- CAB voting UI + email notifications
- Change calendar (Vue + fullcalendar.io)
- Conflict detection API

### Sprint 5–6: CMDB + Impact Analysis
- HD Configuration Item, HD CI Relationship DocTypes
- ERPNext Asset import bulk action
- Relationship graph visualization (vis.js)
- Impact analysis traversal algorithm
- Ticket sidebar CI link + impact panel

### Sprint 7–8: Service Catalog
- HD Service Catalog Category + Item DocTypes
- Catalog portal page (Vue)
- Approval workflow engine (build on Frappe Workflow)
- Fulfillment step tracking
- Customer portal request status page

### Sprint 9: Quality Assurance Scoring
- HD QA Rubric + HD QA Score DocTypes
- LLM scoring integration (uses Phase 2 LLM layer)
- Agent scorecard page
- QA manager dashboard
- Coaching session workflow

### Sprint 10: AI Agent + WFM
- AI Agent intent detection pipeline (uses Phase 2 AI infrastructure)
- ERPNext actions (order/invoice/asset lookup)
- Human handoff protocol
- HD Agent Schedule + HD WFM Forecast DocTypes
- Capacity planning dashboard
- Volume forecasting (WMA algorithm)

---

## Dependencies

| Phase 3 Feature | Phase 2 Dependency | Risk |
|-----------------|-------------------|------|
| AI Agent (autonomous resolution) | LLM Integration Layer (ADR-P2-01), RAG Pipeline (ADR-P2-03) | **HIGH** — AI Agent cannot function without Phase 2 LLM layer |
| AI Agent (ERPNext actions) | ERPNext must be co-installed | MEDIUM — graceful disable if ERPNext absent |
| QA Scoring | LLM Integration Layer (ADR-P2-01) | MEDIUM — fallback to manual scoring |
| AI KB Gap Analysis (Phase 2 story) | Must complete before AI Agent can suggest KB article creation | LOW |
| CMDB ERPNext Asset import | ERPNext must be co-installed | LOW — optional feature |
| Change Enablement | Frappe Workflow engine (Phase 1 foundation) | LOW — already in use for KB lifecycle |

---

## Non-Functional Requirements

| ID | Requirement | Category | Acceptance |
|----|-------------|----------|-----------|
| NFR-P3-01 | AI Agent response time ≤ 15 seconds for auto-resolution | Performance | Measured p95 on production traffic |
| NFR-P3-02 | QA scoring completes within 5 minutes of ticket close | Performance | Background job p95 latency |
| NFR-P3-03 | Audit log writes must not add >50ms latency to ticket operations | Performance | Async write via background job |
| NFR-P3-04 | Audit log must be tamper-evident (append-only enforcement at DB + API level) | Security | No UPDATE/DELETE SQL on HD Audit Log |
| NFR-P3-05 | CI relationship graph renders ≤2s for graphs with ≤500 nodes | Performance | Browser profiling |
| NFR-P3-06 | All Phase 3 DocTypes inherit Frappe role-based access control | Security | No public access without role |
| NFR-P3-07 | AI Agent never exposes customer data from other tenants | Security | ERPNext query row-level filter enforced |
| NFR-P3-08 | Sandbox environment isolated from production email/webhooks by default | Security | Email disabled flag enforced at send hook |
| NFR-P3-09 | CMDB supports ≥50,000 CI records without query degradation | Scale | Indexed CI name, ci_type, status |
| NFR-P3-10 | Audit log supports 10M+ entries with search ≤5s on indexed fields | Scale | Partitioned table or dedicated log store |

---

## Risk Register

| Risk | Impact | Probability | Mitigation |
|------|--------|-------------|-----------|
| AI Agent deflection rate below 40% target | High | Medium | Tune confidence threshold; expand KB coverage; ERPNext actions add significant deflection for data-lookup queries |
| CMDB graph complexity causes UI performance issues | Medium | Medium | Limit initial graph render depth to 3; use virtual rendering for large graphs (vis.js supports this) |
| Frappe multi-site sandbox provisioning complexity | Medium | Low | Use existing bench multi-site commands; sandbox is a configuration copy, not data copy |
| LLM API costs exceed budget in QA scoring | Low | Medium | Rate limit: max N scores/day; configurable scoring sample rate (score 100% by default, adjustable) |
| ERPNext actions expose sensitive financial data unintentionally | High | Low | Strict row-level filter by contact email; review ERPNext query whitelist; audit all ERPNext action calls |
| CAB approval workflow adoption resistance | Medium | Medium | Provide Standard change pre-approval templates that bypass CAB for routine operations |

---

## Appendix A: Integration with Phase 2 Features

Phase 3 is designed to build directly on Phase 2 deliverables:

| Phase 2 Feature | How Phase 3 Uses It |
|-----------------|---------------------|
| LLM Integration Layer (Story 2.0) | AI Agent, QA Scoring — both call LLM provider via same abstraction |
| AI Copilot Summarization (Story 2.2) | AI Agent uses summarization to build handoff context for human agents |
| Intelligent Triage (Story 2.3) | AI Agent re-uses intent classification; Phase 3 adds action execution on top |
| Skills-based Routing (Story 2.4) | Change requests and service catalog items route by team skills |
| AI KB Search (Story 2.7) | AI Agent uses semantic search to find resolution articles |
| AI QA Scoring (Story 2.8) | Phase 3 extends with coaching workflows and dispute resolution |

---

## Appendix B: Competitive Parity Summary After Phase 3

| Competitor | Pre-Phase 3 | Post-Phase 3 | Key Remaining Gaps |
|------------|-------------|--------------|-------------------|
| Freshdesk | ~85% | ~95% | Mobile app, community forums |
| Zoho Desk | ~85% | ~95% | Mobile app |
| Zendesk | ~65% | ~80% | Voice channel, marketplace (1500+ apps) |
| Jira SM | ~55% | ~80% | DevOps pipeline integration, advanced release mgmt |
| ServiceNow | ~30% | ~60% | Platform sophistication, GRC, HR module integration |
| Intercom | ~60% | ~75% | In-app product tours, proactive behavior-based messaging |

**Net result:** Phase 3 completes the ITSM transformation. Frappe Helpdesk becomes the leading open-source ITSM platform for mid-market IT departments — matching Jira SM feature-for-feature while costing 80% less (no per-agent SaaS fees).
