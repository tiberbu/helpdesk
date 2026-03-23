# Copyright (c) 2026, Frappe Technologies Pvt. Ltd. and contributors
# For license information, please see license.txt

"""Core automation engine for HD Automation Rules.

Entry points (called from hooks.py doc_events):
    on_ticket_created(doc, method)  — fires for after_insert on HD Ticket
    on_ticket_updated(doc, method)  — fires for on_update on HD Ticket

Architecture (ADR-14):
    1. Check automation_enabled feature flag
    2. Fetch enabled rules for trigger type (single DB query, ordered by priority_order)
    3. For each rule:
        a. Safety guard: check loop counter
        b. Evaluate conditions
        c. If match: execute actions, record success/failure
"""

import frappe

from helpdesk.helpdesk.automation.conditions import ConditionEvaluator
from helpdesk.helpdesk.automation.actions import ActionExecutor
from helpdesk.helpdesk.automation.safety import SafetyGuard
from helpdesk.helpdesk.automation.triggers import resolve_trigger_type


_condition_evaluator = ConditionEvaluator()
_action_executor = ActionExecutor()
_safety_guard = SafetyGuard()


# ------------------------------------------------------------------ #
# Frappe doc_events entry points                                        #
# ------------------------------------------------------------------ #


def on_ticket_created(doc, method=None):
    """Called by Frappe after_insert on HD Ticket."""
    _run(doc, "after_insert")


def on_ticket_updated(doc, method=None):
    """Called by Frappe on_update on HD Ticket."""
    _run(doc, "on_update")


# ------------------------------------------------------------------ #
# Internal evaluation pipeline                                         #
# ------------------------------------------------------------------ #


def _run(doc, frappe_event: str):
    """Main evaluation pipeline entry point.

    Args:
        doc: HD Ticket frappe.Document.
        frappe_event: Frappe doc event name ("after_insert" / "on_update").
    """
    trigger_type = resolve_trigger_type(doc, frappe_event)
    evaluate(doc, trigger_type)


def evaluate(ticket, trigger_type: str):
    """Evaluate all enabled rules for a trigger type against a ticket.

    Rules are fetched in ascending priority_order (lower = higher priority)
    in a single DB call (NFR-P-06 performance requirement).

    Args:
        ticket: HD Ticket frappe.Document or frappe._dict.
        trigger_type: One of the TRIGGER_TYPES constants.
    """
    # AC #12: honour the automation_enabled feature flag
    if not _is_automation_enabled():
        return

    rules = _fetch_rules(trigger_type)
    if not rules:
        return

    ticket_name = str(ticket.name)

    # AC #4: per-ticket loop guard (checked once before processing this batch)
    if not _safety_guard.check_loop(ticket_name):
        return

    for rule in rules:
        _evaluate_rule(ticket, rule)


def _evaluate_rule(ticket, rule: dict):
    """Evaluate a single rule dict against the ticket."""
    rule_name = rule["name"]

    # Evaluate conditions
    conditions = rule.get("conditions") or "[]"
    if not _condition_evaluator.evaluate(ticket, conditions):
        return  # Conditions did not match; skip this rule

    # Execute actions
    actions = rule.get("actions") or "[]"
    results = _action_executor.execute(ticket, actions)

    # Track success / failure for auto-disable
    had_failure = any(not r.get("success") for r in results)
    if had_failure:
        _safety_guard.record_failure(rule_name)
    else:
        _safety_guard.record_success(rule_name)


def _fetch_rules(trigger_type: str) -> list[dict]:
    """Fetch all enabled rules for the given trigger type.

    Single DB query ordered by priority_order ASC (lower = higher priority).
    Returns a list of plain dicts to keep the hot path allocation-light.
    """
    return frappe.get_all(
        "HD Automation Rule",
        filters={"trigger_type": trigger_type, "enabled": 1},
        fields=["name", "rule_name", "conditions", "actions", "priority_order"],
        order_by="priority_order asc",
    )


def _is_automation_enabled() -> bool:
    """Return True if the automation_enabled flag is set in HD Settings."""
    return bool(frappe.db.get_single_value("HD Settings", "automation_enabled"))
