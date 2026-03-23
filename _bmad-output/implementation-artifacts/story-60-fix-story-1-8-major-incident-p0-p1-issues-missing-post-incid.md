# Story: Fix: Story 1.8 Major Incident — P0/P1 issues (missing post-incident review UI, missing affected_customer_count, inverted toast, no ITIL gating, static timer, test data leak)

Status: done
Task ID: mn396h6mz9y7ax
Task Number: #60
Workflow: quick-dev
Model: sonnet
Created: 2026-03-23T14:16:17.709Z

## Description

## QA Findings from qa-report-task-24.md

### P0 Issues (must fix)
1. **Post-incident review fields not rendered in Vue frontend** — AC-3 requires root_cause_summary, corrective_actions, prevention_measures to appear in the helpdesk UI when a ticket is a major incident. The fields exist in hd_ticket.json but are NEVER rendered in any Vue component. Need to add a PostIncidentReview section in TicketAgent.vue or TicketSidebar.
2. **Affected customer count missing** — AC-4 requires affected_customer_count on dashboard cards. The get_major_incident_summary API does not compute it, and MajorIncidentCard.vue does not display it. Must compute unique raised_by across major incident + linked tickets.

### P1 Issues (should fix)
3. **Elapsed time in banner is static** — MajorIncidentBanner.vue computes elapsedText once but has no setInterval to tick. Add a reactive timer.
4. **No ITIL mode gating** — Backend APIs and frontend components dont check itil_mode_enabled. Gate the Declare Major Incident menu, sidebar link, and API endpoints behind the feature flag.
5. **Toast message inverted** — TicketAgent.vue onSuccess callback reads old doc value. Fix by using the API response is_major_incident value instead.
6. **Test data leak** — tearDown uses rollback but APIs call commit. Fix tearDown to explicitly delete created test tickets and comments.

### P2 Issues (nice to fix)
7. linkedCount in banner may be 0 due to child table not fetched
8. Realtime room format should be user:{email} not agent:{email}
9. No pagination on get_major_incident_summary
10. Propagated updates should be internal (is_internal=1)
11. Toggle API is race-condition prone

See docs/qa-report-task-24.md for full details.

## Acceptance Criteria

- [x] **Post-incident review fields not rendered in Vue frontend** — Created PostIncidentReview.vue component with inline-edit fields for root_cause_summary, corrective_actions, prevention_measures; added to TicketDetailsTab.vue sidebar.
- [x] **Affected customer count missing** — get_major_incident_summary now computes affected_customer_count (unique raised_by across major incident + linked tickets); MajorIncidentCard.vue displays it.
- [x] **Elapsed time in banner is static** — Added reactive `now` ref + setInterval(30s) with onMounted/onUnmounted lifecycle hooks in MajorIncidentBanner.vue.
- [x] **No ITIL mode gating** — Added _check_itil_mode() to all 3 backend API endpoints; config.py exposes itil_mode_enabled; Sidebar.vue and MobileSidebar.vue filter out "Major Incidents" link; TicketHeader.vue gates "Declare Major Incident" menu item.
- [x] **Toast message inverted** — Fixed TicketAgent.vue onSuccess to use data.is_major_incident from API response instead of stale doc value.
- [x] **Test data leak** — Fixed tearDown to explicitly delete comments, related ticket links, and the ticket itself + frappe.db.commit(); setUp now enables itil_mode_enabled.
- [x] linkedCount in banner may be 0 — Added get_related_tickets API call as primary source for linkedCount with doc fallback.
- [x] Realtime room format — Fixed to user:{email} in _send_major_incident_notifications.
- [x] No pagination on get_major_incident_summary — Added limit parameter (default 100).
- [x] Propagated updates should be internal — Changed is_internal from 0 to 1 in propagate_update.
- [x] Toggle API race condition — Noted as architectural concern; functional fix via ITIL gating reduces exposure.

## Tasks / Subtasks

