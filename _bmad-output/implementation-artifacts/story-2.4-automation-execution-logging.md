# Story 2.4: Automation Execution Logging

Status: ready-for-dev

## Story

As an administrator,
I want to see a log of every automation rule execution,
so that I can debug and optimize my rules.

## Acceptance Criteria

1. **HD Automation Log DocType exists with required fields**: The `HD Automation Log` DocType is created with fields: `rule_name` (Link → HD Automation Rule), `ticket` (Link → HD Ticket), `trigger_event` (Data), `conditions_evaluated` (JSON), `actions_executed` (JSON), `execution_time_ms` (Int), `status` (Select: "success"/"failure"/"skipped"), `error_message` (Text), `timestamp` (Datetime). The DocType is read-only (no user creation) and accessible via REST API (NFR-M-02).

2. **Execution logged on every engine run (success and failure)**: Given an automation rule executes — whether it matches conditions and fires actions (success), fails mid-action (failure), or conditions do not match (skipped) — when `AutomationEngine.evaluate()` completes, an `HD Automation Log` record is created capturing the full execution context including `execution_time_ms` measured from engine entry to exit.

3. **Failure logging captures error detail**: Given an automation rule action raises an unhandled exception, when the engine catches the exception, the log record is created with `status = "failure"` and the `error_message` field populated with the traceback or exception message (not surfaced to users, only to admins).

4. **Per-rule execution statistics API**: A whitelisted API method `get_execution_stats(rule_name)` in `helpdesk/api/automation.py` returns a dict with: `execution_count` (total log entries for the rule), `last_fired` (timestamp of the most recent log entry), `failure_rate` (percentage of entries with status "failure", rounded to 1 decimal place). Returns `{"execution_count": 0, "last_fired": null, "failure_rate": 0.0}` for rules with no logs.

5. **Per-rule stats visible on automation list page**: The `AutomationList.vue` page (at `/helpdesk/automations`) displays per-rule statistics — execution count, last fired time, failure rate — fetched via `get_execution_stats()` for each visible rule. Stats are shown in the rule list as read-only columns or inline badges.

6. **Auto-disable after 10 consecutive failures with notification**: Given a rule has failed 10 consecutive times (all 10 most recent log entries for the rule have `status = "failure"`), when the safety module detects this after each failure, the rule's `enabled` field is set to `0` AND a Frappe notification is sent to the rule's `owner` (creator) with: subject "Automation Rule Auto-Disabled: {rule_name}", body indicating the rule was disabled due to consecutive failures and a link to the rule. The notification is delivered via `frappe.sendmail()` and as an in-app notification via `frappe.publish_realtime()` to `agent:{owner_email}`.

7. **Daily log cleanup scheduler event**: A `daily` scheduler event in `hooks.py` pointing to `helpdesk.helpdesk.doctype.hd_automation_log.cleanup.purge_old_logs` deletes `HD Automation Log` records older than the configured retention period.

8. **Configurable log retention period**: A `log_retention_days` Int field (default: `30`, minimum: `1`) is added to `HD Settings`. The `purge_old_logs()` function reads this value via `frappe.db.get_single_value("HD Settings", "log_retention_days")` and falls back to `30` if null.

9. **Unit tests with minimum 80% coverage**: Unit tests exist for: log record creation (success and failure paths), `get_execution_stats()` calculations, auto-disable + notification trigger, and `purge_old_logs()` deletion logic (NFR-M-01).

## Tasks / Subtasks

