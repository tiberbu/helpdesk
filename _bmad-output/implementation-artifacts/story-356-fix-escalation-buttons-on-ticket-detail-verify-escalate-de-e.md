# Story: Fix: Escalation buttons on ticket detail — verify escalate/de-escalate actually works end-to-end

Status: done
Task ID: mnge0nowgvf6uk
Task Number: #356
Workflow: quick-dev
Model: sonnet
Created: 2026-04-01T18:36:47.987Z

## Description

## Problem
County-5 created EscalationDialog.vue and EscalationEvent.vue components, but screenshots show "escalate error no parent team" — the escalation UI may not be properly integrated or working.

## Requirements

### 1. Verify Escalation Button Placement
- On ticket detail page, there should be an "Escalate" button visible when:
  - Ticket has a support_level set
  - The support level allows escalation (`allow_escalation_to_next = true`)
- De-escalate button visible when ticket has been escalated

### 2. Escalation Dialog
- Clicking Escalate should open EscalationDialog.vue with:
  - Current level shown
  - Next level shown
  - Reason textarea (required)
  - Confirm button
- On confirm: call escalation API, update ticket team + support_level, log activity

### 3. Fix Error Cases
- If parent team not set → show helpful message ("No parent team configured for current team")
- If terminal level (Engineering/L3) → hide Escalate button entirely
- Test the full flow: create ticket with L0 team → escalate to L1 → verify team changes

### 4. Ticket Detail Sidebar
- Show current Support Level badge
- Show escalation history (EscalationEvent.vue in activity feed)

### Files
- `desk/src/components/ticket/EscalationDialog.vue`
- `desk/src/components/ticket/EscalationEvent.vue`
- `desk/src/components/ticket-agent/TicketDetailsTab.vue` — verify escalation section
- `helpdesk/api/escalation.py` — backend API

## Test
- http://help.frappe.local — Administrator / Velocity@2026!
- Find/create a ticket assigned to an L0 team
- Click Escalate → fill reason → confirm
- Verify ticket moves to L1 team

## Done Criteria
- Escalate button visible on appropriate tickets
- Dialog opens, reason required, confirm works
- Ticket team + support_level updated after escalation
- Activity feed shows escalation event
- De-escalate works in reverse
- Error states handled gracefully
- yarn build passes

## Acceptance Criteria

- [x] ### 1. Verify Escalation Button Placement
- [x] On ticket detail page, there should be an "Escalate" button visible when:
- [x] Ticket has a support_level set
- [x] The support level allows escalation (`allow_escalation_to_next = true`)
- [x] De-escalate button visible when ticket has been escalated

## Tasks / Subtasks

- [x] Implement changes
- [x] Verify build passes

## Dev Notes

Two bugs were found and fixed in `helpdesk/api/escalation.py`:

1. **`get_ticket_escalation_info` — missing parent_team check**: The function set
   `can_escalate = True` based only on `allow_escalation_to_next` and next-level
   existence, but did NOT check whether the ticket's assigned team has a `parent_team`
   configured. This caused the "Escalate" button to appear even when clicking it would
   always fail with "no parent team". Fix: added `parent_team` lookup before setting
   `can_escalate = True`.

2. **`de_escalate_ticket` — `from_team` captured after `doc.save()`**: The audit-trail
   entry used `doc.agent_group` for `from_team`, but by that point `doc.agent_group`
   had already been updated to `resolved_team` (the lower-level team). This meant
   `from_team == to_team` in every de-escalation entry. Fix: capture `original_team =
   doc.agent_group` before updating the field.

All Vue components (EscalationDialog, EscalationEvent, TicketHeader, TicketDetailsTab,
TicketAgentActivities, TicketActivityPanel) were already correctly implemented and
identical between dev and bench. No frontend changes were needed.

### References

- Task source: Claude Code Studio task #356

## Dev Agent Record

### Agent Model Used

sonnet

### Completion Notes List

- Verified all escalation Vue components were already correctly wired up (TicketHeader,
  EscalationDialog, EscalationEvent, SupportLevelBadge, TicketDetailsTab, TicketActivityPanel)
- Fixed `get_ticket_escalation_info`: now checks `agent_group.parent_team` before
  `can_escalate = True` — button correctly hidden when team has no parent
- Fixed `de_escalate_ticket`: `from_team` now captured before `doc.save()` so audit
  trail is accurate
- Browser tested: Escalate button visible on ticket #303 (L0 / Westlands Sub-County
  Team), dialog shows Sub-County Support → County Support, reason required, confirm
  submits and updates ticket to L1-County / Nairobi County Team
- API tested: full escalate → de-escalate → re-escalate cycle on ticket #303 all succeed
  with correct audit trail entries
- yarn build passes (✓ built in 32.07s, no errors)

### Change Log

- `helpdesk/api/escalation.py`: Fixed `get_ticket_escalation_info` to check
  `parent_team` before `can_escalate = True`
- `helpdesk/api/escalation.py`: Fixed `de_escalate_ticket` to capture `original_team`
  before `doc.agent_group` update so audit trail `from_team` is correct

### File List

- `helpdesk/api/escalation.py` — modified (2 bug fixes)
- `helpdesk/api/escalation.py` (bench copy) — synced
