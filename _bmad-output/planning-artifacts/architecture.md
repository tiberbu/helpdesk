---
stepsCompleted: [1, 2, 3, 4, 5, 6, 7, 8]
workflowType: 'architecture'
lastStep: 8
status: 'complete'
completedAt: '2026-03-22'
inputDocuments:
  - _bmad-output/planning-artifacts/prd.md
  - _bmad-output/planning-artifacts/product-brief.md
  - _bmad-output/planning-artifacts/research.md
  - _bmad-output/planning-artifacts/ux-design-specification.md
project_name: 'Frappe Helpdesk Phase 1'
user_name: 'Mwogi'
date: '2026-03-22'
---

# Architecture Decision Document: Frappe Helpdesk Phase 1

_ITIL Foundation & Platform Transformation -- Technical Architecture_

---

## Project Context Analysis

### Requirements Overview

**Functional Requirements:**
Phase 1 encompasses 10 major feature areas with 30+ individual functional requirements organized into the following categories:

| Category | ID Range | Count | Architectural Impact |
|----------|----------|-------|---------------------|
| Incident Management Enhancement | FR-IM-01 to FR-IM-06 | 6 | Extends HD Ticket DocType; new DocTypes for categorization and incident models; background jobs for MTTR calculation |
| Internal Notes | FR-IN-01 | 1 | New communication type on HD Ticket; permission-gated visibility; @mention notification system |
| CSAT Surveys | FR-CS-01 to FR-CS-02 | 2 | New HD CSAT Response DocType; scheduled email delivery; one-click rating endpoint; dashboard widgets |
| Live Chat Widget | FR-LC-01 to FR-LC-04 | 4 | Embeddable JS widget; Socket.IO channels; HD Chat Session DocType; agent concurrency management |
| Workflow Automation | FR-WA-01 to FR-WA-03 | 3 | HD Automation Rule DocType with JSON conditions/actions; background job rule evaluation; SLA event triggers |
| Custom Report Builder | FR-CR-01 to FR-CR-02 | 2 | HD Custom Report DocType; dynamic query generation; chart rendering; scheduled export |
| Enhanced SLA Management | FR-SL-01 to FR-SL-04 | 4 | Business hours calculation engine; holiday calendar integration; proactive breach alerting; OLA/UC preparation |
| Knowledge Base Improvements | FR-KB-01 to FR-KB-05 | 5 | Frappe Workflow integration for article lifecycle; HD Article Version DocType; ticket-article linking |
| Multi-Brand Support | FR-MB-01 | 1 | HD Brand DocType; per-brand portal theming; brand-based ticket routing |
| Time Tracking | FR-TT-01 to FR-TT-02 | 2 | HD Time Entry DocType; timer UI component; ERPNext Timesheet sync |

**Non-Functional Requirements:**

| Category | Key Constraints | Architectural Implication |
|----------|----------------|--------------------------|
| Performance (NFR-P) | Agent workspace <2s load; search <500ms on 100K tickets; chat <200ms latency; widget <50KB gzipped | Lazy loading; Redis caching; efficient Socket.IO; separate widget build |
| Scalability (NFR-S) | 500 concurrent agents; 200 simultaneous chats; 100K tickets/month; 1000 rule evaluations/min | Redis Queue for async processing; Socket.IO room management; indexed queries |
| Security (NFR-SE) | Internal notes NEVER exposed to customers; chat token auth; CSAT single-use tokens; XSS prevention | Frappe role-based permissions; server-side sanitization; token generation |
| Usability (NFR-U) | Progressive disclosure; 30-min onboarding; WCAG 2.1 AA; full keyboard navigation | Feature flags in HD Settings; frappe-ui component library; ARIA attributes |
| Availability (NFR-A) | Core ticketing unaffected by chat/automation failures; graceful degradation | Circuit breaker patterns; isolated background job queues; fallback UI states |
| Maintainability (NFR-M) | 80% unit test coverage; full REST API coverage; channel abstraction; feature flags | Test infrastructure; standard Frappe CRUD; abstract base classes |

**Scale & Complexity:**
- Primary domain: Full-stack web application (Python/Vue 3)
- Complexity level: High -- real-time features, multi-channel architecture, ITIL compliance, background job orchestration
- Estimated new architectural components: 10 new DocTypes, 15+ API endpoints, 8+ Vue page components, 1 embeddable widget, 3 background job types

### Technical Constraints & Dependencies

| Constraint | Impact | Mitigation |
|-----------|--------|-----------|
| **Frappe Framework v15+** | All DocTypes, APIs, permissions, workflows governed by Frappe conventions | Follow Frappe patterns exactly; use hooks.py for event-driven logic |
| **MariaDB via Frappe ORM** | No raw SQL; all queries through Frappe's `frappe.db` API | Use `frappe.qb` (query builder) for complex reports; proper indexing |
| **Vue 3 + frappe-ui** | Frontend must use existing component library and patterns | Extend, don't replace; contribute reusable components back |
| **Socket.IO via Frappe** | Real-time constrained to Frappe's Socket.IO implementation | Use `frappe.realtime.publish` for server events; custom handlers in `realtime/` |
| **Redis Queue (RQ)** | Background jobs use Frappe's `frappe.enqueue` API | Define job functions in Python modules; use named queues for priority |
| **Existing 41+ DocTypes** | Must maintain backward compatibility with all existing data | Additive field changes only; no breaking schema migrations |
| **pyproject.toml build** | Python packaging via modern pyproject.toml, not setup.py | Follow existing package configuration patterns |

### Cross-Cutting Concerns Identified

1. **Feature Flags** -- All ITIL and new features toggle via HD Settings; "Simple Mode" vs "ITIL Mode" affects ticket form, dashboards, and reports
2. **Channel Abstraction** -- Email, Chat, and future channels must normalize into a unified message format before creating/updating HD Ticket communications
3. **Real-time Updates** -- Socket.IO used for: chat messages, SLA breach alerts, ticket updates, typing indicators, agent availability
4. **Permission Model** -- Internal notes, automation rules, custom reports, and brand management require new role-based permission checks layered on Frappe's existing RBAC
5. **Background Job Orchestration** -- SLA recalculation, automation rule evaluation, CSAT survey scheduling, report generation, and chat session management all run as background jobs
6. **Notification System** -- @mentions, SLA warnings, CSAT alerts, major incident notifications, and chat assignments all flow through a unified notification pipeline

---

## Starter Template Evaluation

