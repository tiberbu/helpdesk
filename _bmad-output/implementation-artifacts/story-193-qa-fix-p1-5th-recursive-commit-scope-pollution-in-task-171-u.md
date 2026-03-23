# Story: QA: Fix: P1 5th recursive commit-scope pollution in task-171 + undeclared hd_ticket.py cron refactor

Status: in-progress
Task ID: mn3fdzmu49noq6
Task Number: #193
Workflow: adversarial-review
Model: opus
Created: 2026-03-23T16:54:23.025Z

## Description

## What to test

Task #189 made the following changes:
1. **story-171 File List expanded**: Updated from 4 to 14 entries listing all files in commit d893b5e97 with UNDECLARED annotations.
2. **story-171 Change Log updated**: Added detailed hd_ticket.py cron refactor entry with description of _autoclose_savepoint CM + broad Exception handler + reference to test coverage in test_close_tickets.py.
3. **TestEnsureHelpersRolePollutionGuard moved**: From `helpdesk/helpdesk/doctype/hd_time_entry/test_hd_time_entry.py` to `helpdesk/tests/test_utils.py` — co-locating tests with the module they test.

## Test Steps
1. Verify story-171 File List has exactly 14 entries
2. Verify story-171 Change Log has hd_ticket.py entry with _autoclose_savepoint description
3. Verify TestEnsureHelpersRolePollutionGuard class is in test_utils.py and NOT in test_hd_time_entry.py
4. Run `bench run-tests --module helpdesk.tests.test_utils` — expect 9 tests pass
5. Run `bench run-tests --module helpdesk.helpdesk.doctype.hd_time_entry.test_hd_time_entry` — expect 80 tests pass
6. Check bench/dev file sync for test_utils.py and test_hd_time_entry.py

## Files Changed
- `_bmad-output/implementation-artifacts/story-171-fix-p1-commit-scope-pollution-in-task-163-stale-frappe-throw.md`
- `helpdesk/helpdesk/tests/test_utils.py`
- `helpdesk/helpdesk/doctype/hd_time_entry/test_hd_time_entry.py`
- `_bmad-output/implementation-artifacts/story-189-*.md`

## Expected Results
- story-171 File List: 14 items
- story-171 Change Log: hd_ticket.py UNDECLARED entry present
- TestEnsureHelpersRolePollutionGuard: in test_utils.py, removed from test_hd_time_entry.py
- 9 tests pass in test_utils, 80 in test_hd_time_entry (no regressions)

## Acceptance Criteria

- [ ] **story-171 File List expanded**: Updated from 4 to 14 entries listing all files in commit d893b5e97 with UNDECLARED annotations.
- [ ] **story-171 Change Log updated**: Added detailed hd_ticket.py cron refactor entry with description of _autoclose_savepoint CM + broad Exception handler + reference to test coverage in test_close_tickets.py.
- [ ] **TestEnsureHelpersRolePollutionGuard moved**: From `helpdesk/helpdesk/doctype/hd_time_entry/test_hd_time_entry.py` to `helpdesk/tests/test_utils.py` — co-locating tests with the module they test.
- [ ] Verify story-171 File List has exactly 14 entries
- [ ] Verify story-171 Change Log has hd_ticket.py entry with _autoclose_savepoint description
- [ ] Verify TestEnsureHelpersRolePollutionGuard class is in test_utils.py and NOT in test_hd_time_entry.py
- [ ] Run `bench run-tests --module helpdesk.tests.test_utils` — expect 9 tests pass
- [ ] Run `bench run-tests --module helpdesk.helpdesk.doctype.hd_time_entry.test_hd_time_entry` — expect 80 tests pass
- [ ] Check bench/dev file sync for test_utils.py and test_hd_time_entry.py

## Tasks / Subtasks

- [ ] **story-171 File List expanded**: Updated from 4 to 14 entries listing all files in commit d893b5e97 with UNDECLARED annotations.
- [ ] **story-171 Change Log updated**: Added detailed hd_ticket.py cron refactor entry with description of _autoclose_savepoint CM + broad Exception handler + reference to test coverage in test_close_tickets.py.
- [ ] **TestEnsureHelpersRolePollutionGuard moved**: From `helpdesk/helpdesk/doctype/hd_time_entry/test_hd_time_entry.py` to `helpdesk/tests/test_utils.py` — co-locating tests with the module they test.
- [ ] Verify story-171 File List has exactly 14 entries
- [ ] Verify story-171 Change Log has hd_ticket.py entry with _autoclose_savepoint description
- [ ] Verify TestEnsureHelpersRolePollutionGuard class is in test_utils.py and NOT in test_hd_time_entry.py
- [ ] Run `bench run-tests --module helpdesk.tests.test_utils` — expect 9 tests pass
- [ ] Run `bench run-tests --module helpdesk.helpdesk.doctype.hd_time_entry.test_hd_time_entry` — expect 80 tests pass
- [ ] Check bench/dev file sync for test_utils.py and test_hd_time_entry.py

## Dev Notes



### References

- Task source: Claude Code Studio task #193

## Dev Agent Record

### Agent Model Used

opus

### Completion Notes List

_(Updated by agent on completion)_

### Change Log

_(Updated by agent during implementation)_

### File List

_(Updated by agent — list all files created or modified)_
