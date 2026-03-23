# Story: Story 2.1: Automation Rule DocType and Engine Core

Status: in-progress
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

- [ ] HD Automation Rule DocType with name, description, enabled, trigger type, conditions (JSON), actions (JSON), priority order
- [ ] Given trigger ticket_created and conditions [priority equals Urgent], when new Urgent ticket is created, conditions evaluated within 100ms and actions executed
- [ ] Multiple matching rules execute in priority order (lower number = higher priority)
- [ ] Loop detection: more than 5 executions for same ticket within 1 minute stops execution with warning

## Tasks / Subtasks

- [ ] Create HD Automation Rule DocType with all specified fields
- [ ] Implement automation engine at helpdesk/helpdesk/automation/engine.py
- [ ] Implement condition evaluator at helpdesk/helpdesk/automation/conditions.py
- [ ] Implement action executors at helpdesk/helpdesk/automation/actions.py
- [ ] Implement trigger registry at helpdesk/helpdesk/automation/triggers.py
- [ ] Implement safety module (loop detection, throttling) at helpdesk/helpdesk/automation/safety.py
- [ ] Wire doc_events in hooks.py for on_update rule evaluation
- [ ] Write unit tests for engine, conditions, actions, and safety guards

## Dev Notes



### References

- Task source: Claude Code Studio task #26

## Dev Agent Record

### Agent Model Used

sonnet

### Completion Notes List

_(Updated by agent on completion)_

### Change Log

_(Updated by agent during implementation)_

### File List

_(Updated by agent — list all files created or modified)_
