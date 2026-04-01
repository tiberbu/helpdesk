# Story: Feat: Ticket list — add Support Level and County columns + filter options

Status: in-progress
Task ID: mnge467nmg8lf5
Task Number: #359
Workflow: quick-dev
Model: sonnet
Created: 2026-04-01T18:49:43.058Z

## Description

## Problem
Tickets now have support_level, county, and sub_county fields but the ticket list view does not display or filter by them. Agents cannot see at a glance which tier/location a ticket belongs to.

## Requirements

### 1. Ticket List Columns
- Add optional columns to the ticket list:
  - **Support Level** — show as colored badge (L0=blue, L1=yellow, L2=orange, L3=red)
  - **County** — text
- These should be toggleable via the Columns selector (already exists)

### 2. Filter Options
- Add filter for Support Level (dropdown with all HD Support Level options)
- Add filter for County (dropdown with distinct counties from tickets)
- These help agents at higher tiers filter tickets by location

### 3. Ticket Detail Sidebar
- Verify the county support panel (already partially implemented in TicketDetailsTab.vue) shows:
  - Support Level as badge
  - County
  - Sub-County
  - Assigned Team with tier indicator
  - Escalation count (if escalated)

## Files
- Ticket list component (check desk/src/pages/ticket/ for the list view)
- Column configuration
- Filter configuration
- `desk/src/components/ticket-agent/TicketDetailsTab.vue` — verify sidebar panel

## Done Criteria
- Support Level + County visible as columns in ticket list
- Filters work for Support Level and County
- Ticket detail sidebar shows full county support info
- Badges are colored appropriately
- yarn build passes

## Acceptance Criteria

- [ ] ### 1. Ticket List Columns
- [ ] Add optional columns to the ticket list:
- [ ] **Support Level** — show as colored badge (L0=blue, L1=yellow, L2=orange, L3=red)
- [ ] **County** — text
- [ ] These should be toggleable via the Columns selector (already exists)

## Tasks / Subtasks

- [ ] Implement changes
- [ ] Verify build passes

## Dev Notes



### References

- Task source: Claude Code Studio task #359

## Dev Agent Record

### Agent Model Used

sonnet

### Completion Notes List

_(Updated by agent on completion)_

### Change Log

_(Updated by agent during implementation)_

### File List

_(Updated by agent — list all files created or modified)_
