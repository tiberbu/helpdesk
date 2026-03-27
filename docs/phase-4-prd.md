# Product Requirements Document: Frappe Helpdesk Phase 4
## Innovation — Voice, Video, Local LLM Marketplace, Predictive Analytics, NPS/CES, Gamification

**Version:** 1.0
**Date:** 2026-03-27
**Author:** BMAD Dev Agent (Amelia)
**Status:** Draft
**Phase:** 4 — Innovation (Months 25–36)
**Depends On:**
- `docs/phase-2-4-architecture.md` — technical architecture decisions (ADR-P4-06, ADR-P4-11, ADR-P4-16)
- `docs/phase-3-prd.md` — Phase 3 PRD (prerequisite features)
- `docs/phase-2-4-competitive-analysis.md` — gap analysis driving Phase 4 scope
- `_bmad-output/planning-artifacts/prd.md` — Phase 1 PRD (foundation)

---

## Executive Summary

### Vision

Phase 4 ("Innovation") pushes Frappe Helpdesk beyond parity with SaaS competitors into differentiated territory: real-time voice and video support built on open WebRTC infrastructure, a Local LLM Marketplace for true AI sovereignty, predictive intelligence that prevents problems before they occur, advanced survey instruments beyond CSAT, and gamification mechanics that elevate agent engagement and retention.

### Phase 4 Objective

Deliver 6 capability clusters over Months 25–36 (2 developers, 10 sprints):

1. **Voice/Phone Support** — WebRTC click-to-call, IVR, call recording, voicemail-to-ticket
2. **Video Support** — Screen sharing, co-browsing, video calls
3. **Local LLM Marketplace** — Model selection UI, Ollama fine-tuning, on-premise deployment
4. **Predictive Analytics** — Ticket volume forecasting, agent burnout detection, churn risk scoring
5. **NPS/CES Surveys** — Net Promoter Score, Customer Effort Score surveys beyond CSAT
6. **Gamification** — Agent leaderboards, achievement badges, performance milestones

### Target Outcome

By end of Phase 4, Frappe Helpdesk achieves:
- ~98% feature parity vs. Freshdesk
- ~90% feature parity vs. Zendesk
- ~75% feature parity vs. ServiceNow
- Voice/video capabilities matching Intercom and Zendesk Talk
- Full AI data sovereignty for regulated industries (healthcare, finance, government)

### Key Differentiators Delivered

- **$0/voice minute** vs. $0.05–$0.12/minute (Zendesk Talk/Freshdesk) — on-premise WebRTC with coturn
- **100% on-premise AI** — Local LLM Marketplace means zero data leaves the organization for AI inference
- **Burnout prevention** — Proactive agent wellbeing analytics not available in any mainstream competitor
- **Earned gamification** — Meaningful achievement system vs. superficial badges in Freshdesk

---

## Success Criteria

| ID | Criterion | Metric | Baseline | Target | Measurement Method |
|----|-----------|--------|----------|--------|-------------------|
| SC-P4-01 | Voice channel adoption | % tickets with voice interaction | 0% | ≥15% | HD Voice Session / total tickets (30-day rolling) |
| SC-P4-02 | Voice call resolution rate | % voice tickets resolved on first call | N/A | ≥70% | Single-session resolved / total voice tickets |
| SC-P4-03 | Local LLM activation | % self-hosted sites using local model | 0% | ≥30% | HD Settings ai_provider = "Ollama" count |
| SC-P4-04 | Predictive accuracy | Agent burnout prediction precision | Unmeasured | ≥75% | True positives / predicted burnout flags |
| SC-P4-05 | NPS response rate | % resolved tickets with NPS response | 0% | ≥20% | NPS responses / NPS surveys sent (30-day) |
| SC-P4-06 | Gamification engagement | % agents with ≥1 badge earned in 30 days | 0% | ≥60% | Agents with badge / active agents (30-day) |
| SC-P4-07 | Churn prediction recall | % of churned customers predicted in advance | Unmeasured | ≥65% | Predicted churns / actual churns (90-day) |
| SC-P4-08 | Video co-browse adoption | % tickets using screen share | 0% | ≥10% | HD Video Session / total tickets (30-day) |

**Decision Gate:** If SC-P4-01 (≥15% voice adoption) and SC-P4-06 (≥60% gamification engagement) are met, Phase 4 is declared complete. If SC-P4-03 (local LLM) adoption is below 30%, improve onboarding flow.

---

## Feature 1: Voice/Phone Support

### Overview

WebRTC-based click-to-call voice support directly embedded in the helpdesk — no third-party telephony SaaS required. Agents answer calls from within the helpdesk interface; customers initiate calls from the customer portal widget. IVR routing, call recording, and voicemail-to-ticket conversion complete the phone channel.

**Competitive benchmark:** Zendesk Talk, Freshdesk Call Center (both require SaaS telephony subscriptions)
**Frappe differentiator:** Zero per-minute costs for self-hosted deployments; open WebRTC with coturn as defined in `docs/phase-2-4-architecture.md` ADR-P4-06 and ADR-P4-11

### User Stories

#### VOICE-01: Click-to-Call from Customer Portal

**As a** customer,
**I want** to start a voice call with a support agent directly from the customer portal,
**So that** I can get help immediately for urgent issues without dialing a phone number.

**Acceptance Criteria:**

| ID | Criterion |
|----|-----------|
| VOICE-01-AC-1 | Customer portal displays "Call Support" button when `webrtc_enabled = 1` in HD Settings |
| VOICE-01-AC-2 | Clicking the button initiates WebRTC SDP offer via Socket.IO signaling (ADR-P4-11) |
| VOICE-01-AC-3 | Agent receives incoming call notification with caller identity, ticket history link, and Accept/Decline controls |
| VOICE-01-AC-4 | On acceptance, audio channel established peer-to-peer via WebRTC; TURN server used for NAT traversal |
| VOICE-01-AC-5 | A new `HD Voice Session` record is created with ticket linkage, agent, start time |
| VOICE-01-AC-6 | Call duration shown in real-time on both agent and customer screens |
| VOICE-01-AC-7 | Customer shown estimated wait time if all agents are busy |
| VOICE-01-AC-8 | If no agent accepts within 90 seconds (configurable), customer is offered voicemail |

#### VOICE-02: IVR Routing

**As a** support manager,
**I want** to configure an IVR menu that routes callers to the correct team,
**So that** voice calls are handled by the right specialist without manual transfer.

**Acceptance Criteria:**

| ID | Criterion |
|----|-----------|
| VOICE-02-AC-1 | `HD IVR Config` DocType supports a multi-level menu: greeting prompt, numbered options, team routing per option |
| VOICE-02-AC-2 | IVR prompts are recorded audio files (uploaded MP3/WAV) or text-to-speech (configurable) |
| VOICE-02-AC-3 | IVR options: route to team, route to specific agent, play information message, go to sub-menu |
| VOICE-02-AC-4 | Caller's IVR path recorded in HD Voice Session: `ivr_path` JSON field (e.g. ["1", "2"]) |
| VOICE-02-AC-5 | IVR can be bypassed for VIP contacts (matched by caller email) — direct routing to priority queue |
| VOICE-02-AC-6 | IVR timeout handling: no response after 10 seconds advances to default option or agent queue |

