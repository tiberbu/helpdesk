# Story 1.1: Feature Flag Infrastructure for ITIL Mode

Status: ready-for-dev

## Story

As an administrator,
I want to toggle between Simple Mode and ITIL Mode in HD Settings,
so that my team can adopt ITIL fields gradually without being overwhelmed.

## Acceptance Criteria

1. **[Settings Persistence]** Given an administrator opens HD Settings, when they toggle the `itil_mode_enabled` checkbox, then the setting is saved to the database and is immediately available to all ticket forms, and the field defaults to OFF (0 / Simple Mode) for full backward compatibility with existing installations.

2. **[Simple Mode — Field Visibility]** Given ITIL Mode is disabled (Simple Mode / `itil_mode_enabled = 0`), when an agent opens a ticket form, then the `priority` field is shown as an editable dropdown (existing behavior), and the `impact`, `urgency`, `category`, and `sub_category` fields are hidden from the form.

3. **[ITIL Mode — Field Visibility]** Given ITIL Mode is enabled (`itil_mode_enabled = 1`), when an agent opens a ticket form, then the `impact`, `urgency`, `category`, and `sub_category` fields are visible, and the `priority` field is shown as read-only (to reflect auto-calculated value from the priority matrix).

4. **[Feature Flag Fields]** Given the HD Settings DocType, when a developer inspects the schema, then all four Phase 1 feature flag fields exist: `itil_mode_enabled` (Check), `chat_enabled` (Check), `csat_enabled` (Check), and `automation_enabled` (Check), all defaulting to 0.

5. **[Priority Matrix Default]** Given the HD Settings DocType, when a fresh installation is provisioned, then the `priority_matrix` JSON field exists with a complete default 3×3 ITIL matrix covering all 9 Impact×Urgency combinations (High-High through Low-Low) mapped to Frappe Helpdesk priority values (Urgent, High, Medium, Low).

6. **[Migration Patch]** Given a pre-existing helpdesk installation, when the Phase 1 migration patch runs, then all new fields are added to HD Settings without data loss, and `itil_mode_enabled` defaults to 0 for backward compatibility.

7. **[Unit Tests]** Given the feature flag implementation, when the test suite runs, then unit tests for feature flag read/write behavior pass with a minimum of 80% code coverage on the new controller methods.

8. **[Client Script Behavior]** Given the HD Ticket client script is loaded, when `itil_mode_enabled` is read from HD Settings, then the script correctly shows/hides the correct fields per AC-2 and AC-3 without page reload (dynamic toggle).

## Tasks / Subtasks

