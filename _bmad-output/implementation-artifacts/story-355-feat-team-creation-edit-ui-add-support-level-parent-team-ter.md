# Story: Feat: Team creation/edit UI — add Support Level, Parent Team, Territory fields

Status: done
Task ID: mngdz4p0rnh4g5
Task Number: #355
Workflow: quick-dev
Model: sonnet
Created: 2026-04-01T18:35:36.710Z

## Description

## Problem
The County Support epic added `support_level`, `parent_team`, and `territory` fields to the HD Team DocType backend, but the UI for creating/editing teams was never updated. The Teams settings page only shows Name + Members.

## Requirements

### 1. New Team Form (`desk/src/components/Settings/Teams/NewTeam.vue`)
Add these fields after Team Name, before Members:

- **Support Level** (Link to HD Support Level) — dropdown showing available support levels (L0/Sub-County, L1/County, L2/National, L3/Engineering)
- **Parent Team** (Link to HD Team) — dropdown to select parent team in hierarchy. Should filter to show only teams with a higher-level support level.
- **Territory** (Data/text) — free text field for county/sub-county/region name

### 2. Existing Team Edit View
- Same fields should appear when editing an existing team
- Check `desk/src/components/Settings/Teams/TeamSettingsLayout.vue` or similar edit component
- Pre-populate from existing team data

### 3. Team List View
- Show Support Level and Parent Team as visible columns in the teams list
- Consider showing hierarchy visually (indentation or tree icon) to indicate nesting:
  - L0 teams indented under their L1 parent
  - L1 teams indented under L2
  - Or group by support level with headers

### 4. Validation
- Parent Team should not allow circular references (A→B→A)
- A team cannot be its own parent
- Support Level is recommended but not required (backward compat)

### Backend Fields (already exist on HD Team DocType):
- `support_level` — Link to HD Support Level
- `parent_team` — Link to HD Team
- `territory` — Data field

## Build
- cd desk && yarn build

## Done Criteria
- New team form shows Support Level, Parent Team, Territory fields
- Edit team shows and saves these fields
- Team list shows hierarchy information (level + parent)
- Dropdowns populated from backend
- yarn build passes

## Acceptance Criteria

- [x] ### 1. New Team Form (`desk/src/components/Settings/Teams/NewTeam.vue`)
- [x] Add these fields after Team Name, before Members:
- [x] **Support Level** (Link to HD Support Level) — dropdown showing available support levels (L0/Sub-County, L1/County, L2/National, L3/Engineering)
- [x] **Parent Team** (Link to HD Team) — dropdown to select parent team in hierarchy. Should filter to show only teams with a higher-level support level.
- [x] **Territory** (Data/text) — free text field for county/sub-county/region name

## Tasks / Subtasks

- [x] Implement changes
- [x] Verify build passes

## Dev Notes

### Implementation Details

- Used shared `createListResource` resources (provided from `TeamsConfig.vue` via Vue `provide`/`inject`) to load `HD Support Level` and `HD Team` data — no duplicate API calls.
- `Autocomplete` component (`@/components/Autocomplete.vue`) used for link fields (Support Level, Parent Team); supports search-filter by default.
- Parent Team options are filtered by level_order > current team's level_order when a support level is set.
- Circular reference validation in `TeamEdit.vue`: traverses the `parent_team` chain in loaded team data to prevent A→B→A loops.
- `TeamEdit.vue` uses a "Team Details" form section with a "Save Details" button; state pre-populated from `team.doc` via `watch`.
- `TeamsConfig.vue` now also fetches `support_level` and `parent_team` fields for the list view.
- `TeamsList.vue` shows: Support Level badge column, ↳ arrow for child teams, "under X Team" sub-line for parent hierarchy.

### References

- Task source: Claude Code Studio task #355

## Dev Agent Record

### Agent Model Used

sonnet

### Completion Notes List

- Added Support Level, Parent Team, Territory fields to NewTeam.vue (new team creation form)
- Added "Team Details" section to TeamEdit.vue (edit existing team) with pre-population from team.doc, dirty tracking, and Save Details button
- Updated TeamsList.vue to show Support Level column and hierarchy (↳ arrow + "under X Team" sub-line)
- Updated TeamsConfig.vue to provide shared list resources (supportLevels, allTeamsForLinks) and fetch support_level/parent_team in the main teams list
- Build passes (yarn build from bench path: 29.65s, no errors)
- Browser verified: all three views (list, new, edit) show fields correctly with pre-populated data

### Change Log

- 2026-04-01: Added support_level, parent_team, territory fields to NewTeam.vue
- 2026-04-01: Added Team Details section with same fields to TeamEdit.vue
- 2026-04-01: Updated TeamsList.vue with Support Level column and hierarchy visual
- 2026-04-01: Updated TeamsConfig.vue to share support level / all-teams resources via provide/inject

### File List

**Modified:**
- `desk/src/components/Settings/Teams/NewTeam.vue`
- `desk/src/components/Settings/Teams/TeamEdit.vue`
- `desk/src/components/Settings/Teams/TeamsList.vue`
- `desk/src/components/Settings/Teams/TeamsConfig.vue`

**Also synced to bench path:**
- `frappe-bench/apps/helpdesk/desk/src/components/Settings/Teams/NewTeam.vue`
- `frappe-bench/apps/helpdesk/desk/src/components/Settings/Teams/TeamEdit.vue`
- `frappe-bench/apps/helpdesk/desk/src/components/Settings/Teams/TeamsList.vue`
- `frappe-bench/apps/helpdesk/desk/src/components/Settings/Teams/TeamsConfig.vue`
