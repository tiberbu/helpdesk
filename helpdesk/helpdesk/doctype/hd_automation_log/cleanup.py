# Copyright (c) 2026, Frappe Technologies Pvt. Ltd. and contributors
# For license information, please see license.txt

"""Daily cleanup job for HD Automation Log records.

Registered in hooks.py under scheduler_events["daily"].
Purges log records older than the configured retention period.
"""

import frappe


def purge_old_logs():
    """Delete HD Automation Log records older than the configured retention period.

    Reads log_retention_days from HD Settings (default: 30). Runs as a daily
    background scheduler event — no user context, no permission checks needed.
    """
    retention_days = frappe.db.get_single_value("HD Settings", "log_retention_days")
    try:
        retention_days = int(retention_days or 30)
    except (TypeError, ValueError):
        retention_days = 30

    # Enforce minimum of 1 day to prevent accidental full wipe
    retention_days = max(1, retention_days)

    cutoff = frappe.utils.add_days(frappe.utils.now_datetime(), -retention_days)

    frappe.db.delete("HD Automation Log", {"timestamp": ("<", cutoff)})
    frappe.db.commit()  # nosemgrep

    frappe.logger().info(
        f"HD Automation Log cleanup: purged records older than {retention_days} days (cutoff: {cutoff})"
    )
