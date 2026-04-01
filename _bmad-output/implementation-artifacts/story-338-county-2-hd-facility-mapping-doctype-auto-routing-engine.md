# Story: [County-2] HD Facility Mapping DocType + auto-routing engine

Status: in-progress
Task ID: mnga2c2jhjqe2p
Task Number: #338
Workflow: quick-dev
Model: sonnet
Created: 2026-04-01T16:46:07.773Z

## Description

## Story 2 of 7 — depends on Story 1

### 1. Create HD Facility Mapping DocType (NEW)
Maps facilities to their support teams.

Fields:
- `facility_name`: Data (required) — the Healthcare Facility name
- `facility_code`: Data — facility MFL code if available
- `sub_county`: Data (required)
- `county`: Data (required)
- `l0_team`: Link to HD Team (required) — Sub-County support team
- `l1_team`: Link to HD Team — County support team (auto-resolved from l0_team.parent_team if not set)
- `l2_team`: Link to HD Team — National team (auto-resolved)
- `product`: Link to HD Multi Brand (optional) — which product this facility uses

### 2. Auto-Routing on Ticket Creation
In HD Ticket before_insert hook or via automation:
1. Look up the ticket creator user → find their facility (from user.facility or a mapping)
2. Look up HD Facility Mapping where facility_name matches
3. Set ticket.facility, ticket.sub_county, ticket.county
4. Set ticket.support_level to the L0 support level
5. Assign ticket to l0_team
6. If no mapping found, assign to a default national team

### 3. Bulk Import Template
Create a CSV import template for HD Facility Mapping with columns:
facility_name, facility_code, sub_county, county, l0_team, l1_team

This allows bulk importing all 47 counties worth of mappings.

### Build & Test
- bench migrate
- Create test mappings for 2-3 facilities
- Create a ticket as a facility user → verify auto-assignment to correct L0 team
- Verify ticket.county and ticket.sub_county are populated

## Done Criteria
- HD Facility Mapping DocType created
- Auto-routing assigns tickets to correct L0 team based on facility
- ticket.county/sub_county auto-populated
- Import template works for bulk data
- bench build passes

## Acceptance Criteria

- [ ] Look up the ticket creator user → find their facility (from user.facility or a mapping)
- [ ] Look up HD Facility Mapping where facility_name matches
- [ ] Set ticket.facility, ticket.sub_county, ticket.county
- [ ] Set ticket.support_level to the L0 support level
- [ ] Assign ticket to l0_team
- [ ] If no mapping found, assign to a default national team

## Tasks / Subtasks

- [ ] Look up the ticket creator user → find their facility (from user.facility or a mapping)
- [ ] Look up HD Facility Mapping where facility_name matches
- [ ] Set ticket.facility, ticket.sub_county, ticket.county
- [ ] Set ticket.support_level to the L0 support level
- [ ] Assign ticket to l0_team
- [ ] If no mapping found, assign to a default national team

## Dev Notes

[epic:county-support] [after:County-1]

### References

- Task source: Claude Code Studio task #338

## Dev Agent Record

### Agent Model Used

sonnet

### Completion Notes List

_(Updated by agent on completion)_

### Change Log

_(Updated by agent during implementation)_

### File List

_(Updated by agent — list all files created or modified)_
