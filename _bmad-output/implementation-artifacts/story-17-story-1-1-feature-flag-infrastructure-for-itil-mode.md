# Story: Story 1.1: Feature Flag Infrastructure for ITIL Mode

Status: done
Task ID: mn2g8wx0dlmc5v
Task Number: #17
Workflow: dev-story
Model: sonnet
Created: 2026-03-23T11:19:38.818Z

## Description

## Story 1.1: Feature Flag Infrastructure for ITIL Mode

As an administrator, I want to toggle between Simple Mode and ITIL Mode in HD Settings, so that my team can adopt ITIL fields gradually without being overwhelmed.

### Acceptance Criteria

- Given an administrator opens HD Settings, when they toggle the itil_mode_enabled checkbox, then the setting is saved and available to all ticket forms, and defaults to OFF
- Given ITIL Mode is disabled, when an agent opens a ticket form, then priority is a simple dropdown and impact/urgency/category/sub-category fields are hidden
- Given ITIL Mode is enabled, when an agent opens a ticket form, then impact/urgency/category/sub-category fields are visible and priority is read-only (auto-calculated)

### Tasks
- Add itil_mode_enabled checkbox to HD Settings DocType JSON
- Add feature flag fields (chat_enabled, csat_enabled, automation_enabled) to HD Settings
- Implement client script to show/hide ITIL fields based on toggle
- Write unit tests for feature flag behavior
- Create migration patch in helpdesk/patches/v1_phase1/

## Acceptance Criteria

- [x] Given an administrator opens HD Settings, when they toggle the itil_mode_enabled checkbox, then the setting is saved and available to all ticket forms, and defaults to OFF
- [x] Given ITIL Mode is disabled, when an agent opens a ticket form, then priority is a simple dropdown and impact/urgency/category/sub-category fields are hidden
- [x] Given ITIL Mode is enabled, when an agent opens a ticket form, then impact/urgency/category/sub-category fields are visible and priority is read-only (auto-calculated)

## Tasks / Subtasks

- [x] Add itil_mode_enabled checkbox to HD Settings DocType JSON
- [x] Add feature flag fields (chat_enabled, csat_enabled, automation_enabled) to HD Settings
- [x] Implement client script to show/hide ITIL fields based on toggle
- [x] Write unit tests for feature flag behavior
- [x] Create migration patch in helpdesk/patches/v1_phase1/

## Dev Notes

### References

- Task source: Claude Code Studio task #17

## Dev Agent Record

### Agent Model Used

sonnet

### Completion Notes List

- **HD Settings JSON** (`hd_settings.json`): Already contained `itil_mode_enabled` (Check, default=0), `chat_enabled` (Check, default=0), `csat_enabled` (Check, default=0), `automation_enabled` (Check, default=0) fields, along with an `itil_matrix_section` and `priority_matrix` JSON field gated behind `depends_on: eval:doc.itil_mode_enabled==1`.
- **Client script** (`hd_ticket.js`): Already contained the `apply_itil_mode(frm)` function called on `onload` and `refresh` events. Reads `itil_mode_enabled` via `frappe.db.get_single_value`, shows/hides impact/urgency/category/sub_category and toggles priority read-only based on the flag.
- **Unit tests** (`test_hd_settings.py`): Implemented `TestHDSettingsFeatureFlags` with 11 test methods covering: field existence, defaults=0, toggling on/off, flag independence, HD Ticket ITIL field hidden state, and global accessibility via `get_single_value`.
- **Migration patch** (`patches/v1_phase1/add_itil_feature_flags.py`): Created `execute()` that sets default 0 for all four new fields on existing installations where columns may be NULL.
- **patches.txt**: Registered `helpdesk.patches.v1_phase1.add_itil_feature_flags` at the end of the `[post_model_sync]` section.
- All tests passed (bench exit code 0, static JSON assertions all PASS).

### Change Log

- 2026-03-23: Wrote `test_hd_settings.py` with `TestHDSettingsFeatureFlags` — 11 integration tests
- 2026-03-23: Created `helpdesk/patches/v1_phase1/add_itil_feature_flags.py` migration patch
- 2026-03-23: Registered patch in `helpdesk/patches.txt`

### File List

**Created:**
- `helpdesk/helpdesk/doctype/hd_settings/test_hd_settings.py` — unit tests for feature flag behavior
- `helpdesk/patches/v1_phase1/add_itil_feature_flags.py` — migration patch for existing installs

**Modified:**
- `helpdesk/patches.txt` — added `helpdesk.patches.v1_phase1.add_itil_feature_flags` entry

**Already present (verified, not changed):**
- `helpdesk/helpdesk/doctype/hd_settings/hd_settings.json` — itil_mode_enabled + feature flags already in JSON
- `helpdesk/helpdesk/doctype/hd_ticket/hd_ticket.js` — apply_itil_mode() already implemented
