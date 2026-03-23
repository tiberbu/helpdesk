# Story 4.2: Proactive SLA Breach Alerts

Status: ready-for-dev

## Story

As a support agent,
I want to receive warnings before an SLA is about to breach,
so that I can take action in time to prevent the breach and maintain service quality.

## Acceptance Criteria

1. **[Warning Threshold Configuration — Per Priority]** Given an administrator opens an HD Service Level Agreement record, when they configure warning thresholds, then they can set three threshold values (default: 30, 15, and 5 minutes before breach), and these thresholds can be configured independently per SLA (allowing different thresholds for different priority levels).

2. **[Color-Coded Dashboard — Yellow at 30-Minute Threshold]** Given a ticket's SLA has 30 or more minutes remaining until breach, when an agent views the agent dashboard ticket list, then the ticket row displays with no SLA warning color (neutral/normal state); when the remaining time drops below 30 minutes (but is above 15 minutes), the SLA countdown indicator turns yellow (UX-DR-06: >30 min = yellow zone).

3. **[Color-Coded Dashboard — Orange at 15-Minute Threshold]** Given a ticket's SLA has between 15 and 30 minutes remaining until breach, when an agent views the agent dashboard, then the SLA countdown badge on that ticket is highlighted orange; the orange state is visually distinct from yellow and draws higher urgency (UX-DR-06: 15–30 min = orange zone).

4. **[Color-Coded Dashboard — Red at Breach / <15 Minutes]** Given a ticket's SLA has less than 15 minutes remaining, or has already breached (resolution_by exceeded), when an agent views the agent dashboard, then the ticket row is highlighted red and the SLA countdown badge shows red; a breached ticket's badge shows elapsed time past breach as a negative countdown (UX-DR-06: <15 min and breach = red zone).

5. **[In-App Notification — Toast + Badge at Each Threshold]** Given a ticket is assigned to an agent and its SLA crosses a warning threshold (30, 15, or 5 minutes remaining), when the SLA monitor cron job detects the threshold crossing, then the assigned agent receives: (a) an in-app toast notification showing ticket ID, subject, and remaining time; and (b) a badge increment on the notification bell icon in the agent header (AR-07 room: `agent:{email}`).

6. **[Manager Notification at 15-Minute Threshold]** Given a team manager notification is configured on the HD Team record (`notify_manager_on_sla_warning: Check`, `manager: Link → HD Agent`), when a ticket assigned to that team crosses the 15-minute warning threshold, then the team manager receives an in-app notification (toast + badge) indicating which ticket is at risk and that 15 minutes remain; the manager notification is only sent at the 15-minute threshold (not at 30 or 5 minutes).

7. **[SLA Breach — Ticket Highlighted Red on Dashboard]** Given a ticket's `resolution_by` timestamp has been exceeded (breach occurred), when the SLA monitor detects this and fires the `sla_breached` event, then: (a) the ticket's `agreement_status` is updated to `"Failed"` in the database; (b) the ticket row on the agent dashboard is highlighted red; (c) the SLA countdown badge on the ticket list shows red with elapsed-time-past-breach; (d) a `sla_breached` real-time event is published to the assigned agent's room.

8. **[sla_warning Event — Automation Engine Integration]** Given the SLA monitor cron job fires a warning event for a ticket, when the `sla_warning` event is published via `frappe.realtime.publish`, then the automation engine (Epic 2) also evaluates all enabled HD Automation Rules with trigger type `sla_warning` against the ticket; if matching rules exist, their actions execute (e.g., reassign to Escalation team, send email); this integration is via a direct Python call from `sla_monitor.py` to the automation engine, not via the real-time layer.

9. **[sla_breached Event — Automation Engine Integration]** Given an SLA breach is detected by the SLA monitor, when `agreement_status` is set to `"Failed"`, then the automation engine evaluates all enabled HD Automation Rules with trigger type `sla_breached` against the ticket; matching rules execute their configured actions; a duplicate breach trigger must not fire again for a ticket already marked `"Failed"` (idempotency guard).

