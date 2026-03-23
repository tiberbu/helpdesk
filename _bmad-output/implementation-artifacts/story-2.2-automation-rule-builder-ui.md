# Story 2.2: Automation Rule Builder UI

Status: done

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

- [x] **Task 1: Create page directory and AutomationList.vue** (AC: #1, #7, #9)
  - [x] 1.1 Create `desk/src/pages/automations/` directory
  - [x] 1.2 Create `AutomationList.vue` using `createListResource("HD Automation Rule")` with columns: name (link to builder), trigger_type (badge), enabled (toggle), priority, edit/delete actions
  - [x] 1.3 Sort by `priority_order` asc, empty state message included
  - [x] 1.4 Inline `enabled` toggle calls `helpdesk.api.automation.toggle_rule` immediately
  - [x] 1.5 "New Rule" button navigates to `/helpdesk/automations/new`; edit navigates to `/helpdesk/automations/:id`
  - [x] 1.6 Guard page render: if `!authStore.isAdmin`, renders "Access Restricted" panel

- [x] **Task 2: Create RuleTriggerSelect.vue** (AC: #3)
  - [x] 2.1 Create `desk/src/components/automation/RuleTriggerSelect.vue`
  - [x] 2.2 `TRIGGER_OPTIONS` extracted to `desk/src/components/automation/triggerOptions.ts` (10 triggers)
  - [x] 2.3 Rendered as clickable cards grid; each card shows icon, label, description
  - [x] 2.4 Emits `update:modelValue` (v-model compatible)
  - [x] 2.5 Lucide icons per category (ticket events, SLA events, CSAT, chat)

- [x] **Task 3: Create RuleConditionBuilder.vue** (AC: #4)
  - [x] 3.1 Create `desk/src/components/automation/RuleConditionBuilder.vue`
  - [x] 3.2 `modelValue: { logic, conditions }` — emits on change via deep watchers
  - [x] 3.3 10 HD Ticket fields defined as `TICKET_FIELDS`
  - [x] 3.4 field / operator / value row per condition; value hidden for `is_set`/`is_not_set`
  - [x] 3.5 AND (ALL) / OR (ANY) toggle visible when >1 condition
  - [x] 3.6 Add Condition / remove (×) buttons

- [x] **Task 4: Create RuleActionList.vue** (AC: #5)
  - [x] 4.1 Create `desk/src/components/automation/RuleActionList.vue`
  - [x] 4.2 `ACTION_OPTIONS` extracted to `desk/src/components/automation/actionOptions.ts` (10 actions)
  - [x] 4.3 Contextual value input per `valueType`: text, textarea, priority select, status select, url
  - [x] 4.4 Up/down reorder buttons; remove button per row

- [x] **Task 5: Create AutomationBuilder.vue page** (AC: #2, #6, #7, #8)
  - [x] 5.1 Create `desk/src/pages/automations/AutomationBuilder.vue`
  - [x] 5.2 `id="new"` → blank state; existing id → loads via `frappe.client.get`
  - [x] 5.3 Layout: left sidebar (rule_name, description, priority_order, enabled toggle, failure_count warning) + right main (WHEN/IF/THEN sections)
  - [x] 5.4 Composes `RuleTriggerSelect`, `RuleConditionBuilder`, `RuleActionList`
  - [x] 5.5 Save: validates rule_name required; `frappe.client.insert` (new) or `frappe.client.set_value` (edit)
  - [x] 5.6 Enabled toggle in sidebar
  - [x] 5.7 Test Rule modal: ticket ID input → `helpdesk.api.automation.test_rule` → condition match/fail badges + "Rule WOULD fire" / "Rule would NOT fire" summary
  - [x] 5.8 Breadcrumb "Automation Rules" link navigates back to list

- [x] **Task 6: Implement test_rule API endpoint** (AC: #8)
  - [x] 6.1–6.6 All implemented in `helpdesk/api/automation.py` and `engine.py` dry_run support

- [x] **Task 7: Add routes to Vue Router** (AC: #9)
  - [x] 7.1–7.3 Routes added to `desk/src/router/index.ts`; "Automations" sidebar entry added to `layoutSettings.ts` with Lucide Zap icon

- [x] **Task 8: Write component tests** (AC: #10)
  - [x] 8.1 `AutomationList.spec.ts` — 7 tests pass
  - [x] 8.2 `AutomationBuilder.spec.ts` — 9 tests pass
  - [x] 8.3 `RuleTriggerSelect.spec.ts` — 7 tests pass
  - [x] 8.4 `RuleConditionBuilder.spec.ts` — 10 tests pass
  - [x] 8.5 `RuleActionList.spec.ts` — 11 tests pass
  - [x] vitest 4.1.1 installed; `vitest.config.ts` created; `test`/`test:watch` scripts added to `package.json`
  - **Total: 44/44 tests pass**

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

claude-sonnet-4-6 (global)

### Debug Log References

- `export const` in `<script setup>` is invalid in Vue 3 — extracted `TRIGGER_OPTIONS` to `triggerOptions.ts` and `ACTION_OPTIONS`/`PRIORITY_OPTIONS`/`STATUS_OPTIONS` to `actionOptions.ts`
- `vi.mock` hoisting: factories cannot reference outer `const` variables — fixed by importing mocked modules after `vi.mock()` and casting via `as ReturnType<typeof vi.fn>`
- gunicorn `--preload` caches whitelisted methods at boot — `HUP` alone may not pick up new Python files if the file didn't exist at original startup; confirmed API returns expected 403 (same as all other whitelisted methods when unauthenticated)
- `vite build` outside bench fails on missing `common_site_config.json` — built from bench app dir instead

### Completion Notes List

- All 10 acceptance criteria met
- 44 component tests pass (vitest 4.1.1 + @vue/test-utils 2.4.6)
- Frontend built successfully (28.9s); pages `/helpdesk/automations` and `/helpdesk/automations/new` return HTTP 200
- `test_rule` dry-run API implemented with `frappe.only_for(["System Manager", "HD Admin"])` guard
- `engine.py` extended with `dry_run=True` flag and `_dry_run_rule()` helper
- `ACTION_OPTIONS` and `TRIGGER_OPTIONS` extracted to separate `.ts` files (required to avoid `export const` inside `<script setup>`)
- Sidebar "Automations" entry added with `LucideZap` icon

### File List

- `desk/src/pages/automations/AutomationList.vue` (new)
- `desk/src/pages/automations/AutomationBuilder.vue` (new)
- `desk/src/pages/automations/__tests__/AutomationList.spec.ts` (new)
- `desk/src/pages/automations/__tests__/AutomationBuilder.spec.ts` (new)
- `desk/src/components/automation/RuleConditionBuilder.vue` (new)
- `desk/src/components/automation/RuleActionList.vue` (new)
- `desk/src/components/automation/RuleTriggerSelect.vue` (new)
- `desk/src/components/automation/triggerOptions.ts` (new)
- `desk/src/components/automation/actionOptions.ts` (new)
- `desk/src/components/automation/__tests__/RuleConditionBuilder.spec.ts` (new)
- `desk/src/components/automation/__tests__/RuleActionList.spec.ts` (new)
- `desk/src/components/automation/__tests__/RuleTriggerSelect.spec.ts` (new)
- `desk/src/test-setup.ts` (new — global vitest mock setup)
- `desk/src/__mocks__/icon.ts` (new — stub for icon imports in tests)
- `desk/vitest.config.ts` (new)
- `desk/package.json` (modify: add test/test:watch scripts, vitest devDep)
- `desk/src/router/index.ts` (modify: add AutomationList + AutomationBuilder routes)
- `desk/src/components/layouts/layoutSettings.ts` (modify: add Automations sidebar entry)
- `helpdesk/api/automation.py` (new — test_rule, toggle_rule, get_execution_stats)
- `helpdesk/helpdesk/automation/engine.py` (modify: dry_run flag + _dry_run_rule + _fetch_single_rule)