- [ ] Task 1 — Add `itil_mode_enabled` and feature flag fields to HD Settings DocType JSON (AC: #1, #4)
  - [ ] 1.1 Open `helpdesk/helpdesk/doctype/hd_settings/hd_settings.json`
  - [ ] 1.2 Add a new Tab Break `itil_tab` labeled "ITIL & Features" to `field_order`
  - [ ] 1.3 Add `Section Break` `itil_mode_section` with label "ITIL Mode"
  - [ ] 1.4 Add `Check` field `itil_mode_enabled` (label: "Enable ITIL Mode", default: 0, description: "When enabled, impact, urgency, category, and sub-category fields appear on tickets and priority becomes auto-calculated.")
  - [ ] 1.5 Add `Column Break` and `Section Break` `feature_flags_section` with label "Feature Flags"
  - [ ] 1.6 Add `Check` field `chat_enabled` (label: "Enable Live Chat", default: 0)
  - [ ] 1.7 Add `Check` field `csat_enabled` (label: "Enable CSAT Surveys", default: 0)
  - [ ] 1.8 Add `Check` field `automation_enabled` (label: "Enable Workflow Automation", default: 0)
  - [ ] 1.9 Add `JSON` field `priority_matrix` (label: "ITIL Priority Matrix", description: "JSON mapping Impact-Urgency pairs to priority values. All 9 combinations must be mapped.", depends_on: "eval:doc.itil_mode_enabled==1") with default value per ADR-03

- [ ] Task 2 — Implement client script to show/hide ITIL fields on HD Ticket form (AC: #2, #3, #8)
  - [ ] 2.1 Create or update `helpdesk/helpdesk/doctype/hd_ticket/hd_ticket.js` client script
  - [ ] 2.2 On form `onload` and `refresh`, call `frappe.db.get_single_value("HD Settings", "itil_mode_enabled")`
  - [ ] 2.3 If `itil_mode_enabled == 0`: hide fields `impact`, `urgency`, `category`, `sub_category`; set `priority` as editable
  - [ ] 2.4 If `itil_mode_enabled == 1`: show fields `impact`, `urgency`, `category`, `sub_category`; set `priority` as read-only
  - [ ] 2.5 Ensure the client script does not break existing form behavior when ITIL Mode is OFF

- [ ] Task 3 — Add new ITIL fields to HD Ticket DocType JSON (prerequisite for client script visibility) (AC: #2, #3)
  - [ ] 3.1 Open `helpdesk/helpdesk/doctype/hd_ticket/hd_ticket.json`
  - [ ] 3.2 Add `Select` field `impact` (label: "Impact", options: "High\nMedium\nLow", hidden: 1, depends_on: evaluated by client script)
  - [ ] 3.3 Add `Select` field `urgency` (label: "Urgency", options: "High\nMedium\nLow", hidden: 1)
  - [ ] 3.4 Confirm `category` and `sub_category` fields are present (or add stubs as `Link` fields to `HD Ticket Category` — Story 1.3 will fully implement them); mark as hidden by default

- [ ] Task 4 — Create migration patch for Phase 1 schema changes (AC: #6)
  - [ ] 4.1 Create directory `helpdesk/patches/v1_phase1/` if it does not exist
  - [ ] 4.2 Create `helpdesk/patches/v1_phase1/__init__.py` (empty)
  - [ ] 4.3 Create `helpdesk/patches/v1_phase1/add_feature_flags_to_hd_settings.py` with a `execute()` function that ensures the new fields exist and sets safe defaults
  - [ ] 4.4 Register the patch in `helpdesk/patches.txt` (or `patches.json` per project convention)

- [ ] Task 5 — Write unit tests for feature flag behavior (AC: #7)
  - [ ] 5.1 Open (or create) `helpdesk/helpdesk/doctype/hd_settings/test_hd_settings.py`
  - [ ] 5.2 Write test: `test_itil_mode_defaults_to_off` — assert `frappe.db.get_single_value("HD Settings", "itil_mode_enabled") == 0`
  - [ ] 5.3 Write test: `test_feature_flags_exist` — assert all four flag fields are readable and return 0 by default
  - [ ] 5.4 Write test: `test_priority_matrix_default` — assert `priority_matrix` JSON field exists and contains all 9 Impact×Urgency keys
  - [ ] 5.5 Write test: `test_itil_mode_can_be_toggled` — set `itil_mode_enabled = 1`, reload, assert value is 1; restore to 0

## Dev Notes

### Architecture Patterns

- **HD Settings is a Single DocType** (no naming series). Use `frappe.db.get_single_value("HD Settings", fieldname)` on the frontend and `frappe.get_single("HD Settings")` on the backend. Never use `frappe.get_doc("HD Settings", "HD Settings")`.
- **Feature flags in HD Settings** are the mandated pattern per AR-06 and NFR-M-04. Do NOT gate features using Custom Fields or site_config.json. All ITIL features MUST be toggleable without code deployment.
- **ADR-03 (Priority Matrix):** The `priority_matrix` JSON field in HD Settings stores the complete 3×3 matrix. The default per the architecture document is:
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
- **ADR-01 (Extend HD Ticket):** New ITIL fields (`impact`, `urgency`, `category`, `sub_category`) are added directly to HD Ticket DocType JSON — NOT via Custom Fields in the UI. This is required because this is the app source (AR-04).
- **Client Script Pattern:** The existing `hd_settings.js` demonstrates the client script conventions used in this project. New client script logic for `hd_ticket.js` must use `frappe.db.get_single_value` for async settings fetch and `frm.set_df_property` for show/hide. See existing client scripts for reference.
- **All new fields default to `0` / `OFF`:** This ensures that upgrading an existing installation does not change any behavior — Simple Mode is the backward-compatible default.

### Files to Create / Modify

| Action | Path | Notes |
|--------|------|-------|
| Modify | `helpdesk/helpdesk/doctype/hd_settings/hd_settings.json` | Add itil_tab, feature flag fields, priority_matrix JSON field |
| Modify | `helpdesk/helpdesk/doctype/hd_settings/hd_settings.py` | Add validation for priority_matrix JSON if present |
| Modify | `helpdesk/helpdesk/doctype/hd_ticket/hd_ticket.json` | Add impact, urgency fields; ensure category, sub_category stubs present |
| Create/Modify | `helpdesk/helpdesk/doctype/hd_ticket/hd_ticket.js` | Client script for ITIL field show/hide |
| Create | `helpdesk/patches/v1_phase1/__init__.py` | Empty init |
| Create | `helpdesk/patches/v1_phase1/add_feature_flags_to_hd_settings.py` | Migration patch |
| Modify | `helpdesk/patches.txt` | Register the migration patch |
| Modify | `helpdesk/helpdesk/doctype/hd_settings/test_hd_settings.py` | Add feature flag unit tests |

### Testing Standards

- Minimum 80% unit test coverage on all new controller logic (NFR-M-01).
- Use Frappe's `frappe.tests.utils.FrappeTestCase` as base class for all test cases.
- Tests must be self-contained and restore any modified Single DocType values after each test using `addCleanup`.
- Run tests with: `bench --site <site> run-tests --module helpdesk.helpdesk.doctype.hd_settings.test_hd_settings`

### Constraints

- Do NOT break existing HD Settings fields — only additive changes allowed (AR-04).
- Do NOT use Custom Fields mechanism — modify DocType JSON directly (AR-04).
- Do NOT gate features in `site_config.json` — use HD Settings (AR-06, NFR-M-04).
- `itil_mode_enabled` must default to `0` for backward compatibility (AC-1).
- i18n: All user-facing labels and descriptions must use `frappe._()` in Python and `__()` in JS (Architecture Enforcement Guideline #7).

### Project Structure Notes

- **Alignment with unified project structure:** All files follow the standard DocType module pattern: `helpdesk/helpdesk/doctype/hd_{name}/hd_{name}.{json|py|js}` [Source: architecture.md#ADR Structure Patterns]
- **Migration patches location:** `helpdesk/patches/v1_phase1/` — per AR-05 all schema migration patches for Phase 1 go here [Source: architecture.md#Project Directory Structure]
- **No conflicts detected:** Story 1.1 is the foundational story; impact/urgency fields added here as stubs will be fully implemented in Story 1.2; category/sub_category stubs will be implemented in Story 1.3. This story must be completed before 1.2 and 1.3.

### References

- Feature flag fields specification: [Source: _bmad-output/planning-artifacts/epics.md#Story 1.1]
- AR-06 (Feature flags in HD Settings): [Source: _bmad-output/planning-artifacts/epics.md#Additional Requirements]
- NFR-M-04 (All ITIL features toggleable via HD Settings): [Source: _bmad-output/planning-artifacts/epics.md#Non-Functional Requirements]
- NFR-U-01 (Progressive disclosure): [Source: _bmad-output/planning-artifacts/epics.md#Non-Functional Requirements]
- ADR-01 (Extend HD Ticket): [Source: _bmad-output/planning-artifacts/architecture.md#ADR-01]
- ADR-03 (Priority Matrix in HD Settings): [Source: _bmad-output/planning-artifacts/architecture.md#ADR-03]
- HD Settings DocType files: `helpdesk/helpdesk/doctype/hd_settings/`
- HD Ticket DocType files: `helpdesk/helpdesk/doctype/hd_ticket/`
- Migration patches directory: `helpdesk/patches/v1_phase1/` [Source: _bmad-output/planning-artifacts/architecture.md#Project Directory Structure]
- Enforcement guideline — no raw SQL: [Source: _bmad-output/planning-artifacts/architecture.md#Enforcement Guidelines]

## Dev Agent Record

### Agent Model Used

Claude Sonnet 4.5 (create-story workflow)

### Debug Log References

_None — story creation phase_

### Completion Notes List

_To be filled by implementing dev agent_

### File List

_To be filled by implementing dev agent upon completion_
