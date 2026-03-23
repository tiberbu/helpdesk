# Story: QA: Fix delete_entry DRY violation + on_trash missing is_agent pre-gate

Status: in-progress
Task ID: mn3ebzzqnwe5sy
Task Number: #159
Workflow: adversarial-review
Model: opus
Created: 2026-03-23T16:24:49.096Z

## Description

Verify fixes from story-156:

1. is_agent() in utils.py now accepts optional user_roles param — no inline role duplication
2. delete_entry() calls is_agent(user_roles=user_roles) instead of copy-pasted logic
3. on_trash() has is_agent() pre-gate blocking bare System Manager from deleting own entries
4. 5 new System Manager negative tests added (add_entry, start_timer, stop_timer, get_summary, on_trash-own-entry)

Files changed:
- helpdesk/utils.py
- helpdesk/api/time_tracking.py
- helpdesk/helpdesk/doctype/hd_time_entry/hd_time_entry.py
- helpdesk/helpdesk/doctype/hd_time_entry/test_hd_time_entry.py

Test steps:
1. Verify 80 tests pass via bench run-tests
2. Verify no inline role check in delete_entry (should call is_agent)
3. Verify on_trash has is_agent call
4. Verify all 5 SM negative tests exist and pass
5. Verify AGENT_ROLES constant in utils.py
6. Check for code quality regressions

Expected: All 80 tests pass, DRY violation resolved, on_trash properly gated.

## Acceptance Criteria

- [ ] is_agent() in utils.py now accepts optional user_roles param — no inline role duplication
- [ ] delete_entry() calls is_agent(user_roles=user_roles) instead of copy-pasted logic
- [ ] on_trash() has is_agent() pre-gate blocking bare System Manager from deleting own entries
- [ ] 5 new System Manager negative tests added (add_entry, start_timer, stop_timer, get_summary, on_trash-own-entry)
- [ ] Verify 80 tests pass via bench run-tests
- [ ] Verify no inline role check in delete_entry (should call is_agent)
- [ ] Verify on_trash has is_agent call
- [ ] Verify all 5 SM negative tests exist and pass
- [ ] Verify AGENT_ROLES constant in utils.py
- [ ] Check for code quality regressions

## Tasks / Subtasks

- [ ] is_agent() in utils.py now accepts optional user_roles param — no inline role duplication
- [ ] delete_entry() calls is_agent(user_roles=user_roles) instead of copy-pasted logic
- [ ] on_trash() has is_agent() pre-gate blocking bare System Manager from deleting own entries
- [ ] 5 new System Manager negative tests added (add_entry, start_timer, stop_timer, get_summary, on_trash-own-entry)
- [ ] Verify 80 tests pass via bench run-tests
- [ ] Verify no inline role check in delete_entry (should call is_agent)
- [ ] Verify on_trash has is_agent call
- [ ] Verify all 5 SM negative tests exist and pass
- [ ] Verify AGENT_ROLES constant in utils.py
- [ ] Check for code quality regressions

## Dev Notes



### References

- Task source: Claude Code Studio task #159

## Dev Agent Record

### Agent Model Used

opus

### Completion Notes List

_(Updated by agent on completion)_

### Change Log

_(Updated by agent during implementation)_

### File List

_(Updated by agent — list all files created or modified)_
