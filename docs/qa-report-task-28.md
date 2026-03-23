# QA Report: Story 2.3 — SLA-Based Automation Triggers (Task #28)

**QA Task**: #220
**Reviewed by**: Adversarial QA (Opus)
**Date**: 2026-03-23
**QA Depth**: 1/1 (max depth)

---

## Test Environment

- **URL**: http://helpdesk.localhost:8004
- **Login**: Administrator / Velocity@2026!
- **Backend tests**: 13/13 passing via `bench run-tests`
- **Playwright MCP**: Not available; API-level and code-level verification used

---

## Acceptance Criteria Results

### AC1: SLA warning thresholds fire sla_warning trigger — PASS (with caveats)

**Evidence**: Test `test_sla_warning_rule_fires_on_threshold` passes. `_fire_warning` correctly invokes `evaluate(ticket_doc, "sla_warning")` which matches rules with `trigger_type="sla_warning"`. Thresholds [30, 15, 5] are configurable via HD Settings.

**Caveat**: See Issue #1 — `check_sla_breaches` (the actual cron entry point) is never tested end-to-end.

### AC2: SLA breach fires sla_breached trigger — PASS

**Evidence**: Test `test_sla_breached_rule_fires_on_breach` passes. `_fire_breached` correctly invokes `evaluate(ticket_doc, "sla_breached")`.

### AC3: Rule with trigger sla_warning and action assign_to_team reassigns ticket — PASS

**Evidence**: Test `test_sla_warning_assign_to_team_action` passes. A rule with `trigger_type="sla_warning"` and `actions=[{"type": "assign_to_team", "value": "Escalation"}]` correctly sets `agent_group` on the ticket.

### AC4: Assigned agent receives in-app notification on sla_warning — FAIL (P1)

**Evidence**: `notify_agent_sla_warning` calls `frappe.publish_realtime(event="sla_warning", room=f"agent:{email}")`. However:
1. **No frontend Socket.IO listener exists** for the `sla_warning` event anywhere in `desk/src/`. Grep across all `.vue` and `.ts` files confirms zero subscribers.
2. **No HD Notification record is created** — the notification is ephemeral Socket.IO only, with no persistence. If the agent's browser tab is closed, the notification is permanently lost.
3. **The `agent:{email}` room pattern is not established** — no code in the frontend joins this room. Frappe's default rooms are `user:{email}` (for `frappe.publish_realtime`). The custom `agent:{email}` room is never subscribed to.

The AC says "receives in-app notification" but the agent will never actually see anything. The backend publishes to a room nobody listens on, and even if they did, there's no UI component to display it.

---

## Adversarial Findings

### Issue 1 — P1: `check_sla_breaches` entry point is never tested end-to-end

- **Severity**: P1
- **File**: `helpdesk/helpdesk/doctype/hd_service_level_agreement/test_sla_monitor_automation.py`
- **Description**: The function `check_sla_breaches` is imported (line 25) but never called in any test. All 13 tests call the private helpers `_fire_warning` and `_fire_breached` directly, bypassing the actual cron entry point logic: the SQL query in `_get_at_risk_tickets()`, the threshold comparison loop, the `_assign` field extraction, and the `minutes_remaining` calculation. A bug in any of these would go undetected.
- **Impact**: The DB query, status filtering, datetime arithmetic, and `_assign` extraction are all untested in integration.

### Issue 2 — P1: SLA warning notification is invisible to agents (dead letter)

- **Severity**: P1
- **File**: `helpdesk/helpdesk/automation/notifications.py` (line 55-58) and `desk/src/` (missing)
- **Description**: `frappe.publish_realtime(event="sla_warning", room=f"agent:{agent_email}")` publishes to a Socket.IO room that no frontend code subscribes to. Grep of entire `desk/src/` confirms zero `.on("sla_warning"` handlers. The standard Frappe room pattern is `user:{email}`, not `agent:{email}`. Even if the room name were corrected, there's no toast/badge/notification UI component to display the warning.
- **Impact**: AC4 ("Assigned agent receives in-app notification on sla_warning") is functionally unmet. The backend sends into the void.

### Issue 3 — P1: `clear_warning_dedup` is dead code in production

- **Severity**: P1
- **File**: `helpdesk/helpdesk/doctype/hd_service_level_agreement/sla_monitor.py` (line 188-201)
- **Description**: `clear_warning_dedup()` is defined for resetting dedup keys when a ticket's SLA is recalculated (reopen, SLA policy change). However, it is **never called from production code** — only from test helpers. Grep confirms it appears in exactly 2 files: `sla_monitor.py` (definition) and `test_sla_monitor_automation.py` (test calls). There is no hook in `hd_ticket.py` on status change or SLA recalculation that calls it.
- **Impact**: Once an SLA warning fires, if the ticket's SLA is reset (e.g., reopened with a new deadline), warnings will NOT fire again for up to 24 hours (Redis TTL). This silently defeats the entire warning mechanism for re-opened tickets.

### Issue 4 — P2: All warning thresholds fire simultaneously on first cron run

- **File**: `helpdesk/helpdesk/doctype/hd_service_level_agreement/sla_monitor.py` (lines 63-66)
- **Description**: The threshold loop checks `if minutes_remaining <= threshold` for each threshold. If a ticket has 4 minutes remaining and thresholds are [30, 15, 5], all three thresholds fire in the same cron run. The agent (if notifications worked) would receive 3 simultaneous warnings. Dedup prevents re-fire, so subsequent cron runs are fine, but the initial blast is noisy and defeats the purpose of graduated warnings.
- **Expected**: Only the most appropriate threshold should fire per cron run (e.g., 5-min warning when 4 min remain), not retroactively fire 30 and 15 as well.

