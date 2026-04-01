# Story: Feat: Support Level management UI — CRUD page for HD Support Level + auto-escalation config

Status: done
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

- [x] ### 1. Support Levels Settings Page
- [x] Add "Support Levels" link in Settings sidebar (under Teams or as new section)
- [x] List view showing all HD Support Level records:
- [x] Level Name (e.g. L0 - Sub-County Support)
- [x] Level Order (numeric, for hierarchy ordering)
- [x] Allow Escalation (checkbox)
- [x] Auto-Escalate Minutes (if set)
- [x] Sortable by level_order

## Tasks / Subtasks

- [x] Implement changes
- [x] Verify build passes

## Dev Notes

Implementation follows the Settings modal panel pattern (same as Teams/SLA tabs). No separate route needed — accessed via Settings modal. All CRUD operations use frappe-ui `createListResource` and `createDocumentResource`.

### References

- Task source: Claude Code Studio task #358

## Dev Agent Record

### Agent Model Used

sonnet

### Completion Notes List

- Implemented Support Levels as a Settings modal panel (consistent with Teams, SLA, etc.)
- Uses `SupportLevelListResourceSymbol` injection pattern for shared list resource
- Visual hierarchy uses sorted `level_order` with arrow icons indicating escalation path
- "Terminal" badge shown for levels with `allow_escalation_to_next = 0`
- Form supports create (via `listResource.insert`) and edit (via `createDocumentResource`)
- Delete with confirmation dialog in both list (dropdown) and form (Delete button)
- Auto-Escalate Minutes shown conditionally based on `auto_escalate_on_breach` checkbox
- Build passes ✅ (29.35s, no new errors)

### Change Log

- 2026-04-01: Created SupportLevels settings panel following Teams/SLA modal pattern
- 2026-04-01: Added Support Levels tab to settingsModal.ts with LucideLayers icon

### File List

**Created:**
- `desk/src/components/Settings/SupportLevels/SupportLevels.vue` — Container managing step state + list resource
- `desk/src/components/Settings/SupportLevels/SupportLevelsList.vue` — List with visual hierarchy, sort by level_order
- `desk/src/components/Settings/SupportLevels/SupportLevelForm.vue` — Create/Edit form with all fields
- `desk/src/components/Settings/SupportLevels/types.ts` — Shared Symbol + SupportLevel interface

**Modified:**
- `desk/src/components/Settings/settingsModal.ts` — Added "Support Levels" tab (App Settings section)
