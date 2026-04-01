# Story: Fix: ServiceDesk sidebar logo and product name visibility on dark theme

Status: done
Task ID: mngbl690rc60tn
Task Number: #350
Workflow: quick-dev
Model: sonnet
Created: 2026-04-01T17:28:46.310Z

## Description

## Problem
The dark sidebar theme was applied (task #332) but the brand logo and "ServiceDesk" product name are poorly visible against the dark background. The headset icon is dark/teal on a dark charcoal sidebar — barely readable. The "ServiceDesk" text and "Help Admin" subtitle also lack contrast.

## What To Fix

### 1. Logo/Icon
- The headset icon in the top-left needs to be WHITE or very light colored on the dark sidebar
- If it is an SVG, change its fill/stroke to white (#FFFFFF) or light gray (#E4E7EB)
- If it references a colored image, create a light/inverted version for the dark sidebar context

### 2. Product Name "ServiceDesk"
- Text should be bright white (#FFFFFF) and bold/semibold
- Font size should be prominent (16-18px)
- Should stand out clearly against the dark background

### 3. Subtitle "Help Admin" (user/role)
- Should be light gray (#9CA3AF or #B0B7C3) — visible but secondary to the product name
- Slightly smaller font than the product name

### 4. Dropdown Chevron
- The dropdown arrow next to the name should be light gray (#9CA3AF)

### Files to Check
- desk/src/components/layouts/Sidebar.vue — logo area, product name, user info
- desk/src/assets/logos/ — HDLogo.vue or similar SVG component
- Any CSS that controls the sidebar header/branding area

### Reference
Look at how Zendesk, Linear, or Front display their logo on dark sidebars — white icon + white product name + muted subtitle.

## Build
- cd desk && yarn build
- Verify at http://help.frappe.local

## Done Criteria
- Logo/icon is clearly visible (white/light) on dark sidebar
- "ServiceDesk" text is bright white and prominent
- User name/role subtitle is visible but secondary
- Dropdown arrow visible
- Overall header area looks polished and professional
- yarn build passes

## Acceptance Criteria

- [x] Implementation matches task description
- [x] No regressions introduced
- [x] Code compiles/builds without errors

## Tasks / Subtasks

- [x] Implement changes
- [x] Verify build passes

## Dev Notes



### References

- Task source: Claude Code Studio task #350

## Dev Agent Record

### Agent Model Used

sonnet

### Completion Notes List

- Fixed dark sidebar text contrast in UserMenu.vue: product name now white+semibold, subtitle light gray (#9CA3AF), chevron light gray (#9CA3AF), hover/active state uses dark #2D3239 instead of light surface colors.
- HDLogo.vue already had white headset on teal gradient background — no change needed.
- Built from bench path (/home/ubuntu/frappe-bench/apps/helpdesk/desk) per project convention.
- Browser-verified: screenshot confirms "ServiceDesk" (white bold) and "Administrator" (gray) clearly visible on dark #1A1D21 sidebar.

### Change Log

- 2026-04-01: Fixed UserMenu.vue — replaced dark Tailwind text colors with dark-sidebar-appropriate colors. `text-gray-900 font-medium` → `text-white font-semibold` (product name); `text-gray-700` → `text-[#9CA3AF]` (subtitle); `text-gray-600` → `text-[#9CA3AF]` (chevron); `bg-surface-white shadow-sm` / `hover:bg-surface-gray-3` → `bg-[#2D3239]` / `hover:bg-[#2D3239]` (button states).

### File List

- `desk/src/components/UserMenu.vue` — modified (text color fixes for dark sidebar)
