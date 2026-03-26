# Architecture Decision Document: Frappe Helpdesk Phase 2–4

_AI Intelligence, Omnichannel, Advanced ITIL & Platform Innovation — Technical Architecture_

**Version:** 1.0
**Date:** 2026-03-26
**Author:** BMAD Dev Agent (Amelia)
**Status:** Ready for Implementation
**Depends On:**
- `_bmad-output/planning-artifacts/architecture.md` — Phase 1 architecture (foundation)
- `docs/phase-2-4-competitive-analysis.md` — gap analysis driving Phase 2–4 scope
- `docs/feature-roadmap.md` — phased feature roadmap

---

## Architectural Foundation

Phase 2–4 builds on the Phase 1 architecture without replacing it. The established Phase 1
patterns — Frappe DocType system, Redis Queue background jobs, Socket.IO real-time, Vue 3 +
frappe-ui frontend, channel abstraction layer, and automation engine — remain canonical. This
document extends them.

**Phase 1 infrastructure already in place:**
- `helpdesk/helpdesk/channels/` — channel abstraction layer (email + chat adapters)
- `helpdesk/helpdesk/automation/` — rule evaluation engine
- `helpdesk/utils/` — business hours, token, sanitizer utilities
- Socket.IO room strategy (`ticket:`, `chat:`, `agent:`, `team:`, `sla:`)
- Pinia stores: `agent.ts`, `chat.ts`, `notifications.ts`, `automation.ts`, `report.ts`

---

## Section 1: AI/LLM Integration Layer

### ADR-P2-01: LLM Provider Abstraction

**Decision:** Implement a unified LLM provider interface that abstracts OpenAI, Anthropic,
Google Gemini, and local models (Ollama/vLLM) behind a single `LLMProvider` protocol. No
application code calls provider APIs directly.

**Architecture:**

```
helpdesk/helpdesk/ai/
├── __init__.py
├── providers/
│   ├── base.py              # Abstract LLMProvider protocol
│   ├── openai_provider.py   # OpenAI / Azure OpenAI adapter
│   ├── anthropic_provider.py # Anthropic Claude adapter
│   ├── gemini_provider.py   # Google Gemini adapter
│   └── ollama_provider.py   # Local Ollama / vLLM adapter
├── prompt_manager.py        # Prompt template registry + rendering
├── context_builder.py       # Build ticket/KB context for LLM calls
├── rag_pipeline.py          # Retrieval-augmented generation orchestration
├── embedding_service.py     # Text → vector embedding service
└── safety.py                # Rate limiting, cost control, PII redaction
```

**LLMProvider Interface:**
```python
class LLMProvider(Protocol):
    """Uniform interface for all LLM providers."""

    def complete(
        self,
        messages: list[dict],
        model: str,
        temperature: float = 0.7,
        max_tokens: int = 1024,
        stream: bool = False,
    ) -> LLMResponse: ...

    def embed(self, text: str, model: str) -> list[float]: ...

    def get_available_models(self) -> list[ModelInfo]: ...
```

**HD Settings additions for LLM configuration:**
```python
# HD Settings new fields
{
    "ai_enabled": {"fieldtype": "Check", "default": 0},
    "ai_provider": {"fieldtype": "Select", "options": "OpenAI\nAnthropic\nGoogle\nOllama\nCustom"},
    "ai_model": {"fieldtype": "Data"},          # e.g. "gpt-4o", "claude-sonnet-4-6"
    "ai_api_key": {"fieldtype": "Password"},
    "ai_base_url": {"fieldtype": "Data"},        # For Ollama / custom endpoints
    "ai_embedding_model": {"fieldtype": "Data"}, # e.g. "text-embedding-3-small"
    "ai_max_tokens_per_request": {"fieldtype": "Int", "default": 2048},
    "ai_cost_limit_daily_usd": {"fieldtype": "Currency", "default": 10},
}
```

**Implementation location:** `helpdesk/helpdesk/ai/`
**API module:** `helpdesk/api/ai.py`

---

### ADR-P2-02: Prompt Management System

**Decision:** Store prompt templates as versioned `HD Prompt Template` DocType records, not
hardcoded strings. Allows admins to customize AI behavior without code changes.

**New DocType: HD Prompt Template**
```
Fields:
- name: str (e.g. "reply_draft_v1")
- feature: Select (reply_draft | summarize | tone_adjust | translate | triage | qa_score)
- system_prompt: Long Text
- user_prompt_template: Long Text  # Jinja2 template
- model_override: Data (optional)
- temperature: Float (default 0.7)
- is_active: Check
- version: Int (auto-increment)
```

**Prompt rendering:**
```python
# helpdesk/helpdesk/ai/prompt_manager.py
def render_prompt(feature: str, context: dict) -> tuple[str, str]:
    """Returns (system_prompt, user_prompt) for given feature and context."""
    template = frappe.db.get_value(
        "HD Prompt Template",
        {"feature": feature, "is_active": 1},
        ["system_prompt", "user_prompt_template"]
    )
    user_prompt = frappe.render_template(template.user_prompt_template, context)
    return template.system_prompt, user_prompt
```

---

### ADR-P2-03: RAG Pipeline and Embedding Store

**Decision:** Use `pgvector` extension on PostgreSQL OR a standalone Meilisearch instance for
vector search. For self-hosted deployments defaulting to MariaDB (no pgvector), embed vectors
in a dedicated `HD Article Embedding` DocType with serialized float arrays, queried with cosine
similarity via Python. For production-scale deployments, Meilisearch is the recommended store.

