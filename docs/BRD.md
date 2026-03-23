# Business Requirements Document (BRD)
## Frappe Helpdesk — Next-Generation Support Platform

**Document ID:** BRD-HD-2026-001
**Version:** 1.0
**Date:** 2026-03-21
**Author:** BMAD Analyst Agent
**Status:** Draft — Pending Sign-off

---

## 1. Executive Summary

Frappe Helpdesk is an open-source customer support and IT service management platform built on the Frappe Framework. It currently serves as a basic ticketing system for teams already invested in the Frappe/ERPNext ecosystem. However, it lacks the features that define modern, world-class support tools, particularly in AI assistance, omnichannel support, real-time collaboration, and advanced analytics.

This Business Requirements Document defines the strategic transformation of Frappe Helpdesk from a basic ticketing tool into a comprehensive, AI-native support platform that can compete with Zendesk, Freshdesk, Intercom, and ServiceNow — while maintaining its core advantages of open-source freedom, zero per-agent pricing, and deep Frappe ecosystem integration.

The transformation is planned across four phases spanning 36 months, with the first phase deliverable within 6 months. Total investment covers 2–6 engineering resources across phases. The projected outcome is a market-leading open-source helpdesk capable of serving SMBs, enterprises, and developer-oriented organizations globally.

---

## 2. Problem Statement

### 2.1 Current State

> **Updated 2026-03-23** — Post upstream sync with 600+ commits from frappe/helpdesk develop

Frappe Helpdesk is a functional support system that has recently received significant improvements. Based on codebase analysis (41+ DocTypes, API modules, frontend components), the platform handles:
- Basic ticket lifecycle (create, assign, resolve)
- SLA tracking with business hours, holiday calendars, and breach detection
- Knowledge base with categories, search (with synonyms/stopwords), and feedback
- Customer portal for ticket submission and tracking
- Assignment rules (round-robin, manual)
- Email channel integration via ERPNext Email Accounts
- Role-based access (Agent, Customer, Admin)
- ✅ **NEW: Saved replies (macros)** — Pre-written templates with variables and team-based sharing (HD Saved Reply)
- ✅ **NEW: Collision detection** — Real-time Socket.IO viewer tracking and typing indicators
- ✅ **NEW: Agent landing page** — Customizable dashboard with pending tickets, SLA metrics, feedback, performance trends
- ✅ **NEW: Keyboard shortcuts** — Full navigation (T, P, A, S, R, C, Ctrl+K) with shortcuts modal
- ✅ **NEW: Command palette** — Quick-access navigation via Ctrl+K
- ✅ **NEW: i18n** — 25+ language translations with runtime translation plugin
- ✅ **NEW: Telemetry** — PostHog-based analytics for usage tracking
- ✅ **NEW: Comment reactions** — Emoji reactions on ticket comments

### 2.2 The Gap (Updated)

The helpdesk software market is valued at $14–17 billion (2025) and growing at 10–12% CAGR. The defining differentiator of 2025–2026 is **autonomous AI agents** that resolve 40–80% of customer queries without human intervention. Every major competitor now offers this. Frappe Helpdesk has none.

The platform was previously missing 17 critical features. **The upstream sync resolved 3 of the most critical gaps** (canned responses, collision detection, agent productivity tools) and partially addressed reporting. **14 critical feature gaps remain:**

1. **No AI Agent** — Intercom Fin achieves 66% autonomous resolution rate. Frappe Helpdesk routes 100% of queries to human agents.
2. **No AI Copilot** — Agents receive zero AI assistance for drafting, KB surfacing, or summarization.
3. ~~No canned responses/macros~~ — ✅ **RESOLVED** — Saved Replies with team sharing and autocomplete
4. ~~No collision detection~~ — ✅ **RESOLVED** — Real-time Socket.IO viewer tracking + typing indicators
5. **No live chat** — Only email is supported; real-time customer assistance is unavailable.
6. **No CSAT surveys** — Customer satisfaction cannot be measured post-resolution (feedback options exist but no formal CSAT).
7. **Limited reporting** — Agent dashboard provides basic metrics, but no custom report builder exists.
8. **No WhatsApp/SMS/Social** — 3 of the 5 fastest-growing support channels are entirely absent.

