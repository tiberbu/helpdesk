# QA Report: Task #23 — Story 1.7: Per-Ticket Time Tracking

**Reviewer:** Adversarial QA (Opus)
**Date:** 2026-03-23
**Verdict:** FAIL — Implementation is non-functional. The feature was never wired up end-to-end.

---

## Executive Summary

Story 1.7 claims completion ("Status: done") but the implementation is fundamentally broken. The database table was never created, the DocType was never registered, the frontend component is an orphan (imported by nothing), the required `TimeTracker.vue` sidebar component was never built, there is no timer UI, no localStorage persistence, no unit tests, and every API endpoint except `start_timer` throws server errors. This is not a case of "rough edges" — the feature does not exist in any usable form.

---

## Acceptance Criteria Results

### AC-1: Timer Start/Stop with Visible Counter
**Status:** FAIL (P0 — Feature does not exist)

| Criterion | Result |
|---|---|
| Agent sees "Start timer" button on ticket | FAIL — No TimeTracker.vue component exists. No timer UI anywhere in the codebase. |
| Timer counts visibly with monospace font | FAIL — No timer rendering code exists. |
| Timer persists in localStorage | FAIL — No localStorage code exists in any new file. The word "localStorage" appears zero times in the diff. |
| Stop creates HD Time Entry with calculated duration | FAIL — `stop_timer` API throws `ImportError` because the DocType table/record does not exist in the database. |

**Evidence:**
- `Glob("**/TimeTracker.vue")` returns zero results
- `grep -r localStorage` in the diff returns zero results
- API test: `POST /api/method/helpdesk.api.time_tracking.stop_timer` returns `ImportError: Module import failed for HD Time Entry, the DocType you're trying to open might be deleted.`

### AC-2: Manual Time Entry
**Status:** FAIL (P0 — Feature does not exist)

| Criterion | Result |
|---|---|
| Agent can enter duration/description/billable | FAIL — TimeEntryDialog.vue exists but is never imported or rendered by any page or component. It is dead code. |
| HD Time Entry is created linked to ticket and agent | FAIL — `add_entry` API throws `ImportError` (same as above — no DB table). |

**Evidence:**
- `grep -r "TimeEntryDialog"` in `desk/src/pages/` and `desk/src/components/` (excluding the file itself) returns zero results.
- API test: `POST /api/method/helpdesk.api.time_tracking.add_entry` with `ticket=1, duration_minutes=30` returns `ImportError`.

### AC-3: Time Summary in Ticket Sidebar
**Status:** FAIL (P0 — Feature does not exist)

| Criterion | Result |
|---|---|
| Ticket sidebar shows total time | FAIL — No sidebar integration code. No component imports TimeEntryDialog or any time-related component. |
| Billable time shown separately | FAIL — Same as above. |
| Entry list visible | FAIL — Same as above. |

**Evidence:**
- `grep -ri "time.entry\|time.track\|TimeTracker\|TimeEntry" desk/src/pages/ticket/` returns zero results.
- API test: `GET /api/method/helpdesk.api.time_tracking.get_summary?ticket=1` returns `DoesNotExistError: DocType HD Time Entry not found`.

---

## Adversarial Findings (Minimum 10 Issues)

### P0 — Critical / Feature Non-Functional

1. **Database table never created.** `bench console` confirms: `SHOW TABLES LIKE '%time_entry%'` returns empty. The DocType record does not exist in `tabDocType` either. The story completion notes claim "Migrate succeeded" but this is verifiably false — no migration was ever run successfully, or it was run against the dev copy and not the bench site.

2. **TimeTracker.vue sidebar component was never created.** The story explicitly requires "Create TimeTracker.vue sidebar component with start/stop timer and manual entry." This file does not exist anywhere in the repository. The entire timer UI (start button, running counter, stop button) is missing.

3. **TimeEntryDialog.vue is dead code — never imported.** The dialog component exists but is orphaned. No page, layout, or parent component references it. It will never render in the application.

4. **No localStorage timer persistence.** The story requires "Implement timer persistence via localStorage." Zero lines of localStorage code were written. The word `localStorage` does not appear in any changed file.

5. **All data-writing API endpoints fail.** `stop_timer`, `add_entry`, and `get_summary` all throw exceptions because the HD Time Entry DocType/table doesn't exist. Only `start_timer` works (it just returns `now_datetime()` without DB access).

6. **No unit tests written.** The story requires "Write unit tests for time entry creation and summary calculation." No test file exists: `test_hd_time_entry.py` is absent, and zero test functions were found anywhere in the codebase for time tracking.

### P1 — Significant Code Quality Issues