**Embedding Store Options (configured in HD Settings):**

| Store | When to Use | Performance |
|-------|------------|-------------|
| `frappe_db` | Dev / small (<5K articles) | <500ms, no extra infra |
| `meilisearch` | Production (5K–500K articles) | <50ms, separate service |
| `pgvector` | PostgreSQL deployments | <20ms, SQL-native |

**New DocType: HD Article Embedding**
```
Fields:
- article: Link → HD Article
- embedding_model: Data
- vector_data: Long Text  # JSON-serialized float list
- chunk_index: Int
- chunk_text: Long Text
- created_at: Datetime
```

**RAG Pipeline flow:**
```
Query Text
    │
    ▼
embedding_service.embed(query_text)  → query_vector
    │
    ▼
vector_store.search(query_vector, top_k=5)  → [chunk_ids]
    │
    ▼
context_builder.assemble(chunks, ticket)  → context_string
    │
    ▼
LLMProvider.complete([system, user + context])  → response
    │
    ▼
Return to agent UI
```

**Indexing trigger:**
```python
# hooks.py additions
doc_events = {
    "HD Article": {
        "after_insert": "helpdesk.helpdesk.ai.embedding_service.enqueue_embed_article",
        "on_update": "helpdesk.helpdesk.ai.embedding_service.enqueue_embed_article",
    }
}
```

**Background job:** `frappe.enqueue("helpdesk.helpdesk.ai.embedding_service.embed_article", article_name=name, queue="long")`

---

### ADR-P2-04: AI Copilot API Endpoints

**New API module:** `helpdesk/api/ai.py`

| Endpoint | Description |
|----------|-------------|
| `draft_reply(ticket_name, tone)` | Generate draft reply from ticket thread + KB context |
| `summarize_ticket(ticket_name)` | Summarize ticket conversation |
| `suggest_articles(ticket_name)` | Return top-5 KB articles by semantic similarity |
| `adjust_tone(text, target_tone)` | Rewrite text in specified tone |
| `translate_text(text, target_language)` | Translate to target language |
| `triage_ticket(ticket_name)` | Classify intent, sentiment, suggested priority/team |
| `score_conversation(ticket_name, criteria)` | QA score for a resolved ticket |

All endpoints:
- `@frappe.whitelist()` with agent role check
- Rate-limited via `ai/safety.py` (max 60 AI calls/agent/hour)
- Cost tracked in `HD AI Usage Log` DocType

**New DocType: HD AI Usage Log**
```
Fields:
- agent: Link → HD Agent
- feature: Data
- provider: Data
- model: Data
- prompt_tokens: Int
- completion_tokens: Int
- cost_usd: Currency
- ticket: Link → HD Ticket (optional)
- created_at: Datetime
```

---

## Section 2: Channel Abstraction — Phase 2 Extensions

### ADR-P2-05: Extending the Channel Adapter Registry

**Decision:** The Phase 1 channel registry (`helpdesk/helpdesk/channels/registry.py`) is
extended with Phase 2 adapters using the same `ChannelAdapter` base class. No existing
adapters are modified.

**New Adapters:**

```
helpdesk/helpdesk/channels/
├── __init__.py
├── base.py                   # (existing)
├── email_adapter.py          # (existing)
├── chat_adapter.py           # (existing)
├── whatsapp_adapter.py       # NEW Phase 2
├── sms_adapter.py            # NEW Phase 2
├── facebook_adapter.py       # NEW Phase 2
├── instagram_adapter.py      # NEW Phase 2
├── twitter_adapter.py        # NEW Phase 2
└── voice_adapter.py          # NEW Phase 4 (WebRTC)
```

**WhatsApp Adapter architecture:**
```python
# helpdesk/helpdesk/channels/whatsapp_adapter.py
class WhatsAppAdapter(ChannelAdapter):
    """Wraps WhatsApp Business Cloud API (Meta)."""

    source = "whatsapp"

    def receive(self, webhook_payload: dict) -> ChannelMessage:
        """Parse incoming WhatsApp webhook → ChannelMessage."""

    def send(self, ticket_name: str, message: str, attachments: list = None) -> bool:
        """Send reply via WhatsApp Business API."""

    def send_template(self, phone: str, template_name: str, variables: dict) -> bool:
        """Send approved template message (for proactive outreach)."""
```

**HD Settings additions for channels:**
```python
{
    "whatsapp_enabled": {"fieldtype": "Check", "default": 0},
    "whatsapp_phone_number_id": {"fieldtype": "Data"},
    "whatsapp_access_token": {"fieldtype": "Password"},
    "whatsapp_verify_token": {"fieldtype": "Password"},
    "sms_enabled": {"fieldtype": "Check", "default": 0},
    "sms_provider": {"fieldtype": "Select", "options": "Twilio\nMessageBird\nAfricasTalking"},
    "sms_account_sid": {"fieldtype": "Data"},
    "sms_auth_token": {"fieldtype": "Password"},
    "sms_from_number": {"fieldtype": "Data"},
    "facebook_enabled": {"fieldtype": "Check", "default": 0},
    "facebook_page_token": {"fieldtype": "Password"},
    "facebook_verify_token": {"fieldtype": "Password"},
}
```

**Webhook endpoint registration:**
```python
# hooks.py
website_route_rules = [
    {"from_route": "/api/channel/whatsapp", "to_route": "helpdesk.helpdesk.channels.whatsapp_adapter.webhook"},
    {"from_route": "/api/channel/sms", "to_route": "helpdesk.helpdesk.channels.sms_adapter.webhook"},
    {"from_route": "/api/channel/facebook", "to_route": "helpdesk.helpdesk.channels.facebook_adapter.webhook"},
]
```

