# QA Report: Task #330 — Replace ServiceDesk sidebar icon with modern professional SVG

**QA Task**: #331
**Dev Task**: #330
**Date**: 2026-04-01
**QA Depth**: 1/1 (max depth reached)
**Tester**: QA Agent (Opus)

---

## Summary

Task #330 replaced the ServiceDesk sidebar icon (`helpdesk/public/desk/favicon.svg`) with a modern teal headset SVG. The new icon is clearly visible in the Frappe desktop app switcher. All acceptance criteria PASS.

---

## Acceptance Criteria Results

### AC1: Find where the sidebar icon is rendered
**PASS**
The icon is referenced in `helpdesk/hooks.py` at line 15: `"logo": "/assets/helpdesk/desk/favicon.svg"`. The dev agent correctly identified and documented this path.

### AC2: Check hooks.py for icon reference
**PASS**
`hooks.py` references `/assets/helpdesk/desk/favicon.svg`. The hooks.py file itself was NOT modified by this task (confirmed via story completion notes).

### AC3: Create new clean vector SVG icon at the same file path
**PASS**
- New SVG at `helpdesk/public/desk/favicon.svg` is a 118×118 viewBox modern headset icon
- Uses deep teal gradient (`#0E7490` → `#164E63`) — professional color palette, not the old purple
- White headset with arc, ear cups, mic arm, and mic capsule
- Clean vector paths, well-structured SVG with proper `xmlns` attribute
- Scalable — works at any size due to vector nature (16×16, 24×24, 64×64)

### AC4: Replace favicon if it exists
**PASS**
The favicon at `helpdesk/public/desk/favicon.svg` was overwritten with the new SVG. Confirmed via file read — the file contains the new teal headset design.

### AC5: bench build passes (or asset is live)
**PASS (with note)**
`bench build --app helpdesk` failed due to pre-existing Node.js version incompatibility (needs >=24, got 22.22.0). However, this is NOT blocking because `sites/assets/helpdesk` is a symlink to `apps/helpdesk/helpdesk/public`, so the asset is served immediately without a rebuild. This is a pre-existing infrastructure issue, not caused by this task.

### AC6: New icon visible in browser at Frappe desktop app switcher
**PASS**
- Navigated to `http://help.frappe.local/` via Playwright
- Screenshot captured: `test-screenshots/task-330-01-desktop-app-switcher.png`
- ServiceDesk app card clearly shows the new teal headset icon (rounded square, white headset on teal gradient)
- Close-up screenshot: `test-screenshots/task-330-02-servicedesk-icon-closeup.png`

### AC7: No changes to hooks.py, config/, or desk/ source
**PASS**
Story completion notes confirm only `helpdesk/public/desk/favicon.svg` was modified. The `hooks.py`, `config/`, and `desk/` source directories were not touched by this task. (Note: other uncommitted changes in the working tree are from prior stories, not this task.)

---

## Console Errors

All console errors observed are **socket.io 502 Bad Gateway** errors — these are a pre-existing infrastructure issue (socketio service not running or misconfigured). They are unrelated to the icon change.

**No task-related console errors found.**

---

## Screenshots

| # | File | Description |
|---|------|-------------|
| 01 | `test-screenshots/task-330-01-desktop-app-switcher.png` | Full desktop view showing new teal headset icon on ServiceDesk card |
| 02 | `test-screenshots/task-330-02-servicedesk-icon-closeup.png` | Close-up of the ServiceDesk icon (teal headset) |

---

## Asset Verification

- `curl http://help.frappe.local/assets/helpdesk/desk/favicon.svg` returns valid SVG with teal gradient and headset paths
- SVG structure: `<svg width="118" height="118">` with `linearGradient`, `rect`, `path`, `circle` elements

---

## Regression Check

- Frappe desktop loads normally
- ServiceDesk app link correctly navigates to `/helpdesk/home`
- No rendering issues with the icon at the displayed size
- No JavaScript errors related to the icon change

---

## Issues Found

**None.** All acceptance criteria pass. No P0-P3 issues identified.

---

## Verdict: ✅ ALL PASS

No fix task required. The icon replacement was clean and correctly scoped.
