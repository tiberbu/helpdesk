# Story: Story 1.6: Related Ticket Linking

Status: done
Task ID: mn2g9u0mwwx3vk
Task Number: #22
Workflow: dev-story
Model: sonnet
Created: 2026-03-23T12:29:26.729Z

## Description

## Story 1.6: Related Ticket Linking

As a support agent, I want to link related tickets together, so that patterns are visible and updates can propagate between related issues.

### Acceptance Criteria

- Given an agent views Ticket A, when they click Link Ticket and select Ticket B with type Related to, then Ticket B appears in A sidebar and A appears in B sidebar (bidirectional)
- Given an agent links Ticket A to Ticket B with type Duplicate of, when saved, then Ticket A is auto-closed with status Duplicate and comment added
- Link types available: Related to, Caused by, Duplicate of

### Tasks
- Create HD Related Ticket child table DocType
- Add related_tickets Table field to HD Ticket DocType JSON
- Implement bidirectional linking logic in hd_ticket.py
- Implement auto-close on Duplicate of link type
- Create RelatedTickets.vue sidebar panel component
- Write unit tests for all link types and bidirectional behavior

## Acceptance Criteria

- [x] Given an agent views Ticket A, when they click Link Ticket and select Ticket B with type Related to, then Ticket B appears in A sidebar and A appears in B sidebar (bidirectional)
- [x] Given an agent links Ticket A to Ticket B with type Duplicate of, when saved, then Ticket A is auto-closed with status Duplicate and comment added
- [x] Link types available: Related to, Caused by, Duplicate of

## Tasks / Subtasks

- [x] Create HD Related Ticket child table DocType
- [x] Add related_tickets Table field to HD Ticket DocType JSON
- [x] Implement bidirectional linking logic in incident.py (ADR-08 — API in helpdesk/api/incident.py)
- [x] Implement auto-close on Duplicate of link type
- [x] Create RelatedTickets.vue sidebar panel component
- [x] Write unit tests for all link types and bidirectional behavior

## Dev Notes



### References

- Task source: Claude Code Studio task #22

## Dev Agent Record

### Agent Model Used

sonnet

### Completion Notes List

- All 13 unit tests pass (`Ran 13 tests in 2.839s OK`)
- Browser testing confirmed: RelatedTickets panel visible in ticket sidebar, bidirectional display working, "Link a Ticket" dialog opens correctly
- Two bugs fixed post-implementation:
  1. `TicketDetailsTab.vue`: Template used `ticket?.value?.doc?.name` but Vue auto-unwraps injected ComputedRef — fixed to `ticket?.doc?.name` and `String(ticket.doc.name)`
  2. `incident.py get_related_tickets`: `info_map` key was integer (autoincrement) but lookup used string — fixed with `str()` normalization
- API `link_tickets` confirmed working via direct browser fetch (200 OK, `{"success": true}`)
- "Duplicate" HD Ticket Status created by migration patch with `category: "Resolved"`
- Component placement: RelatedTickets placed outside the broken `overflow-y-scroll max-h-[80%]` container directly at the bottom of TicketDetailsTab

### Change Log

- 2026-03-23: Implementation complete — all backend, frontend, tests, and browser verification done

### File List

**Created:**
- `helpdesk/helpdesk/doctype/hd_related_ticket/__init__.py`
- `helpdesk/helpdesk/doctype/hd_related_ticket/hd_related_ticket.json`
- `helpdesk/helpdesk/doctype/hd_related_ticket/hd_related_ticket.py`
- `helpdesk/helpdesk/doctype/hd_related_ticket/test_hd_related_ticket.py` (13 tests)
- `helpdesk/api/incident.py`
- `helpdesk/patches/v1_phase1/add_related_ticket_linking.py`
- `desk/src/components/ticket/RelatedTickets.vue`
- `desk/src/components/ticket/LinkTicketDialog.vue`

**Modified:**
- `helpdesk/helpdesk/doctype/hd_ticket/hd_ticket.json` (added `related_tickets` Table field)
- `helpdesk/patches/v1_phase1/add_category_fields_to_hd_ticket.py` (added table existence guard)
- `helpdesk/patches.txt` (added new patch line)
- `desk/src/components/ticket-agent/TicketDetailsTab.vue` (integrated RelatedTickets, fixed v-if condition)
