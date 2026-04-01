# Story: Fix: Escalation buttons on ticket detail — verify escalate/de-escalate actually works end-to-end

Status: in-progress
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

- [ ] ### 1. Verify Escalation Button Placement
- [ ] On ticket detail page, there should be an "Escalate" button visible when:
- [ ] Ticket has a support_level set
- [ ] The support level allows escalation (`allow_escalation_to_next = true`)
- [ ] De-escalate button visible when ticket has been escalated

## Tasks / Subtasks

- [ ] Implement changes
- [ ] Verify build passes

## Dev Notes



### References

- Task source: Claude Code Studio task #356

## Dev Agent Record

### Agent Model Used

sonnet

### Completion Notes List

_(Updated by agent on completion)_

### Change Log

_(Updated by agent during implementation)_

### File List

_(Updated by agent — list all files created or modified)_