### Primary Technology Domain

**Existing application** -- Frappe Helpdesk is a mature Frappe application with an established codebase, not a greenfield project. There is no starter template to select.

### Existing Technology Stack (Established)

| Layer | Technology | Version | Notes |
|-------|-----------|---------|-------|
| **Backend Framework** | Frappe Framework | v15+ | Python 3.10+, provides ORM, REST API, permissions, workflows |
| **Database** | MariaDB | 10.6+ | Via Frappe ORM; InnoDB engine |
| **Cache / Queue** | Redis | 7+ | Session cache, job queue (RQ), real-time pub/sub |
| **Frontend Framework** | Vue 3 | 3.3+ | Composition API, `<script setup>` syntax |
| **UI Library** | frappe-ui | Latest | Button, Badge, FormControl, ListView, TextEditor, etc. |
| **Build Tool** | Vite | 5+ | HMR, tree-shaking, optimized builds |
| **Styling** | Tailwind CSS | 3+ | Utility-first; consistent spacing/color tokens |
| **Icons** | Lucide | Latest | Tree-shakeable SVG icons |
| **Real-time** | Socket.IO | 4+ | Via Frappe; bidirectional event communication |
| **Package Manager** | yarn | 1.x | Frontend dependency management |
| **Python Packaging** | pyproject.toml | PEP 621 | Modern Python packaging standard |
| **Deployment** | Frappe Bench / Docker | -- | Standard Frappe deployment tooling |

**Architectural Decisions Already Made by Existing Codebase:**
- DocType system for data modeling (JSON schema definitions auto-generating DB tables, forms, and REST APIs)
- `hooks.py` for event-driven server-side logic (doc_events, scheduler_events, etc.)
- `frappe.enqueue()` for background job processing via Redis Queue
- `frappe.realtime` for Socket.IO event publishing
- `createResource` / `createListResource` for frontend data fetching (SWR-like caching)
- `ListViewBuilder` pattern for all list pages with filtering, sorting, pagination
- Pinia stores for frontend state management
- Route-based code splitting with Vue Router

---

## Core Architectural Decisions

### Decision Priority Analysis

**Critical Decisions (Block Implementation):**
1. HD Ticket extension strategy (extend vs. new DocTypes)
2. Channel abstraction layer design
3. Live chat architecture (Socket.IO rooms, session management)
4. Automation rule evaluation engine design
5. SLA business hours calculation approach

**Important Decisions (Shape Architecture):**
6. CSAT survey delivery mechanism
7. Custom report query generation strategy
8. Knowledge base article workflow integration
9. Widget build and embedding strategy

**Deferred Decisions (Phase 2+):**
- AI/LLM integration layer (Phase 2)
- Vector search infrastructure (Phase 2)
- WhatsApp/SMS channel adapters (Phase 2)
- CMDB/Asset Management DocTypes (Phase 3)

### Data Architecture

#### ADR-01: Extend HD Ticket Rather Than Separate DocTypes

**Decision:** Add `record_type`, `impact`, `urgency`, `category`, `sub_category`, `is_major_incident`, and related fields directly to HD Ticket rather than creating separate Incident/Service Request DocTypes.

**Rationale:**
- Maintains backward compatibility with existing 41+ DocTypes that reference HD Ticket
- Preserves existing SLA, assignment, escalation, and notification logic
- Frappe DocType field additions are non-destructive (NULL default for legacy records)
- Progressive disclosure hides ITIL fields in "Simple Mode"

**Implementation:**
```python
# hooks.py doc_events pattern
doc_events = {
    "HD Ticket": {
        "validate": "helpdesk.helpdesk.overrides.hd_ticket.validate_priority_matrix",
        "on_update": "helpdesk.helpdesk.overrides.hd_ticket.evaluate_automation_rules",
    }
}
```

#### ADR-02: New DocType Schema for Phase 1

**Decision:** Create 10 new DocTypes to support Phase 1 features:

```
New DocTypes:
├── HD Ticket Category          # Multi-level categorization tree
├── HD Related Ticket           # Child table for bidirectional ticket linking
├── HD CSAT Response            # Customer satisfaction survey responses
├── HD CSAT Survey Template     # Per-brand customizable survey templates
├── HD Automation Rule          # Visual rule builder definitions
├── HD Automation Log           # Rule execution audit trail
├── HD Time Entry               # Per-ticket time logging
├── HD Incident Model           # Predefined incident templates
├── HD Article Version          # KB article version history
├── HD Brand                    # Multi-brand configuration
├── HD Chat Session             # Live chat session tracking
└── HD Chat Message             # Individual chat messages (child of session)
```

**Key Relationships:**

```
HD Ticket
├── category → HD Ticket Category (Link)
├── sub_category → HD Ticket Category (Link, filtered by category)
├── related_tickets → HD Related Ticket (Table, child)
├── time_entries → HD Time Entry (via ticket Link)
├── csat_response → HD CSAT Response (via ticket Link)
├── chat_session → HD Chat Session (via ticket Link)
└── incident_model → HD Incident Model (Link)

HD Article
├── versions → HD Article Version (via article Link)
├── linked_tickets → HD Ticket (via linking table)
└── workflow_state → Frappe Workflow (Draft/Review/Published/Archived)

HD Service Level Agreement
└── agreement_type → Select (SLA/OLA/UC) [preparation field]

HD Brand
├── default_team → HD Team (Link)
├── default_sla → HD Service Level Agreement (Link)
└── csat_template → HD CSAT Survey Template (Link)
```

#### ADR-03: Priority Matrix Calculation

**Decision:** Implement a configurable Impact x Urgency priority matrix stored in HD Settings as a JSON field, with server-side calculation via `validate` hook.

**Schema:**
```python
# HD Settings additions
{
    "itil_mode_enabled": {"fieldtype": "Check", "default": 0},
    "priority_matrix": {
        "fieldtype": "JSON",
        "default": {
            "High-High": "Urgent",     # P1
            "High-Medium": "High",     # P2
            "High-Low": "Medium",      # P3
            "Medium-High": "High",     # P2
            "Medium-Medium": "Medium", # P3
            "Medium-Low": "Low",       # P4
            "Low-High": "Medium",      # P3
            "Low-Medium": "Low",       # P4
            "Low-Low": "Low"           # P5
        }
    }
}
```

### Authentication & Security

#### ADR-04: Permission Model Extensions