10. **[SLA Monitor Cron — Every 5 Minutes, Warning State Deduplication]** Given the SLA monitor cron job runs every 5 minutes, when it processes a ticket, then it does NOT re-send a warning notification if that threshold has already been sent for this ticket's current SLA cycle; the system tracks sent warnings in Redis using key `sla_warned:{ticket_name}:{threshold_minutes}` with TTL equal to the SLA resolution window; only transitions that cross a new threshold trigger a notification.

11. **[SLA Breach Email Notification]** Given an SLA breach occurs, when the `sla_breached` event fires, then an email notification is enqueued using the `helpdesk/templates/emails/sla_breach_alert.html` template and sent to the assigned agent (and optionally to the team manager if configured); the email includes: ticket ID, subject, priority, customer name, time of breach, and a direct link to the ticket.

12. **[Unit Tests — Threshold Detection and Notification Delivery]** Given the unit test suite for SLA warning logic, when the tests run, then at minimum the following pass with 80%+ coverage (NFR-M-01): threshold crossing detection at 30 min, 15 min, and 5 min; deduplication guard (no double-send); breach detection and `agreement_status` update; manager notification at 15-min threshold only; automation engine invocation on `sla_warning` and `sla_breached`; idempotency guard for already-breached tickets.

## Tasks / Subtasks