#### VOICE-03: Call Recording

**As a** support manager,
**I want** all voice calls optionally recorded and stored,
**So that** I can review calls for QA, dispute resolution, and training purposes.

**Acceptance Criteria:**

| ID | Criterion |
|----|-----------|
| VOICE-03-AC-1 | Call recording enabled/disabled globally in HD Settings; can be overridden per team |
| VOICE-03-AC-2 | Recording consent prompt played to customer at call start if recording is enabled (configurable message) |
| VOICE-03-AC-3 | Recording stored in Frappe private files as WebM/Opus audio; URL stored in HD Voice Session.recording_url |
| VOICE-03-AC-4 | Recording accessible from ticket detail sidebar via inline audio player |
| VOICE-03-AC-5 | Recordings auto-deleted after configurable retention period (default: 90 days) |
| VOICE-03-AC-6 | Recording access restricted to agents assigned to the ticket and managers |
| VOICE-03-AC-7 | Post-call transcription triggered via Whisper API (if configured); stored in HD Voice Session.transcript |

#### VOICE-04: Voicemail-to-Ticket

**As a** customer,
**I want** to leave a voicemail when no agents are available,
**So that** my issue is captured and followed up without requiring me to call back.

**Acceptance Criteria:**

| ID | Criterion |
|----|-----------|
| VOICE-04-AC-1 | Voicemail offered when: all agents offline, outside business hours, or caller declines queue wait |
| VOICE-04-AC-2 | Customer records voicemail message (max 3 minutes, configurable) via WebRTC audio |
| VOICE-04-AC-3 | Voicemail stored as audio file; automatically creates HD Ticket with subject "Voicemail from [contact]" |
| VOICE-04-AC-4 | Ticket description includes: voicemail audio player, auto-transcription (if Whisper configured), caller timestamp |
| VOICE-04-AC-5 | Voicemail ticket routed to the team/agent the caller was trying to reach via IVR |
| VOICE-04-AC-6 | Agent notified of new voicemail ticket via existing notification pipeline |

### Frappe DocType Design

#### HD IVR Config (Single DocType)
```
Fields:
- ivr_enabled: Check (default: 0)
- greeting_audio: Attach
- greeting_tts: Small Text
- use_tts: Check
- tts_provider: Select (None/Google/Amazon Polly/ElevenLabs)
- tts_api_key: Password
- timeout_seconds: Int (default: 10)
- max_menu_depth: Int (default: 3)
- menu_options: Table → HD IVR Menu Option (key, label, action_type, team, agent, submenu_ref)
- vip_bypass_enabled: Check
- voicemail_enabled: Check
- voicemail_max_duration: Int (default: 180)
```

#### HD Voice Session (Standard DocType — as defined in ADR-P4-06)
```
Fields:
- ticket: Link → HD Ticket
- agent: Link → HD Agent
- customer_email: Data
- started_at: Datetime
- ended_at: Datetime
- duration_seconds: Int
- status: Select (Ringing/Active/On Hold/Ended/Voicemail/Missed)
- ivr_path: JSON (list of IVR options selected)
- recording_enabled: Check
- recording_url: Data
- transcript: Long Text
- sentiment_score: Float
- voicemail: Check
- recording_file: Attach
```

### API Requirements

```python
# helpdesk/api/voice.py
@frappe.whitelist()
def initiate_call(ticket_name: str, customer_email: str) -> dict:
    """Create HD Voice Session, notify available agents. Return session details."""

@frappe.whitelist()
def accept_call(session_name: str) -> dict:
    """Agent accepts call. Returns WebRTC connection parameters (TURN/STUN)."""

@frappe.whitelist()
def end_call(session_name: str) -> dict:
    """End call, calculate duration, trigger transcription if configured."""

@frappe.whitelist()
def save_voicemail(ticket_name: str, audio_file: str) -> dict:
    """Store voicemail, create HD Ticket, trigger notification."""

@frappe.whitelist()
def get_voice_stats(period: str = "30d") -> dict:
    """Return call volume, resolution rate, avg duration, missed calls."""

@frappe.whitelist()
def get_ivr_config() -> dict:
    """Return IVR configuration for customer portal widget."""
```

---

## Feature 2: Video Support

### Overview

Screen sharing and co-browsing capability that allows agents and customers to share screens in real-time for visual troubleshooting. Built on the same WebRTC infrastructure as voice (ADR-P4-11 in `docs/phase-2-4-architecture.md`), with video tracks added alongside audio.

**Competitive benchmark:** Intercom (screen sharing), Gorgias (co-browsing via third-party), Zendesk (no native co-browse)
**Frappe differentiator:** No third-party co-browsing vendor required; zero per-session cost

### User Stories

#### VIDEO-01: Agent-Initiated Screen Share Request

**As an** agent,
**I want** to request a customer share their screen during a live conversation,
**So that** I can see exactly what the customer is experiencing to resolve issues faster.

**Acceptance Criteria:**

| ID | Criterion |
|----|-----------|
| VIDEO-01-AC-1 | Agent sees "Request Screen Share" button in ticket header when customer is active in portal |
| VIDEO-01-AC-2 | Customer receives in-portal notification: "Agent [name] is requesting to view your screen" with Accept/Decline |
| VIDEO-01-AC-3 | On acceptance, customer browser prompts for screen/window/tab selection via `getDisplayMedia()` |
| VIDEO-01-AC-4 | Agent sees customer screen in a resizable panel within the ticket detail view |
| VIDEO-01-AC-5 | Customer sees a persistent "Screen shared" indicator with one-click Stop Sharing button |
| VIDEO-01-AC-6 | Screen share session linked to existing HD Voice Session if active, or creates a new `HD Video Session` |
| VIDEO-01-AC-7 | Screen share automatically ends when either party closes the browser tab or clicks stop |

#### VIDEO-02: Two-Way Video Call

**As a** customer,
**I want** to start a video call with an agent for complex issues,
**So that** face-to-face communication can resolve my problem more effectively than text chat.

**Acceptance Criteria:**

| ID | Criterion |
|----|-----------|
| VIDEO-02-AC-1 | "Start Video Call" option available alongside voice call in customer portal (if `video_enabled = 1` in HD Settings) |
| VIDEO-02-AC-2 | Both agent and customer share webcam video + audio via WebRTC; agent controls layout in their workspace |
| VIDEO-02-AC-3 | Video can be muted/unmuted independently from audio on both sides |
| VIDEO-02-AC-4 | Agent can enable their own screen share during a video call (additive track) |
| VIDEO-02-AC-5 | Recording of video calls follows same consent and retention rules as voice (VOICE-03) |
| VIDEO-02-AC-6 | `HD Video Session` created; linked to ticket; duration, recording_url, participants stored |

#### VIDEO-03: Co-Browsing (Guided Navigation)

**As an** agent,
**I want** to guide a customer through the customer portal by highlighting and annotating elements on their screen,
**So that** I can show rather than tell them how to complete complex portal tasks.

**Acceptance Criteria:**

