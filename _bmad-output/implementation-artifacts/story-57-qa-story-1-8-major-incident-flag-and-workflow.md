# Story: QA: Story 1.8: Major Incident Flag and Workflow

Status: in-progress
Task ID: mn38urm9tr7nj4
Task Number: #57
Workflow: adversarial-review
Model: opus
Created: 2026-03-23T13:51:16.705Z

## Description

QA testing for Story 1.8 Major Incident Flag and Workflow.

## What to Test
1. Navigate to a ticket at http://helpdesk.localhost:8004 and open the ... actions menu — verify "Declare Major Incident" option is present
2. Click "Declare Major Incident" — verify confirmation dialog appears before any action is taken
3. Confirm in dialog — verify red MajorIncidentBanner appears at top of ticket with elapsed time
4. Banner should show "Declared X ago" elapsed time counter
5. Banner "Propagate Update" button opens a dialog with textarea; submitting posts comment on ticket and all linked tickets
6. Navigate to /helpdesk/major-incidents — verify dashboard shows cards with: ticket link, elapsed time, status badge, linked ticket count
7. When no major incidents exist, empty state shows "No active major incidents"
8. Re-click "Remove Major Incident Flag" from ... menu — verify confirmation and banner disappears
9. Post-incident review fields (Root Cause Summary, Corrective Actions, Prevention Measures) are visible in ticket form when is_major_incident=1
10. Non-agent (customer) cannot flag via API

## Files Changed
- helpdesk/helpdesk/doctype/hd_ticket/hd_ticket.json
- helpdesk/helpdesk/doctype/hd_settings/hd_settings.json
- helpdesk/api/incident.py
- desk/src/components/ticket/MajorIncidentBanner.vue
- desk/src/pages/major-incidents/MajorIncidentDashboard.vue
- desk/src/pages/major-incidents/MajorIncidentCard.vue
- desk/src/pages/ticket/TicketAgent.vue
- desk/src/components/ticket-agent/TicketHeader.vue
- desk/src/components/layouts/layoutSettings.ts
- desk/src/router/index.ts
- helpdesk/helpdesk/doctype/hd_ticket/test_major_incident.py

## Test URL
http://helpdesk.localhost:8004

## Credentials
See docs/testing-info.md

## Requirements
- Use Playwright MCP for browser testing
- Take screenshots of all major UI states
- Check browser console for errors
- Document all findings in docs/ as structured QA report (P0-P3)
- DO NOT modify source code

## Acceptance Criteria

- [ ] Use Playwright MCP for browser testing
- [ ] Take screenshots of all major UI states
- [ ] Check browser console for errors
- [ ] Document all findings in docs/ as structured QA report (P0-P3)
- [ ] DO NOT modify source code

## Tasks / Subtasks

- [ ] Navigate to a ticket at http://helpdesk.localhost:8004 and open the ... actions menu — verify "Declare Major Incident" option is present
- [ ] Click "Declare Major Incident" — verify confirmation dialog appears before any action is taken
- [ ] Confirm in dialog — verify red MajorIncidentBanner appears at top of ticket with elapsed time
- [ ] Banner should show "Declared X ago" elapsed time counter
- [ ] Banner "Propagate Update" button opens a dialog with textarea; submitting posts comment on ticket and all linked tickets
- [ ] Navigate to /helpdesk/major-incidents — verify dashboard shows cards with: ticket link, elapsed time, status badge, linked ticket count
- [ ] When no major incidents exist, empty state shows "No active major incidents"
- [ ] Re-click "Remove Major Incident Flag" from ... menu — verify confirmation and banner disappears
- [ ] Post-incident review fields (Root Cause Summary, Corrective Actions, Prevention Measures) are visible in ticket form when is_major_incident=1
- [ ] Non-agent (customer) cannot flag via API

## Dev Notes



### References

- Task source: Claude Code Studio task #57

## Dev Agent Record

### Agent Model Used

opus

### Completion Notes List

_(Updated by agent on completion)_

### Change Log

_(Updated by agent during implementation)_

### File List

_(Updated by agent — list all files created or modified)_
