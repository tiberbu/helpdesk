# Frappe Helpdesk Feature Roadmap

**Version:** 1.0
**Date:** 2026-03-21
**Author:** BMAD Analyst Agent
**Status:** Approved for Development Planning

---

## Vision Statement

> **"Frappe Helpdesk will be the world's most powerful open-source support platform — combining enterprise-grade ITIL compliance, AI-native intelligence, and zero-marginal-agent-cost economics to deliver the customer experience of Zendesk/Intercom at a fraction of the cost, with no vendor lock-in, full data sovereignty, and deep ecosystem integration for Frappe/ERPNext users."**

We will own the intersection of three underserved markets:
1. **SMBs priced out of Zendesk/Intercom** — our no-per-agent pricing saves $33,000–$101,400/year at 50 agents
2. **Enterprises demanding data sovereignty** — self-hosted, open-source, GDPR-compliant by architecture
3. **Developer-first teams** — who customize, extend, and build on top rather than being constrained by SaaS limits

---

## Differentiators: What Makes This Tool Unique

### 1. Open Source Advantage
- Full source code access — customize anything, integrate everything
- No vendor lock-in — own your data and your deployment
- Community-driven development — extensions, plugins, translations
- Self-hosted = GDPR, HIPAA, SOC2 compliance on customer's own terms
- **No competitor can match this**: Zendesk, Freshdesk, Intercom are all closed SaaS

### 2. Frappe Ecosystem (ERPNext / CRM / HR Integration)
- **Native ERP context**: Agent sees customer's orders, invoices, assets, and support history in one screen — no integration needed
- **CRM integration**: Link tickets to leads, deals, opportunities — support as a revenue driver
- **HR integration**: Internal IT helpdesk with HR data (employee onboarding, asset assignment)
- **No competitor can match this**: No other helpdesk has native ERP integration

### 3. AI-Native from the Ground Up
- Designed for open-source LLMs (Llama, Mistral, Gemma) — runs on-premise, no per-resolution fees
- While Zendesk charges $1.00/resolution, Frappe's AI Agent costs $0 per resolution when self-hosted
- RAG pipeline using customer's own knowledge base data — privacy preserved
- AI QA, sentiment analysis, intent routing — all configurable and extensible

### 4. Developer-Friendly Extensibility
- Frappe Framework's DocType system for rapid data model extension
- Auto-generated REST APIs for every entity
- Background jobs via Redis Queue
- Custom scripts (server + client) without forking
- Built-in webhook system
- Plugin/App marketplace architecture

---

## Phased Roadmap

---

### Phase 1: Foundation (Months 1–6)
*Core ITIL practices, essential agent experience, multi-channel entry*

**Goal:** Make Frappe Helpdesk competitive with Freshdesk/Zoho Desk for SMB use cases. Close the most embarrassing feature gaps that prevent adoption.

---

#### P0: Immediate Gaps (Month 1–2)

> **Updated 2026-03-23**: 3 of 4 P0 items implemented by upstream. Only Internal Notes remains.

| # | Feature | Description | ITIL Practice | Competitive Benchmark | Effort | Business Value | Dependencies | Status |
|---|---------|-------------|---------------|-----------------------|--------|----------------|--------------|--------|
| 1.1 | ~~**Canned Responses / Macros**~~ | Pre-written reply templates with dynamic variables. Team-based sharing. Autocomplete integration. | Service Request Mgmt | All 15 competitors | S | High | None | ✅ **IMPLEMENTED** — Renamed to "Saved Replies" (HD Saved Reply DocType) with HD Saved Reply Team for sharing |
| 1.2 | **Internal Notes on Tickets** | Private notes visible only to agents. @mention teammates for internal collaboration. Distinguish visually from customer-facing replies. | Incident Management | Zendesk, Front, Help Scout, Freshdesk | S | High | None | ❌ Still needed |
| 1.3 | ~~**Collision Detection**~~ | Real-time indicator when another agent is viewing or replying to a ticket. Typing indicators. | Incident Management | Help Scout, Freshdesk, Hiver, Zoho | S | High | Socket.IO | ✅ **IMPLEMENTED** — `realtime/handlers.js` with Socket.IO: `view_ticket`, `stop_view_ticket`, `helpdesk_ticket_typing`, `helpdesk_ticket_typing_stopped` events. Frontend: `desk/src/composables/realtime.ts` |
| 1.4 | ~~**Agent Keyboard Shortcuts**~~ | Full keyboard navigation: `R` to reply, `C` for comment, `T` for type, `P` for priority, `A` to assign, `S` for status, `Ctrl+K` command palette. | Service Request Mgmt | Zendesk, Help Scout, Front | S | Medium | None | ✅ **IMPLEMENTED** — `desk/src/composables/shortcuts.ts` + `ShortcutsModal.vue` with Ctrl+/ help |

