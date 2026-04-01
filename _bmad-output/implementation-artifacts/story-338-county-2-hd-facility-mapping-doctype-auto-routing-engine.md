# Story: [County-2] HD Facility Mapping DocType + auto-routing engine

Status: done
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

- [x] Look up the ticket creator user → find their facility (from user.facility or a mapping)
- [x] Look up HD Facility Mapping where facility_name matches
- [x] Set ticket.facility, ticket.sub_county, ticket.county
- [x] Set ticket.support_level to the L0 support level
- [x] Assign ticket to l0_team
- [x] If no mapping found, assign to a default national team

## Tasks / Subtasks

- [x] Look up the ticket creator user → find their facility (from user.facility or a mapping)
- [x] Look up HD Facility Mapping where facility_name matches
- [x] Set ticket.facility, ticket.sub_county, ticket.county
- [x] Set ticket.support_level to the L0 support level
- [x] Assign ticket to l0_team
- [x] If no mapping found, assign to a default national team

## Dev Notes

[epic:county-support] [after:County-1]

### References

- Task source: Claude Code Studio task #338

## Dev Agent Record

### Agent Model Used

sonnet

### Completion Notes List

- Created `HD Facility Mapping` DocType with all required fields (facility_name, facility_code, sub_county, county, l0_team, l1_team, l2_team, product).
- `product` field uses `HD Brand` (existing) since `HD Multi Brand` does not exist in this codebase.
- `l1_team` and `l2_team` auto-resolve via `_auto_resolve_parent_teams()` in `HDFacilityMapping.validate()` by walking the `parent_team` chain on HD Team.
- Auto-routing implemented in `HDTicket.before_insert()` via `_apply_facility_routing()`:
  - Reads `User.facility` (custom field added via patch `add_hd_facility_mapping`)
  - Looks up `HD Facility Mapping` by facility name
  - Populates `ticket.facility`, `ticket.sub_county`, `ticket.county`
  - Sets `ticket.support_level` from `l0_team.support_level`
  - Sets `ticket.agent_group` to `l0_team`
  - Falls back to `_get_default_national_team()` (finds first team with support_level ≥ L2) when no mapping exists
  - Respects explicitly-set `agent_group` (does not override)
- Migration patch `add_hd_facility_mapping` adds:
  - `tabHD Facility Mapping` table via `frappe.reload_doctype`
  - `User-facility` Custom Field via `frappe.get_doc("Custom Field", ...)`
- CSV import template at `helpdesk/data/import_templates/hd_facility_mapping_import_template.csv` with 5 sample rows.
- 11 tests written and all pass (`Ran 11 tests in 1.344s OK`).

### Change Log

- 2026-04-01: Created HD Facility Mapping DocType (JSON + Python + test)
- 2026-04-01: Added `_apply_facility_routing()` + `_get_default_national_team()` to hd_ticket.py
- 2026-04-01: Created patch `add_hd_facility_mapping.py`, added to patches.txt
- 2026-04-01: Created CSV import template
- 2026-04-01: bench migrate ran successfully, all tables/custom fields created

### File List

**Created:**
- `helpdesk/helpdesk/doctype/hd_facility_mapping/__init__.py`
- `helpdesk/helpdesk/doctype/hd_facility_mapping/hd_facility_mapping.json`
- `helpdesk/helpdesk/doctype/hd_facility_mapping/hd_facility_mapping.py`
- `helpdesk/helpdesk/doctype/hd_facility_mapping/test_hd_facility_mapping.py`
- `helpdesk/patches/v1_phase1/add_hd_facility_mapping.py`
- `helpdesk/data/import_templates/hd_facility_mapping_import_template.csv`

**Modified:**
- `helpdesk/helpdesk/doctype/hd_ticket/hd_ticket.py` — added `_apply_facility_routing()` in `before_insert`, added module-level `_get_default_national_team()`
- `helpdesk/patches.txt` — added `add_hd_facility_mapping` entry
