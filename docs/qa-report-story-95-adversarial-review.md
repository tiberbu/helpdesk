# Adversarial Review: Story #95 — Fix TimeTracker.vue bench drift + P2 defense-in-depth gaps

**Reviewer:** Adversarial QA (Opus)
**Date:** 2026-03-23
**Task ID:** mn3bxrrpd3w40o
**Artifact Reviewed:** `helpdesk/api/time_tracking.py` (dev + bench), `TimeTracker.vue`, `TimeEntryDialog.vue`, `hd_time_entry.py`, `test_hd_time_entry.py`
**Scope:** The `int()` -> `cint()` fix and overall defense-in-depth posture of the time tracking subsystem.

---

## Findings

1. **`cint()` silently converts garbage to 0, which then fails on a *different* validation — misleading error message.** The stated goal was "graceful error (not a 500 unhandled ValueError)" when passing `duration_minutes=abc`. With `cint('abc')` returning `0`, the user gets `"Duration must be at least 1 minute"` — not `"Invalid duration value"`. The error is technically graceful (417 not 500), but the message is *wrong*: the problem isn't that the duration is too short, it's that the input isn't a number. A proper defense-in-depth fix would detect non-numeric input explicitly and throw a semantically correct error like `"duration_minutes must be a valid integer"`.

2. **`billable` parameter `cint()` conversion has no validation at all after conversion.** `cint('abc')` silently becomes `0` (falsy/non-billable). There is no check that billable is in `{0, 1}`. Passing `billable=999` would store `999` in the database. The acceptance criterion says "Passing non-numeric string as `billable` returns a graceful error" — but it doesn't return *any* error; it silently coerces to `0`. This is not what the acceptance criteria describe.

3. **No unit tests for the actual `cint()` fix.** The test file has 30+ tests but **zero tests** for `add_entry(duration_minutes="abc")` or `stop_timer(billable="xyz")`. The entire point of Story #93/95 was the `int()` -> `cint()` change, yet there is no regression test proving the fix works. If someone reverts `cint` back to `int`, no test would catch it.

4. **`delete_entry` fetches the document *before* checking `is_agent()` (line 163).** `frappe.get_doc("HD Time Entry", name)` performs a database read. If `name` is a crafted non-existent value, you get a `DoesNotExistError` before the permission gate fires. An unauthenticated or non-agent user can probe for existence of time entry names by observing different error types (404 vs 403). The `is_agent()` check should come first.

5. **`ticket` parameter is never validated as an existing HD Ticket before `frappe.has_permission()`.** In `add_entry()` and `stop_timer()`, if `ticket` is an empty string or a nonexistent ticket ID, `frappe.has_permission("HD Ticket", "write", doc=ticket, throw=True)` will throw a generic `DoesNotExistError` — not a user-friendly "Ticket not found" message. Defense-in-depth should validate the ticket exists first.

6. **`description` parameter is not sanitized for XSS/HTML injection.** The `description` field is stored raw and rendered in the frontend via `{{ entry.description }}`. While Vue's `{{ }}` template syntax auto-escapes, the `:title="entry.description || ''"` attribute binding could potentially be exploited if a future refactor switches to `v-html`. There is no server-side sanitization (e.g., `frappe.utils.strip_html_tags`) as a defense-in-depth measure.

7. **`get_summary` with `limit=0` is a potential DoS vector.** If a ticket accumulates thousands of time entries (e.g., via automated script), `limit=0` fetches them all in one query with no pagination. This could cause memory exhaustion or long response times. There's no rate limit, no pagination, and no upper bound on returned entries.

8. **Timer localStorage is vulnerable to cross-tab race conditions.** Two browser tabs on the same ticket can both call `startTimer()`, each overwriting the `localStorage` key. When tab A stops the timer, it clears localStorage, but tab B still shows a running timer with a stale `started_at`. There's no locking mechanism. The `foreignTimerTicket` check only scans for *other* tickets, not duplicate timers on the *same* ticket.

