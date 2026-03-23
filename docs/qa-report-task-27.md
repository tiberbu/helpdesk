# QA Report: Task #27 — Story 2.2: Automation Rule Builder UI

**Reviewer:** Adversarial QA (Opus)
**Date:** 2026-03-23
**Task:** #218 (QA for #27)
**Verdict:** Multiple P1 issues found; consolidated fix task required

---

## Acceptance Criteria Results

### AC-1: WHEN section with 10+ triggers
**PASS** — `triggerOptions.ts` exports exactly 10 triggers matching spec: ticket_created, ticket_updated, ticket_assigned, ticket_resolved, ticket_reopened, sla_warning, sla_breached, csat_received, chat_started, chat_ended. `RuleTriggerSelect.vue` renders them as clickable cards with icons and descriptions.

### AC-2: IF section with field/operator/value and AND/OR grouping
**PASS (partial)** — `RuleConditionBuilder.vue` provides 10 ticket fields, 7 operators (equals, not_equals, contains, greater_than, less_than, is_set, is_not_set), and an AND/OR toggle. Value input is correctly hidden for is_set/is_not_set. However, see P1-1 below regarding the AND/OR logic being silently discarded on save.

### AC-3: THEN section with 10+ actions
**PASS** — `actionOptions.ts` exports exactly 10 action types matching spec. Contextual inputs (priority select, status select, textarea for notes, URL for webhook) and up/down reorder buttons are implemented.

### AC-4: Test Rule (dry-run) shows evaluation results
**PASS (partial)** — The Test Rule modal calls `helpdesk.api.automation.test_rule` API, which delegates to `engine.evaluate(dry_run=True)`. Per-condition match/fail results and per-action would-execute flags are displayed. However, see P1-2 for the ticket ID input being a free-text field with no Link-type autocomplete.

---

## Issues Found

### P1-1: AND/OR logic operator silently discarded on save (DATA LOSS)
- **Severity:** P1
- **File:** `desk/src/pages/automations/AutomationBuilder.vue`
- **Line:** 356
- **Description:** The save function serializes `conditionsState.value.conditions` (the array) but NOT `conditionsState.value.logic` (the AND/OR toggle). The `conditions` field stored in the database is `JSON.stringify(conditionsState.value.conditions || [])` — a flat array with no `logic` key. When the rule is loaded back, `loadRule` at line 308-318 tries to parse the stored conditions:
  - If it's an array (which it will be), it defaults logic to `"AND"` — so any user who selected `"OR"` will have their choice silently overwritten to `"AND"` on reload.
- **Current code (line 356):**
  ```js
  conditions: JSON.stringify(conditionsState.value.conditions || []),
  ```
- **Expected code:**
  ```js
  conditions: JSON.stringify({
    logic: conditionsState.value.logic || "AND",
    conditions: conditionsState.value.conditions || [],
  }),
  ```
- **Verify:** Create a rule with OR logic, save, reload. The logic should persist as OR, not reset to AND.

### P1-2: No success toast/feedback after save
- **Severity:** P1
- **File:** `desk/src/pages/automations/AutomationBuilder.vue`
- **Lines:** 347-373
- **Description:** After a successful save, the code silently navigates to the list page (`router.push`) with no user feedback — no toast, no notification, nothing. If the save fails (API error), there's also no catch block that shows an error toast; the `finally` just resets `saving`. The user has no confirmation that their rule was actually saved. Every other Frappe page (ticket edit, KB article edit, etc.) shows a success toast.
- **Expected:** Add `createToast({ title: __("Rule saved"), icon: "check", iconClasses: "text-green-600" })` on success, and a catch block with error toast on failure.

### P1-3: `alert()` and `confirm()` used instead of frappe-ui dialogs
- **Severity:** P1
- **Files:**
  - `desk/src/pages/automations/AutomationBuilder.vue` lines 335, 339, 343, 396
  - `desk/src/pages/automations/AutomationList.vue` line 182
- **Description:** The implementation uses raw browser `alert()` for validation errors and `confirm()` for delete confirmation. This is inconsistent with the rest of the helpdesk UI which uses frappe-ui toast/dialog components. Raw `alert()` blocks the main thread, looks unprofessional, and cannot be styled or tested properly.
- **Expected:** Use `createToast()` for validation errors and frappe-ui `Dialog` for delete confirmation.

### P1-4: AutomationBuilder has no admin permission check
- **Severity:** P1
- **File:** `desk/src/pages/automations/AutomationBuilder.vue`
- **Description:** The `AutomationList.vue` correctly shows an "Access Restricted" UI for non-admin users (`v-if="!authStore.isAdmin"`). However, `AutomationBuilder.vue` has NO permission check at all — any authenticated agent can directly navigate to `/automations/new` or `/automations/:id` and create/edit rules. The backend API `test_rule` and `toggle_rule` use `frappe.only_for(["System Manager", "HD Admin"])`, but the save uses `frappe.client.insert` / `frappe.client.set_value` which rely on DocType permissions, not the custom admin check.
- **Expected:** Add `authStore.isAdmin` check in AutomationBuilder (redirect to list if not admin), or at minimum show the same restricted UI.

