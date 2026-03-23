# Story 2.1: Automation Rule DocType and Engine Core

Status: ready-for-dev

## Story

As an administrator,
I want to create automation rules with triggers, conditions, and actions,
so that routine ticket operations happen automatically.

## Acceptance Criteria

1. **HD Automation Rule DocType exists** with all required fields: `name`, `description`, `enabled` (Check), `trigger_type` (Select), `conditions` (JSON), `actions` (JSON), `priority_order` (Int) — and is accessible via REST API.

2. **Trigger evaluation speed**: Given a rule with trigger `ticket_created` and conditions `[{"field": "priority", "operator": "equals", "value": "Urgent"}]`, when a new Urgent ticket is created, conditions are evaluated within 100ms (NFR-P-06) and matching actions are executed.

3. **Priority-ordered execution**: When multiple rules match the same ticket event, rules execute in ascending `priority_order` (lower number = higher priority), completing all matched rules before returning.

4. **Loop detection**: When more than 5 automation rule executions occur for the same ticket within a 1-minute window, the engine stops further execution and logs a warning to prevent infinite cascades.

5. **Auto-disable on consecutive failures**: When a rule fails 10 consecutive times, the engine automatically sets `enabled = 0` on the rule and logs a warning (NFR-A-03).

6. **`hooks.py` wired**: The `on_update` doc event for `HD Ticket` invokes the automation engine so rules are evaluated on every ticket save.

7. **Trigger registry**: A trigger registry in `triggers.py` maps event names (`ticket_created`, `ticket_updated`, `ticket_assigned`, `ticket_resolved`, `ticket_reopened`) to their corresponding Frappe doc event hooks.

8. **Condition evaluator**: Supports operators `equals`, `not_equals`, `contains`, `greater_than`, `less_than`, `is_set`, `is_not_set` against HD Ticket fields, with AND/OR logical grouping.

9. **Action executors**: Supports at minimum: `assign_to_agent`, `assign_to_team`, `set_priority`, `set_status`, `add_tag`, `add_internal_note`.

10. **Security**: Automation Rules are restricted to `System Manager` or `HD Admin` role (NFR-SE-04). Only these roles can create, edit, or delete rules.

11. **Unit tests**: Unit tests exist for engine, conditions, actions, and safety guards with at least 80% coverage (NFR-M-01).

12. **`automation_enabled` feature flag**: The engine checks the `automation_enabled` flag in HD Settings and skips evaluation when disabled (AR-06).

## Tasks / Subtasks

