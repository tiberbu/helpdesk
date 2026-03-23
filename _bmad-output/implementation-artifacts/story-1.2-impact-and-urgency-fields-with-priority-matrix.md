# Story 1.2: Impact and Urgency Fields with Priority Matrix

Status: ready-for-dev

## Story

As a support agent in ITIL Mode,
I want to set impact and urgency on a ticket so that priority is calculated automatically from the ITIL priority matrix,
so that ticket prioritization is consistent and objective.

## Acceptance Criteria

1. **[Auto-Calculate Priority — High/High]** Given ITIL Mode is enabled (`itil_mode_enabled = 1`), when an agent sets `impact` to "High" and `urgency` to "High" on a ticket, then the `priority` field auto-calculates to "Urgent" per the default matrix, and the `priority` field is read-only (not editable by the agent).

2. **[All 9 Matrix Combinations]** Given ITIL Mode is enabled, when an agent sets any combination of impact (High/Medium/Low) and urgency (High/Medium/Low), then priority is calculated from the active matrix in HD Settings per the following default mapping:
   - High-High → Urgent
   - High-Medium → High
   - High-Low → Medium
   - Medium-High → High
   - Medium-Medium → Medium
   - Medium-Low → Low
   - Low-High → Medium
   - Low-Medium → Low
   - Low-Low → Low

3. **[Priority Field Read-Only in ITIL Mode]** Given ITIL Mode is enabled and either `impact` or `urgency` is set on a ticket, when the ticket form is rendered, then the `priority` field is read-only and displays the auto-calculated value — the agent cannot manually override it.

4. **[Configurable Priority Matrix]** Given an administrator opens HD Settings, when they edit the `priority_matrix` JSON field with a valid 9-entry mapping, then the matrix is saved, and subsequent priority calculations on new and updated tickets use the updated matrix values.

5. **[Matrix Validation]** Given an administrator edits the `priority_matrix` JSON in HD Settings, when they save with fewer than 9 combinations or with invalid keys, then a validation error is raised listing the missing/invalid combinations, and the save is rejected.

6. **[Legacy Ticket Backward Compatibility]** Given a ticket created before ITIL Mode was enabled (impact and urgency fields are empty), when an agent opens the ticket with ITIL Mode active, then the existing manually-set priority is retained as-is; the `priority` field remains editable only when both `impact` and `urgency` are empty (i.e., no ITIL classification yet applied).

7. **[Server-Side Validation Hook]** Given any ticket save event (create or update), when ITIL Mode is enabled and both `impact` and `urgency` have values, then the server-side `validate` hook reads the `priority_matrix` from HD Settings and assigns the correct priority — client-side calculation alone is insufficient.

8. **[Migration Patch for New Fields]** Given a pre-existing helpdesk installation, when the Phase 1 migration patch runs, then the `impact` and `urgency` Select fields are present on HD Ticket (if not already added by Story 1.1), and the `priority_matrix` JSON field is present in HD Settings with the default matrix, without any data loss.

9. **[Unit Tests — All 9 Combinations]** Given the priority matrix implementation, when the test suite runs, then unit tests for all 9 impact × urgency combinations pass, plus edge-case tests for legacy records (empty impact/urgency) and custom matrix validation, achieving ≥80% coverage on new backend code.

10. **[ITIL Mode Disabled — No Change]** Given ITIL Mode is disabled (`itil_mode_enabled = 0`), when an agent saves a ticket, then the priority matrix logic is NOT invoked and priority behaves exactly as it did before Phase 1 (agent can set it manually, no auto-calculation).

## Tasks / Subtasks

