# Story 2.2: Automation Rule Builder UI

Status: ready-for-dev

## Story

As an administrator,
I want to build automation rules using a visual interface,
so that I can configure complex rules without writing code.

## Acceptance Criteria

1. **AutomationList page exists** at route `/helpdesk/automations` (`desk/src/pages/automations/AutomationList.vue`) showing all HD Automation Rules with columns: name, trigger type, enabled toggle, execution count, last fired, actions (edit/delete). Accessible only to System Manager or HD Admin (NFR-SE-04).

2. **AutomationBuilder page exists** at route `/helpdesk/automations/new` and `/helpdesk/automations/:id` (`desk/src/pages/automations/AutomationBuilder.vue`) rendering three distinct sections: **WHEN** (trigger), **IF** (conditions), and **THEN** (actions). New rules start with a blank form; existing rules load their saved configuration.

3. **WHEN (Trigger) section** — implemented as `RuleTriggerSelect.vue` — offers at minimum these 10 triggers via dropdown: `ticket_created`, `ticket_updated`, `ticket_assigned`, `ticket_resolved`, `ticket_reopened`, `sla_warning`, `sla_breached`, `csat_received`, `chat_started`, `chat_ended`. Each trigger displays a human-readable label and description.

4. **IF (Conditions) section** — implemented as `RuleConditionBuilder.vue` — allows adding multiple condition rows, each with three inputs: `field` (select from HD Ticket field list), `operator` (select: equals, not_equals, contains, greater_than, less_than, is_set, is_not_set), and `value` (text/select based on field type). Conditions support AND/OR grouping toggle (defaults to AND). The built condition JSON is validated before save.

5. **THEN (Actions) section** — implemented as `RuleActionList.vue` — allows adding multiple action rows, each with an `action type` dropdown (at minimum 10 actions: `assign_to_agent`, `assign_to_team`, `set_priority`, `set_status`, `set_category`, `add_tag`, `send_email`, `send_notification`, `add_internal_note`, `trigger_webhook`) and a contextual `value` input that adapts per action type (e.g., agent picker for `assign_to_agent`, text field for `add_tag`). Actions are reorderable via drag-and-drop or up/down buttons.

6. **Save rule**: Clicking "Save" persists the rule as an HD Automation Rule document via the Frappe REST API (`/api/resource/HD Automation Rule`). The `conditions` and `actions` are serialized as JSON arrays. Form shows validation errors (missing trigger, empty actions list) before saving. On success, a toast notification confirms "Rule saved."

7. **Enable/Disable toggle**: The builder page shows a toggle switch bound to the `enabled` field. AutomationList shows the same toggle inline per rule. Changes save immediately via PATCH to the REST API.

8. **Test Rule (dry-run)**: Clicking "Test Rule" opens a modal where the user can select a sample ticket. On confirm, the frontend calls `helpdesk.api.automation.test_rule(rule_name, ticket_name)`. The modal then displays step-by-step evaluation: which conditions matched/failed and which actions would execute — without actually executing any actions. The `test_rule` API endpoint must be implemented in `helpdesk/api/automation.py` with `@frappe.whitelist()`.

9. **Route registration**: Routes `/helpdesk/automations` and `/helpdesk/automations/:id` are added to the Vue Router configuration (`desk/src/router.ts` or equivalent), with `automations` as a named route group. Both routes are accessible only to logged-in users with System Manager or HD Admin role.

10. **Component tests**: `vitest`/`vue-test-utils` tests exist for `AutomationList.vue`, `AutomationBuilder.vue`, `RuleConditionBuilder.vue`, `RuleActionList.vue`, and `RuleTriggerSelect.vue`. Tests cover: rendering, adding/removing conditions and actions, trigger selection, save flow (mocked API), and dry-run modal display.

## Tasks / Subtasks