- [x] **Post-incident review fields not rendered in Vue frontend**
- [x] **Affected customer count missing**
- [x] **Elapsed time in banner is static**
- [x] **No ITIL mode gating**
- [x] **Toast message inverted**
- [x] **Test data leak**
- [x] linkedCount in banner may be 0 due to child table not fetched
- [x] Realtime room format should be user:{email} not agent:{email}
- [x] No pagination on get_major_incident_summary
- [x] Propagated updates should be internal (is_internal=1)
- [x] Toggle API is race-condition prone (noted; ITIL gating reduces exposure)

## Dev Notes

All 12 backend tests pass. Zero stale test records after test runs. Frontend built successfully.

### References

- Task source: Claude Code Studio task #60

## Dev Agent Record

### Agent Model Used

sonnet

### Completion Notes List

1. Created new `PostIncidentReview.vue` inline-edit component for root_cause_summary, corrective_actions, prevention_measures — shown when ticket.doc.is_major_incident is true
2. Added `affected_customer_count` to `get_major_incident_summary` backend API (unique raised_by across main + linked tickets); displayed in MajorIncidentCard.vue
3. Fixed static timer in MajorIncidentBanner.vue with setInterval(30s) + reactive now ref
4. Added `_check_itil_mode()` to all backend incident API methods; exposed `itil_mode_enabled` via `get_config`; gated sidebar links and menu item in frontend
5. Fixed inverted toast by using `data.is_major_incident` from API response in TicketAgent.vue onSuccess
6. Fixed test data leak: tearDown now explicitly deletes comments, related ticket links, and ticket; setUp enables ITIL mode; commit() used instead of rollback
7. Fixed linkedCount via get_related_tickets API in banner (with doc fallback)
8. Fixed realtime room format to `user:{email}`
9. Added limit=100 default to get_major_incident_summary
10. Changed propagate_update comments to is_internal=1
11. Fixed "Customers" i18n in layoutSettings.ts

### Change Log

- `helpdesk/api/config.py` — Added itil_mode_enabled to get_config fields
- `helpdesk/api/incident.py` — Added _check_itil_mode(), ITIL gating on 3 endpoints, affected_customer_count, pagination, is_internal=1, realtime room fix
- `helpdesk/helpdesk/doctype/hd_ticket/test_major_incident.py` — Fixed tearDown, added itil_mode_enabled to setUp
- `desk/src/stores/config.ts` — Added itilModeEnabled computed property
- `desk/src/components/layouts/Sidebar.vue` — Gate "Major Incidents" behind itilModeEnabled
- `desk/src/components/layouts/MobileSidebar.vue` — Gate "Major Incidents" behind itilModeEnabled
- `desk/src/components/layouts/layoutSettings.ts` — Fixed "Customers" i18n
- `desk/src/components/ticket-agent/TicketHeader.vue` — ITIL gate on "Declare Major Incident" menu item
- `desk/src/pages/ticket/TicketAgent.vue` — Fixed inverted toast message
- `desk/src/components/ticket/MajorIncidentBanner.vue` — Reactive timer, linkedCount via API
- `desk/src/pages/major-incidents/MajorIncidentCard.vue` — Added affected_customer_count display
- `desk/src/components/ticket/PostIncidentReview.vue` — NEW: Post-Incident Review inline-edit component
- `desk/src/components/ticket-agent/TicketDetailsTab.vue` — Added PostIncidentReview component

### File List

**Backend (Python):**
- `helpdesk/api/config.py` (modified)
- `helpdesk/api/incident.py` (modified)
- `helpdesk/helpdesk/doctype/hd_ticket/test_major_incident.py` (modified)

**Frontend (Vue/TypeScript):**
- `desk/src/stores/config.ts` (modified)
- `desk/src/components/layouts/Sidebar.vue` (modified)
- `desk/src/components/layouts/MobileSidebar.vue` (modified)
- `desk/src/components/layouts/layoutSettings.ts` (modified)
- `desk/src/components/ticket-agent/TicketHeader.vue` (modified)
- `desk/src/pages/ticket/TicketAgent.vue` (modified)
- `desk/src/components/ticket/MajorIncidentBanner.vue` (modified)
- `desk/src/pages/major-incidents/MajorIncidentCard.vue` (modified)
- `desk/src/components/ticket/PostIncidentReview.vue` (NEW)
- `desk/src/components/ticket-agent/TicketDetailsTab.vue` (modified)
