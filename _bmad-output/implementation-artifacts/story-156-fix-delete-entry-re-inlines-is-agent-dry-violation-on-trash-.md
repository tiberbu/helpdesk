# Story: Fix: delete_entry re-inlines is_agent() DRY violation + on_trash missing pre-gate

Status: done
Task ID: mn3e59u7bmv6hc
Task Number: #156
Workflow: quick-dev
Model: sonnet
Created: 2026-03-23T16:19:38.209Z

## Description

P1 findings from adversarial review docs/qa-report-task-148.md:

**Finding 1 (P1)**: delete_entry() re-inlines is_agent() logic (lines 248-252 of time_tracking.py) instead of calling the canonical function. This reintroduces the exact DRY violation that task #142 fixed. The justification is sharing user_roles with _check_delete_permission, but the correct fix is to refactor is_agent() to accept an optional user_roles param, not copy-paste its logic.

**Finding 2 (P1)**: on_trash() has no is_agent() pre-gate. It delegates to _check_delete_permission() which only checks ownership + PRIVILEGED_ROLES. A bare System Manager who creates an entry via REST POST can delete their own entry via on_trash because entry.agent == user passes. The DocType JSON delete:1 removal blocks this at the Frappe layer, but there is no test verifying that Frappe perm layer actually blocks it.

**Finding 4 (P2)**: The inline role set in delete_entry includes Agent but PRIVILEGED_ROLES does not. No shared constant ties these together.

Recommended fixes:
1. Add optional user_roles param to is_agent() in utils.py
2. Replace inline role check in delete_entry with is_agent(user_roles=user_roles)
3. Add is_agent() call to on_trash() as a pre-gate, or add a test proving Frappe perm layer blocks System Manager REST DELETE
4. Add negative tests for System Manager on add_entry/start_timer/stop_timer/get_summary

## Acceptance Criteria

- [x] Add optional user_roles param to is_agent() in utils.py
- [x] Replace inline role check in delete_entry with is_agent(user_roles=user_roles)
- [x] Add is_agent() call to on_trash() as a pre-gate, or add a test proving Frappe perm layer blocks System Manager REST DELETE
- [x] Add negative tests for System Manager on add_entry/start_timer/stop_timer/get_summary

## Tasks / Subtasks

- [x] Add optional user_roles param to is_agent() in utils.py
- [x] Replace inline role check in delete_entry with is_agent(user_roles=user_roles)
- [x] Add is_agent() call to on_trash() as a pre-gate, or add a test proving Frappe perm layer blocks System Manager REST DELETE
- [x] Add negative tests for System Manager on add_entry/start_timer/stop_timer/get_summary

## Dev Notes



### References

- Task source: Claude Code Studio task #156

## Dev Agent Record

### Agent Model Used

sonnet

### Completion Notes List

- Fixed P1 DRY violation: added `user_roles` optional param to `is_agent()` in utils.py and replaced the inline role check in `delete_entry()` with `is_agent(user_roles=user_roles)`. A linter also extracted an `AGENT_ROLES` frozenset constant to further eliminate duplication (addresses Finding 4 as well).
- Fixed P1 security gap: added explicit `is_agent()` pre-gate to `on_trash()` — blocks bare System Manager users who own their own entries from deleting via REST DELETE path.
- Added 5 new tests: System Manager blocked on add_entry, start_timer, stop_timer, get_summary, and on_trash with own entry. All 76 tests pass.
- Dev and bench copies synced.

### Change Log

- `helpdesk/utils.py`: Added `user_roles: set = None` param to `is_agent()`; added `AGENT_ROLES` frozenset constant as single source of truth for agent role names.
- `helpdesk/api/time_tracking.py`: `delete_entry()` — replaced inline role check with `is_agent(user_roles=user_roles)`.
- `helpdesk/helpdesk/doctype/hd_time_entry/hd_time_entry.py`: Added `from helpdesk.utils import is_agent`; added `is_agent()` pre-gate to `on_trash()`.
- `helpdesk/helpdesk/doctype/hd_time_entry/test_hd_time_entry.py`: Added 5 new negative tests for bare System Manager on all API endpoints + on_trash own-entry scenario.

### File List

- `helpdesk/utils.py` (modified)
- `helpdesk/api/time_tracking.py` (modified)
- `helpdesk/helpdesk/doctype/hd_time_entry/hd_time_entry.py` (modified)
- `helpdesk/helpdesk/doctype/hd_time_entry/test_hd_time_entry.py` (modified)