---

#### P1: Core Quality Features (Month 2–4)

| # | Feature | Description | ITIL Practice | Competitive Benchmark | Effort | Business Value | Dependencies |
|---|---------|-------------|---------------|-----------------------|--------|----------------|--------------|
| 1.5 | **CSAT Surveys** | Post-resolution satisfaction surveys sent automatically (email/portal). 1–5 star rating + optional comment. Dashboard showing CSAT scores by agent, team, period. | Continual Improvement | All 15 competitors | M | High | Email integration |
| 1.6 | **Advanced Workflow Automation** | Visual if-then-else rule builder. Triggers: ticket created/updated/SLA breached. Conditions: channel, priority, tag, customer segment. Actions: assign, tag, notify, send reply, set field, escalate. | Incident/Change Mgmt | Zendesk Triggers, Zoho Blueprint, ServiceNow Flow | L | High | None |
| 1.7 | **Custom Report Builder** | Drag-and-drop report builder for agents/managers. Filters, group-by, custom metrics, scheduled delivery via email. Charts: bar, line, pie, table. Export to CSV/Excel. | Continual Improvement | Zendesk Explore, ServiceNow PA, HubSpot | L | High | None |
| 1.8 | **Enhanced SLA with Business Hours** | Business-hours-only SLA calculation. Holiday calendar support. Multi-timezone per team. SLA breach alerts before breach occurs (30/15/5 min warnings). | Service Level Mgmt | Zendesk, ServiceNow, Jira SM | M | High | None |

---

#### P1: Multi-Channel Entry (Month 3–6)

| # | Feature | Description | ITIL Practice | Competitive Benchmark | Effort | Business Value | Dependencies |
|---|---------|-------------|---------------|-----------------------|--------|----------------|--------------|
| 1.9 | **Live Chat Widget** | Embeddable JavaScript widget for customer-facing websites/apps. Real-time messaging with typing indicators. Agent availability status. Chat-to-ticket conversion. Customizable branding. | Service Request Mgmt | All major competitors | M | High | WebSocket/Socket.IO |
| 1.10 | **Multi-Brand Support** | Multiple branded portals from one Frappe Helpdesk instance. Separate domains, email addresses, knowledge bases, and agent teams per brand. | Service Catalog Mgmt | Zendesk, Zoho, Freshdesk | M | Medium | None |
| 1.11 | **Time Tracking** | Per-ticket time logging for agents. Billable/non-billable time. Time reports by agent, ticket, period. Integration with ERPNext Projects for billing. | Service Request Mgmt | Freshdesk, Zoho Desk, Jira SM | S | Medium | None |

---

#### Phase 1 ITIL Alignment Summary

> **Updated 2026-03-23**: Several Phase 1 items now implemented by upstream

| ITIL Practice | Phase 1 Coverage | Implementation Status |
|---------------|-----------------|---------------------|
| Incident Management | Collision detection ✅, internal notes ❌, workflow automation ❌ | Collision detection + typing indicators DONE |
| Service Request Management | Canned responses ✅, live chat ❌, macros ✅ | Saved Replies DONE |
| Service Level Management | Enhanced SLA ❌, business hours ✅ (existing), breach alerts ❌ | Business hours already existed |
| Continual Improvement | CSAT surveys ❌, custom reports ❌ | Not yet implemented |
| Knowledge Management | (existing KB + AI search in Phase 2) | — |
| **Additional (from upstream)** | Agent dashboard ✅, keyboard shortcuts ✅, command palette ✅, i18n ✅, telemetry ✅ | All DONE |

