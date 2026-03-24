# Story: Fix: Story 1.9 QA Issues - Remove incorrect ITIL mode gating + missing completed_at display

Status: in-progress
Task ID: mn49psk63oc47m
Task Number: #259
Workflow: quick-dev
Model: sonnet
Created: 2026-03-24T07:03:38.046Z

## Description

## P1: Remove ITIL mode gating from incident model APIs

The story explicitly states: "Incident Models are available in both Simple and ITIL Mode. No feature flag gating required for Story 1.9."

But both `apply_incident_model` and `complete_checklist_item` in `helpdesk/api/incident_model.py` have ITIL mode guards that block usage when ITIL mode is off.

### Fix:
1. Remove lines 30-31 in `incident_model.py` (`if not frappe.db.get_single_value("HD Settings", "itil_mode_enabled"): frappe.throw(...)`)
2. Remove lines 96-97 (same guard in `complete_checklist_item`)
3. Remove unit tests that expect ITIL gating: `test_apply_model_raises_validation_error_when_itil_disabled` and `test_complete_checklist_item_raises_when_itil_disabled`
4. Apply changes to BOTH dev and bench copies
5. Reload gunicorn after changes

## P2: Add completed_at display in TicketChecklist.vue

AC10 says completed items should show "completed_by + completed_at details" but only completed_by is displayed.

### Fix:
In `desk/src/components/ticket/TicketChecklist.vue`, around line 69, add completed_at after completed_by:
```html
{{ item.completed_by }}
<template v-if="item.completed_at"> &middot; {{ item.completed_at }}</template>
```
Rebuild frontend after change.

## P2: Resolution validation edge case on model re-application

When re-applying a model to an already-Resolved ticket, validation blocks save since new checklist items are incomplete. Consider checking `doc.has_value_changed("status")` in `validate_checklist_before_resolution()` so validation only fires on status transition.

See full QA report: docs/qa-report-epic1-story-1.9.md

## Acceptance Criteria

- [x] Remove lines 30-31 in `incident_model.py` (`if not frappe.db.get_single_value("HD Settings", "itil_mode_enabled"): frappe.throw(...)`)
- [x] Remove lines 96-97 (same guard in `complete_checklist_item`)
- [x] Remove unit tests that expect ITIL gating: `test_apply_model_raises_validation_error_when_itil_disabled` and `test_complete_checklist_item_raises_when_itil_disabled`
- [x] Apply changes to BOTH dev and bench copies
- [x] Reload gunicorn after changes

## Tasks / Subtasks

- [x] Remove lines 30-31 in `incident_model.py` (`if not frappe.db.get_single_value("HD Settings", "itil_mode_enabled"): frappe.throw(...)`)
- [x] Remove lines 96-97 (same guard in `complete_checklist_item`)
- [x] Remove unit tests that expect ITIL gating: `test_apply_model_raises_validation_error_when_itil_disabled` and `test_complete_checklist_item_raises_when_itil_disabled`
- [x] Apply changes to BOTH dev and bench copies
- [x] Reload gunicorn after changes

## Dev Notes



### References

- Task source: Claude Code Studio task #259

## Dev Agent Record

### Agent Model Used

sonnet

### Completion Notes List

- Removed ITIL mode guards from `apply_incident_model` and `complete_checklist_item` in `incident_model.py` — incident models now work in both Simple and ITIL mode.
- Removed `test_apply_model_raises_validation_error_when_itil_disabled` and `test_complete_checklist_item_raises_when_itil_disabled` tests that expected the now-removed guards.
- Added `completed_at` display in `TicketChecklist.vue` (P2 fix).
- Fixed resolution validation edge case: `validate_checklist_before_resolution` now uses `has_value_changed("status")` to only fire on status transitions, not general saves (e.g. re-applying a model to an already-resolved ticket).
- All 19 tests pass. Frontend built and gunicorn reloaded.

### Change Log

- 2026-03-24: Removed ITIL mode gating from `helpdesk/api/incident_model.py` (both dev and bench)
- 2026-03-24: Removed ITIL gating tests from `test_incident_model.py` (both dev and bench)
- 2026-03-24: Added `completed_at` display to `TicketChecklist.vue` (both dev and bench)
- 2026-03-24: Fixed resolution validation edge case in `hd_ticket.py` with `has_value_changed("status")` (both dev and bench)
- 2026-03-24: Rebuilt frontend, reloaded gunicorn

### File List

- `helpdesk/api/incident_model.py` — removed ITIL mode guards
- `helpdesk/helpdesk/doctype/hd_ticket/test_incident_model.py` — removed 2 ITIL gating tests
- `helpdesk/helpdesk/doctype/hd_ticket/hd_ticket.py` — added `has_value_changed("status")` guard
- `desk/src/components/ticket/TicketChecklist.vue` — added `completed_at` display
- (All above applied to both `/home/ubuntu/bmad-project/helpdesk/` and `/home/ubuntu/frappe-bench/apps/helpdesk/`)
