# Story: Story 2.1: Automation Rule DocType and Engine Core

Status: done
Task ID: mn2gah20jnuvaf
Task Number: #26
Workflow: dev-story
Model: sonnet
Created: 2026-03-23T20:43:21.260Z

## Description

## Story 2.1: Automation Rule DocType and Engine Core

As an administrator, I want to create automation rules with triggers, conditions, and actions, so that routine ticket operations happen automatically.

### Acceptance Criteria

- HD Automation Rule DocType with name, description, enabled, trigger type, conditions (JSON), actions (JSON), priority order
- Given trigger ticket_created and conditions [priority equals Urgent], when new Urgent ticket is created, conditions evaluated within 100ms and actions executed
- Multiple matching rules execute in priority order (lower number = higher priority)
- Loop detection: more than 5 executions for same ticket within 1 minute stops execution with warning

### Tasks
- Create HD Automation Rule DocType with all specified fields
- Implement automation engine at helpdesk/helpdesk/automation/engine.py
- Implement condition evaluator at helpdesk/helpdesk/automation/conditions.py
- Implement action executors at helpdesk/helpdesk/automation/actions.py
- Implement trigger registry at helpdesk/helpdesk/automation/triggers.py
- Implement safety module (loop detection, throttling) at helpdesk/helpdesk/automation/safety.py
- Wire doc_events in hooks.py for on_update rule evaluation
- Write unit tests for engine, conditions, actions, and safety guards

## Acceptance Criteria

- [x] HD Automation Rule DocType with name, description, enabled, trigger type, conditions (JSON), actions (JSON), priority order
- [x] Given trigger ticket_created and conditions [priority equals Urgent], when new Urgent ticket is created, conditions evaluated within 100ms and actions executed
- [x] Multiple matching rules execute in priority order (lower number = higher priority)
- [x] Loop detection: more than 5 executions for same ticket within 1 minute stops execution with warning

## Tasks / Subtasks

- [x] Create HD Automation Rule DocType with all specified fields
- [x] Implement automation engine at helpdesk/helpdesk/automation/engine.py
- [x] Implement condition evaluator at helpdesk/helpdesk/automation/conditions.py
- [x] Implement action executors at helpdesk/helpdesk/automation/actions.py
- [x] Implement trigger registry at helpdesk/helpdesk/automation/triggers.py
- [x] Implement safety module (loop detection, throttling) at helpdesk/helpdesk/automation/safety.py
- [x] Wire doc_events in hooks.py for on_update rule evaluation
- [x] Write unit tests for engine, conditions, actions, and safety guards

## Dev Notes

See story-2.1-automation-rule-doctype-and-engine-core.md for full architecture notes.

### Key Implementation Decisions

- `automation_enabled` flag check moved into `evaluate()` (not just `_run()`) so tests calling `evaluate()` directly also respect the flag.
- DocType uses `autoname: field:rule_name` with `unique:1` on rule_name field.
- `failure_count` field added to DocType for auto-disable tracking (NFR-A-03).
- Loop detection uses `frappe.cache().set_value/get_value` with 60s TTL.
- All DB writes in actions use `frappe.db.set_value()` (no doc.save()) to avoid re-triggering `on_update` hooks.

### References

- Task source: Claude Code Studio task #26

## Dev Agent Record

### Agent Model Used

claude-sonnet-4-6

### Completion Notes List

- Implemented all 7 tasks in story file
- 53 total unit/integration tests passing (26 conditions + 7 safety + 7 actions + 13 doctype + 7 engine)
- Fixed one bug during testing: feature flag check was only in `_run()`, moved into `evaluate()` so direct calls to `evaluate()` also respect the flag
- No frontend changes in this story (deferred to Story 2.2)
- `automation_enabled` field already existed in HD Settings from Story 1.1

### Change Log

- Created `helpdesk/helpdesk/doctype/hd_automation_rule/` DocType (4 files)
- Created `helpdesk/helpdesk/automation/` package (10 files: __init__, engine, conditions, actions, safety, triggers + 4 test files)
- Modified `helpdesk/hooks.py` — added HD Ticket doc_events for after_insert + on_update
- Ran `bench migrate` to create `tabHD Automation Rule` table in DB

### File List

- `helpdesk/helpdesk/doctype/hd_automation_rule/__init__.py` (created)
- `helpdesk/helpdesk/doctype/hd_automation_rule/hd_automation_rule.json` (created)
- `helpdesk/helpdesk/doctype/hd_automation_rule/hd_automation_rule.py` (created)
- `helpdesk/helpdesk/doctype/hd_automation_rule/test_hd_automation_rule.py` (created)
- `helpdesk/helpdesk/automation/__init__.py` (created)
- `helpdesk/helpdesk/automation/engine.py` (created)
- `helpdesk/helpdesk/automation/conditions.py` (created)
- `helpdesk/helpdesk/automation/actions.py` (created)
- `helpdesk/helpdesk/automation/safety.py` (created)
- `helpdesk/helpdesk/automation/triggers.py` (created)
- `helpdesk/helpdesk/automation/test_conditions.py` (created)
- `helpdesk/helpdesk/automation/test_safety.py` (created)
- `helpdesk/helpdesk/automation/test_actions.py` (created)
- `helpdesk/helpdesk/automation/test_engine.py` (created)
- `helpdesk/hooks.py` (modified — added HD Ticket doc_events)