- [ ] **Task 1: Create HD Automation Log DocType** (AC: #1)
  - [ ] 1.1 Create `helpdesk/helpdesk/doctype/hd_automation_log/` directory with `__init__.py`
  - [ ] 1.2 Create `hd_automation_log.json` with fields:
    - `rule_name` (Link, options: "HD Automation Rule", in_list_view: 1)
    - `ticket` (Link, options: "HD Ticket", in_list_view: 1)
    - `trigger_event` (Data, in_list_view: 1)
    - `conditions_evaluated` (JSON)
    - `actions_executed` (JSON)
    - `execution_time_ms` (Int)
    - `status` (Select, options: "success\nfailure\nskipped", in_list_view: 1)
    - `error_message` (Text)
    - `timestamp` (Datetime, default: "Now", in_list_view: 1)
  - [ ] 1.3 Set DocType properties: `is_submittable: 0`, `allow_import: 0`, `allow_rename: 0`, `track_changes: 0` (log records are immutable)
  - [ ] 1.4 Set permissions: System Manager and HD Admin (read + delete only); no creation/write permissions for any role (creation is programmatic only)
  - [ ] 1.5 Create `hd_automation_log.py` controller (minimal — no business logic needed in controller; log creation is via `frappe.get_doc().insert(ignore_permissions=True)`)
  - [ ] 1.6 Create `cleanup.py` in the same directory with `purge_old_logs()` function (Task 4 below)

- [ ] **Task 2: Integrate logging into the automation engine** (AC: #2, #3)
  - [ ] 2.1 In `helpdesk/helpdesk/automation/engine.py`, wrap the condition evaluation + action execution block with a timer: record `start_time = time.monotonic()` before conditions evaluation; compute `execution_time_ms = int((time.monotonic() - start_time) * 1000)` after completion
  - [ ] 2.2 After action execution completes (success path), call `_create_log(rule, ticket, trigger_type, conditions, actions, execution_time_ms, status="success")` — a private helper method on `AutomationEngine`
  - [ ] 2.3 In the `except Exception` block (failure path), call `_create_log(...)` with `status="failure"` and `error_message=frappe.get_traceback()` before re-logging or continuing
  - [ ] 2.4 When conditions do not match (skipped path), call `_create_log(...)` with `status="skipped"`, `actions_executed=[]`
  - [ ] 2.5 Implement `_create_log()` private method:
    ```python
    def _create_log(self, rule, ticket, trigger_event, conditions_evaluated,
                    actions_executed, execution_time_ms, status, error_message=""):
        try:
            frappe.get_doc({
                "doctype": "HD Automation Log",
                "rule_name": rule.name,
                "ticket": ticket.name if ticket else None,
                "trigger_event": trigger_event,
                "conditions_evaluated": frappe.as_json(conditions_evaluated),
                "actions_executed": frappe.as_json(actions_executed),
                "execution_time_ms": execution_time_ms,
                "status": status,
                "error_message": error_message,
                "timestamp": frappe.utils.now_datetime(),
            }).insert(ignore_permissions=True)
        except Exception:
            frappe.log_error(frappe.get_traceback(), "HD Automation Log creation failed")
            # Never let logging failures interrupt rule execution
    ```
  - [ ] 2.6 Wrap `_create_log()` in its own try/except so a logging failure never affects core ticket processing (NFR-A-01)

- [ ] **Task 3: Extend safety module with auto-disable notification** (AC: #6)
  - [ ] 3.1 In `helpdesk/helpdesk/automation/safety.py`, extend the auto-disable logic (from Story 2.1): after setting `rule.enabled = 0` and saving, check the 10 most recent `HD Automation Log` entries for the rule — if all 10 have `status = "failure"`, trigger notification
  - [ ] 3.2 Alternatively (simpler approach): after the existing consecutive failure counter reaches 10 in `safety.py`, call `_notify_rule_creator(rule)` before or after disabling
  - [ ] 3.3 Implement `_notify_rule_creator(rule)` helper in `safety.py`:
    - Fetch rule owner email: `owner_email = frappe.db.get_value("User", rule.owner, "email")`
    - Send email via `frappe.sendmail(recipients=[owner_email], subject=..., message=...)`
    - Send in-app notification via `frappe.publish_realtime("notification", {...}, room=f"agent:{owner_email}")`
    - Include in the notification: rule name, link to rule at `/helpdesk/automations/{rule.name}`, and guidance to check the HD Automation Log
  - [ ] 3.4 Guard `_notify_rule_creator()` in try/except — notification failures must not interrupt the disable operation
  - [ ] 3.5 Add unit test for notification: mock `frappe.sendmail` and `frappe.publish_realtime`; trigger 10 failures; assert both were called with correct arguments

- [ ] **Task 4: Add log cleanup function and scheduler event** (AC: #7, #8)
  - [ ] 4.1 In `helpdesk/helpdesk/doctype/hd_automation_log/cleanup.py`, implement `purge_old_logs()`:
    ```python
    import frappe

    def purge_old_logs():
        """Delete HD Automation Log records older than configured retention period."""
        retention_days = frappe.db.get_single_value("HD Settings", "log_retention_days") or 30
        cutoff_date = frappe.utils.add_days(frappe.utils.today(), -int(retention_days))
        frappe.db.delete("HD Automation Log", {"timestamp": ("<", cutoff_date)})
        frappe.db.commit()
    ```
  - [ ] 4.2 Add `log_retention_days` Int field to `helpdesk/helpdesk/doctype/hd_settings/hd_settings.json`:
    ```json
    {
      "fieldname": "log_retention_days",
      "fieldtype": "Int",
      "label": "Automation Log Retention (days)",
      "default": "30",
      "description": "HD Automation Log records older than this many days will be automatically deleted. Minimum: 1."
    }
    ```
  - [ ] 4.3 In `helpdesk/hooks.py`, add or verify the daily cleanup scheduler event:
    ```python
    scheduler_events = {
        # ... existing entries ...
        "daily": [
            "helpdesk.helpdesk.doctype.hd_automation_log.cleanup.purge_old_logs",
            # ... other daily jobs ...
        ]
    }
    ```
  - [ ] 4.4 Create migration patch `helpdesk/patches/v1_phase1/add_log_retention_days_setting.py` that sets `log_retention_days = 30` on HD Settings for existing installations

- [ ] **Task 5: Implement per-rule execution statistics API** (AC: #4)
  - [ ] 5.1 In `helpdesk/api/automation.py`, implement `get_execution_stats(rule_name: str)`:
    ```python
    @frappe.whitelist()
    def get_execution_stats(rule_name: str) -> dict:
        frappe.has_permission("HD Automation Rule", "read", throw=True)
        logs = frappe.db.get_all(
            "HD Automation Log",
            filters={"rule_name": rule_name},
            fields=["status", "timestamp"],
            order_by="timestamp desc",
        )
        if not logs:
            return {"execution_count": 0, "last_fired": None, "failure_rate": 0.0}
        total = len(logs)
        failures = sum(1 for log in logs if log["status"] == "failure")
        return {
            "execution_count": total,
            "last_fired": str(logs[0]["timestamp"]),
            "failure_rate": round((failures / total) * 100, 1),
        }
    ```
  - [ ] 5.2 Verify `helpdesk/api/automation.py` exists (from Story 2.1/2.2 scope); create it if it does not exist with the standard module header
  - [ ] 5.3 Write unit tests for `get_execution_stats()` covering: rule with no logs, rule with mixed success/failure, rule with 100% failures, `failure_rate` rounding

- [ ] **Task 6: Display stats on AutomationList.vue** (AC: #5)
  - [ ] 6.1 In `desk/src/pages/automations/AutomationList.vue` (created in Story 2.2), add a `createResource` call for each rule row to fetch `get_execution_stats`:
    ```javascript
    const stats = createResource({
      url: "helpdesk.api.automation.get_execution_stats",
      params: { rule_name: row.name },
      auto: true,
    })
    ```
  - [ ] 6.2 Display stats as additional columns or inline badges in the rule list: "X runs", "Last: {relative time}", "{N}% failures" (use dayjs for relative time formatting consistent with existing codebase)
  - [ ] 6.3 Style the failure rate badge: green if 0%, yellow if 1–25%, red if >25% (using Tailwind classes consistent with frappe-ui patterns)
  - [ ] 6.4 If `AutomationList.vue` does not yet exist (Story 2.2 not merged), create a minimal stub that lists rules with stats — document the dependency clearly in a code comment
  - [ ] 6.5 Handle loading and empty states: show skeleton placeholders while stats load; show "—" for rules with no execution history

- [ ] **Task 7: Write unit tests** (AC: #9)
  - [ ] 7.1 Create `helpdesk/helpdesk/doctype/hd_automation_log/test_hd_automation_log.py`:
    - Test log record creation via `_create_log()` (success, failure, skipped paths)
    - Test that a logging failure inside `_create_log()` does not raise (exception is swallowed)
    - Test `purge_old_logs()` with a mix of old and recent records — assert only old records deleted
    - Test `purge_old_logs()` reads `log_retention_days` from HD Settings correctly
  - [ ] 7.2 Create or extend `helpdesk/helpdesk/automation/test_safety.py` (from Story 2.1):
    - Test auto-disable + notification: simulate 10 consecutive failures; assert `rule.enabled == 0` AND `frappe.sendmail` called
    - Test that notification is NOT sent when consecutive failure count < 10
    - Test that `_notify_rule_creator()` failure does not prevent the rule from being disabled
  - [ ] 7.3 Create `helpdesk/api/test_automation_stats.py`:
    - Test `get_execution_stats()` with 0, 5, and 100 log entries
    - Test failure rate calculation: 3 failures out of 10 entries = 30.0%
    - Test `last_fired` returns most recent timestamp

## Dev Notes

### Architecture Overview

Story 2.4 is the final story in Epic 2 and completes the automation engine pipeline defined in ADR-14. The execution logger is the last step after action execution:

```
Ticket Event (create/update/resolve/etc.)
    |
    v
Rule Fetcher (enabled rules matching trigger type)
    |
    v
Safety Guard (loop detection, Redis counter)
    |
    v
Condition Evaluator (AND/OR conditions against ticket fields)
    |
    v
Action Executor (assign, notify, set_field, etc.)
    |
    v
Execution Logger [THIS STORY] --> HD Automation Log record
    |
    v
Auto-Disable Check [THIS STORY extends Story 2.1 safety.py]
```

### Dependency on Story 2.1 (Automation Engine Core)

This story EXTENDS `engine.py` and `safety.py` from Story 2.1. Key assumptions:
- `AutomationEngine.evaluate(ticket, trigger_type)` already exists
- `SafetyGuard` in `safety.py` already tracks consecutive failures via `failure_count` field on `HD Automation Rule`
- The `failure_count` on `HD Automation Rule` DocType JSON must be verified; if not present, add it in Story 2.4
- Do NOT re-implement auto-disable logic; extend it with the notification step

If Story 2.1 is not yet merged, stub out the minimum `AutomationEngine` class interface to support development of the logging layer independently.

### Dependency on Story 2.2 (Automation Rule Builder UI)

The stats display in Task 6 (`AutomationList.vue`) is a frontend extension of Story 2.2's UI. If Story 2.2 is not yet merged:
- Implement the `get_execution_stats` API (Task 5) fully — it has no frontend dependency
- Create a minimal `AutomationList.vue` stub or leave a TODO comment in the component for the stats columns
- The backend (logging, cleanup, stats API) is fully independent of Story 2.2

### HD Automation Log DocType — Field Schema

```json
{
  "doctype": "DocType",
  "name": "HD Automation Log",
  "module": "Helpdesk",
  "is_submittable": 0,
  "allow_import": 0,
  "allow_rename": 0,
  "track_changes": 0,
  "fields": [
    {"fieldname": "rule_name", "fieldtype": "Link", "options": "HD Automation Rule", "label": "Rule", "reqd": 1, "in_list_view": 1},
    {"fieldname": "ticket", "fieldtype": "Link", "options": "HD Ticket", "label": "Ticket", "in_list_view": 1},
    {"fieldname": "trigger_event", "fieldtype": "Data", "label": "Trigger Event", "in_list_view": 1},
    {"fieldname": "conditions_evaluated", "fieldtype": "JSON", "label": "Conditions Evaluated"},
    {"fieldname": "actions_executed", "fieldtype": "JSON", "label": "Actions Executed"},
    {"fieldname": "execution_time_ms", "fieldtype": "Int", "label": "Execution Time (ms)"},
    {"fieldname": "status", "fieldtype": "Select", "options": "success\nfailure\nskipped", "label": "Status", "in_list_view": 1},
    {"fieldname": "error_message", "fieldtype": "Text", "label": "Error Message"},
    {"fieldname": "timestamp", "fieldtype": "Datetime", "label": "Timestamp", "default": "Now", "in_list_view": 1}
  ],
  "permissions": [
    {"role": "System Manager", "read": 1, "delete": 1},
    {"role": "HD Admin", "read": 1, "delete": 1},
    {"role": "HD Agent", "read": 1}
  ]
}
```

### Log Insertion Pattern

Use `insert(ignore_permissions=True)` because the engine runs in system context (background jobs, doc_events). Never use `frappe.new_doc()` + `save()` for log creation — it triggers unnecessary validation hooks:

```python
frappe.get_doc({
    "doctype": "HD Automation Log",
    "rule_name": rule.name,
    "ticket": getattr(ticket, "name", None),
    "trigger_event": trigger_event,
    "conditions_evaluated": frappe.as_json(conditions_evaluated or []),
    "actions_executed": frappe.as_json(actions_executed or []),
    "execution_time_ms": execution_time_ms,
    "status": status,  # "success", "failure", or "skipped"
    "error_message": error_message or "",
    "timestamp": frappe.utils.now_datetime(),
}).insert(ignore_permissions=True)
```

### Auto-Disable Notification Pattern

```python
def _notify_rule_creator(rule):
    """Notify the automation rule creator that the rule was auto-disabled."""
    try:
        owner_email = frappe.db.get_value("User", rule.owner, "email") or rule.owner
        rule_url = f"/helpdesk/automations/{frappe.utils.quote(rule.name)}"
        subject = frappe._("Automation Rule Auto-Disabled: {0}").format(rule.name)
        message = frappe._(
            "Your automation rule <b>{0}</b> has been automatically disabled after "
            "10 consecutive failures. Please review the <a href='/helpdesk/automations/"
            "?rule={1}'>Automation Log</a> for details and re-enable the rule after "
            "fixing the issue."
        ).format(rule.name, rule.name)

        frappe.sendmail(
            recipients=[owner_email],
            subject=subject,
            message=message,
        )
        frappe.publish_realtime(
            event="notification",
            message={
                "title": subject,
                "message": frappe._("Rule '{0}' was auto-disabled. Check Automation Logs.").format(rule.name),
                "type": "warning",
                "link": rule_url,
            },
            room=f"agent:{owner_email}",
        )
    except Exception:
        frappe.log_error(frappe.get_traceback(), f"Auto-disable notification failed for rule {rule.name}")
```

### Consecutive Failure Detection

Two approaches — pick whichever is more consistent with Story 2.1's implementation:

**Option A (counter on DocType — preferred if Story 2.1 already uses `failure_count` field):**
```python
# In safety.py, after incrementing failure_count:
if rule.failure_count >= 10:
    rule.enabled = 0
    rule.save(ignore_permissions=True)
    _notify_rule_creator(rule)
```

**Option B (query HD Automation Log — more accurate, no DocType field needed):**
```python
# Check last 10 logs for the rule
recent_statuses = frappe.db.get_all(
    "HD Automation Log",
    filters={"rule_name": rule.name},
    fields=["status"],
    order_by="timestamp desc",
    limit=10,
)
if len(recent_statuses) >= 10 and all(s["status"] == "failure" for s in recent_statuses):
    rule.enabled = 0
    rule.save(ignore_permissions=True)
    _notify_rule_creator(rule)
```

**Recommendation:** Option A is simpler and consistent with the `failure_count` field described in Story 2.1's `safety.py`. Use Option A. The `failure_count` field must be reset to `0` on any successful execution in `engine.py`.

### Log Cleanup — frappe.db.delete Pattern

```python
import frappe

def purge_old_logs():
    retention_days = int(frappe.db.get_single_value("HD Settings", "log_retention_days") or 30)
    cutoff = frappe.utils.add_days(frappe.utils.now_datetime(), -retention_days)
    deleted = frappe.db.delete(
        "HD Automation Log",
        {"timestamp": ("<", cutoff)}
    )
    frappe.db.commit()
    frappe.logger().info(f"HD Automation Log cleanup: purged records older than {retention_days} days")
```

Note: `frappe.db.delete()` is the correct Frappe ORM method (not `frappe.db.sql`). This runs as a `daily` scheduler event — no user context, no permission checks needed.

### Scheduler Event (Architecture ADR-12)

The architecture document (ADR-12) already specifies this daily event:

```python
# hooks.py (from Architecture ADR-12)
scheduler_events = {
    "daily": [
        "helpdesk.helpdesk.doctype.hd_automation_log.cleanup.purge_old_logs",
        "helpdesk.helpdesk.doctype.hd_article.review_reminder.send_review_reminders"
    ]
}
```

Verify this entry exists in `hooks.py`. If not present, add it — do not duplicate the `daily` key if it already exists, just append to the list.

### Per-Rule Stats — Performance Consideration

The `get_execution_stats()` API performs a single `frappe.db.get_all()` per rule. On the automation list page with many rules, this could result in N calls. Optimize if needed:

```python
# Batch stats for all rules at once (optional optimization)
@frappe.whitelist()
def get_all_execution_stats() -> list:
    """Returns stats for all rules in a single query."""
    frappe.has_permission("HD Automation Rule", "read", throw=True)
    results = frappe.db.sql("""
        SELECT
            rule_name,
            COUNT(*) as execution_count,
            MAX(timestamp) as last_fired,
            ROUND(SUM(CASE WHEN status = 'failure' THEN 1 ELSE 0 END) * 100.0 / COUNT(*), 1) as failure_rate
        FROM `tabHD Automation Log`
        GROUP BY rule_name
    """, as_dict=True)
    return results
```

The batch approach avoids N API calls from the list page. Implement `get_all_execution_stats()` in addition to per-rule `get_execution_stats()` — the frontend can use the batch endpoint for the list view.

### Key Files to Create / Modify

| File | Action | Purpose |
|------|--------|---------|
| `helpdesk/helpdesk/doctype/hd_automation_log/__init__.py` | Create | Python package marker |
| `helpdesk/helpdesk/doctype/hd_automation_log/hd_automation_log.json` | Create | DocType schema definition |
| `helpdesk/helpdesk/doctype/hd_automation_log/hd_automation_log.py` | Create | Minimal DocType controller |
| `helpdesk/helpdesk/doctype/hd_automation_log/cleanup.py` | Create | `purge_old_logs()` daily cleanup function |
| `helpdesk/helpdesk/doctype/hd_automation_log/test_hd_automation_log.py` | Create | Unit tests for DocType and cleanup |
| `helpdesk/helpdesk/automation/engine.py` | Modify | Add `_create_log()` helper; instrument execution timing; call logger after each rule evaluation |
| `helpdesk/helpdesk/automation/safety.py` | Modify | Add `_notify_rule_creator()` helper; call it when rule is auto-disabled (after 10 consecutive failures) |
| `helpdesk/api/automation.py` | Create/Modify | Add `get_execution_stats(rule_name)` and `get_all_execution_stats()` whitelisted methods |
| `helpdesk/api/test_automation_stats.py` | Create | Unit tests for stats API |
| `helpdesk/helpdesk/doctype/hd_settings/hd_settings.json` | Modify | Add `log_retention_days` Int field (default: 30) |
| `helpdesk/patches/v1_phase1/add_log_retention_days_setting.py` | Create | Migration patch: set default on existing installations |
| `helpdesk/hooks.py` | Verify/Modify | Confirm `daily` scheduler entry for `purge_old_logs` exists |
| `desk/src/pages/automations/AutomationList.vue` | Create/Modify | Add execution stats columns (execution count, last fired, failure rate) |

### NFR References

| NFR | Requirement | Implementation Approach |
|-----|-------------|------------------------|
| NFR-P-06 | Rule evaluation < 100ms per rule | Logging is async via `insert(ignore_permissions=True)`; failures in logging never block evaluation |
| NFR-A-01 | Core ticketing unaffected by automation failures | `_create_log()` wrapped in try/except; cleanup job runs independently |
| NFR-A-03 | Auto-disable rules after 10 consecutive failures | Extended in `safety.py` with creator notification |
| NFR-M-01 | 80% unit test coverage on new backend code | Tests for log creation, cleanup, stats API, auto-disable+notify |
| NFR-M-02 | All new DocTypes accessible via REST API | HD Automation Log uses standard Frappe REST (`/api/resource/HD Automation Log`) |
| NFR-SE-04 | Automation rules restricted to System Manager / HD Admin | Stats API checks `frappe.has_permission("HD Automation Rule", "read")` |
| NFR-S-04 | 1000 rule evaluations/minute | Logging uses `insert(ignore_permissions=True)` — fast path; cleanup runs daily in background |

### Project Structure Notes

- **Alignment**: `HD Automation Log` is a new DocType under `helpdesk/helpdesk/doctype/` following the `HD ` prefix convention (AR-02). The `cleanup.py` module lives alongside the DocType per the Frappe pattern for scheduler functions that are logically bound to a specific DocType.
- **No frontend page for log browsing**: Administrators access `HD Automation Log` via the standard Frappe desk (`/app/hd-automation-log`). Story 2.4 adds stats to the existing `AutomationList.vue` page; a dedicated log browser page is out of scope for Phase 1.
- **Separation from Story 2.1**: Story 2.1 defined the `failure_count` mechanism in `safety.py`. Story 2.4 ADDS the notification step to the existing auto-disable flow. Do not re-implement or move the counter logic; locate the notification call immediately after `rule.enabled = 0` in the existing auto-disable block.
- **Batch stats optimization**: The `get_all_execution_stats()` endpoint uses a raw SQL query with `frappe.db.sql()`. This is an exception to the "no raw SQL" rule (ADR enforcement) because it aggregates across all rules efficiently. Add a comment explaining the trade-off.
- **Log volume**: At NFR-S-04 (1000 evaluations/minute), 30-day retention = ~43.2M log records maximum. The 30-day purge is essential. Add a composite index on `(rule_name, timestamp)` in the DocType JSON to ensure stats queries remain fast:
  ```json
  {"doctype": "DocType Index", "fields": ["rule_name", "timestamp"]}
  ```

### References

- [Source: _bmad-output/planning-artifacts/architecture.md#ADR-14: Automation Rule Evaluation Engine]
- [Source: _bmad-output/planning-artifacts/architecture.md#ADR-02: New DocType Schema for Phase 1]
- [Source: _bmad-output/planning-artifacts/architecture.md#ADR-12: Background Job Architecture]
- [Source: _bmad-output/planning-artifacts/architecture.md#ADR-04: Permission Model Extensions]
- [Source: _bmad-output/planning-artifacts/architecture.md#ADR-08: API Design for New Features]
- [Source: _bmad-output/planning-artifacts/architecture.md#Implementation Patterns -- Naming Patterns]
- [Source: _bmad-output/planning-artifacts/architecture.md#Structure Patterns -- New DocType Structure]
- [Source: _bmad-output/planning-artifacts/architecture.md#Process Patterns -- Error Handling]
- [Source: _bmad-output/planning-artifacts/epics.md#Epic 2: Story 2.4: Automation Execution Logging]
- [Source: _bmad-output/planning-artifacts/epics.md#Non-Functional Requirements: NFR-P-06, NFR-A-01, NFR-A-03, NFR-M-01, NFR-M-02, NFR-SE-04, NFR-S-04]
- [Source: _bmad-output/planning-artifacts/epics.md#Additional Requirements: AR-02, AR-03]
- [Source: _bmad-output/planning-artifacts/epics.md#FR-WA-02: Automation Rule Execution Logging]
- [Source: _bmad-output/implementation-artifacts/story-2.1-automation-rule-doctype-and-engine-core.md]
- [Source: _bmad-output/implementation-artifacts/story-2.2-automation-rule-builder-ui.md]

## Dev Agent Record

### Agent Model Used

### Debug Log References

### Completion Notes List

### File List

- `helpdesk/helpdesk/doctype/hd_automation_log/__init__.py` (create)
- `helpdesk/helpdesk/doctype/hd_automation_log/hd_automation_log.json` (create)
- `helpdesk/helpdesk/doctype/hd_automation_log/hd_automation_log.py` (create)
- `helpdesk/helpdesk/doctype/hd_automation_log/cleanup.py` (create)
- `helpdesk/helpdesk/doctype/hd_automation_log/test_hd_automation_log.py` (create)
- `helpdesk/helpdesk/automation/engine.py` (modify: add `_create_log()`, execution timing, log call)
- `helpdesk/helpdesk/automation/safety.py` (modify: add `_notify_rule_creator()`, call on auto-disable)
- `helpdesk/api/automation.py` (create/modify: add `get_execution_stats()`, `get_all_execution_stats()`)
- `helpdesk/api/test_automation_stats.py` (create: unit tests for stats API)
- `helpdesk/helpdesk/doctype/hd_settings/hd_settings.json` (modify: add `log_retention_days` field)
- `helpdesk/patches/v1_phase1/add_log_retention_days_setting.py` (create: migration patch)
- `helpdesk/hooks.py` (verify/modify: add daily scheduler entry for `purge_old_logs`)
- `desk/src/pages/automations/AutomationList.vue` (create/modify: add stats columns)