- [ ] **Task 1: Create page directory and AutomationList.vue** (AC: #1, #7, #9)
  - [ ] 1.1 Create `desk/src/pages/automations/` directory
  - [ ] 1.2 Create `AutomationList.vue` using `createListResource("HD Automation Rule")` with columns: name (link to builder), trigger_type (badge), enabled (toggle), execution stats placeholder, edit/delete actions
  - [ ] 1.3 Add `frappe-ui` ListView with search, sort by `priority_order`, and empty state ("No automation rules yet. Create one to get started.")
  - [ ] 1.4 Inline `enabled` toggle calls `PATCH /api/resource/HD Automation Rule/{name}` with `{enabled: 0|1}` immediately
  - [ ] 1.5 "New Rule" button navigates to `/helpdesk/automations/new`; row click navigates to `/helpdesk/automations/:id`
  - [ ] 1.6 Guard page render: if user lacks `HD Admin` and `System Manager` roles, redirect to home with "Access denied" toast

- [ ] **Task 2: Create RuleTriggerSelect.vue** (AC: #3)
  - [ ] 2.1 Create `desk/src/components/automation/RuleTriggerSelect.vue`
  - [ ] 2.2 Define the TRIGGER_OPTIONS constant with 10+ entries: `{ value, label, description }` — all 10 required triggers plus optionally more
  - [ ] 2.3 Render as a styled dropdown (frappe-ui `FormControl` or `Select`) showing label + description in the option slot
  - [ ] 2.4 Emit `update:modelValue` (v-model compatible) with the selected trigger value string
  - [ ] 2.5 Add subtle icon per trigger category (ticket events, SLA events, chat events) using Lucide icons

- [ ] **Task 3: Create RuleConditionBuilder.vue** (AC: #4)
  - [ ] 3.1 Create `desk/src/components/automation/RuleConditionBuilder.vue`
  - [ ] 3.2 Accept `modelValue: Condition[]` prop (array of `{field, operator, value}` objects); emit updates
  - [ ] 3.3 Define `HD_TICKET_FIELDS` constant listing key ticket fields: priority, status, agent_group, assigned_to, category, sub_category, source, subject — with field type metadata for conditional value rendering
  - [ ] 3.4 For each condition row: render `field` dropdown → `operator` dropdown (filtered by field type) → `value` input (text, select, or link picker depending on field)
  - [ ] 3.5 AND/OR group toggle above conditions list; stores `logical_operator: "AND" | "OR"` alongside conditions array in emitted value
  - [ ] 3.6 "Add Condition" button appends a blank condition row; "×" button on each row removes it
  - [ ] 3.7 Validation: highlight rows with incomplete field/operator/value before save attempt

- [ ] **Task 4: Create RuleActionList.vue** (AC: #5)
  - [ ] 4.1 Create `desk/src/components/automation/RuleActionList.vue`
  - [ ] 4.2 Accept `modelValue: Action[]` prop (array of `{type, value}` objects); emit updates
  - [ ] 4.3 Define `ACTION_OPTIONS` constant with 10+ actions, each specifying: `value`, `label`, `valueType` (`agent_link | team_link | select | text | email | url`)
  - [ ] 4.4 Per action row: `type` dropdown → contextual `value` input (link picker for agent/team, priority select for `set_priority`, status select for `set_status`, text for others)
  - [ ] 4.5 "Add Action" button appends new row; "×" removes; up/down arrow buttons reorder (affects execution order)
  - [ ] 4.6 Action type `trigger_webhook` shows a URL text field with URL format validation
  - [ ] 4.7 Action type `send_email` shows to/subject/body fields (minimal; full templating is future scope)

- [ ] **Task 5: Create AutomationBuilder.vue page** (AC: #2, #6, #7, #8)
  - [ ] 5.1 Create `desk/src/pages/automations/AutomationBuilder.vue`
  - [ ] 5.2 On mount: if route has `:id` param, fetch rule via `createResource("HD Automation Rule", id)` and hydrate WHEN/IF/THEN state; if `/new`, initialize empty state
  - [ ] 5.3 Layout: two-column — left sidebar (rule name input, enabled toggle, priority_order input, description textarea, Save/Test/Cancel buttons); right main area with WHEN/IF/THEN sections stacked
  - [ ] 5.4 Compose `RuleTriggerSelect.vue` in the WHEN section, `RuleConditionBuilder.vue` in IF section, `RuleActionList.vue` in THEN section
  - [ ] 5.5 "Save" handler: validate (trigger required, at least 1 action), serialize state to `conditions` / `actions` JSON, POST to `/api/resource/HD Automation Rule` (new) or PUT (edit); show success toast or error banner
  - [ ] 5.6 Enable/disable toggle bound to `enabled` field; included in save payload
  - [ ] 5.7 "Test Rule" button opens `TestRuleModal` (inline or separate component): ticket picker (link field searching HD Ticket), "Run Test" button calling `helpdesk.api.automation.test_rule`, then renders results: per-condition match/no-match badges, per-action would-execute list, overall "Rule would fire: Yes/No" summary
  - [ ] 5.8 "Cancel" / breadcrumb navigates back to `/helpdesk/automations` list
  - [ ] 5.9 Unsaved changes warning: if user navigates away with dirty state, show frappe-ui Dialog confirmation

- [ ] **Task 6: Implement test_rule API endpoint** (AC: #8)
  - [ ] 6.1 In `helpdesk/api/automation.py` (extends Story 2.1's stub), add `@frappe.whitelist()` function `test_rule(rule_name: str, ticket_name: str) -> dict`
  - [ ] 6.2 Load the HD Automation Rule by `rule_name`; load the HD Ticket by `ticket_name`
  - [ ] 6.3 Invoke `AutomationEngine.evaluate(ticket, trigger_type, dry_run=True)` — engine must support `dry_run` flag that runs condition evaluation and action planning without committing changes
  - [ ] 6.4 Return structured response: `{ "would_fire": bool, "conditions": [{"field", "operator", "value", "matched": bool}], "actions": [{"type", "value", "would_execute": bool}], "trigger_type": str }`
  - [ ] 6.5 Restrict to `System Manager` or `HD Admin` roles via `frappe.only_for(["System Manager", "HD Admin"])`
  - [ ] 6.6 Ensure `engine.py` (Story 2.1) `evaluate()` accepts optional `dry_run=False` kwarg: when `True`, skip `ActionExecutor.execute()` and instead return planned actions list

- [ ] **Task 7: Add routes to Vue Router** (AC: #9)
  - [ ] 7.1 Locate the main Vue Router config file (`desk/src/router.ts` or `desk/src/router/index.ts`)
  - [ ] 7.2 Add lazy-loaded route entries:
    ```js
    { path: "/automations", component: () => import("@/pages/automations/AutomationList.vue"), name: "AutomationList" }
    { path: "/automations/:id", component: () => import("@/pages/automations/AutomationBuilder.vue"), name: "AutomationBuilder" }
    ```
  - [ ] 7.3 Add navigation entry (sidebar link) under the admin/settings section pointing to `/helpdesk/automations` — check existing sidebar config pattern

- [ ] **Task 8: Write component tests** (AC: #10)
  - [ ] 8.1 Create `desk/src/pages/automations/__tests__/AutomationList.spec.ts` — test: renders list, inline toggle calls API, "New Rule" button navigates, row click navigates
  - [ ] 8.2 Create `desk/src/pages/automations/__tests__/AutomationBuilder.spec.ts` — test: loads existing rule, Save calls API with correct JSON, Cancel navigates away, unsaved changes dialog
  - [ ] 8.3 Create `desk/src/components/automation/__tests__/RuleTriggerSelect.spec.ts` — test: all 10 triggers present, emits correct value on selection
  - [ ] 8.4 Create `desk/src/components/automation/__tests__/RuleConditionBuilder.spec.ts` — test: add condition, remove condition, AND/OR toggle, validation highlights
  - [ ] 8.5 Create `desk/src/components/automation/__tests__/RuleActionList.spec.ts` — test: add action, remove action, reorder, webhook URL validation

## Dev Notes

### Architecture Reference (ADR-09, ADR-14)

This story is the **frontend layer** for Story 2.1's backend automation engine. The UI translates visual builder state into the JSON condition/action format defined in ADR-14, then persists it to the HD Automation Rule DocType.

**Depends on Story 2.1 being complete** — the `HD Automation Rule` DocType and `AutomationEngine` with `dry_run` support must exist before `test_rule` API can be implemented.

**Frontend data flow:**
```
AutomationBuilder.vue (page state)
    ├── RuleTriggerSelect.vue  → trigger_type: string
    ├── RuleConditionBuilder.vue → conditions: Condition[] (JSON)
    └── RuleActionList.vue     → actions: Action[] (JSON)
         ↓
    Save: POST/PUT /api/resource/HD Automation Rule
    Test: POST helpdesk.api.automation.test_rule
```

### JSON Formats (from Architecture ADR-14)

Conditions JSON (stored in `HD Automation Rule.conditions`):
```json
[
  {"field": "priority", "operator": "equals", "value": "Urgent"},
  {"field": "agent_group", "operator": "is_not_set", "value": null}
]
```

With logical operator wrapper (frontend state):
```json
{
  "logical_operator": "AND",
  "conditions": [
    {"field": "priority", "operator": "equals", "value": "Urgent"}
  ]
}
```

Actions JSON (stored in `HD Automation Rule.actions`):
```json
[
  {"type": "assign_to_team", "value": "Support L2"},
  {"type": "add_internal_note", "value": "Auto-escalated due to Urgent priority"}
]
```

### File Locations (from Architecture ADR-09)

**New files to create:**
```
desk/src/pages/automations/
├── AutomationList.vue
├── AutomationBuilder.vue
└── __tests__/
    ├── AutomationList.spec.ts
    └── AutomationBuilder.spec.ts

desk/src/components/automation/
├── RuleConditionBuilder.vue
├── RuleActionList.vue
├── RuleTriggerSelect.vue
└── __tests__/
    ├── RuleConditionBuilder.spec.ts
    ├── RuleActionList.spec.ts
    └── RuleTriggerSelect.spec.ts
```

**Files to modify:**
```
desk/src/router.ts (or router/index.ts)  — add automation routes
helpdesk/api/automation.py               — add test_rule endpoint
helpdesk/helpdesk/automation/engine.py   — add dry_run flag support
```

### Vue Component Patterns (from Architecture ADR-09)

Follow the existing codebase patterns:

```vue
<script setup lang="ts">
import { ref, computed } from "vue"
import { createResource, createListResource } from "frappe-ui"
import { useRouter, useRoute } from "vue-router"

// Props with TypeScript interfaces
interface Condition {
  field: string
  operator: string
  value: string | null
}

interface Action {
  type: string
  value: string
}

// Data fetching
const rules = createListResource({
  doctype: "HD Automation Rule",
  fields: ["name", "trigger_type", "enabled", "priority_order", "description"],
  orderBy: "priority_order asc",
  auto: true,
})
</script>
```

### API Patterns (from Architecture ADR-08)

```python
# helpdesk/api/automation.py
import frappe
from frappe import _
from helpdesk.helpdesk.automation.engine import AutomationEngine

@frappe.whitelist()
def test_rule(rule_name: str, ticket_name: str) -> dict:
    """Dry-run evaluate an automation rule against a ticket without executing actions."""
    frappe.only_for(["System Manager", "HD Admin"])

    rule = frappe.get_doc("HD Automation Rule", rule_name)
    ticket = frappe.get_doc("HD Ticket", ticket_name)

    engine = AutomationEngine()
    result = engine.evaluate(ticket, rule.trigger_type, dry_run=True, rule_name=rule_name)

    return {
        "would_fire": result.get("would_fire", False),
        "conditions": result.get("conditions_detail", []),
        "actions": result.get("actions_detail", []),
        "trigger_type": rule.trigger_type,
    }
```

### Trigger List (complete, from Epic 2.2 AC)

| Value | Label | Category |
|-------|-------|----------|
| `ticket_created` | Ticket Created | Ticket Events |
| `ticket_updated` | Ticket Updated | Ticket Events |
| `ticket_assigned` | Ticket Assigned | Ticket Events |
| `ticket_resolved` | Ticket Resolved | Ticket Events |
| `ticket_reopened` | Ticket Reopened | Ticket Events |
| `sla_warning` | SLA Warning | SLA Events |
| `sla_breached` | SLA Breached | SLA Events |
| `csat_received` | CSAT Response Received | Feedback Events |
| `chat_started` | Chat Started | Chat Events |
| `chat_ended` | Chat Ended | Chat Events |

### Action List (complete, from Epic 2.2 AC)

| Value | Label | Value Type |
|-------|-------|------------|
| `assign_to_agent` | Assign to Agent | agent link |
| `assign_to_team` | Assign to Team | team link |
| `set_priority` | Set Priority | select: Low/Medium/High/Urgent |
| `set_status` | Set Status | select: Open/Replied/Resolved/Closed |
| `set_category` | Set Category | category link |
| `add_tag` | Add Tag | text |
| `send_email` | Send Email | to/subject/body fields |
| `send_notification` | Send In-App Notification | text (message content) |
| `add_internal_note` | Add Internal Note | textarea |
| `trigger_webhook` | Trigger Webhook | URL text |

### Pinia Store (from Architecture ADR-11)

A lightweight automation store for builder state:

```typescript
// desk/src/stores/automation.ts
import { defineStore } from "pinia"
import { ref } from "vue"

export const useAutomationStore = defineStore("automation", () => {
  const isDirty = ref(false)
  const currentRule = ref(null)

  function markDirty() { isDirty.value = true }
  function markClean() { isDirty.value = false }

  return { isDirty, currentRule, markDirty, markClean }
})
```

### Security Notes (NFR-SE-04, ADR-04)

- AutomationList and AutomationBuilder pages must check user role before render
- `test_rule` API uses `frappe.only_for(["System Manager", "HD Admin"])`
- The HD Automation Rule DocType permissions (from Story 2.1): System Manager + HD Admin = full CRUD; HD Agent = read-only
- Frontend role check pattern: use `frappe.session.user_roles` or the existing `useAuthStore` / `useSessionStore`

### UX Design Requirements (UX-DR-07)

> "Automation rule builder uses visual if-then-else interface with WHEN/IF/THEN sections"

- Each section has a distinct header: **WHEN** (blue badge), **IF** (orange badge), **THEN** (green badge)
- Empty-state prompts per section: "Select a trigger to begin", "Add conditions (optional)", "Add at least one action"
- Drag handles on action rows for reordering
- Dry-run modal shows color-coded results: ✅ condition matched, ❌ condition did not match, 🔵 action would execute

### NFR References

| NFR | Requirement | Implementation Note |
|-----|-------------|---------------------|
| NFR-SE-04 | Automation rules restricted to System Manager / HD Admin | Role check on page render + `frappe.only_for()` on API |
| NFR-U-04 | WCAG 2.1 AA compliance | Use frappe-ui components with ARIA labels on all form controls |
| NFR-U-05 | Full keyboard navigation | Tab order: trigger select → condition rows → action rows → save button |
| NFR-P-06 | Rule evaluation < 100ms | dry_run uses same engine path — no extra latency budget consumed |
| NFR-A-03 | Auto-disable after 10 failures | Builder UI shows warning badge on rules with high failure counts |
| NFR-M-01 | 80% unit test coverage | Component tests for all 5 components + API unit test |

### Relationship to Other Stories

- **Depends on**: Story 2.1 — `HD Automation Rule` DocType and `AutomationEngine` must exist; `engine.py` needs `dry_run` param
- **Enables**: Story 2.3 (SLA triggers) — the builder UI will display `sla_warning` and `sla_breached` triggers already defined in `TRIGGER_OPTIONS`
- **Enables**: Story 2.4 (execution logging) — the list page will show execution stats once Story 2.4's `HD Automation Log` is available

### Project Structure Notes

- **Pages location**: `desk/src/pages/automations/` — new directory following existing convention (e.g., `desk/src/pages/ticket/`, `desk/src/pages/knowledge-base/`)
- **Components location**: `desk/src/components/automation/` — specified by Architecture ADR-09
- **Router file**: locate at `desk/src/router.ts` or `desk/src/router/index.ts` — check existing file; add routes inside the existing routes array without breaking current entries
- **Sidebar nav**: check `desk/src/components/BaseLayout.vue` or similar for sidebar navigation config; add "Automations" link under the admin section
- **Naming**: PascalCase for Vue files (ADR-09 frontend naming), kebab-case routes
- **No new DocType in this story**: Only the `test_rule` API endpoint is new backend scope; DocType itself is Story 2.1

### References

- [Source: _bmad-output/planning-artifacts/architecture.md#ADR-09: Frontend Component Organization]
- [Source: _bmad-output/planning-artifacts/architecture.md#ADR-14: Automation Rule Evaluation Engine]
- [Source: _bmad-output/planning-artifacts/architecture.md#ADR-08: API Design for New Features]
- [Source: _bmad-output/planning-artifacts/architecture.md#ADR-11: State Management for Real-time Features]
- [Source: _bmad-output/planning-artifacts/architecture.md#ADR-04: Permission Model Extensions]
- [Source: _bmad-output/planning-artifacts/architecture.md#Implementation Patterns -- Frontend Naming]
- [Source: _bmad-output/planning-artifacts/architecture.md#Format Patterns -- JSON Field Conventions]
- [Source: _bmad-output/planning-artifacts/epics.md#Epic 2: Story 2.2]
- [Source: _bmad-output/planning-artifacts/epics.md#FR-WA-01]
- [Source: _bmad-output/planning-artifacts/epics.md#Non-Functional Requirements: NFR-SE-04, NFR-U-04, NFR-U-05, NFR-P-06, NFR-M-01]
- [Source: _bmad-output/planning-artifacts/epics.md#UX Design Requirements: UX-DR-07]
- [Source: _bmad-output/implementation-artifacts/story-2.1-automation-rule-doctype-and-engine-core.md]

## Dev Agent Record

### Agent Model Used

(to be filled by dev agent)

### Debug Log References

### Completion Notes List

### File List

- `desk/src/pages/automations/AutomationList.vue` (new)
- `desk/src/pages/automations/AutomationBuilder.vue` (new)
- `desk/src/components/automation/RuleConditionBuilder.vue` (new)
- `desk/src/components/automation/RuleActionList.vue` (new)
- `desk/src/components/automation/RuleTriggerSelect.vue` (new)
- `desk/src/pages/automations/__tests__/AutomationList.spec.ts` (new)
- `desk/src/pages/automations/__tests__/AutomationBuilder.spec.ts` (new)
- `desk/src/components/automation/__tests__/RuleConditionBuilder.spec.ts` (new)
- `desk/src/components/automation/__tests__/RuleActionList.spec.ts` (new)
- `desk/src/components/automation/__tests__/RuleTriggerSelect.spec.ts` (new)
- `desk/src/router.ts` (modify: add automation routes)
- `helpdesk/api/automation.py` (modify: add test_rule endpoint)
- `helpdesk/helpdesk/automation/engine.py` (modify: add dry_run flag to evaluate())
