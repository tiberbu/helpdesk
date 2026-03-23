# Story: QA: Fix P1 delete_entry double get_roles + stale test count + audit trail violations

Status: in-progress
Task ID: mn3e1ytm7qeab9
Task Number: #152
Workflow: adversarial-review
Model: opus
Created: 2026-03-23T16:17:05.085Z

## Description

## QA task for story-146

Verify all P1/P2 fixes from adversarial review task-139.

### What to test
1. `delete_entry()` in `helpdesk/api/time_tracking.py` — confirm single `get_roles()` call (no double hit)
2. `_check_delete_permission()` in `hd_time_entry.py` — confirm `user_roles` optional param works and Administrator short-circuits correctly
3. `ensure_agent_manager_user()` and `ensure_system_manager_user()` in `test_utils.py` — confirm role-pollution assertions are present
4. Story-130 completion notes — confirm AUDIT CORRECTION note and corrected test count (71)

### Expected behavior
- `delete_entry()` calls `frappe.get_roles()` exactly once (fetched at top, passed to `_check_delete_permission`)
- `_check_delete_permission` has `user_roles=None` param; returns immediately for Administrator
- All three `ensure_*` helpers have role-pollution assertions
- Story-130 notes have AUDIT CORRECTION text and mention 71 actual tests

### Test steps
1. Read `helpdesk/api/time_tracking.py` — inspect `delete_entry()` for single `get_roles()` call
2. Read `helpdesk/helpdesk/doctype/hd_time_entry/hd_time_entry.py` — inspect `_check_delete_permission()`
3. Read `helpdesk/test_utils.py` — inspect all three `ensure_*` helpers
4. Read story-130 completion notes file
5. Run tests: `bench --site helpdesk.localhost run-tests --app helpdesk --module helpdesk.helpdesk.doctype.hd_time_entry.test_hd_time_entry`
6. Run tests: `bench --site helpdesk.localhost run-tests --app helpdesk --module helpdesk.tests.test_utils`

### Files changed
- `helpdesk/api/time_tracking.py`
- `helpdesk/helpdesk/doctype/hd_time_entry/hd_time_entry.py`
- `helpdesk/test_utils.py`
- `_bmad-output/implementation-artifacts/story-130-fix-p1-p2-from-adversarial-review-task-120-stale-test-count-.md`

### Playwright testing
No frontend changes — backend/test-utils only. Focus on code review and test execution.

## Acceptance Criteria

- [ ] `delete_entry()` calls `frappe.get_roles()` exactly once (fetched at top, passed to `_check_delete_permission`)
- [ ] `_check_delete_permission` has `user_roles=None` param; returns immediately for Administrator
- [ ] All three `ensure_*` helpers have role-pollution assertions
- [ ] Story-130 notes have AUDIT CORRECTION text and mention 71 actual tests

## Tasks / Subtasks

- [ ] `delete_entry()` in `helpdesk/api/time_tracking.py` — confirm single `get_roles()` call (no double hit)
- [ ] `_check_delete_permission()` in `hd_time_entry.py` — confirm `user_roles` optional param works and Administrator short-circuits correctly
- [ ] `ensure_agent_manager_user()` and `ensure_system_manager_user()` in `test_utils.py` — confirm role-pollution assertions are present
- [ ] Story-130 completion notes — confirm AUDIT CORRECTION note and corrected test count (71)
- [ ] Read `helpdesk/api/time_tracking.py` — inspect `delete_entry()` for single `get_roles()` call
- [ ] Read `helpdesk/helpdesk/doctype/hd_time_entry/hd_time_entry.py` — inspect `_check_delete_permission()`
- [ ] Read `helpdesk/test_utils.py` — inspect all three `ensure_*` helpers
- [ ] Read story-130 completion notes file
- [ ] Run tests: `bench --site helpdesk.localhost run-tests --app helpdesk --module helpdesk.helpdesk.doctype.hd_time_entry.test_hd_time_entry`
- [ ] Run tests: `bench --site helpdesk.localhost run-tests --app helpdesk --module helpdesk.tests.test_utils`

## Dev Notes



### References

- Task source: Claude Code Studio task #152

## Dev Agent Record

### Agent Model Used

opus

### Completion Notes List

_(Updated by agent on completion)_

### Change Log

_(Updated by agent during implementation)_

### File List

_(Updated by agent — list all files created or modified)_