| ID | Criterion |
|----|-----------|
| VIDEO-03-AC-1 | During an active screen share, agent sees a "Co-Browse Mode" toggle |
| VIDEO-03-AC-2 | In co-browse mode, agent can draw annotations (arrows, highlights, circles) over the customer's shared screen view |
| VIDEO-03-AC-3 | Agent annotations appear in real-time as an overlay on the customer's screen |
| VIDEO-03-AC-4 | Co-browse annotations are ephemeral (not saved) and disappear when session ends |
| VIDEO-03-AC-5 | Agent cannot control the customer's mouse or keyboard — annotations only (security requirement) |
| VIDEO-03-AC-6 | Co-browse session activity logged to HD Video Session (co_browse_enabled: Check, annotation_count: Int) |

### Frappe DocType Design

#### HD Video Session (Standard DocType)
```
Fields:
- ticket: Link → HD Ticket
- agent: Link → HD Agent
- customer_email: Data
- session_type: Select (Screen Share/Video Call/Co-Browse)
- started_at: Datetime
- ended_at: Datetime
- duration_seconds: Int
- recording_enabled: Check
- recording_url: Data
- co_browse_enabled: Check
- annotation_count: Int
- status: Select (Pending/Active/Ended)
- voice_session: Link → HD Voice Session (if combined call)
```

### API Requirements

```python
# helpdesk/api/video.py
@frappe.whitelist()
def request_screen_share(ticket_name: str) -> dict:
    """Notify customer of screen share request. Return signaling room."""

@frappe.whitelist()
def accept_screen_share(session_name: str) -> dict:
    """Customer accepts. Return WebRTC parameters for display media stream."""

@frappe.whitelist()
def start_video_call(ticket_name: str) -> dict:
    """Create HD Video Session for video call. Notify agent."""

@frappe.whitelist()
def end_video_session(session_name: str) -> dict:
    """End session, store duration, trigger recording finalization."""

@frappe.whitelist()
def send_cobrowse_annotation(session_name: str, annotation: dict) -> dict:
    """Relay annotation overlay to customer via Socket.IO."""
```

---

## Feature 3: Local LLM Marketplace

### Overview

A curated marketplace of local LLM models (Ollama, vLLM, llama.cpp) with one-click deployment, model comparison, fine-tuning pipeline, and usage analytics — enabling regulated industries to achieve 100% AI data sovereignty. Extends the Phase 2 `LLMProvider` abstraction (ADR-P2-01 in `docs/phase-2-4-architecture.md`) with a management UI.

**Competitive benchmark:** Zendesk AI (cloud-only, data leaves customer), Freshdesk Freddy (cloud-only)
**Frappe differentiator:** Only enterprise helpdesk platform offering managed on-premise LLM deployment with fine-tuning capability

### User Stories

#### LLM-01: Model Marketplace Browser

**As an** IT admin,
**I want** to browse and install local LLM models from a curated marketplace,
**So that** I can select the best model for my use case without leaving the helpdesk.

**Acceptance Criteria:**

| ID | Criterion |
|----|-----------|
| LLM-01-AC-1 | Marketplace page at `/helpdesk/settings/llm-marketplace` lists available models with: name, parameter size, VRAM requirement, benchmark scores (MMLU, HellaSwag), license type |
| LLM-01-AC-2 | Models categorized: General Purpose, Code Assistance, Multilingual, Instruction-Tuned, Small (≤7B), Large (≥30B) |
| LLM-01-AC-3 | "Install" button triggers `bench exec` Ollama pull command via background job; progress shown in UI |
| LLM-01-AC-4 | Installed models appear in HD Settings → AI → Provider: Ollama → Model dropdown |
| LLM-01-AC-5 | Model benchmark results shown inline: average response time, TTFT (time-to-first-token), quality score on sample prompts |
| LLM-01-AC-6 | Marketplace model list refreshed from Frappe-hosted registry URL (configurable); works offline with cached list |

#### LLM-02: Model Performance Comparison

**As an** IT admin,
**I want** to compare multiple local LLM models side-by-side on my actual helpdesk prompts,
**So that** I can choose the model that delivers the best quality/speed tradeoff for my workload.

**Acceptance Criteria:**

| ID | Criterion |
|----|-----------|
| LLM-02-AC-1 | "Compare Models" UI: select 2–4 installed models and a prompt type (reply_draft, triage, qa_score) |
| LLM-02-AC-2 | Comparison runs the same 10 sample prompts (pulled from real recent tickets, PII-stripped) against each model |
| LLM-02-AC-3 | Results table: model name, avg latency (ms), output quality (human rating 1–5), cost (0 for local) |
| LLM-02-AC-4 | "Set as Active" button promotes a model to production for a specific feature (different models per feature allowed) |
| LLM-02-AC-5 | Comparison results stored in `HD LLM Benchmark` DocType for historical reference |

#### LLM-03: Fine-Tuning Pipeline

**As a** support manager,
**I want** to fine-tune a base LLM on my company's historical ticket data,
**So that** the model learns our product terminology and tone for more accurate AI responses.

**Acceptance Criteria:**

| ID | Criterion |
|----|-----------|
| LLM-03-AC-1 | Fine-tuning wizard: select base model (installed), training data source (closed tickets + approved replies, date range) |
| LLM-03-AC-2 | Training data automatically formatted as instruction-following pairs: `{"instruction": ticket_subject_body, "response": best_reply}` |
| LLM-03-AC-3 | Best replies selected by: agent marked as helpful, CSAT ≥ 4, or manually curated via `hd_fine_tune_include` flag on comment |
| LLM-03-AC-4 | Fine-tuning runs via LoRA (low-rank adaptation) using Ollama or Unsloth backend; GPU recommended but not required |
| LLM-03-AC-5 | Training progress shown in UI: loss curve, estimated time remaining, current epoch |
| LLM-03-AC-6 | Fine-tuned model saved as new Ollama model variant (`helpdesk-{base}-{date}`) |
| LLM-03-AC-7 | Fine-tuned model tested on holdout set before promotion; accuracy improvement shown vs. base model |
| LLM-03-AC-8 | Fine-tuning job metadata stored in `HD LLM Fine-Tune Job` DocType |

#### LLM-04: LLM Usage and Cost Analytics

**As an** IT admin,
**I want** to see usage metrics and cost comparison across local and cloud LLM configurations,
**So that** I can justify the infrastructure investment in local models.

**Acceptance Criteria:**

| ID | Criterion |
|----|-----------|
| LLM-04-AC-1 | LLM analytics dashboard: daily/weekly/monthly AI feature usage (draft_reply, triage, qa_score, agent) |
| LLM-04-AC-2 | Cost comparison: "if using GPT-4o at current usage, cost would be $X/month" vs. $0 for local |
| LLM-04-AC-3 | Latency dashboard: p50/p95/p99 response times per model per feature |
| LLM-04-AC-4 | Quality dashboard: AI resolution rate, CSAT scores for AI-assisted vs. non-AI tickets |
| LLM-04-AC-5 | Data residency confirmation badge: "100% on-premise — no data sent to external LLM" when local model active |

### Frappe DocType Design

#### HD LLM Marketplace Item (Standard DocType)
```
Fields:
- model_id: Data (e.g. "llama3.2:8b", required, unique)
- display_name: Data
- provider: Select (Ollama/vLLM/llama.cpp)
- parameter_size_b: Float (in billions)
- vram_gb_required: Float
- license: Select (MIT/Apache 2.0/Llama/Gemma/Custom)
- categories: JSON (list of category tags)
- mmlu_score: Float
- hellaswag_score: Float
- description: Small Text
- pull_command: Data (e.g. "ollama pull llama3.2:8b")
- registry_url: Data
- is_installed: Check (auto-updated)
- installed_at: Datetime
```