**Decision:** Layer new permissions on Frappe's existing RBAC system using custom `has_permission` methods and `frappe.whitelist` decorators.

**Permission Mapping:**

| Feature | Read | Write | Create | Delete | Condition |
|---------|------|-------|--------|--------|-----------|
| Internal Notes | Agent role | Agent role | Agent role | Agent/Admin | `note.is_internal` check on all customer-facing APIs |
| Automation Rules | All agents | Admin only | Admin only | Admin only | `frappe.only_for("System Manager", "HD Admin")` |
| Custom Reports | All agents | Creator/Admin | All agents | Creator/Admin | Standard Frappe owner permission |
| Brand Config | Admin only | Admin only | Admin only | Admin only | System Manager role |
| Chat Messages | Agent role | -- | Agent/Customer | -- | Token-based for customer; role-based for agent |
| CSAT Response | Agent role | -- | Customer (via token) | Admin only | One-time token authentication |

#### ADR-05: Chat Widget Security

**Decision:** Chat widget sessions use short-lived JWT tokens with customer email hash as subject. Tokens are generated on pre-chat form submission and validated server-side.

**Flow:**
```
Customer fills pre-chat form → POST /api/method/helpdesk.api.chat.create_session
→ Server validates email, generates JWT (24h expiry)
→ JWT returned to widget → Stored in localStorage
→ All subsequent Socket.IO messages include JWT in handshake
→ Server validates JWT on each message event
```

#### ADR-06: CSAT Survey Token Security

**Decision:** CSAT survey links use HMAC-SHA256 signed single-use tokens. Token encodes ticket ID + customer email + expiry. Token is invalidated after first use.

```python
# Token generation
token = hmac.new(
    key=frappe.utils.get_site_secret(),
    msg=f"{ticket_id}:{customer_email}:{expiry_timestamp}".encode(),
    digestmod="sha256"
).hexdigest()

# URL: /api/method/helpdesk.api.csat.submit_rating?token={token}&rating={1-5}
```

### API & Communication Patterns

#### ADR-07: Channel Abstraction Layer

**Decision:** Implement an abstract channel interface that normalizes all inbound messages (email, chat, future WhatsApp/SMS) into a unified `ChannelMessage` format before HD Ticket processing.

**Architecture:**

```
                    ┌──────────────┐
                    │  HD Ticket   │
                    │  Processing  │
                    └──────┬───────┘
                           │
                    ┌──────▼───────┐
                    │  Channel     │
                    │  Normalizer  │
                    └──────┬───────┘
                           │
              ┌────────────┼────────────┐
              │            │            │
      ┌───────▼──┐  ┌─────▼────┐  ┌───▼────────┐
      │  Email   │  │  Chat    │  │  WhatsApp  │
      │  Adapter │  │  Adapter │  │  Adapter   │
      └──────────┘  └──────────┘  └────────────┘
        (exists)     (Phase 1)     (Phase 2)
```

**ChannelMessage Interface:**
```python
class ChannelMessage:
    """Normalized message format for all channels."""
    source: str          # "email", "chat", "whatsapp", "portal"
    sender_email: str
    sender_name: str
    subject: str         # For email; auto-generated for chat
    content: str         # HTML content, sanitized
    content_type: str    # "text/html" or "text/plain"
    attachments: list    # [{filename, content, content_type}]
    metadata: dict       # Channel-specific metadata (chat_session_id, etc.)
    ticket_id: str       # Existing ticket ID if this is a reply
    is_internal: bool    # True for internal notes
    timestamp: datetime
```

**Implementation Location:** `helpdesk/helpdesk/channels/`
```
helpdesk/helpdesk/channels/
├── __init__.py
├── base.py              # Abstract ChannelAdapter base class
├── email_adapter.py     # Wraps existing email processing
├── chat_adapter.py      # New: Chat message normalization
├── normalizer.py        # ChannelMessage → HD Ticket communication
└── registry.py          # Channel adapter registration and dispatch
```

#### ADR-08: API Design for New Features

**Decision:** All new features expose APIs via standard Frappe patterns:

1. **DocType CRUD** -- Auto-generated REST endpoints (`/api/resource/HD Automation Rule`)
2. **Custom Methods** -- `@frappe.whitelist()` functions in `helpdesk/api/` modules
3. **Real-time Events** -- `frappe.realtime.publish` via Socket.IO

**New API Modules:**

| Module | Endpoints | Purpose |
|--------|-----------|---------|
| `helpdesk/api/chat.py` | `create_session`, `send_message`, `end_session`, `get_sessions`, `transfer_session` | Live chat operations |
| `helpdesk/api/csat.py` | `submit_rating`, `get_dashboard_data`, `get_agent_scores` | CSAT survey operations |
| `helpdesk/api/automation.py` | `test_rule`, `get_execution_stats`, `toggle_rule` | Automation rule management |
| `helpdesk/api/reports.py` | `execute_report`, `schedule_report`, `export_report` | Custom report operations |
| `helpdesk/api/time_tracking.py` | `start_timer`, `stop_timer`, `add_entry`, `get_summary` | Time tracking operations |
| `helpdesk/api/incident.py` | `flag_major_incident`, `link_tickets`, `propagate_update` | Major incident operations |

### Frontend Architecture

#### ADR-09: Frontend Component Organization

**Decision:** Organize new frontend components by feature domain, following the existing codebase pattern of `desk/src/pages/{domain}/` and shared components in `desk/src/components/`.

**New Page Components:**

| Route | Component | Feature |
|-------|-----------|---------|
| `/helpdesk/chat` | `desk/src/pages/chat/ChatDashboard.vue` | Agent chat queue |
| `/helpdesk/chat/:sessionId` | `desk/src/pages/chat/ChatSession.vue` | Individual chat conversation |
| `/helpdesk/reports` | `desk/src/pages/reports/ReportList.vue` | Custom report list |
| `/helpdesk/reports/new` | `desk/src/pages/reports/ReportBuilder.vue` | Report builder interface |
| `/helpdesk/automations` | `desk/src/pages/automations/AutomationList.vue` | Automation rule list |
| `/helpdesk/automations/:id` | `desk/src/pages/automations/AutomationBuilder.vue` | Rule builder UI |
| `/helpdesk/settings/brands` | `desk/src/pages/settings/Brands.vue` | Brand management |
| `/helpdesk/settings/categories` | `desk/src/pages/settings/Categories.vue` | Ticket category hierarchy |

