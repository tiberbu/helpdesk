# Story: Fix: Story 2.2 Automation Rule Builder UI — Conditions save format mismatch + New Rule button visible to non-admins

Status: in-progress
Task ID: mn4b3ciqjymc0f
Task Number: #265
Workflow: quick-dev
Model: sonnet
Created: 2026-03-24T07:41:40.516Z

## Description

## Fix Task (from QA report docs/qa-report-task-27.md)

### SCOPE LOCK
You MUST only modify the files listed below. Any change outside this scope = failure.

### Issues to fix

#### Issue 1 (P0): Frontend saves conditions as dict wrapper; backend rejects it
- File: `desk/src/pages/automations/AutomationBuilder.vue`
- Line: 367
- Current:
```js
conditions: JSON.stringify({ logic: conditionsState.value.logic || "AND", conditions: conditionsState.value.conditions || [] }),
```
- Expected: Serialize as flat array when AND logic, or wrap in nested group for OR logic:
```js
conditions: JSON.stringify(
  conditionsState.value.logic === "OR" && conditionsState.value.conditions?.length
    ? [{ logic: "OR", conditions: conditionsState.value.conditions }]
    : conditionsState.value.conditions || []
),
```
- This ensures:
  - AND logic: saves as `[{field,op,val},...]` (flat array, compatible with backend validation and engine evaluator)
  - OR logic: saves as `[{"logic":"OR","conditions":[{field,op,val},...]}]` (nested group, compatible with both validation and `ConditionEvaluator.evaluate()` recursive group handling)
- Verify: `curl -s -b /tmp/qa-cookies.txt -X POST 'http://help.frappe.local/api/method/frappe.client.insert' -H 'Content-Type: application/json' -H "X-Frappe-CSRF-Token: $CSRF" -d '{"doc":{"doctype":"HD Automation Rule","rule_name":"fix-verify-test","trigger_type":"ticket_created","conditions":"[{\"field\":\"priority\",\"operator\":\"equals\",\"value\":\"Urgent\"}]","actions":"[{\"type\":\"set_priority\",\"value\":\"High\"}]","priority_order":99,"enabled":0}}'` should return 200 (not ValidationError)

- Also fix load path (line 322-330): when loading an existing rule that has the nested group format `[{"logic":"OR","conditions":[...]}]`, extract the logic and conditions for the UI state. Current code handles the old dict wrapper format but should also handle the nested group format.

#### Issue 2 (P1): 'New Rule' button visible to non-admin users
- File: `desk/s

## Acceptance Criteria

- [ ] Implementation matches task description
- [ ] No regressions introduced
- [ ] Code compiles/builds without errors

## Tasks / Subtasks

- [ ] Implement changes
- [ ] Verify build passes

## Dev Notes



### References

- Task source: Claude Code Studio task #265

## Dev Agent Record

### Agent Model Used

sonnet

### Completion Notes List

_(Updated by agent on completion)_

### Change Log

_(Updated by agent during implementation)_

### File List

_(Updated by agent — list all files created or modified)_
