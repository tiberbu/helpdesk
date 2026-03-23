# Story: QA: Story 1.8: Major Incident Flag and Workflow

Status: done
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

- [x] Use Playwright MCP for browser testing (N/A - Playwright MCP not available; used API-level testing via curl instead)
- [x] Take screenshots of all major UI states (N/A - no Playwright; code review used instead)
- [x] Check browser console for errors (N/A - no Playwright; code-level analysis performed)
- [x] Document all findings in docs/ as structured QA report (P0-P3)
- [x] DO NOT modify source code

## Tasks / Subtasks

- [x] Navigate to a ticket at http://helpdesk.localhost:8004 and open the ... actions menu — verify "Declare Major Incident" option is present (code review: TicketHeader.vue adds menu item)
- [x] Click "Declare Major Incident" — verify confirmation dialog appears before any action is taken (code review: Dialog in TicketAgent.vue)
- [x] Confirm in dialog — verify red MajorIncidentBanner appears at top of ticket with elapsed time (code review: MajorIncidentBanner.vue, API verified)
- [x] Banner should show "Declared X ago" elapsed time counter (code review: ISSUE F-07 - timer is static, not live-updating)
- [x] Banner "Propagate Update" button opens a dialog with textarea; submitting posts comment on ticket and all linked tickets (API verified: propagate_update works)
- [x] Navigate to /helpdesk/major-incidents — verify dashboard shows cards with: ticket link, elapsed time, status badge, linked ticket count (code review + API verified)
- [x] When no major incidents exist, empty state shows "No active major incidents" (code review: MajorIncidentDashboard.vue line 44)
- [x] Re-click "Remove Major Incident Flag" from ... menu — verify confirmation and banner disappears (API verified: toggle works)
- [x] Post-incident review fields (Root Cause Summary, Corrective Actions, Prevention Measures) are visible in ticket form when is_major_incident=1 (FAIL - F-01: fields exist in DocType but NO frontend rendering)
- [x] Non-agent (customer) cannot flag via API (API verified: PermissionError returned for unauthenticated caller)

## Dev Notes



### References

- Task source: Claude Code Studio task #57

## Dev Agent Record

### Agent Model Used

opus

### Completion Notes List

- Adversarial review completed with 13 findings: 2 P0, 4 P1, 5 P2, 2 P3
- P0-F01: Post-incident review fields (Root Cause Summary, Corrective Actions, Prevention Measures) have no frontend rendering - acceptance criteria failure
- P0-F02: Test tearDown cannot rollback committed data; 25+ orphan test tickets pollute major incidents dashboard
- P1-F03: Backend accepts empty propagation messages
- P1-F04: No ITIL mode gating on major incident feature (contradicts Story 1.1 architecture)
- P1-F05: Toggle API design risks race conditions between concurrent agents
- P1-F06: Dashboard has N+1 query pattern with no pagination
- All 12 backend unit tests pass
- API-level testing via curl confirmed flag/unflag/propagate/summary endpoints work correctly
- Playwright MCP was not available; browser-level testing was not performed
- Full report at docs/qa-story-1.8-major-incident-adversarial-review.md

### Change Log

- 2026-03-23: Created adversarial QA report at docs/qa-story-1.8-major-incident-adversarial-review.md

### File List

- docs/qa-story-1.8-major-incident-adversarial-review.md (created)