### 2.3 Business Impact of Remaining Gaps

- **Adoption barriers**: Significantly reduced — canned responses, collision detection, and keyboard shortcuts now present. Remaining blockers: no CSAT, no live chat, no custom reporting
- **Agent productivity loss**: Estimated 40–60% of agent time spent on tasks AI could handle (drafting, lookups, routing). Saved replies partially address this.
- **Competitive disadvantage**: Gap narrowing — now competitive on agent experience basics. Still behind on AI, omnichannel, and advanced analytics.
- **Ecosystem waste**: ERPNext users still switch to Zendesk/Freshdesk for missing features, paying $50–$150/agent/month unnecessarily

---

## 3. Business Objectives

| ID | Objective | KPI | Target (12 months) | Target (36 months) |
|----|-----------|-----|-------------------|-------------------|
| BO-1 | Eliminate critical feature gaps blocking adoption | Feature parity score vs. Freshdesk | 80% parity | 95% parity |
| BO-2 | Increase agent productivity through AI assistance | Tickets handled per agent per day | +30% | +60% |
| BO-3 | Achieve measurable customer satisfaction tracking | CSAT score collection rate | 80% of resolved tickets | 90%+ |
| BO-4 | Expand supported channels beyond email | Active channel count | 3 (email, chat, WhatsApp) | 7+ |
| BO-5 | Enable AI-powered ticket deflection | % tickets auto-resolved by AI | 20% (Phase 2 copilot) | 50%+ (Phase 3 AI Agent) |
| BO-6 | Increase Frappe/ERPNext customer retention | Churn to external helpdesks | -50% | -80% |
| BO-7 | Establish open-source ITSM leadership | ITIL practice coverage | 4 practices (Phase 1) | 8 practices (Phase 3) |
| BO-8 | Build developer ecosystem | Community extensions in marketplace | N/A | 50+ apps |

---

## 4. Stakeholders

| Stakeholder | Role | Interest | Influence |
|-------------|------|---------|-----------|
| **Frappe Technologies** | Platform owner and primary developer | Commercial viability, community adoption, technical excellence | High |
| **Frappe Community** | Open-source contributors | Feature utility, code quality, extensibility | High |
| **ERPNext/Frappe Customers** | Primary end-users | Cost savings, feature completeness, ERP integration | High |
| **Support Team Managers** | Decision-makers for tool selection | Reporting, agent management, SLA compliance | High |
| **Support Agents** | Daily users | Speed, AI assistance, mobile access, ease of use | High |
| **IT Administrators** | Deployment and maintenance | Self-hosting, security, scalability, customization | Medium |
| **End Customers** | Recipients of support | Response speed, channel choice, self-service quality | Medium |
| **Competitive Market** | External benchmark | Feature benchmarking, pricing pressure | Medium |
| **LLM/AI Providers** | Technology partners | Integration standards, cost structures | Low |

---

## 5. Functional Requirements

> **Updated 2026-03-23** — Requirements marked ✅ have been implemented by upstream. Remaining requirements retain their priority codes.

Requirements are grouped by ITIL practice. Priority codes: **P0** = immediate, **P1** = Phase 1, **P2** = Phase 2, **P3** = Phase 3, **P4** = Phase 4.

---

### 5.1 Incident Management