**Channel source tracked on HD Ticket:** existing `via` / `source` field extended with new values.

---

### ADR-P4-06: Voice/WebRTC Architecture

**Decision:** Phase 4 voice uses WebRTC peer connections mediated by a TURN/STUN server. The
Frappe backend handles signaling (SDP offer/answer exchange) via Socket.IO; media flows
peer-to-peer.

**Components:**
```
helpdesk/helpdesk/channels/voice/
├── signaling.py         # SDP offer/answer relay via Socket.IO
├── session.py           # HD Voice Session DocType controller
└── transcription.py     # Post-call transcription via Whisper API

widget/voice/
├── VoiceWidget.vue      # Customer-facing click-to-call button
└── webrtc.js            # RTCPeerConnection management
```

**New DocType: HD Voice Session**
```
Fields:
- ticket: Link → HD Ticket
- agent: Link → HD Agent
- customer_email: Data
- started_at: Datetime
- ended_at: Datetime
- duration_seconds: Int
- recording_url: Data
- transcript: Long Text
- sentiment_score: Float
```

---

## Section 3: ITIL Service Management — Problem, Change, CMDB

### ADR-P3-07: Problem Management DocTypes

**Decision:** Implement Problem Management as first-class DocTypes rather than extending HD Ticket.
A Problem is a distinct record type with its own lifecycle (Identified → Investigated → Known
Error → Resolved).

**New DocType: HD Problem**
```
Fields:
- title: Data (mandatory)
- description: Long Text
- status: Select (Identified | Under Investigation | Known Error | Resolved | Closed)
- root_cause: Long Text
- workaround: Long Text
- known_error: Check
- kedb_article: Link → HD Article  # Known Error DB article
- linked_incidents: Table → HD Problem Incident (child)
- category: Link → HD Ticket Category
- priority: Select (Critical | High | Medium | Low)
- owner: Link → HD Agent
- resolution_date: Date
- problem_review_date: Date
```

**New Child DocType: HD Problem Incident**
```
Fields:
- problem: Link → HD Problem (parent)
- ticket: Link → HD Ticket
- link_type: Select (Related Incident | Root Cause | Workaround Applied)
```

**New DocType: HD Change Request**
```
Fields:
- title: Data (mandatory)
- change_type: Select (Standard | Normal | Emergency)
- status: Select (Draft | Pending CAB | Approved | In Progress | Completed | Failed | Cancelled)
- description: Long Text
- justification: Long Text
- implementation_plan: Long Text
- rollback_plan: Long Text
- risk_level: Select (High | Medium | Low)
- scheduled_start: Datetime
- scheduled_end: Datetime
- actual_start: Datetime
- actual_end: Datetime
- approvers: Table → HD Change Approver (child)
- related_incidents: Table → HD Change Incident (child)
- linked_problems: Table → HD Change Problem (child)
- team: Link → HD Team
- owner: Link → HD Agent
```

**CAB Approval Workflow:**
```python
# Frappe Workflow: "HD Change Approval Workflow"
# States: Draft → Pending CAB → Approved / Rejected → In Progress → Completed
# Transitions gated by HD Change Approver role
```

**Change Calendar integration:** `HD Change Request` records with `scheduled_start/end` are
surfaced on an `/helpdesk/change-calendar` page as a timeline view.

---

### ADR-P3-08: CMDB Architecture

**Decision:** Implement a lightweight CMDB as `HD Configuration Item` (CI) DocType with
relationship tracking via `HD CI Relationship` child DocType. Deep ERPNext Asset integration
is provided via optional sync adapter.

**New DocType: HD Configuration Item**
```
Fields:
- ci_name: Data (mandatory)
- ci_type: Select (Server | Application | Database | Network Device | Service | Endpoint | Other)
- status: Select (Active | Inactive | Decommissioned | Under Maintenance)
- owner_team: Link → HD Team
- managed_by: Link → HD Agent
- location: Data
- environment: Select (Production | Staging | Development)
- ip_address: Data
- hostname: Data
- version: Data
- dependencies: Table → HD CI Relationship (child, "depends_on")
- impacted_by: Table → HD CI Relationship (child, "impacted_by")
- linked_tickets: Dynamic Link
- erpnext_asset: Link → Asset (optional ERPNext sync)
- metadata: JSON  # Flexible key-value pairs for CI-specific attributes
```

**New Child DocType: HD CI Relationship**
```
Fields:
- parent_ci: Link → HD Configuration Item
- related_ci: Link → HD Configuration Item
- relationship_type: Select (Depends On | Used By | Hosted On | Connects To | Managed By)
```

**Impact Analysis query:**
```python
@frappe.whitelist()
def get_impact_analysis(ci_name: str) -> dict:
    """Return all services/tickets potentially impacted by a CI failure."""
    # Traverse HD CI Relationship graph BFS
    # Return: {affected_cis, open_tickets, dependent_services}
```

---

## Section 4: Service Catalog

### ADR-P3-09: Service Catalog Architecture

**Decision:** Implement the Service Catalog as a structured set of DocTypes: `HD Service`,
`HD Service Form`, and `HD Service Request`. Fulfillment uses Frappe Workflow for multi-stage
approvals. The catalog is exposed in both the agent portal and customer portal.

