# Story: [County-5] Escalation UI — one-click escalate/de-escalate with reason dialog

Status: done
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

- [x] Add "Escalate" button in ticket header/toolbar (next to status/assign)
- [x] Add "De-escalate" button (for L1+ agents only)
- [x] Support Level Badge on ticket header
- [x] Escalation Timeline
- [x] Ticket Sidebar

## Tasks / Subtasks

- [x] Add "Escalate" button in ticket header/toolbar (next to status/assign)
- [x] Add "De-escalate" button (for L1+ agents only)
- [x] Support Level Badge on ticket header
- [x] Escalation Timeline
- [x] Ticket Sidebar

## Dev Notes

[epic:county-support] [after:County-4]

### References

- Task source: Claude Code Studio task #341

## Dev Agent Record

### Agent Model Used

sonnet

### Completion Notes List

All escalation UI components were implemented as part of County-4 and are fully integrated:

- **EscalationDialog.vue** — modal with from→to level display, required reason textarea, calls `escalate_ticket` or `de_escalate_ticket` API
- **SupportLevelBadge.vue** — colored badge showing display_name from HD Support Level, dynamically fetched
- **EscalationEvent.vue** — timeline entry with direction badge (orange=escalation, blue=de-escalation), from→to levels, agent name, reason, timestamp
- **TicketHeader.vue** — Escalate/De-escalate buttons gated on `escalationInfo.data?.can_escalate/can_de_escalate`, SupportLevelBadge shown next to status
- **TicketDetailsTab.vue** — Support Routing section shows support_level badge, escalation_count, facility, sub_county, county (gated on `hasCountyInfo`)
- **TicketActivityPanel.vue** — parses `escalation_path` JSON field from ticket, creates `escalation_event` activity entries sorted chronologically
- **TicketAgentActivities.vue** — renders EscalationEvent component for `escalation_event` type with arrow-up/down-circle icon in orange/blue
- **helpdesk/api/escalation.py** — `get_ticket_escalation_info()` returns `can_escalate`, `can_de_escalate`, current/next/previous level metadata

Build: `yarn build` passes with 0 errors. Browser test on ticket 11981 (L0 tier) confirmed:
- "Sub-County Support" badge visible in header
- "Escalate" button visible (L0 can escalate to L1)
- De-escalate button correctly hidden (L0 cannot de-escalate)
- Escalation dialog shows "From: Sub-County Support → To: County Support"
- Support Routing sidebar section shows facility/sub_county/county
- API returns correct `can_escalate: true, can_de_escalate: false` for L0

### Change Log

- 2026-04-01: Story verified complete — all components implemented in County-4, yarn build passes, browser tested on ticket 11981

### File List

**Created (County-4):**
- `desk/src/components/ticket/EscalationDialog.vue`
- `desk/src/components/ticket/EscalationEvent.vue`
- `desk/src/components/ticket/SupportLevelBadge.vue`

**Modified (County-4):**
- `desk/src/components/ticket-agent/TicketHeader.vue`
- `desk/src/components/ticket-agent/TicketDetailsTab.vue`
- `desk/src/components/ticket-agent/TicketActivityPanel.vue`
- `desk/src/components/ticket/TicketAgentActivities.vue`
- `helpdesk/api/escalation.py`