**New Shared Components:**
```
desk/src/components/
├── chat/
│   ├── ChatWidget.vue           # Embeddable widget (separate build)
│   ├── ChatMessageList.vue      # Message display (shared agent/widget)
│   ├── ChatInput.vue            # Message input with attachments
│   └── AgentAvailability.vue    # Online/away/offline toggle
├── csat/
│   ├── CSATSurveyForm.vue       # One-click rating form
│   ├── CSATDashboardWidget.vue  # Dashboard CSAT widget
│   └── CSATScoreCard.vue        # Agent/team score display
├── automation/
│   ├── RuleConditionBuilder.vue # If-then-else condition UI
│   ├── RuleActionList.vue       # Action configuration
│   └── RuleTriggerSelect.vue    # Trigger type selection
├── reports/
│   ├── ReportFieldPicker.vue    # Drag-and-drop field selection
│   ├── ReportFilterBuilder.vue  # Filter configuration
│   └── ReportChartRenderer.vue  # Chart rendering (bar/line/pie)
├── ticket/
│   ├── InternalNote.vue         # Visually distinct internal note
│   ├── RelatedTickets.vue       # Related ticket sidebar panel
│   ├── TimeTracker.vue          # Start/stop timer + manual entry
│   ├── TicketCategorySelect.vue # Cascading category/sub-category
│   └── MajorIncidentBanner.vue  # Major incident alert banner
└── kb/
    ├── ArticleVersionHistory.vue # Version list and diff view
    └── ArticleLinkDialog.vue     # Search and link articles
```

#### ADR-10: Chat Widget Build Strategy

**Decision:** Build the embeddable chat widget as a separate Vite entry point that produces a standalone JS bundle (<50KB gzipped) with Shadow DOM isolation.

**Build Configuration:**
```javascript
// vite.config.widget.js (separate from main desk build)
export default defineConfig({
    build: {
        lib: {
            entry: 'widget/src/main.js',
            name: 'FrappeHelpdeskChat',
            fileName: 'helpdesk-chat',
            formats: ['iife']  // Single file, no modules
        },
        rollupOptions: {
            output: { inlineDynamicImports: true }
        },
        cssCodeSplit: false,
        minify: 'terser',
    }
});
```

**Widget Architecture:**
```
widget/
├── src/
│   ├── main.js              # Entry point; creates Shadow DOM root
│   ├── Widget.vue            # Root component
│   ├── components/
│   │   ├── PreChatForm.vue   # Name/email/subject collection
│   │   ├── ChatView.vue      # Message list + input
│   │   ├── OfflineForm.vue   # "Leave a message" fallback
│   │   └── BrandingHeader.vue # Logo, colors from config
│   ├── socket.js             # Socket.IO client (bundled)
│   └── styles.css            # Self-contained styles (no Tailwind)
└── vite.config.js            # Standalone build config
```

**Embedding:**
```html
<script src="https://helpdesk.example.com/assets/helpdesk-chat.js"
        data-site="https://helpdesk.example.com"
        data-brand="default"
        data-position="bottom-right"
        async></script>
```

#### ADR-11: State Management for Real-time Features

**Decision:** Extend existing Pinia stores pattern for new stateful features. Create dedicated stores for chat and notifications.

```
desk/src/stores/
├── agent.ts          # (existing) Agent profile and preferences
├── chat.ts           # NEW: Active chat sessions, unread counts
├── notifications.ts  # NEW: SLA alerts, @mentions, chat assignments
├── automation.ts     # NEW: Rule builder state
└── report.ts         # NEW: Report builder configuration state
```

### Infrastructure & Deployment

#### ADR-12: Background Job Architecture

**Decision:** Use Frappe's Redis Queue with dedicated job functions for each async operation. Use named queues to separate priorities.

**Job Categories:**

| Queue | Jobs | Priority | Frequency |
|-------|------|----------|-----------|
| `default` | Automation rule evaluation, ticket routing | Normal | On ticket events |
| `short` | SLA breach notifications, @mention notifications, chat session cleanup | High | Real-time / scheduled |
| `long` | Report generation, CSAT survey batch send, SLA recalculation, data export | Low | Scheduled / on-demand |

**Scheduler Events (hooks.py):**
```python
scheduler_events = {
    "cron": {
        "*/5 * * * *": [
            "helpdesk.helpdesk.doctype.hd_service_level_agreement.sla_monitor.check_sla_breaches"
        ],
        "0 */1 * * *": [
            "helpdesk.helpdesk.doctype.hd_csat_response.csat_scheduler.send_pending_surveys"
        ],
    },
    "daily": [
        "helpdesk.helpdesk.doctype.hd_automation_log.cleanup.purge_old_logs",
        "helpdesk.helpdesk.doctype.hd_article.review_reminder.send_review_reminders"
    ]
}
```

#### ADR-13: SLA Business Hours Calculation Engine

**Decision:** Implement business hours calculation as a pure Python utility that computes "business minutes elapsed" between two timestamps, accounting for working hours, holidays, and timezone differences.

**Algorithm:**
```python
def calculate_business_minutes(start: datetime, end: datetime,
                                service_days: list, holidays: list,
                                timezone: str) -> int:
    """
    1. Convert start/end to team timezone
    2. Iterate day-by-day from start to end
    3. For each day:
       a. Skip if holiday
       b. Skip if not a service day (e.g., Saturday)
       c. Calculate overlap between [day_start, day_end] and [service_start, service_end]
       d. Accumulate business minutes
    4. Return total business minutes
    """
```

**Integration Points:**
- Called from `hd_ticket.validate()` to update SLA countdown
- Called from SLA monitor cron job (every 5 minutes) for breach detection
- Caches service day/holiday data in Redis to avoid repeated DB queries

#### ADR-14: Automation Rule Evaluation Engine

**Decision:** Implement a condition-action engine that evaluates automation rules against ticket state changes, with loop detection and execution throttling.

**Architecture:**

```
Ticket Event (create/update/resolve/etc.)
    │
    ▼
Rule Fetcher (get enabled rules matching trigger type)
    │
    ▼
Condition Evaluator (evaluate AND/OR conditions against ticket fields)
    │
    ▼
Action Executor (execute matched actions in priority order)
    │
    ▼
Execution Logger (log results to HD Automation Log)
```

**Safety Guards:**
- **Loop detection:** Max 5 rule executions per ticket per minute
- **Auto-disable:** After 10 consecutive failures, rule is disabled with notification to creator
- **Execution timeout:** Individual action timeout of 30 seconds
- **Dry-run mode:** `test_rule` API endpoint evaluates conditions without executing actions

