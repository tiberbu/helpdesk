# QA Report: Task #325 — Rebrand: Helpdesk → ServiceDesk

**QA Task**: #326
**Date**: 2026-04-01
**Tester**: QA Agent (Opus)
**QA Depth**: 1/1

---

## Summary

The rebrand was **partially successful**. The Vue SPA frontend (sidebar, page titles, user menu) correctly shows "ServiceDesk" throughout. However, `hooks.py` was not synced to the bench deployment, causing the Frappe desk app switcher to still show "Helpdesk". Additionally, the Frappe workspace JSON file was not rebranded at all, resulting in the Frappe desk workspace page showing "Helpdesk" in multiple locations.

---

## Test Environment

- **URL**: http://help.frappe.local/helpdesk
- **Login**: Administrator / admin
- **Browser**: Playwright (Chromium)

---

## Acceptance Criteria Results

### AC1: Sidebar header shows "ServiceDesk"
**PASS** ✅
- Sidebar header displays "ServiceDesk" with the new indigo headset icon
- Evidence: [task-326-02-sidebar-branding.png](../test-screenshots/task-326-02-sidebar-branding.png)

### AC2: Page title shows "ServiceDesk"
**PASS** ✅
- Browser tab title shows "ServiceDesk" on the home page
- Evidence: Page title confirmed as "ServiceDesk" in Playwright snapshot

### AC3: New professional icon applied
**PASS** ✅
- New indigo/purple headset icon visible in sidebar
- favicon.svg properly synced to bench
- Evidence: [task-326-01-servicedesk-landing.png](../test-screenshots/task-326-01-servicedesk-landing.png)

### AC4: Frappe desk app switcher shows "ServiceDesk"
**FAIL** ❌ — **P0**
- App switcher shows **"Helpdesk"** instead of "ServiceDesk"
- Root cause: `hooks.py` was updated in dev copy but NOT synced to bench copy
- Dev copy: `app_title = "ServiceDesk"`, `"title": "ServiceDesk"`
- Bench copy: `app_title = "Helpdesk"`, `"title": "Helpdesk"`
- Evidence: [task-326-06-frappe-desk.png](../test-screenshots/task-326-06-frappe-desk.png)

### AC5: Frappe workspace page shows "ServiceDesk"
**FAIL** ❌ — **P1**
- Workspace page at `/app/helpdesk` shows "Helpdesk" in 6+ locations:
  - Page title: "Helpdesk"
  - Breadcrumb: "/ Helpdesk"
  - Link: "Visit Helpdesk"
  - Section header: "Helpdesk Configuration"
  - Card label: "Helpdesk Reports"
  - Sidebar module label: "Helpdesk"
- Root cause: `helpdesk/helpdesk/workspace/helpdesk/helpdesk.json` was never modified in either dev or bench copy
- Evidence: [task-326-07-frappe-workspace-helpdesk.png](../test-screenshots/task-326-07-frappe-workspace-helpdesk.png)

### AC6: All user-facing Vue components show "ServiceDesk"
**PASS** ✅
- Grep for `"Helpdesk"`, `'Helpdesk'`, `` `Helpdesk` `` in `desk/src/` returns zero matches
- UserMenu, Sidebar, InviteAgents, TicketCustomer, MobileTicketAgent all verified clean

### AC7: Welcome ticket template rebranded
**PASS** ✅
- `welcome_ticket.py` correctly says "Welcome to ServiceDesk" and "ServiceDesk" in body text
- Note: Existing ticket #1 in DB still shows "Welcome to Helpdesk" (pre-existing data, not a code issue)

### AC8: `cd desk && yarn build` passes
**PASS** ✅ (per dev agent completion notes — 29s build, no errors)

### AC9: No console errors related to rebrand
**PASS** ✅
- All console errors are socket.io connection refused (pre-existing infrastructure issue)
- No JavaScript errors related to missing assets or broken references

---

## Console Errors

All 13 console errors are identical: `Failed to load resource: net::ERR_CONNECTION_REFUSED @ https://help.frappe.local/socket.io/...`

These are pre-existing socket.io connectivity issues, unrelated to the rebrand.

---

## Issues Found

### Issue 1 — P0: hooks.py not synced to bench
- **Severity**: P0 (Critical — user-visible in Frappe desk app switcher)
- **File**: `/home/ubuntu/frappe-bench/apps/helpdesk/hooks.py`
- **Lines**: 2, 16
- **Current**: `app_title = "Helpdesk"` and `"title": "Helpdesk"`
- **Expected**: `app_title = "ServiceDesk"` and `"title": "ServiceDesk"`
- **Steps to reproduce**: Navigate to http://help.frappe.local/desk — app shows as "Helpdesk"
- **Screenshot**: task-326-06-frappe-desk.png

### Issue 2 — P1: Workspace JSON not rebranded
- **Severity**: P1 (High — entire Frappe workspace page shows old branding)
- **File**: `helpdesk/helpdesk/workspace/helpdesk/helpdesk.json` (both dev + bench copies)
- **Lines**: 3 (content JSON), 11, 128, 165
- **Current**: "Helpdesk" in label, title, content strings, card names
- **Expected**: "ServiceDesk" in all display strings
- **Steps to reproduce**: Navigate to http://help.frappe.local/app/helpdesk
- **Screenshot**: task-326-07-frappe-workspace-helpdesk.png

### Issue 3 — P3: README.md not synced to bench
- **Severity**: P3 (Cosmetic — not user-visible in app)
- **File**: `/home/ubuntu/frappe-bench/apps/helpdesk/README.md`
- **Description**: Bench copy still says "Frappe Helpdesk" in lines 3-4, 27-28
- **No fix task needed**

### Issue 4 — P3: widget/package.json not synced to bench
- **Severity**: P3 (Cosmetic — not user-visible)
- **File**: `/home/ubuntu/frappe-bench/apps/helpdesk/widget/package.json`
- **Description**: Bench copy still says "Embeddable chat widget for Frappe Helpdesk"
- **No fix task needed**

### Issue 5 — P3: README.md has remaining "Helpdesk" in setup instructions
- **Severity**: P3 (Documentation only)
- **File**: `/home/ubuntu/bmad-project/helpdesk/README.md`
- **Lines**: 131, 169, 183, 188
- **Description**: Setup/install instructions still reference "Helpdesk" as product name
- **No fix task needed**

---

## Screenshots

| # | File | Description |
|---|------|-------------|
| 01 | task-326-01-servicedesk-landing.png | Home page with ServiceDesk branding |
| 02 | task-326-02-sidebar-branding.png | Sidebar close-up showing ServiceDesk + icon |
| 03 | task-326-03-tickets-page.png | Tickets list page |
| 04 | task-326-04-ticket-detail-welcome.png | Ticket #1 detail (old welcome ticket data) |
| 05 | task-326-05-knowledge-base.png | Knowledge Base page |
| 06 | task-326-06-frappe-desk.png | **FAIL**: Frappe desk shows "Helpdesk" in app switcher |
| 07 | task-326-07-frappe-workspace-helpdesk.png | **FAIL**: Workspace page shows "Helpdesk" everywhere |
| 08 | task-326-08-customer-portal.png | Customer portal with correct branding |
| 09 | task-326-09-settings-page.png | Settings page (pre-existing access issue) |

---

## Verdict

**FAIL** — 1 P0 and 1 P1 issue found. Fix task created for P0/P1 issues.
