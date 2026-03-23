# Story: Fix: Story 2.1 Automation Rule — Nested conditions rejected + trigger type shadowing

Status: done
Task ID: mn3o5cv8zis3fr
Task Number: #217
Workflow: quick-dev
Model: sonnet
Created: 2026-03-23T20:59:23.109Z

## Description

## Fix Task (from QA report docs/qa-report-task-26.md)

### SCOPE LOCK
You MUST only modify the files listed below. Any change outside this scope = failure.

### Issues to fix

#### Issue 1 (P1): DocType validator rejects nested condition groups
- File: `helpdesk/helpdesk/doctype/hd_automation_rule/hd_automation_rule.py`
- Lines: 50-60
- Current: `_validate_conditions()` checks every dict for `'field'` and `'operator'` keys, but nested condition groups use `{'logic': 'OR', 'conditions': [...]}`
- Expected: Allow dicts that have a `'conditions'` key (nested groups) to pass validation without requiring `'field'`/`'operator'`. Nested group items should be recursively validated.
- Current code:
```python
for i, cond in enumerate(data):
    if not isinstance(cond, dict):
        frappe.throw(...)
    if "field" not in cond or "operator" not in cond:
        frappe.throw(...)
```
- Expected code:
```python
for i, cond in enumerate(data):
    if not isinstance(cond, dict):
        frappe.throw(...)
    if "conditions" in cond:
        # Nested condition group — validate recursively
        nested = cond["conditions"]
        if not isinstance(nested, list):
            frappe.throw(_("Condition #{0} nested 'conditions' must be a list.").format(i + 1), frappe.ValidationError)
        for j, sub in enumerate(nested):
            if not isinstance(sub, dict):
                frappe.throw(_("Condition #{0} sub-condition #{1} must be a JSON object.").format(i + 1, j + 1), frappe.ValidationError)
            if "field" not in sub or "operator" not in sub:
                frappe.throw(_("Condition #{0} sub-condition #{1} must have 'field' and 'operator' keys.").format(i + 1, j + 1), frappe.ValidationError)
    elif "field" not in cond or "operator" not in cond:
        frappe.throw(_("Condition #{0} must have 'field' and 'operator' keys.").format(i + 1), frappe.ValidationError)
```
- Verify: `curl -s -b /tmp/hd-cookies.txt -X POST 'http://helpdesk.localhost:8004/api/resource/HD%2

## Acceptance Criteria

- [x] Implementation matches task description
- [x] No regressions introduced
- [x] Code compiles/builds without errors

## Tasks / Subtasks

- [x] Implement changes
- [x] Verify build passes

## Dev Notes



### References

- Task source: Claude Code Studio task #217

## Dev Agent Record

### Agent Model Used

sonnet

### Completion Notes List

- Fixed Issue 1 (P1): `_validate_conditions()` now accepts nested condition groups (`{"logic": "OR", "conditions": [...]}`) by checking for the `"conditions"` key first and recursively validating sub-conditions, before falling through to the flat `"field"`/`"operator"` check.
- Fixed Issue 2 (P1): `resolve_trigger_type()` now returns `list[str]` instead of `str`. Specialized triggers (ticket_resolved, ticket_reopened, ticket_assigned) now include `"ticket_updated"` in the returned list so rules registered for `ticket_updated` fire alongside specialized triggers. `_run()` in engine.py updated to iterate over the returned list.
- All 46 tests (13 DocType + 26 conditions + 7 engine) pass with no regressions.
- Both dev and bench copies updated.

### Change Log

- `hd_automation_rule.py`: Added nested condition group support in `_validate_conditions()` — branch on `"conditions" in cond` before `"field"/"operator"` check.
- `triggers.py`: Changed `resolve_trigger_type()` return type from `str` to `list[str]`; specialized triggers now co-fire `"ticket_updated"`.
- `engine.py`: Updated `_run()` to iterate over the list returned by `resolve_trigger_type()`.

### File List

- `helpdesk/helpdesk/doctype/hd_automation_rule/hd_automation_rule.py`
- `helpdesk/helpdesk/automation/triggers.py`
- `helpdesk/helpdesk/automation/engine.py`
