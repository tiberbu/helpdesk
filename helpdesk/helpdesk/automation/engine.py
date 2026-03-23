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

import time

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
    trigger_types = resolve_trigger_type(doc, frappe_event)
    for trigger_type in trigger_types:
        evaluate(doc, trigger_type)


def evaluate(ticket, trigger_type: str, dry_run: bool = False, rule_name: str | None = None):
    """Evaluate all enabled rules for a trigger type against a ticket.

    Rules are fetched in ascending priority_order (lower = higher priority)
    in a single DB call (NFR-P-06 performance requirement).

    When dry_run=True and rule_name is provided, evaluates only that rule and
    returns a structured dict of condition/action results without executing
    any actions.

    Args:
        ticket: HD Ticket frappe.Document or frappe._dict.
        trigger_type: One of the TRIGGER_TYPES constants.
        dry_run: If True, evaluate without executing actions and return details.
        rule_name: When dry_run=True, the specific rule to evaluate.

    Returns:
        None for normal mode; dict with evaluation details for dry_run mode.
    """
    # AC #12: honour the automation_enabled feature flag
    if not _is_automation_enabled():
        if dry_run:
            return {"would_fire": False, "conditions_detail": [], "actions_detail": [], "blocked": "automation_disabled"}
        return

    if dry_run and rule_name:
        rule = _fetch_single_rule(rule_name)
        if not rule:
            return {"would_fire": False, "conditions_detail": [], "actions_detail": [], "blocked": "rule_not_found"}
        return _dry_run_rule(ticket, rule)

    rules = _fetch_rules(trigger_type)
    if not rules:
        return

    ticket_name = str(ticket.name)

    # AC #4: per-ticket loop guard (checked once before processing this batch)
    if not _safety_guard.check_loop(ticket_name):
        return

    for rule in rules:
        _evaluate_rule(ticket, rule, trigger_type)


def _evaluate_rule(ticket, rule: dict, trigger_type: str = ""):
    """Evaluate a single rule dict against the ticket."""
    rule_name = rule["name"]
    ticket_name = getattr(ticket, "name", None)
    conditions = rule.get("conditions") or "[]"
    actions = rule.get("actions") or "[]"

    start = time.monotonic()

    # Evaluate conditions
    if not _condition_evaluator.evaluate(ticket, conditions):
        return  # Conditions did not match; skip this rule

    # Execute actions
    results = _action_executor.execute(ticket, actions)
    elapsed_ms = int((time.monotonic() - start) * 1000)

    # Track success / failure for auto-disable
    had_failure = any(not r.get("success") for r in results)
    if had_failure:
        error_parts = [r.get("error", "") for r in results if not r.get("success")]
        _create_log(
            rule_name=rule_name,
            ticket=ticket_name,
            trigger_event=trigger_type,
            conditions_evaluated=conditions,
            actions_executed=actions,
            execution_time_ms=elapsed_ms,
            status="failure",
            error_message="; ".join(filter(None, error_parts)),
        )
        _safety_guard.record_failure(rule_name)
    else:
        _create_log(
            rule_name=rule_name,
            ticket=ticket_name,
            trigger_event=trigger_type,
            conditions_evaluated=conditions,
            actions_executed=actions,
            execution_time_ms=elapsed_ms,
            status="success",
        )
        _safety_guard.record_success(rule_name)


def _create_log(
    rule_name: str,
    ticket,
    trigger_event,
    conditions_evaluated,
    actions_executed,
    execution_time_ms: int,
    status: str,
    error_message: str = "",
):
    """Insert an HD Automation Log record.

    Silently swallows all exceptions — logging must never interrupt core
    ticket processing (NFR-A-01).
    """
    try:
        frappe.get_doc(
            {
                "doctype": "HD Automation Log",
                "rule_name": rule_name,
                "ticket": str(ticket) if ticket else None,
                "trigger_event": trigger_event or "",
                "conditions_evaluated": (
                    conditions_evaluated
                    if isinstance(conditions_evaluated, str)
                    else frappe.as_json(conditions_evaluated)
                ),
                "actions_executed": (
                    actions_executed
                    if isinstance(actions_executed, str)
                    else frappe.as_json(actions_executed)
                ),
                "execution_time_ms": execution_time_ms,
                "status": status,
                "error_message": error_message or "",
                "timestamp": frappe.utils.now_datetime(),
            }
        ).insert(ignore_permissions=True)
    except Exception:
        frappe.log_error(
            title="HD Automation Log: insert failed",
            message=frappe.get_traceback(),
        )


def _dry_run_rule(ticket, rule: dict) -> dict:
    """Evaluate a single rule in dry-run mode.

    Returns a structured dict with per-condition match results and per-action
    would-execute flags, without actually executing any actions.

    Args:
        ticket: HD Ticket frappe.Document or frappe._dict.
        rule: Rule dict (from _fetch_single_rule).

    Returns:
        dict with keys: would_fire, conditions_detail, actions_detail.
    """
    import json

    # --- Conditions ---
    conditions_raw = rule.get("conditions") or "[]"
    if isinstance(conditions_raw, str):
        try:
            conditions_list = json.loads(conditions_raw)
        except (json.JSONDecodeError, TypeError):
            conditions_list = []
    else:
        conditions_list = conditions_raw or []

    # Evaluate each condition individually for detailed output
    conditions_detail = []
    for cond in conditions_list:
        if not isinstance(cond, dict):
            continue
        if "conditions" in cond:
            # Nested group — evaluate as a whole
            group_logic = cond.get("logic", "AND").upper()
            group_result = _condition_evaluator.evaluate(ticket, cond["conditions"], logic=group_logic)
            conditions_detail.append({
                "field": "(group)",
                "operator": group_logic,
                "value": None,
                "matched": group_result,
            })
        else:
            matched = _condition_evaluator._evaluate_single(ticket, cond)
            conditions_detail.append({
                "field": cond.get("field"),
                "operator": cond.get("operator"),
                "value": cond.get("value"),
                "matched": matched,
            })

    # Overall: evaluate all conditions together
    overall_match = _condition_evaluator.evaluate(ticket, conditions_raw)

    # --- Actions ---
    actions_raw = rule.get("actions") or "[]"
    if isinstance(actions_raw, str):
        try:
            actions_list = json.loads(actions_raw)
        except (json.JSONDecodeError, TypeError):
            actions_list = []
    else:
        actions_list = actions_raw or []

    actions_detail = []
    for action in actions_list:
        if not isinstance(action, dict):
            continue
        actions_detail.append({
            "type": action.get("type"),
            "value": action.get("value"),
            "would_execute": overall_match,
        })

    return {
        "would_fire": overall_match,
        "conditions_detail": conditions_detail,
        "actions_detail": actions_detail,
    }


def _fetch_single_rule(rule_name: str) -> dict | None:
    """Fetch a single HD Automation Rule by name."""
    results = frappe.get_all(
        "HD Automation Rule",
        filters={"name": rule_name},
        fields=["name", "rule_name", "trigger_type", "conditions", "actions", "priority_order", "enabled"],
    )
    return results[0] if results else None


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