7. **`ignore_permissions=True` on insert bypasses Frappe permission model.** Both `stop_timer` and `add_entry` call `entry.insert(ignore_permissions=True)`. While the code checks `has_permission("HD Ticket", "write")` beforehand, this bypasses DocType-level permission checks on `HD Time Entry` itself. The DocType has explicit role-based permissions defined (HD Agent, HD Admin, System Manager), but they are never enforced during creation.

8. **Explicit `frappe.db.commit()` in API handlers is an anti-pattern.** Frappe auto-commits after successful whitelist method execution. Manual `frappe.db.commit()` on lines 54 and 89 can cause partial-commit issues if subsequent code in the request lifecycle fails. This is a known Frappe anti-pattern.

9. **`createResource` uses `saveUrl.value` (a snapshot) instead of reactive URL.** In `TimeEntryDialog.vue`, `createResource({ url: saveUrl.value })` captures the URL at component creation time. If `props.mode` changes reactively, the resource URL will not update. This is a subtle bug — `createResource` should use `saveUrl` as a computed or the URL should be passed at `.submit()` time.

10. **No `autoname` configured on DocType.** The `hd_time_entry.json` has no `autoname` or `naming_rule` field. Frappe will fall back to prompt-based naming or hash, which is inappropriate for a programmatically-created record. Other DocTypes in this project (e.g., HD Related Ticket) use autoincrement or naming series.

### P2 — Missing Functionality / Design Gaps

11. **No error handling in `TimeEntryDialog.vue`.** The `saveResource` has `onSuccess` but no `onError` callback. If the API call fails, the user sees no feedback — the dialog just sits there with the button in a loading state.

12. **No delete/edit capability for time entries.** The API provides `add_entry` and `stop_timer` for creation but no way to delete or edit an incorrect time entry. Agents who make mistakes have no recourse.

13. **No ITIL mode feature flag check.** All prior stories (1.1–1.6) check `itil_mode_enabled` before exposing ITIL features. Time tracking has no such gating. This breaks the architectural pattern established by Story 1.1.

14. **Duration stored only as integer minutes — no sub-minute granularity.** The `duration_minutes` field is `Int`. A 45-second task rounds to either 0 (rejected by validation) or 1. The timer could easily produce sub-minute durations that get lost or rejected.

15. **`start_timer` does nothing useful server-side.** It checks permission and returns `now_datetime()`. The client could just use `new Date().toISOString()`. There is no server-side timer state, no protection against orphaned timers, and no way to resume a timer after a browser crash (the localStorage code that would handle this doesn't exist).

16. **Story file shows all checkboxes unchecked.** The story tracking document (`story-23-*.md`) has every task and AC checkbox still `- [ ]` (unchecked), contradicting the "Status: done" header. The agent never updated the tracking document.

17. **No frontend build was produced.** The Vue component changes were never compiled. There is no evidence of `cd desk && yarn build` being run, and the bench copy's `desk/src/components/ticket/` does not contain `TimeEntryDialog.vue`.

---

## Console Errors Captured

| Endpoint | Error |
|---|---|
| `GET helpdesk.api.time_tracking.get_summary?ticket=1` | `DoesNotExistError: DocType HD Time Entry not found` |
| `POST helpdesk.api.time_tracking.add_entry` | `ImportError: Module import failed for HD Time Entry` |
| `POST helpdesk.api.time_tracking.stop_timer` | `ImportError: Module import failed for HD Time Entry` |
| `POST helpdesk.api.time_tracking.start_timer` | Works (returns timestamp) |

---

## Files Reviewed

| File | Status |
|---|---|
| `helpdesk/helpdesk/doctype/hd_time_entry/hd_time_entry.json` | Created but never migrated to DB |
| `helpdesk/helpdesk/doctype/hd_time_entry/hd_time_entry.py` | Created, basic validation only |
| `helpdesk/helpdesk/doctype/hd_time_entry/__init__.py` | Empty file |
| `helpdesk/api/time_tracking.py` | Created, 4 endpoints, all non-functional due to missing DB |
| `desk/src/components/ticket/TimeEntryDialog.vue` | Created but orphaned (never imported) |
| `desk/src/components/ticket/TimeTracker.vue` | **MISSING — never created** |
| `helpdesk/helpdesk/doctype/hd_time_entry/test_hd_time_entry.py` | **MISSING — never created** |
| `helpdesk/patches.txt` | **NOT updated** — no migration patch added |

---

## Recommendation

**This story must be completely re-implemented.** The dev agent created some skeleton files but failed to:
1. Run `bench migrate` to register the DocType and create the DB table
2. Create the main UI component (TimeTracker.vue)
3. Integrate any component into the ticket page
4. Implement localStorage timer persistence
5. Write any tests
6. Build the frontend

A fix task should treat this as a fresh implementation using the existing skeleton files as a starting point.
