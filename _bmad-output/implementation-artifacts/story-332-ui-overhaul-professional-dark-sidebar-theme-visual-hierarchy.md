# Story: UI Overhaul: Professional dark sidebar theme + visual hierarchy upgrade

Status: in-progress
Task ID: mng83ep1e1ejlr
Task Number: #332
Workflow: quick-dev
Model: sonnet
Created: 2026-04-01T15:50:58.599Z

## Description

## Goal
Transform ServiceDesk from an all-white flat UI to a professional, enterprise-grade theme matching industry leaders (Zendesk, Intercom, Front, Linear).

## SCOPE — desk/src/ ONLY
All changes in `desk/src/` Vue components and CSS. Do NOT touch:
- hooks.py
- helpdesk/config/
- Any Python backend files
- helpdesk/public/ (except adding new CSS/assets)

## Design Spec

### 1. Dark Sidebar
- Background: solid `#1A1D21` (near-black charcoal)
- Logo area: same or slightly darker
- Menu item text: `#B0B7C3` (light gray), icons same
- Hover state: background `#2D3239`, text brightens to `#E4E7EB`
- Active item: left border 3px accent color (`#0891B2` teal), background `#252A31`, text white
- Section headers/dividers: `#3A3F47` border, `#6B7280` text
- Scrollbar: thin, subtle (matches sidebar bg)
- Width stays the same as current

### 2. Content Area Background
- Change from pure `#FFFFFF` to `#F8F9FA` (warm light gray)
- Cards and panels stay `#FFFFFF` with subtle box-shadow (`0 1px 3px rgba(0,0,0,0.06)`)
- This creates visual depth: dark sidebar → gray background → white cards = 3 layers

### 3. Accent Color System
- Primary accent: `#0891B2` (deep teal) — buttons, links, active states, badges
- Hover: `#0E7490` (darker teal)
- Light accent bg: `#ECFEFF` (for selected rows, hover highlights)
- Keep these as CSS variables for easy future theming

### 4. Ticket List Improvements
- Alternating row colors: `#FFFFFF` / `#F9FAFB` (subtle striping)
- Hover row: `#F0FDFA` (very light teal tint)
- Selected row: `#0891B2` 3px left border + `#ECFEFF` background
- Compact rows: 40px height for density

### 5. Status Badge Colors
- Open: `#3B82F6` (blue)
- In Progress: `#F59E0B` (amber)
- Replied: `#8B5CF6` (purple)
- Resolved: `#10B981` (green)
- Closed: `#6B7280` (gray)
- Overdue/Breached: `#EF4444` (red)

### 6. Header/Toolbar
- Top bar: `#FFFFFF` with bottom border `#E5E7EB`
- Search bar: `#F3F4F6` background with `#9CA3AF` placeholder
- Action buttons: solid teal accent for

## Acceptance Criteria

- [ ] Implementation matches task description
- [ ] No regressions introduced
- [ ] Code compiles/builds without errors

## Tasks / Subtasks

- [ ] Implement changes
- [ ] Verify build passes

## Dev Notes



### References

- Task source: Claude Code Studio task #332

## Dev Agent Record

### Agent Model Used

sonnet

### Completion Notes List

_(Updated by agent on completion)_

### Change Log

_(Updated by agent during implementation)_

### File List

_(Updated by agent — list all files created or modified)_