---

### Phase 2: Intelligence (Months 7–14)
*AI-powered features, automation, predictive analytics, WhatsApp/messaging*

**Goal:** Leapfrog Freshdesk/Zoho Desk into Zendesk/Intercom territory with AI capabilities that reduce agent workload by 30–50%.

---

#### P2: AI Copilot (Month 7–9)

| # | Feature | Description | ITIL Practice | Competitive Benchmark | Effort | Business Value | Dependencies |
|---|---------|-------------|---------------|-----------------------|--------|----------------|--------------|
| 2.1 | **AI Copilot — Reply Draft** | AI generates a draft reply based on ticket content + knowledge base. Agent reviews, edits, sends. Supports multiple LLMs: OpenAI, Anthropic, local Llama/Mistral. | Incident Management | Intercom Copilot, Zendesk Copilot, Front | L | High | LLM integration layer |
| 2.2 | **AI Copilot — Summarization** | One-click conversation summary for long threads. Captures: issue, actions taken, current status, next steps. Enables fast handoffs between agents or teams. | Incident Management | Intercom, Zendesk, Help Scout, Hiver | M | High | LLM integration |
| 2.3 | **AI Copilot — KB Article Surfacing** | While agent types a reply, AI suggests relevant knowledge base articles in the sidebar. Embedding-based semantic search (not just keyword match). | Knowledge Management | Intercom, Zendesk, Front | M | High | Vector search/embeddings |
| 2.4 | **AI Copilot — Tone & Translation** | Rewrite agent's draft in different tones (formal, friendly, empathetic). Real-time translation for multilingual support (agent writes in English, customer receives in Spanish). | Service Request Mgmt | Front, Dixa, Zoho Zia | M | Medium | LLM integration |

---

#### P2: AI Triage (Month 8–10)

| # | Feature | Description | ITIL Practice | Competitive Benchmark | Effort | Business Value | Dependencies |
|---|---------|-------------|---------------|-----------------------|--------|----------------|--------------|
| 2.5 | **Intelligent Triage** | Auto-classify tickets by: intent (billing, technical, shipping), sentiment (angry, neutral, happy), language, priority. Route to correct team/agent automatically. | Incident Management | Zendesk AI, Freshdesk Freddy, Zoho Zia | M | High | LLM/ML integration |
| 2.6 | **Sentiment Detection** | Real-time sentiment scoring on every incoming message. Alert agents when customer frustration escalates. Priority boost for angry customers. Dashboard: escalating tickets. | Incident Management | Zoho Zia, Hiver, Dixa, Kustomer | M | Medium | NLP model |
| 2.7 | **Smart Routing** | Skills-based routing: match tickets to agents by language, expertise, product area. Load-balanced assignment respecting agent capacity. VIP customer fast-track routing. | Service Request Mgmt | Zendesk, Dixa, Freshdesk | M | High | None |

---

#### P2: Messaging Channels (Month 9–12)

| # | Feature | Description | ITIL Practice | Competitive Benchmark | Effort | Business Value | Dependencies |
|---|---------|-------------|---------------|-----------------------|--------|----------------|--------------|
| 2.8 | **WhatsApp Integration** | Two-way WhatsApp Business API integration. Incoming messages create tickets. Agents reply from Frappe UI. Message templates for outbound notifications. | Service Request Mgmt | Zendesk, Freshdesk, Intercom, Zoho | M | High | WhatsApp Business API |
| 2.9 | **SMS Channel** | Two-way SMS via Twilio/MessageBird. Ticket creation from SMS. Reply via SMS. Opt-in/opt-out management. | Service Request Mgmt | Zendesk, Freshdesk, Front, Kustomer | M | Medium | SMS provider API |
| 2.10 | **Social Media Channels** | Facebook Messenger, Instagram DM, X/Twitter DM as support channels. Social post monitoring for brand mentions. Convert social mentions to tickets. | Service Request Mgmt | Zendesk, Zoho, Freshdesk, Gorgias | M | Medium | Meta API, X API |

