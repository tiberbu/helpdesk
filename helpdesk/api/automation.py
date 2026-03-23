# Copyright (c) 2026, Frappe Technologies Pvt. Ltd. and contributors
# For license information, please see license.txt

"""Automation rule API endpoints.

Whitelisted methods:
    test_rule          — dry-run evaluate a rule against a ticket
    toggle_rule        — enable / disable a rule
    get_execution_stats — per-rule execution statistics
"""

import frappe
from frappe import _

from helpdesk.helpdesk.automation.engine import evaluate as engine_evaluate


@frappe.whitelist()
def test_rule(rule_name: str, ticket_name: str) -> dict:
    """Dry-run evaluate an automation rule against a ticket.

    Evaluates conditions and plans actions without executing anything.

    Args:
        rule_name: The name (= rule_name field value) of the HD Automation Rule.
        ticket_name: The name of the HD Ticket to test against.

    Returns:
        dict with keys: would_fire (bool), conditions (list), actions (list), trigger_type (str).
    """
    frappe.only_for(["System Manager", "HD Admin"])

    if not frappe.db.exists("HD Automation Rule", rule_name):
        frappe.throw(_("Automation Rule '{0}' not found.").format(rule_name), frappe.DoesNotExistError)

    if not frappe.db.exists("HD Ticket", ticket_name):
        frappe.throw(_("Ticket '{0}' not found.").format(ticket_name), frappe.DoesNotExistError)

    rule_doc = frappe.db.get_value(
        "HD Automation Rule",
        rule_name,
        ["trigger_type", "conditions", "actions"],
        as_dict=True,
    )
    ticket = frappe.get_doc("HD Ticket", ticket_name)

    result = engine_evaluate(ticket, rule_doc.trigger_type, dry_run=True, rule_name=rule_name)

    if not result:
        result = {"would_fire": False, "conditions_detail": [], "actions_detail": []}

    return {
        "would_fire": result.get("would_fire", False),
        "conditions": result.get("conditions_detail", []),
        "actions": result.get("actions_detail", []),
        "trigger_type": rule_doc.trigger_type,
    }


@frappe.whitelist()
def toggle_rule(rule_name: str, enabled: int) -> dict:
    """Enable or disable an HD Automation Rule.

    Args:
        rule_name: The name of the HD Automation Rule.
        enabled:   1 to enable, 0 to disable.

    Returns:
        dict with keys: rule_name, enabled.
    """
    frappe.only_for(["System Manager", "HD Admin"])

    if not frappe.db.exists("HD Automation Rule", rule_name):
        frappe.throw(_("Automation Rule '{0}' not found.").format(rule_name), frappe.DoesNotExistError)

    frappe.db.set_value("HD Automation Rule", rule_name, "enabled", int(enabled))
    return {"rule_name": rule_name, "enabled": int(enabled)}


@frappe.whitelist()
def get_execution_stats() -> list:
    """Return per-rule execution statistics from HD Automation Log.

    Returns a list of dicts, one per HD Automation Rule, with fields:
        rule_name, trigger_type, enabled, priority_order, failure_count,
        execution_count, last_fired, failure_rate.

    Uses a single aggregate SQL query across HD Automation Log for efficiency,
    then merges with the rule list (batch approach avoids N+1 queries).
    """
    frappe.only_for(["System Manager", "HD Admin"])

    rules = frappe.get_all(
        "HD Automation Rule",
        fields=["name", "rule_name", "trigger_type", "enabled", "failure_count", "priority_order"],
        order_by="priority_order asc",
    )

    # Aggregate log stats per rule in a single query
    log_rows = frappe.db.sql(
        """
        SELECT
            rule_name,
            COUNT(*) AS execution_count,
            MAX(timestamp) AS last_fired,
            SUM(CASE WHEN status = 'failure' THEN 1 ELSE 0 END) AS failure_total
        FROM `tabHD Automation Log`
        GROUP BY rule_name
        """,
        as_dict=True,
    )

    stats_by_rule = {row["rule_name"]: row for row in log_rows}

    for rule in rules:
        log_stat = stats_by_rule.get(rule["name"]) or {}
        execution_count = int(log_stat.get("execution_count") or 0)
        failure_total = int(log_stat.get("failure_total") or 0)
        rule["execution_count"] = execution_count
        rule["last_fired"] = str(log_stat["last_fired"]) if log_stat.get("last_fired") else None
        rule["failure_rate"] = (
            round((failure_total / execution_count) * 100, 1) if execution_count > 0 else 0.0
        )

    return rules