- [ ] **Task 1: Create HD Automation Rule DocType** (AC: #1, #10)
  - [ ] 1.1 Create `helpdesk/helpdesk/doctype/hd_automation_rule/` directory with `__init__.py`
  - [ ] 1.2 Create `hd_automation_rule.json` with fields: `name` (Data, reqd), `description` (Text), `enabled` (Check, default 1), `trigger_type` (Select, reqd), `conditions` (JSON), `actions` (JSON), `priority_order` (Int, default 10)
  - [ ] 1.3 Create `hd_automation_rule.py` controller with `validate()` method that ensures `conditions` and `actions` are valid JSON arrays
  - [ ] 1.4 Set DocType permissions: System Manager (full), HD Admin (full), HD Agent (read-only)
  - [ ] 1.5 Create `test_hd_automation_rule.py` with basic CRUD tests
  - [ ] 1.6 Add migration patch in `helpdesk/patches/v1_phase1/` if needed

- [ ] **Task 2: Create automation engine package** (AC: #2, #3, #6, #7, #12)
  - [ ] 2.1 Create `helpdesk/helpdesk/automation/__init__.py`
  - [ ] 2.2 Create `triggers.py` — trigger type registry mapping event names to Frappe doc event hooks; define `TRIGGER_TYPES` constant list with at minimum: `ticket_created`, `ticket_updated`, `ticket_assigned`, `ticket_resolved`, `ticket_reopened`
  - [ ] 2.3 Create `engine.py` — core `AutomationEngine` class with `evaluate(ticket, trigger_type)` method: fetch enabled rules for trigger, sort by `priority_order`, invoke condition evaluator, invoke action executors, record execution in safety module
  - [ ] 2.4 Wire `hooks.py` `doc_events` entry for `HD Ticket` `on_update` to call `helpdesk.helpdesk.automation.engine.on_ticket_update`; add `after_insert` for `ticket_created` trigger

- [ ] **Task 3: Implement condition evaluator** (AC: #2, #8)
  - [ ] 3.1 Create `conditions.py` — `ConditionEvaluator` class with `evaluate(ticket, conditions: list) -> bool` method
  - [ ] 3.2 Implement operators: `equals`, `not_equals`, `contains`, `greater_than`, `less_than`, `is_set`, `is_not_set`
  - [ ] 3.3 Implement `AND` grouping (default, all conditions must match) and `OR` grouping flag on condition group
  - [ ] 3.4 Validate condition JSON schema on `HD Automation Rule` save; throw `frappe.ValidationError` for malformed input
  - [ ] 3.5 Write unit tests in `test_conditions.py` for each operator and logical grouping combination

- [ ] **Task 4: Implement action executors** (AC: #9)
  - [ ] 4.1 Create `actions.py` — `ActionExecutor` class with `execute(ticket, actions: list)` method and dispatcher
  - [ ] 4.2 Implement `assign_to_agent` action: set `assigned_to` field on ticket
  - [ ] 4.3 Implement `assign_to_team` action: set `agent_group` field on ticket
  - [ ] 4.4 Implement `set_priority` action: set `priority` field on ticket
  - [ ] 4.5 Implement `set_status` action: set `status` field on ticket
  - [ ] 4.6 Implement `add_tag` action: append tag to ticket via Frappe tags
  - [ ] 4.7 Implement `add_internal_note` action: create internal communication on ticket
  - [ ] 4.8 Write unit tests in `test_actions.py` for each action type

- [ ] **Task 5: Implement safety module** (AC: #4, #5)
  - [ ] 5.1 Create `safety.py` — `SafetyGuard` class
  - [ ] 5.2 Implement loop detection: use Redis counter key `automation:loop:{ticket_name}` with 60-second TTL; if counter >= 5, call `frappe.log_error()` with warning and return `False` to block execution
  - [ ] 5.3 Implement consecutive failure tracking: maintain `failure_count` on `HD Automation Rule`; after 10 consecutive failures, set `enabled = 0` and log error
  - [ ] 5.4 Implement execution timeout guard: wrap individual action execution in try/except with 30-second timeout signal
  - [ ] 5.5 Write unit tests in `test_safety.py` for loop detection, auto-disable, and timeout behaviour

- [ ] **Task 6: `automation_enabled` feature flag check** (AC: #12)
  - [ ] 6.1 In `engine.py`, read `frappe.db.get_single_value("HD Settings", "automation_enabled")` at the start of `evaluate()`; return early if `0`
  - [ ] 6.2 Ensure `automation_enabled` Check field exists in `HD Settings` (add if missing, default `1`)

- [ ] **Task 7: Write integration tests** (AC: #2, #3, #4)
  - [ ] 7.1 Create `test_engine.py` — integration test creating a rule, creating an Urgent ticket, asserting the action fired and ticket field changed
  - [ ] 7.2 Test priority ordering: create two rules with same trigger, confirm lower `priority_order` fires first
  - [ ] 7.3 Test loop detection end-to-end: trigger 6 rapid evaluations, confirm 6th is blocked

## Dev Notes

### Architecture Reference (ADR-14)

The automation engine follows the pipeline defined in Architecture ADR-14:

```
Ticket Event (create/update/resolve/etc.)
    |
    v
Rule Fetcher (get enabled rules matching trigger type, ordered by priority_order ASC)
    |
    v
Safety Guard (check loop counter in Redis)
    |
    v
Condition Evaluator (evaluate AND/OR conditions against ticket fields)
    |
    v
Action Executor (execute matched actions)
    |
    v
Execution Logger (log results to HD Automation Log — Story 2.4)
```

### Key Constraints

- **Performance**: Each condition evaluation must complete within 100ms (NFR-P-06). Use a single `frappe.db.get_list` call to fetch all enabled rules for a trigger type rather than N individual lookups.
- **Background Queues**: Automation rule evaluation uses the `default` Redis Queue (ADR-12). For heavy actions (e.g., send_email), enqueue separately via `frappe.enqueue()`.
- **Loop Detection**: Uses Redis (`frappe.cache()`) with key `automation:loop:{ticket_name}` and 60-second TTL. Increment on each execution; block when >= 5.
- **Security**: Use `frappe.only_for(["System Manager", "HD Admin"])` in the DocType controller `validate()` to restrict write access (NFR-SE-04).
- **Feature Flag**: `automation_enabled` must be checked at engine entry point (AR-06).

### JSON Field Conventions (from Architecture doc)

Conditions format:
```json
[
  {"field": "priority", "operator": "equals", "value": "Urgent"},
  {"field": "agent_group", "operator": "is_not_set", "value": null}
]
```

Actions format:
```json
[
  {"type": "assign_to_team", "value": "Support L2"},
  {"type": "add_internal_note", "value": "Auto-escalated due to Urgent priority"}
]
```

### `hooks.py` Integration

```python
# hooks.py — doc_events
doc_events = {
    "HD Ticket": {
        "after_insert": "helpdesk.helpdesk.automation.engine.on_ticket_created",
        "on_update": "helpdesk.helpdesk.automation.engine.on_ticket_updated",
    }
}
```

### DocType Structure Pattern

Follow the standard Frappe pattern (Architecture doc, Implementation Patterns):

```
helpdesk/helpdesk/doctype/hd_automation_rule/
├── __init__.py
├── hd_automation_rule.json       # DocType schema
├── hd_automation_rule.py         # Controller
└── test_hd_automation_rule.py    # Unit tests
```

### Automation Package Structure

```
helpdesk/helpdesk/automation/
├── __init__.py
├── engine.py          # AutomationEngine.evaluate(); on_ticket_created(); on_ticket_updated()
├── conditions.py      # ConditionEvaluator.evaluate(ticket, conditions) -> bool
├── actions.py         # ActionExecutor.execute(ticket, actions)
├── triggers.py        # TRIGGER_TYPES list; trigger-to-hook mapping
└── safety.py          # SafetyGuard: loop detection, auto-disable, timeout
```

### Relevant Existing Patterns

- **doc_events hook entry point**: See existing `helpdesk/helpdesk/overrides/hd_ticket.py` for pattern — functions receive `(doc, method)` signature from Frappe
- **frappe.cache() usage**: Use `frappe.cache().get_value(key)` / `frappe.cache().set_value(key, val, expires_in_sec=60)` for Redis loop counter
- **frappe.enqueue()**: Use `queue="default"` for automation evaluation tasks
- **Permissions**: `frappe.only_for(roles)` or `frappe.has_permission(doctype, "write", throw=True)` in controller

### HD Settings Field

Add `automation_enabled` Check field to `HD Settings` if not present:
```json
{
  "fieldname": "automation_enabled",
  "fieldtype": "Check",
  "label": "Enable Automation Rules",
  "default": "1"
}
```

### NFR References

| NFR | Requirement | Implementation Note |
|-----|-------------|---------------------|
| NFR-P-06 | Rule evaluation < 100ms per rule per ticket event | Single DB fetch for enabled rules; no N+1 queries |
| NFR-SE-04 | Automation rules restricted to System Manager / HD Admin | `frappe.only_for()` in DocType controller |
| NFR-A-03 | Auto-disable rules after 10 consecutive failures | `failure_count` field on DocType + safety.py check |
| NFR-M-01 | 80% unit test coverage on all new backend code | Tests for engine, conditions, actions, safety |
| NFR-S-04 | Process 1000 rule evaluations/minute | `default` queue; non-blocking async via `frappe.enqueue()` |

### Project Structure Notes

- **Alignment**: New `automation/` package placed under `helpdesk/helpdesk/` following existing override and channel package patterns
- **Naming**: DocType uses `HD ` prefix per AR-02; table auto-named `tabHD Automation Rule` by Frappe
- **API module**: `helpdesk/api/automation.py` for whitelisted methods (`test_rule`, `toggle_rule`) — these are Story 2.2 scope but the engine's dry-run flag should be supported from day 1
- **Patches**: If `HD Settings` needs the `automation_enabled` field, add a patch in `helpdesk/patches/v1_phase1/add_automation_settings_field.py`
- **No frontend in this story**: UI components (`AutomationList.vue`, `AutomationBuilder.vue`) are Story 2.2 scope

### References

- [Source: _bmad-output/planning-artifacts/architecture.md#ADR-14: Automation Rule Evaluation Engine]
- [Source: _bmad-output/planning-artifacts/architecture.md#ADR-02: New DocType Schema for Phase 1]
- [Source: _bmad-output/planning-artifacts/architecture.md#ADR-01: Extend HD Ticket Rather Than Separate DocTypes]
- [Source: _bmad-output/planning-artifacts/architecture.md#ADR-12: Background Job Architecture]
- [Source: _bmad-output/planning-artifacts/architecture.md#Implementation Patterns -- Naming Patterns]
- [Source: _bmad-output/planning-artifacts/architecture.md#Format Patterns -- JSON Field Conventions]
- [Source: _bmad-output/planning-artifacts/epics.md#Epic 2: Story 2.1]
- [Source: _bmad-output/planning-artifacts/epics.md#Non-Functional Requirements: NFR-P-06, NFR-SE-04, NFR-A-03, NFR-M-01, NFR-S-04]
- [Source: _bmad-output/planning-artifacts/epics.md#Additional Requirements: AR-02, AR-03, AR-06]

## Dev Agent Record

### Agent Model Used

claude-opus-4-5

### Debug Log References

### Completion Notes List

### File List

- `helpdesk/helpdesk/doctype/hd_automation_rule/__init__.py`
- `helpdesk/helpdesk/doctype/hd_automation_rule/hd_automation_rule.json`
- `helpdesk/helpdesk/doctype/hd_automation_rule/hd_automation_rule.py`
- `helpdesk/helpdesk/doctype/hd_automation_rule/test_hd_automation_rule.py`
- `helpdesk/helpdesk/automation/__init__.py`
- `helpdesk/helpdesk/automation/engine.py`
- `helpdesk/helpdesk/automation/conditions.py`
- `helpdesk/helpdesk/automation/actions.py`
- `helpdesk/helpdesk/automation/triggers.py`
- `helpdesk/helpdesk/automation/safety.py`
- `helpdesk/helpdesk/automation/test_engine.py`
- `helpdesk/helpdesk/automation/test_conditions.py`
- `helpdesk/helpdesk/automation/test_actions.py`
- `helpdesk/helpdesk/automation/test_safety.py`
- `helpdesk/hooks.py` (modify: add doc_events entries)
- `helpdesk/helpdesk/doctype/hd_settings/hd_settings.json` (modify: add automation_enabled field)
- `helpdesk/patches/v1_phase1/add_automation_settings_field.py` (if HD Settings needs patching)
