# QA Report: Task #23 — Story 1.7: Per-Ticket Time Tracking

**Reviewer:** Adversarial QA (Opus)
**Date:** 2026-03-23 (revised 2026-03-24)
**Verdict:** CONDITIONAL PASS — Core functionality works. 10+ issues found, mostly P1/P2.

---

## Executive Summary

The implementation has been substantially reworked since the initial (non-functional) commit. The backend API, DocType, unit tests (81 passing), and frontend components (TimeTracker.vue, TimeEntryDialog.vue) all exist and are integrated into the ticket sidebar. The APIs work end-to-end via curl. However, the adversarial review reveals persistent stored XSS via unsanitized description, a frontend/backend permission model mismatch for delete visibility, no ITIL feature flag gating, and several code quality issues.

---

## Acceptance Criteria Results

### AC-1: Timer Start/Stop with Visible Counter
**Status:** PASS (with caveats)

| Criterion | Result |
|---|---|
| Agent sees "Start timer" button on ticket | PASS — `TimeTracker.vue:52-62` renders "Start Timer" button, integrated at `TicketDetailsTab.vue:79-82` |
| Timer counts visibly with monospace font | PASS — `font-mono text-lg tabular-nums` class at line 22, `formattedElapsed` computed with HH:MM:SS format |
| Timer persists in localStorage | PASS — `localStorage.setItem/getItem` with `hd_timer_${ticketId}` key, `loadTimer()` restores on mount |
| Stop creates HD Time Entry with calculated duration | PASS — `stopTimer()` opens TimeEntryDialog with `stop-timer` mode, calls `stop_timer` API which creates entry |

**Caveats:**
- Cross-ticket timer detection iterates all `localStorage` keys (line 242-255) — O(n) scan on every mount

### AC-2: Manual Time Entry
**Status:** PASS

| Criterion | Result |
|---|---|
| Agent can enter duration/description/billable | PASS — TimeEntryDialog.vue has hours/minutes inputs, textarea, checkbox |
| HD Time Entry is created linked to ticket and agent | PASS — `add_entry` API creates entry, verified via curl: returns `success: true` |

### AC-3: Time Summary in Ticket Sidebar
**Status:** PASS

| Criterion | Result |
|---|---|
| Ticket sidebar shows total time | PASS — `formatMinutes()` renders total at line 70-73 |
| Billable time shown separately | PASS — Conditional display at line 75-80 |
| Entry list visible | PASS — `<ul>` at line 84-119 with entry details, badges, delete buttons |

---

## Adversarial Findings

### P1 — Significant Issues

1. **Stored XSS via description field (OWASP A7).** The `description` field uses Frappe `Text` fieldtype and is stored raw without sanitization. Existing database entries contain `<b>bold</b> <img src="x">test` (confirmed via `get_summary` API response). In `TimeTracker.vue:107`, the description is rendered via `{{ entry.description }}` which Vue auto-escapes for text interpolation — so the XSS is *mitigated in the current template*. However, the stored HTML is a persistent ticking bomb: any future template change to `v-html`, any report/export that renders it raw, or any Frappe list view / print format will execute the payload. The description field should either be `Small Text` (no rich formatting expected), or the API/model should strip HTML on write. The existing poisoned entries in the database need to be cleaned.

2. **Frontend `canDelete()` shows delete button for System Manager, but backend blocks it.** `TimeTracker.vue:350` checks `has_role("System Manager")` and shows the trash icon. But `delete_entry()` in `time_tracking.py:246` uses `is_agent()` as a pre-gate, and `PRIVILEGED_ROLES` explicitly excludes System Manager (per the comment at `hd_time_entry.py:34`). A System Manager user sees the delete button, clicks it, and gets an error toast. The frontend `canDelete()` should mirror the backend's permission model: System Manager alone is not sufficient.

3. **No edit/update capability for time entries.** Agents who enter incorrect duration, description, or billable status have no way to correct it short of deleting and re-creating. There is no `update_entry` API endpoint. For a billing/time-tracking feature, this is a significant usability gap — agents should be able to fix mistakes without losing the original timestamp/audit trail.

4. **`delete_entry` uses `ignore_permissions=True` bypassing DocType permissions.** At `time_tracking.py:261`, `frappe.delete_doc("HD Time Entry", name, ignore_permissions=True)` is used because regular Agents don't have `delete:1` in the DocType JSON. While the comment explains the rationale and the `_check_delete_permission` + `on_trash` hooks enforce custom checks, this is a defense-in-depth violation: any code path that calls `frappe.delete_doc` with `ignore_permissions=True` bypasses Frappe's entire permission stack. If the `on_trash` hook is ever accidentally removed or refactored, there's no safety net.

