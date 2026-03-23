# Story: Story 1.3: Multi-Level Ticket Categorization

Status: done
Task ID: mn2g8x1nqj17o2
Task Number: #19
Workflow: dev-story
Model: sonnet
Created: 2026-03-23T11:45:12.566Z

## Description

## Story 1.3: Multi-Level Ticket Categorization

As a support agent, I want to categorize tickets with Category and Sub-category, so that reporting and routing can use granular classification.

### Acceptance Criteria

- Given an administrator creates HD Ticket Category records with parent_category reference, then a hierarchical Category > Sub-category structure is established
- Given an agent selects a Category on a ticket, then Sub-category dropdown filters to show only children of selected Category
- Given "Category required on resolution" is configured in HD Settings, when an agent attempts to resolve without category, then validation error prevents resolution

### Tasks
- Create HD Ticket Category DocType with name, parent_category, description, is_active fields
- Add category and sub_category Link fields to HD Ticket DocType JSON
- Implement cascading filter for sub_category based on selected category
- Add category_required_on_resolution checkbox to HD Settings
- Implement validate hook for category requirement on resolution
- Write unit tests for categorization hierarchy and filtering
- Create migration patch and default category seed data

## Acceptance Criteria

- [x] Given an administrator creates HD Ticket Category records with parent_category reference, then a hierarchical Category > Sub-category structure is established
- [x] Given an agent selects a Category on a ticket, then Sub-category dropdown filters to show only children of selected Category
- [x] Given "Category required on resolution" is configured in HD Settings, when an agent attempts to resolve without category, then validation error prevents resolution

## Tasks / Subtasks

- [x] Create HD Ticket Category DocType with name, parent_category, description, is_active fields
- [x] Add category and sub_category Link fields to HD Ticket DocType JSON
- [x] Implement cascading filter for sub_category based on selected category
- [x] Add category_required_on_resolution checkbox to HD Settings
- [x] Implement validate hook for category requirement on resolution
- [x] Write unit tests for categorization hierarchy and filtering
- [x] Create migration patch and default category seed data

## Dev Notes

Implementation followed existing Frappe/helpdesk patterns throughout.

Key design decisions:
- `HD Ticket Category` uses `autoname: "Prompt"` so the category name IS the document name — self-reference check compares `self.parent_category == self.name` directly.
- `category` and `sub_category` on HD Ticket are visible in **both** Simple and ITIL modes (only `impact`/`urgency` are ITIL-only). This matches AC #3 from the original story requirements.
- `validate_category()` handles two concerns: (1) category required on resolution when the HD Settings flag is enabled; (2) sub_category parent integrity check.
- The Vue `TicketCategorySelect.vue` component uses `createListResource` with a reactive watch to re-fetch sub-categories on category change.

### References

- Task source: Claude Code Studio task #19

## Dev Agent Record

### Agent Model Used

sonnet

### Completion Notes List

- HD Ticket Category DocType: `hd_ticket_category.json` updated with `is_active` Check (default 1), `in_list_view` on key fields, permissions for System Manager / Agent Manager / Agent.
- `hd_ticket_category.py`: Added `validate()` calling `_validate_no_self_reference()` which throws `frappe.ValidationError` when `parent_category == name`.
- `hd_ticket.json`: Removed `hidden: 1` from `category` and `sub_category` fields; added `search_index: 1` on `category`; added `depends_on: "eval:doc.category"` on `sub_category`.
- `hd_ticket.js`: Rewrote to limit `itil_only_fields` to `["impact", "urgency"]` (not category/sub_category); added `apply_sub_category_filter()` using `frm.set_query()`; added `category` change handler.
- `hd_ticket.py`: Added `validate_category()` method checking (a) category required on resolution when HD Settings flag is set, (b) sub_category parent integrity.
- `hd_settings.json`: Added `category_required_on_resolution` Check field (default 0, depends on itil_mode_enabled) in ITIL tab.
- `TicketCategorySelect.vue`: New Vue 3 component with cascading category/sub-category dropdowns using `createListResource`.
- Patches: `add_category_fields_to_hd_ticket.py` ensures DB columns exist; `create_default_categories.py` seeds 4 top-level + 9 sub-categories.
- Tests: `test_hd_ticket_category.py` has 4 tests covering CRUD and self-ref validation; `test_hd_ticket.py` has new `TestCategoryValidation` class with 5 tests.

### Change Log

- 2026-03-23: Implementation completed by dev agent (Claude Sonnet)

### File List

**Created:**
- `helpdesk/helpdesk/doctype/hd_ticket_category/test_hd_ticket_category.py`
- `helpdesk/patches/v1_phase1/add_category_fields_to_hd_ticket.py`
- `helpdesk/patches/v1_phase1/create_default_categories.py`
- `desk/src/components/ticket/TicketCategorySelect.vue`

**Modified:**
- `helpdesk/helpdesk/doctype/hd_ticket_category/hd_ticket_category.json`
- `helpdesk/helpdesk/doctype/hd_ticket_category/hd_ticket_category.py`
- `helpdesk/helpdesk/doctype/hd_ticket/hd_ticket.json`
- `helpdesk/helpdesk/doctype/hd_ticket/hd_ticket.js`
- `helpdesk/helpdesk/doctype/hd_ticket/hd_ticket.py`
- `helpdesk/helpdesk/doctype/hd_ticket/test_hd_ticket.py`
- `helpdesk/helpdesk/doctype/hd_settings/hd_settings.json`
- `helpdesk/patches.txt`
