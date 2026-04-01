# Story: Feat: Team creation/edit UI — add Support Level, Parent Team, Territory fields

Status: in-progress
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

- [ ] ### 1. New Team Form (`desk/src/components/Settings/Teams/NewTeam.vue`)
- [ ] Add these fields after Team Name, before Members:
- [ ] **Support Level** (Link to HD Support Level) — dropdown showing available support levels (L0/Sub-County, L1/County, L2/National, L3/Engineering)
- [ ] **Parent Team** (Link to HD Team) — dropdown to select parent team in hierarchy. Should filter to show only teams with a higher-level support level.
- [ ] **Territory** (Data/text) — free text field for county/sub-county/region name

## Tasks / Subtasks

- [ ] Implement changes
- [ ] Verify build passes

## Dev Notes



### References

- Task source: Claude Code Studio task #355

## Dev Agent Record

### Agent Model Used

sonnet

### Completion Notes List

_(Updated by agent on completion)_

### Change Log

_(Updated by agent during implementation)_

### File List

_(Updated by agent — list all files created or modified)_