**Implementation Location:** `helpdesk/helpdesk/automation/`
```
helpdesk/helpdesk/automation/
├── __init__.py
├── engine.py          # Core rule evaluation engine
├── conditions.py      # Condition evaluator (AND/OR/field operators)
├── actions.py         # Action executors (assign, notify, set_field, etc.)
├── triggers.py        # Trigger type registry and event mapping
└── safety.py          # Loop detection, throttling, auto-disable
```

---

## Implementation Patterns & Consistency Rules

### Naming Patterns

**DocType Naming:**
- All new DocTypes prefixed with `HD ` (e.g., `HD Automation Rule`, `HD Chat Session`)
- DocType folder names: lowercase, underscored (e.g., `hd_automation_rule/`)
- DocType JSON filename matches folder name (e.g., `hd_automation_rule.json`)

**Database Naming:**
- Table names: `tabHD Automation Rule` (Frappe convention -- auto-generated)
- Column names: `snake_case` (e.g., `is_major_incident`, `agreement_type`)
- Link fields: target DocType name as fieldname where possible (e.g., `category` → `HD Ticket Category`)

**API Naming:**
- Whitelisted methods: `snake_case` (e.g., `create_session`, `submit_rating`)
- API module files: `snake_case.py` (e.g., `time_tracking.py`)
- Full API path: `helpdesk.api.{module}.{method}` (e.g., `helpdesk.api.chat.create_session`)

**Frontend Naming:**
- Vue components: PascalCase files (e.g., `ChatDashboard.vue`, `RuleConditionBuilder.vue`)
- Composables: camelCase with `use` prefix (e.g., `useChat.ts`, `useAutomation.ts`)
- Stores: camelCase (e.g., `chat.ts`, `notifications.ts`)
- Routes: kebab-case paths (e.g., `/helpdesk/chat`, `/helpdesk/reports`)

**Event Naming (Socket.IO):**
- Server events: `snake_case` (e.g., `chat_message`, `sla_warning`, `ticket_update`)
- Client events: `snake_case` (e.g., `send_message`, `typing_start`, `typing_stop`)

### Structure Patterns

**New DocType Structure (each DocType follows this pattern):**
```
helpdesk/helpdesk/doctype/hd_{name}/
├── __init__.py
├── hd_{name}.json          # DocType schema definition
├── hd_{name}.py            # Server-side controller (validate, on_update, etc.)
├── test_hd_{name}.py       # Unit tests
└── hd_{name}.js            # Client script (optional)
```

**API Module Structure:**
```python
# helpdesk/api/{feature}.py
import frappe
from frappe import _

@frappe.whitelist()
def method_name(param1: str, param2: int = 0):
    """Docstring explaining the endpoint."""
    frappe.has_permission("HD Ticket", "read", throw=True)
    # Implementation
    return {"data": result}
```

**Vue Component Structure:**
```vue
<template>
  <!-- Template using frappe-ui components -->
</template>

<script setup lang="ts">
// Imports: Vue, frappe-ui, composables, stores
// Props and emits with TypeScript types
// Reactive state with ref/reactive
// Data fetching with createResource/createListResource
// Event handlers
</script>
```

### Format Patterns

**API Response Formats:**
- Standard Frappe response: `{"message": data}` for whitelisted methods
- DocType CRUD: Standard Frappe REST response format
- Error responses: `frappe.throw()` with translatable message strings
- Validation errors: `frappe.throw(_("Message"), frappe.ValidationError)`

**Date/Time Formats:**
- Database: Frappe datetime format (`YYYY-MM-DD HH:mm:ss`)
- API: ISO 8601 strings
- Frontend display: dayjs formatting via existing `dayjs.ts` config

**JSON Field Conventions:**
- Automation rule conditions: `[{"field": "priority", "operator": "equals", "value": "Urgent"}]`
- Automation rule actions: `[{"type": "assign_to_team", "value": "Support L2"}]`
- All JSON stored in `JSON` or `Long Text` fieldtype with server-side validation

### Communication Patterns

**Socket.IO Room Strategy:**
```
Room Naming:
├── ticket:{ticket_id}        # All viewers of a specific ticket
├── chat:{session_id}          # Participants of a chat session
├── agent:{agent_email}        # Private channel for agent notifications
├── team:{team_name}           # Team-wide notifications
└── sla:warnings               # SLA warning broadcasts to managers
```

**Real-time Event Payload Structure:**
```javascript
{
    "event": "chat_message",          // Event type
    "room": "chat:SESS-001",          // Target room
    "data": {
        "session_id": "SESS-001",
        "sender": "customer@example.com",
        "content": "Hello, I need help",
        "timestamp": "2026-03-22T10:30:00Z",
        "type": "text"                // text, attachment, system
    }
}
```

### Process Patterns

**Error Handling:**
- Backend: `frappe.throw()` for user-facing errors; `frappe.log_error()` for system errors
- Automation failures: Log to HD Automation Log, increment failure counter, auto-disable after threshold
- Chat failures: Degrade to "Leave a message" form; never show raw errors to customer
- Frontend: `toast` notifications for user errors; console.error for debug

**Background Job Error Recovery:**
```python
@frappe.whitelist()
def enqueue_with_retry(method, **kwargs):
    """Standard pattern for background jobs with retry."""
    frappe.enqueue(
        method,
        queue="default",
        timeout=300,
        is_async=True,
        **kwargs
    )
```

**Loading States:**
- All async operations use frappe-ui's `createResource` loading state
- Chat: Optimistic UI updates (show message immediately, confirm on server acknowledgment)
- Reports: Show skeleton loader during query execution
- Automation dry-run: Progress indicator with step-by-step evaluation display

### Enforcement Guidelines

**All AI Agents MUST:**
1. Use `frappe.whitelist()` for every externally-callable API method
2. Add `frappe.has_permission()` checks before any data access
3. Use `frappe._(...)` for all user-facing strings (i18n)
4. Write `test_hd_{name}.py` with minimum 80% coverage for new DocTypes
5. Follow the existing `createResource` / `createListResource` pattern for frontend data fetching
6. Never use raw SQL; always use `frappe.db.get_all()`, `frappe.db.get_value()`, or `frappe.qb`
7. Add new fields to DocType JSON, not via Custom Field (since this is the app source)
8. Use `frappe.enqueue()` for any operation that might take >1 second

