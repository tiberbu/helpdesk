# Story: Fix: P1 _ensure_sm_agent_user missing HD Agent record + P1 is_agent identity contract + P2 on_trash wasteful get_roles + P2 PRIVILEGED_ROLES auto-derivation risk

Status: in-progress
Task ID: mn3esjuxkt6loh
Task Number: #175
Workflow: quick-dev
Model: sonnet
Created: 2026-03-23T16:37:42.925Z

## Description

## QA Findings from adversarial review (docs/qa-report-task-155.md)

### P1: _ensure_sm_agent_user does not create HD Agent record
- The helper creates User with Agent+SM roles but NO HD Agent record
- is_agent() has HD Agent fallback check; test is fragile if is_agent() changes
- Fix: Add HD Agent creation to _ensure_sm_agent_user, or move to test_utils.py using create_agent pattern

### P1: is_agent() identity contract unenforceable
- user and user_roles can silently mismatch with no runtime assertion
- delete_entry passes user_roles but not user param; coincidentally works
- Fix: Add assertion or simplify API to not accept both params

### P2: on_trash fetches get_roles even for Administrator
- Comment claims Administrator short-circuits before role lookup — factually incorrect
- get_roles() called unconditionally on line 102 before is_agent() check
- Fix: Check is_admin() first, skip get_roles() for Administrator

### P2: PRIVILEGED_ROLES auto-derivation is a privilege escalation risk
- AGENT_ROLES - {Agent} means any new role added to AGENT_ROLES auto-becomes privileged
- Fix: Explicitly enumerate PRIVILEGED_ROLES instead of deriving

### P2: _ensure_sm_agent_user not in shared test_utils.py (DRY violation)
### P2: No role pollution guard on _ensure_sm_agent_user
### P2: session.py hardcoded role checks not updated

### Files to modify
- helpdesk/utils.py (is_agent identity contract)
- helpdesk/helpdesk/doctype/hd_time_entry/hd_time_entry.py (on_trash optimization, PRIVILEGED_ROLES)
- helpdesk/helpdesk/doctype/hd_time_entry/test_hd_time_entry.py (_ensure_sm_agent_user)
- helpdesk/test_utils.py (add ensure_sm_agent_user)

## Acceptance Criteria

- [ ] Implementation matches task description
- [ ] No regressions introduced
- [ ] Code compiles/builds without errors

## Tasks / Subtasks

- [ ] Implement changes
- [ ] Verify build passes

## Dev Notes



### References

- Task source: Claude Code Studio task #175

## Dev Agent Record

### Agent Model Used

sonnet

### Completion Notes List

_(Updated by agent on completion)_

### Change Log

_(Updated by agent during implementation)_

### File List

_(Updated by agent — list all files created or modified)_
