# Story: Fix: P1 PRIVILEGED_ROLES/AGENT_ROLES unsync + on_trash double get_roles + is_agent semantic trap

Status: in-progress
Task ID: mn3ela4l06tm0g
Task Number: #169
Workflow: quick-dev
Model: sonnet
Created: 2026-03-23T16:32:04.039Z

## Description

P1 findings from adversarial review docs/qa-report-task-156.md:

**Finding 1 (P1)**: PRIVILEGED_ROLES and AGENT_ROLES are parallel constants with overlapping semantics and no shared derivation. PRIVILEGED_ROLES should be derived from AGENT_ROLES (e.g. AGENT_ROLES - {"Agent"}) to prevent drift.

**Finding 3 (P2)**: on_trash() calls is_agent(user) then _check_delete_permission(self, user) without forwarding user_roles, causing the exact double get_roles() call the task was supposed to fix. Fix: pre-fetch roles and pass to both.

**Finding 11 (P1)**: is_agent(user, user_roles) allows mismatched identity — user_roles could belong to a different user than user param. Add validation or prominent documentation.

**Finding 2 (P2)**: Type annotation user_roles: set = None should be set | None = None.

**Finding 6 (P2)**: on_trash uses positional is_agent(user), delete_entry uses keyword is_agent(user_roles=user_roles). Standardize to keyword args.

Recommended fixes:
1. Define PRIVILEGED_ROLES = AGENT_ROLES - {"Agent"} in utils.py or derive in hd_time_entry.py
2. Pre-fetch user_roles in on_trash() and pass to both is_agent() and _check_delete_permission()
3. Fix type annotation to set | None = None
4. Add assertion or docstring warning about user/user_roles identity mismatch
5. Standardize calling convention to use keyword arguments

## Acceptance Criteria

- [ ] Define PRIVILEGED_ROLES = AGENT_ROLES - {"Agent"} in utils.py or derive in hd_time_entry.py
- [ ] Pre-fetch user_roles in on_trash() and pass to both is_agent() and _check_delete_permission()
- [ ] Fix type annotation to set | None = None
- [ ] Add assertion or docstring warning about user/user_roles identity mismatch
- [ ] Standardize calling convention to use keyword arguments

## Tasks / Subtasks

- [ ] Define PRIVILEGED_ROLES = AGENT_ROLES - {"Agent"} in utils.py or derive in hd_time_entry.py
- [ ] Pre-fetch user_roles in on_trash() and pass to both is_agent() and _check_delete_permission()
- [ ] Fix type annotation to set | None = None
- [ ] Add assertion or docstring warning about user/user_roles identity mismatch
- [ ] Standardize calling convention to use keyword arguments

## Dev Notes



### References

- Task source: Claude Code Studio task #169

## Dev Agent Record

### Agent Model Used

sonnet

### Completion Notes List

_(Updated by agent on completion)_

### Change Log

_(Updated by agent during implementation)_

### File List

_(Updated by agent — list all files created or modified)_
