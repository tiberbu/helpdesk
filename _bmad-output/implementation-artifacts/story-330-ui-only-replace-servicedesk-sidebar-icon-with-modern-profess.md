# Story: UI-only: Replace ServiceDesk sidebar icon with modern professional SVG

Status: in-progress
Task ID: mng7unziqi3qln
Task Number: #330
Workflow: quick-dev
Model: sonnet
Created: 2026-04-01T15:44:10.736Z

## Description

## Scope — UI ONLY
Replace the app icon shown in the Frappe desk sidebar with a new modern SVG. This is a UI-only change.

## DO NOT TOUCH
- hooks.py — do not modify
- helpdesk/config/ — do not modify
- desk/ directory — do not modify
- Any core app naming or package references

## What To Do
1. Find where the sidebar icon is rendered for the helpdesk app. It is likely:
   - An SVG file in `helpdesk/public/images/` referenced by Frappe app switcher
   - Or set via `app_logo_url` in hooks.py (but do NOT change hooks.py — only replace the image file it points to)
2. Check: `grep -rn "icon\|logo\|svg" helpdesk/hooks.py` to find what image path is referenced
3. Create a new clean vector SVG icon at that same file path (overwrite the old one):
   - Design: modern enterprise service desk icon — a shield with headset, or concierge bell with checkmark, or hexagonal badge with support symbol
   - Colors: deep blue/teal professional palette (not the old purple)
   - Must work at 16x16, 24x24, 64x64
4. Also replace favicon if it exists in `helpdesk/public/` (same path, just overwrite)
5. Run: `bench build --app helpdesk` to rebuild assets
6. Verify in browser at http://help.frappe.local — new icon should appear in app sidebar/switcher

## Done Criteria
- New modern icon visible in Frappe sidebar app switcher
- Old icon file overwritten with new SVG
- No changes to hooks.py, config/, or desk/
- `bench build --app helpdesk` passes

## Acceptance Criteria

- [ ] Find where the sidebar icon is rendered for the helpdesk app. It is likely:
- [ ] Check: `grep -rn "icon\|logo\|svg" helpdesk/hooks.py` to find what image path is referenced
- [ ] Create a new clean vector SVG icon at that same file path (overwrite the old one):
- [ ] Also replace favicon if it exists in `helpdesk/public/` (same path, just overwrite)
- [ ] Run: `bench build --app helpdesk` to rebuild assets
- [ ] Verify in browser at http://help.frappe.local — new icon should appear in app sidebar/switcher

## Tasks / Subtasks

- [ ] Find where the sidebar icon is rendered for the helpdesk app. It is likely:
- [ ] Check: `grep -rn "icon\|logo\|svg" helpdesk/hooks.py` to find what image path is referenced
- [ ] Create a new clean vector SVG icon at that same file path (overwrite the old one):
- [ ] Also replace favicon if it exists in `helpdesk/public/` (same path, just overwrite)
- [ ] Run: `bench build --app helpdesk` to rebuild assets
- [ ] Verify in browser at http://help.frappe.local — new icon should appear in app sidebar/switcher

## Dev Notes



### References

- Task source: Claude Code Studio task #330

## Dev Agent Record

### Agent Model Used

sonnet

### Completion Notes List

_(Updated by agent on completion)_

### Change Log

_(Updated by agent during implementation)_

### File List

_(Updated by agent — list all files created or modified)_
