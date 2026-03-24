# QA Report: Story 4.2 — Proactive SLA Breach Alerts

**Task**: #39 (QA task #238)
**Date**: 2026-03-24
**Tester**: Claude QA Agent (Opus 4.6)
**QA Depth**: 1/1 (max depth)

## Summary

Story 4.2 implements proactive SLA breach alerts including warning thresholds, color-coded badges, manager notifications, breach email templates, and automation engine integration. **All 16 unit tests pass.** The backend implementation is solid and well-structured. Frontend files required syncing to the bench copy and rebuild (done during QA). No P0/P1 issues found.

## Acceptance Criteria Results

### AC#1: Warning thresholds (default 30, 15, 5 min before breach) with color coding
**PASS**

**Evidence:**
- `HD Settings.sla_warning_thresholds` field exists and defaults to `[30, 15, 5]`
- `_get_warning_thresholds()` reads from HD Settings, returns sorted descending `[30, 15, 5]`
- Verified via bench console: `Thresholds: [30, 15, 5]`
- Color-coded badges in `Tickets.vue` `handle_resolution_by_field()`:
  - `< 0 min` -> red "Breached" badge
  - `< 15 min` -> red fromNow badge
  - `15-30 min` -> orange fromNow badge
  - `30-60 min` -> yellow fromNow badge
  - `> 60 min` -> plain text
- All `theme` values (`red`, `orange`, `yellow`) are valid and used elsewhere in the codebase

### AC#2: Agent receives in-app notification (toast + badge) at each threshold
**PASS**

**Evidence:**
- `notify_agent_sla_warning()` in `notifications.py` publishes `sla_warning` event via `frappe.publish_realtime(user=agent_email)`
- `notification.ts` has `$socket.on("sla_warning", ...)` listener that:
  - Shows toast: `"SLA Warning: Ticket #X — Y min until breach"`
  - Calls `resource.reload()` to update badge count
- Manager notifications distinguished with `is_manager_notification` flag: prefix becomes `"SLA Alert (Manager)"`
- Unit tests confirm `publish_realtime` is called with correct `event` and `user` params

### AC#3: Team manager receives notification at 15min threshold (if configured)
**PASS**

**Evidence:**
- `HD Team.sla_manager` Link field exists (verified via bench meta inspection)
- `HD Settings.sla_manager_notification_threshold` Int field defaults to 15
- `_fire_warning()` calls `notify_manager_sla_warning()` only when `threshold == manager_threshold`
- `notify_manager_sla_warning()` looks up `sla_manager` on HD Team -> HD Agent -> user email
- 5 dedicated unit tests pass:
  - `test_manager_notified_at_15min_threshold` -- manager notified at 15min
  - `test_manager_not_notified_at_30min_threshold` -- no notification at 30min
  - `test_manager_not_notified_at_5min_threshold` -- no notification at 5min
  - `test_manager_notification_skipped_when_no_sla_manager` -- graceful skip
  - `test_manager_notification_skipped_when_no_agent_group` -- graceful skip

### AC#4: SLA breach: ticket highlighted red, countdown badge shows red
**PASS**

**Evidence:**
- `_fire_breached()` sets `agreement_status = "Failed"` on the ticket
- `Tickets.vue` shows red "Breached" badge when `minutesLeft < 0`
- Red badge also shown for `< 15 min` remaining
- `sla_breached` Socket.IO listener in `notification.ts` shows toast: `"SLA Breached: Ticket #X has exceeded its SLA"`
- Unit test `test_breach_sets_agreement_status_failed` confirms status update

### AC#5: sla_warning/sla_breached events fire for automation engine (Epic 2)
**PASS**

**Evidence:**
- Both `sla_warning` and `sla_breached` are registered in `triggers.py` (lines 21-22)
- `_fire_warning()` step 3: `evaluate(ticket_doc, "sla_warning")` wrapped in try/except
- `_fire_breached()` step 4: `evaluate(ticket_doc, "sla_breached")` wrapped in try/except
- Automation engine failures are logged but never block notification delivery (NFR-A-01)

## Additional Verification

### Cron Job Registration
**PASS** -- `hooks.py` line 45: `"*/5 * * * *": ["helpdesk...sla_monitor.check_sla_breaches", ...]`

### Email Template
**PASS** -- `sla_breach_alert.html` exists with proper HTML structure: red-themed breach notification with ticket details and "Open Ticket" CTA button.

### Breach Email Enqueuing
**PASS** -- `_fire_breached()` calls `frappe.enqueue(..., queue="short")` to send breach email. `send_breach_email()` uses `frappe.sendmail(template="sla_breach_alert", ...)`. Unit test confirms short queue usage.

### Deduplication (Redis)
**PASS** -- Redis keys `sla:warned:{ticket}:{threshold}` (24h TTL) prevent duplicate warnings. `sla:breached:{ticket}` prevents duplicate breach events. Unit test `test_breach_idempotency_no_double_fire` confirms second call is a no-op.

### Migration Patch
**PASS** -- `add_sla_manager_to_hd_team.py` patch exists and is listed in `patches.txt` (line 62). Migration ran successfully.

### Unit Tests
**PASS** -- All 16 tests pass (4 test classes):
- `TestManagerThresholdConfig` (3 tests)
- `TestNotifyManagerSLAWarning` (4 tests)
- `TestSLABreachBehavior` (4 tests)
- `TestSLAManagerNotification` (5 tests)

### Frontend Build
**PASS** -- `yarn build` completes successfully in 28s. No TypeScript or build errors.

## Issues Found

### P3: `clear_warning_dedup` not called from production code (PRE-EXISTING)
- **Severity**: P3 (pre-existing from Story 2.3 QA, not introduced by this story)
- **Description**: `clear_warning_dedup()` is defined in `sla_monitor.py:325` and used in tests, but never called from `hd_ticket.py` when a ticket is reopened or SLA is recalculated. This means if a ticket's SLA resets, the dedup keys remain and warnings won't re-fire.
- **Impact**: Low -- dedup keys have 24h TTL so they self-expire. Only affects tickets that are reopened within 24h of a previous warning.
- **Not a Story 4.2 regression** -- this was flagged in the Story 2.3 QA report (`docs/qa-report-task-28.md`).

### P3: Frontend files were not synced to bench copy
- **Severity**: P3 (process issue, fixed during QA)
- **Description**: `Tickets.vue` and `notification.ts` changes were in the dev copy but not synced to `/home/ubuntu/frappe-bench/apps/helpdesk/`. Synced and rebuilt during QA.
- **Status**: Fixed during QA session.

## Console Errors
None detected. The Frappe API endpoints return valid JSON. The frontend build completes without errors.

## Regression Check
- Tickets list page loads successfully (HTTP 200)
- Existing SLA fields (`sla_warning_thresholds`) still work correctly
- HD Team records accessible with new `sla_manager` field (nullable, no breakage)
- No schema errors after migration

## Verdict

**PASS** -- All 5 acceptance criteria are met. No P0 or P1 issues found. The implementation is well-structured with proper error handling, deduplication, and test coverage. No fix task required.
