# QA Report: Task #334 — Critical UI Audit: Fix scroll, overflow, and broken interactions

**QA Task**: #336
**Date**: 2026-04-01
**Tester**: QA Agent (Opus)
**Environment**: http://help.frappe.local/helpdesk (Administrator)

## Summary

Task #334 addressed three UI issues: (1) AutomationBuilder scroll trap, (2) Ticket sidebar not scrollable, (3) Linked tickets search broken. **Issues 1 and 2 are fully fixed. Issue 3 (linked ticket search) remains broken — P0.**

## Test Results

### AC-1: AutomationBuilder — scrollable panels ✅ PASS

**What was tested:**
- Navigated to `http://help.frappe.local/helpdesk/automations/QA-Test-Rule-001`
- Verified WHEN/IF/THEN builder panels are all accessible via scrolling
- Verified "Add Condition" and "Add Action" buttons are visible and functional
- Tested creating a new automation rule at `/helpdesk/automations/new`

**Evidence:**
- Main content container: `clientHeight=439`, `scrollHeight=1601` — fully scrollable (was previously trapped)
- Successfully scrolled to bottom to see IF (Conditions) + THEN (Actions) sections
- Clicked "Add Action" — a second action row was added successfully
- New rule page also scrolls correctly: `scrollHeight=1681`

**Screenshots:**
- `task-336-02-automation-builder-top.png` — Top of automation builder showing WHEN triggers
- `task-336-04-automation-builder-scrolled-bottom.png` — Bottom showing IF + THEN sections with Add buttons
- `task-336-05-automation-add-action-works.png` — After clicking Add Action, 2nd row visible
- `task-336-12-new-automation-rule.png` — New rule page loads correctly
- `task-336-13-new-automation-scrolled.png` — New rule page scrolls to bottom

---

### AC-2: Ticket Detail — right sidebar scrollable ✅ PASS

**What was tested:**
- Navigated to `http://help.frappe.local/helpdesk/tickets/3`
- Verified the right sidebar (ticket properties, SLA info, linked articles, related tickets, time tracking) scrolls

**Evidence:**
- Sidebar content wrapper: `clientHeight=371`, `scrollHeight=726` — fully scrollable
- Scrolled to bottom: Linked Articles, Related Tickets, Time Tracking, "No time logged yet" all visible
- `TicketSidebar.vue` class changed to `flex-1 min-h-0 overflow-y-auto` — correct fix

**Screenshots:**
- `task-336-06-ticket-detail-view.png` — Ticket detail with sidebar at top
- `task-336-07-ticket-sidebar-scrolled.png` — Sidebar scrolled to bottom showing all sections

---

### AC-3: Linked Tickets — search functional ❌ FAIL (P0)

**What was tested:**
- Opened ticket #3, scrolled sidebar to "Related Tickets", clicked "+ Link"
- "Link a Ticket" dialog opened correctly
- Typed "Priority" in search — **"No results found"**
- Typed "10" in search — **"No results found"**
- Typed "1" in search — **"No results found"**

**Root Cause Analysis:**

The API is confirmed working — `frappe.client.get_list` with `or_filters` returns correct results (verified via network inspector and curl). The issue is in the **frappe-ui Autocomplete component interaction**:

1. **`TypeError: Cannot read properties of null (reading 'value')`** — The Autocomplete's default `compareFn` is `(a, b) => a.value === b.value`. When `selectedTicket` is `null` (initial state), headlessui's Combobox calls `compareFn(null, option)` → `null.value` → TypeError. This crash prevents ComboboxOption items from rendering.

2. **`:filter-results="false"` is a no-op** — The frappe-ui Autocomplete component does NOT define a `filterResults` prop. This prop is silently ignored. The Autocomplete ALWAYS runs its internal `filterOptions()` function (line 259 of Autocomplete.vue). However, this is secondary to the crash above.

**Console Error (captured):**
```
TypeError: Cannot read properties of null (reading 'value')
    at Proxy.default (index-cb2fd826.js:95:12965)
    at Object.compare (index-cb2fd826.js:51:8037)
    at Object.isSelected (index-cb2fd826.js:51:11019)
```

**Evidence:**
- Network shows API request `%Priority%` returned HTTP 200 with ticket #10
- Network shows API request `%1%` returned HTTP 200
- Autocomplete dropdown shows "No results found" despite API returning data
- TypeError crash in console on every search attempt

**Screenshots:**
- `task-336-08-link-ticket-dialog.png` — Dialog opens correctly
- `task-336-09-link-ticket-search-priority.png` — "Priority" search shows "No results found"
- `task-336-10-link-ticket-search-id-10.png` — "10" search shows "No results found"
- `task-336-11-link-ticket-search-1.png` — "1" search shows "No results found"

**Severity: P0** — Core feature completely non-functional. Users cannot link related tickets.

**File**: `desk/src/components/ticket/LinkTicketDialog.vue`
**Line**: 14-20 (Autocomplete usage)

**Fix Required:**
- Add `:compareFn="(a, b) => a?.value === b?.value"` to handle null selectedTicket
- Remove non-functional `:filter-results="false"` prop

---

## Console Errors Summary

| Error | Severity | Notes |
|-------|----------|-------|
| `TypeError: Cannot read properties of null (reading 'value')` | P0 | Crashes Autocomplete in LinkTicketDialog — prevents search results from rendering |
| `socket.io ERR_CONNECTION_REFUSED` (×30+) | P3 | Socket.io not running in test env — cosmetic, not a regression |

## Regression Check

- Home page: ✅ No regressions
- Ticket list: ✅ No regressions
- Ticket detail layout: ✅ No regressions (sidebar scrolls, activity panel works)
- Automation list: ✅ No regressions
- Automation builder (edit + new): ✅ No regressions

## Files Changed in Task #334

| File | Change | Status |
|------|--------|--------|
| `desk/src/pages/automations/AutomationBuilder.vue` | flex→space-y-6, TDZ fix | ✅ Verified working |
| `desk/src/components/ticket-agent/TicketDetailsTab.vue` | Removed overflow-hidden | ✅ Verified working |
| `desk/src/components/ticket-agent/TicketSidebar.vue` | Added min-h-0 overflow-y-auto | ✅ Verified working |
| `desk/src/components/ticket/LinkTicketDialog.vue` | Label includes subject, value=String | ❌ Search still broken (compareFn crash) |
