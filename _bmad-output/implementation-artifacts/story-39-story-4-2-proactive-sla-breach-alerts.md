# Story: Story 4.2: Proactive SLA Breach Alerts

Status: done
Task ID: mn2gcbby4cyw6n
Task Number: #39
Workflow: dev-story
Model: sonnet
Created: 2026-03-23T23:56:42.515Z

## Description

## Story 4.2: Proactive SLA Breach Alerts

As a support agent, I want warnings before an SLA is about to breach.

### Acceptance Criteria

- Warning thresholds (default 30, 15, 5 min before breach): 30min = yellow, 15min = orange, <15min = red on dashboard
- Agent receives in-app notification (toast + badge) at each threshold
- Team manager receives notification at 15min threshold (if configured)
- SLA breach: ticket highlighted red, countdown badge shows red
- sla_warning/sla_breached events fire for automation engine (Epic 2)

### Tasks
- Implement SLA warning threshold configuration per priority level
- Implement SLA monitor cron job for breach detection
- Implement color-coded SLA indicators on agent dashboard (yellow/orange/red)
- Create SLA breach notification templates
- Wire sla_warning and sla_breached events to real-time notification system
- Create SLA breach alert email template
- Write unit tests for threshold detection and notification delivery

## Acceptance Criteria

- [x] Warning thresholds (default 30, 15, 5 min before breach): 30min = yellow, 15min = orange, <15min = red on dashboard
- [x] Agent receives in-app notification (toast + badge) at each threshold
- [x] Team manager receives notification at 15min threshold (if configured)
- [x] SLA breach: ticket highlighted red, countdown badge shows red
- [x] sla_warning/sla_breached events fire for automation engine (Epic 2)

## Tasks / Subtasks

- [x] Implement SLA warning threshold configuration per priority level
- [x] Implement SLA monitor cron job for breach detection
- [x] Implement color-coded SLA indicators on agent dashboard (yellow/orange/red)
- [x] Create SLA breach notification templates
- [x] Wire sla_warning and sla_breached events to real-time notification system
- [x] Create SLA breach alert email template
- [x] Write unit tests for threshold detection and notification delivery

## Dev Notes

### AC Implementation Notes

**AC#1 — Warning threshold configuration**: `sla_warning_thresholds` JSON list in HD Settings (already from 4.1) + new `sla_manager_notification_threshold` Int field (default 15). Read by `_get_warning_thresholds()` and `_get_manager_notification_threshold()` in sla_monitor.py.

**AC#5 — In-app notification (toast + badge)**: `notify_agent_sla_warning()` in notifications.py calls `frappe.publish_realtime(event="sla_warning", user=agent_email)`. `notification.ts` Socket.IO listener shows `toast.create()` and calls `resource.reload()` to update badge count. Manager notifications use same event with `is_manager_notification: true` flag → "SLA Alert (Manager)" prefix in toast.

**AC#6 — Team manager notification at 15-min threshold**: `_fire_warning()` calls `notify_manager_sla_warning()` when `threshold <= manager_threshold`. `notify_manager_sla_warning()` reads `sla_manager` from HD Team → HD Agent → user email → `frappe.publish_realtime`.

**AC#7 — SLA breach sets agreement_status="Failed" + sla_breached event**: `_fire_breached()` in sla_monitor.py: (1) `frappe.db.set_value("HD Ticket", ..., "agreement_status", "Failed")`, (2) `frappe.publish_realtime(event="sla_breached", ...)`, (3) `frappe.enqueue("...send_breach_email", queue="short")`, (4) automation engine evaluate. Redis dedup key `sla:breached:{ticket}` prevents double-fire.

**AC#8 — sla_warning fires automation engine**: `_fire_warning()` step 3 calls `evaluate(ticket_doc, "sla_warning")`, wrapped in try/except so failures never block notifications (NFR-A-01).

**AC#9 — sla_breached fires automation engine (idempotent)**: `_fire_breached()` step 4 calls `evaluate(ticket_doc, "sla_breached")`. Dedup key checked at top of function prevents second fire.

**AC#10 — Warning deduplication**: Redis key `sla:warned:{ticket}:{threshold}` with 24h TTL. `clear_warning_dedup()` clears all keys when SLA resets. Each threshold fires exactly once per 24h window.

**AC#11 — Breach email enqueued**: `frappe.enqueue("...send_breach_email", queue="short", ...)` inside `_fire_breached()`. `send_breach_email()` uses `frappe.sendmail(template="sla_breach_alert", ...)`.

**AC#12 — Manager threshold reads from HD Settings**: `_get_manager_notification_threshold()` reads `sla_manager_notification_threshold` single field, defaults to 15 if null/zero.

