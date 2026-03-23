# Story: Story 2.2: Automation Rule Builder UI

Status: in-progress
Task ID: mn2gah2sm7zas7
Task Number: #27
Workflow: dev-story
Model: sonnet
Created: 2026-03-23T20:54:29.506Z

## Description

## Story 2.2: Automation Rule Builder UI

As an administrator, I want to build automation rules using a visual interface, so that I can configure complex rules without writing code.

### Acceptance Criteria

- WHEN section: 10+ triggers (ticket_created, ticket_updated, ticket_assigned, ticket_resolved, ticket_reopened, sla_warning, sla_breached, csat_received, chat_started, chat_ended)
- IF section: conditions with field/operator/value supporting AND/OR grouping
- THEN section: 10+ actions (assign_to_agent, assign_to_team, set_priority, set_status, set_category, add_tag, send_email, send_notification, add_internal_note, trigger_webhook)
- Test Rule (dry-run) shows evaluation results without executing

### Tasks
- Create AutomationList.vue page at desk/src/pages/automations/
- Create AutomationBuilder.vue page with WHEN/IF/THEN sections
- Create RuleConditionBuilder.vue, RuleActionList.vue, RuleTriggerSelect.vue components
- Implement dry-run API endpoint at helpdesk/api/automation.py
- Add routes for /helpdesk/automations and /helpdesk/automations/:id
- Write component tests

## Acceptance Criteria

- [ ] WHEN section: 10+ triggers (ticket_created, ticket_updated, ticket_assigned, ticket_resolved, ticket_reopened, sla_warning, sla_breached, csat_received, chat_started, chat_ended)
- [ ] IF section: conditions with field/operator/value supporting AND/OR grouping
- [ ] THEN section: 10+ actions (assign_to_agent, assign_to_team, set_priority, set_status, set_category, add_tag, send_email, send_notification, add_internal_note, trigger_webhook)
- [ ] Test Rule (dry-run) shows evaluation results without executing

## Tasks / Subtasks

- [ ] Create AutomationList.vue page at desk/src/pages/automations/
- [ ] Create AutomationBuilder.vue page with WHEN/IF/THEN sections
- [ ] Create RuleConditionBuilder.vue, RuleActionList.vue, RuleTriggerSelect.vue components
- [ ] Implement dry-run API endpoint at helpdesk/api/automation.py
- [ ] Add routes for /helpdesk/automations and /helpdesk/automations/:id
- [ ] Write component tests

## Dev Notes



### References

- Task source: Claude Code Studio task #27

## Dev Agent Record

### Agent Model Used

sonnet

### Completion Notes List

_(Updated by agent on completion)_

### Change Log

_(Updated by agent during implementation)_

### File List

_(Updated by agent — list all files created or modified)_
