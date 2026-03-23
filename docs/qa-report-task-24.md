# QA Report: Story 1.8 — Major Incident Flag and Workflow

**Task #24** | Reviewer: Adversarial QA (Opus) | Date: 2026-03-23
**Verdict: FAIL** — Multiple P0/P1 issues found

---

## Acceptance Criteria Results

### AC-1: Agent checks is_major_incident -> confirmation dialog, escalation notifications, red banner with elapsed time
**FAIL (P1)**

- **Confirmation dialog**: PASS — Dialog is wired through `TicketHeader.vue` "..." menu -> `showMajorIncidentDialog` provide/inject -> Dialog in `TicketAgent.vue`. Correct.
- **Escalation notifications**: PASS (with caveats) — `_send_major_incident_notifications` sends emails and `publish_realtime`. See issue #6 for realtime room naming concern.
- **Red banner with elapsed time**: PARTIAL FAIL — Banner renders and calculates elapsed time, but the elapsed time is a **static computed property** that never updates. There is no `setInterval` or reactive timer. Once rendered, the "Declared Xm ago" text is frozen until the component re-renders for another reason. A "live elapsed time" display requires a ticking timer.

### AC-2: Agent posts status update -> propagate to all linked tickets
**PASS**

- `propagate_update` API correctly posts an `HD Ticket Comment` on the major-incident ticket and all linked tickets via `HD Related Ticket` child rows.
- Frontend `MajorIncidentBanner.vue` has a "Propagate Update" button + dialog.
- API-level test verified via curl: returns `{"success": true, "count": N}`.

### AC-3: Major incident resolved -> post-incident review fields appear (root_cause_summary, corrective_actions, prevention_measures)
**FAIL (P0)**

- The fields exist in `hd_ticket.json` with `depends_on: eval:doc.is_major_incident` — this only works in Frappe's desk form view (`/app/hd-ticket/...`), **not in the custom Vue helpdesk frontend**.
- A grep across the entire `desk/src/` directory for `root_cause_summary`, `corrective_actions`, or `prevention_measures` returns **zero results**. These fields are **never rendered in the Vue frontend**.
- The AC says "post-incident review fields appear" — they don't appear anywhere a helpdesk agent would actually see them in the helpdesk app. This acceptance criterion is completely unmet in the user-facing UI.

### AC-4: Manager views /helpdesk/major-incidents -> cards with elapsed time, linked ticket count, affected customer count
**FAIL (P0)**

- **Cards with elapsed time**: PASS — `MajorIncidentCard.vue` displays elapsed time.
- **Linked ticket count**: PASS — `MajorIncidentCard.vue` displays `linked_ticket_count`.
- **Affected customer count**: FAIL — The AC explicitly requires "affected customer count" but:
  - The `get_major_incident_summary` API does **not** compute or return `affected_customer_count`.
  - `MajorIncidentCard.vue` does **not** display any customer count.
  - The original story spec (story-1.8) defined this as "unique count of `raised_by` across all linked tickets plus the major incident ticket itself."
  - This field is entirely missing from the implementation.

---

## Additional Issues Found (Adversarial Review)

### Issue #5: No ITIL Mode Feature Flag Gating (P1)

Story 1.1 established the `itil_mode_enabled` feature flag in HD Settings. The `major_incident_contacts` field in `hd_settings.json` correctly has `depends_on: eval:doc.itil_mode_enabled==1`, but:

- **Backend**: None of the API endpoints (`flag_major_incident`, `propagate_update`, `get_major_incident_summary`) check whether ITIL mode is enabled. Agents can flag major incidents even when ITIL features are supposed to be off.
- **Frontend**: The "Declare Major Incident" menu item in `TicketHeader.vue` is always visible regardless of ITIL mode. The sidebar link "Major Incidents" in `layoutSettings.ts` is always visible.
- All ITIL features should be gated behind the feature flag. Without this, organizations that haven't opted into ITIL mode see confusing Major Incident options everywhere.

### Issue #6: Toast Message is Inverted After Flagging (P1)

In `TicketAgent.vue` lines 185-189, the `onSuccess` callback for `flagResource` checks `ticket.value?.doc?.is_major_incident` to decide which toast message to show. But `onSuccess` fires **before** `reloadTicket` completes — the doc still has the **old** value. This means:

- When you **flag** a major incident (was 0, now 1), the toast says "Major incident flag removed" (because doc still shows 0).
- When you **unflag** (was 1, now 0), the toast says "Ticket declared as major incident" (because doc still shows 1).

The toast messages are backwards.

### Issue #7: Massive Test Data Leak — 31 Orphaned Major Incident Records (P1)

The `tearDown` in `test_major_incident.py` calls `frappe.db.rollback()`, but the API methods (`flag_major_incident`, `propagate_update`) call `frappe.db.commit()` internally. Once committed, rollback is a no-op. This leaves behind:

- **31 stale test tickets** all flagged as major incidents (confirmed via API call returning 31 records, all named "Major Incident Test Ticket").
- The major incidents dashboard would show 31 garbage test records to real users.
- Each test run adds 6 more records that never get cleaned up.

