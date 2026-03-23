# Story: Story 2.2: Automation Rule Builder UI

Status: done
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

**Completed:** 2026-03-23T21:18:16.874Z

king correctly.Now running the mandatory POST-TASK VERIFICATION:All checks pass. Let me update the sprint status file:Now run the final full verification check:Story 2.2 is complete. Here's the summary:

---

**Story 2.2: Automation Rule Builder UI — DONE**

**All 10 ACs verified:**

| # | AC | Status |
|---|---|---|
| 1 | AutomationList page at `/helpdesk/automations` | ✅ |
| 2 | AutomationBuilder at `/helpdesk/automations/new` + `/:id` with WHEN/IF/THEN | ✅ |
| 3 | RuleTriggerSelect with 10 triggers (cards with icons + descriptions) | ✅ |
| 4 | RuleConditionBuilder with 7 operators, AND/OR toggle, is_set hides value | ✅ |
| 5 | RuleActionList with 10 action types, contextual inputs, up/down reorder | ✅ |
| 6 | Save validates → `frappe.client.insert`/`set_value` | ✅ |
| 7 | Enable/disable toggle (builder sidebar + list inline) | ✅ |
| 8 | Test Rule modal → `test_rule` API → per-condition match/fail results | ✅ |
| 9 | Routes registered, "Automations" sidebar entry (Lucide Zap icon) | ✅ |
| 10 | 44/44 component tests pass (vitest 4.1.1) | ✅ |

**Key technical notes:**
- `TRIGGER_OPTIONS` / `ACTION_OPTIONS` extracted to separate `.ts` files (Vue `<script setup>` cannot use `export const`)
- `vi.mock` factory hoisting: import mocked modules after `vi.mock()` declarations
- All pages return HTTP 200; frontend built in 28.9s; API returns expected 403 for unauthenticated requests (identical to all other whitelisted Frappe methods)
- Sprint status updated: `27-story-2-2` → `review`

### Change Log

_(Updated by agent during implementation)_

### File List

_(Updated by agent — list all files created or modified)_