| ID | Requirement | Priority | Acceptance Criteria | Status |
|----|-------------|---------|---------------------|--------|
| FR-IM-01 | System SHALL provide internal agent notes on tickets, visually distinct from customer-facing replies | P0 | Notes are visible only to agents; customers cannot see internal notes; @mentions notify teammates | ❌ Not yet |
| FR-IM-02 | System SHALL detect when multiple agents are viewing or replying to the same ticket (collision detection) | ~~P0~~ | Visual indicator shows other agents viewing; typing indicators show "Agent X is typing" | ✅ **IMPLEMENTED** — `realtime/handlers.js` + `composables/realtime.ts` |
| FR-IM-03 | System SHALL support advanced workflow automation with visual if-then-else rule builder | P1 | Rules can be triggered by ticket events; conditions can reference any ticket field; 10+ action types available |
| FR-IM-04 | System SHALL provide AI-powered intent classification and sentiment detection on every incoming message | P2 | Intent detected within 5 seconds of ticket creation; sentiment score (1–5) displayed on ticket; configurable routing rules based on sentiment |
| FR-IM-05 | System SHALL provide an AI Copilot that drafts reply suggestions for agents | P2 | Draft generated in < 3 seconds; agent can edit before sending; supports 3+ LLM providers; works with local Llama/Mistral models |
| FR-IM-06 | System SHALL provide an AI Copilot that summarizes long ticket threads | P2 | Summary generated in < 5 seconds; covers: issue, actions taken, current status, next steps |
| FR-IM-07 | System SHALL support Problem Management with RCA tracking and KEDB | P3 | Incidents can be linked to Problem records; workarounds documented; KEDB searchable |
| FR-IM-08 | System SHALL provide an autonomous AI Agent that resolves tickets without human intervention | P3 | AI Agent handles minimum 5 action types (FAQ, order lookup, password reset, etc.); escalates with context summary; target 40%+ deflection |

---

### 5.2 Service Request Management

| ID | Requirement | Priority | Acceptance Criteria |
|----|-------------|---------|---------------------|
| FR-SR-01 | System SHALL provide canned responses (macros) with dynamic variable substitution | ~~P0~~ | Agents can create, share, and search templates; team-based sharing; autocomplete integration | ✅ **IMPLEMENTED** — HD Saved Reply + HD Saved Reply Team DocTypes |
| FR-SR-02 | System SHALL support full keyboard navigation for agent workflow | ~~P0~~ | All primary actions via shortcut (T, P, A, S, R, C); Ctrl+K command palette; Ctrl+/ shortcut help | ✅ **IMPLEMENTED** — `composables/shortcuts.ts` + `ShortcutsModal.vue` + `CP.vue` |
| FR-SR-03 | System SHALL provide a real-time live chat widget embeddable on customer websites | P1 | Widget installs via single JavaScript snippet; supports customizable branding; typing indicators; chat-to-ticket conversion; agent availability status |
| FR-SR-04 | System SHALL support multi-brand operation from a single instance | P1 | Multiple brands with separate portals, email addresses, KB, and agent teams; configurable per brand |
| FR-SR-05 | System SHALL integrate WhatsApp Business API as a support channel | P2 | Inbound WhatsApp messages create tickets; agents reply from Frappe UI; outbound templates supported; read receipts visible |
| FR-SR-06 | System SHALL integrate SMS (Twilio or equivalent) as a support channel | P2 | Two-way SMS; opt-in/opt-out management; SMS reply from agent workspace |
| FR-SR-07 | System SHALL integrate Facebook Messenger, Instagram DM, and X/Twitter DM as support channels | P2 | Messages from each channel create tickets; agents reply without leaving Frappe Helpdesk |
| FR-SR-08 | System SHALL provide a Service Catalog with structured request forms and approval workflows | P3 | Catalog items with forms, approvers, fulfillment steps, SLA targets; self-service portal for employees |
| FR-SR-09 | System SHALL provide skills-based, language-based, and VIP routing for ticket assignment | P2 | Agent skills configured in profile; tickets matched to skills; VIP customer flag for priority routing |
| FR-SR-10 | System SHALL support native WebRTC voice calls between agents and customers | P4 | Customer calls from portal; agent receives in browser; recording and transcription; IVR for routing |

---

### 5.3 Service Level Management