**New DocType: HD Service**
```
Fields:
- service_name: Data (mandatory)
- category: Link → HD Ticket Category
- description: Long Text
- icon: Data (emoji or icon name)
- sla: Link → HD Service Level Agreement
- team: Link → HD Team
- approval_required: Check
- auto_fulfill: Check  # For simple requests (e.g. "add to mailing list")
- fulfillment_steps: Table → HD Service Step (child)
- form_template: Link → HD Service Form
- is_active: Check
- visibility: Select (Public | Internal | VIP Only)
- estimated_fulfillment_hours: Float
```

**New DocType: HD Service Form**
```
Fields:
- form_name: Data
- fields: JSON  # [{fieldname, label, fieldtype, mandatory, options}]
- validation_script: Code  # Optional JS validation
```

**New DocType: HD Service Request**
```
Fields:
- service: Link → HD Service
- ticket: Link → HD Ticket  # Auto-created ticket for SLA tracking
- requested_by: Link → User
- form_data: JSON  # Submitted form values
- status: Select (Submitted | Approved | In Progress | Fulfilled | Rejected | Cancelled)
- current_step: Int
- steps: Table → HD Service Request Step (child)
- approval_status: Select (Not Required | Pending | Approved | Rejected)
- approver: Link → HD Agent
- fulfilled_at: Datetime
- rejection_reason: Long Text
```

**Request Fulfillment Flow:**
```
Customer/Employee submits Service Catalog form
    │
    ▼
HD Service Request created (status: Submitted)
    │
    ├─ if approval_required → notify approver → wait for approve/reject
    │                          (Frappe Workflow state machine)
    ├─ if auto_fulfill → trigger fulfillment_action immediately
    └─ if manual steps → assign to team, iterate HD Service Request Steps
    │
    ▼
Ticket auto-created (HD Ticket linked to Service Request)
    │
    ▼
SLA tracking on linked ticket, notifications via existing pipeline
    │
    ▼
On all steps complete → status: Fulfilled → CSAT survey triggered
```

**Frontend:**
- `/helpdesk/catalog` — Agent portal service catalog browser
- `/portal/catalog` — Customer portal service catalog
- `desk/src/pages/catalog/ServiceCatalog.vue`
- `desk/src/pages/catalog/ServiceRequestForm.vue`
- `desk/src/pages/catalog/ServiceRequestDetail.vue`

---

## Section 5: Autonomous AI Agent Architecture

### ADR-P3-10: AI Agent Intent Detection and Action Framework

**Decision:** The AI Agent is implemented as a multi-step reasoning loop using a
`ReActAgent` pattern: Reason → Act → Observe → Reason. Each agent action is a
registered `AgentTool` with defined input/output schema.

**Architecture:**

```
helpdesk/helpdesk/ai/agent/
├── __init__.py
├── react_agent.py       # ReAct loop orchestration
├── tool_registry.py     # AgentTool registration + dispatch
├── tools/
│   ├── knowledge_base.py    # search_kb(query) → articles
│   ├── ticket_actions.py    # update_ticket(), add_reply(), close_ticket()
│   ├── erpnext_actions.py   # get_order_status(), get_invoice(), lookup_customer()
│   ├── email_tools.py       # send_email(), lookup_contact()
│   └── escalation.py        # escalate_to_agent(reason, context)
├── session_manager.py   # HD AI Agent Session DocType management
├── safety_guard.py      # Hallucination detection, action limits
└── handoff.py           # Human handoff protocol
```

**New DocType: HD AI Agent Session**
```
Fields:
- ticket: Link → HD Ticket
- status: Select (Active | Resolved | Escalated | Abandoned)
- turns: Table → HD AI Agent Turn (child)
- resolution_confidence: Float  # 0.0–1.0
- escalation_reason: Long Text
- actions_taken: JSON  # List of executed actions
- human_agent: Link → HD Agent (set on escalation)
- started_at: Datetime
- resolved_at: Datetime
```

**New Child DocType: HD AI Agent Turn**
```
Fields:
- turn_number: Int
- role: Select (User | AI | Tool | System)
- content: Long Text
- tool_name: Data (if role=Tool)
- tool_input: JSON
- tool_output: JSON
- timestamp: Datetime
```

**ReAct Loop:**
```python
class ReActAgent:
    MAX_TURNS = 20
    CONFIDENCE_THRESHOLD = 0.85

    def run(self, ticket_name: str) -> AgentResult:
        session = self._create_session(ticket_name)
        while session.turn_count < self.MAX_TURNS:
            # 1. REASON: build context, call LLM
            thought, action = self._reason(session)
            if action.type == "FINISH":
                return self._resolve(session, action)
            if action.type == "ESCALATE":
                return self._escalate(session, action.reason)
            # 2. ACT: execute tool
            result = tool_registry.execute(action.tool, action.inputs)
            # 3. OBSERVE: record result, loop
            session.add_turn("Tool", result)
        # Max turns reached → escalate
        return self._escalate(session, "Max turns exceeded")
```

**Human Handoff Protocol:**
```python
# handoff.py
def escalate_to_human(session: HDAgentSession, reason: str) -> None:
    """
    1. Set session status = "Escalated"
    2. Create handoff summary via LLM (what was tried, why escalated)
    3. Assign ticket to appropriate human agent (via existing routing)
    4. Add internal note to ticket with AI conversation summary
    5. Send real-time notification to assigned agent
    """
```

---

## Section 6: Real-Time Infrastructure — WebRTC and WebSocket Scaling

### ADR-P4-11: WebRTC Signaling Architecture

