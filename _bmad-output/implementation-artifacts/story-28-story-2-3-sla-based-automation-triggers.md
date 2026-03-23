# Story: Story 2.3: SLA-Based Automation Triggers

Status: done
Task ID: mn2gah3kvzvb42
Task Number: #28
Workflow: dev-story
Model: sonnet
Created: 2026-03-23T21:18:17.452Z

## Description

## Story 2.3: SLA-Based Automation Triggers

As an administrator, I want to trigger automations based on SLA events, so that at-risk tickets get proactive attention automatically.

### Acceptance Criteria

- SLA warning thresholds (default 30, 15, 5 min before breach) fire sla_warning trigger for matching automation rules
- SLA breach fires sla_breached trigger
- Example: rule with trigger sla_warning and action assign_to_team: Escalation reassigns ticket
- Assigned agent receives in-app notification on sla_warning

### Tasks
- Integrate SLA monitor cron job with automation trigger system
- Implement sla_warning and sla_breached trigger types
- Wire SLA events to automation engine evaluation
- Add notification delivery for SLA warning events
- Write integration tests for SLA trigger -> automation execution flow

## Acceptance Criteria

- [x] SLA warning thresholds (default 30, 15, 5 min before breach) fire sla_warning trigger for matching automation rules
- [x] SLA breach fires sla_breached trigger
- [x] Example: rule with trigger sla_warning and action assign_to_team: Escalation reassigns ticket
- [x] Assigned agent receives in-app notification on sla_warning

## Tasks / Subtasks

- [x] Integrate SLA monitor cron job with automation trigger system
- [x] Implement sla_warning and sla_breached trigger types
- [x] Wire SLA events to automation engine evaluation
- [x] Add notification delivery for SLA warning events
- [x] Write integration tests for SLA trigger -> automation execution flow

## Dev Notes



### References

- Task source: Claude Code Studio task #28

## Dev Agent Record

### Agent Model Used

sonnet

### Completion Notes List

- All 4 ACs implemented and verified by 13 passing integration tests.
- `sla_monitor.py` cron job (`*/5 * * * *`) scans open tickets with `resolution_by` set, fires `sla_warning` at configured thresholds (default 30/15/5 min) and `sla_breached` after deadline passes.
- Redis deduplication (24h TTL) ensures each threshold fires exactly once per SLA cycle; `clear_warning_dedup()` allows reset on SLA re-set.
- `notifications.py` publishes Socket.IO `sla_warning` event to `agent:{email}` room; no-op for unassigned tickets.
- All automation engine calls wrapped in try/except (NFR-A-01) so failures never interrupt SLA alerting.
- Fix applied during testing: HD Team DocType uses `autoname = field:team_name`, so `_make_team()` helper must use `team_name` key, not `name`.

### Change Log

- 2026-03-23: Created `sla_monitor.py` — cron entry point with `check_sla_breaches`, threshold logic, Redis dedup
- 2026-03-23: Created `notifications.py` — `notify_agent_sla_warning`, `_extract_agent_email` helpers
- 2026-03-23: Modified `triggers.py` — added `sla_warning`, `sla_breached` to TRIGGER_TYPES
- 2026-03-23: Modified `hd_settings.json` — added `sla_warning_thresholds` JSON field (default `[30, 15, 5]`)
- 2026-03-23: Modified `hooks.py` — added `*/5 * * * *` cron scheduler entry
- 2026-03-23: Created `test_sla_monitor_automation.py` — 13 integration tests covering all ACs
- 2026-03-23: Created `patches/v1_phase1/add_sla_warning_thresholds_setting.py` — migration patch
- 2026-03-23: Modified `patches.txt` — registered migration patch

### File List

- `helpdesk/helpdesk/doctype/hd_service_level_agreement/sla_monitor.py` (created)
- `helpdesk/helpdesk/doctype/hd_service_level_agreement/test_sla_monitor_automation.py` (created)
- `helpdesk/helpdesk/automation/notifications.py` (created)
- `helpdesk/helpdesk/automation/triggers.py` (modified)
- `helpdesk/helpdesk/doctype/hd_settings/hd_settings.json` (modified)
- `helpdesk/hooks.py` (modified)
- `helpdesk/patches/v1_phase1/add_sla_warning_thresholds_setting.py` (created)
- `helpdesk/patches.txt` (modified)