5. **No rate limiting on time entry creation.** An agent (or compromised account) could programmatically create thousands of time entries via rapid `add_entry` calls. There's no throttle, no daily cap, and no bulk detection. For a billing feature, this is a fraud surface.

### P2 — Design Gaps and Code Quality

6. **No ITIL mode feature flag gating.** All prior ITIL features (Stories 1.1-1.6, 1.8) check `itil_mode_enabled` before exposing functionality. Time tracking has no such check — neither in the API (`time_tracking.py`) nor in the frontend (`TimeTracker.vue` / `TicketDetailsTab.vue`). This breaks the architectural pattern established by Story 1.1. Time tracking should at minimum be conditionally rendered based on the ITIL config flag.

7. **`deleteTarget` dialog v-model missing.** In `TimeTracker.vue:151-171`, the `<Dialog>` for delete confirmation uses `v-if="deleteTarget"` but has no `v-model` binding. The Dialog component may not properly manage its open state, relying entirely on the `@close` handler to set `deleteTarget = null`. If the Dialog's internal close mechanism fires before `@close` propagates, the component could enter an inconsistent state.

8. **Timer `tick()` drift on inactive tabs.** `setInterval(tick, 1000)` at `TimeTracker.vue:235/276/306` uses `Date.now()` difference for elapsed calculation (good), but `setInterval` itself is throttled by browsers in background tabs (typically to once per second at best, sometimes once per minute). While the *calculated* elapsed will be correct when the tab returns to foreground, the visual counter will appear frozen during background periods, confusing users who alt-tab back.

9. **`formatDate` shows only day+month, no year.** `TimeTracker.vue:384-388` formats timestamps as `"2-digit" day + "short" month` (e.g., "23 Mar"). For entries older than the current year, there's no way to distinguish which year they belong to. A ticket with long-lived time tracking across December-January boundaries would show misleading dates.

10. **`agent_name` formatting truncates last name to initial.** `time_tracking.py:150-152` formats names as "John D." rather than "John Doe". For teams where multiple agents share a first name (John D., John S.), this is ambiguous. The full last name should be shown, or at minimum the formatting should be configurable.

11. **`limit=0` on `get_summary` fetches ALL entries with no pagination.** `time_tracking.py:310` uses `limit=0` to fetch every time entry for a ticket. For tickets with hundreds of entries (e.g., long-running support cases), this returns a potentially massive JSON payload in a single response. There's no pagination, no lazy loading, and no configurable limit.

12. **Story tracking file still shows all checkboxes unchecked.** `story-23-story-1-7-per-ticket-time-tracking.md` still has `- [ ]` on all ACs and tasks despite Status: done. The File List and Change Log sections are empty. The dev agent never updated its tracking document after completing work.

---

## Console Errors Captured

| Test | Result |
|---|---|
| `GET get_summary?ticket=1` (authenticated) | OK — returns 9 entries, 70 total minutes |
| `POST start_timer` (authenticated) | OK — returns `started_at` timestamp |
| `POST add_entry` with `duration_minutes="abc"` | Returns `ValidationError: duration_minutes must be a valid integer` |
| Unit tests (81) | All pass, 6.8s |

---

## Files Reviewed

| File | Status |
|---|---|
| `helpdesk/helpdesk/doctype/hd_time_entry/hd_time_entry.json` | OK — autoname: hash, proper role permissions |
| `helpdesk/helpdesk/doctype/hd_time_entry/hd_time_entry.py` | OK — validate(), on_trash(), _check_delete_permission() |
| `helpdesk/api/time_tracking.py` | OK — 5 endpoints, input validation, is_agent() gates |
| `helpdesk/helpdesk/doctype/hd_time_entry/test_hd_time_entry.py` | OK — 81 tests, comprehensive coverage |
| `desk/src/components/ticket/TimeTracker.vue` | OK — timer, summary, delete, localStorage |
| `desk/src/components/ticket/TimeEntryDialog.vue` | OK — manual/timer entry dialog |
| `desk/src/components/ticket-agent/TicketDetailsTab.vue` | OK — TimeTracker integrated with isAgent guard |

---

## Recommendation

The core feature is functional and well-tested. A fix task should address:
1. **P1-1:** Sanitize description on write (strip HTML) and clean existing poisoned entries
2. **P1-2:** Fix `canDelete()` to exclude bare System Manager from delete UI
3. **P1-3:** Add edit/update capability (or at minimum document as a known limitation)
4. **P2-6:** Add ITIL mode feature flag gating to match architectural pattern
5. **P2-7/8:** Minor frontend robustness fixes