#### HD LLM Benchmark (Standard DocType)
```
Fields:
- model_a: Data
- model_b: Data
- model_c: Data
- model_d: Data
- prompt_type: Select (reply_draft/triage/qa_score/summarize)
- results: JSON (per-model: avg_latency_ms, quality_score, sample_count)
- run_at: Datetime
- run_by: Link → User
```

#### HD LLM Fine-Tune Job (Standard DocType)
```
Fields:
- base_model: Data
- output_model_name: Data
- training_date_from: Date
- training_date_to: Date
- training_pairs: Int
- validation_accuracy_base: Float
- validation_accuracy_finetuned: Float
- epochs: Int
- batch_size: Int
- lora_rank: Int
- status: Select (Queued/Running/Completed/Failed)
- started_at: Datetime
- completed_at: Datetime
- loss_log: Long Text (JSON loss history)
- error_message: Small Text
```

### API Requirements

```python
# helpdesk/api/llm_marketplace.py
@frappe.whitelist()
def get_marketplace_models(refresh: bool = False) -> list:
    """Return curated model list from registry. Refresh from remote if requested."""

@frappe.whitelist()
def install_model(model_id: str) -> dict:
    """Enqueue Ollama pull job. Return job_id for progress tracking."""

@frappe.whitelist()
def compare_models(model_ids: list, prompt_type: str) -> dict:
    """Run comparison on sample prompts. Store in HD LLM Benchmark."""

@frappe.whitelist()
def start_fine_tune(base_model: str, date_from: str, date_to: str) -> dict:
    """Prepare training data, enqueue fine-tune job. Return job_name."""

@frappe.whitelist()
def get_fine_tune_progress(job_name: str) -> dict:
    """Return training progress, current loss, estimated completion."""

@frappe.whitelist()
def get_llm_usage_analytics(period: str = "30d") -> dict:
    """Return usage, latency, cost, and quality metrics per model/feature."""
```

---

## Feature 4: Predictive Analytics

### Overview

Machine learning models that predict future ticket volume, identify agents at risk of burnout, and score customers for churn risk — enabling proactive intervention before problems escalate. Builds on the Phase 2 analytics pipeline (ADR-P2-13, ADR-P2-14 in `docs/phase-2-4-architecture.md`) with Phase 4 models trained on richer longitudinal data.

**Competitive benchmark:** Zendesk Explore (basic forecasting only), Freshdesk Analytics (no burnout/churn models)
**Frappe differentiator:** Burnout prediction and churn risk scoring are unique capabilities not available in any mainstream helpdesk competitor

### User Stories

#### PRED-01: Ticket Volume Forecasting

**As a** support manager,
**I want** accurate 14-day ticket volume forecasts broken down by category and channel,
**So that** I can plan staffing and agent schedules before peaks occur.

**Acceptance Criteria:**

| ID | Criterion |
|----|-----------|
| PRED-01-AC-1 | Volume forecast generated daily; covers next 14 days at hourly granularity |
| PRED-01-AC-2 | Forecast model trained on 180-day rolling history; uses SARIMA with day-of-week + month seasonality (ADR-P2-14) |
| PRED-01-AC-3 | Forecast broken down by: total, by channel (email/chat/voice/portal), by ticket category |
| PRED-01-AC-4 | Forecast confidence intervals shown (80% and 95%) as shaded bands on chart |
| PRED-01-AC-5 | Manager can flag upcoming events (product launches, campaigns) as "+N% uplift" for specific date ranges |
| PRED-01-AC-6 | Forecast accuracy scorecard: actual vs. predicted for last 30 days with MAPE metric |
| PRED-01-AC-7 | Alert sent to manager when next-day forecast exceeds current capacity by >20% |

#### PRED-02: Agent Burnout Prediction

**As a** support manager,
**I want** early warning when an agent is approaching burnout,
**So that** I can intervene with workload relief or support before they disengage or resign.

**Acceptance Criteria:**

| ID | Criterion |
|----|-----------|
| PRED-02-AC-1 | Burnout risk score (0–100) calculated for each agent daily; stored in `HD Agent Burnout Score` |
| PRED-02-AC-2 | Risk model features: tickets_closed_trend (declining), avg_response_time_trend (increasing), after_hours_activity (increasing), CSAT_trend (declining), last_PTO_date (recency) |
| PRED-02-AC-3 | Risk thresholds: 0–30 = Healthy (green), 31–60 = Watch (amber), 61–80 = At Risk (orange), 81–100 = Critical (red) |
| PRED-02-AC-4 | Manager dashboard shows burnout risk for all direct reports; only the agent and their manager can see individual scores |
| PRED-02-AC-5 | When agent crosses into "At Risk" threshold: manager receives private email with agent name, risk score, and suggested interventions |
| PRED-02-AC-6 | Agent never sees their own raw burnout score; they see "Workload Health" indicator with actionable suggestions (e.g., "Your response times are trending up — consider taking a break") |
| PRED-02-AC-7 | Model retrained weekly on new agent performance data |

#### PRED-03: Customer Churn Risk Scoring

**As a** customer success manager,
**I want** to know which customers are at risk of churning based on their support experience,
**So that** I can prioritize proactive outreach before they cancel.

**Acceptance Criteria:**

| ID | Criterion |
|----|-----------|
| PRED-03-AC-1 | Churn risk score (0–100) calculated weekly for each customer (HD Customer) with ≥3 tickets |
| PRED-03-AC-2 | Risk model features: recent_CSAT_avg (low = high risk), ticket_volume_trend (increasing = high risk), resolution_time_trend (increasing = high risk), NPS_score (low = high risk), last_escalation_age (recent = high risk) |
| PRED-03-AC-3 | Churn risk badge visible on HD Customer record and ticket sidebar for the customer |
| PRED-03-AC-4 | Churn risk leaderboard: top 20 at-risk customers with score, last contact date, recommended action |
| PRED-03-AC-5 | Alert triggered when customer crosses 70+ risk threshold: creates HD Task assigned to CSM |
| PRED-03-AC-6 | Historical churn scores stored in `HD Customer Churn Score` for model validation |
| PRED-03-AC-7 | Model validation: compare predicted churn (score > 70) vs. actual churn over 90-day window; precision/recall displayed |

#### PRED-04: SLA Breach Risk Scoring (Phase 4 Enhancement)

**As an** agent,
**I want** real-time SLA breach risk scores on open tickets,
**So that** I can prioritize tickets that are most likely to breach before they do.

**Acceptance Criteria:**

| ID | Criterion |
|----|-----------|
| PRED-04-AC-1 | SLA breach risk (0–100) updated every 15 minutes per open ticket (enhancing Phase 2 ADR-P2-14 model) |
| PRED-04-AC-2 | Risk model features: time_to_breach, priority, category, current_agent_workload, historical_breach_rate_for_category |
| PRED-04-AC-3 | Tickets with risk ≥ 80 highlighted in ticket list with red breach risk badge |
| PRED-04-AC-4 | Agent receives push notification when their ticket crosses 80% breach risk |
| PRED-04-AC-5 | Breach risk score shown in ticket sidebar; historical risk curve shown as sparkline |

