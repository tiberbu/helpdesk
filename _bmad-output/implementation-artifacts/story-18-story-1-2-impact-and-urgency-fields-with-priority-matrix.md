# Story: Story 1.2: Impact and Urgency Fields with Priority Matrix

Status: done
Task ID: mn2g8wzgjnyj5s
Task Number: #18
Workflow: dev-story
Model: sonnet
Created: 2026-03-23T11:26:36.412Z

## Description

## Story 1.2: Impact and Urgency Fields with Priority Matrix

As a support agent in ITIL Mode, I want to set impact and urgency on a ticket so that priority is calculated automatically from the ITIL priority matrix.

### Acceptance Criteria

- Given ITIL Mode is enabled, when an agent sets Impact to High and Urgency to High, then Priority auto-calculates to Urgent (P1 Critical) per the default matrix and priority field is read-only
- Given an administrator opens HD Settings, when they edit the priority matrix JSON, then the matrix is validated (all 9 combinations mapped) and future calculations use updated matrix
- Given a legacy ticket created before ITIL Mode, when an agent opens it, then manually-set priority is retained and agent can optionally set impact/urgency

### Tasks
- Add impact and urgency Select fields to HD Ticket DocType JSON
- Add priority_matrix JSON field to HD Settings
- Implement validate hook for priority matrix calculation in hd_ticket.py
- Create client script for read-only priority display in ITIL mode
- Write unit tests for all 9 matrix combinations
- Create migration patch for new fields

## Acceptance Criteria

- [x] Given ITIL Mode is enabled, when an agent sets Impact to High and Urgency to High, then Priority auto-calculates to Urgent (P1 Critical) per the default matrix and priority field is read-only
- [x] Given an administrator opens HD Settings, when they edit the priority matrix JSON, then the matrix is validated (all 9 combinations mapped) and future calculations use updated matrix
- [x] Given a legacy ticket created before ITIL Mode, when an agent opens it, then manually-set priority is retained and agent can optionally set impact/urgency

## Tasks / Subtasks

- [x] Add impact and urgency Select fields to HD Ticket DocType JSON
- [x] Add priority_matrix JSON field to HD Settings
- [x] Implement validate hook for priority matrix calculation in hd_ticket.py
- [x] Create client script for read-only priority display in ITIL mode
- [x] Write unit tests for all 9 matrix combinations
- [x] Create migration patch for new fields

## Dev Notes



### References

- Task source: Claude Code Studio task #18

## Dev Agent Record

### Agent Model Used

sonnet

### Completion Notes List

- All 3 acceptance criteria implemented and verified via 17 passing unit tests.
- `impact` and `urgency` Select fields were already present in `hd_ticket.json` (added by Story 1.1); Task 1 was verification-only.
- `priority_matrix` JSON field with 9-combo default was already present in `hd_settings.json` (Story 1.1); Task 2 was verification-only.
- Server-side `validate_priority_matrix()` added to `HDTicket.validate()` — reads `itil_mode_enabled` and `priority_matrix` from HD Settings, short-circuits when ITIL mode is off or when impact/urgency are empty (legacy ticket backward compat).
- HD Settings `validate_priority_matrix()` validates JSON structure, all 9 required keys, and valid priority values (Urgent/High/Medium/Low).
- Client script updated: priority is read-only only when **both** impact AND urgency have values; legacy tickets (both empty) get editable priority. Field change handlers (`impact`, `urgency`) trigger real-time read-only toggling.
- `HD Ticket Category` stub DocType created (needed by `category`/`sub_category` link fields in hd_ticket.json; full implementation is Story 1.3).
- Migration patch `add_impact_urgency_to_hd_ticket.py` is idempotent; uses `information_schema` to check column existence before `ALTER TABLE`.
- Pre-existing 11 test failures (`TestHDTicket`) are due to missing `freezegun` module — unrelated to this story.

### Change Log

- `hd_ticket.py`: Added `validate_priority_matrix()` method to `HDTicket` class; called from `validate()`.
- `hd_settings.py`: Added `import json`; added `validate_priority_matrix()` method to `HDSettings` class; called from `validate()`.
- `hd_ticket.js`: Added `impact` and `urgency` field change handlers; refactored `apply_itil_mode` to call new `update_priority_read_only()` helper; priority is read-only only when both fields are set.
- `test_hd_ticket.py`: Added `TestPriorityMatrix` class with 17 tests covering all 9 matrix combos, legacy ticket, ITIL-off guard, custom matrix, and validation edge cases.
- `patches/v1_phase1/add_impact_urgency_to_hd_ticket.py`: New migration patch for `impact`/`urgency` columns.
- `patches.txt`: Registered new patch after Story 1.1 entry.
- `doctype/hd_ticket_category/`: Created stub DocType (JSON, py, __init__.py) required by link fields.

### File List

- `helpdesk/helpdesk/doctype/hd_ticket/hd_ticket.py` — modified
- `helpdesk/helpdesk/doctype/hd_ticket/hd_ticket.js` — modified
- `helpdesk/helpdesk/doctype/hd_ticket/test_hd_ticket.py` — modified
- `helpdesk/helpdesk/doctype/hd_settings/hd_settings.py` — modified
- `helpdesk/helpdesk/doctype/hd_ticket_category/__init__.py` — created
- `helpdesk/helpdesk/doctype/hd_ticket_category/hd_ticket_category.json` — created
- `helpdesk/helpdesk/doctype/hd_ticket_category/hd_ticket_category.py` — created
- `helpdesk/patches/v1_phase1/add_impact_urgency_to_hd_ticket.py` — created
- `helpdesk/patches.txt` — modified
