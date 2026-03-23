# Story: QA: Fix: System Manager delete permission contradictory between delete_entry API and REST DELETE

Status: in-progress
Task ID: mn3e0q7pvtcap4
Task Number: #149
Workflow: adversarial-review
Model: opus
Created: 2026-03-23T16:15:50.966Z

## Description

Code review for story-148 permission fix.

## What to test

### Files changed
- `helpdesk/helpdesk/doctype/hd_time_entry/hd_time_entry.py` — System Manager removed from PRIVILEGED_ROLES; _check_delete_permission docstring updated
- `helpdesk/helpdesk/doctype/hd_time_entry/hd_time_entry.json` — delete:1 removed from System Manager permission block
- `helpdesk/helpdesk/doctype/hd_time_entry/test_hd_time_entry.py` — test_on_trash_allows_system_manager inverted to test_on_trash_blocks_system_manager; frappe.db.commit() removed from test isolation fix

### Expected behavior
- PRIVILEGED_ROLES = frozenset({"HD Admin", "Agent Manager"}) — System Manager excluded
- DocType JSON System Manager block has no delete:1
- test_on_trash_blocks_system_manager_delete passes (expects PermissionError)
- test_delete_entry_system_manager_blocked_at_pre_gate has no frappe.db.commit() in finally block
- All 71 tests pass

### Test steps
1. Review PRIVILEGED_ROLES constant — confirm System Manager absent
2. Review hd_time_entry.json System Manager block — confirm no delete:1
3. Review _check_delete_permission docstring quality and accuracy
4. Review test changes — confirm inverted assertion is correct and isolation fix is correct
5. Confirm no other references to System Manager in delete permission logic remain
6. Run full test suite and confirm 71 pass

### QA criteria
- No contradictory permission surface between delete_entry() and REST DELETE for System Manager
- PRIVILEGED_ROLES and DocType JSON are consistent with each other
- Tests are correctly written and do not call frappe.db.commit() in test isolation contexts

## Acceptance Criteria

- [ ] PRIVILEGED_ROLES = frozenset({"HD Admin", "Agent Manager"}) — System Manager excluded
- [ ] DocType JSON System Manager block has no delete:1
- [ ] test_on_trash_blocks_system_manager_delete passes (expects PermissionError)
- [ ] test_delete_entry_system_manager_blocked_at_pre_gate has no frappe.db.commit() in finally block
- [ ] All 71 tests pass

## Tasks / Subtasks

- [ ] Review PRIVILEGED_ROLES constant — confirm System Manager absent
- [ ] Review hd_time_entry.json System Manager block — confirm no delete:1
- [ ] Review _check_delete_permission docstring quality and accuracy
- [ ] Review test changes — confirm inverted assertion is correct and isolation fix is correct
- [ ] Confirm no other references to System Manager in delete permission logic remain
- [ ] Run full test suite and confirm 71 pass

## Dev Notes



### References

- Task source: Claude Code Studio task #149

## Dev Agent Record

### Agent Model Used

opus

### Completion Notes List

_(Updated by agent on completion)_

### Change Log

_(Updated by agent during implementation)_

### File List

_(Updated by agent — list all files created or modified)_