### Frappe DocType Design

#### HD Agent Burnout Score (Standard DocType)
```
Fields:
- agent: Link → HD Agent (required)
- score_date: Date (required)
- burnout_score: Float (0–100)
- risk_level: Select (Healthy/Watch/At Risk/Critical)
- tickets_trend: Float (% change vs 14-day prior)
- response_time_trend: Float
- after_hours_pct: Float
- csat_trend: Float
- days_since_pto: Int
- model_version: Data
```

#### HD Customer Churn Score (Standard DocType)
```
Fields:
- customer: Link → HD Customer (required)
- score_date: Date (required)
- churn_score: Float (0–100)
- risk_level: Select (Low/Medium/High/Critical)
- recent_csat_avg: Float
- ticket_volume_trend: Float
- resolution_time_trend: Float
- nps_score: Float
- days_since_escalation: Int
- model_version: Data
- action_created: Check
```

### API Requirements

```python
# helpdesk/api/predictive.py
@frappe.whitelist()
def get_volume_forecast(days: int = 14, breakdown: str = "total") -> list:
    """Return volume forecast with confidence intervals."""

@frappe.whitelist()
def get_team_burnout_dashboard(team: str = None) -> list:
    """Return burnout scores for all agents (manager only). Filter by team."""

@frappe.whitelist()
def get_churn_risk_leaderboard(top_n: int = 20) -> list:
    """Return top N at-risk customers with scores and recommended actions."""

@frappe.whitelist()
def get_sla_breach_risk(ticket_name: str) -> dict:
    """Return current breach risk score and contributing factors for a ticket."""

@frappe.whitelist()
def get_forecast_accuracy_report(period_days: int = 30) -> dict:
    """Return MAPE and per-day accuracy for volume forecast validation."""

@frappe.whitelist()
def add_forecast_event(date_from: str, date_to: str, uplift_pct: float, reason: str) -> dict:
    """Add manual uplift event to forecast (e.g. product launch)."""
```

---

## Feature 5: NPS/CES Surveys

### Overview

Net Promoter Score (NPS) and Customer Effort Score (CES) survey instruments that go beyond CSAT to measure loyalty and friction across the customer journey. Surveys are triggered at configurable lifecycle points, tracked longitudinally, and surfaced in customer-level analytics.

**Competitive benchmark:** Zendesk CSAT (basic), Freshdesk CSAT + NPS (limited), Qualtrics/Medallia (standalone — not integrated with helpdesk)
**Frappe differentiator:** Unified CSAT + NPS + CES in a single platform, correlated with ticket and agent data

### User Stories

#### SURVEY-01: NPS Survey Collection

**As a** customer success manager,
**I want** to send NPS surveys at strategic moments in the customer journey,
**So that** I can measure loyalty trends and identify promoters and detractors.

**Acceptance Criteria:**

| ID | Criterion |
|----|-----------|
| SURVEY-01-AC-1 | `HD NPS Survey` DocType: respondent, score (0–10), verbatim, category (Promoter ≥9 / Passive 7–8 / Detractor ≤6), sent_at, responded_at |
| SURVEY-01-AC-2 | NPS trigger events (configurable in HD Settings): after ticket close, after 30 days since last NPS, on service request fulfillment |
| SURVEY-01-AC-3 | NPS survey sent via email with one-click scoring (0–10) in email body; clicking score captures response without portal login required |
| SURVEY-01-AC-4 | Follow-up open text question shown after score selection: "What's the primary reason for your score?" |
| SURVEY-01-AC-5 | Customer NPS history tracked: all responses over time visible on HD Customer record |
| SURVEY-01-AC-6 | NPS dashboard: overall NPS trend (30/90/180 days), promoter/passive/detractor breakdown, top verbatim themes (AI-extracted) |
| SURVEY-01-AC-7 | Detractor (score ≤ 6) automatically creates follow-up task for CSM; score visible in churn risk model (PRED-03) |
| SURVEY-01-AC-8 | NPS survey suppressed for 90 days after a previous NPS response from the same contact (configurable cooldown) |

#### SURVEY-02: Customer Effort Score (CES) Survey

**As a** support manager,
**I want** to measure how much effort customers expend to resolve their issues,
**So that** I can identify high-friction processes and prioritize improvements.

**Acceptance Criteria:**

| ID | Criterion |
|----|-----------|
| SURVEY-02-AC-1 | `HD CES Survey` DocType: respondent, ticket, score (1–7 Likert), verbatim, sent_at, responded_at |
| SURVEY-02-AC-2 | CES survey sent automatically after ticket resolution (separate from CSAT; configurable to send both or one) |
| SURVEY-02-AC-3 | CES survey question: "The company made it easy for me to handle my issue" (Strongly Disagree → Strongly Agree) |
| SURVEY-02-AC-4 | Low CES (1–3) flags the ticket for process review; auto-tags ticket with `high-effort-contact` |
| SURVEY-02-AC-5 | CES dashboard: average CES by team, by ticket category, by channel; trend over time |
| SURVEY-02-AC-6 | CES ↔ CSAT correlation report: are high-effort contacts also giving low satisfaction? |
| SURVEY-02-AC-7 | CES score included in agent scorecard (QA module from Phase 3); low CES impacts quality metrics |

#### SURVEY-03: Unified Survey Dashboard

**As a** customer experience manager,
**I want** a unified view of CSAT, NPS, and CES metrics in one dashboard,
**So that** I can understand the full customer experience across all satisfaction dimensions.

**Acceptance Criteria:**

| ID | Criterion |
|----|-----------|
| SURVEY-03-AC-1 | Unified CX Dashboard shows: CSAT %, NPS (calculated as Promoters% - Detractors%), CES average — all with 30/90-day trends |
| SURVEY-03-AC-2 | Correlation matrix: which ticket types drive low NPS? Which channels produce high CES? |
| SURVEY-03-AC-3 | Customer-level view: CSAT history, NPS score, CES average on HD Customer record |
| SURVEY-03-AC-4 | Verbatim analysis: AI-extracted themes from NPS + CES open text (uses Phase 2/3 LLM layer) |
| SURVEY-03-AC-5 | Benchmark comparison: "Your NPS of 42 is above industry average of 32 for SaaS" (curated benchmarks in HD Settings) |
| SURVEY-03-AC-6 | Dashboard exportable to PDF for executive reporting |

### Frappe DocType Design

#### HD NPS Survey (Standard DocType)
```
Fields:
- respondent: Link → Contact (required)
- customer: Link → HD Customer
- ticket: Link → HD Ticket (optional — trigger ticket)
- score: Int (0–10, required)
- category: Select (Promoter/Passive/Detractor) — auto-calculated
- verbatim: Long Text
- sent_at: Datetime
- responded_at: Datetime
- survey_token: Data (unique, for one-click email response)
- follow_up_task: Link → HD Task
```

#### HD CES Survey (Standard DocType)
```
Fields:
- respondent: Link → Contact (required)
- customer: Link → HD Customer
- ticket: Link → HD Ticket (required)
- score: Int (1–7, required)
- verbatim: Long Text
- sent_at: Datetime
- responded_at: Datetime
- survey_token: Data (unique, for one-click email response)
- high_effort_flagged: Check (auto-set if score ≤ 3)
```

