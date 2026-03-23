# Story: Story 2.4: Automation Execution Logging

Status: done
Task ID: mn2gah4bbxs2uq
Task Number: #29
Workflow: dev-story
Model: sonnet
Created: 2026-03-23T21:27:39.145Z

## Description

## Story 2.4: Automation Execution Logging

As an administrator, I want to see a log of every automation rule execution, so that I can debug and optimize my rules.

### Acceptance Criteria

- HD Automation Log record created on each execution: rule_name, ticket, trigger_event, conditions_evaluated, actions_executed, execution_time_ms, status, timestamp
- Per-rule stats: execution count, last fired time, failure rate visible on automation list page
- Auto-disable after 10 consecutive failures with notification to rule creator
- Old logs purged after 30 days (configurable) via daily cleanup job

### Tasks
- Create HD Automation Log DocType
- Integrate logging into automation engine execution pipeline
- Implement auto-disable logic in safety module
- Add daily log cleanup scheduler event in hooks.py
- Add per-rule execution statistics API
- Write unit tests for logging, auto-disable, and cleanup

## Acceptance Criteria

- [x] HD Automation Log record created on each execution: rule_name, ticket, trigger_event, conditions_evaluated, actions_executed, execution_time_ms, status, timestamp
- [x] Per-rule stats: execution count, last fired time, failure rate visible on automation list page
- [x] Auto-disable after 10 consecutive failures with notification to rule creator
- [x] Old logs purged after 30 days (configurable) via daily cleanup job

## Tasks / Subtasks

- [x] Create HD Automation Log DocType
- [x] Integrate logging into automation engine execution pipeline
- [x] Implement auto-disable logic in safety module
- [x] Add daily log cleanup scheduler event in hooks.py
- [x] Add per-rule execution statistics API
- [x] Write unit tests for logging, auto-disable, and cleanup

## Dev Notes



### References

- Task source: Claude Code Studio task #29

## Dev Agent Record

### Agent Model Used

sonnet

### Completion Notes List

- All 4 acceptance criteria implemented and verified
- 34 unit tests passing across 3 test modules (engine: 7, safety: 10, log: 17)
- HD Automation Log DocType created with audit-trail semantics (no create/write permissions for normal roles)
- `_create_log()` helper in engine.py silently swallows all exceptions to prevent logging from disrupting automation execution
- `_notify_rule_creator()` in safety.py sends email + realtime notification on auto-disable; also swallows exceptions
- `log_retention_days` field added to HD Settings with default 30
- AutomationList.vue updated with Executions, Last Fired, and Failure Rate columns (merged via computed from stats API)
- Key fix: `test_engine.py` tearDown now deletes HD Automation Log records before deleting rules to prevent `frappe.LinkExistsError`
- `frappe.publish_realtime` is called multiple times internally by Frappe on `db.set_value`; notification test checks for event="notification" in call list rather than asserting call count

### Change Log

- Created `helpdesk/helpdesk/doctype/hd_automation_log/__init__.py`
- Created `helpdesk/helpdesk/doctype/hd_automation_log/hd_automation_log.json`
- Created `helpdesk/helpdesk/doctype/hd_automation_log/hd_automation_log.py`
- Created `helpdesk/helpdesk/doctype/hd_automation_log/cleanup.py`
- Created `helpdesk/helpdesk/doctype/hd_automation_log/test_hd_automation_log.py`
- Modified `helpdesk/helpdesk/automation/engine.py` — timing, `_create_log()`, log on success/failure/skipped paths
- Modified `helpdesk/helpdesk/automation/safety.py` — `_notify_rule_creator()` called after auto-disable
- Modified `helpdesk/helpdesk/automation/test_engine.py` — tearDown deletes log records before rules
- Modified `helpdesk/helpdesk/doctype/hd_settings/hd_settings.json` — added `log_retention_days` field
- Modified `helpdesk/hooks.py` — daily scheduler event for `purge_old_logs`
- Modified `helpdesk/api/automation.py` — implemented `get_execution_stats()` with aggregate SQL
- Modified `desk/src/pages/automations/AutomationList.vue` — stats columns, computed merge, reload on mutations

### File List

- `helpdesk/helpdesk/doctype/hd_automation_log/__init__.py` (created)
- `helpdesk/helpdesk/doctype/hd_automation_log/hd_automation_log.json` (created)
- `helpdesk/helpdesk/doctype/hd_automation_log/hd_automation_log.py` (created)
- `helpdesk/helpdesk/doctype/hd_automation_log/cleanup.py` (created)
- `helpdesk/helpdesk/doctype/hd_automation_log/test_hd_automation_log.py` (created)
- `helpdesk/helpdesk/automation/engine.py` (modified)
- `helpdesk/helpdesk/automation/safety.py` (modified)
- `helpdesk/helpdesk/automation/test_engine.py` (modified)
- `helpdesk/helpdesk/automation/test_safety.py` (modified)
- `helpdesk/helpdesk/doctype/hd_settings/hd_settings.json` (modified)
- `helpdesk/hooks.py` (modified)
- `helpdesk/api/automation.py` (modified)
- `desk/src/pages/automations/AutomationList.vue` (modified)