| ID | Requirement | Priority | Acceptance Criteria |
|----|-------------|---------|---------------------|
| FR-SL-01 | System SHALL support business-hours-only SLA calculation with holiday calendars | P1 | Business hours configurable per team; holiday calendar per region; SLA pauses outside business hours; multi-timezone support |
| FR-SL-02 | System SHALL send proactive SLA breach alerts before breach occurs | P1 | Configurable warning thresholds (30/15/5 minutes before breach); alert to agent, manager, and optionally customer |
| FR-SL-03 | System SHALL provide SLA compliance dashboards with drill-down capability | P1 | Real-time SLA compliance %; drill-down by agent, team, ticket type; trend over time |
| FR-SL-04 | System SHALL predict SLA breach risk using ML models | P2 | Risk score per ticket updated every 15 minutes; high-risk tickets surfaced in agent dashboard |

---

### 5.4 Knowledge Management

| ID | Requirement | Priority | Acceptance Criteria |
|----|-------------|---------|---------------------|
| FR-KM-01 | System SHALL provide AI-powered semantic search for knowledge base articles | P2 | Search returns semantically relevant results, not just keyword matches; embedding-based search backend |
| FR-KM-02 | System SHALL surface relevant KB articles in real-time as agents type replies | P2 | Article suggestions appear in sidebar within 2 seconds of typing; relevance score displayed |
| FR-KM-03 | System SHALL identify KB gaps from patterns in unresolved/escalated tickets | P2 | Weekly report of top 20 topics without KB coverage; AI drafts article stubs from ticket content |
| FR-KM-04 | System SHALL support AI-generated answers from KB content (RAG pipeline) | P2 | AI generates direct answers citing source articles; confidence score displayed; fallback to article list if confidence < threshold |
| FR-KM-05 | System SHALL provide community forums integrated with the knowledge base | P3 | Q&A voting, accepted answers, AI suggestion from KB; top answers promoted to KB |
| FR-KM-06 | System SHALL auto-generate KB article drafts from patterns in resolved tickets | P3 | AI identifies top 10 repeat questions monthly; drafts articles with agent review workflow |

---

### 5.5 Continual Improvement

| ID | Requirement | Priority | Acceptance Criteria |
|----|-------------|---------|---------------------|
| FR-CI-01 | System SHALL send CSAT surveys automatically after ticket resolution | P1 | Email survey sent within 24 hours of resolution; 1–5 star rating + optional comment; unsubscribe option; surveys respect SLA policies |
| FR-CI-02 | System SHALL provide a custom report builder for agents and managers | P1 | Drag-and-drop report builder; filters, group-by, custom metrics; scheduled email delivery; CSV/Excel export; charts: bar, line, pie, table |
| FR-CI-03 | System SHALL track agent time per ticket | P1 | Manual start/stop timer; billable/non-billable classification; time report by agent/ticket/period; ERPNext Projects integration |
| FR-CI-04 | System SHALL provide predictive analytics for ticket volume forecasting | P2 | 7-day and 30-day volume forecast; agent capacity recommendations; seasonal trend detection |
| FR-CI-05 | System SHALL auto-score 100% of conversations for quality (AI QA) | P2 | Configurable scoring criteria; score per conversation; coaching insights; manager QA dashboard; calibration against manual scores |
| FR-CI-06 | System SHALL provide gamification for agent motivation | P3 | Points for resolution, CSAT, KB authoring; badges; team leaderboards; manager-configurable reward rules |

---

### 5.6 Change Enablement

| ID | Requirement | Priority | Acceptance Criteria |
|----|-------------|---------|---------------------|
| FR-CE-01 | System SHALL support RFC (Request for Change) workflow with CAB approval | P3 | Change request form; multi-level approval; CAB meeting scheduling; change calendar with conflict detection |
| FR-CE-02 | System SHALL link changes to incidents they caused or resolved | P3 | Bi-directional links: change → incident, incident → change; impact analysis visualization |
| FR-CE-03 | System SHALL provide change success/failure tracking | P3 | Post-implementation review workflow; success rate metrics; lessons learned documentation |