### P2-1: No pagination on AutomationList
- **Severity:** P2
- **File:** `desk/src/pages/automations/AutomationList.vue`
- **Line:** 142-147
- **Description:** `createListResource` is called without `pageLength` or any pagination controls. With many rules, the entire list loads at once. The list has no search, no filtering, and no sorting controls beyond the default DB order.

### P2-2: No unsaved changes guard
- **Severity:** P2
- **File:** `desk/src/pages/automations/AutomationBuilder.vue`
- **Description:** No `onBeforeRouteLeave` or `beforeunload` handler. If a user spends time configuring a complex rule and accidentally clicks "Cancel" or navigates away, all changes are silently lost with no warning.

### P2-3: ITIL mode gating not applied to Automations sidebar entry
- **Severity:** P2
- **File:** `desk/src/components/layouts/layoutSettings.ts`
- **Lines:** 47-51
- **Description:** The "Automations" sidebar entry is unconditionally added to `agentPortalSidebarOptions`. Per the project's ITIL gating pattern (documented in MEMORY.md), new ITIL features should be gated behind `itilModeEnabled`. Other ITIL features (Major Incidents) follow this pattern, but Automations does not.

### P2-4: `frappe.client.set_value` called with full payload object as `fieldname`
- **Severity:** P2
- **File:** `desk/src/pages/automations/AutomationBuilder.vue`
- **Line:** 363-367
- **Description:** The update call passes the entire payload object as the `fieldname` parameter to `frappe.client.set_value`. While Frappe does support this undocumented pattern (passing a dict to `fieldname` updates multiple fields), it's fragile and may break across Frappe versions. The standard pattern is `frappe.client.save` with the full document.

### P2-5: No accessibility attributes on interactive elements
- **Severity:** P2
- **Files:** `RuleTriggerSelect.vue`, `RuleConditionBuilder.vue`, `RuleActionList.vue`
- **Description:** Trigger selection cards are plain `<div>` elements with `@click` handlers — no `role="radio"`, no `aria-checked`, no `tabindex`, no keyboard navigation. Condition and action remove/reorder buttons lack `aria-label`. The AND/OR toggle buttons lack `aria-pressed`.

### P3-1: Trigger icon mapping is positional, not keyed
- **Severity:** P3
- **File:** `desk/src/components/automation/RuleTriggerSelect.vue`
- **Lines:** 55-58
- **Description:** Icons are mapped to triggers by array index position: `[LucideTicket, LucideRefreshCw, ...][i]`. If anyone reorders `TRIGGER_OPTIONS` in `triggerOptions.ts`, all icons silently shift to wrong triggers. Should be a keyed map: `{ ticket_created: LucideTicket, ... }`.

### P3-2: Hardcoded priority and status options not fetched from server
- **Severity:** P3
- **File:** `desk/src/components/automation/actionOptions.ts`
- **Lines:** 14-26
- **Description:** Priority options (Low/Medium/High/Urgent) and Status options (Open/Replied/Resolved/Closed) are hardcoded. The helpdesk supports ITIL priority matrix and custom ticket statuses. These should be fetched from the server or at least reference shared constants.

### P3-3: Condition field list doesn't include ITIL fields
- **Severity:** P3
- **File:** `desk/src/components/automation/RuleConditionBuilder.vue`
- **Lines:** 163-174
- **Description:** `TICKET_FIELDS` is hardcoded to 10 fields but omits ITIL-specific fields added in earlier stories: `impact`, `urgency`, `is_major_incident`, `ticket_type`. Automation rules cannot filter on these fields.

### P3-4: No error handling on list load failure or delete failure
- **Severity:** P3
- **File:** `desk/src/pages/automations/AutomationList.vue`
- **Description:** `toggleEnabled` and `deleteRule` have no try/catch. If the API call fails (network error, permission denied), the error is swallowed or shown as an unhandled promise rejection in the console.

### P3-5: Test Rule modal ticket input is free-text, not a Link field
- **Severity:** P3
- **File:** `desk/src/pages/automations/AutomationBuilder.vue`
- **Lines:** 174-178
- **Description:** The ticket ID input for dry-run testing is a plain text input. Users must know the exact ticket name/ID. Should be a Link-type autocomplete that searches HD Ticket (subject, name).

---

## Console Errors
API endpoints return proper error responses (DoesNotExistError) for invalid inputs. No unexpected console errors detected via curl testing. Playwright browser testing was unavailable for this review.

---

## Summary

| Severity | Count | Items |
|----------|-------|-------|
| P0       | 0     |       |
| P1       | 4     | P1-1 (logic discarded), P1-2 (no save feedback), P1-3 (alert/confirm), P1-4 (no admin guard on builder) |
| P2       | 5     | P2-1 to P2-5 |
| P3       | 5     | P3-1 to P3-5 |

**Recommendation:** Create ONE consolidated fix task for P1 issues. P2/P3 issues documented for future sprints.
