# Story: Fix: Story 1.9 QA findings -- missing __ import, permission gaps, ITIL gating

Status: done
Task ID: mn39qn7ll8fa2o
Task Number: #62
Workflow: quick-dev
Model: sonnet
Created: 2026-03-23T14:16:17.719Z

## Description

## Fix Task for Story 1.9 QA Findings

See full report: docs/qa-report-task-25.md

### P1 Issues (must fix)
1. **Missing __ import in TicketDetailsTab.vue** -- Add `import { __ } from "@/translation"` to the script setup. Lines 198, 202, 227 use __() but it is never imported. Causes ReferenceError at runtime.
2. **Client-side resolution guard misses Duplicate status** -- In handleFieldUpdate(), the guard checks `value === "Resolved" || value === "Closed"` but "Duplicate" also has status_category "Resolved". Should check against the status_category, not the literal status name.

### P2 Issues (should fix)
3. **No is_agent() check in API** -- `apply_incident_model()` and `complete_checklist_item()` use has_permission but not is_agent(). Customers can call these APIs on their own tickets. Add `is_agent()` check.
4. **Remove explicit frappe.db.commit()** -- Lines 61 and 115 of incident_model.py. Frappe auto-commits whitelisted methods. Explicit commits cause test data leaks and break transaction safety.
5. **No ITIL feature flag gating** -- incident_model and ticket_checklist fields on HD Ticket should have depends_on for itil_mode_enabled. API should check the flag.
6. **Priority type mismatch** -- default_priority on HD Incident Model should be Link to HD Ticket Priority, not a Select with hardcoded values.
7. **Fixture child entries missing doctype key** -- Add `"doctype": "HD Incident Checklist Item"` to each checklist_items entry in fixtures.
8. **Clean up test data** -- Delete the 20 leaked Test Model records.

### Files to modify
- desk/src/components/ticket-agent/TicketDetailsTab.vue
- helpdesk/api/incident_model.py
- helpdesk/fixtures/hd_incident_model.json
- helpdesk/helpdesk/doctype/hd_incident_model/hd_incident_model.json
- helpdesk/helpdesk/doctype/hd_ticket/hd_ticket.json

## Acceptance Criteria

- [x] **Missing __ import in TicketDetailsTab.vue** -- Add `import { __ } from "@/translation"` to the script setup. Lines 198, 202, 227 use __() but it is never imported. Causes ReferenceError at runtime.
- [x] **Client-side resolution guard misses Duplicate status** -- In handleFieldUpdate(), the guard checks `value === "Resolved" || value === "Closed"` but "Duplicate" also has status_category "Resolved". Should check against the status_category, not the literal status name.
- [x] **No is_agent() check in API** -- `apply_incident_model()` and `complete_checklist_item()` use has_permission but not is_agent(). Customers can call these APIs on their own tickets. Add `is_agent()` check.
- [x] **Remove explicit frappe.db.commit()** -- Lines 61 and 115 of incident_model.py. Frappe auto-commits whitelisted methods. Explicit commits cause test data leaks and break transaction safety.
- [x] **No ITIL feature flag gating** -- incident_model and ticket_checklist fields on HD Ticket should have depends_on for itil_mode_enabled. API should check the flag.
- [x] **Priority type mismatch** -- default_priority on HD Incident Model should be Link to HD Ticket Priority, not a Select with hardcoded values.
- [x] **Fixture child entries missing doctype key** -- Add `"doctype": "HD Incident Checklist Item"` to each checklist_items entry in fixtures.
- [x] **Clean up test data** -- Delete the 20 leaked Test Model records.

## Tasks / Subtasks

- [x] **Missing __ import in TicketDetailsTab.vue** -- Add `import { __ } from "@/translation"` to the script setup. Lines 198, 202, 227 use __() but it is never imported. Causes ReferenceError at runtime.
- [x] **Client-side resolution guard misses Duplicate status** -- In handleFieldUpdate(), the guard checks `value === "Resolved" || value === "Closed"` but "Duplicate" also has status_category "Resolved". Should check against the status_category, not the literal status name.
- [x] **No is_agent() check in API** -- `apply_incident_model()` and `complete_checklist_item()` use has_permission but not is_agent(). Customers can call these APIs on their own tickets. Add `is_agent()` check.
- [x] **Remove explicit frappe.db.commit()** -- Lines 61 and 115 of incident_model.py. Frappe auto-commits whitelisted methods. Explicit commits cause test data leaks and break transaction safety.
- [x] **No ITIL feature flag gating** -- incident_model and ticket_checklist fields on HD Ticket should have depends_on for itil_mode_enabled. API should check the flag.
- [x] **Priority type mismatch** -- default_priority on HD Incident Model should be Link to HD Ticket Priority, not a Select with hardcoded values.
- [x] **Fixture child entries missing doctype key** -- Add `"doctype": "HD Incident Checklist Item"` to each checklist_items entry in fixtures.
- [x] **Clean up test data** -- Delete the 20 leaked Test Model records.

## Dev Notes



### References

- Task source: Claude Code Studio task #62

## Dev Agent Record

### Agent Model Used

sonnet

### Completion Notes List

- All 8 QA findings addressed: 2 P1, 5 P2, 1 cleanup task
- __ translation import added to TicketDetailsTab.vue; resolution guard now uses `ticketStatusStore.getStatus(value).category === "Resolved"` which catches Duplicate status too
- `is_agent()` guard and ITIL mode check added to both `apply_incident_model` and `complete_checklist_item`
- Both `frappe.db.commit()` calls removed (Frappe auto-commits whitelisted methods)
- `depends_on` added to `incident_model` and `ticket_checklist` fields on HD Ticket for ITIL gating
- `default_priority` on HD Incident Model changed from Select to Link → HD Ticket Priority
- All 17 checklist_items fixture entries updated with `"doctype": "HD Incident Checklist Item"`
- 20 leaked Test Model records deleted from database
- test_incident_model.py updated to enable/disable ITIL mode in setUp/tearDown
- 11/11 tests pass after all changes

### Change Log

- 2026-03-23: Fixed all 8 QA findings from QA report task-25

### File List

- desk/src/components/ticket-agent/TicketDetailsTab.vue — added `__` and `useTicketStatusStore` imports; store instance; fixed resolution guard to check status_category
- helpdesk/api/incident_model.py — added `is_agent()` import/check, ITIL mode check, removed `frappe.db.commit()` from both functions
- helpdesk/fixtures/hd_incident_model.json — added `"doctype": "HD Incident Checklist Item"` to all 17 checklist entries
- helpdesk/helpdesk/doctype/hd_incident_model/hd_incident_model.json — changed `default_priority` from Select to Link → HD Ticket Priority
- helpdesk/helpdesk/doctype/hd_ticket/hd_ticket.json — added `depends_on: itil_mode_enabled` to `incident_model` and `ticket_checklist` fields
- helpdesk/helpdesk/doctype/hd_ticket/test_incident_model.py — added ITIL mode enable/disable to setUp/tearDown
