# Story: Story 2.3: SLA-Based Automation Triggers

Status: in-progress
Task ID: mn2gah3kvzvb42
Task Number: #28
Workflow: dev-story
Model: sonnet
Created: 2026-03-23T21:18:17.452Z

## Description

## Story 2.3: SLA-Based Automation Triggers

As an administrator, I want to trigger automations based on SLA events, so that at-risk tickets get proactive attention automatically.

### Acceptance Criteria

- SLA warning thresholds (default 30, 15, 5 min before breach) fire sla_warning trigger for matching automation rules
- SLA breach fires sla_breached trigger
- Example: rule with trigger sla_warning and action assign_to_team: Escalation reassigns ticket
- Assigned agent receives in-app notification on sla_warning

### Tasks
- Integrate SLA monitor cron job with automation trigger system
- Implement sla_warning and sla_breached trigger types
- Wire SLA events to automation engine evaluation
- Add notification delivery for SLA warning events
- Write integration tests for SLA trigger -> automation execution flow

## Acceptance Criteria

- [ ] SLA warning thresholds (default 30, 15, 5 min before breach) fire sla_warning trigger for matching automation rules
- [ ] SLA breach fires sla_breached trigger
- [ ] Example: rule with trigger sla_warning and action assign_to_team: Escalation reassigns ticket
- [ ] Assigned agent receives in-app notification on sla_warning

## Tasks / Subtasks

- [ ] Integrate SLA monitor cron job with automation trigger system
- [ ] Implement sla_warning and sla_breached trigger types
- [ ] Wire SLA events to automation engine evaluation
- [ ] Add notification delivery for SLA warning events
- [ ] Write integration tests for SLA trigger -> automation execution flow

## Dev Notes



### References

- Task source: Claude Code Studio task #28

## Dev Agent Record

### Agent Model Used

sonnet

### Completion Notes List

_(Updated by agent on completion)_

### Change Log

_(Updated by agent during implementation)_

### File List

_(Updated by agent — list all files created or modified)_