**Decision:** Voice/video calls use WebRTC with Frappe's existing Socket.IO as the signaling
channel. A TURN server (coturn) is required for NAT traversal in production.

**Signaling flow:**
```
Agent browser                        Frappe Server              Customer browser
    │                                     │                           │
    │── socket.emit('call_offer', sdp) ──►│── socket.to(room) emit ──►│
    │                                     │                           │
    │◄─ socket.emit('call_answer', sdp) ──│◄── socket.emit('call_answer') ─│
    │                                     │                           │
    │◄────── ICE candidates exchanged via Socket.IO ─────────────────►│
    │                                     │                           │
    │◄═══════════ WebRTC P2P Media (audio/video) ════════════════════►│
```

**New Socket.IO rooms for voice:**
```
voice:{ticket_name}    # Signaling room for a specific ticket voice call
```

**Configuration (HD Settings):**
```python
{
    "webrtc_enabled": {"fieldtype": "Check", "default": 0},
    "turn_server_url": {"fieldtype": "Data"},      # turns:host:5349
    "turn_username": {"fieldtype": "Data"},
    "turn_credential": {"fieldtype": "Password"},
    "stun_server_url": {"fieldtype": "Data", "default": "stun:stun.l.google.com:19302"},
}
```

---

### ADR-P2-12: WebSocket Scaling for 500+ Concurrent Agents

**Decision:** Frappe's Socket.IO server uses `socket.io-redis` adapter for horizontal scaling.
Multiple Frappe workers share session state through Redis pub/sub. No application-level changes
are required — this is a deployment-level configuration.

**Scaling configuration (docker-compose / bench supervisor):**
```yaml
# In production: multiple Socket.IO workers behind nginx load balancer
# nginx upstream with ip_hash for sticky sessions
upstream frappe_socketio {
    ip_hash;
    server frappe-worker-1:9000;
    server frappe-worker-2:9000;
    server frappe-worker-3:9000;
}
```

**Redis adapter configuration:**
```javascript
// realtime/handlers.js (existing file, add Redis adapter init)
const { createAdapter } = require("@socket.io/redis-adapter");
const { createClient } = require("redis");

const pubClient = createClient({ url: process.env.REDIS_URL });
const subClient = pubClient.duplicate();
io.adapter(createAdapter(pubClient, subClient));
```

**Capacity targets:**

| Load | Infrastructure | Latency |
|------|---------------|---------|
| 500 agents, 200 chats | 3× Frappe workers, Redis cluster | <200ms |
| 1000 agents, 500 chats | 6× workers, Redis Sentinel | <200ms |
| 2000+ agents | Redis Cluster, Kubernetes HPA | <300ms |

---

## Section 7: Analytics Pipeline

### ADR-P2-13: Event Streaming and Aggregation

**Decision:** Implement an analytics event pipeline using a lightweight event log
(`HD Analytics Event` DocType) as the source of truth. Aggregations run as scheduled
background jobs. For Phase 2, this is sufficient. Phase 4 may introduce Apache Kafka
or ClickHouse for higher-volume analytics.

**New DocType: HD Analytics Event**
```
Fields:
- event_type: Data      # "ticket_created", "ticket_resolved", "chat_started", etc.
- actor: Data           # agent email or "customer"
- entity_type: Data     # "HD Ticket", "HD Chat Session", etc.
- entity_name: Data
- properties: JSON      # Event-specific data
- timestamp: Datetime
- session_id: Data      # Browser session for funnel analysis
```

**Event emission:**
```python
# helpdesk/helpdesk/analytics/tracker.py
def track(event_type: str, actor: str, entity_type: str,
          entity_name: str, properties: dict = None) -> None:
    """Fire-and-forget analytics event. Enqueued to avoid blocking request."""
    frappe.enqueue(
        "helpdesk.helpdesk.analytics.tracker._write_event",
        queue="long",
        event_type=event_type, actor=actor,
        entity_type=entity_type, entity_name=entity_name,
        properties=properties or {}
    )
```

**Aggregation pipeline:**
```
helpdesk/helpdesk/analytics/
├── __init__.py
├── tracker.py          # Event emission API
├── aggregator.py       # Scheduled aggregation jobs
├── metrics.py          # Metric computation functions
├── predictive.py       # ML models for forecasting / scoring
└── exporters/
    ├── csv_exporter.py
    └── excel_exporter.py
```

**Scheduler events:**
```python
# hooks.py additions
scheduler_events = {
    "cron": {
        "0 * * * *": [
            "helpdesk.helpdesk.analytics.aggregator.aggregate_hourly_metrics"
        ],
        "0 2 * * *": [
            "helpdesk.helpdesk.analytics.aggregator.aggregate_daily_metrics",
            "helpdesk.helpdesk.analytics.predictive.update_breach_risk_scores",
        ],
        "0 3 * * 1": [
            "helpdesk.helpdesk.analytics.predictive.retrain_volume_forecast_model"
        ]
    }
}
```

---

### ADR-P2-14: Predictive Analytics Models

**Decision:** Phase 2 predictive models use scikit-learn trained on HD Analytics Events.
Models are serialized to `HD ML Model` DocType (pickle stored in Frappe files). No GPU or
external ML platform required for Phase 2. Phase 4 may introduce fine-tuning pipelines.

**Model inventory:**

