# Copyright (c) 2026, Frappe Technologies Pvt. Ltd. and contributors
# For license information, please see license.txt

"""Notification helpers for the automation engine.

Provides in-app (Socket.IO) notifications for SLA-related events so that
agents are alerted when their assigned tickets are approaching or past breach.
"""

import frappe


def notify_agent_sla_warning(
    ticket_name: str,
    assigned_to: str,
    threshold_minutes: int,
    minutes_remaining: float,
    resolution_by,
):
    """Deliver an in-app SLA warning notification to the assigned agent.

    Publishes a Socket.IO event to the ``agent:{email}`` room (Architecture
    Communication Patterns — Socket.IO Room Strategy) so the agent's workspace
    receives a real-time toast/badge update.

    If the ticket has no assigned agent the call is a silent no-op — this is
    intentional; unassigned tickets will be picked up by automation rules
    (e.g. assign_to_team) rather than by direct agent notification.

    Args:
        ticket_name:       HD Ticket document name.
        assigned_to:       Agent email (from _assign field or assigned_to).
                           May be a JSON list string like '["agent@x.com"]'.
        threshold_minutes: The warning threshold that triggered this call (e.g. 30).
        minutes_remaining: Actual minutes left before breach (may be < threshold).
        resolution_by:     SLA deadline datetime object.
    """
    agent_email = _extract_agent_email(assigned_to)
    if not agent_email:
        return  # Unassigned ticket — skip silently

    try:
        # Fetch ticket subject for a useful notification message
        subject = frappe.db.get_value("HD Ticket", ticket_name, "subject") or ticket_name

        payload = {
            "ticket": ticket_name,
            "subject": subject,
            "threshold_minutes": threshold_minutes,
            "minutes_remaining": round(minutes_remaining, 1),
            "sla_deadline": str(resolution_by),
        }

        # Publish to the agent's private Socket.IO room
        frappe.publish_realtime(
            event="sla_warning",
            message=payload,
            room=f"agent:{agent_email}",
        )

    except Exception:
        # Non-critical: log but never raise — notification failure must not
        # interrupt the SLA monitor or automation engine pipeline (NFR-A-01).
        frappe.log_error(
            title=f"SLA Notification: failed for ticket {ticket_name}",
            message=frappe.get_traceback(),
        )


# ------------------------------------------------------------------ #
# Helpers                                                               #
# ------------------------------------------------------------------ #


def _extract_agent_email(assigned_to: str) -> str:
    """Extract a single agent email from the assigned_to / _assign value.

    The HD Ticket ``_assign`` field stores a JSON list of assignee emails,
    e.g. ``'["agent@example.com"]'``.  ``assigned_to`` is a plain Data field
    that may hold a single email.  We handle both formats.

    Returns the first valid email string, or an empty string if none found.
    """
    if not assigned_to:
        return ""

    # Try JSON list first (from _assign field)
    if isinstance(assigned_to, str) and assigned_to.strip().startswith("["):
        try:
            import json
            parsed = json.loads(assigned_to)
            if isinstance(parsed, list) and parsed:
                email = parsed[0]
                return str(email).strip() if email else ""
        except (ValueError, TypeError):
            pass

    # Plain email string
    email = str(assigned_to).strip()
    return email if "@" in email else ""