---

## Project Structure & Boundaries

### Complete Project Directory Structure

```
helpdesk/
├── helpdesk/                           # Backend Python module
│   ├── api/                            # API endpoints
│   │   ├── __init__.py
│   │   ├── agent.py                    # (existing)
│   │   ├── agent_home/                 # (existing)
│   │   ├── article.py                  # (existing)
│   │   ├── auth.py                     # (existing)
│   │   ├── chat.py                     # NEW: Live chat API
│   │   ├── csat.py                     # NEW: CSAT survey API
│   │   ├── automation.py               # NEW: Automation rule API
│   │   ├── reports.py                  # NEW: Custom report API
│   │   ├── time_tracking.py            # NEW: Time tracking API
│   │   ├── incident.py                 # NEW: Major incident API
│   │   ├── ticket.py                   # (existing)
│   │   ├── search.py                   # (existing)
│   │   └── ...                         # (other existing)
│   ├── helpdesk/                       # Core module
│   │   ├── doctype/                    # All DocTypes
│   │   │   ├── hd_ticket/              # (existing, extended)
│   │   │   ├── hd_ticket_category/     # NEW: Multi-level categorization
│   │   │   ├── hd_related_ticket/      # NEW: Ticket linking child table
│   │   │   ├── hd_csat_response/       # NEW: CSAT survey responses
│   │   │   ├── hd_csat_survey_template/ # NEW: Per-brand templates
│   │   │   ├── hd_automation_rule/     # NEW: Workflow automation rules
│   │   │   ├── hd_automation_log/      # NEW: Rule execution log
│   │   │   ├── hd_time_entry/          # NEW: Time tracking entries
│   │   │   ├── hd_incident_model/      # NEW: Incident templates
│   │   │   ├── hd_article_version/     # NEW: KB article versions
│   │   │   ├── hd_brand/              # NEW: Multi-brand config
│   │   │   ├── hd_chat_session/        # NEW: Chat sessions
│   │   │   ├── hd_chat_message/        # NEW: Chat messages
│   │   │   └── ...                     # (40+ existing DocTypes)
│   │   ├── channels/                   # NEW: Channel abstraction layer
│   │   │   ├── __init__.py
│   │   │   ├── base.py
│   │   │   ├── email_adapter.py
│   │   │   ├── chat_adapter.py
│   │   │   ├── normalizer.py
│   │   │   └── registry.py
│   │   └── automation/                 # NEW: Automation engine
│   │       ├── __init__.py
│   │       ├── engine.py
│   │       ├── conditions.py
│   │       ├── actions.py
│   │       ├── triggers.py
│   │       └── safety.py
│   ├── overrides/                      # (existing) Framework overrides
│   │   ├── hd_ticket.py                # Extended with ITIL validation
│   │   └── ...
│   ├── patches/                        # Database migration patches
│   │   └── v1_phase1/                  # NEW: Phase 1 migration patches
│   │       ├── add_itil_fields_to_ticket.py
│   │       ├── create_default_categories.py
│   │       ├── add_sla_agreement_type.py
│   │       └── add_article_lifecycle_fields.py
│   ├── templates/                      # Email templates
│   │   ├── csat_survey.html            # NEW: CSAT survey email
│   │   ├── sla_breach_alert.html       # NEW: SLA breach notification
│   │   ├── major_incident_alert.html   # NEW: Major incident notification
│   │   └── ...                         # (existing templates)
│   └── utils/                          # NEW: Shared utilities
│       ├── __init__.py
│       ├── business_hours.py           # SLA business hours calculator
│       ├── token.py                    # HMAC token generation/validation
│       └── sanitizer.py               # HTML/XSS sanitization for chat
├── desk/                               # Frontend Vue application
│   └── src/
│       ├── pages/
│       │   ├── chat/                   # NEW: Chat pages
│       │   │   ├── ChatDashboard.vue
│       │   │   └── ChatSession.vue
│       │   ├── reports/                # NEW: Report pages
│       │   │   ├── ReportList.vue
│       │   │   └── ReportBuilder.vue
│       │   ├── automations/            # NEW: Automation pages
│       │   │   ├── AutomationList.vue
│       │   │   └── AutomationBuilder.vue
│       │   ├── home/                   # (existing) Dashboard
│       │   ├── desk/                   # (existing) Ticket views
│       │   ├── knowledge-base/         # (existing) KB
│       │   ├── ticket/                 # (existing) Ticket detail
│       │   └── dashboard/              # (existing)
│       ├── components/
│       │   ├── chat/                   # NEW: Chat components
│       │   ├── csat/                   # NEW: CSAT components
│       │   ├── automation/             # NEW: Automation components
│       │   ├── reports/                # NEW: Report components
│       │   ├── ticket/                 # NEW: Ticket enhancement components
│       │   └── kb/                     # NEW: KB enhancement components
│       ├── composables/
│       │   ├── useChat.ts              # NEW: Chat composable
│       │   ├── useAutomation.ts        # NEW: Automation composable
│       │   └── realtime.ts             # (existing) Real-time composable
│       ├── stores/
│       │   ├── chat.ts                 # NEW: Chat state
│       │   └── notifications.ts        # NEW: Notification state
│       └── router/                     # Routes (updated with new pages)
├── widget/                             # NEW: Embeddable chat widget
│   ├── src/
│   │   ├── main.js
│   │   ├── Widget.vue
│   │   ├── components/
│   │   ├── socket.js
│   │   └── styles.css
│   └── vite.config.js
├── realtime/                           # Socket.IO handlers
│   └── handlers.js                     # Extended with chat events
└── docker/                             # Docker configuration
```

### Architectural Boundaries

**API Boundaries:**
- All external API calls go through `@frappe.whitelist()` methods
- Customer-facing APIs (CSAT, chat widget) use token-based authentication
- Agent APIs use Frappe session authentication
- No direct database access from frontend; all through `createResource`

**Component Boundaries:**
- Chat widget is a fully isolated build with its own Socket.IO client
- Automation engine is a standalone module with no direct frontend coupling
- Channel adapters are pluggable via registry pattern
- Report query generator is isolated from report UI

**Data Boundaries:**
- Internal notes have hard server-side permission boundary (never in customer API responses)
- Brand data scopes ticket visibility and portal theming
- Automation rules are admin-only with separate permission model
- CSAT responses are read-only after submission

### Requirements to Structure Mapping