- [ ] Task 1 — Verify / finalize `impact` and `urgency` fields on HD Ticket DocType JSON (AC: #1, #2, #6)
  - [ ] 1.1 Open `helpdesk/helpdesk/doctype/hd_ticket/hd_ticket.json`
  - [ ] 1.2 Confirm `impact` Select field exists with options `High\nMedium\nLow`; add if missing (Story 1.1 may have added stubs)
  - [ ] 1.3 Confirm `urgency` Select field exists with options `High\nMedium\nLow`; add if missing
  - [ ] 1.4 Ensure both fields have `hidden: 1` as default (controlled by client script when ITIL mode is on — see Story 1.1 Task 2)
  - [ ] 1.5 Ensure both fields are placed adjacent to the `priority` field in field order for logical grouping

- [ ] Task 2 — Verify / finalize `priority_matrix` JSON field on HD Settings (AC: #4, #5)
  - [ ] 2.1 Open `helpdesk/helpdesk/doctype/hd_settings/hd_settings.json`
  - [ ] 2.2 Confirm `priority_matrix` JSON field exists (Story 1.1 may have added it); add if missing
  - [ ] 2.3 Ensure the field has `depends_on: "eval:doc.itil_mode_enabled==1"` so it only shows in HD Settings when ITIL Mode is on
  - [ ] 2.4 Confirm the default value JSON string contains all 9 valid combinations per ADR-03

- [ ] Task 3 — Implement server-side priority matrix `validate` hook in `hd_ticket.py` (AC: #1, #2, #3, #7, #10)
  - [ ] 3.1 Open `helpdesk/helpdesk/doctype/hd_ticket/hd_ticket.py` (or the override module at `helpdesk/helpdesk/overrides/hd_ticket.py`)
  - [ ] 3.2 Implement `validate_priority_matrix(doc, method=None)` function:
    - Read `itil_mode_enabled` from HD Settings using `frappe.db.get_single_value("HD Settings", "itil_mode_enabled")`
    - If `itil_mode_enabled == 0`, return immediately (no change — AC #10)
    - If `itil_mode_enabled == 1` and both `doc.impact` and `doc.urgency` are non-empty:
      - Read `priority_matrix` JSON from HD Settings
      - Construct key `f"{doc.impact}-{doc.urgency}"`
      - Look up priority in matrix; assign to `doc.priority`
    - If `itil_mode_enabled == 1` but impact or urgency is empty (legacy ticket): leave priority unchanged (AC #6)
  - [ ] 3.3 Register the hook in `helpdesk/hooks.py` under `doc_events["HD Ticket"]["validate"]` if not already registered

- [ ] Task 4 — Implement HD Settings `validate` hook for priority matrix validation (AC: #4, #5)
  - [ ] 4.1 Open `helpdesk/helpdesk/doctype/hd_settings/hd_settings.py`
  - [ ] 4.2 Add or update `validate(self)` method to check `priority_matrix` field when `itil_mode_enabled == 1`:
    - Parse JSON; if malformed raise `frappe.ValidationError` with descriptive message
    - Verify all 9 required keys are present: `High-High`, `High-Medium`, `High-Low`, `Medium-High`, `Medium-Medium`, `Medium-Low`, `Low-High`, `Low-Medium`, `Low-Low`
    - For each key verify the value is one of the valid Frappe Helpdesk priority values (`Urgent`, `High`, `Medium`, `Low`)
    - If any key is missing or invalid, raise `frappe.ValidationError` listing the offending keys

- [ ] Task 5 — Update client script to make priority read-only when ITIL matrix applies (AC: #3, #6, #10)
  - [ ] 5.1 Open `helpdesk/helpdesk/doctype/hd_ticket/hd_ticket.js`
  - [ ] 5.2 In the existing ITIL mode client script (from Story 1.1), update the `itil_mode_enabled == 1` branch:
    - After showing `impact` and `urgency` fields, add listener for changes on both fields
    - When both `impact` and `urgency` have values: set `priority` field as read-only (`frm.set_df_property("priority", "read_only", 1)`) and trigger form refresh to show calculated value
    - When impact or urgency is cleared: if ticket is a legacy record (no prior ITIL classification), make `priority` editable again (`frm.set_df_property("priority", "read_only", 0)`)
  - [ ] 5.3 Ensure the client script reflects the server-calculated priority after save (not just client-side preview — server is authoritative per AC #7)

- [ ] Task 6 — Create migration patch for impact/urgency fields (AC: #8)
  - [ ] 6.1 Confirm `helpdesk/patches/v1_phase1/` directory exists (created in Story 1.1)
  - [ ] 6.2 Create `helpdesk/patches/v1_phase1/add_impact_urgency_to_hd_ticket.py` with an `execute()` function:
    - Check if `impact` column exists on `tabHD Ticket`; add if absent using `frappe.db.add_column`
    - Check if `urgency` column exists on `tabHD Ticket`; add if absent
    - Note: `priority_matrix` on HD Settings should already exist from Story 1.1 patch; add defensive check
  - [ ] 6.3 Register patch in `helpdesk/patches.txt` (after the Story 1.1 patch entry)

- [ ] Task 7 — Write unit tests for all 9 matrix combinations and edge cases (AC: #9)
  - [ ] 7.1 Open (or create) `helpdesk/helpdesk/doctype/hd_ticket/test_hd_ticket.py`
  - [ ] 7.2 Write `test_priority_matrix_high_high` — set impact=High, urgency=High, assert priority == "Urgent"
  - [ ] 7.3 Write `test_priority_matrix_high_medium` — assert priority == "High"
  - [ ] 7.4 Write `test_priority_matrix_high_low` — assert priority == "Medium"
  - [ ] 7.5 Write `test_priority_matrix_medium_high` — assert priority == "High"
  - [ ] 7.6 Write `test_priority_matrix_medium_medium` — assert priority == "Medium"
  - [ ] 7.7 Write `test_priority_matrix_medium_low` — assert priority == "Low"
  - [ ] 7.8 Write `test_priority_matrix_low_high` — assert priority == "Medium"
  - [ ] 7.9 Write `test_priority_matrix_low_medium` — assert priority == "Low"
  - [ ] 7.10 Write `test_priority_matrix_low_low` — assert priority == "Low"
  - [ ] 7.11 Write `test_legacy_ticket_retains_priority` — set impact=None, urgency=None with ITIL mode on; assert existing priority unchanged
  - [ ] 7.12 Write `test_itil_mode_off_no_calculation` — set impact=High, urgency=High with `itil_mode_enabled=0`; assert priority NOT changed to "Urgent"
  - [ ] 7.13 Write `test_custom_matrix_validation_missing_keys` — save HD Settings with priority_matrix missing 1 key; assert `frappe.ValidationError` raised
  - [ ] 7.14 Write `test_custom_matrix_used_when_set` — save a custom matrix (e.g. High-High → "Medium"), save a ticket; assert priority calculated from custom matrix
  - [ ] 7.15 Ensure all tests use `addCleanup` to restore `itil_mode_enabled` and `priority_matrix` to defaults

## Dev Notes

### Architecture Patterns

- **Server-Side Authority:** Priority calculation MUST be server-side via the `validate` hook. Client-side JS is for UX only (read-only display, instant feedback). The server is always authoritative per AC #7. [Source: architecture.md#ADR-03]

- **Hook Registration Pattern:** The `validate` hook for HD Ticket is already declared in the architecture doc:
  ```python
  # hooks.py doc_events pattern
  doc_events = {
      "HD Ticket": {
          "validate": "helpdesk.helpdesk.overrides.hd_ticket.validate_priority_matrix",
          "on_update": "helpdesk.helpdesk.overrides.hd_ticket.evaluate_automation_rules",
      }
  }
  ```
  Check whether the implementation lives in `hd_ticket.py` directly or in `helpdesk/helpdesk/overrides/hd_ticket.py` — follow the existing pattern in the repo. [Source: architecture.md#ADR-01]

- **HD Settings Singleton:** Always access via `frappe.db.get_single_value("HD Settings", fieldname)` for individual fields, or `frappe.get_single("HD Settings")` for the full document. NEVER `frappe.get_doc("HD Settings", "HD Settings")` with a name argument. [Source: story-1.1 Dev Notes]

- **Priority Matrix Default (ADR-03):**
  ```json
  {
    "High-High": "Urgent",
    "High-Medium": "High",
    "High-Low": "Medium",
    "Medium-High": "High",
    "Medium-Medium": "Medium",
    "Medium-Low": "Low",
    "Low-High": "Medium",
    "Low-Medium": "Low",
    "Low-Low": "Low"
  }
  ```
  [Source: architecture.md#ADR-03]

- **Feature Flag Check Pattern:** Always guard ITIL logic with the feature flag to ensure Simple Mode is unaffected (AC #10):
  ```python
  if not frappe.db.get_single_value("HD Settings", "itil_mode_enabled"):
      return
  ```

- **Frappe Field Type — JSON:** The `priority_matrix` field uses Frappe's `JSON` fieldtype, which stores the value as a JSON string in the database. When reading via Python, use `json.loads(value)` if accessing via raw DB; via `frappe.get_single` the framework auto-parses it.

- **Client Script `frm.set_df_property`:** Use this pattern for read-only toggling:
  ```javascript
  // Make priority read-only when ITIL matrix is active
  frm.set_df_property("priority", "read_only", 1);
  frm.refresh_field("priority");
  ```

- **Backward Compatibility Rule:** If `doc.impact` or `doc.urgency` is falsy (empty string or None), the matrix calculation must NOT run — legacy tickets retain their manually-set priority. This is AC #6 and critical for upgrades.

### Files to Create / Modify

| Action | Path | Notes |
|--------|------|-------|
| Modify | `helpdesk/helpdesk/doctype/hd_ticket/hd_ticket.json` | Verify/finalize `impact` and `urgency` Select fields |
| Modify | `helpdesk/helpdesk/doctype/hd_ticket/hd_ticket.py` | Add `validate_priority_matrix` logic (or `overrides/hd_ticket.py`) |
| Modify | `helpdesk/helpdesk/doctype/hd_ticket/hd_ticket.js` | Update client script — priority read-only when both fields set |
| Modify | `helpdesk/helpdesk/doctype/hd_settings/hd_settings.json` | Verify `priority_matrix` JSON field present |
| Modify | `helpdesk/helpdesk/doctype/hd_settings/hd_settings.py` | Add matrix validation in `validate()` |
| Modify | `helpdesk/hooks.py` | Register `validate` hook if not done in Story 1.1 |
| Create | `helpdesk/patches/v1_phase1/add_impact_urgency_to_hd_ticket.py` | Migration patch for new ticket fields |
| Modify | `helpdesk/patches.txt` | Register migration patch |
| Create/Modify | `helpdesk/helpdesk/doctype/hd_ticket/test_hd_ticket.py` | Unit tests for all 9 combinations + edge cases |

### Testing Standards

- Minimum **80% unit test coverage** on all new backend logic (NFR-M-01).
- Use `frappe.tests.utils.FrappeTestCase` as base class.
- Tests must be self-contained: use `addCleanup` to restore HD Settings (`itil_mode_enabled`, `priority_matrix`) after each test.
- Run tests with: `bench --site <site> run-tests --module helpdesk.helpdesk.doctype.hd_ticket.test_hd_ticket`
- All 9 matrix combinations must have individual test methods (AC #9).

### Constraints

- Do NOT break existing HD Ticket behavior in Simple Mode (`itil_mode_enabled = 0`) — the validate hook must short-circuit immediately when ITIL mode is off (AC #10).
- Do NOT use Custom Fields mechanism — modify DocType JSON directly (AR-04).
- Do NOT manually set `doc.priority` outside of the matrix lookup — always consult the stored matrix so custom configurations are respected (AC #4).
- Legacy tickets with empty `impact`/`urgency` MUST retain their existing priority — no overwrite (AC #6).
- i18n: All user-facing validation error messages must use `frappe._()` in Python and `__()` in JS.
- Priority values in the matrix must match the actual options on the HD Ticket `priority` Select field (case-sensitive).

### Project Structure Notes

- **Depends on Story 1.1:** Story 1.1 adds `itil_mode_enabled` to HD Settings and stub `impact`/`urgency` fields to HD Ticket. This story implements the actual calculation logic on top of those stubs. Verify Story 1.1 is merged before starting.
- **Override Module Location:** Check whether `helpdesk/helpdesk/overrides/hd_ticket.py` exists; if so, add the matrix logic there rather than in the DocType controller `hd_ticket.py` to follow the existing override pattern.
- **Patch Sequencing:** The Story 1.2 migration patch must run AFTER the Story 1.1 patch (`add_feature_flags_to_hd_settings`). Ensure correct ordering in `patches.txt`.
- **No New DocTypes:** This story adds no new DocTypes — it only extends HD Ticket and HD Settings with logic. New DocTypes for this epic are defined in Story 1.3 (HD Ticket Category) and later stories.

### References

- Story 1.2 acceptance criteria: [Source: _bmad-output/planning-artifacts/epics.md#Story 1.2]
- FR-IM-01 (Impact, urgency, priority matrix): [Source: _bmad-output/planning-artifacts/epics.md#Functional Requirements]
- ADR-01 (Extend HD Ticket): [Source: _bmad-output/planning-artifacts/architecture.md#ADR-01]
- ADR-03 (Priority Matrix in HD Settings): [Source: _bmad-output/planning-artifacts/architecture.md#ADR-03]
- NFR-M-01 (80% unit test coverage): [Source: _bmad-output/planning-artifacts/epics.md#Non-Functional Requirements]
- NFR-M-04 (ITIL features toggleable via HD Settings): [Source: _bmad-output/planning-artifacts/epics.md#Non-Functional Requirements]
- AR-04 (Modify DocType JSON, not Custom Fields): [Source: _bmad-output/planning-artifacts/epics.md#Additional Requirements]
- AR-05 (Migration patches in `helpdesk/patches/v1_phase1/`): [Source: _bmad-output/planning-artifacts/epics.md#Additional Requirements]
- UX-DR-01 (Progressive disclosure for ITIL fields): [Source: _bmad-output/planning-artifacts/epics.md#UX Design Requirements]
- HD Ticket DocType files: `helpdesk/helpdesk/doctype/hd_ticket/`
- HD Settings DocType files: `helpdesk/helpdesk/doctype/hd_settings/`
- Story 1.1 (prerequisite — feature flags + field stubs): [Source: _bmad-output/implementation-artifacts/story-1.1-feature-flag-infrastructure-for-itil-mode.md]

## Dev Agent Record

### Agent Model Used

Claude Sonnet 4.5 (create-story workflow)

### Debug Log References

_None — story creation phase_

### Completion Notes List

_To be filled by implementing dev agent_

### File List

_To be filled by implementing dev agent upon completion_