### API Requirements

```python
# helpdesk/api/surveys.py
@frappe.whitelist(allow_guest=True)
def record_nps_response(token: str, score: int, verbatim: str = "") -> dict:
    """Record NPS response from one-click email token. No login required."""

@frappe.whitelist(allow_guest=True)
def record_ces_response(token: str, score: int, verbatim: str = "") -> dict:
    """Record CES response from one-click email token. No login required."""

@frappe.whitelist()
def get_unified_cx_dashboard(period_days: int = 30) -> dict:
    """Return CSAT %, NPS, CES average with trends and breakdowns."""

@frappe.whitelist()
def get_customer_survey_history(customer_name: str) -> dict:
    """Return all CSAT, NPS, CES responses for a customer."""

@frappe.whitelist()
def get_nps_verbatim_themes(period_days: int = 30) -> list:
    """AI-extracted themes from NPS open text responses."""

@frappe.whitelist()
def get_survey_correlation_report(period_days: int = 90) -> dict:
    """Return CSAT/NPS/CES correlations by ticket type, channel, team."""
```

---

## Feature 6: Gamification

### Overview

A meaningful achievement and recognition system for agents that rewards quality, consistency, and collaboration — not just ticket volume. Badges earned for genuine milestones, leaderboards for healthy competition, and weekly team highlights that celebrate top performers and create a culture of excellence.

**Competitive benchmark:** Freshdesk Arcade (basic, points-heavy), Zoho Desk (limited), no gamification in Zendesk/ServiceNow
**Frappe differentiator:** Quality-weighted achievements (QA scores + CSAT, not just volume), ITIL-specific badges, and transparent opt-out for agents who prefer not to participate

### User Stories

#### GAME-01: Agent Achievement Badges

**As an** agent,
**I want** to earn badges for genuine accomplishments in my helpdesk work,
**So that** my effort and quality are recognized in a visible and motivating way.

**Acceptance Criteria:**

| ID | Criterion |
|----|-----------|
| GAME-01-AC-1 | `HD Badge` DocType defines badge catalog: name, description, icon (emoji/SVG), category, criteria_type, criteria_value |
| GAME-01-AC-2 | Default badge catalog (configurable): Speed Demon (10 tickets in 1 day), CSAT Champion (5-star CSAT for 30 days), Knowledge Builder (linked KB article to 20 tickets), First Responder (first reply < 5 min, 10 times), QA Gold (QA score ≥ 4.5 for 30 days), Mentor (led 3 coaching sessions), Major Incident Hero (participated in major incident resolution) |
| GAME-01-AC-3 | Badge evaluation runs nightly; new badges awarded automatically when criteria met |
| GAME-01-AC-4 | Agent receives in-app notification when a new badge is earned |
| GAME-01-AC-5 | Badges displayed on agent profile page and in ticket sidebar (optional — agent can hide) |
| GAME-01-AC-6 | Badge history preserved; multiple earned dates shown for repeatable badges |
| GAME-01-AC-7 | Admin can create custom badges with custom criteria; criteria defined as Python expression evaluated against agent stats |

#### GAME-02: Performance Leaderboard

**As a** support manager,
**I want** a weekly performance leaderboard for my team,
**So that** healthy competition motivates agents to improve their metrics.

**Acceptance Criteria:**

| ID | Criterion |
|----|-----------|
| GAME-02-AC-1 | Leaderboard page at `/helpdesk/leaderboard` shows team rankings for configurable period (weekly default) |
| GAME-02-AC-2 | Leaderboard score is composite: tickets_resolved (30%) + avg_CSAT (30%) + QA_score (25%) + response_time_rank (15%) — weights configurable |
| GAME-02-AC-3 | Leaderboard filterable by team; managers see only their team's board by default |
| GAME-02-AC-4 | Agent can opt out of leaderboard visibility; their metrics still tracked but name replaced with "Anonymous Agent" |
| GAME-02-AC-5 | Top 3 agents highlighted with gold/silver/bronze indicators |
| GAME-02-AC-6 | Trend arrows show week-over-week rank change for each agent |
| GAME-02-AC-7 | Leaderboard history archived weekly in `HD Leaderboard Snapshot` DocType |

#### GAME-03: Team Highlights and Recognition

**As a** support manager,
**I want** to automatically celebrate team wins in a weekly digest,
**So that** achievements are visible to the whole team and create a culture of recognition.

**Acceptance Criteria:**

| ID | Criterion |
|----|-----------|
| GAME-03-AC-1 | Weekly team highlights email sent every Monday: top performer, most improved, badge earners of the week, team CSAT/NPS trend |
| GAME-03-AC-2 | Highlights posted as an announcement in the helpdesk dashboard (visible to whole team) |
| GAME-03-AC-3 | Manager can add a personal message to the weekly digest before it sends (optional) |
| GAME-03-AC-4 | "Give Recognition" button on agent profile: manager or peer can give a public shout-out that appears in the digest |
| GAME-03-AC-5 | Agent milestones celebrated: 100th ticket, 1-year anniversary, first Major Incident resolved |
| GAME-03-AC-6 | Team win highlights: "Team hit 95% CSAT this week — 3-week streak!" |

#### GAME-04: Personal Achievement Dashboard

**As an** agent,
**I want** to see my personal progress toward goals and achievements,
**So that** I know what I'm working toward and can track my own improvement.

**Acceptance Criteria:**

| ID | Criterion |
|----|-----------|
| GAME-04-AC-1 | Agent profile page includes "Achievements" tab: earned badges, progress bars toward in-progress badges |
| GAME-04-AC-2 | Progress indicators: "You need 3 more CSAT 5-star ratings to earn CSAT Champion" |
| GAME-04-AC-3 | Personal stats: total tickets resolved, lifetime CSAT average, avg response time, QA score trend |
| GAME-04-AC-4 | "My Ranking" mini-widget on agent home page (can be hidden if opted out of leaderboard) |
| GAME-04-AC-5 | Career milestones timeline: first ticket, 100th ticket, first badge, first 5-star CSAT |

### Frappe DocType Design

#### HD Badge (Standard DocType)
```
Fields:
- badge_name: Data (required, unique)
- description: Small Text
- icon: Data (emoji or SVG path)
- category: Select (Quality/Speed/Knowledge/Leadership/Collaboration/Milestone/ITIL)
- criteria_type: Select (tickets_count/csat_avg/qa_score/response_time/custom)
- criteria_period_days: Int (evaluation window)
- criteria_value: Float (threshold)
- criteria_expression: Code (Python expression for custom badges)
- is_repeatable: Check (can be earned multiple times)
- is_active: Check
```

#### HD Agent Badge (Child DocType of HD Agent)
```
Fields:
- badge: Link → HD Badge (required)
- earned_at: Datetime
- criteria_value_at_earn: Float (metric value when badge was earned)
- notified: Check
```

#### HD Leaderboard Snapshot (Standard DocType)
```
Fields:
- period_start: Date (required)
- period_end: Date (required)
- team: Link → HD Team
- rankings: JSON (list of {agent, rank, composite_score, breakdown})
- generated_at: Datetime
```

#### HD Agent Recognition (Standard DocType)
```
Fields:
- agent: Link → HD Agent (recipient)
- given_by: Link → User
- message: Small Text
- is_public: Check
- given_at: Datetime
- included_in_digest: Check
```