### Issue #8: `linkedCount` in Banner Relies on Unavailable Data (P2)

`MajorIncidentBanner.vue` computes `linkedCount` from `ticket?.value?.doc?.related_tickets`. However, `related_tickets` is a child table field. Whether the Frappe `document_resource` actually fetches child table rows depends on the `useTicket` composable's configuration. A grep for `related_tickets` in `desk/src/composables/` returns **no results** — suggesting the child table data may not be loaded, causing `linkedCount` to always be 0 even when related tickets exist.

### Issue #9: Realtime Room Format Incorrect (P2)

`_send_major_incident_notifications` publishes to `room=f"agent:{email}"`. Frappe's standard realtime room format for per-user notifications is `user:{user}`. There is no evidence that helpdesk agents subscribe to `agent:{email}` rooms. The in-app realtime notifications likely never reach their intended recipients.

### Issue #10: No Pagination or Limit on Major Incident Summary API (P2)

`get_major_incident_summary` fetches ALL tickets with `is_major_incident=1` with no `limit` parameter. Combined with the test data leak (issue #7), the API already returns 31 records. In production with long-running systems, this could return hundreds of records. Should include pagination or at minimum filter to only open/active incidents by default.

### Issue #11: Propagated Updates Are Public Comments — Not Internal (P2)

`propagate_update` creates `HD Ticket Comment` records with `is_internal: 0`. This means major incident status updates are visible to customers on linked tickets. Major incident coordination updates (e.g., "investigating root cause", "escalating to infrastructure team") are operational/internal communications that should not be exposed to customers. This is a security/information-disclosure concern. The `is_internal` flag should be 1, or there should be a toggle.

### Issue #12: `flag_major_incident` Is a Toggle, Not Explicit Flag/Unflag (P2)

The API uses a toggle pattern — calling `flag_major_incident` flips the current state. This is race-condition prone: if two agents simultaneously try to flag the same ticket, one succeeds and the other accidentally unflags it. An explicit `action` parameter (e.g., `flag` or `unflag`) would be safer and more predictable.

### Issue #13: Email Template Renders Raw HTML Variable Without Escaping (P3)

In `_send_major_incident_notifications`, `ticket_link` is built as raw HTML:
```python
ticket_link = f"<a href='{ticket_url}'>{ticket_subject_escaped} (#{ticket})</a>"
```
The `ticket_url` is not URL-encoded. While ticket IDs are integers (low risk), this is still a poor pattern. Additionally, the `ticket_link` variable containing raw HTML is passed to `frappe.render_template` — if the template uses `{{ ticket_link }}` with auto-escaping (Jinja2 default), the HTML will be double-escaped. The template must use `{{ ticket_link | safe }}` or similar — confirmed the template uses `{{ ticket_link }}` which may cause broken HTML display depending on Jinja2 autoescape settings.

### Issue #14: "Customers" Label Not Translated in layoutSettings.ts (P3)

In `layoutSettings.ts` line 29, the "Customers" sidebar label is `"Customers"` (raw string) while all other labels use `__("...")` for i18n translation. This is a pre-existing bug but was touched in this changeset.

---

## Summary of Findings

| # | Severity | Description |
|---|----------|-------------|
| 1 | P0 | Post-incident review fields (root_cause_summary, corrective_actions, prevention_measures) not rendered in Vue frontend — AC-3 completely unmet |
| 2 | P0 | Affected customer count missing from API and dashboard cards — AC-4 partially unmet |
| 3 | P1 | Elapsed time in banner is static/frozen, not a live ticking timer |
| 4 | P1 | No ITIL mode feature flag gating on backend APIs or frontend components |
| 5 | P1 | Toast messages are inverted (shows wrong message after flag/unflag) |
| 6 | P1 | Test data leak: 31+ orphaned major incident test records never cleaned up |
| 7 | P2 | `linkedCount` in banner likely always 0 due to child table not fetched |
| 8 | P2 | Realtime room format `agent:{email}` doesn't match Frappe convention `user:{user}` |
| 9 | P2 | No pagination on `get_major_incident_summary` — returns unbounded results |
| 10 | P2 | Propagated updates are public (is_internal=0) — leaks operational info to customers |
| 11 | P2 | Toggle-based API is race-condition prone |
| 12 | P3 | Email template may double-escape HTML link |
| 13 | P3 | "Customers" label not wrapped in __() for i18n |

**P0 issues: 2** | **P1 issues: 4** | **P2 issues: 5** | **P3 issues: 2**

---

## Browser Testing Notes

Playwright MCP was not available. API-level testing was performed via curl:

- `GET helpdesk.api.incident.get_major_incident_summary` — returned 31 stale test records (evidence of issue #7), no `affected_customer_count` field (evidence of issue #2)
- `POST helpdesk.api.incident.flag_major_incident` with ticket=1 — returned `{"success":true,"is_major_incident":1}` confirming toggle works
- Frontend Vue code reviewed by reading source files directly

---

## Recommendation

**Do not ship.** Two P0 issues (missing AC-3 and AC-4 functionality) and four P1 issues require a fix task before this story can be considered complete. The test data leak (issue #6) should be fixed immediately as it pollutes the production database on every test run.
