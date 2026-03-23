# Story 2.3: SLA-Based Automation Triggers

Status: ready-for-dev

## Story

As an administrator,
I want to trigger automations based on SLA events (warnings and breaches),
so that at-risk tickets get proactive attention automatically.

## Acceptance Criteria

1. **`sla_warning` trigger fires at configurable thresholds**: Given an SLA has warning thresholds configured (default: 30, 15, 5 minutes before breach), when a ticket reaches any warning threshold during the SLA monitor cron run (every 5 min), the `sla_warning` trigger fires and all matching enabled automation rules are evaluated by the automation engine.

2. **`sla_breached` trigger fires on breach**: Given an SLA breach occurs (the `resolution_by` time is exceeded), when the SLA monitor cron detects the breach, the `sla_breached` trigger fires and all matching enabled automation rules are evaluated by the automation engine.

3. **`sla_warning` and `sla_breached` are registered trigger types**: Both trigger types are present in the `TRIGGER_TYPES` constant in `triggers.py` and available as selectable trigger options in the automation engine (compatible with Story 2.2 builder UI which lists them as valid triggers).

4. **Automation rule actions execute on SLA triggers**: Given an automation rule has `trigger_type = "sla_warning"` and `actions = [{"type": "assign_to_team", "value": "Escalation"}]`, when a ticket's SLA warning fires, the automation engine executes the action and the ticket's `agent_group` is updated to "Escalation".

5. **In-app notification on `sla_warning`**: Given an `sla_warning` fires for a ticket that has an assigned agent (`assigned_to` is set), when the SLA monitor processes the warning, the assigned agent receives an in-app notification (delivered via Socket.IO to the `agent:{agent_email}` room) with a payload indicating the ticket name, SLA threshold crossed, and time remaining.

6. **Threshold state deduplication**: Given a ticket has already fired the `sla_warning` trigger for the 30-minute threshold, when the SLA monitor runs again (5 min later, now 25 min before breach), the 30-minute threshold does NOT fire again. Each threshold (30, 15, 5 min) fires exactly once per SLA cycle per ticket.

7. **Configurable warning thresholds**: The warning threshold minutes (default: 30, 15, 5) are stored as a JSON list field `sla_warning_thresholds` in HD Settings (or on `HD Service Level Agreement`) and the SLA monitor reads them dynamically, not hardcoded.

8. **Integration test: end-to-end SLA trigger -> rule execution**: An integration test creates an automation rule with trigger `sla_warning`, creates a ticket near SLA breach, runs the monitor check, and asserts that the rule's action was executed and an `HD Automation Log` entry was created (Status: success).

9. **`automation_enabled` feature flag respected**: When the `automation_enabled` flag in HD Settings is `0`, no automation rules are evaluated when SLA events fire (consistent with Story 2.1 engine behavior).

10. **Unit tests with minimum 80% coverage** on all new/modified backend code in `sla_monitor.py`, `triggers.py`, and the notification helper (NFR-M-01).

## Tasks / Subtasks

