# Story: Fix: Story 1.8 Major Incident — P0/P1 issues (missing post-incident review UI, missing affected_customer_count, inverted toast, no ITIL gating, static timer, test data leak)

Status: in-progress
Task ID: mn396h6mz9y7ax
Task Number: #60
Workflow: quick-dev
Model: sonnet
Created: 2026-03-23T14:16:17.709Z

## Description

## QA Findings from qa-report-task-24.md

### P0 Issues (must fix)
1. **Post-incident review fields not rendered in Vue frontend** — AC-3 requires root_cause_summary, corrective_actions, prevention_measures to appear in the helpdesk UI when a ticket is a major incident. The fields exist in hd_ticket.json but are NEVER rendered in any Vue component. Need to add a PostIncidentReview section in TicketAgent.vue or TicketSidebar.
2. **Affected customer count missing** — AC-4 requires affected_customer_count on dashboard cards. The get_major_incident_summary API does not compute it, and MajorIncidentCard.vue does not display it. Must compute unique raised_by across major incident + linked tickets.

### P1 Issues (should fix)
3. **Elapsed time in banner is static** — MajorIncidentBanner.vue computes elapsedText once but has no setInterval to tick. Add a reactive timer.
4. **No ITIL mode gating** — Backend APIs and frontend components dont check itil_mode_enabled. Gate the Declare Major Incident menu, sidebar link, and API endpoints behind the feature flag.
5. **Toast message inverted** — TicketAgent.vue onSuccess callback reads old doc value. Fix by using the API response is_major_incident value instead.
6. **Test data leak** — tearDown uses rollback but APIs call commit. Fix tearDown to explicitly delete created test tickets and comments.

### P2 Issues (nice to fix)
7. linkedCount in banner may be 0 due to child table not fetched
8. Realtime room format should be user:{email} not agent:{email}
9. No pagination on get_major_incident_summary
10. Propagated updates should be internal (is_internal=1)
11. Toggle API is race-condition prone

See docs/qa-report-task-24.md for full details.

## Acceptance Criteria

- [ ] **Post-incident review fields not rendered in Vue frontend** — AC-3 requires root_cause_summary, corrective_actions, prevention_measures to appear in the helpdesk UI when a ticket is a major incident. The fields exist in hd_ticket.json but are NEVER rendered in any Vue component. Need to add a PostIncidentReview section in TicketAgent.vue or TicketSidebar.
- [ ] **Affected customer count missing** — AC-4 requires affected_customer_count on dashboard cards. The get_major_incident_summary API does not compute it, and MajorIncidentCard.vue does not display it. Must compute unique raised_by across major incident + linked tickets.
- [ ] **Elapsed time in banner is static** — MajorIncidentBanner.vue computes elapsedText once but has no setInterval to tick. Add a reactive timer.
- [ ] **No ITIL mode gating** — Backend APIs and frontend components dont check itil_mode_enabled. Gate the Declare Major Incident menu, sidebar link, and API endpoints behind the feature flag.
- [ ] **Toast message inverted** — TicketAgent.vue onSuccess callback reads old doc value. Fix by using the API response is_major_incident value instead.
- [ ] **Test data leak** — tearDown uses rollback but APIs call commit. Fix tearDown to explicitly delete created test tickets and comments.
- [ ] linkedCount in banner may be 0 due to child table not fetched
- [ ] Realtime room format should be user:{email} not agent:{email}
- [ ] No pagination on get_major_incident_summary
- [ ] Propagated updates should be internal (is_internal=1)
- [ ] Toggle API is race-condition prone

## Tasks / Subtasks

- [ ] **Post-incident review fields not rendered in Vue frontend** — AC-3 requires root_cause_summary, corrective_actions, prevention_measures to appear in the helpdesk UI when a ticket is a major incident. The fields exist in hd_ticket.json but are NEVER rendered in any Vue component. Need to add a PostIncidentReview section in TicketAgent.vue or TicketSidebar.
- [ ] **Affected customer count missing** — AC-4 requires affected_customer_count on dashboard cards. The get_major_incident_summary API does not compute it, and MajorIncidentCard.vue does not display it. Must compute unique raised_by across major incident + linked tickets.
- [ ] **Elapsed time in banner is static** — MajorIncidentBanner.vue computes elapsedText once but has no setInterval to tick. Add a reactive timer.
- [ ] **No ITIL mode gating** — Backend APIs and frontend components dont check itil_mode_enabled. Gate the Declare Major Incident menu, sidebar link, and API endpoints behind the feature flag.
- [ ] **Toast message inverted** — TicketAgent.vue onSuccess callback reads old doc value. Fix by using the API response is_major_incident value instead.
- [ ] **Test data leak** — tearDown uses rollback but APIs call commit. Fix tearDown to explicitly delete created test tickets and comments.
- [ ] linkedCount in banner may be 0 due to child table not fetched
- [ ] Realtime room format should be user:{email} not agent:{email}
- [ ] No pagination on get_major_incident_summary
- [ ] Propagated updates should be internal (is_internal=1)
- [ ] Toggle API is race-condition prone

## Dev Notes



### References

- Task source: Claude Code Studio task #60

## Dev Agent Record

### Agent Model Used

sonnet

### Completion Notes List

_(Updated by agent on completion)_

### Change Log

_(Updated by agent during implementation)_

### File List

_(Updated by agent — list all files created or modified)_
