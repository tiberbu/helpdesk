# QA Report: Task #357 — Feat: Wire tier dashboards into navigation — sidebar links + role-based visibility

**Date:** 2026-04-01
**QA Engineer:** Claude (automated)
**Story:** story-357-feat-wire-tier-dashboards-into-navigation-sidebar-links-role
**Depth:** 1/1

## Summary

Story #357 was narrowly scoped: add a "County Dashboard" sidebar link in the agent portal so users can navigate to the pre-existing county dashboard page. The implementation correctly adds the sidebar entry with a map icon, pointing to the existing `CountyDashboard` route.

## Acceptance Criteria Results

### AC1: Add "County Dashboard" link in the sidebar
**PASS**

- County Dashboard link is visible in the agent sidebar, positioned between "Major Incidents" and "Automations"
- Clicking it navigates to `/helpdesk/dashboard/county`
- The `CountyDashboard` route was already registered in `desk/src/router/index.ts:122`
- Screenshot: `test-screenshots/task-357-01-sidebar-county-dashboard-link.png`

### AC2: Icon — map or building-office or government building
**PASS**

- Uses `LucideMap` icon (map pin icon), which matches the "map" option from the requirements
- Icon is clearly visible in the sidebar next to the label
- Screenshot: `test-screenshots/task-357-01-sidebar-county-dashboard-link.png`

### AC3: Only visible to agents with appropriate roles
**PASS**

- The link is added to `agentPortalSidebarOptions` (not `customerPortalSidebarOptions`)
- Customer portal sidebar only has Tickets and Knowledge Base — no County Dashboard
- Verified via code review of `desk/src/components/layouts/layoutSettings.ts:66-77`

## Additional Observations

### Dashboard Content Empty for Administrator (P3 — Informational, NOT in scope of #357)

When Administrator navigates to the County Dashboard page, the content area is blank. This is because:
- Administrator is not a member of any HD Team
- The `get_tier_dashboard` API returns `tier: null` when the user has no team membership
- `CountyDashboard.vue` has no fallback/admin view for `tier === null`

This is a **pre-existing issue** from the County-6 dashboard implementation (story #342), not introduced by story #357. The original requirements mentioned "Admin -> full view with level switcher" but that was not part of story #357's scope (which was only sidebar wiring).

**Screenshot:** `test-screenshots/task-357-02-county-dashboard-page.png`

## Console Errors

- **socket.io connection refused** (26 occurrences) — infrastructure issue, socketio server not running. Not related to this feature.
- **indexedDB backing store errors** (16 occurrences) — browser/environment issue. Not related to this feature.
- **No application-level JavaScript errors** related to the County Dashboard feature.

## Build Verification

- `yarn build` passes successfully (built in 33.68s, 106 precache entries)

## Files Changed

- `desk/src/components/layouts/layoutSettings.ts` — Added `LucideMap` import and County Dashboard entry to `agentPortalSidebarOptions`

## Screenshots

| Screenshot | Description |
|---|---|
| `test-screenshots/task-357-01-sidebar-county-dashboard-link.png` | Sidebar showing County Dashboard link with map icon |
| `test-screenshots/task-357-02-county-dashboard-page.png` | County Dashboard page (empty for Admin — pre-existing issue) |
| `test-screenshots/task-357-03-county-dashboard-fullpage.png` | Full page view of County Dashboard |

## Verdict

**ALL ACCEPTANCE CRITERIA PASS.** No P0 or P1 issues found. The empty dashboard content for Administrator is a P3 informational note — it's a pre-existing gap from the County-6 story, not a regression introduced by this sidebar wiring task.
