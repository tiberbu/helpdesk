# QA Report: Story 1.7 — Per-Ticket Time Tracking (Re-run #56)

**Reviewer:** Adversarial QA (Opus)
**Date:** 2026-03-23
**Task ID:** mn38sfpzdoc88t
**Previous QA:** `docs/qa-report-task-23.md` (Task #23 / #55)
**Verdict:** FAIL — Backend APIs functional but frontend never wired up. Feature invisible to users.

---

## Executive Summary

Compared to the previous QA run (Task #23), the database table now exists and all four backend API endpoints (`start_timer`, `stop_timer`, `add_entry`, `get_summary`) are functional and return correct results. However, the core frontend component `TimeTracker.vue` was **never created**, `TimeEntryDialog.vue` remains dead code (imported by nothing), no sidebar integration was done, no unit tests exist, no migration patch was registered, and the frontend was never rebuilt. The feature is invisible to end-users. This is a partial fix at best — the backend works, but the feature remains non-functional from a user perspective.

---

## Acceptance Criteria Results

### AC-1: Timer — Start (Start Timer button, visible counter, localStorage, one-at-a-time)
**Status:** FAIL (P0)

| Criterion | Result |
|---|---|
| Agent sees "Start Timer" button | FAIL — `TimeTracker.vue` does not exist. No timer button anywhere in the UI. |
| Timer counts with monospace `HH:MM:SS` | FAIL — No timer rendering code exists. |
| Timer persists in `localStorage` under `hd_timer_{ticketId}` | FAIL — No localStorage code in any file. |
| Single-timer-at-a-time warning | FAIL — No frontend logic exists. |
| `start_timer` API works | PASS — Returns `{"started_at": "2026-03-23 19:21:06.477395"}` |

**API Evidence:**
```
POST /api/method/helpdesk.api.time_tracking.start_timer {ticket: 1}
Response: {"message": {"started_at": "2026-03-23 19:21:06.477395"}}
```

### AC-2: Timer — Stop and Create Entry
**Status:** FAIL (P0 — no UI exists)

| Criterion | Result |
|---|---|
| Stop button creates HD Time Entry | FAIL — No stop button exists (no TimeTracker.vue). |
| Description prompt modal after stop | FAIL — TimeEntryDialog.vue exists but is never rendered. |
| localStorage cleared on stop | FAIL — No localStorage code. |
| `stop_timer` API works | PASS — Creates entry with `started_at` populated. |

**API Evidence:**
```
POST /api/method/helpdesk.api.time_tracking.stop_timer
  {ticket: 1, started_at: "2026-03-23 19:00:00", duration_minutes: 21, description: "timer test", billable: 1}
Response: {"message": {"name": "det5faint7", "success": true}}
```

### AC-3: Manual Entry — Form
**Status:** FAIL (P0 — no UI integration)

| Criterion | Result |
|---|---|
| "Add Time Entry" button in sidebar | FAIL — No sidebar integration. |
| Modal with duration/description/billable | PARTIAL — `TimeEntryDialog.vue` implements the form correctly but is never imported. |
| `add_entry` API works | PASS — Creates entry correctly. |

**API Evidence:**
```
POST /api/method/helpdesk.api.time_tracking.add_entry
  {ticket: 1, duration_minutes: 30, description: "test", billable: 0}
Response: {"message": {"name": "d8e6ksa0pd", "success": true}}
```

### AC-4: Manual Entry — Validation
**Status:** PARTIAL PASS (P1 — backend validates, frontend never renders)

| Criterion | Result |
|---|---|
| Form-level error for 0 duration | PASS (in dead code) — `TimeEntryDialog.vue` has `showDurationError` computed. |
| API rejects 0 duration | PASS — Returns `ValidationError: Duration must be at least 1 minute.` |
| API rejects negative duration | PASS — Returns `ValidationError`. |

### AC-5: HD Time Entry DocType — Schema
**Status:** MOSTLY PASS (P2 issues)

| Criterion | Result |
|---|---|
| Fields match spec (ticket, agent, duration_minutes, billable, description, timestamp, started_at) | PASS |
| Permissions for HD Agent, HD Admin, System Manager | PASS |
| Module is "Helpdesk" | PASS |
| `autoname` configured | FAIL — No `autoname` or `naming_rule`. Falls back to random hash naming. |
| Sort by timestamp DESC | PASS |
| Accessible via REST API (`/api/resource/HD Time Entry`) | PASS |

**REST API Evidence:**
```
GET /api/resource/HD%20Time%20Entry?limit_page_length=5
Response: {"data": [{"name": "d8e6ksa0pd"}, {"name": "det5faint7"}]}
```

### AC-6: Time Summary — Sidebar Display
**Status:** FAIL (P0 — no UI exists)

| Criterion | Result |
|---|---|
| Sidebar shows total/billable time | FAIL — No `TimeTracker.vue`. |
| Entry list with agent name, date, duration, description, billable badge | FAIL — No rendering component. |
| `get_summary` API works | PASS — Returns correct totals and entries. |

**API Evidence:**
```
GET /api/method/helpdesk.api.time_tracking.get_summary?ticket=1
Response: {"message": {"total_minutes": 30, "billable_minutes": 0, "entries": [...]}}
```

### AC-7: Time Summary — Entry Delete
**Status:** FAIL (P0 — no UI; backend delete works via standard Frappe API)

| Criterion | Result |
|---|---|
| Delete icon on own entries | FAIL — No sidebar UI. |
| Confirmation dialog | FAIL — No UI. |
| `frappe.client.delete` works | PASS — Successfully deletes entries. |
| Ownership enforcement (agents only delete own) | NOT TESTED — No custom delete logic; relies on standard Frappe DocType permissions which grant all HD Agents full delete on ALL entries (not just their own). |

### AC-8: API — `get_summary`
**Status:** PASS

| Criterion | Result |
|---|---|
| Returns total_minutes, billable_minutes, entries | PASS |
| Entries sorted by timestamp DESC | PASS |
| Agent role check (read on HD Ticket) | PASS |
| `agent_name` resolved to first name + last initial | PASS |

### AC-9: API — `start_timer` / `stop_timer`
**Status:** PASS

| Criterion | Result |
|---|---|
| `start_timer` checks write permission | PASS |
| `stop_timer` creates entry with `started_at` | PASS |
| Both use `@frappe.whitelist()` | PASS |

### AC-10: API — `add_entry`
**Status:** PASS

| Criterion | Result |
|---|---|
| Validates `duration_minutes >= 1` | PASS |
| Creates entry with correct agent/timestamp | PASS |
| Returns `{name, success}` | PASS |

### AC-11: Timer Persistence — localStorage
**Status:** FAIL (P0 — no implementation)

| Criterion | Result |
|---|---|
| `TimeTracker.vue` checks localStorage on mount | FAIL — Component does not exist. |
| Timer resumes from stored start time | FAIL |
| Cross-ticket warning banner | FAIL |

### AC-12: Unit Tests — Backend
**Status:** FAIL (P0 — no tests exist)

| Criterion | Result |
|---|---|
| `test_hd_time_entry.py` exists | FAIL — File was never created. |
| Tests for add_entry, stop_timer, get_summary | FAIL |
| Permission test for non-agent | FAIL |
| 80% line coverage (NFR-M-01) | FAIL — 0% coverage (no tests). |

---

## Adversarial Findings

### P0 — Critical / Feature Non-Functional

1. **`TimeTracker.vue` was never created.** This is the main sidebar component that provides the Start/Stop timer UI, time summary display, entry list, and delete functionality. It is specified in AC-1, AC-2, AC-6, AC-7, AC-11, and Task 3 of the story. Without it, the entire feature is invisible to users. The story's `Files to Create` table explicitly lists it. `Glob("**/TimeTracker.vue")` returns zero results in both the dev and bench codebases.

2. **`TimeEntryDialog.vue` is dead code — never imported by any component.** The dialog exists at `desk/src/components/ticket/TimeEntryDialog.vue` but `grep -r "TimeEntryDialog"` across `desk/src/pages/` and `desk/src/components/` (excluding itself) returns zero hits. Since `TimeTracker.vue` (which would import it) doesn't exist, it will never render.

3. **No sidebar integration.** The `TicketAgentSidebar.vue` does not import or render any time tracking component. Comparing with `RelatedTickets.vue` (Story 1.6), which is properly imported in `TicketDetailsTab.vue`, no equivalent wiring was done for time tracking. The time tracking feature is completely absent from the ticket detail page.

4. **No unit tests exist.** `test_hd_time_entry.py` was never created. `find -name "test_hd_time_entry.py"` returns zero results in both dev and bench codebases. AC-12 requires 7+ test cases covering add_entry, stop_timer, get_summary, validation, and permissions. NFR-M-01 requires 80% line coverage. Current coverage: 0%.

5. **No localStorage timer persistence.** The word `localStorage` does not appear in any new or modified file in the codebase. AC-1 and AC-11 require localStorage-based timer persistence under key `hd_timer_{ticketId}`. This is entirely unimplemented.

6. **Frontend was never rebuilt.** `grep -r "TimeEntryDialog\|TimeTracker\|Time Tracking" /path/to/bench/helpdesk/public/desk/` returns zero results. Even if the components were properly integrated, the compiled JavaScript in the bench public directory does not contain them. `yarn build` was never run after adding the new Vue files.

### P1 — Significant Issues

7. **No migration patch registered in `patches.txt`.** The story requires a patch `helpdesk.patches.v1_phase1.create_hd_time_entry` to be added to `patches.txt`. `grep "time_entry" patches.txt` returns nothing. The patch file itself (`create_hd_time_entry.py`) was also never created. The DB table exists (likely created via manual `bench migrate` during dev), but any fresh installation would fail to create it.

8. **`ignore_permissions=True` on all inserts bypasses DocType permission model.** Both `stop_timer` (line 53) and `add_entry` (line 88) in `time_tracking.py` call `entry.insert(ignore_permissions=True)`. While the code checks `has_permission("HD Ticket", "write")` beforehand, this means the HD Time Entry DocType's own role-based permissions (HD Agent, HD Admin, System Manager) are never enforced during creation. Any user with HD Ticket write access can create time entries even if they lack HD Time Entry permissions.

9. **Explicit `frappe.db.commit()` is a Frappe anti-pattern.** Lines 54 and 89 of `time_tracking.py` call `frappe.db.commit()` manually. Frappe auto-commits after successful whitelist method execution. Manual commits can cause partial-commit issues if subsequent request lifecycle code fails, and prevent proper transaction rollback on errors.

10. **`createResource` URL is non-reactive in `TimeEntryDialog.vue`.** Line 117-118: `createResource({ url: saveUrl.value })` captures the URL at component creation time as a snapshot. If `props.mode` were to change reactively, the resource URL would not update. The `saveUrl` computed property would change, but the resource would still hit the old endpoint. This is a latent bug.

### P2 — Missing Functionality / Design Gaps

11. **No `autoname` on HD Time Entry DocType.** The `hd_time_entry.json` has no `autoname` or `naming_rule` field. Frappe falls back to random hash naming (e.g., `d8e6ksa0pd`). The story spec says "follows HD prefix naming convention (AR-02)" but no naming convention is configured. Other project DocTypes use autoincrement or naming series.

12. **HD Agents can delete ANY agent's time entries.** The DocType permissions grant `delete: 1` to the HD Agent role without any owner-based restriction. AC-7 states "Agents may only delete their own entries; HD Admin / System Manager may delete any entry." The current permissions allow any agent to delete any agent's entries. No custom ownership check exists anywhere.

13. **No upper bound on `duration_minutes`.** The API accepts `duration_minutes=999999999` without complaint (tested and confirmed: entry was created successfully). A typo or malicious input could create absurdly large time entries (999,999,999 minutes = ~1,902 years) that corrupt reporting.

14. **`get_summary` does not verify ticket exists before querying.** Calling `get_summary(ticket="999999")` returns `{total_minutes: 0, billable_minutes: 0, entries: []}` instead of raising an error. The `has_permission("HD Ticket", "read", doc="999999")` call silently succeeds for non-existent tickets when the user is Administrator. This could mask bugs.

15. **Description field has no `maxlength` enforcement on backend.** AC-3 specifies "max 500 chars" for description. The `TimeEntryDialog.vue` (dead code) has no `:max-length` attribute actually enforced, and the backend `hd_time_entry.json` has no `length` property on the description field. The API controller (`time_tracking.py`) does not validate description length. Any length string can be submitted.

16. **`stop_timer` requires `started_at` as a required positional parameter but provides no default.** If the frontend fails to pass `started_at` (e.g., due to localStorage corruption), the API throws `TypeError` instead of a user-friendly `ValidationError`. Confirmed via curl test.

17. **No ITIL mode feature flag gating.** All prior stories (1.1-1.6) check `itil_mode_enabled` in HD Settings before exposing ITIL features. Time tracking has no such check in either backend or frontend. This breaks the architectural pattern established by Story 1.1 — the feature is always available regardless of ITIL mode setting.

18. **XSS potential in description field.** Frappe sanitizes script tags on save (tested: `<script>alert("xss")</script>` was stripped to empty string). However, the sanitization is silent — the user's description is silently erased rather than rejected. This could cause data loss for descriptions containing angle brackets (e.g., "Applied fix for <Component> rendering").

19. **`get_summary` makes N+1 database queries for agent names.** For each time entry, a separate `frappe.db.get_value("User", ...)` query is executed in a loop (lines 134-143). For a ticket with 50 time entries, this means 51 DB queries (1 for entries + 50 for names). Should use a single query with a join or batch lookup.

20. **Story file status still shows "ready-for-dev" with all checkboxes unchecked.** The story tracking document at `story-1.7-per-ticket-time-tracking.md` has `Status: ready-for-dev` and every task/subtask checkbox is `- [ ]`. No completion notes or file list was filled in. The dev agent never updated the tracking document.

---

## Browser Testing

**Playwright MCP:** Not available in this environment.

**Manual curl-based API testing performed:**
- All 4 API endpoints tested with valid/invalid inputs
- Validation rules confirmed working (zero duration, negative duration rejected)
- REST API access confirmed (`/api/resource/HD Time Entry`)
- Delete via `frappe.client.delete` confirmed working
- XSS and large-value edge cases tested

**Frontend status:** Cannot be browser-tested because:
1. `TimeTracker.vue` does not exist
2. `TimeEntryDialog.vue` is not imported by any component
3. Frontend was never rebuilt (`yarn build` not run)
4. No time tracking UI is visible on any page

---

## Files Reviewed

| File | Status | Notes |
|---|---|---|
| `helpdesk/helpdesk/doctype/hd_time_entry/hd_time_entry.json` | EXISTS | Schema correct, missing autoname |
| `helpdesk/helpdesk/doctype/hd_time_entry/hd_time_entry.py` | EXISTS | Basic validation only |
| `helpdesk/helpdesk/doctype/hd_time_entry/__init__.py` | EXISTS | Empty |
| `helpdesk/api/time_tracking.py` | EXISTS | 4 endpoints, all functional |
| `desk/src/components/ticket/TimeEntryDialog.vue` | EXISTS | Dead code (orphaned) |
| `desk/src/components/ticket/TimeTracker.vue` | **MISSING** | Never created |
| `helpdesk/helpdesk/doctype/hd_time_entry/test_hd_time_entry.py` | **MISSING** | Never created |
| `helpdesk/patches/v1_phase1/create_hd_time_entry.py` | **MISSING** | Never created |
| `helpdesk/patches.txt` | NOT UPDATED | No time entry patch registered |
| `desk/src/components/ticket/TicketAgentSidebar.vue` | NOT MODIFIED | No TimeTracker import |
| Bench `helpdesk/public/desk/` (build output) | NOT UPDATED | No time tracking in compiled JS |

---

## Summary of P0/P1 Issues for Fix Task

| # | Severity | Issue |
|---|---|---|
| 1 | P0 | `TimeTracker.vue` never created — entire timer UI missing |
| 2 | P0 | `TimeEntryDialog.vue` is dead code — never imported |
| 3 | P0 | No sidebar integration in `TicketAgentSidebar.vue` or `TicketDetailsTab.vue` |
| 4 | P0 | No unit tests (`test_hd_time_entry.py` missing) |
| 5 | P0 | No localStorage timer persistence code |
| 6 | P0 | Frontend never rebuilt (`yarn build`) |
| 7 | P1 | No migration patch in `patches.txt` |
| 8 | P1 | `ignore_permissions=True` bypasses DocType RBAC |
| 9 | P1 | Manual `frappe.db.commit()` anti-pattern |
| 10 | P1 | `createResource` URL non-reactive in TimeEntryDialog |

---

## Recommendation

A comprehensive fix task is required. The backend API layer is functional and can be retained. The fix must:
1. Create `TimeTracker.vue` with full timer UI (start/stop, elapsed display, localStorage persistence)
2. Integrate `TimeTracker` into the ticket sidebar (following `RelatedTickets.vue` pattern in `TicketDetailsTab.vue`)
3. Wire `TimeEntryDialog.vue` into `TimeTracker.vue`
4. Create `test_hd_time_entry.py` with all required test cases
5. Create migration patch and register in `patches.txt`
6. Fix `ignore_permissions` and `frappe.db.commit()` anti-patterns
7. Add `autoname` to DocType
8. Add ownership check for delete (agents can only delete own entries)
9. Rebuild frontend and sync to bench