9. **`canDelete()` in TimeTracker.vue relies on client-side `window.frappe.user.has_role()` which may be undefined.** The optional chaining `?.` prevents a crash, but if `window.frappe.user` is not populated (e.g., SSR context, or frappe-ui version mismatch), `hasAdminRole` silently becomes `undefined` (falsy), and Agent Managers won't see the delete button even though the backend allows it. There's no fallback — the component doesn't fetch the user's roles from the API independently.

10. **Frontend `TimeEntryDialog` allows `hours=24` AND `minutes=59` simultaneously = 1499 minutes, exceeding `MAX_DURATION_MINUTES` (1440).** The `:max="24"` on hours and `:max="59"` on minutes are independently enforced HTML constraints, but HTML `max` attributes on number inputs are merely *advisory* — the user can type any value. The JavaScript `isValid` computed does catch this (`totalMinutes.value <= MAX_DURATION_MINUTES`), so the save button disables, but the `showMaxDurationError` message only shows after `touched.value` is true (after first save attempt). A user could set hours=24, minutes=30 and not see any error until they click Save. The UX is confusing — the hours field happily accepts 24 while the minutes field accepts 30, with no immediate feedback.

11. **Dev/bench sync is manual and undocumented in CI.** The task confirms files are in sync, but there's no automated mechanism (symlink, rsync hook, CI check) to ensure they stay in sync. The MEMORY.md documents manual `rsync` commands, meaning every future change risks bench drift — the exact problem this story was supposed to fix. The root cause (two separate codebases) is not addressed.

12. **`stop_timer` trusts the client-supplied `duration_minutes` without cross-checking against `started_at`.** The client sends both `started_at` and `duration_minutes`. A malicious agent could send `started_at=5 minutes ago` but `duration_minutes=1440` to inflate billable hours. The backend validates each independently but never checks `duration_minutes <= (now - started_at)` (with some tolerance). This is a billing integrity gap.

13. **`PRIVILEGED_ROLES` is defined as a constant in `hd_time_entry.py` and hardcoded in `TimeTracker.vue`.** If a new privileged role is added (e.g., "Support Manager"), it must be updated in *three* places: the Python constant, the DocType JSON permissions, and the Vue `canDelete()` function. There's no single source of truth that the frontend consumes — it's a hardcoded list that will inevitably drift.

14. **No audit trail for deleted time entries.** `delete_entry` calls `frappe.delete_doc` which permanently removes the record. There's no soft-delete, no activity log entry, and no record of who deleted what. For a billing-related feature, this is a compliance gap — a privileged user could delete billable entries with no trace.

---

## Severity Summary

| # | Severity | Finding |
|---|----------|---------|
| 1 | P2 | `cint` produces misleading error message for non-numeric input |
| 2 | P1 | `billable` silently coerced — acceptance criteria not actually met |
| 3 | P1 | No unit tests for the `cint()` fix (the whole point of the story) |
| 4 | P2 | `delete_entry` information leak: doc fetch before auth check |
| 5 | P3 | `ticket` not validated for existence before permission check |
| 6 | P3 | No server-side HTML sanitization on description |
| 7 | P2 | `get_summary` with `limit=0` — unbounded query, DoS risk |
| 8 | P3 | localStorage timer race condition across tabs |
| 9 | P2 | `canDelete()` depends on fragile `window.frappe` globals |
| 10 | P3 | Confusing UX: hours/minutes fields don't cross-validate immediately |
| 11 | P2 | No automated dev/bench sync — root cause of bench drift unaddressed |
| 12 | P1 | `duration_minutes` not cross-validated against `started_at` — billing fraud risk |
| 13 | P2 | Privileged roles hardcoded in 3 places — will drift |
| 14 | P2 | No audit trail for deleted billable time entries |

**P0:** 0 | **P1:** 3 | **P2:** 6 | **P3:** 4 | **Total:** 13 findings