- [ ] Task 1 — Add SLA Warning Threshold Configuration to HD Service Level Agreement (AC: #1)
  - [ ] 1.1 Open `helpdesk/helpdesk/doctype/hd_service_level_agreement/hd_service_level_agreement.json`
  - [ ] 1.2 Add `Section Break` field: "Warning Threshold Configuration"
  - [ ] 1.3 Add `Int` field `warning_threshold_1` (label: "First Warning (minutes before breach)", default: `30`)
  - [ ] 1.4 Add `Int` field `warning_threshold_2` (label: "Second Warning (minutes before breach)", default: `15`)
  - [ ] 1.5 Add `Int` field `warning_threshold_3` (label: "Third Warning (minutes before breach)", default: `5`)
  - [ ] 1.6 Add `Check` field `notify_manager_on_15min_warning` (label: "Notify Team Manager at 15-Minute Warning", default: `0`)
  - [ ] 1.7 Update `helpdesk/helpdesk/doctype/hd_service_level_agreement/hd_service_level_agreement.py` with a `validate()` enhancement to assert `warning_threshold_1 > warning_threshold_2 > warning_threshold_3 > 0` — raise `frappe.ValidationError` with a user-friendly message if not

- [ ] Task 2 — Add Manager Notification Config to HD Team (AC: #6)
  - [ ] 2.1 Open `helpdesk/helpdesk/doctype/hd_team/hd_team.json`
  - [ ] 2.2 Add `Section Break` field: "SLA Notifications"
  - [ ] 2.3 Add `Link` field `sla_manager` (label: "SLA Notification Manager", options: `HD Agent`) — the agent who receives the 15-minute team-level SLA warning
  - [ ] 2.4 Add `__init__.py` to `hd_team/` if not already present

- [ ] Task 3 — Extend `sla_monitor.py` with Warning Threshold Logic (AC: #5, #6, #7, #8, #9, #10)
  - [ ] 3.1 Open (or create if Story 4.1 not yet merged) `helpdesk/helpdesk/doctype/hd_service_level_agreement/sla_monitor.py`
  - [ ] 3.2 In `check_sla_breaches()`, after calculating `remaining_minutes` for each open ticket, implement threshold comparison:
        ```python
        thresholds = [sla.warning_threshold_1, sla.warning_threshold_2, sla.warning_threshold_3]
        for threshold in thresholds:
            redis_key = f"sla_warned:{ticket.name}:{threshold}"
            if remaining_minutes <= threshold and not frappe.cache().get_value(redis_key):
                _send_sla_warning(ticket, threshold, sla)
                frappe.cache().set_value(redis_key, 1, expires_in_sec=sla_window_seconds)
        ```
  - [ ] 3.3 Implement `_send_sla_warning(ticket, threshold_minutes, sla)`:
        a. Publish real-time event via `frappe.realtime.publish("sla_warning", {...}, room=f"agent:{ticket.assigned_to}")`
        b. If `threshold_minutes == sla.warning_threshold_2` (15-minute default) AND `sla.notify_manager_on_15min_warning` AND `team.sla_manager`: publish manager notification to `agent:{manager_email}` room
        c. Invoke automation engine: `from helpdesk.helpdesk.automation.engine import evaluate_rules; evaluate_rules("sla_warning", ticket.name)`
  - [ ] 3.4 Implement breach detection: if `remaining_minutes < 0` and `ticket.agreement_status != "Failed"`:
        a. `frappe.db.set_value("HD Ticket", ticket.name, "agreement_status", "Failed")`
        b. Publish `frappe.realtime.publish("sla_breached", {...}, room=f"agent:{ticket.assigned_to}")`
        c. Enqueue email notification: `frappe.enqueue("helpdesk.helpdesk.doctype.hd_service_level_agreement.sla_monitor.send_breach_email", queue="short", ticket_name=ticket.name)`
        d. Invoke automation engine: `evaluate_rules("sla_breached", ticket.name)`
        e. Idempotency guard: skip tickets already marked `"Failed"` (checked before step a)
  - [ ] 3.5 Add a Redis lock guard at the top of `check_sla_breaches()` to prevent overlapping cron runs:
        ```python
        lock_key = "sla_monitor_lock"
        if frappe.cache().get_value(lock_key):
            return
        frappe.cache().set_value(lock_key, 1, expires_in_sec=240)
        try:
            ...  # main logic
        finally:
            frappe.cache().delete_value(lock_key)
        ```

- [ ] Task 4 — Implement `send_breach_email()` and SLA Breach Email Template (AC: #11)
  - [ ] 4.1 In `sla_monitor.py`, implement `send_breach_email(ticket_name: str)` as a standalone function (not `@frappe.whitelist`):
        ```python
        def send_breach_email(ticket_name: str):
            ticket = frappe.get_doc("HD Ticket", ticket_name)
            context = {
                "ticket": ticket,
                "breach_time": frappe.utils.now_datetime(),
                "ticket_url": frappe.utils.get_url(f"/helpdesk/tickets/{ticket_name}"),
                "agent_name": frappe.db.get_value("HD Agent", ticket.assigned_to, "agent_name") or ticket.assigned_to,
            }
            frappe.sendmail(
                recipients=[ticket.assigned_to],
                subject=frappe._("SLA Breached: {0}").format(ticket.subject),
                template="sla_breach_alert",
                args=context,
                now=True
            )
        ```
  - [ ] 4.2 Create email template `helpdesk/helpdesk/templates/emails/sla_breach_alert.html` with:
        - Header: "⚠ SLA Breached" in red
        - Ticket ID (bold, linked), Subject, Priority badge, Customer name
        - Breach time (formatted human-readable)
        - Elapsed time past breach
        - CTA button: "Open Ticket" linking to `{{ ticket_url }}`
        - Plain text fallback block
  - [ ] 4.3 Verify the template path matches what Frappe's `frappe.sendmail(template=...)` expects — check existing templates (e.g., `csat_survey.html`) for the correct path format

- [ ] Task 5 — Frontend: SLA Color-Coded Indicators on Agent Dashboard (AC: #2, #3, #4)
  - [ ] 5.1 Locate the ticket list row component — likely `helpdesk/desk/src/components/ticket/` or `helpdesk/desk/src/pages/desk/` — find the component that renders the SLA countdown column
  - [ ] 5.2 Add a computed property `slaColorClass(remainingMinutes)` to the ticket list item component or composable:
        ```typescript
        function slaColorClass(remainingMinutes: number | null): string {
          if (remainingMinutes === null) return ''
          if (remainingMinutes < 0) return 'sla-breached'   // red
          if (remainingMinutes < 15) return 'sla-critical'  // red
          if (remainingMinutes < 30) return 'sla-warning'   // orange
          if (remainingMinutes <= 30) return 'sla-caution'  // yellow
          return ''
        }
        ```
        Note: per UX-DR-06: yellow = >30 min threshold crossed, orange = 15–30 min, red = <15 min or breached
  - [ ] 5.3 Apply the color class to the SLA countdown badge and optionally to the entire ticket row — use Tailwind classes:
        - `sla-caution`: `bg-yellow-100 text-yellow-800 border-yellow-300`
        - `sla-warning`: `bg-orange-100 text-orange-800 border-orange-300`
        - `sla-breached` / `sla-critical`: `bg-red-100 text-red-800 border-red-300` (row highlight: `bg-red-50`)
  - [ ] 5.4 Ensure the SLA remaining time updates in real-time on the dashboard — either via 1-minute polling or by listening to `sla_warning` and `sla_breached` Socket.IO events in the realtime composable to trigger a data refresh
  - [ ] 5.5 For breached tickets: display negative countdown as "+Xm Xm past breach" or "Breached Xm ago" in the SLA badge

- [ ] Task 6 — Frontend: Real-Time SLA Notification Handling (AC: #5, #6, #7)
  - [ ] 6.1 Open (or create) `helpdesk/desk/src/stores/notifications.ts`
  - [ ] 6.2 Add `sla_warning` and `sla_breached` event listeners to the Socket.IO setup (in `realtime.ts` composable or `notifications.ts` store):
        ```typescript
        frappe.realtime.on('sla_warning', (data) => {
          notificationStore.addSLAWarning(data)
          showToast({
            title: `SLA Warning: ${data.ticket_subject}`,
            message: `${data.remaining_minutes} minutes until breach`,
            type: data.remaining_minutes < 15 ? 'error' : 'warning',
            duration: 8000
          })
        })
        frappe.realtime.on('sla_breached', (data) => {
          notificationStore.addSLABreach(data)
          showToast({
            title: `SLA Breached: ${data.ticket_subject}`,
            message: `Ticket ${data.ticket_name} has breached SLA`,
            type: 'error',
            duration: 10000
          })
        })
        ```
  - [ ] 6.3 Implement `addSLAWarning` and `addSLABreach` actions in the notifications store that: increment the unread badge count on the notification bell; add a notification item to the notification list with ticket link; mark as type `"sla_warning"` or `"sla_breached"` for filtering

- [ ] Task 7 — Migration Patch for New SLA Warning Fields (AC: #1)
  - [ ] 7.1 Create `helpdesk/patches/v1_phase1/add_sla_warning_thresholds.py` with `execute()` function
  - [ ] 7.2 In `execute()`: for each existing `HD Service Level Agreement` record, if `warning_threshold_1` is not set (null or 0), populate defaults: `warning_threshold_1 = 30`, `warning_threshold_2 = 15`, `warning_threshold_3 = 5`, `notify_manager_on_15min_warning = 0`
  - [ ] 7.3 Register the patch in `helpdesk/patches.txt` after the Story 4.1 business hours patch

- [ ] Task 8 — Write Unit Tests for Threshold Detection and Notification Delivery (AC: #12)
  - [ ] 8.1 Create `helpdesk/helpdesk/doctype/hd_service_level_agreement/test_sla_monitor.py` using `frappe.tests.utils.FrappeTestCase` as base
  - [ ] 8.2 `test_30min_threshold_fires_warning` — mock a ticket with `remaining_minutes = 28`, assert `_send_sla_warning` is called with `threshold=30`, assert Redis key is set
  - [ ] 8.3 `test_15min_threshold_fires_warning_and_manager_notif` — mock ticket with `remaining_minutes = 12`, SLA with `notify_manager_on_15min_warning = 1` and `team.sla_manager` set; assert both agent and manager notifications published
  - [ ] 8.4 `test_5min_threshold_fires_warning` — mock ticket with `remaining_minutes = 3`, assert warning fires with `threshold=5`
  - [ ] 8.5 `test_deduplication_no_double_send` — mock Redis returning `1` for the warning key; assert `_send_sla_warning` is NOT called a second time for same ticket/threshold
  - [ ] 8.6 `test_breach_sets_agreement_status_failed` — mock ticket with `remaining_minutes = -5` and `agreement_status != "Failed"`; assert `frappe.db.set_value` called with `"Failed"`, assert `sla_breached` event published
  - [ ] 8.7 `test_breach_idempotency_skip_already_failed` — mock ticket with `agreement_status = "Failed"`; assert no DB write and no event published
  - [ ] 8.8 `test_automation_engine_invoked_on_sla_warning` — mock `evaluate_rules`; assert it is called with `"sla_warning"` and ticket name when threshold crosses
  - [ ] 8.9 `test_automation_engine_invoked_on_sla_breached` — assert `evaluate_rules("sla_breached", ticket_name)` is called on breach
  - [ ] 8.10 `test_manager_notification_only_at_15min` — assert manager notification is NOT sent for 30-min or 5-min thresholds even when `notify_manager_on_15min_warning = 1`
  - [ ] 8.11 `test_redis_lock_prevents_overlap` — mock Redis lock as already set; assert `check_sla_breaches()` returns early without processing

## Dev Notes

### Architecture Patterns

- **Story Dependency (Critical):** This story builds on top of Story 4.1's `sla_monitor.py` and business hours calculation. Story 4.1's `check_sla_breaches()` function must already exist at `helpdesk/helpdesk/doctype/hd_service_level_agreement/sla_monitor.py`. If Story 4.1 is not yet merged, check the story-4.1 file for the `check_sla_breaches()` scaffold and extend from there. Do NOT start from scratch — extend the existing implementation.

- **Scheduler Event (Already Registered by Story 4.1):** The `*/5 * * * *` cron entry in `hooks.py` pointing to `sla_monitor.check_sla_breaches` is already registered by Story 4.1. Do NOT add a duplicate entry. Simply extend `check_sla_breaches()` with warning threshold logic. [Source: architecture.md#ADR-12]

- **Real-time Event Publishing Pattern:**
  ```python
  # Agent-level SLA warning notification
  frappe.realtime.publish(
      "sla_warning",
      {
          "ticket_name": ticket.name,
          "ticket_subject": ticket.subject,
          "remaining_minutes": remaining_minutes,
          "threshold": threshold_minutes,
          "priority": ticket.priority,
          "assigned_to": ticket.assigned_to,
      },
      room=f"agent:{ticket.assigned_to}"
  )
  ```
  Room naming convention: `agent:{agent_email}` for per-agent notifications. [Source: architecture.md#Communication Patterns and ADR-07 AR-07]

- **Notification Store (`notifications.ts`):** The architecture specifies a new `notifications.ts` Pinia store at `helpdesk/desk/src/stores/notifications.ts` for managing SLA alerts, @mentions, and chat assignments. Create this file if it does not exist (Story 4.1 may not create it). The store should expose: `unreadCount: number`, `notifications: Notification[]`, `addSLAWarning(data)`, `addSLABreach(data)`, `markAllRead()`. [Source: architecture.md#Project Directory Structure, stores section]

- **Redis Warning Deduplication:** The deduplication key pattern is `sla_warned:{ticket_name}:{threshold}`. The TTL is set to the SLA's total resolution window in seconds so that the key auto-expires when the ticket's SLA is reset (e.g., after re-open). Use `frappe.cache().set_value(key, 1, expires_in_sec=ttl)` — never use raw Redis client. [Source: architecture.md#ADR-13 Integration Points, Redis caching pattern]

- **Redis Concurrency Lock Pattern (from Story 4.1):**
  ```python
  lock_key = "sla_monitor_lock"
  if frappe.cache().get_value(lock_key):
      return
  frappe.cache().set_value(lock_key, 1, expires_in_sec=240)  # 4-minute lock
  try:
      # processing logic
  finally:
      frappe.cache().delete_value(lock_key)
  ```
  This prevents overlapping cron runs if a previous invocation takes longer than 5 minutes. [Source: story-4.1#Constraints]

- **Automation Engine Integration:** The automation engine lives at `helpdesk/helpdesk/automation/engine.py` (Story 2.1). Import and call it directly from `sla_monitor.py`:
  ```python
  try:
      from helpdesk.helpdesk.automation.engine import evaluate_rules
      evaluate_rules(trigger_type="sla_warning", doc_name=ticket_name)
  except ImportError:
      # Automation engine not yet deployed (Story 2.1 not merged); skip silently
      pass
  except Exception:
      frappe.log_error("Automation engine error on SLA warning", frappe.get_traceback())
  ```
  Always wrap the call in try/except — automation failures must NEVER block the SLA notification pipeline (NFR-A-01: core ticketing unaffected by automation failures). [Source: architecture.md#NFR-A-01, ADR-14]

- **Background Job Queue for Email:** SLA breach emails are enqueued on the `short` queue (high priority, real-time delivery):
  ```python
  frappe.enqueue(
      "helpdesk.helpdesk.doctype.hd_service_level_agreement.sla_monitor.send_breach_email",
      queue="short",
      ticket_name=ticket.name,
  )
  ```
  [Source: architecture.md#ADR-12 Job Categories — `short` queue for SLA breach notifications]

- **Email Template Location:** The `sla_breach_alert.html` template lives at `helpdesk/helpdesk/templates/emails/sla_breach_alert.html`. This path is explicitly called out in the architecture's project directory structure. [Source: architecture.md#Project Directory Structure, templates section]

- **Frappe `frappe.sendmail` Pattern:**
  ```python
  frappe.sendmail(
      recipients=["agent@example.com"],
      subject=frappe._("SLA Breached: {0}").format(ticket.subject),
      template="sla_breach_alert",   # resolves to helpdesk/templates/emails/sla_breach_alert.html
      args={"ticket": ticket, "ticket_url": url, ...},
      now=True  # send immediately, not via queue
  )
  ```
  Use `frappe._("...")` for all user-facing strings (i18n). [Source: architecture.md#Enforcement Guidelines #7]

- **Frontend Color Classes — Tailwind:** Per UX-DR-06 the three warning zones are:
  - `> 30 minutes remaining` → yellow: `text-yellow-700 bg-yellow-50 ring-yellow-600/20`
  - `15–30 minutes remaining` → orange: `text-orange-700 bg-orange-50 ring-orange-600/20`
  - `< 15 minutes or breached` → red: `text-red-700 bg-red-50 ring-red-600/20` (row: `bg-red-50`)
  Use `frappe-ui Badge` component with `theme` prop if available, otherwise apply Tailwind classes directly.

- **Backward Compatibility:** Existing `agreement_status` values (`"Met"`, `"Failed"`, `"First Response Due"`) must not change. Only the `"Failed"` transition at breach time is relevant here. The `_send_sla_warning` function only publishes notifications — it does NOT change `agreement_status` (only breach does). [Source: architecture.md#ADR-01, AR-04]

- **Frappe ORM — No Raw SQL (AR-06 Enforcement):** All DB access via `frappe.db.get_all()`, `frappe.db.get_value()`, `frappe.db.set_value()`. For threshold config, use cached `frappe.db.get_value("HD Service Level Agreement", sla_name, ["warning_threshold_1", "warning_threshold_2", "warning_threshold_3"], as_dict=True)` with Redis TTL.

- **i18n:** All user-facing labels in DocType JSON and controller error messages must use `frappe._("...")` in Python and `__("...")` in JavaScript / TypeScript. Toast notification messages must use the `__()` utility from frappe-ui or Frappe's JS layer.

### Files to Create / Modify

| Action | Path | Notes |
|--------|------|-------|
| Modify | `helpdesk/helpdesk/doctype/hd_service_level_agreement/hd_service_level_agreement.json` | Add warning_threshold_1/2/3 and notify_manager_on_15min_warning fields (Task 1) |
| Modify | `helpdesk/helpdesk/doctype/hd_service_level_agreement/hd_service_level_agreement.py` | Add threshold validation in validate() (Task 1.7) |
| Modify | `helpdesk/helpdesk/doctype/hd_team/hd_team.json` | Add sla_manager Link field (Task 2) |
| Modify | `helpdesk/helpdesk/doctype/hd_service_level_agreement/sla_monitor.py` | Extend check_sla_breaches() with threshold logic, add _send_sla_warning(), breach handling, send_breach_email() (Tasks 3, 4) |
| Create | `helpdesk/helpdesk/templates/emails/sla_breach_alert.html` | SLA breach email template (Task 4.2) |
| Modify | `helpdesk/desk/src/components/ticket/<TicketListRow>.vue` | Add slaColorClass() computed and apply color classes (Task 5) — confirm exact filename by inspecting codebase |
| Modify | `helpdesk/desk/src/composables/realtime.ts` | Add sla_warning and sla_breached Socket.IO event listeners (Task 6) |
| Create | `helpdesk/desk/src/stores/notifications.ts` | New Pinia store for SLA alerts and notification badge (Task 6) |
| Create | `helpdesk/patches/v1_phase1/add_sla_warning_thresholds.py` | Migration patch for default thresholds (Task 7) |
| Modify | `helpdesk/patches.txt` | Register new migration patch (Task 7.3) |
| Create | `helpdesk/helpdesk/doctype/hd_service_level_agreement/test_sla_monitor.py` | Unit tests for threshold detection and notification (Task 8) |

### Testing Standards

- Minimum 80% unit test coverage on all new backend code (NFR-M-01).
- Use `frappe.tests.utils.FrappeTestCase` as the base class for all Python test cases.
- Mock `frappe.realtime.publish`, `frappe.cache()`, and `frappe.enqueue` in unit tests to avoid side effects.
- Mock the automation engine import (wrap in try/except as above) so tests do not require Story 2.1 to be merged.
- Test `send_breach_email` by mocking `frappe.sendmail` and asserting call arguments (recipients, template, subject).
- Run tests with: `bench --site <site> run-tests --module helpdesk.helpdesk.doctype.hd_service_level_agreement.test_sla_monitor`

### Constraints

- **Do NOT duplicate the `*/5 * * * *` scheduler event in `hooks.py`** — it is already registered by Story 4.1. Only modify `sla_monitor.py`.
- **Do NOT change `agreement_status` in `_send_sla_warning()`** — only set it to `"Failed"` during breach detection.
- **Automation engine errors must NEVER block SLA notifications** — always wrap `evaluate_rules()` in try/except (NFR-A-01).
- **Warning deduplication is mandatory** — without it, the agent receives 5+ duplicate toasts every 5 minutes for the same threshold, which is a critical UX failure.
- **The Redis lock from Story 4.1 must be preserved** — do not remove it while extending `check_sla_breaches()`.
- **All new DocType fields must be declared in DocType JSON** — not via Custom Fields (AR-04).
- **Patches must go in `helpdesk/patches/v1_phase1/`** — register in `patches.txt` after Story 4.1's patch (AR-05).

### Project Structure Notes

- **`sla_monitor.py` ownership:** This file is owned by Story 4.1 for the cron infrastructure and breach detection scaffold. Story 4.2 extends it with warning notifications, email, and automation integration. Coordinate with Story 4.1 completion before merging this story to avoid merge conflicts.
- **`notifications.ts` new store:** Created in this story. Future stories (@mentions from Story 1.5, chat assignments from Story 3.5) will add more notification types to the same store. Design the store to be extensible: use a generic `Notification` interface with a `type: "sla_warning" | "sla_breached" | "mention" | "chat_assignment"` discriminant.
- **Frontend ticket list component:** The exact filename for the ticket list row component is not specified in the architecture; inspect `helpdesk/desk/src/pages/desk/` or `helpdesk/desk/src/components/ticket/` to find the component that renders the SLA countdown badge. Common names: `TicketListItem.vue`, `DeskTicketRow.vue`, `TicketRow.vue`. Use Glob/Read to confirm before editing.
- **Relationship to Story 2.3 (SLA-Based Automation Triggers):** Story 2.3 consumes the `sla_warning` and `sla_breached` events fired here. Story 4.2 is the source; Story 2.3 configures the automation rules. The integration point is `evaluate_rules(trigger_type, doc_name)` — Stories 4.2 and 2.3 must agree on this interface before merging.
- **Story dependency chain:** Story 4.1 → Story 4.2 → Story 4.3 (SLA Dashboard uses `agreement_status = "Failed"` data), Story 2.3 (automation rules on SLA events). Ensure Story 4.1 is in `review` or `done` status before starting Story 4.2.

### References

- FR-SL-02 (Proactive SLA Breach Alerts): [Source: _bmad-output/planning-artifacts/prd.md#FR-SL-02]
- FR-SL-02 Acceptance Criteria (30/15/5 min thresholds, color-coding, in-app + email notifications): [Source: _bmad-output/planning-artifacts/epics.md#Story 4.2]
- FR-WA-03 (SLA-based automation triggers at configurable warning thresholds): [Source: _bmad-output/planning-artifacts/epics.md#Non-Functional Requirements]
- UX-DR-06 (SLA breach color coding: yellow >30 min, orange 15–30 min, red <15 min): [Source: _bmad-output/planning-artifacts/epics.md#UX Design Requirements]
- NFR-M-01 (80% unit test coverage): [Source: _bmad-output/planning-artifacts/epics.md#Non-Functional Requirements]
- NFR-A-01 (Core ticketing unaffected by automation failures — wrap evaluate_rules in try/except): [Source: _bmad-output/planning-artifacts/epics.md#Non-Functional Requirements]
- NFR-A-03 (Auto-disable automation rules after 10 consecutive failures): [Source: _bmad-output/planning-artifacts/epics.md#Non-Functional Requirements]
- ADR-12 (Background Job Architecture — `short` queue for SLA notifications, scheduler events): [Source: _bmad-output/planning-artifacts/architecture.md#ADR-12]
- ADR-13 (SLA Business Hours Calculation Engine — sla_monitor.py, Redis caching): [Source: _bmad-output/planning-artifacts/architecture.md#ADR-13]
- ADR-14 (Automation Rule Evaluation Engine — engine.py, evaluate_rules() interface): [Source: _bmad-output/planning-artifacts/architecture.md#ADR-14]
- AR-03 (Background jobs use Redis Queue): [Source: _bmad-output/planning-artifacts/epics.md#Additional Requirements]
- AR-04 (DocType JSON modification, not Custom Fields): [Source: _bmad-output/planning-artifacts/epics.md#Additional Requirements]
- AR-05 (Migration patches in helpdesk/patches/v1_phase1/): [Source: _bmad-output/planning-artifacts/epics.md#Additional Requirements]
- AR-07 (Socket.IO room naming: agent:{email}, ticket:{id}, team:{name}): [Source: _bmad-output/planning-artifacts/epics.md#Additional Requirements]
- Notification store (`notifications.ts`): [Source: _bmad-output/planning-artifacts/architecture.md#Project Directory Structure, stores]
- SLA breach email template path (`sla_breach_alert.html`): [Source: _bmad-output/planning-artifacts/architecture.md#Project Directory Structure, templates]
- Real-time events (`sla_warning → agent:{email} room`): [Source: _bmad-output/planning-artifacts/architecture.md#Communication Patterns]
- HD Service Level Agreement DocType: `helpdesk/helpdesk/doctype/hd_service_level_agreement/`
- HD Team DocType: `helpdesk/helpdesk/doctype/hd_team/`
- HD Ticket DocType: `helpdesk/helpdesk/doctype/hd_ticket/`
- hooks.py (scheduler): `helpdesk/hooks.py`
- Frontend stores: `helpdesk/desk/src/stores/`
- Frontend realtime composable: `helpdesk/desk/src/composables/realtime.ts`

## Dev Agent Record

### Agent Model Used

Claude Sonnet 4.5 (create-story workflow)

### Debug Log References

_None — story creation phase_

### Completion Notes List

_To be filled by implementing dev agent_

### File List

_To be filled by implementing dev agent upon completion_