| Model | Algorithm | Input Features | Output | Retrain |
|-------|-----------|---------------|--------|---------|
| SLA Breach Risk | Gradient Boosting | priority, age, category, agent load | breach_probability: 0–1 | Daily |
| Volume Forecast | SARIMA | historical ticket_created counts | next_7_days_volume | Weekly |
| Topic Clustering | KMeans + TF-IDF | ticket subjects + first replies | cluster_labels | Weekly |
| Agent Performance | Linear Regression | tickets_closed, CSAT, response_time | performance_score | Daily |

**New DocType: HD ML Model**
```
Fields:
- model_name: Data
- model_type: Select (breach_risk | volume_forecast | topic_cluster | agent_performance)
- version: Int
- accuracy_score: Float
- trained_at: Datetime
- model_file: Attach  # Serialized pickle
- is_active: Check
- training_samples: Int
- feature_names: JSON
```

---

## Section 8: Integration Framework

### ADR-P2-15: Outbound Webhook System

**Decision:** Implement a configurable outbound webhook system as `HD Webhook` DocType, fired
on configurable Frappe doc_events. This replaces ad-hoc integration code with a declarative
configuration approach.

**New DocType: HD Webhook**
```
Fields:
- webhook_name: Data (mandatory)
- is_enabled: Check
- trigger_doctype: Link → DocType
- trigger_events: JSON  # ["after_insert", "on_update", "on_submit"]
- condition: Code  # Python expression, e.g. doc.priority == "Urgent"
- url: Data (mandatory)
- http_method: Select (POST | PUT | PATCH)
- headers: JSON  # [{"key": "Authorization", "value": "Bearer ..."}]
- payload_template: Long Text  # Jinja2 template for request body
- secret: Password  # HMAC signature key
- retry_on_failure: Check
- max_retries: Int (default 3)
- timeout_seconds: Int (default 10)
```

**Webhook delivery:**
```python
# helpdesk/helpdesk/integrations/webhook_sender.py
def deliver_webhook(webhook_name: str, doc: Document) -> None:
    """Renders payload template, signs request, sends HTTP call with retry."""
    # Enqueued as background job to avoid blocking doc_events
```

**Signature format:** `X-Frappe-Helpdesk-Signature: sha256={hmac_hex}`

---

### ADR-P4-16: App Marketplace Architecture

**Decision:** The Frappe Helpdesk Marketplace is implemented as a directory of Frappe apps
(installable via `bench get-app`) with a curated registry hosted at `marketplace.frappe.io`.
Within Frappe Helpdesk, an `HD Marketplace` settings page lists available apps with
install/uninstall management via bench API.

**App categories:**
- `channel` — new channel adapters (Discord, Telegram, etc.)
- `ai_model` — LLM provider adapters
- `integration` — CRM, ERP, monitoring tool connectors
- `analytics` — custom dashboards and reports
- `workflow` — pre-built automation rule packs

**App manifest schema (each Marketplace app must include):**
```json
{
    "marketplace_id": "helpdesk-slack-channel",
    "display_name": "Slack Channel Adapter",
    "category": "channel",
    "version": "1.0.0",
    "frappe_helpdesk_version": ">=2.0",
    "entry_points": {
        "channel_adapter": "helpdesk_slack.channels.slack_adapter.SlackAdapter"
    },
    "settings_doctype": "HD Slack Settings"
}
```

---

### ADR-P3-17: SSO and SAML Integration

**Decision:** SSO for the agent portal uses Frappe's built-in Social Login Keys + OAuth 2.0
support. SAML 2.0 is added via `frappe-saml` library integration. Customer portal SSO uses
JWT tokens compatible with ERPNext Customer Portal.

**SSO configuration (HD Settings):**
```python
{
    "sso_enabled": {"fieldtype": "Check", "default": 0},
    "sso_provider": {"fieldtype": "Select", "options": "Google\nMicrosoft\nGitHub\nSAML\nOkta\nCustom"},
    "saml_entity_id": {"fieldtype": "Data"},
    "saml_sso_url": {"fieldtype": "Data"},
    "saml_certificate": {"fieldtype": "Long Text"},
    "saml_attribute_mapping": {"fieldtype": "JSON"},
    # e.g. {"email": "urn:oid:1.2.840.113549.1.9.1", "name": "urn:oid:2.5.4.3"}
}
```

**SAML flow:**
```
Agent clicks "Sign in with SSO"
    │
    ▼
Redirect to IdP (Okta / Azure AD / Google Workspace)
    │
    ▼
IdP asserts SAML response → POST /api/method/helpdesk.api.auth.saml_acs
    │
    ▼
Map SAML attributes → Frappe User (create if first login)
    │
    ▼
Set Frappe session, redirect to /helpdesk
```

---

## Section 9: Multi-Tenancy and Sandbox Architecture

### ADR-P3-18: Multi-Tenancy via Frappe Sites

**Decision:** Multi-tenancy (multiple isolated customer organizations on one infrastructure)
uses Frappe's native multi-site architecture — one Frappe site per tenant. A lightweight
`HD Tenant Manager` admin utility manages site provisioning, configuration templates, and
cross-site monitoring.

**Tenant isolation model:**

| Layer | Isolation Mechanism |
|-------|-------------------|
| Data | Separate MariaDB database per Frappe site |
| Files | Separate `sites/{sitename}/private/` filesystem |
| Config | Separate `sites/{sitename}/site_config.json` |
| Cache | Separate Redis key namespace (`{sitename}:*`) |
| Jobs | Shared RQ workers but separate queues per site |

