# Copyright (c) 2026, Frappe Technologies Pvt. Ltd. and contributors
# For license information, please see license.txt

"""SLA monitor cron job — fires sla_warning and sla_breached automation triggers.

Scheduled to run every 5 minutes via hooks.py scheduler_events:
    "*/5 * * * *": ["helpdesk.helpdesk.doctype.hd_service_level_agreement.sla_monitor.check_sla_breaches"]

For each open ticket with a resolution_by deadline:
  - If time-to-breach is within a warning threshold (and hasn't fired yet this cycle):
      1. Notify the assigned agent in-app via Socket.IO (sla_warning room event).
      2. Invoke AutomationEngine.evaluate(ticket, "sla_warning") so matching rules execute.
  - If the deadline has already passed:
      1. Invoke AutomationEngine.evaluate(ticket, "sla_breached") (fires once per breach).

Deduplication uses Redis so each threshold fires exactly once per SLA cycle:
    Key: sla:warned:{ticket_name}:{threshold_minutes}  TTL: 24 h
    Key: sla:breached:{ticket_name}                     TTL: 24 h
"""

import json

import frappe
from frappe.utils import now_datetime

# Redis TTL for "already fired" deduplication keys (24 hours)
_DEDUP_TTL_SECONDS = 86400

# Default thresholds (minutes before breach) used when HD Settings value is missing
_DEFAULT_THRESHOLDS = [30, 15, 5]


def check_sla_breaches():
    """Entry point called by the scheduler every 5 minutes.

    Scans all open tickets that have a resolution_by deadline set and fires
    sla_warning / sla_breached automation triggers as appropriate.
    """
    try:
        thresholds = _get_warning_thresholds()
        tickets = _get_at_risk_tickets()
        now = now_datetime()

        for ticket_row in tickets:
            ticket_name = ticket_row["name"]
            resolution_by = ticket_row.get("resolution_by")
            assigned_to = ticket_row.get("_assign") or ticket_row.get("assigned_to") or ""

            if not resolution_by:
                continue

            # Normalize to datetime if stored as string
            if isinstance(resolution_by, str):
                from frappe.utils import get_datetime
                resolution_by = get_datetime(resolution_by)

            minutes_remaining = (resolution_by - now).total_seconds() / 60

            if minutes_remaining <= 0:
                # SLA already breached
                _fire_breached(ticket_name, assigned_to)
            else:
                # Check each warning threshold
                for threshold in thresholds:
                    if minutes_remaining <= threshold:
                        _fire_warning(ticket_name, assigned_to, threshold, minutes_remaining, resolution_by)

    except Exception:
        frappe.log_error(
            title="SLA Monitor: unexpected error in check_sla_breaches",
            message=frappe.get_traceback(),
        )


# ------------------------------------------------------------------ #
# Trigger dispatchers                                                   #
# ------------------------------------------------------------------ #


def _fire_warning(ticket_name: str, assigned_to: str, threshold: int,
                  minutes_remaining: float, resolution_by):
    """Fire sla_warning for a specific threshold if not already fired this cycle."""
    dedup_key = f"sla:warned:{ticket_name}:{threshold}"
    if frappe.cache().get_value(dedup_key):
        return  # Already fired for this threshold in this cycle

    # Mark as fired before doing anything (prevents double-fire on errors)
    frappe.cache().set_value(dedup_key, 1, expires_in_sec=_DEDUP_TTL_SECONDS)

    # 1. Deliver in-app notification to the assigned agent
    try:
        from helpdesk.helpdesk.automation.notifications import notify_agent_sla_warning
        notify_agent_sla_warning(
            ticket_name=ticket_name,
            assigned_to=assigned_to,
            threshold_minutes=threshold,
            minutes_remaining=minutes_remaining,
            resolution_by=resolution_by,
        )
    except Exception:
        frappe.log_error(
            title=f"SLA Monitor: notification failed for {ticket_name}",
            message=frappe.get_traceback(),
        )

    # 2. Invoke automation engine — isolated so failures never block notifications
    try:
        ticket_doc = frappe.get_doc("HD Ticket", ticket_name)
        from helpdesk.helpdesk.automation.engine import evaluate
        evaluate(ticket_doc, "sla_warning")
    except Exception:
        frappe.log_error(
            title=f"SLA Monitor: automation eval failed for {ticket_name} sla_warning",
            message=frappe.get_traceback(),
        )


def _fire_breached(ticket_name: str, assigned_to: str):
    """Fire sla_breached once per breach cycle."""
    dedup_key = f"sla:breached:{ticket_name}"
    if frappe.cache().get_value(dedup_key):
        return  # Already fired for this breach cycle

    frappe.cache().set_value(dedup_key, 1, expires_in_sec=_DEDUP_TTL_SECONDS)

    try:
        ticket_doc = frappe.get_doc("HD Ticket", ticket_name)
        from helpdesk.helpdesk.automation.engine import evaluate
        evaluate(ticket_doc, "sla_breached")
    except Exception:
        frappe.log_error(
            title=f"SLA Monitor: automation eval failed for {ticket_name} sla_breached",
            message=frappe.get_traceback(),
        )


# ------------------------------------------------------------------ #
# Helpers                                                               #
# ------------------------------------------------------------------ #


def _get_warning_thresholds() -> list[int]:
    """Read configurable warning thresholds from HD Settings.

    Returns a sorted (descending) list of int minutes so we check the largest
    threshold first — important so the highest threshold fires before smaller
    ones when a ticket skips multiple thresholds between cron runs.

    Falls back to _DEFAULT_THRESHOLDS if the field is missing or invalid.
    """
    raw = frappe.db.get_single_value("HD Settings", "sla_warning_thresholds")
    if raw:
        try:
            parsed = json.loads(raw) if isinstance(raw, str) else raw
            if isinstance(parsed, list) and parsed:
                return sorted([int(t) for t in parsed], reverse=True)
        except (json.JSONDecodeError, TypeError, ValueError):
            pass
    return sorted(_DEFAULT_THRESHOLDS, reverse=True)


def _get_at_risk_tickets() -> list[dict]:
    """Return all open tickets that have a resolution_by deadline.

    Only non-resolved, non-closed tickets are considered — resolved tickets
    have already met (or are past) their SLA.
    """
    # Fetch tickets with resolution_by set and status not Resolved/Closed
    QBTicket = frappe.qb.DocType("HD Ticket")
    QBStatus = frappe.qb.DocType("HD Ticket Status")

    rows = (
        frappe.qb.from_(QBTicket)
        .join(QBStatus)
        .on(QBTicket.status == QBStatus.name)
        .select(
            QBTicket.name,
            QBTicket.resolution_by,
            QBTicket._assign,
        )
        .where(QBTicket.resolution_by.isnotnull())
        .where(QBStatus.category.notin(["Resolved", "Paused"]))
    ).run(as_dict=True)

    return rows


def clear_warning_dedup(ticket_name: str):
    """Clear all warning deduplication keys for a ticket.

    Called when a ticket's SLA is reset (e.g. re-opened, SLA policy changed)
    so that warnings fire again for the new SLA cycle.

    Args:
        ticket_name: HD Ticket document name.
    """
    thresholds = _get_warning_thresholds()
    cache = frappe.cache()
    for threshold in thresholds:
        cache.delete_value(f"sla:warned:{ticket_name}:{threshold}")
    cache.delete_value(f"sla:breached:{ticket_name}")