### Issue 5 — P2: No notification on `sla_breached`

- **File**: `helpdesk/helpdesk/doctype/hd_service_level_agreement/sla_monitor.py` (lines 118-134)
- **Description**: `_fire_breached` only calls the automation engine. It does NOT call `notify_agent_sla_warning` or any notification function. When an SLA actually breaches, the assigned agent gets no direct notification — only automation rules fire. The AC only requires notification on `sla_warning`, but from a product perspective, an agent should be MORE urgently notified on breach than on warning.

### Issue 6 — P2: 24-hour Redis TTL may expire before SLA cycle completes

- **File**: `helpdesk/helpdesk/doctype/hd_service_level_agreement/sla_monitor.py` (line 27)
- **Description**: `_DEDUP_TTL_SECONDS = 86400` (24h). If an SLA deadline is more than 24 hours away (which is common for low-priority tickets with 48h or 72h SLAs), the dedup key expires before the SLA cycle ends. When the ticket eventually approaches breach, thresholds fire a second time because the dedup key has already been purged.
- **Impact**: False-positive re-warnings for long SLA cycles.

### Issue 7 — P2: `sla_warning_thresholds` field misplaced in HD Settings UI

- **File**: `helpdesk/helpdesk/doctype/hd_settings/hd_settings.json` (field_order, line 16)
- **Description**: The `sla_warning_thresholds` JSON field is placed in the `feature_flags_section` alongside boolean toggles (`chat_enabled`, `csat_enabled`, `automation_enabled`). A JSON configuration field for minute thresholds is not a feature flag. It should be in its own SLA Configuration section or under the existing SLA-related settings area.

### Issue 8 — P2: No audit trail for SLA warnings/breaches

- **File**: `helpdesk/helpdesk/doctype/hd_service_level_agreement/sla_monitor.py`
- **Description**: When the SLA monitor fires warnings or breaches, no persistent record is created. No `HD Ticket Comment` (timeline entry), no `HD Notification` record, no `Communication` log. The only traces are ephemeral Redis dedup keys (24h TTL) and Error Log entries (only on failure). There is no way for an administrator to verify that SLA warnings were sent, audit when they fired, or troubleshoot missed warnings.

### Issue 9 — P3: `_get_at_risk_tickets` query fetches `_assign` but not `assigned_to`

- **File**: `helpdesk/helpdesk/doctype/hd_service_level_agreement/sla_monitor.py` (lines 169-185, 47)
- **Description**: The query only selects `QBTicket._assign`. In `check_sla_breaches`, line 47 does `assigned_to = ticket_row.get("_assign") or ticket_row.get("assigned_to") or ""`. The `ticket_row.get("assigned_to")` fallback will always return `None` because that field was never selected in the query. This is dead code that creates a false sense of robustness. If `_assign` is empty/null, the fallback silently fails.

### Issue 10 — P3: No input validation on `sla_warning_thresholds` JSON field

- **File**: `helpdesk/helpdesk/doctype/hd_settings/hd_settings.json` and `sla_monitor.py`
- **Description**: The `sla_warning_thresholds` field is a freeform JSON field with no server-side `validate` hook. An admin could enter `"not json"`, `[-5, 0]`, `[9999]`, or `[]`. While `_get_warning_thresholds` has a graceful fallback to defaults, negative or zero thresholds would silently cause unexpected behavior (matching already-breached tickets or never matching). No error feedback is given to the admin.

### Issue 11 — P3: No `__init__.py` exports for new module functions

- **File**: `helpdesk/helpdesk/automation/__init__.py`
- **Description**: The new `notifications.py` module is not exported from the automation package `__init__.py`. While Python doesn't require this for direct imports, it means `from helpdesk.helpdesk.automation import notify_agent_sla_warning` won't work. This is a minor code organization issue.

### Issue 12 — P3: Test tearDown calls commit then rollback (fragile pattern)

- **File**: `helpdesk/helpdesk/doctype/hd_service_level_agreement/test_sla_monitor_automation.py` (lines 74-77)
- **Description**: `tearDown` calls `frappe.db.commit()` on line 74 after deleting rules, then `frappe.db.rollback()` on line 77. The rollback is a no-op after commit, so any test data created between setUp and tearDown that wasn't explicitly deleted (e.g., tickets, teams, the test agent) will persist. The test creates `sla.monitor.agent@test.com` in every setUp but never deletes it in tearDown, causing potential test pollution.

---

## Summary

| Severity | Count | Description |
|----------|-------|-------------|
| P0       | 0     | — |
| P1       | 3     | No e2e test for cron entry point; notification is a dead letter; `clear_warning_dedup` is dead code |
| P2       | 4     | Simultaneous threshold blast; no breach notification; TTL too short; field misplacement; no audit trail |
| P3       | 4     | Dead fallback code; no JSON validation; no __init__ exports; fragile tearDown |

### Verdict

The backend automation plumbing (trigger types, dedup, engine integration) is solid and well-tested at the unit level. However, **the notification delivery chain is completely broken end-to-end** — the backend publishes to a Socket.IO room that nothing subscribes to, using a non-standard room name, with no frontend handler. AC4 is functionally unmet. Additionally, `clear_warning_dedup` being dead code in production means SLA re-calculations won't re-fire warnings, which is a significant operational gap.

---

## Console Errors

No console errors detected via API testing. Frontend Socket.IO behavior could not be verified (Playwright unavailable).

---

## Screenshots

Playwright MCP was not available for this QA session. All verification was done via:
- Backend test execution (13/13 pass)
- API calls to verify HD Settings configuration
- Code-level grep and analysis of Socket.IO room subscriptions