**New app: `frappe_helpdesk_saas`** (separate Frappe app for SaaS deployments only):
```
frappe_helpdesk_saas/
├── hooks.py
├── api/
│   ├── provisioning.py   # create_site(), suspend_site(), delete_site()
│   └── billing.py        # usage metrics for billing integration
├── doctypes/
│   ├── hd_tenant/        # Tenant registry
│   └── hd_tenant_plan/   # Subscription plan limits
└── templates/
    └── site_config_template.json
```

---

### ADR-P2-19: Sandbox / Staging Environment Architecture

**Decision:** Each production Frappe site can generate a sandbox (staging) site via
`bench --site {site} restore` into a separate `{site}-sandbox` site, with production
data anonymized. Sandbox sites are temporary (auto-deleted after 7 days).

**Sandbox use cases:**
1. Test automation rules before activating in production
2. Preview prompt template changes before rollout
3. QA for new Marketplace app installs

**Sandbox API:**
```python
# helpdesk/api/sandbox.py
@frappe.whitelist()
def create_sandbox(source_site: str, anonymize_pii: bool = True) -> dict:
    """Create sandbox from current site. Admin only."""

@frappe.whitelist()
def destroy_sandbox(sandbox_site: str) -> bool:
    """Delete sandbox site and all data."""
```

---

## Section 10: Performance at Scale

### ADR-P2-20: Performance Targets and Architecture for 500+ Agents / 100K+ Tickets/Month

**Performance Targets:**

| Metric | Phase 1 Target | Phase 2–4 Target | Mechanism |
|--------|---------------|-----------------|-----------|
| Agent workspace load | <2s | <1.5s | SWR caching, selective hydration |
| Ticket list (100K records) | <500ms | <300ms | Covering indexes, cursor pagination |
| AI reply draft | — | <3s | Streaming response, LLM timeout 10s |
| Chat message delivery | <200ms | <150ms | Socket.IO direct delivery |
| KB semantic search | — | <500ms | Meilisearch hybrid search |
| SLA recalculation (1K tickets) | <5s | <3s | Redis-cached calendar data |
| Webhook delivery p99 | — | <2s | Async queue, retry backoff |
| Analytics dashboard | — | <1s | Pre-aggregated metrics table |

---

### ADR-P2-21: Database Indexing Strategy for Scale

**Required indexes for 100K+ tickets/month:**

```sql
-- HD Analytics Event (high-write, high-read)
CREATE INDEX idx_analytics_type_time ON `tabHD Analytics Event` (event_type, timestamp);
CREATE INDEX idx_analytics_entity ON `tabHD Analytics Event` (entity_type, entity_name);

-- HD Ticket (existing, verify these exist)
CREATE INDEX idx_ticket_status_team ON `tabHD Ticket` (status, team);
CREATE INDEX idx_ticket_assigned_status ON `tabHD Ticket` (assigned_to, status);
CREATE INDEX idx_ticket_created ON `tabHD Ticket` (creation);
CREATE INDEX idx_ticket_sla_breach ON `tabHD Ticket` (response_by, resolution_by, status);

-- HD AI Usage Log (audit trail, append-only)
CREATE INDEX idx_ai_usage_agent_time ON `tabHD AI Usage Log` (agent, creation);

-- HD Article Embedding (vector lookup)
CREATE INDEX idx_embedding_article ON `tabHD Article Embedding` (article, embedding_model);
```

**Patch location:** `helpdesk/patches/v2_phase2/add_analytics_indexes.py`

---

### ADR-P2-22: Caching Strategy

**Redis cache key conventions for Phase 2–4:**

```python
CACHE_KEYS = {
    # AI
    "ai_provider_config":     "hd:ai:config",           # TTL: 5min
    "prompt_template:{feat}": "hd:prompt:{feature}",    # TTL: 1min
    "embedding:{article}":    "hd:emb:{article_name}",  # TTL: 24h

    # Analytics
    "metrics:daily:{date}":   "hd:metrics:day:{date}",  # TTL: 25h
    "metrics:hourly:{h}":     "hd:metrics:hr:{hour}",   # TTL: 2h
    "breach_risk:{ticket}":   "hd:risk:{ticket}",       # TTL: 5min

    # Channels
    "whatsapp_token":         "hd:wa:token",            # TTL: 55min
    "channel_registry":       "hd:channels:registry",  # TTL: 10min

    # Service Catalog
    "catalog:public":         "hd:catalog:pub",         # TTL: 5min
}
```

**Cache invalidation:** All cached values invalidated via `frappe.cache().delete_key(key)` in
relevant `on_update` hooks.

---

## New DocType Summary (Phase 2–4)

| DocType | Phase | Purpose |
|---------|-------|---------|
| HD Prompt Template | 2 | Versioned LLM prompt management |
| HD AI Usage Log | 2 | LLM cost tracking per agent/feature |
| HD Article Embedding | 2 | Vector embeddings for KB RAG |
| HD ML Model | 2 | Serialized predictive ML models |
| HD Analytics Event | 2 | Raw analytics event log |
| HD Webhook | 2 | Outbound webhook configuration |
| HD Problem | 3 | ITIL Problem Management |
| HD Problem Incident | 3 | Problem ↔ Incident linking (child) |
| HD Change Request | 3 | ITIL Change Enablement |
| HD Change Approver | 3 | CAB approver child table |
| HD Change Incident | 3 | Change ↔ Incident linking (child) |
| HD Change Problem | 3 | Change ↔ Problem linking (child) |
| HD Configuration Item | 3 | CMDB asset/service tracking |
| HD CI Relationship | 3 | CI dependency graph (child) |
| HD Service | 3 | Service Catalog entry |
| HD Service Form | 3 | Dynamic form template for catalog |
| HD Service Request | 3 | Service request fulfillment tracking |
| HD Service Request Step | 3 | Fulfillment step (child) |
| HD AI Agent Session | 3 | Autonomous AI agent conversation |
| HD AI Agent Turn | 3 | Single turn in AI session (child) |
| HD Voice Session | 4 | WebRTC voice call tracking |

