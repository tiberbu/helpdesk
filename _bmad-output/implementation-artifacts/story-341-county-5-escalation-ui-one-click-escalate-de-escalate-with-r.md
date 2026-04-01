# Story: [County-5] Escalation UI — one-click escalate/de-escalate with reason dialog

Status: in-progress
Task ID: mnga2c8k3vq91n
Task Number: #341
Workflow: quick-dev
Model: sonnet
Created: 2026-04-01T16:55:59.693Z

## Description

## Story 5 of 7 — depends on Story 4

### Ticket Detail View Changes
1. Add "Escalate" button in ticket header/toolbar (next to status/assign)
   - Only shown if current support_level.allow_escalation_to_next is True
   - Clicking opens a dialog with:
     - Current level displayed
     - Next level displayed
     - Reason textarea (required)
     - Escalate / Cancel buttons
   - On confirm: calls escalate API, refreshes ticket

2. Add "De-escalate" button (for L1+ agents only)
   - Opens dialog showing lower tiers to send back to
   - Reason required

3. Support Level Badge on ticket header
   - Shows current tier with color from HD Support Level
   - E.g. "L0 - Sub-County Support" in blue badge

4. Escalation Timeline
   - In ticket activity/timeline, show escalation events distinctly
   - Different icon/color from regular activity
   - Shows: from → to level, agent, reason, timestamp

5. Ticket Sidebar
   - Show facility, sub_county, county info
   - Show escalation_count
   - Show current support_level

### Files to Modify
- desk/src/pages/tickets/ — ticket detail components
- Add EscalationDialog.vue component
- Add SupportLevelBadge.vue component
- Modify ticket sidebar to show hierarchy info

### Build: cd desk && yarn build

## Done Criteria
- Escalate button visible and functional
- De-escalate button for higher tiers
- Reason dialog enforced
- Support level badge on ticket
- Escalation events in timeline
- Facility/county info in sidebar
- yarn build passes

## Acceptance Criteria

- [ ] Add "Escalate" button in ticket header/toolbar (next to status/assign)
- [ ] Add "De-escalate" button (for L1+ agents only)
- [ ] Support Level Badge on ticket header
- [ ] Escalation Timeline
- [ ] Ticket Sidebar

## Tasks / Subtasks

- [ ] Add "Escalate" button in ticket header/toolbar (next to status/assign)
- [ ] Add "De-escalate" button (for L1+ agents only)
- [ ] Support Level Badge on ticket header
- [ ] Escalation Timeline
- [ ] Ticket Sidebar

## Dev Notes

[epic:county-support] [after:County-4]

### References

- Task source: Claude Code Studio task #341

## Dev Agent Record

### Agent Model Used

sonnet

### Completion Notes List

_(Updated by agent on completion)_

### Change Log

_(Updated by agent during implementation)_

### File List

_(Updated by agent — list all files created or modified)_