---

#### P2: Analytics & Predictive (Month 11–14)

| # | Feature | Description | ITIL Practice | Competitive Benchmark | Effort | Business Value | Dependencies |
|---|---------|-------------|---------------|-----------------------|--------|----------------|--------------|
| 2.11 | **Predictive Analytics** | ML models for: ticket volume forecasting (next 7/30 days), SLA breach risk scoring, agent capacity planning, topic trend detection. | Continual Improvement | ServiceNow Performance Analytics, Zendesk Explore | L | High | ML pipeline, Phase 1 report builder |
| 2.12 | **Knowledge Base v2 — AI Search** | Semantic search powered by embeddings. Generative answers: "Based on our KB, here's the answer: [...]". AI identifies KB gaps from unanswered tickets. AI drafts new KB articles from resolved ticket patterns. | Knowledge Management | Zendesk Guide, Intercom, Help Scout | L | High | LLM + vector search |
| 2.13 | **AI Quality Scoring (QA)** | Auto-score every conversation against configurable criteria (tone, resolution quality, policy adherence, empathy). Identify coaching opportunities. 100% coverage vs. 2% manual sampling. | Continual Improvement | Front Smart QA, Dixa Discover, Zendesk QA (Klaus) | L | High | LLM integration |

---

#### Phase 2 ITIL Alignment Summary

| ITIL Practice | Phase 2 Coverage |
|---------------|-----------------|
| Incident Management | AI triage, sentiment detection, copilot drafting |
| Knowledge Management | AI search, KB gap analysis, auto-article drafting |
| Continual Improvement | Predictive analytics, AI QA, CSAT analytics |
| Service Request Management | WhatsApp, SMS, social channels, smart routing |
| Service Level Management | SLA breach prediction, capacity planning |

---

### Phase 3: Excellence (Months 15–24)
*Advanced ITIL, self-service excellence, ecosystem, autonomous AI*

**Goal:** Compete with ServiceNow for ITSM workloads while maintaining the simplicity that makes us better than Zendesk for SMBs.

---

#### P3: Autonomous AI Agent (Month 15–18)

| # | Feature | Description | ITIL Practice | Competitive Benchmark | Effort | Business Value | Dependencies |
|---|---------|-------------|---------------|-----------------------|--------|----------------|--------------|
| 3.1 | **AI Agent — Autonomous Resolution** | Fully autonomous AI handles tickets end-to-end: understands query, retrieves knowledge, performs actions (lookup order, reset password, process refund), responds, and closes ticket. Target: 40–60% deflection rate. | Service Request Mgmt | Intercom Fin (66%), Zendesk AI, Dixa Mim (80%) | XL | High | Phase 2 AI infrastructure, action integrations |
| 3.2 | **AI Agent — ERPNext Actions** | AI Agent can: look up order status from ERPNext, check invoice status, create purchase requests, submit IT asset requests, query HR policies. Native advantage competitors cannot replicate. | Service Request Mgmt | No direct competitor | XL | High | ERPNext API integration, AI Agent |
| 3.3 | **AI Agent — Escalation Intelligence** | AI decides when to escalate to human agent. Hands off with full context summary. Human agent can see AI conversation, what was tried, and why it escalated. Continuous learning from escalation patterns. | Incident Management | Intercom Fin, Zendesk AI | L | High | AI Agent (3.1) |

---

#### P3: Advanced ITIL (Month 16–20)