---

## New API Modules (Phase 2–4)

| Module | Purpose |
|--------|---------|
| `helpdesk/api/ai.py` | AI Copilot endpoints (draft, summarize, suggest, tone, triage) |
| `helpdesk/api/problem.py` | Problem Management CRUD + linking |
| `helpdesk/api/change.py` | Change Request management + CAB workflow |
| `helpdesk/api/cmdb.py` | CI CRUD + impact analysis |
| `helpdesk/api/catalog.py` | Service Catalog browse + request submission |
| `helpdesk/api/analytics.py` | Metrics query, dashboard data, predictive scores |
| `helpdesk/api/webhooks.py` | Webhook CRUD + test delivery |
| `helpdesk/api/sandbox.py` | Sandbox provisioning (admin only) |
| `helpdesk/api/voice.py` | WebRTC signaling endpoints |

---

## New Frontend Pages (Phase 2–4)

| Route | Component | Phase |
|-------|-----------|-------|
| `/helpdesk/ai-copilot` | `pages/ai/AICopilotPanel.vue` | 2 |
| `/helpdesk/problems` | `pages/itil/ProblemList.vue` | 3 |
| `/helpdesk/problems/:id` | `pages/itil/ProblemDetail.vue` | 3 |
| `/helpdesk/changes` | `pages/itil/ChangeList.vue` | 3 |
| `/helpdesk/changes/:id` | `pages/itil/ChangeDetail.vue` | 3 |
| `/helpdesk/change-calendar` | `pages/itil/ChangeCalendar.vue` | 3 |
| `/helpdesk/cmdb` | `pages/itil/CMDBList.vue` | 3 |
| `/helpdesk/cmdb/:id` | `pages/itil/CIDetail.vue` | 3 |
| `/helpdesk/catalog` | `pages/catalog/ServiceCatalog.vue` | 3 |
| `/helpdesk/catalog/:id` | `pages/catalog/ServiceRequestForm.vue` | 3 |
| `/helpdesk/analytics` | `pages/analytics/AnalyticsDashboard.vue` | 2 |
| `/helpdesk/analytics/predictive` | `pages/analytics/PredictiveDashboard.vue` | 2 |
| `/helpdesk/settings/webhooks` | `pages/settings/Webhooks.vue` | 2 |
| `/helpdesk/settings/ai` | `pages/settings/AISettings.vue` | 2 |
| `/portal/catalog` | `pages/portal/PortalCatalog.vue` | 3 |

---

## Enforcement Guidelines (Phase 2–4 Additions)

All Phase 1 enforcement rules apply (see `_bmad-output/planning-artifacts/architecture.md`).
Additionally for Phase 2–4:

1. **LLM calls MUST go through `LLMProvider` abstraction** — no direct `openai.chat.completions` calls
2. **All AI features MUST be gated by `ai_enabled` in HD Settings**
3. **Every LLM call MUST be logged to `HD AI Usage Log`** with token counts and cost
4. **Prompt templates MUST be stored in `HD Prompt Template`** — no hardcoded prompt strings
5. **Analytics events MUST be enqueued** (`frappe.enqueue`) — never written synchronously in doc_events
6. **Webhook deliveries MUST be async** — never blocking HTTP calls in request handlers
7. **CMDB/Problem/Change are ITIL-gated** — hidden unless `itil_mode_enabled = 1` in HD Settings
8. **AI Agent tools MUST declare their action schema** in `tool_registry.py` before use
9. **PII redaction MUST run before embedding or LLM calls** via `ai/safety.py`
10. **All new indexes MUST be added via patches** in `helpdesk/patches/v2_phase2/`

---

## Architecture Readiness Assessment

**Overall Status:** READY FOR PHASED IMPLEMENTATION

**Phase 2 (Intelligence + Channels):**
- AI/LLM layer: Complete ADR. New infrastructure required: vector store (Meilisearch recommended).
- Channel extensions: Additive to Phase 1 adapter pattern. No refactoring needed.
- Analytics pipeline: Self-contained. No new infrastructure for Phase 2 baseline.

**Phase 3 (Advanced ITIL + Service Catalog + AI Agent):**
- Problem/Change/CMDB: New DocTypes only. ITIL mode gated.
- Service Catalog: Medium complexity. Frappe Workflow handles approvals.
- AI Agent: Highest complexity. Depends on Phase 2 AI/LLM layer being stable.

**Phase 4 (Innovation):**
- WebRTC: Requires TURN server deployment. Signaling reuses existing Socket.IO.
- Marketplace: Primarily a community/ecosystem effort; registry architecture is simple.
- Local LLM: Handled transparently by Ollama adapter in Phase 2 `LLMProvider` abstraction.

**Key Risks:**
1. Vector search at scale — Meilisearch adds operational complexity; mitigate by providing MariaDB fallback for small deployments.
2. AI Agent reliability — ReAct loop requires extensive testing and safety guardrails; build conservative CONFIDENCE_THRESHOLD defaults.
3. WebRTC NAT traversal — coturn deployment complexity; document standard configuration; offer hosted TURN as SaaS option.
4. CMDB data quality — CI relationships require discipline to maintain; provide import tools from ERPNext Assets.
