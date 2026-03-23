# QA Report: Story 1.8 - Major Incident Flag and Workflow

**Reviewer**: Adversarial Review (Cynical)
**Date**: 2026-03-23
**Story**: 1.8 - Major Incident Flag and Workflow
**Verdict**: 13 findings identified (2 P0, 4 P1, 5 P2, 2 P3)

---

## P0 - Critical / Blocking

### F-01: Post-Incident Review fields not rendered in frontend

**Severity**: P0
**Files**: `desk/src/` (all frontend files)
**Description**: The story requires post-incident review fields (Root Cause Summary, Corrective Actions, Prevention Measures) to be visible in the ticket form when `is_major_incident=1`. These fields exist in the DocType JSON (`hd_ticket.json` lines 534-549) with `depends_on: "eval:doc.is_major_incident"`, but there is **zero frontend code** that renders these fields. A `grep -ri "root_cause\|corrective\|prevention\|post.incident" desk/src/` returns no matches. The Frappe standard form may render them, but the custom Vue ticket agent view (`TicketAgent.vue`) does not include them anywhere - not in the sidebar, not in a tab, not in any section. Agents have no way to fill in post-incident review data from the helpdesk UI.

### F-02: Test tearDown fails to clean up due to premature commits

**Severity**: P0
**Files**: `test_major_incident.py`, `helpdesk/api/incident.py`
**Description**: Every API method (`flag_major_incident`, `propagate_update`) calls `frappe.db.commit()` explicitly. The test `tearDown()` calls `frappe.db.rollback()`, but rollback cannot undo already-committed transactions. This means test artifacts accumulate permanently in the database. API verification confirmed **25+ orphaned "Major Incident Test Ticket" records** flagged as major incidents still present in the DB. The `get_major_incident_summary` dashboard will show garbage test data to users. This also means running tests repeatedly will slow down queries and pollute the major incidents dashboard.

---

## P1 - High / Significant

### F-03: propagate_update accepts empty messages - no backend validation

**Severity**: P1
**Files**: `helpdesk/api/incident.py:228-277`
**Description**: The `propagate_update` endpoint accepts an empty string as `message` and successfully posts a comment containing only `[Major Incident Update from #X]: ` with no actual content. The frontend has a `trim()` check on the button's `:disabled` prop, but the backend has no validation. Any API caller can spam linked tickets with empty update comments. The backend should reject empty/whitespace-only messages with a `ValidationError`.

### F-04: No ITIL mode gating on Major Incident feature

**Severity**: P1
**Files**: `helpdesk/api/incident.py`, `desk/src/components/ticket-agent/TicketHeader.vue`, `desk/src/components/layouts/layoutSettings.ts`
**Description**: Story 1.1 established an `itil_mode_enabled` feature flag in HD Settings. The HD Settings JSON correctly gates `major_incident_contacts` behind `depends_on: "eval:doc.itil_mode_enabled==1"`, but none of the backend API endpoints (`flag_major_incident`, `propagate_update`, `get_major_incident_summary`) check whether ITIL mode is enabled. The frontend sidebar always shows "Major Incidents" nav item and the "Declare Major Incident" menu option regardless of ITIL mode. This feature should be hidden/disabled when ITIL mode is off.

### F-05: `flag_major_incident` is a toggle - no explicit intent parameter

**Severity**: P1
**Files**: `helpdesk/api/incident.py:184-224`
**Description**: The `flag_major_incident` API is a toggle: calling it once flags, calling it again unflags. This is a dangerous API design for a critical operation. A race condition between two agents could silently unflag a major incident that was just declared. The API should accept an explicit `action` parameter (`"flag"` or `"unflag"`) so callers express clear intent. At minimum, the response already includes `is_major_incident` so the frontend can detect mismatches, but there's no guard against concurrent toggle conflicts.

### F-06: Dashboard has no pagination or limit - N+1 query pattern

**Severity**: P1
**Files**: `helpdesk/api/incident.py:280-314`
**Description**: `get_major_incident_summary` fetches ALL tickets with `is_major_incident=1` (no limit), then executes a separate `frappe.db.count()` query for each ticket to get `linked_ticket_count`. With 25+ orphaned test tickets already in the DB (see F-02), this means 25+ individual COUNT queries per dashboard load. No pagination, no limit, no batch query. At scale this will be slow.

---

## P2 - Medium / Functional

### F-07: MajorIncidentBanner elapsed time is static - no live timer

