# Story: Feat: Support Level management UI — CRUD page for HD Support Level + auto-escalation config

Status: in-progress
Task ID: mnge2v9ft68rn1
Task Number: #358
Workflow: quick-dev
Model: sonnet
Created: 2026-04-01T18:38:31.109Z

## Description

## Problem
HD Support Level DocType was created (County-1) with fields like level_order, allow_escalation_to_next, auto_escalate_minutes, etc. But there is no UI in the ServiceDesk app to manage these. Admins must go to Frappe Desk to configure support levels.

## Requirements

### 1. Support Levels Settings Page
- Add "Support Levels" link in Settings sidebar (under Teams or as new section)
- List view showing all HD Support Level records:
  - Level Name (e.g. L0 - Sub-County Support)
  - Level Order (numeric, for hierarchy ordering)
  - Allow Escalation (checkbox)
  - Auto-Escalate Minutes (if set)
- Sortable by level_order

### 2. Create/Edit Support Level
- Form with fields:
  - **Level Name** (text) — e.g. "Sub-County Support", "County Support"
  - **Level Order** (number) — determines hierarchy (0=lowest, 3=highest)
  - **Allow Escalation to Next** (checkbox) — can tickets at this level be escalated?
  - **Auto-Escalate Minutes** (number, optional) — if no response within N minutes, auto-escalate
  - **Description** (text) — optional description of this support tier

### 3. Visual Hierarchy
- Show levels as an ordered list (by level_order) with visual indication of escalation path:
  L0 → L1 → L2 → L3 (terminal)
- Show which levels can escalate and which are terminal

## Files
- New: `desk/src/pages/settings/SupportLevels.vue` or similar
- `desk/src/router/index.ts` — add route
- Settings sidebar — add link

## Done Criteria
- Support Levels page accessible from Settings
- List all HD Support Level records
- Create new support level with all fields
- Edit existing levels
- Delete levels (with confirmation)
- Visual hierarchy display
- yarn build passes

## Acceptance Criteria

- [ ] ### 1. Support Levels Settings Page
- [ ] Add "Support Levels" link in Settings sidebar (under Teams or as new section)
- [ ] List view showing all HD Support Level records:
- [ ] Level Name (e.g. L0 - Sub-County Support)
- [ ] Level Order (numeric, for hierarchy ordering)
- [ ] Allow Escalation (checkbox)
- [ ] Auto-Escalate Minutes (if set)
- [ ] Sortable by level_order

## Tasks / Subtasks

- [ ] Implement changes
- [ ] Verify build passes

## Dev Notes



### References

- Task source: Claude Code Studio task #358

## Dev Agent Record

### Agent Model Used

sonnet

### Completion Notes List

_(Updated by agent on completion)_

### Change Log

_(Updated by agent during implementation)_

### File List

_(Updated by agent — list all files created or modified)_
