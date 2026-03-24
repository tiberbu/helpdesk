# Story: Fix: Story 2.1 Automation Rule — Deep nesting validation + phantom trigger types

Status: done
Task ID: mn4ark5qdnjyf8
Task Number: #261
Workflow: quick-dev
Model: sonnet
Created: 2026-03-24T07:32:30.544Z

## Description

## Fix Task (from QA report docs/qa-report-task-26.md)

### SCOPE LOCK
You MUST only modify the files listed below. Any change outside this scope = failure.

### Issues to fix

#### Issue 1 (P1): Deep nested conditions (3+ levels) rejected by validator
- File: `helpdesk/helpdesk/doctype/hd_automation_rule/hd_automation_rule.py`
- Lines: 64-74
- Current: Sub-conditions within a nested group are checked for `"field"` and `"operator"` keys, but a sub-condition can itself be a nested group with `"conditions"` key.
- Expected: Make the validation recursive. Extract the condition-checking loop into a helper method and call it recursively for nested groups.
- Current code (lines 64-74):
```python
for j, sub in enumerate(nested):
    if not isinstance(sub, dict):
        frappe.throw(...)
    if "field" not in sub or "operator" not in sub:
        frappe.throw(...)
```
- Expected code:
```python
for j, sub in enumerate(nested):
    if not isinstance(sub, dict):
        frappe.throw(...)
    if "conditions" in sub:
        # Recursively validate deeper nesting
        inner = sub["conditions"]
        if not isinstance(inner, list):
            frappe.throw(_("Condition #{0} sub-condition #{1} nested 'conditions' must be a list.").format(i + 1, j + 1), frappe.ValidationError)
        # Recurse — call the same validation
        self._validate_condition_list(inner, depth=depth+1)
    elif "field" not in sub or "operator" not in sub:
        frappe.throw(...)
```
Note: Refactoring `_validate_conditions` to use a recursive helper `_validate_condition_list(data, depth=0)` with a max depth guard (e.g. 5) is the cleanest approach.
- Verify: `curl -s -b /tmp/hd-qa-cookies.txt -X POST 'http://help.frappe.local/api/resource/HD%20Automation%20Rule' -H 'Content-Type: application/json' -d '{"rule_name":"deep-test","trigger_type":"ticket_created","conditions":"[{\"logic\":\"OR\",\"conditions\":[{\"logic\":\"AND\",\"conditions\":[{\"field\":\"priority\",\"operator\":\"equals\",\"value\":\

## Acceptance Criteria

- [ ] Implementation matches task description
- [ ] No regressions introduced
- [ ] Code compiles/builds without errors

## Tasks / Subtasks

- [ ] Implement changes
- [ ] Verify build passes

## Dev Notes



### References

- Task source: Claude Code Studio task #261

## Dev Agent Record

### Agent Model Used

sonnet

### Completion Notes List

_(Updated by agent on completion)_

### Change Log

_(Updated by agent during implementation)_

### File List

_(Updated by agent — list all files created or modified)_
