# Story: Feat: Wire tier dashboards into navigation — sidebar links + role-based visibility

Status: in-progress
Task ID: mnge2fgkn107bn
Task Number: #357
Workflow: quick-dev
Model: sonnet
Created: 2026-04-01T18:38:10.631Z

## Description

## Problem
County-6 created L0/L1/L2/L3 dashboard view components and a CountyDashboardPage.vue, but they are not accessible from the sidebar navigation. Users have no way to reach these dashboards.

## Existing Components (already created)
- `desk/src/pages/home/components/L0DashboardView.vue`
- `desk/src/pages/home/components/L1DashboardView.vue`
- `desk/src/pages/home/components/L2DashboardView.vue`
- `desk/src/pages/home/components/L3DashboardView.vue`
- `desk/src/pages/home/components/CountyDashboard.vue`
- `desk/src/pages/dashboard/CountyDashboardPage.vue`
- Router already has county dashboard route (check `desk/src/router/index.ts`)

## Requirements

### 1. Sidebar Navigation
- Add "County Dashboard" link in the sidebar (under Dashboard or as a separate section)
- Icon: map or building-office or government building
- Only visible to agents with appropriate roles

### 2. Dashboard Page
- Show the appropriate dashboard view based on user role/team support level:
  - L0 agent → L0DashboardView (sub-county view)
  - L1 agent → L1DashboardView (county view with sub-county drill-down)
  - L2 agent → L2DashboardView (national view with county drill-down)
  - L3 agent → L3DashboardView (engineering view)
  - Admin → full view with level switcher
- Auto-detect user team support level from their HD Team membership

### 3. Dashboard Content Verification
- Verify each dashboard view actually renders data (not empty)
- L1 should show county-level ticket stats with sub-county breakdown
- L2 should show national stats with county-level breakdown
- Charts/stats should use real ticket data filtered by hierarchy

## Files
- `desk/src/router/index.ts` — verify route exists
- Sidebar component — add County Dashboard link
- `desk/src/pages/home/Home.vue` — may need integration

## Done Criteria
- County Dashboard accessible from sidebar
- Correct dashboard view shown per user role
- Data renders (ticket counts, charts)
- Admin can see all levels
- yarn build passes

## Acceptance Criteria

- [ ] ### 1. Sidebar Navigation
- [ ] Add "County Dashboard" link in the sidebar (under Dashboard or as a separate section)
- [ ] Icon: map or building-office or government building
- [ ] Only visible to agents with appropriate roles

## Tasks / Subtasks

- [ ] Implement changes
- [ ] Verify build passes

## Dev Notes



### References

- Task source: Claude Code Studio task #357

## Dev Agent Record

### Agent Model Used

sonnet

### Completion Notes List

_(Updated by agent on completion)_

### Change Log

_(Updated by agent during implementation)_

### File List

_(Updated by agent — list all files created or modified)_
