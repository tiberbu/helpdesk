# Story: [County-4] Escalation chain with restrictions + SLA auto-escalation

Status: done
Task ID: mnga2c5zg6tp19
Task Number: #340
Workflow: quick-dev
Model: sonnet
Created: 2026-04-01T16:46:07.898Z

## Description

## Story 4 of 7 — depends on Stories 1, 2

### 1. Escalation Chain Logic
When agent clicks Escalate:
1. Check current ticket.support_level
2. Look up support_level.allow_escalation_to_next — if False, block with message "This tier does not allow escalation"
3. Find next support level (level_order + 1)
4. Find the parent_team of the current assigned team
5. Reassign ticket to parent team
6. Update ticket.support_level to next level
7. Increment ticket.escalation_count
8. Add internal note: "Escalated from [Level] to [Level] by [Agent]. Reason: [required]"
9. Notify new team via email/in-app

### 2. Engineering Escalation Restriction
- Escalation TO Engineering (L3) requires explicit approval or specific conditions:
  - Only L2 (National) agents can escalate to L3
  - Must provide detailed technical description
  - Optional: require manager approval (configurable)
- This is controlled by `allow_escalation_to_next` on the L2 support level being True, but L3 having it False (terminal)

### 3. SLA Auto-Escalation (Background Job)
Create a scheduled job that runs every 5 minutes:
1. Find all open tickets where:
   - Current support_level has auto_escalate_on_breach = True
   - Ticket has had no agent response for > auto_escalate_minutes
   - Ticket is not already at the highest level
2. For each: auto-escalate following the same chain logic
3. Add internal note: "Auto-escalated due to no response within [X] minutes at [Level]"
4. Track in escalation_path

### 4. De-escalation
- Higher-tier agents can send tickets back down
- Sets support_level back to lower tier
- Reassigns to the original team (or a specific child team)
- Internal note: "De-escalated from [Level] to [Level] by [Agent]. Reason: [required]"

### 5. Escalation Audit Trail
Store on ticket (JSON or child table):
```json
[
  {"from_level": "L0", "to_level": "L1", "by": "agent@email", "reason": "...", "auto": false, "at": "2026-04-01 10:00"},
  {"from_level": "L1", "to_level": "L2", "by": "system", "reason": "S

## Acceptance Criteria

- [x] Check current ticket.support_level
- [x] Look up support_level.allow_escalation_to_next — if False, block with message "This tier does not allow escalation"
- [x] Find next support level (level_order + 1)
- [x] Find the parent_team of the current assigned team
- [x] Reassign ticket to parent team
- [x] Update ticket.support_level to next level
- [x] Increment ticket.escalation_count
- [x] Add internal note: "Escalated from [Level] to [Level] by [Agent]. Reason: [required]"
- [x] Notify new team via email/in-app
- [x] Find all open tickets where: auto_escalate_on_breach=True & no agent response > minutes & not at highest level
- [x] For each: auto-escalate following the same chain logic
- [x] Add internal note: "Auto-escalated due to no response within [X] minutes at [Level]"
- [x] Track in escalation_path

## Tasks / Subtasks

- [x] Check current ticket.support_level
- [x] Look up support_level.allow_escalation_to_next — if False, block with message "This tier does not allow escalation"
- [x] Find next support level (level_order + 1)
- [x] Find the parent_team of the current assigned team
- [x] Reassign ticket to parent team
- [x] Update ticket.support_level to next level
- [x] Increment ticket.escalation_count
- [x] Add internal note: "Escalated from [Level] to [Level] by [Agent]. Reason: [required]"
- [x] Notify new team via email/in-app
- [x] Find all open tickets where: auto_escalate_on_breach=True & no agent response > minutes
- [x] For each: auto-escalate following the same chain logic
- [x] Add internal note: "Auto-escalated due to no response within [X] minutes at [Level]"
- [x] Track in escalation_path

## Dev Notes

[epic:county-support] [after:County-2]

### References

- Task source: Claude Code Studio task #340

## Dev Agent Record

### Agent Model Used

sonnet

### Completion Notes List

- HD Support Level DocType (prerequisite from County-1) was already scaffolded with the `add_hd_support_level.py` patch.
- HD Team and HD Ticket JSON updated with hierarchy + escalation fields (parent_team, support_level, territory, is_group on Team; support_level, facility, sub_county, county, escalation_count, escalation_path on Ticket).
- `helpdesk/api/escalation.py` implements: `escalate_ticket`, `de_escalate_ticket`, `get_escalation_path`, shared `_perform_escalation()` helper, and `_notify_team()` background job.
- `helpdesk/helpdesk/doctype/hd_ticket/escalation_scheduler.py` implements `auto_escalate_tickets()` which scans for eligible tickets every 5 minutes and enqueues per-ticket background jobs.
- Scheduler registered in hooks.py under the existing `*/5 * * * *` cron slot.
- Migration patch `add_escalation_fields_to_hd_ticket.py` created and registered in patches.txt.
- 20 unit tests covering: happy-path escalation, escalation count, audit trail, internal notes, all blocked cases (terminal tier, no parent team, no support level, empty reason, non-agent), de-escalation, get_escalation_path, and auto-escalation candidate detection (including skipping non-auto levels, terminal level, resolved tickets, and recent-response tickets).
- **All 20 tests pass** (`Ran 20 tests in 8.189s OK`).

### Change Log

- 2026-04-01: Created HD Support Level DocType
- 2026-04-01: Updated HD Team JSON (parent_team, support_level, territory, is_group)
- 2026-04-01: Updated HD Ticket JSON (support_level, facility, sub_county, county, escalation_count, escalation_path)
- 2026-04-01: Created helpdesk/api/escalation.py
- 2026-04-01: Created helpdesk/helpdesk/doctype/hd_ticket/escalation_scheduler.py
- 2026-04-01: Updated helpdesk/hooks.py (added auto_escalate_tickets to */5 cron)
- 2026-04-01: Created helpdesk/patches/v1_phase1/add_escalation_fields_to_hd_ticket.py
- 2026-04-01: Updated helpdesk/patches.txt
- 2026-04-01: Created helpdesk/tests/test_escalation.py (20 tests)
- 2026-04-01: bench migrate ran successfully

### File List

**Created:**
- `helpdesk/helpdesk/doctype/hd_support_level/__init__.py`
- `helpdesk/helpdesk/doctype/hd_support_level/hd_support_level.json`
- `helpdesk/helpdesk/doctype/hd_support_level/hd_support_level.py`
- `helpdesk/api/escalation.py`
- `helpdesk/helpdesk/doctype/hd_ticket/escalation_scheduler.py`
- `helpdesk/patches/v1_phase1/add_escalation_fields_to_hd_ticket.py`
- `helpdesk/tests/test_escalation.py`

**Modified:**
- `helpdesk/helpdesk/doctype/hd_team/hd_team.json` (added parent_team, support_level, territory, is_group fields)
- `helpdesk/helpdesk/doctype/hd_ticket/hd_ticket.json` (added support_level, facility, sub_county, county, escalation_count, escalation_path fields)
- `helpdesk/hooks.py` (added escalation_scheduler to */5 cron)
- `helpdesk/patches.txt` (added add_escalation_fields_to_hd_ticket)