---

### 5.7 IT Asset Management / CMDB

| ID | Requirement | Priority | Acceptance Criteria |
|----|-------------|---------|---------------------|
| FR-AM-01 | System SHALL provide a CMDB for tracking configuration items and their relationships | P3 | CI types: server, application, database, network device; relationship mapping; visual dependency graph |
| FR-AM-02 | System SHALL perform impact analysis when a CI is affected | P3 | "Which services are affected if this server goes down?" answered automatically from CI relationships |
| FR-AM-03 | System SHALL integrate with ERPNext Asset Management as the CMDB source of truth | P3 | ERPNext assets sync to CMDB; agent workspace shows customer-owned assets in ticket context |

---

## 6. Non-Functional Requirements

### 6.1 Performance

| ID | Requirement | Target |
|----|-------------|--------|
| NFR-P-01 | Page load time (agent workspace) | < 2 seconds on standard hardware |
| NFR-P-02 | Ticket search response time | < 500ms for full-text search |
| NFR-P-03 | Live chat message delivery latency | < 200ms end-to-end |
| NFR-P-04 | AI Copilot reply draft generation | < 3 seconds for 95th percentile |
| NFR-P-05 | AI Agent autonomous response | < 10 seconds for 95th percentile |
| NFR-P-06 | System throughput | Support 10,000 concurrent agents; 1M tickets/month |
| NFR-P-07 | Database query performance | No query > 1 second for standard operations |

### 6.2 Scalability

| ID | Requirement | Target |
|----|-------------|--------|
| NFR-S-01 | Horizontal scaling | Stateless worker nodes; scale by adding servers |
| NFR-S-02 | Database partitioning | Ticket archiving for instances > 10M tickets |
| NFR-S-03 | Multi-site architecture | Frappe multi-tenant support maintained |
| NFR-S-04 | Message queue | Redis/RQ for all async processing; no synchronous bottlenecks |

### 6.3 Security

| ID | Requirement | Target |
|----|-------------|--------|
| NFR-SE-01 | Data encryption | TLS 1.3 in transit; AES-256 at rest |
| NFR-SE-02 | Authentication | SSO via SAML 2.0, OAuth 2.0, LDAP; MFA supported |
| NFR-SE-03 | Authorization | Role-based access control (existing Frappe permission system) |
| NFR-SE-04 | Audit logging | All agent actions logged with timestamp, user, and change detail |
| NFR-SE-05 | Data isolation | Multi-tenant: complete data isolation between sites |
| NFR-SE-06 | Vulnerability management | OWASP Top 10 compliance; penetration testing before major releases |

### 6.4 Availability & Reliability

| ID | Requirement | Target |
|----|-------------|--------|
| NFR-A-01 | System uptime | 99.9% for SaaS deployments; self-hosted SLA at customer discretion |
| NFR-A-02 | Backup and recovery | Automated daily backups; RTO < 4 hours; RPO < 1 hour |
| NFR-A-03 | Graceful degradation | AI features degrade gracefully when LLM is unavailable; core ticketing always available |
| NFR-A-04 | Error handling | All errors logged; user-facing error messages are actionable |

### 6.5 Usability

| ID | Requirement | Target |
|----|-------------|--------|
| NFR-U-01 | Onboarding time | New agent productive within 30 minutes of first login |
| NFR-U-02 | Mobile responsiveness | Full agent capability on mobile browser; native app in Phase 3 |
| NFR-U-03 | Accessibility | WCAG 2.1 AA compliance |
| NFR-U-04 | Internationalization | UI translatable; RTL language support; date/time locale-aware |
| NFR-U-05 | Browser support | Chrome, Firefox, Safari, Edge (latest 2 versions each) |

### 6.6 Maintainability & Extensibility

