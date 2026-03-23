# Story: Story 1.7: Per-Ticket Time Tracking

Status: done
Task ID: mn2g9u2vb6impu
Task Number: #23
Workflow: dev-story
Model: sonnet
Created: 2026-03-23T13:23:33.416Z

## Description

## Story 1.7: Per-Ticket Time Tracking

As a support agent, I want to log time spent on a ticket with both manual entry and timer mode, so that effort is tracked for reporting and billing.

### Acceptance Criteria

- Given an agent views a ticket, when they click Start timer, then a timer counts visibly (monospace font, persists in localStorage), and Stop creates an HD Time Entry with calculated duration
- Given manual entry, when agent enters duration/description/billable, then HD Time Entry is created linked to ticket and agent
- Given multiple time entries, when viewing ticket sidebar, then time summary shows total time, billable time, and entry list

### Tasks
- Create HD Time Entry DocType with ticket, agent, duration_minutes, billable, description, timestamp fields
- Create TimeTracker.vue sidebar component with start/stop timer and manual entry
- Implement timer persistence via localStorage
- Create helpdesk/api/time_tracking.py with start_timer, stop_timer, add_entry, get_summary endpoints
- Write unit tests for time entry creation and summary calculation

## Acceptance Criteria

- [ ] Given an agent views a ticket, when they click Start timer, then a timer counts visibly (monospace font, persists in localStorage), and Stop creates an HD Time Entry with calculated duration
- [ ] Given manual entry, when agent enters duration/description/billable, then HD Time Entry is created linked to ticket and agent
- [ ] Given multiple time entries, when viewing ticket sidebar, then time summary shows total time, billable time, and entry list

## Tasks / Subtasks

- [ ] Create HD Time Entry DocType with ticket, agent, duration_minutes, billable, description, timestamp fields
- [ ] Create TimeTracker.vue sidebar component with start/stop timer and manual entry
- [ ] Implement timer persistence via localStorage
- [ ] Create helpdesk/api/time_tracking.py with start_timer, stop_timer, add_entry, get_summary endpoints
- [ ] Write unit tests for time entry creation and summary calculation

## Dev Notes



### References

- Task source: Claude Code Studio task #23

## Dev Agent Record

### Agent Model Used

sonnet

### Completion Notes List

**Completed:** 2026-03-23T13:26:56.393Z

Good. Now let me explore the existing codebase structure to implement correctly.Now I understand the structure. Let me look at the sidebar and patches.txt to understand what to modify.Let me check TicketAgentFields to find where RelatedTickets was registered:Now I have full context. Let me implement all tasks. Starting with Task 1 — the DocType files:Now I have the exact DocType JSON format. Creating all files:Now run bench migrate to create the DB table:Migrate succeeded. Now sync the DocType to the bench copy:Now Task 2 — create the API module:Now Task 3 — create the Vue components. First `TimeEntryDialog.vue`:Now `TimeTracker.vue`:

### Change Log

_(Updated by agent during implementation)_

### File List

_(Updated by agent — list all files created or modified)_