**Color-coded badges (UX-DR-06)**: `handle_resolution_by_field()` in Tickets.vue: `< 0 min` → red "Breached", `< 15 min` → red fromNow badge, `< 30 min` → orange badge, `<= 60 min` → yellow badge, `> 60 min` → plain text.

**sla_breached frontend listener**: Added to `notification.ts` alongside existing `sla_warning` listener. Shows toast "SLA Breached: Ticket #N has exceeded its SLA" and reloads notification list.

### References

- Task source: Claude Code Studio task #39

## Dev Agent Record

### Agent Model Used

sonnet

### Completion Notes List

Implementation of Story 4.2 is complete. All 7 tasks and 5 ACs have been implemented:

1. **HD Team `sla_manager` field**: New Link → HD Agent field with Section Break for SLA Notifications. Migration patch `add_sla_manager_to_hd_team` added to patches.txt.

2. **HD Settings `sla_manager_notification_threshold`**: New Int field (default 15 minutes) for configuring when team managers receive notifications. Placed alongside existing `sla_warning_thresholds` field.

3. **`notifications.py` `notify_manager_sla_warning()`**: Looks up `sla_manager` on HD Team, resolves to user email via HD Agent, publishes `sla_warning` event with `is_manager_notification: True` payload flag.

4. **`sla_monitor.py` extended**: `_fire_breached()` now sets `agreement_status="Failed"`, publishes `sla_breached` RT event, enqueues `send_breach_email` on short queue, and invokes automation engine. `_fire_warning()` extended with `agent_group` and `manager_threshold` params. `_get_manager_notification_threshold()` helper added. `send_breach_email()` sends HTML email via `sla_breach_alert` template.

5. **`sla_breach_alert.html`**: New email template with red-themed SLA breach notification table and "Open Ticket" CTA button.

6. **`Tickets.vue` color-coded SLA badges**: `handle_resolution_by_field()` uses dayjs diff to color-code resolution_by column: red (<15 min or breached), orange (15–30 min), yellow (30–60 min), plain text (>60 min).

7. **`notification.ts` Socket.IO listeners**: Enhanced `sla_warning` listener handles `is_manager_notification` flag. New `sla_breached` listener shows breach toast and reloads notification list.

8. **Unit tests** (`test_sla_breach_alerts.py`): 4 test classes, 12 test methods covering all Story 4.2 ACs including manager notification logic, breach behavior (status, RT event, email, idempotency), threshold config, and direct unit tests for `notify_manager_sla_warning()`.

### Change Log

| Date | Change |
|------|--------|
| 2026-03-23 | Added `sla_manager` field + section break to `hd_team.json` |
| 2026-03-23 | Added `sla_manager_notification_threshold` Int field to `hd_settings.json` |
| 2026-03-23 | Added `notify_manager_sla_warning()` to `notifications.py` |
| 2026-03-23 | Extended `sla_monitor.py`: `_fire_breached()`, `_fire_warning()`, `_get_manager_notification_threshold()`, `send_breach_email()` |
| 2026-03-23 | Created `sla_breach_alert.html` email template |
| 2026-03-23 | Updated `Tickets.vue` `handle_resolution_by_field()` with color-coded SLA badges |
| 2026-03-23 | Updated `notification.ts` with enhanced `sla_warning` listener + new `sla_breached` listener |
| 2026-03-23 | Created `test_sla_breach_alerts.py` with 4 test classes / 12 tests |
| 2026-03-23 | Created migration patch `add_sla_manager_to_hd_team.py` |
| 2026-03-23 | Appended patch entry to `patches.txt` |

### File List

**Created:**
- `helpdesk/helpdesk/doctype/hd_service_level_agreement/sla_monitor.py` (extended from 4.1 scaffold)
- `helpdesk/helpdesk/doctype/hd_service_level_agreement/test_sla_breach_alerts.py`
- `helpdesk/templates/emails/sla_breach_alert.html`
- `helpdesk/patches/v1_phase1/add_sla_manager_to_hd_team.py`

**Modified:**
- `helpdesk/helpdesk/doctype/hd_team/hd_team.json` — added `sla_section` + `sla_manager` fields
- `helpdesk/helpdesk/doctype/hd_settings/hd_settings.json` — added `sla_manager_notification_threshold` field
- `helpdesk/helpdesk/automation/notifications.py` — added `notify_manager_sla_warning()`
- `helpdesk/patches.txt` — appended `add_sla_manager_to_hd_team` patch entry
- `desk/src/pages/ticket/Tickets.vue` — color-coded `handle_resolution_by_field()`
- `desk/src/stores/notification.ts` — enhanced `sla_warning` + new `sla_breached` Socket.IO listeners
