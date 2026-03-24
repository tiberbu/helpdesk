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

- [x] WHEN section: 10+ triggers (ticket_created, ticket_updated, ticket_assigned, ticket_resolved, ticket_reopened, sla_warning, sla_breached, csat_received, chat_started, chat_ended)
- [x] IF section: conditions with field/operator/value supporting AND/OR grouping
- [x] THEN section: 10+ actions (assign_to_agent, assign_to_team, set_priority, set_status, set_category, add_tag, send_email, send_notification, add_internal_note, trigger_webhook)
- [x] Test Rule (dry-run) shows evaluation results without executing

## Tasks / Subtasks

- [x] Create AutomationList.vue page at desk/src/pages/automations/
- [x] Create AutomationBuilder.vue page with WHEN/IF/THEN sections
- [x] Create RuleConditionBuilder.vue, RuleActionList.vue, RuleTriggerSelect.vue components
- [x] Implement dry-run API endpoint at helpdesk/api/automation.py
- [x] Add routes for /helpdesk/automations and /helpdesk/automations/:id
- [x] Write component tests (44/44 passing)

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

- Created `desk/src/pages/automations/AutomationList.vue` — lists all HD Automation Rules with trigger badge, enabled toggle, priority, edit/delete; admin-only access guard
- Created `desk/src/pages/automations/AutomationBuilder.vue` — WHEN/IF/THEN builder with left sidebar (rule_name, description, enabled, priority_order) and Test Rule dry-run modal
- Created `desk/src/components/automation/RuleTriggerSelect.vue` — 10 trigger options as clickable icon cards
- Created `desk/src/components/automation/triggerOptions.ts` — extracted TRIGGER_OPTIONS (required because `<script setup>` cannot use `export const`)
- Created `desk/src/components/automation/RuleConditionBuilder.vue` — field/operator/value rows with ALL/ANY toggle, value hidden for is_set/is_not_set
- Created `desk/src/components/automation/RuleActionList.vue` — 10 action types with contextual value inputs and up/down reorder buttons
- Created `desk/src/components/automation/actionOptions.ts` — extracted ACTION_OPTIONS, PRIORITY_OPTIONS, STATUS_OPTIONS
- Created `helpdesk/api/automation.py` — `test_rule` (dry-run), `toggle_rule`, `get_execution_stats` endpoints
- Modified `helpdesk/helpdesk/automation/engine.py` — added `dry_run=True` flag, `_dry_run_rule()`, `_fetch_single_rule()`
- Modified `desk/src/router/index.ts` — added `/automations` and `/automations/:id` routes
- Modified `desk/src/components/layouts/layoutSettings.ts` — added "Automations" sidebar entry with LucideZap icon
- Created `desk/vitest.config.ts` — vitest config with icon stub plugin and jsdom environment
- Created `desk/src/test-setup.ts` — global mock setup for frappe-ui, vue-router, auth store, translation
- Created `desk/src/__mocks__/icon.ts` — stub component for ~icons/ imports
- Created 5 component test files (44 tests total, all passing)
- Modified `desk/package.json` — added `test` and `test:watch` scripts

### File List

- `desk/src/pages/automations/AutomationList.vue` (new)
- `desk/src/pages/automations/AutomationBuilder.vue` (new)
- `desk/src/pages/automations/__tests__/AutomationList.spec.ts` (new)
- `desk/src/pages/automations/__tests__/AutomationBuilder.spec.ts` (new)
- `desk/src/components/automation/RuleTriggerSelect.vue` (new)
- `desk/src/components/automation/triggerOptions.ts` (new)
- `desk/src/components/automation/RuleConditionBuilder.vue` (new)
- `desk/src/components/automation/RuleActionList.vue` (new)
- `desk/src/components/automation/actionOptions.ts` (new)
- `desk/src/components/automation/__tests__/RuleTriggerSelect.spec.ts` (new)
- `desk/src/components/automation/__tests__/RuleConditionBuilder.spec.ts` (new)
- `desk/src/components/automation/__tests__/RuleActionList.spec.ts` (new)
- `desk/src/test-setup.ts` (new)
- `desk/src/__mocks__/icon.ts` (new)
- `desk/vitest.config.ts` (new)
- `desk/package.json` (modified)
- `desk/src/router/index.ts` (modified)
- `desk/src/components/layouts/layoutSettings.ts` (modified)
- `helpdesk/api/automation.py` (new)
- `helpdesk/helpdesk/automation/engine.py` (modified)