| Feature Area | Backend Location | Frontend Location | Background Jobs |
|-------------|-----------------|-------------------|-----------------|
| Incident Management (FR-IM) | `doctype/hd_ticket/` (extended), `doctype/hd_ticket_category/`, `doctype/hd_incident_model/`, `api/incident.py` | `components/ticket/` | MTTR calculation |
| Internal Notes (FR-IN) | `doctype/hd_ticket/` (communication type), `overrides/hd_ticket.py` | `components/ticket/InternalNote.vue` | @mention notifications |
| CSAT Surveys (FR-CS) | `doctype/hd_csat_response/`, `doctype/hd_csat_survey_template/`, `api/csat.py` | `components/csat/` | Survey email scheduling |
| Live Chat (FR-LC) | `doctype/hd_chat_session/`, `doctype/hd_chat_message/`, `api/chat.py`, `channels/chat_adapter.py` | `pages/chat/`, `components/chat/`, `widget/` | Session cleanup |
| Workflow Automation (FR-WA) | `doctype/hd_automation_rule/`, `doctype/hd_automation_log/`, `automation/` | `pages/automations/`, `components/automation/` | Rule evaluation |
| Custom Reports (FR-CR) | `api/reports.py` | `pages/reports/`, `components/reports/` | Report generation, export |
| Enhanced SLA (FR-SL) | `doctype/hd_service_level_agreement/` (extended), `utils/business_hours.py` | Dashboard widgets | SLA monitoring cron |
| Knowledge Base (FR-KB) | `doctype/hd_article/` (extended), `doctype/hd_article_version/` | `components/kb/` | Review reminders |
| Multi-Brand (FR-MB) | `doctype/hd_brand/` | Settings page, portal theming | -- |
| Time Tracking (FR-TT) | `doctype/hd_time_entry/`, `api/time_tracking.py` | `components/ticket/TimeTracker.vue` | ERPNext sync |

### Data Flow

```
                    Customer Interaction Flow
                    ========================

  Customer (Email/Chat/Portal)
        │
        ▼
  Channel Adapter (email_adapter / chat_adapter)
        │
        ▼
  Channel Normalizer → ChannelMessage
        │
        ▼
  HD Ticket Processing
  ├── Create/Update HD Ticket
  ├── Trigger doc_events
  │   ├── validate: Priority matrix calculation
  │   ├── on_update: Automation rule evaluation
  │   └── on_update: SLA timer update
  │
  ├── Background Jobs
  │   ├── SLA monitoring (cron, every 5 min)
  │   ├── CSAT survey scheduling (cron, hourly)
  │   ├── Automation rule evaluation (on event)
  │   └── Report generation (on demand)
  │
  └── Real-time Events
      ├── ticket_update → ticket:{id} room
      ├── sla_warning → agent:{email} room
      ├── chat_message → chat:{session} room
      └── @mention → agent:{email} room
        │
        ▼
  Agent Dashboard / Ticket View / Chat Interface
```

---

## Architecture Validation Results

### Coherence Validation

**Decision Compatibility:**
- All technology choices are within the existing Frappe ecosystem -- no new infrastructure dependencies in Phase 1
- Vue 3 + frappe-ui + Tailwind CSS is the established frontend stack; all new components follow this
- Socket.IO for real-time is already in use; chat extends the same pattern
- Redis Queue for background jobs is the standard Frappe approach; new jobs follow existing patterns
- MariaDB with Frappe ORM -- all new DocTypes use standard JSON schema definitions

**Pattern Consistency:**
- DocType naming follows existing `HD ` prefix convention
- API endpoints follow existing `helpdesk.api.{module}` pattern
- Frontend components follow existing `pages/{domain}/` and `components/{domain}/` organization
- Real-time events follow existing `frappe.realtime.publish` pattern from collision detection

**Structure Alignment:**
- New directories (`channels/`, `automation/`, `utils/`, `widget/`) are additive; no reorganization of existing code
- All new DocTypes live under existing `helpdesk/helpdesk/doctype/` hierarchy
- Frontend routes extend existing Vue Router configuration
- Migration patches follow Frappe's `patches/` convention

### Requirements Coverage Validation

**Functional Requirements Coverage:**

| Requirement | Architectural Support | Status |
|------------|----------------------|--------|
| FR-IM-01: Impact/Urgency | HD Ticket field extension + priority matrix in HD Settings | Covered |
| FR-IM-02: Categorization | HD Ticket Category DocType + cascading Link fields | Covered |
| FR-IM-03: Incident Models | HD Incident Model DocType + auto-populate on selection | Covered |
| FR-IM-04: Related Linking | HD Related Ticket child table + bidirectional logic | Covered |
| FR-IM-05: Major Incidents | `is_major_incident` flag + notification pipeline + dashboard | Covered |
| FR-IM-06: MTTR Reporting | Background job calculation + dashboard widgets | Covered |
| FR-IN-01: Internal Notes | Communication type + permission boundary + @mention | Covered |
| FR-CS-01: CSAT Survey | HD CSAT Response + email scheduler + one-click token | Covered |
| FR-CS-02: CSAT Dashboard | API endpoints + dashboard widgets | Covered |
| FR-LC-01: Chat Widget | Separate widget build + Shadow DOM + Socket.IO | Covered |
| FR-LC-02: Real-time Chat | Socket.IO rooms + typing indicators + message status | Covered |
| FR-LC-03: Chat-to-Ticket | Channel adapter + HD Chat Session → HD Ticket | Covered |
| FR-LC-04: Agent Chat UI | Chat pages + concurrent session management | Covered |
| FR-WA-01: Rule Builder | HD Automation Rule + condition/action engine | Covered |
| FR-WA-02: Rule Logging | HD Automation Log + dashboard stats | Covered |
| FR-WA-03: SLA Triggers | SLA monitor cron + automation trigger integration | Covered |
| FR-CR-01: Report Builder | Dynamic query generation + chart rendering | Covered |
| FR-CR-02: Report Scheduling | Background job + email delivery | Covered |
| FR-SL-01: Business Hours | Business hours calculator utility + Redis caching | Covered |
| FR-SL-02: Breach Alerts | SLA monitor cron + real-time notifications | Covered |
| FR-SL-03: SLA Dashboard | API endpoints + dashboard widgets | Covered |
| FR-SL-04: OLA/UC Prep | `agreement_type` field on HD SLA | Covered |
| FR-KB-01: Article Workflow | Frappe Workflow engine integration | Covered |
| FR-KB-02: Article Versioning | HD Article Version DocType | Covered |
| FR-KB-03: Review Dates | `review_date` field + scheduler reminder | Covered |
| FR-KB-04: Ticket-Article Linking | Bidirectional linking + sidebar panel | Covered |
| FR-KB-05: Internal Articles | `internal_only` flag + permission check | Covered |
| FR-MB-01: Multi-Brand | HD Brand DocType + portal theming + routing | Covered |
| FR-TT-01: Time Logging | HD Time Entry DocType + timer component | Covered |
| FR-TT-02: Time Reports | API endpoints + ERPNext sync (optional) | Covered |