### API Requirements

```python
# helpdesk/api/gamification.py
@frappe.whitelist()
def get_agent_badges(agent_email: str = None) -> list:
    """Return earned badges + progress toward unearned badges for agent."""

@frappe.whitelist()
def get_leaderboard(team: str = None, period: str = "week") -> list:
    """Return ranked agent list with composite scores. Respects opt-out."""

@frappe.whitelist()
def evaluate_badges_for_agent(agent_email: str) -> dict:
    """Run badge evaluation for one agent. Return newly earned badges."""

@frappe.whitelist()
def give_recognition(agent_email: str, message: str, is_public: bool = True) -> dict:
    """Record peer/manager recognition. Include in next weekly digest."""

@frappe.whitelist()
def get_weekly_highlights(team: str = None) -> dict:
    """Return weekly highlights data for digest email and dashboard widget."""

@frappe.whitelist()
def opt_out_leaderboard(opt_out: bool = True) -> dict:
    """Toggle agent's leaderboard visibility preference."""
```

---

## Technical Architecture Summary

### New DocTypes (Phase 4)

| DocType | Module | Type | Phase Feature |
|---------|--------|------|---------------|
| HD IVR Config | Helpdesk | Single | Voice |
| HD Voice Session | Helpdesk | Standard | Voice (ADR-P4-06) |
| HD Video Session | Helpdesk | Standard | Video |
| HD LLM Marketplace Item | Helpdesk | Standard | LLM Marketplace |
| HD LLM Benchmark | Helpdesk | Standard | LLM Marketplace |
| HD LLM Fine-Tune Job | Helpdesk | Standard | LLM Marketplace |
| HD Agent Burnout Score | Helpdesk | Standard | Predictive Analytics |
| HD Customer Churn Score | Helpdesk | Standard | Predictive Analytics |
| HD NPS Survey | Helpdesk | Standard | Surveys |
| HD CES Survey | Helpdesk | Standard | Surveys |
| HD Badge | Helpdesk | Standard | Gamification |
| HD Agent Badge | Helpdesk | Child (HD Agent) | Gamification |
| HD Leaderboard Snapshot | Helpdesk | Standard | Gamification |
| HD Agent Recognition | Helpdesk | Standard | Gamification |

### HD Settings Additions (Phase 4)
```python
# Voice
webrtc_enabled, turn_server_url, turn_username, turn_credential,
stun_server_url, video_enabled, ivr_enabled, recording_enabled,
recording_retention_days, voicemail_enabled, voicemail_max_duration_s

# LLM Marketplace
llm_marketplace_registry_url, ollama_base_url, local_llm_enabled,
fine_tune_backend  # Select (Ollama/Unsloth)

# Surveys
nps_enabled, nps_trigger, nps_cooldown_days,
ces_enabled, ces_with_csat, survey_from_email

# Gamification
gamification_enabled, leaderboard_enabled, leaderboard_weights_json,
weekly_digest_enabled, weekly_digest_send_day
```

### API Modules (Phase 4)
```
helpdesk/api/voice.py          — WebRTC signaling, IVR, voicemail
helpdesk/api/video.py          — Screen share, video call, co-browse
helpdesk/api/llm_marketplace.py — Model install, compare, fine-tune
helpdesk/api/predictive.py     — Volume forecast, burnout, churn, SLA risk
helpdesk/api/surveys.py        — NPS, CES collection and analytics
helpdesk/api/gamification.py   — Badges, leaderboard, recognition
```

### Channel Adapter (Phase 4)
Per `docs/phase-2-4-architecture.md` ADR-P2-05, the voice adapter is:
```
helpdesk/helpdesk/channels/voice_adapter.py   — VoiceAdapter (WebRTC-based)
helpdesk/helpdesk/channels/voice/
├── signaling.py       — SDP relay via Socket.IO (ADR-P4-11)
├── session.py         — HD Voice Session controller
└── transcription.py   — Post-call Whisper transcription
```

### Frontend Components (Phase 4)

| Component | Location | Feature |
|-----------|----------|---------|
| VoiceWidget.vue | widget/voice/ | Voice (customer portal) |
| CallPanel.vue | desk/src/components/ticket/ | Voice (agent workspace) |
| IVRConfigEditor.vue | desk/src/pages/settings/ | Voice IVR |
| ScreenSharePanel.vue | desk/src/components/ticket/ | Video |
| VideoCallFrame.vue | desk/src/components/ticket/ | Video |
| CoBrowseOverlay.vue | desk/src/components/ticket/ | Video |
| LLMMarketplace.vue | desk/src/pages/settings/ | LLM Marketplace |
| ModelCompareTool.vue | desk/src/pages/settings/ | LLM Marketplace |
| FineTuneWizard.vue | desk/src/pages/settings/ | LLM Marketplace |
| VolumeForecastChart.vue | desk/src/pages/analytics/ | Predictive |
| BurnoutDashboard.vue | desk/src/pages/analytics/ | Predictive |
| ChurnRiskLeaderboard.vue | desk/src/pages/analytics/ | Predictive |
| UnifiedCXDashboard.vue | desk/src/pages/analytics/ | Surveys |
| NPSSurveyResponse.vue | portal/survey/ | Surveys (public) |
| CESSurveyResponse.vue | portal/survey/ | Surveys (public) |
| Leaderboard.vue | desk/src/pages/leaderboard/ | Gamification |
| AgentBadges.vue | desk/src/pages/profile/ | Gamification |
| WeeklyHighlightsBanner.vue | desk/src/pages/home/ | Gamification |

---

## Phase 4 Sprint Plan

### Sprint 1–2: Voice Infrastructure
- HD IVR Config DocType + IVR menu builder UI
- `voice_adapter.py` — WebRTC signaling via Socket.IO (per ADR-P4-11)
- HD Voice Session DocType + session lifecycle
- VoiceWidget.vue (customer portal) + CallPanel.vue (agent workspace)
- Call recording storage + Whisper transcription integration
- Voicemail-to-ticket pipeline
- **Rationale:** Voice is the highest-impact channel addition; infrastructure first

### Sprint 3–4: Video + Co-Browse
- HD Video Session DocType
- `getDisplayMedia()` screen share flow; WebRTC video track management
- ScreenSharePanel.vue + VideoCallFrame.vue
- Co-browse annotation overlay (Socket.IO relay + canvas overlay)
- TURN server configuration documentation + coturn Docker image

### Sprint 5–6: Local LLM Marketplace
- HD LLM Marketplace Item DocType + registry sync
- Ollama install/management background jobs
- Model comparison tool + HD LLM Benchmark DocType
- Fine-tuning pipeline: data preparation, LoRA training job, HD LLM Fine-Tune Job DocType
- LLM usage analytics dashboard with cost comparison

### Sprint 7: Predictive Analytics
- Ticket volume forecast model (SARIMA enhancement from Phase 2 ADR-P2-14)
- Agent burnout scoring model + HD Agent Burnout Score DocType
- Customer churn risk model + HD Customer Churn Score DocType
- SLA breach risk enhancements (Phase 4 upgrade of Phase 2 breach predictor)
- Manager burnout dashboard + churn risk leaderboard

