# Story: [County-4] Escalation chain with restrictions + SLA auto-escalation

Status: in-progress
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

- [ ] Check current ticket.support_level
- [ ] Look up support_level.allow_escalation_to_next — if False, block with message "This tier does not allow escalation"
- [ ] Find next support level (level_order + 1)
- [ ] Find the parent_team of the current assigned team
- [ ] Reassign ticket to parent team
- [ ] Update ticket.support_level to next level
- [ ] Increment ticket.escalation_count
- [ ] Add internal note: "Escalated from [Level] to [Level] by [Agent]. Reason: [required]"
- [ ] Notify new team via email/in-app
- [ ] Find all open tickets where:
- [ ] For each: auto-escalate following the same chain logic
- [ ] Add internal note: "Auto-escalated due to no response within [X] minutes at [Level]"
- [ ] Track in escalation_path

## Tasks / Subtasks

- [ ] Check current ticket.support_level
- [ ] Look up support_level.allow_escalation_to_next — if False, block with message "This tier does not allow escalation"
- [ ] Find next support level (level_order + 1)
- [ ] Find the parent_team of the current assigned team
- [ ] Reassign ticket to parent team
- [ ] Update ticket.support_level to next level
- [ ] Increment ticket.escalation_count
- [ ] Add internal note: "Escalated from [Level] to [Level] by [Agent]. Reason: [required]"
- [ ] Notify new team via email/in-app
- [ ] Find all open tickets where:
- [ ] For each: auto-escalate following the same chain logic
- [ ] Add internal note: "Auto-escalated due to no response within [X] minutes at [Level]"
- [ ] Track in escalation_path

## Dev Notes

[epic:county-support] [after:County-2]

### References

- Task source: Claude Code Studio task #340

## Dev Agent Record

### Agent Model Used

sonnet

### Completion Notes List

_(Updated by agent on completion)_

### Change Log

_(Updated by agent during implementation)_

### File List

_(Updated by agent — list all files created or modified)_