**Non-Functional Requirements Coverage:**

| NFR | Architectural Approach |
|-----|----------------------|
| NFR-P-01: <2s page load | Lazy loading, code splitting, createResource caching |
| NFR-P-02: <500ms search | Existing MariaDB full-text + indexed queries |
| NFR-P-03: <200ms chat | Socket.IO direct delivery, minimal server processing |
| NFR-P-04: <5s SLA recalc/1000 | Background job with Redis caching of calendar data |
| NFR-P-05: <50KB widget | Separate Vite build, tree-shaking, terser minification |
| NFR-P-06: <100ms rule eval | In-memory condition evaluation, no DB queries per rule |
| NFR-S-01: 500 agents | Frappe multi-worker; Socket.IO connection pooling |
| NFR-S-02: 200 chats | Socket.IO room-based routing; stateless message handling |
| NFR-S-03: 100K tickets/month | Indexed queries; background job offloading |
| NFR-SE-01: Notes isolation | Server-side permission check on ALL APIs returning ticket communications |
| NFR-SE-02: Chat auth | JWT token-based session authentication |
| NFR-SE-03: CSAT security | HMAC-signed single-use tokens |
| NFR-SE-06: XSS prevention | Server-side HTML sanitization via `bleach` or `frappe.utils.sanitize_html` |
| NFR-A-01: Core isolation | Automation/chat failures caught and logged; core CRUD unaffected |
| NFR-A-02: Graceful degradation | Widget shows offline form if Socket.IO unavailable |
| NFR-A-03: Auto-disable | Safety module auto-disables rules after 10 consecutive failures |
| NFR-M-01: 80% test coverage | Test files required for every new DocType |
| NFR-M-03: Channel abstraction | Abstract base class with adapter pattern |
| NFR-M-04: Feature flags | `itil_mode_enabled`, `chat_enabled`, `csat_enabled`, `automation_enabled` in HD Settings |

### Architecture Completeness Checklist

**Requirements Analysis**
- [x] Project context thoroughly analyzed (PRD, product brief, research, UX spec)
- [x] Scale and complexity assessed (high complexity, real-time features, 500 agents)
- [x] Technical constraints identified (Frappe Framework, MariaDB, existing 41+ DocTypes)
- [x] Cross-cutting concerns mapped (feature flags, channels, real-time, permissions, jobs, notifications)

**Architectural Decisions**
- [x] Critical decisions documented with rationale (14 ADRs)
- [x] Technology stack fully specified (existing + no new infra deps)
- [x] Integration patterns defined (channel abstraction, Socket.IO rooms, background jobs)
- [x] Performance considerations addressed (caching, async processing, indexed queries)

**Implementation Patterns**
- [x] Naming conventions established (DocType, API, frontend, events)
- [x] Structure patterns defined (DocType files, API modules, Vue components)
- [x] Communication patterns specified (Socket.IO rooms, event payloads)
- [x] Process patterns documented (error handling, loading states, background jobs)

**Project Structure**
- [x] Complete directory structure defined with all new files and directories
- [x] Component boundaries established (widget, automation engine, channel adapters)
- [x] Integration points mapped (data flow diagram)
- [x] Requirements to structure mapping complete (all 30+ FRs mapped)

### Architecture Readiness Assessment

**Overall Status:** READY FOR IMPLEMENTATION

**Confidence Level:** High -- architecture extends proven Frappe patterns with no new infrastructure dependencies

**Key Strengths:**
1. Zero new infrastructure requirements -- all features build on existing Frappe/Redis/MariaDB/Socket.IO stack
2. Channel abstraction enables Phase 2 channel additions (WhatsApp, SMS) without refactoring
3. Automation engine is modular and extensible with clear safety boundaries
4. Progressive disclosure via feature flags ensures backward compatibility
5. Separate widget build isolates chat widget performance from main application

**Areas for Future Enhancement:**
1. Vector search (Meilisearch/pgvector) will be needed for Phase 2 AI-powered KB search
2. LLM integration layer architecture to be designed in Phase 2
3. Horizontal Socket.IO scaling (Redis adapter) if 200 concurrent chat sessions is exceeded
4. Report query optimization may need materialized views at scale

### Implementation Handoff

**AI Agent Guidelines:**
1. Follow all architectural decisions exactly as documented in this ADR set
2. Use implementation patterns consistently -- DocType naming, API structure, component organization
3. Respect project structure boundaries -- new code goes in designated directories
4. All new features MUST be behind feature flags in HD Settings
5. Never break backward compatibility with existing DocTypes or APIs
6. Every new DocType must include tests with minimum 80% coverage
7. All user-facing strings must use `frappe._()` for i18n

**First Implementation Priority:**
Based on PRD recommended implementation order:
1. Sprint 1-2: Internal Notes (FR-IN-01), Impact/Urgency (FR-IM-01), Categorization (FR-IM-02), Time Tracking (FR-TT-01)
2. Sprint 3-4: CSAT Surveys (FR-CS-01), Related Linking (FR-IM-04), Business Hours SLA (FR-SL-01), Article Workflow (FR-KB-01)
3. Sprint 5-6: Automation Builder (FR-WA-01), Major Incidents (FR-IM-05), Breach Alerts (FR-SL-02), Ticket-Article Linking (FR-KB-04)
4. Sprint 7-8: Live Chat (FR-LC-01 through FR-LC-04), CSAT Dashboard (FR-CS-02)
5. Sprint 9-10: Report Builder (FR-CR-01), SLA Dashboard (FR-SL-03), Incident Reporting (FR-IM-06)
6. Sprint 11-12: Multi-Brand (FR-MB-01), Report Scheduling (FR-CR-02), KB Versioning/Reviews/Internal (FR-KB-02/03/05), Incident Models (FR-IM-03), Rule Logging (FR-WA-02)