| # | Feature | Description | ITIL Practice | Competitive Benchmark | Effort | Business Value | Dependencies |
|---|---------|-------------|---------------|-----------------------|--------|----------------|--------------|
| 3.4 | **Problem Management** | Link multiple related incidents to a problem record. Root cause analysis tracking. Workaround documentation. Known error database (KEDB). Problem resolution drives KB article creation. | Problem Management | ServiceNow, Jira SM | L | High | Existing incident management |
| 3.5 | **Change Management** | RFC (Request for Change) workflow with CAB approval. Change calendar to prevent conflicting deployments. Change success/failure tracking. Link changes to incidents they resolve. | Change Enablement | ServiceNow, Jira SM | L | High | Workflow automation |
| 3.6 | **CMDB (Configuration Management)** | Track IT assets, services, and their relationships. Configuration Items (CIs): servers, applications, databases, network devices. Impact analysis: "Which services are affected by this CI failure?" | IT Asset Management | ServiceNow (industry leader), Jira SM | XL | High | ERPNext Asset Management integration |

---

#### P3: Self-Service Excellence (Month 17–21)

| # | Feature | Description | ITIL Practice | Competitive Benchmark | Effort | Business Value | Dependencies |
|---|---------|-------------|---------------|-----------------------|--------|----------------|--------------|
| 3.7 | **Service Catalog** | Structured catalog of available services with request forms, approval workflows, fulfillment steps, and SLA targets. Employee self-service portal (IT requests, HR requests). | Service Catalog Mgmt | ServiceNow, Jira SM, HubSpot | L | High | Workflow automation |
| 3.8 | **Customer Portal v2** | Redesigned portal: ticket history, live chat, knowledge base, service catalog, community forum integration. Single-sign-on (SSO) with ERPNext Customer portal. Ticket status tracking with real-time updates. | Service Request Mgmt | Zendesk, ServiceNow, Jira SM | M | High | Live chat, service catalog |
| 3.9 | **Community Forums** | Integrated community Q&A platform. Voting, accepted answers, reputation. AI suggests forum answers from KB. Top community answers promoted to KB articles. | Knowledge Management | Zendesk Community, Freshdesk Forums, Khoros | L | Medium | KB v2, AI integration |
| 3.10 | **Proactive Messaging** | Behavior-triggered outreach (website events, app events). In-app announcements, product tours, onboarding checklists. "We noticed you've been struggling with X — here's a guide." | Continual Improvement | Intercom (market leader), HubSpot | L | Medium | Live chat widget, event tracking |

---

#### P3: Gamification & Agent Experience (Month 19–22)

| # | Feature | Description | ITIL Practice | Competitive Benchmark | Effort | Business Value | Dependencies |
|---|---------|-------------|---------------|-----------------------|--------|----------------|--------------|
| 3.11 | **Gamification** | Points for ticket resolution, CSAT scores, KB articles written. Badges and achievements. Team leaderboards. Manager configurable point system. Reward redemption. Agent morale driver — unique open-source differentiator. | Continual Improvement | Freshdesk Arcade (only leader) | M | Medium | CSAT |
| 3.12 | **Agent Workspace v2** | Redesigned agent UI: split-view ticket list + detail, collapsible sidebar, pinnable customer info, recently visited tickets, keyboard-driven navigation throughout. | Service Request Mgmt | Front, Intercom, Zendesk | M | High | All Phase 1 agent features |
| 3.13 | **Workforce Management (WFM)** | Agent scheduling, shift management, break tracking, capacity forecasting. Integrate with predictive analytics for demand-based scheduling. | Workforce Planning | Zendesk (Tymeshift), Genesys | XL | Medium | Predictive analytics |

---

#### Phase 3 ITIL Alignment Summary

| ITIL Practice | Phase 3 Coverage |
|---------------|-----------------|
| Problem Management | Full RCA workflow, KEDB |
| Change Enablement | RFC, CAB, change calendar |
| IT Asset Management | CMDB, CI tracking, impact analysis |
| Service Catalog Management | Service catalog, approval workflows |
| Knowledge Management | Community forums, proactive KB |
| Continual Improvement | Gamification, WFM |

---

### Phase 4: Innovation (Months 25–36)
*Unique differentiators, market-leading features, platform play*

**Goal:** Establish category leadership. Build features that NO competitor (open or closed source) offers. Own the open-source AI helpdesk category.

---