### Sprint 8: NPS/CES Surveys
- HD NPS Survey + HD CES Survey DocTypes
- One-click email response pipeline (allow_guest token API)
- NPS trigger event configuration + cooldown enforcement
- CES high-effort flag → process review workflow
- Unified CX Dashboard (CSAT + NPS + CES combined view)
- AI verbatim theme extraction (uses Phase 3 LLM layer)

### Sprint 9–10: Gamification + Polish
- HD Badge + HD Agent Badge DocTypes + default badge catalog
- Nightly badge evaluation job
- Leaderboard composite scoring + HD Leaderboard Snapshot archival
- HD Agent Recognition + peer/manager shout-out flow
- Weekly highlights digest email + dashboard banner
- Agent achievement profile tab
- Integration testing: gamification ↔ QA scores ↔ CSAT ↔ NPS
- Performance profiling: ensure voice/video latency targets met

---

## Dependencies

| Phase 4 Feature | Prerequisite | Risk |
|-----------------|-------------|------|
| Voice (WebRTC) | TURN/STUN server (coturn) deployment | **HIGH** — call quality degrades without TURN in NAT environments |
| Voice (Transcription) | Whisper API key or local Whisper model | MEDIUM — voicemail/transcript optional if not configured |
| Video (Screen Share) | Modern browser with `getDisplayMedia()` support | LOW — all major browsers since 2020 |
| Local LLM Marketplace | Ollama installed on server; GPU recommended | MEDIUM — CPU inference works but is slow; document hardware requirements |
| LLM Fine-Tuning | Phase 2 LLM layer (ADR-P2-01) + Ollama/Unsloth | **HIGH** — depends on Phase 2 LLM infrastructure being stable |
| Predictive Analytics | Phase 2 analytics pipeline (ADR-P2-13, ADR-P2-14) | **HIGH** — burnout/churn models need 180+ days of historical data |
| NPS/CES Surveys | Phase 1 email pipeline; Phase 3 CSAT infrastructure | LOW — additive to existing survey mechanism |
| Gamification (QA badges) | Phase 3 QA Scoring (HD QA Score) | MEDIUM — QA-based badges require Phase 3 QA to be operational |
| Gamification (Leaderboard) | Phase 1 CSAT + Phase 3 QA Scoring | LOW — leaderboard degrades gracefully if QA scores absent |
| Churn Risk Model | NPS scores (SURVEY-01) for full accuracy | LOW — model works without NPS but improves when NPS data available |

---

## Non-Functional Requirements

| ID | Requirement | Category | Acceptance |
|----|-------------|----------|-----------|
| NFR-P4-01 | Voice call connection setup time ≤ 3 seconds (SDP exchange + ICE) | Performance | p95 from call initiation to audio established |
| NFR-P4-02 | Voice/video latency ≤ 200ms end-to-end with TURN server | Performance | WebRTC audio latency measured in production |
| NFR-P4-03 | Burnout score calculation completes within 5 minutes of nightly job | Performance | Background job p95 for 200-agent deployment |
| NFR-P4-04 | LLM model comparison completes within 60 seconds (10 sample prompts, 4 models) | Performance | Parallel inference assumed |
| NFR-P4-05 | Voice recordings encrypted at rest (AES-256 in Frappe private files) | Security | Frappe private file storage enforces this by default |
| NFR-P4-06 | NPS/CES survey tokens are single-use + expire after 72 hours | Security | Token validation in allow_guest API endpoints |
| NFR-P4-07 | Burnout scores accessible only to agent's direct manager + System Manager | Security | Field-level permission check in API |
| NFR-P4-08 | Agent can opt out of leaderboard; opt-out must be honored within 1 hour | Privacy | Leaderboard generation respects opt_out flag |
| NFR-P4-09 | Local LLM inference never sends data to external URLs when Ollama active | Security | Network call audit in LLMProvider.complete() |
| NFR-P4-10 | Fine-tuning training data PII-stripped via `ai/safety.py` before use | Privacy | PII redaction required per ADR enforcement rule 9 |
| NFR-P4-11 | Voice/video features hidden when `webrtc_enabled = 0` in HD Settings | Feature flag | All voice/video UI components check this setting |

---

## Risk Register

| Risk | Impact | Probability | Mitigation |
|------|--------|-------------|-----------|
| TURN server deployment complexity blocks voice adoption | High | High | Provide pre-configured coturn Docker Compose in docs; offer hosted TURN as optional SaaS add-on |
| Agent burnout model false positives cause HR concerns | High | Medium | Default to "Watch" threshold rather than "At Risk" until model matures; always frame as "workload indicator" not "HR flag" |
| GPU requirement for fine-tuning limits local LLM adoption | Medium | High | Ensure CPU-based LoRA fine-tuning works (slower); provide realistic hardware requirement documentation |
| NPS survey fatigue reduces response rate below 20% target | Medium | Medium | Enforce 90-day cooldown; A/B test email subject lines; embed score in email body (one-click) |
| Gamification perceived as surveillance/micromanagement | High | Medium | Make leaderboard opt-out easy; weight quality metrics not just volume; agent badges are visible to agent by default but can be hidden |
| WebRTC compatibility issues in enterprise network environments | Medium | Medium | Document TURN configuration; provide connection diagnostics tool; fallback to phone number if WebRTC fails |
| Predictive churn model insufficient data in early deployment | Medium | Low | Require minimum 90 days + 100 tickets before showing churn scores; show data-sufficiency warning otherwise |

---

## Appendix A: Integration with Phase 3 Features

Phase 4 builds directly on Phase 3 deliverables:

| Phase 3 Feature | How Phase 4 Uses It |
|-----------------|---------------------|
| QA Scoring (Story P3.6) | Gamification: QA Gold badge, QA metric in leaderboard composite score |
| Autonomous AI Agent (Story P3.10) | Voice: AI Agent handles voicemail-to-ticket triage; LLM Marketplace: AI Agent uses fine-tuned local model |
| Workforce Management (Story P3.5) | Predictive: burnout model features include WFM schedule data (after-hours activity vs. schedule) |
| Service Catalog (Story P3.4) | NPS/CES: CES survey triggered on service request fulfillment; NPS measures catalog satisfaction |
| Audit Logging (Story P3.8) | Voice: all call events logged to HD Audit Log; LLM Marketplace: model installs and fine-tune jobs audited |

---

## Appendix B: Competitive Parity Summary After Phase 4

| Competitor | Pre-Phase 4 | Post-Phase 4 | Key Remaining Gaps |
|------------|-------------|--------------|-------------------|
| Freshdesk | ~95% | ~98% | Mobile native app, community forums |
| Zoho Desk | ~95% | ~98% | Mobile native app |
| Zendesk | ~80% | ~90% | App marketplace (1500+ apps), Sunshine CRM platform depth |
| Jira SM | ~80% | ~85% | DevOps pipeline integration, Confluence knowledge base depth |
| ServiceNow | ~60% | ~75% | GRC module, HR Service Delivery, platform configurability at enterprise scale |
| Intercom | ~75% | ~85% | Proactive behavior-based messaging, in-app product tours |

**Net result:** Phase 4 completes the innovation roadmap. Frappe Helpdesk becomes the **only open-source helpdesk platform** offering voice/video, local LLM fine-tuning, predictive agent wellbeing analytics, and enterprise gamification — at zero per-seat SaaS cost.
