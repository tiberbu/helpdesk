# Copyright (c) 2026, Frappe Technologies Pvt. Ltd. and contributors
# For license information, please see license.txt

"""Safety guards for the automation engine.

Provides:
    - Loop detection: block evaluation when > 5 executions for the same
      ticket within 60 seconds (configurable via MAX_EXECUTIONS_PER_WINDOW).
    - Auto-disable: disable a rule after MAX_CONSECUTIVE_FAILURES consecutive
      failures (NFR-A-03).
"""

import frappe

# Maximum rule executions per ticket within the time window
MAX_EXECUTIONS_PER_WINDOW = 5

# Time window for loop detection in seconds
LOOP_WINDOW_SECONDS = 60

# Number of consecutive failures before a rule is auto-disabled (NFR-A-03)
MAX_CONSECUTIVE_FAILURES = 10

# Redis key template for loop detection counters
_LOOP_KEY_TEMPLATE = "automation:loop:{ticket_name}"


class SafetyGuard:
    """Encapsulates all safety checks for the automation engine."""

    def check_loop(self, ticket_name: str) -> bool:
        """Check whether execution for this ticket should be blocked.

        Increments the per-ticket execution counter in Redis. If the counter
        already reached MAX_EXECUTIONS_PER_WINDOW this window, logs a warning
        and returns False (block execution).

        Args:
            ticket_name: The HD Ticket name/ID.

        Returns:
            True  — safe to proceed.
            False — loop detected; caller must abort.
        """
        key = _LOOP_KEY_TEMPLATE.format(ticket_name=ticket_name)
        cache = frappe.cache()

        # Read current count; default to 0 if key doesn't exist
        current = cache.get_value(key) or 0
        try:
            current = int(current)
        except (TypeError, ValueError):
            current = 0

        if current >= MAX_EXECUTIONS_PER_WINDOW:
            frappe.log_error(
                title="AutomationRule: loop detected",
                message=(
                    f"Ticket {ticket_name!r} has triggered automation rules "
                    f"{current} times within {LOOP_WINDOW_SECONDS}s. "
                    "Further execution blocked to prevent infinite loop."
                ),
            )
            return False

        # Increment counter; (re-)set TTL on every increment so the window
        # slides from the first execution.
        new_count = current + 1
        cache.set_value(key, new_count, expires_in_sec=LOOP_WINDOW_SECONDS)
        return True

    def record_success(self, rule_name: str):
        """Reset the consecutive-failure counter after a successful execution.

        Args:
            rule_name: HD Automation Rule document name.
        """
        try:
            current = frappe.db.get_value("HD Automation Rule", rule_name, "failure_count") or 0
            if int(current) != 0:
                frappe.db.set_value("HD Automation Rule", rule_name, "failure_count", 0)
        except Exception:
            # Non-critical; swallow errors from counter reset
            pass

    def record_failure(self, rule_name: str):
        """Increment the consecutive-failure counter.

        If the counter reaches MAX_CONSECUTIVE_FAILURES the rule is
        automatically disabled and an error is logged (NFR-A-03).

        Args:
            rule_name: HD Automation Rule document name.
        """
        try:
            current = frappe.db.get_value("HD Automation Rule", rule_name, "failure_count") or 0
            new_count = int(current) + 1
            frappe.db.set_value("HD Automation Rule", rule_name, "failure_count", new_count)

            if new_count >= MAX_CONSECUTIVE_FAILURES:
                frappe.db.set_value("HD Automation Rule", rule_name, "enabled", 0)
                frappe.log_error(
                    title="AutomationRule: auto-disabled after repeated failures",
                    message=(
                        f"Automation Rule '{rule_name}' has been automatically disabled "
                        f"after {new_count} consecutive failures (threshold: "
                        f"{MAX_CONSECUTIVE_FAILURES})."
                    ),
                )
                _notify_rule_creator(rule_name)
        except Exception:
            # Non-critical; swallow errors from failure tracking
            frappe.log_error(
                title="AutomationRule: failed to record failure",
                message=frappe.get_traceback(),
            )

    def reset_loop_counter(self, ticket_name: str):
        """Clear the loop counter for a ticket (test helper / manual reset)."""
        key = _LOOP_KEY_TEMPLATE.format(ticket_name=ticket_name)
        frappe.cache().delete_value(key)


def _notify_rule_creator(rule_name: str):
    """Send email + in-app notification to the rule owner when auto-disabled.

    Silently swallows all exceptions — notification failure must not
    interrupt the disable operation.
    """
    try:
        owner = frappe.db.get_value("HD Automation Rule", rule_name, "owner")
        if not owner:
            return

        owner_email = frappe.db.get_value("User", owner, "email") or owner
        subject = frappe._("Automation Rule Auto-Disabled: {0}").format(rule_name)
        message = frappe._(
            "Your automation rule <b>{0}</b> has been automatically disabled "
            "after {1} consecutive failures. Please review the "
            "<a href='/helpdesk/automations'>Automation Rules</a> page and "
            "check the HD Automation Log for details before re-enabling the rule."
        ).format(rule_name, MAX_CONSECUTIVE_FAILURES)

        frappe.sendmail(
            recipients=[owner_email],
            subject=subject,
            message=message,
        )

        frappe.publish_realtime(
            event="notification",
            message={
                "title": subject,
                "message": frappe._(
                    "Rule '{0}' was auto-disabled after {1} consecutive failures."
                ).format(rule_name, MAX_CONSECUTIVE_FAILURES),
                "type": "warning",
                "link": "/helpdesk/automations",
            },
            room=f"agent:{owner_email}",
        )
    except Exception:
        frappe.log_error(
            title="AutomationRule: auto-disable notification failed",
            message=frappe.get_traceback(),
        )