- [ ] **Task 1: Register `sla_warning` and `sla_breached` trigger types** (AC: #3)
  - [ ] 1.1 In `helpdesk/helpdesk/automation/triggers.py`, add `"sla_warning"` and `"sla_breached"` to the `TRIGGER_TYPES` constant list
  - [ ] 1.2 Add docstrings/comments in `triggers.py` clarifying that these triggers are fired externally by the SLA monitor (not via `doc_events` like ticket triggers) and that the engine's `evaluate(ticket, trigger_type)` method is called directly by the cron job
  - [ ] 1.3 Verify (and add if missing) that `HD Automation Rule`'s `trigger_type` Select field options include `"sla_warning"` and `"sla_breached"` in `hd_automation_rule.json`

- [ ] **Task 2: Add threshold state tracking to prevent duplicate fires** (AC: #6)
  - [ ] 2.1 Determine storage mechanism for fired-threshold state: use Redis via `frappe.cache()` with key pattern `sla:warned:{ticket_name}:{threshold_minutes}` with TTL equal to the ticket's SLA resolution window (or at minimum 24 hours)
  - [ ] 2.2 In `sla_monitor.py`, before firing `sla_warning` for a given threshold, check if the Redis key exists; if it does, skip; if not, set the key and proceed with trigger evaluation
  - [ ] 2.3 On `sla_breached`, set a Redis key `sla:breached:{ticket_name}` to prevent re-firing the breach trigger on subsequent cron runs for the same ticket
  - [ ] 2.4 Clear all `sla:warned:{ticket_name}:*` and `sla:breached:{ticket_name}` keys when a ticket's SLA is reset (e.g., ticket re-opened, SLA policy changed)

- [ ] **Task 3: Integrate SLA monitor with automation engine** (AC: #1, #2, #4, #9)
  - [ ] 3.1 In `helpdesk/helpdesk/doctype/hd_service_level_agreement/sla_monitor.py`, import and call `AutomationEngine.evaluate(ticket_doc, "sla_warning")` after the warning threshold detection block
  - [ ] 3.2 Similarly call `AutomationEngine.evaluate(ticket_doc, "sla_breached")` after the breach detection block
  - [ ] 3.3 Wrap automation engine calls in `try/except Exception` so that automation failures never interrupt SLA monitoring or alert delivery (NFR-A-01: core operations unaffected by automation failures)
  - [ ] 3.4 Pass a `context` dict to the engine `evaluate()` call containing `{"threshold_minutes": N}` for `sla_warning` so that condition rules can optionally filter by threshold (e.g., "only escalate on 5-minute warning")
  - [ ] 3.5 Confirm the `automation_enabled` flag check in `engine.py` returns early if disabled (from Story 2.1 — verify, do not re-implement)

- [ ] **Task 4: Add configurable warning thresholds to HD Settings** (AC: #7)
  - [ ] 4.1 Add `sla_warning_thresholds` JSON field to `HD Settings` DocType (`hd_settings.json`) with default value `[30, 15, 5]`
  - [ ] 4.2 In `sla_monitor.py`, read `frappe.db.get_single_value("HD Settings", "sla_warning_thresholds")` and parse as JSON list; fall back to `[30, 15, 5]` if null/empty
  - [ ] 4.3 Add a migration patch `helpdesk/patches/v1_phase1/add_sla_warning_thresholds_setting.py` that sets the default value on existing installations

- [ ] **Task 5: Deliver in-app notification to assigned agent on `sla_warning`** (AC: #5)
  - [ ] 5.1 Create or extend a notification helper in `helpdesk/helpdesk/automation/` (e.g., `notifications.py`) with a function `notify_agent_sla_warning(ticket_doc, threshold_minutes)` that:
    - Reads `ticket_doc.assigned_to` (skip silently if unassigned)
    - Calls `frappe.realtime.publish("sla_warning", room="agent:{agent_email}", message={...})` with payload: `{"ticket": ticket_doc.name, "subject": ticket_doc.subject, "threshold_minutes": threshold_minutes, "sla_deadline": ticket_doc.resolution_by}`
  - [ ] 5.2 Call `notify_agent_sla_warning()` from `sla_monitor.py` after threshold detection, before automation engine evaluation
  - [ ] 5.3 Also create an `HD Notification` record (or use existing Frappe notification mechanism) so the badge counter updates in the agent's workspace — use the existing notification pattern from `overrides/hd_ticket.py` or `api/agent.py` as reference
  - [ ] 5.4 Write unit test for `notify_agent_sla_warning()` covering: assigned ticket (notification sent), unassigned ticket (no error, skipped silently)

- [ ] **Task 6: Write integration tests** (AC: #8, #10)
  - [ ] 6.1 Create `helpdesk/helpdesk/doctype/hd_service_level_agreement/test_sla_monitor_automation.py`
  - [ ] 6.2 Test: create an `HD Automation Rule` with `trigger_type = "sla_warning"` and `actions = [{"type": "assign_to_team", "value": "Escalation"}]`; create a ticket with SLA expiring in 10 minutes; call `check_sla_breaches()` directly; assert ticket `agent_group` changed to "Escalation" and an `HD Automation Log` entry with `status = "success"` exists
  - [ ] 6.3 Test: create an `HD Automation Rule` with `trigger_type = "sla_breached"`; set ticket SLA to expired (past `resolution_by`); call `check_sla_breaches()`; assert rule action executed and `HD Automation Log` entry created
  - [ ] 6.4 Test threshold deduplication: run `check_sla_breaches()` twice for a ticket at the same warning threshold; assert automation rule fires only once (single `HD Automation Log` entry)
  - [ ] 6.5 Test `automation_enabled = 0`: set flag to disabled; run `check_sla_breaches()`; assert no `HD Automation Log` entries created

- [ ] **Task 7: Verify existing SLA monitor cron wiring** (AC: #1, #2)
  - [ ] 7.1 Confirm `hooks.py` `scheduler_events` has the `*/5 * * * *` cron entry pointing to `helpdesk.helpdesk.doctype.hd_service_level_agreement.sla_monitor.check_sla_breaches` (from Architecture ADR-12); add if missing
  - [ ] 7.2 Confirm or add the breach/warning detection logic in `sla_monitor.py` that identifies tickets where `time_to_resolution` is within threshold windows — this may be partially implemented by Story 4.2 (Proactive SLA Breach Alerts); Story 2.3 extends it to also call the automation engine

## Dev Notes

### Architecture Overview

This story sits at the intersection of two epics: Epic 2 (Automation) and Epic 4 (SLA). The SLA monitor cron (Architecture ADR-12) already runs every 5 minutes and detects warning/breach events. Story 2.3 wires those events into the automation engine (`AutomationEngine.evaluate()` from Story 2.1).

```
SLA Monitor Cron (*/5 * * * *)
    |
    +-- For each at-risk ticket:
    |       |
    |       +-- Warning threshold crossed?
    |       |       |--> notify_agent_sla_warning()     [Task 5]
    |       |       |--> AutomationEngine.evaluate(ticket, "sla_warning")  [Task 3]
    |       |
    |       +-- SLA Breached?
    |               |--> AutomationEngine.evaluate(ticket, "sla_breached")  [Task 3]
    |
    +-- (existing) in-app color-coding & badge updates [Story 4.2 scope]
```

### Dependency on Story 2.1 (Automation Engine Core)

Story 2.3 requires the `AutomationEngine` from Story 2.1 to already be implemented. The `evaluate(ticket, trigger_type)` method must exist and support any trigger type string (not just `ticket_created`, `ticket_updated`, etc.). The `sla_warning` and `sla_breached` types are purely additive entries in `TRIGGER_TYPES`.

### Dependency on Story 4.2 (Proactive SLA Breach Alerts)

Story 4.2 implements the core SLA monitor detection logic (detecting tickets near breach, sending agent notifications). Story 2.3 extends `sla_monitor.py` — it does NOT duplicate alert logic. If Story 4.2 is not yet merged, this story must stub out the minimal detection logic. The integration point is:

```python
# sla_monitor.py — after existing alert notification block
try:
    from helpdesk.helpdesk.automation.engine import AutomationEngine
    engine = AutomationEngine()
    engine.evaluate(ticket_doc, "sla_warning", context={"threshold_minutes": threshold})
except Exception:
    frappe.log_error(frappe.get_traceback(), "SLA Automation Trigger Failed")
```

### Threshold Deduplication — Redis Key Pattern

```python
# Set when threshold first fires
cache_key = f"sla:warned:{ticket_name}:{threshold_minutes}"
frappe.cache().set_value(cache_key, 1, expires_in_sec=86400)  # 24-hour TTL

# Check before firing
if frappe.cache().get_value(cache_key):
    continue  # Already fired for this threshold
```

Use `frappe.cache()` (Redis) — consistent with Story 2.1's loop detection pattern (`automation:loop:{ticket_name}`).

### Real-time Notification Pattern

Socket.IO room naming from Architecture doc (Communication Patterns):
- `agent:{agent_email}` — private agent notification channel

```python
# Deliver in-app SLA warning to assigned agent
frappe.publish_realtime(
    event="sla_warning",
    message={
        "ticket": ticket.name,
        "subject": ticket.subject,
        "threshold_minutes": threshold_minutes,
        "sla_deadline": str(ticket.resolution_by),
    },
    room=f"agent:{ticket.assigned_to}",
)
```

Note: `frappe.publish_realtime()` is the standard call pattern in Frappe; `frappe.realtime.publish()` is equivalent.

### Automation Context Metadata

Pass threshold context so rules can be threshold-specific:

```python
# engine.evaluate() signature extended to support optional context dict
engine.evaluate(ticket_doc, "sla_warning", context={"threshold_minutes": 15})
```

The `ConditionEvaluator` in `conditions.py` may need a minor extension to support evaluating against `context` fields (e.g., `{"field": "threshold_minutes", "operator": "equals", "value": "15"}`). This is an enhancement — implement if time allows; otherwise all `sla_warning` rules fire regardless of which threshold triggered.

### SLA Warning Thresholds — HD Settings Field

```json
{
  "fieldname": "sla_warning_thresholds",
  "fieldtype": "JSON",
  "label": "SLA Warning Thresholds (minutes before breach)",
  "description": "List of minutes before SLA breach to fire warning triggers. Default: [30, 15, 5]",
  "default": "[30, 15, 5]"
}
```

### Key Files to Create / Modify

| File | Action | Purpose |
|------|--------|---------|
| `helpdesk/helpdesk/automation/triggers.py` | Modify | Add `sla_warning`, `sla_breached` to `TRIGGER_TYPES` |
| `helpdesk/helpdesk/automation/notifications.py` | Create | `notify_agent_sla_warning()` helper |
| `helpdesk/helpdesk/doctype/hd_service_level_agreement/sla_monitor.py` | Modify | Call automation engine + notifications on warning/breach detection |
| `helpdesk/helpdesk/doctype/hd_automation_rule/hd_automation_rule.json` | Modify | Add `sla_warning`, `sla_breached` as `trigger_type` Select options |
| `helpdesk/helpdesk/doctype/hd_settings/hd_settings.json` | Modify | Add `sla_warning_thresholds` JSON field |
| `helpdesk/patches/v1_phase1/add_sla_warning_thresholds_setting.py` | Create | Migration patch for default value |
| `helpdesk/helpdesk/doctype/hd_service_level_agreement/test_sla_monitor_automation.py` | Create | Integration tests |
| `helpdesk/helpdesk/automation/test_notifications.py` | Create | Unit tests for notification helper |
| `helpdesk/hooks.py` | Verify/Modify | Confirm `*/5 * * * *` cron entry exists |

### Relevant Architecture References

- **ADR-12 (Background Job Architecture)**: Defines the `*/5 * * * *` scheduler event pointing to `check_sla_breaches`; `short` queue for SLA notifications
- **ADR-14 (Automation Rule Evaluation Engine)**: Engine pipeline — `evaluate()` called from external sources (not just doc_events) is a supported pattern
- **Communication Patterns (Socket.IO Rooms)**: `agent:{agent_email}` is the canonical private agent channel for SLA warnings
- **ADR-04 (Permission Model)**: SLA monitor runs in background context; no user permission check required for system-initiated automation actions

### Error Isolation Pattern (NFR-A-01)

Automation failures must NEVER interrupt SLA alerting. Always wrap engine calls:

```python
try:
    engine.evaluate(ticket_doc, "sla_warning", context={"threshold_minutes": threshold})
except Exception:
    frappe.log_error(frappe.get_traceback(), f"Automation eval failed for {ticket_doc.name} sla_warning")
    # Continue — do not re-raise
```

### NFR References

| NFR | Requirement | Implementation Approach |
|-----|-------------|------------------------|
| NFR-P-06 | Rule evaluation < 100ms per rule | Engine uses single `frappe.db.get_list` for enabled rules — unchanged from Story 2.1 |
| NFR-A-01 | Core ticketing unaffected by automation failures | try/except around all `engine.evaluate()` calls in `sla_monitor.py` |
| NFR-A-03 | Auto-disable rules after 10 consecutive failures | Inherited from Story 2.1 `safety.py` — no change needed |
| NFR-M-01 | 80% unit test coverage on new backend code | Tests for `notifications.py`, updated `sla_monitor.py`, integration tests |
| NFR-S-04 | 1000 rule evaluations/minute | SLA monitor batches evaluation per ticket; `default` queue for async actions |

### Project Structure Notes

- **Alignment**: `sla_monitor.py` lives in `helpdesk/helpdesk/doctype/hd_service_level_agreement/` per Frappe convention. The notification helper goes in `helpdesk/helpdesk/automation/notifications.py` to keep automation logic co-located.
- **No new DocTypes**: This story requires no new DocTypes. `HD Automation Log` creation on SLA trigger execution is handled automatically by the existing engine (Story 2.1 / Story 2.4 scope).
- **Story 4.2 Coordination**: Story 4.2 (Proactive SLA Breach Alerts) owns the color-coding, badge updates, and email alert delivery. Story 2.3 owns the automation engine invocation and the in-app Socket.IO notification to the assigned agent. If both stories land in the same sprint, coordinate to avoid duplicate notification sends.
- **Scheduler entry**: `hooks.py` cron entry should already exist if Story 4.2 is complete. Verify; do not duplicate the entry.

### References

- [Source: _bmad-output/planning-artifacts/architecture.md#ADR-12: Background Job Architecture]
- [Source: _bmad-output/planning-artifacts/architecture.md#ADR-14: Automation Rule Evaluation Engine]
- [Source: _bmad-output/planning-artifacts/architecture.md#Communication Patterns — Socket.IO Room Strategy]
- [Source: _bmad-output/planning-artifacts/architecture.md#ADR-04: Permission Model Extensions]
- [Source: _bmad-output/planning-artifacts/architecture.md#Process Patterns — Error Handling]
- [Source: _bmad-output/planning-artifacts/epics.md#Epic 2: Story 2.3: SLA-Based Automation Triggers]
- [Source: _bmad-output/planning-artifacts/epics.md#Epic 4: Story 4.2: Proactive SLA Breach Alerts]
- [Source: _bmad-output/planning-artifacts/epics.md#Non-Functional Requirements: NFR-P-06, NFR-A-01, NFR-A-03, NFR-M-01, NFR-S-04]
- [Source: _bmad-output/planning-artifacts/epics.md#Additional Requirements: AR-03, AR-06]
- [Source: _bmad-output/planning-artifacts/prd.md#FR-WA-03: SLA-Based Automation Triggers]
- [Source: _bmad-output/planning-artifacts/prd.md#FR-SL-02: Proactive Breach Alerts]
- [Source: _bmad-output/implementation-artifacts/story-2.1-automation-rule-doctype-and-engine-core.md]

## Dev Agent Record

### Agent Model Used

claude-sonnet-4-5

### Debug Log References

### Completion Notes List

### File List

- `helpdesk/helpdesk/automation/triggers.py` (modify: add `sla_warning`, `sla_breached` to `TRIGGER_TYPES`)
- `helpdesk/helpdesk/automation/notifications.py` (create: `notify_agent_sla_warning()`)
- `helpdesk/helpdesk/automation/test_notifications.py` (create: unit tests)
- `helpdesk/helpdesk/doctype/hd_service_level_agreement/sla_monitor.py` (modify: wire automation engine + notifications)
- `helpdesk/helpdesk/doctype/hd_service_level_agreement/test_sla_monitor_automation.py` (create: integration tests)
- `helpdesk/helpdesk/doctype/hd_automation_rule/hd_automation_rule.json` (modify: add `sla_warning`, `sla_breached` Select options)
- `helpdesk/helpdesk/doctype/hd_settings/hd_settings.json` (modify: add `sla_warning_thresholds` JSON field)
- `helpdesk/patches/v1_phase1/add_sla_warning_thresholds_setting.py` (create: migration patch)
- `helpdesk/hooks.py` (verify/modify: confirm `*/5 * * * *` cron scheduler entry)