| # | Feature | Description | ITIL Practice | Competitive Benchmark | Effort | Business Value | Dependencies |
|---|---------|-------------|---------------|-----------------------|--------|----------------|--------------|
| 4.1 | **Local LLM Marketplace** | Curated collection of pre-configured open-source LLMs (Llama 3, Mistral, Phi-3, Gemma) for AI Agent + Copilot. One-click model deployment. Benchmarks: accuracy vs. cost per resolution. No competitor offers on-prem AI at this level. | Service Request Mgmt | No direct competitor | XL | High | AI Agent, AI Copilot |
| 4.2 | **Frappe App Marketplace** | Community app store for Frappe Helpdesk extensions. Categories: channels, integrations, AI models, analytics, workflows. Revenue share model. Build ecosystem moat vs. Zendesk's 1500+ app marketplace. | Service Catalog Mgmt | Zendesk Marketplace (1500+), Freshdesk Marketplace | XL | High | All prior phases |
| 4.3 | **Voice/Phone (WebRTC)** | Native WebRTC voice calls from agent browser. Customer click-to-call from portal/widget. Call recording, transcription, sentiment analysis. IVR for call routing. No Twilio dependency — WebRTC-native. | Service Request Mgmt | Zendesk Talk, Dixa, Gladly | XL | High | Live chat infrastructure |
| 4.4 | **Video Support** | One-click video call with screen sharing from ticket context. No plugin install for customer. Automatic ticket update with video session notes. | Incident Management | Kustomer, Gladly (partial) | L | Medium | Voice/WebRTC |
| 4.5 | **Revenue Intelligence** | Track revenue impact of support: upsells during tickets, prevented churn by ticket topic, LTV change after support interaction. ERPNext integration for real purchase data — no CRM required. | Continual Improvement | Gorgias (ecommerce only), Gladly | L | High | ERPNext integration, analytics |
| 4.6 | **AI Agent Fine-Tuning Studio** | Admin UI for training/fine-tuning the local AI Agent on company-specific data. Upload docs, set tone, define allowed actions, test responses. No ML expertise required. Version control for AI behavior. | Knowledge Management | No direct competitor | XL | High | Local LLM marketplace |
| 4.7 | **ERPNext Deep Integration Suite** | Pre-built integration packs: Manufacturing (machine support tickets), Healthcare (patient support), Education (student helpdesk), Retail (order management). Industry-specific ticket templates and workflows. | Service Catalog Mgmt | No direct competitor | L | High | ERPNext, service catalog |
| 4.8 | **Federated Helpdesk** | Connect multiple Frappe Helpdesk instances (subsidiaries, franchises, partners) into one unified network. Cross-instance ticket routing, shared KB, unified reporting. No SaaS tool supports self-hosted federation. | IT Service Continuity | No direct competitor | XL | Medium | All prior phases |

---

## Priority Summary Matrix

| Phase | Timeline | Investment | Primary Value |
|-------|----------|-----------|---------------|
| Phase 1: Foundation | Months 1–6 | 2–3 devs | Competitive viability — stop losing to Freshdesk |
| Phase 2: Intelligence | Months 7–14 | 3–4 devs | AI differentiation — compete with Zendesk |
| Phase 3: Excellence | Months 15–24 | 4–5 devs | ITIL leadership + self-service dominance |
| Phase 4: Innovation | Months 25–36 | 5–6 devs | Category creation — own open-source AI helpdesk |

---

## Competitive Positioning by Phase

| Competitor | Phase 1 Position | Phase 2 Position | Phase 3 Position | Phase 4 Position |
|-----------|-----------------|-----------------|-----------------|-----------------|
| Freshdesk | Near parity | Exceeds | Exceeds | Far exceeds |
| Zoho Desk | Near parity | Exceeds | Exceeds | Far exceeds |
| Help Scout | Parity | Exceeds | Far exceeds | Far exceeds |
| Zendesk | Still behind | Near parity | Parity | Exceeds |
| Intercom | Still behind | Near parity | Parity | Exceeds |
| ServiceNow | Still behind | Still behind | Near parity | Parity |

---

*This roadmap is a living document. Feature priorities should be reviewed quarterly against adoption data, customer feedback, and competitive landscape changes.*
