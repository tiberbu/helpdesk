# Story: Story 1.9: Incident Models / Templates

Status: done
Task ID: mn2g9u7e6rz3o7
Task Number: #25
Workflow: dev-story
Model: sonnet
Created: 2026-03-23T13:56:37.954Z

## Description

## Story 1.9: Incident Models / Templates

As an administrator, I want to create incident models with predefined fields, so that common incident types are logged consistently.

### Acceptance Criteria

- Given HD Incident Model DocType exists, when admin creates a model, they can configure: name, description, default_category, default_sub_category, default_priority, default_team, checklist_items
- Given an agent selects an incident model during ticket creation, then all predefined fields auto-populate
- Given an incident model includes checklist items, then items are displayed and must be completed before resolution
- Given fresh installation, then at least 5 default models available (Password Reset, System Outage, Access Request, Hardware Failure, Software Bug)

### Tasks
- Create HD Incident Model DocType with all specified fields
- Add incident_model Link field to HD Ticket
- Implement auto-populate logic on model selection
- Implement checklist item display and resolution validation
- Create 5 default incident model fixtures
- Write unit tests for model application and checklist validation

## Acceptance Criteria

- [ ] Given HD Incident Model DocType exists, when admin creates a model, they can configure: name, description, default_category, default_sub_category, default_priority, default_team, checklist_items
- [ ] Given an agent selects an incident model during ticket creation, then all predefined fields auto-populate
- [ ] Given an incident model includes checklist items, then items are displayed and must be completed before resolution
- [ ] Given fresh installation, then at least 5 default models available (Password Reset, System Outage, Access Request, Hardware Failure, Software Bug)

## Tasks / Subtasks

- [ ] Create HD Incident Model DocType with all specified fields
- [ ] Add incident_model Link field to HD Ticket
- [ ] Implement auto-populate logic on model selection
- [ ] Implement checklist item display and resolution validation
- [ ] Create 5 default incident model fixtures
- [ ] Write unit tests for model application and checklist validation

## Dev Notes



### References

- Task source: Claude Code Studio task #25

## Dev Agent Record

### Agent Model Used

sonnet

### Completion Notes List

**Completed:** 2026-03-23T14:09:18.374Z

t-side resolution guard]: 
   handleFieldUpdate checks ticket_checklist for incomplete mandatory items when 
   status → "Resolved"/"Closed" and calls toast.warning() + returns early.

✅ [AC #12 — 5 default fixture models]: 
   GET /api/resource/HD%20Incident%20Model → Password Reset (Low), System Outage (Urgent), 
   Access Request (Medium), Hardware Failure (High), Software Bug (Medium). All 5 present.

✅ [AC #13 — Unit tests]: 
   bench run-tests → 11/11 PASS in 1.553s
   - test_apply_model_sets_priority ✔
   - test_apply_model_sets_incident_model_reference ✔
   - test_apply_model_skips_blank_fields ✔
   - test_apply_model_creates_checklist_rows ✔
   - test_apply_model_replaces_existing_checklist ✔
   - test_apply_model_marks_checklist_uncompleted ✔
   - test_complete_checklist_item_sets_completed ✔
   - test_complete_checklist_item_toggles_off ✔
   - test_resolution_blocked_when_mandatory_items_incomplete ✔
   - test_resolution_allowed_when_all_mandatory_items_complete ✔
   - test_resolution_allowed_when_no_checklist ✔

🌐 [API tests via curl]:
   - Login → Logged In
   - Create ticket 351 → OK
   - apply_incident_model(351, "System Outage") → priority=Urgent, 4 checklist items
   - complete_checklist_item → is_completed=1, completed_by=Administrator
   - Resolve with incomplete items → ValidationError blocked ✓

✅ [Existing tests not broken]: 
   test_major_incident: 12/12 PASS | test_internal_notes: 10/10 PASS

FINAL: ✅ All 13 acceptance criteria verified — 0 issues
```

### Change Log

_(Updated by agent during implementation)_

### File List

_(Updated by agent — list all files created or modified)_