**Severity**: P2
**Files**: `desk/src/components/ticket/MajorIncidentBanner.vue:97-107`
**Description**: The `elapsedText` computed property calculates elapsed time from `Date.now()` at render time, but it's a `computed()` with no reactive dependency that changes over time. Vue computed properties only re-evaluate when their reactive dependencies change. Since `Date.now()` is not reactive, the elapsed time display ("Declared Xm ago") will be stale and never update while the page is open. It needs a `setInterval` to update a reactive `now` ref, or use `useIntervalFn` from VueUse.

### F-08: MajorIncidentBanner linkedCount reads from `related_tickets` child table array

**Severity**: P2
**Files**: `desk/src/components/ticket/MajorIncidentBanner.vue:93-95`
**Description**: `linkedCount` is computed as `(ticket?.value?.doc?.related_tickets || []).length`. This relies on the Frappe document resource including the full child table array in the response. Whether `related_tickets` is populated in the ticket document resource depends on the specific `useTicket` composable's field list. If the composable doesn't fetch child table rows (common for performance), `linkedCount` will always be 0, and the banner will never show "X linked ticket(s)". The MajorIncidentCard on the dashboard correctly uses the API's `linked_ticket_count` field instead.

### F-09: Toast message in onSuccess relies on stale pre-reload state

**Severity**: P2
**Files**: `desk/src/pages/ticket/TicketAgent.vue:182-189`
**Description**: The `flagResource.onSuccess` callback reads `ticket.value?.doc?.is_major_incident` to determine which toast message to show, then calls `reloadTicket()`. It works by coincidence (reading the OLD value before reload), but the correct approach is to use the API response data (`data.is_major_incident`) which is available in the `onSuccess` callback parameter. If the ticket composable ever pre-updates optimistically, the toast would show the wrong message.

### F-10: MajorIncidentCard router navigation uses inconsistent path

**Severity**: P2
**Files**: `desk/src/pages/major-incidents/MajorIncidentCard.vue:10-12`
**Description**: The `<a>` tag has `href="/helpdesk/tickets/${incident.name}"` but `@click.prevent` navigates to `/tickets/${incident.name}` (no `/helpdesk` prefix). The `href` and the `router.push` path are inconsistent. Middle-click (open in new tab) will use the `href` with `/helpdesk` prefix (correct for browser URL), but `router.push` uses the route path without the base. This works because the router has `createWebHistory("/helpdesk/")` as base, but it's confusing and fragile.

### F-11: `_send_major_incident_notifications` uses non-standard Socket.IO room naming

**Severity**: P2
**Files**: `helpdesk/api/incident.py:356-365`
**Description**: `frappe.publish_realtime` sends to room `f"agent:{email}"` but there's no evidence this room naming convention exists in the helpdesk frontend. The standard Frappe realtime rooms are `user:{email}` (for the user's personal room). Unless the frontend explicitly subscribes to `agent:` rooms, these Socket.IO events will never be received. The frontend also has no listener for the `major_incident_declared` event.

---

## P3 - Low / Cosmetic / Minor

### F-12: Email template has no unsubscribe link or footer

**Severity**: P3
**Files**: `helpdesk/templates/major_incident_alert.html`
**Description**: The major incident alert email template is a raw HTML email with no unsubscribe mechanism, no footer with sender identity, and no link back to helpdesk settings. While this is an internal notification, email best practices (and some jurisdictions' regulations) expect an unsubscribe or manage-preferences link.

### F-13: `major_incident_contacts` field is free-text comma-separated - no validation

**Severity**: P3
**Files**: `helpdesk/helpdesk/doctype/hd_settings/hd_settings.json:174`, `helpdesk/api/incident.py:325`
**Description**: The `major_incident_contacts` field is a `Small Text` allowing free-form input. The code splits by comma and newline, strips whitespace, but does no email format validation. Invalid entries will cause silent `sendmail` failures in the background job. A `Table` child DocType with Link-to-User fields or at minimum regex validation would be more robust.

---

## Summary

| Severity | Count | Key Themes |
|----------|-------|------------|
| P0       | 2     | Missing frontend fields, test data pollution |
| P1       | 4     | Missing validation, no ITIL gating, unsafe toggle API, N+1 queries |
| P2       | 5     | Stale timer, fragile data reads, wrong Socket.IO rooms |
| P3       | 2     | Email standards, field validation |

**Recommendation**: Do not ship until P0 and P1 items are resolved. F-01 (missing post-incident review UI) is an acceptance criteria failure. F-02 (test pollution) needs immediate DB cleanup and test refactoring. F-04 (ITIL mode gating) contradicts the feature flag architecture from Story 1.1.
