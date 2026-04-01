# Story: Rebrand: Helpdesk → ServiceDesk — name, icon, and all references across entire project

Status: in-progress
Task ID: mng728k2b6mhbz
Task Number: #325
Workflow: quick-dev
Model: sonnet
Created: 2026-04-01T15:22:04.372Z

## Description

## Goal
Rebrand the product from "Helpdesk" to "ServiceDesk" throughout the entire codebase.

## Scope

### 1. App Icon
- Replace the current purple ticket/inbox icon with a classy, professional ServiceDesk icon
- Suggested: a shield with a headset, or a sleek concierge bell, or a modern support hub icon — something that conveys enterprise service management, not just a ticket box
- The icon must work at all sizes (favicon, sidebar, app switcher, mobile)
- Update SVG/PNG assets in: `helpdesk/public/`, `desk/public/`, any `assets/` directories
- Update favicon files

### 2. Display Name Changes
- Sidebar header: "Helpdesk" → "ServiceDesk"
- App title / page titles: all references to "Helpdesk" or "Help Desk"
- Navigation labels, breadcrumbs, tooltips
- Login page / portal header
- Email templates and notification text
- About/settings pages
- Command palette entries
- All user-facing strings in Vue components (use grep for __() translations too)

### 3. Code-Level References (display only)
- Update display strings in Vue files, Python files, JSON fixtures
- Update `app_title`, `app_description` in hooks.py if present
- Update desk_settings, portal_settings display names
- Do NOT rename DocTypes, module folders, or Python package names (that would break migrations)
- Do NOT rename the git repo or frappe app name

### 4. Files to Check
- `desk/src/components/layouts/Sidebar.vue` — app name display
- `desk/src/components/layouts/DesktopLayout.vue`
- `desk/src/pages/` — all page titles
- `helpdesk/hooks.py` — app_title, app_publisher
- `helpdesk/config/` — desktop.py, docs.py
- `helpdesk/public/` — icons, favicon
- `desk/public/` — index.html title
- `desk/index.html` — page title
- All `__()` translation calls referencing helpdesk/Helpdesk
- README.md

## Done Criteria
- All user-visible text says "ServiceDesk" instead of "Helpdesk"
- New professional icon applied to sidebar, favicon, app switcher
- `cd desk && yarn build` passes
- `bench build --app helpdesk` passes
- 

## Acceptance Criteria

- [ ] Implementation matches task description
- [ ] No regressions introduced
- [ ] Code compiles/builds without errors

## Tasks / Subtasks

- [ ] Implement changes
- [ ] Verify build passes

## Dev Notes



### References

- Task source: Claude Code Studio task #325

## Dev Agent Record

### Agent Model Used

sonnet

### Completion Notes List

_(Updated by agent on completion)_

### Change Log

_(Updated by agent during implementation)_

### File List

_(Updated by agent — list all files created or modified)_