| ID | Requirement | Target |
|----|-------------|--------|
| NFR-M-01 | API coverage | 100% of entities accessible via REST API |
| NFR-M-02 | Webhook events | All ticket lifecycle events emit webhooks |
| NFR-M-03 | Custom field support | Any entity extensible with custom fields without code changes |
| NFR-M-04 | Plugin architecture | Third-party apps installable without modifying core code |
| NFR-M-05 | Test coverage | Minimum 80% unit test coverage on new features; integration tests for all API endpoints |
| NFR-M-06 | Documentation | API docs auto-generated from code; admin setup guide; user guide updated per release |

---

## 7. Integration Requirements

### 7.1 Frappe Ecosystem Integrations (Native — Required)

| System | Integration Type | Data Flow | Priority |
|--------|-----------------|-----------|---------|
| **ERPNext** | Native Frappe DocLink | Customers, orders, invoices, assets, items → agent ticket context | P1 |
| **Frappe CRM** | Native Frappe DocLink | Leads, contacts, deals, opportunities ↔ tickets | P1 |
| **Frappe HR** | Native Frappe DocLink | Employees, departments, assets → internal IT helpdesk | P2 |
| **ERPNext Projects** | Native Frappe DocLink | Time tracking → billable hours in Projects | P1 |

### 7.2 Communication Channels (Required)

| Channel | Integration Type | Priority |
|---------|-----------------|---------|
| **Email** | SMTP/IMAP via ERPNext Email Account | Existing |
| **Live Chat** | WebSocket (Socket.IO) | P1 |
| **WhatsApp** | WhatsApp Business API (Meta) | P2 |
| **SMS** | Twilio / MessageBird API | P2 |
| **Facebook Messenger** | Meta Messenger API | P2 |
| **Instagram DM** | Meta Graph API | P2 |
| **X/Twitter DM** | X API v2 | P2 |
| **Voice/Phone** | WebRTC (native) + SIP bridge | P4 |

### 7.3 AI / LLM Integrations

| Provider | Type | Priority |
|----------|------|---------|
| **OpenAI GPT-4/4o** | API (cloud) | P2 |
| **Anthropic Claude** | API (cloud) | P2 |
| **Google Gemini** | API (cloud) | P2 |
| **Ollama (local LLMs)** | Local inference server | P2 |
| **LM Studio** | Local inference server | P3 |
| **Hugging Face** | Model hosting / API | P3 |

### 7.4 Third-Party Integrations (Connectors)

| System | Type | Priority |
|--------|------|---------|
| **Slack** | Ticket notifications, slash commands, @mentions | P2 |
| **Microsoft Teams** | Ticket notifications, bot commands | P2 |
| **Jira** | Bi-directional ticket sync (support ↔ dev tickets) | P2 |
| **Salesforce** | Customer data sync, ticket → CRM case | P3 |
| **Shopify** | Order data in agent workspace | P3 |
| **PagerDuty / OpsGenie** | Incident alerting for P1 issues | P3 |

---

## 8. Success Criteria

### 8.1 Phase 1 Success Criteria (Month 6)

| Criterion | Measurement Method | Target |
|-----------|-------------------|--------|
| Canned responses adopted | % of tickets using canned responses | > 40% |
| Collision detection preventing duplicates | Duplicate reply incidents per week | < 5 |
| CSAT baseline established | CSAT response rate | > 60% |
| Live chat handling tickets | % new tickets via live chat | > 10% |
| Custom reports created | Number of custom reports created by managers | > 20 |
| SLA improvement | SLA breach rate | Decrease by 15% |

### 8.2 Phase 2 Success Criteria (Month 14)

| Criterion | Measurement Method | Target |
|-----------|-------------------|--------|
| AI Copilot adoption | % tickets where agent used AI draft suggestion | > 50% |
| Agent productivity improvement | Tickets handled per agent per day | +30% |
| WhatsApp channel adoption | % new tickets from WhatsApp | > 15% |
| AI triage accuracy | Routing accuracy (correct team assignment) | > 85% |
| Predictive analytics accuracy | Ticket volume forecast accuracy (7-day) | ± 10% |

### 8.3 Phase 3 Success Criteria (Month 24)

| Criterion | Measurement Method | Target |
|-----------|-------------------|--------|
| AI Agent deflection rate | % tickets resolved without human agent | > 40% |
| ITIL practice coverage | ITIL practices fully implemented | 7 of 11 |
| Problem Management adoption | % repeat incidents linked to Problem record | > 70% |
| Service Catalog adoption | % service requests via catalog (vs. freeform) | > 50% |

### 8.4 Phase 4 Success Criteria (Month 36)

| Criterion | Measurement Method | Target |
|-----------|-------------------|--------|
| Marketplace ecosystem | Number of published community apps | > 50 |
| AI Agent performance | Autonomous resolution rate | > 55% |
| Competitive positioning | Feature parity score vs. Zendesk | > 85% |
| ERPNext customer retention | Churn to external helpdesks | < 5% |

---

## 9. Risks and Mitigations

| ID | Risk | Likelihood | Impact | Mitigation |
|----|------|-----------|--------|-----------|
| R-01 | **LLM API costs too high for SMBs** | High | High | Prioritize local LLM support (Ollama/Llama); offer tiered AI features; benchmark cost per resolution |
| R-02 | **AI quality insufficient for autonomous resolution** | Medium | High | Phase 2 copilot-first approach; human-in-the-loop always available; clear confidence thresholds for escalation |
| R-03 | **WebSocket scalability for live chat** | Medium | High | Load test at 10,000 concurrent connections early; consider horizontal Socket.IO clustering |
| R-04 | **WhatsApp Business API policy changes by Meta** | Low | High | Abstract channel layer so WhatsApp can be swapped; maintain alternative SMS channel |
| R-05 | **ITIL implementation scope creep in Phase 3** | High | Medium | Strict scope gates between phases; ITIL practices released incrementally; community input on prioritization |
| R-06 | **Performance degradation with AI features** | Medium | High | AI processing async (background jobs); never block ticket creation/reply on AI response |
| R-07 | **Community fragmentation from plugin ecosystem** | Low | Medium | Plugin quality standards; automated security scanning; deprecation policy for abandoned plugins |
| R-08 | **Competitive response from Frappe competitors** | Medium | Medium | Move fast on differentiating features (ERPNext integration, local LLM marketplace) that competitors cannot easily copy |
| R-09 | **Data privacy violations from AI processing** | Low | Very High | Customer data never sent to cloud LLMs without explicit opt-in; local LLM default for on-prem deployments; privacy mode that disables all cloud AI |
| R-10 | **Engineering capacity insufficient for roadmap** | Medium | High | Phase gates with explicit resource reviews; community contributions for non-core features; feature prioritization by adoption data |

---

## 10. Dependencies

### 10.1 Technical Dependencies

| Dependency | Required For | Risk |
|-----------|-------------|------|
| Frappe Framework v15+ | All features | Low — internally controlled |
| Socket.IO (already in Frappe) | Live chat, collision detection | Low |
| Redis (already in Frappe) | Background jobs, caching, pub/sub | Low |
| Python 3.10+ | All backend features | Low |
| Vue 3 + Frappe UI | Agent workspace, portal | Low |
| Vector database (Meilisearch or pgvector) | AI search, RAG pipeline | Medium — new dependency |
| Ollama (optional) | Local LLM inference | Low — optional, not required |
| WhatsApp Business API | WhatsApp channel | High — Meta policy dependency |

### 10.2 Business Dependencies

| Dependency | Required For | Owner |
|-----------|-------------|-------|
| Frappe Technologies product approval | All features | Frappe Technologies |
| Community sprint planning | Phase sequencing | Frappe Community Council |
| ERPNext team alignment | ERPNext integration features | ERPNext team |
| Legal review of AI data policies | AI features | Frappe Legal/Compliance |

---

## 11. Out of Scope

The following are explicitly out of scope for this BRD and will be addressed in future documents:

1. **Frappe Cloud infrastructure changes** — Hosting, CDN, and deployment topology
2. **Pricing model changes** — Monetization strategy for commercial helpdesk tiers
3. **Mobile native apps** — iOS and Android apps beyond PWA (tracked separately)
4. **Third-party marketplace revenue model** — App store economics and billing
5. **Multi-language UI translations** — Core UI is English; translations via community process
6. **CX for Frappe Helpdesk itself** — How Frappe handles its own support
7. **Compliance certifications** — SOC2, HIPAA, ISO 27001 certification processes

---

## 12. Assumptions

1. The Frappe Framework will continue to support the technical capabilities required (Socket.IO, background jobs, multi-site)
2. ERPNext version compatibility will be maintained throughout the roadmap period
3. Open-source LLMs (Llama 3, Mistral) will continue to improve in quality to support AI Agent use cases
4. WhatsApp Business API will remain accessible at reasonable cost tiers for SMBs
5. The development team has or will acquire competency in ML/AI engineering by Phase 2
6. Community contributions will supplement core team on non-critical features
7. Competitive landscape will not dramatically shift in a way that invalidates this roadmap within 12 months

---

## 13. Sign-off

This Business Requirements Document requires approval from the following stakeholders before Phase 1 development commences:

| Stakeholder | Role | Signature | Date |
|------------|------|-----------|------|
| | Product Owner, Frappe Technologies | | |
| | Lead Architect, Frappe Helpdesk | | |
| | Community Representative | | |
| | Customer Advisory Board Representative | | |
| | Security/Compliance Officer | | |

---

---

## Addendum: Upstream Sync Impact Assessment (2026-03-23)

### New Capabilities from 600+ Upstream Commits

| New Capability | BRD Requirement | Impact |
|----------------|----------------|--------|
| **Saved Replies** (HD Saved Reply + HD Saved Reply Team) | FR-SR-01 ✅ | Resolves P0 canned responses requirement |
| **Collision Detection** (Socket.IO realtime handlers) | FR-IM-02 ✅ | Resolves P0 collision detection requirement |
| **Keyboard Shortcuts** (composables/shortcuts.ts) | FR-SR-02 ✅ | Resolves P0 keyboard navigation requirement |
| **Agent Landing Page** (Home.vue + agent_home API) | Partial: FR-CI-02 | Provides agent dashboard with metrics (not full custom report builder) |
| **i18n** (translation.ts + 25+ locales) | NFR-U-04 | Partially addresses internationalization requirement |
| **Telemetry** (PostHog integration) | New capability | Not originally in BRD; supports measurement/reporting |
| **Comment Reactions** (HD Comment Reaction) | New capability | Not originally in BRD; enhances team collaboration |
| **Command Palette** (CP.vue) | Enhancement to FR-SR-02 | Enhances agent productivity beyond original requirement |

### Updated Requirement Status Summary

| Priority | Total Requirements | Implemented | Remaining |
|----------|-------------------|-------------|-----------|
| P0 | 4 | **3** (FR-IM-02, FR-SR-01, FR-SR-02) | 1 (FR-IM-01: Internal Notes) |
| P1 | 8 | 0 | 8 |
| P2 | 13 | 0 | 13 |
| P3 | 9 | 0 | 9 |
| P4 | 1 | 0 | 1 |
| **Total** | **35** | **3** | **32** |

### Revised Phase 1 Scope

With 3 of 4 P0 items resolved, Phase 1 can be accelerated:
- **Remaining P0:** Internal Notes (FR-IM-01) — estimated 1–2 weeks
- **P1 priorities shift to:** CSAT Surveys, Advanced Workflow Automation, Custom Report Builder, Enhanced SLA, Live Chat Widget
- **Estimated Phase 1 timeline reduction:** 1–2 months saved from original estimate

---

*This document is version-controlled in the Frappe Helpdesk repository. All changes require review and re-approval by designated stakeholders.*

*Last updated: 2026-03-23 (upstream sync impact assessment)*
*Next review date: 2026-06-21 (quarterly)*
