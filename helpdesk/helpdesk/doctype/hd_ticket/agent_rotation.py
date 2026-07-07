# Copyright (c) 2026, Frappe Technologies Pvt. Ltd. and contributors
# For license information, please see license.txt

"""
Agent Rotation — post-breach ticket hand-off within a team.

When a ticket's SLA is breached and the assigned agent has not worked on it,
this module rotates the ticket to the next available agent in the same team.
Each agent gets one chance; once all team members have been tried without
resolving the ticket, it escalates to the parent team (senior devs).

Rotation cycle per agent is controlled by HD Settings.agent_rotation_minutes
(default: 30 minutes of inactivity after breach before passing to the next agent).

Scheduler entry (hooks.py):
    "*/5 * * * *": ["...agent_rotation.run_agent_rotation"]

Notification matrix
-------------------
Event                   | Recipient        | Channel
------------------------|------------------|---------------------------
Breach detected         | Current agent    | In-app bell + realtime
Passed to next agent    | Previous agent   | In-app bell (you breached)
Received from breach    | Incoming agent   | In-app bell (prev breached)
All agents exhausted    | Senior team      | In-app bell (standard assignment)

Deduplication
-------------
Redis key: hdrot:rotated:{ticket}  TTL: 24h  — set after each rotation so the
cron does not rotate the same ticket twice in one 5-minute window.
Redis key: hdrot:exhausted:{ticket} TTL: 7d — set when all agents are tried
so we don't re-enter the rotation loop even across cron restarts.
"""

import json

import frappe
from frappe import _
from frappe.utils import now_datetime, add_to_date

# Minutes of inactivity (after breach) before passing to the next agent
_DEFAULT_ROTATION_MINUTES = 30

# Redis TTL constants
_ROTATION_DEDUP_TTL = 86400   # 24 h — prevents double-rotation in same window
_EXHAUSTED_TTL = 604800       # 7 days — prevents re-entering after exhaustion


# ---------------------------------------------------------------------------
# Public entry point (called by scheduler every 5 minutes)
# ---------------------------------------------------------------------------


def run_agent_rotation() -> None:
    """Find breached tickets where the assigned agent is idle and rotate them."""
    try:
        candidates = _find_rotation_candidates()
        for ticket_name in candidates:
            frappe.enqueue(
                "helpdesk.helpdesk.doctype.hd_ticket.agent_rotation._rotate_single",
                queue="short",
                ticket_name=ticket_name,
                job_id=f"agent_rotation_{ticket_name}",
                deduplicate=True,
            )
    except Exception:
        frappe.log_error(
            title="Agent Rotation: unexpected error in run_agent_rotation",
            message=frappe.get_traceback(),
        )


# ---------------------------------------------------------------------------
# Core rotation logic
# ---------------------------------------------------------------------------


def _rotate_single(ticket_name: str) -> None:
    """Rotate a single ticket to the next agent. Runs as a background job."""
    try:
        # Guard: skip if already rotated this window
        if frappe.cache().get_value(f"hdrot:rotated:{ticket_name}"):
            return
        # Guard: skip if exhaustion already handled
        if frappe.cache().get_value(f"hdrot:exhausted:{ticket_name}"):
            return

        frappe.set_user("Administrator")
        doc = frappe.get_doc("HD Ticket", ticket_name)

        # Re-validate: ticket must still be breached and open
        if doc.agreement_status != "Failed":
            return
        if doc.status in ("Resolved", "Closed", "Duplicate"):
            return

        current_agent = _get_current_agent(doc)
        team_name = doc.agent_group

        if not team_name:
            return  # No team — nothing to rotate within

        # Load all team members (ordered by how they appear in the team)
        team_members = _get_team_members(team_name)
        if not team_members:
            return

        # Load the rotation trail for this ticket
        rotation_path = _load_rotation_path(doc)
        tried_agents = {entry["agent"] for entry in rotation_path}

        # Determine next agent: first team member not yet tried
        next_agent = _pick_next_agent(team_members, tried_agents, current_agent)

        if next_agent:
            _do_rotation(doc, current_agent, next_agent, rotation_path)
        else:
            # All team members tried — escalate to senior devs
            _escalate_to_senior(doc, rotation_path)

        frappe.db.commit()  # nosemgrep

    except Exception:
        frappe.log_error(
            title=f"Agent Rotation: failed for ticket {ticket_name}",
            message=frappe.get_traceback(),
        )


def _do_rotation(doc, current_agent: str, next_agent: str, rotation_path: list) -> None:
    """
    Hand the ticket from current_agent to next_agent.

    1. Notify current agent that they breached and the ticket is being passed.
    2. Record current agent in rotation_path.
    3. Re-assign the ticket to next_agent.
    4. Notify next_agent that they received the ticket due to previous breach.
    5. Set rotation dedup key.
    """
    ticket_name = str(doc.name)
    now = now_datetime()
    subject = doc.subject or ticket_name

    # 1. Notify outgoing agent: "you breached, ticket passed on"
    if current_agent and "@" in current_agent:
        _notify_agent_breached_and_passed(
            agent_email=current_agent,
            ticket_name=ticket_name,
            subject=subject,
            next_agent=next_agent,
        )

    # 2. Record current agent as tried
    rotation_path.append({
        "agent": current_agent or "",
        "assigned_at": str(frappe.db.get_value("HD Ticket", ticket_name, "modified") or now),
        "passed_at": str(now),
        "reason": "SLA breached with no activity",
    })
    _save_rotation_path(doc, rotation_path)

    # 3. Clear existing assignment and assign to next agent
    _reassign_ticket(doc, next_agent)

    # 4. Notify incoming agent: "assigned because previous agent breached"
    _notify_agent_received_from_breach(
        agent_email=next_agent,
        ticket_name=ticket_name,
        subject=subject,
        previous_agent=current_agent or "previous agent",
    )

    # 5. Set dedup key — prevents this ticket being rotated again this window
    frappe.cache().set_value(
        f"hdrot:rotated:{ticket_name}", 1, expires_in_sec=_ROTATION_DEDUP_TTL
    )

    # 6. Internal audit note
    _add_internal_note(
        ticket=ticket_name,
        content=_("Ticket rotated from {0} to {1} due to SLA breach with no activity.").format(
            current_agent or "unassigned", next_agent
        ),
    )


def _escalate_to_senior(doc, rotation_path: list) -> None:
    """
    All team members have been tried — escalate to parent team (senior devs).

    Uses the existing _perform_escalation helper to keep audit trail consistent.
    """
    ticket_name = str(doc.name)

    # Mark exhausted so we don't re-enter this loop
    frappe.cache().set_value(
        f"hdrot:exhausted:{ticket_name}", 1, expires_in_sec=_EXHAUSTED_TTL
    )

    # Persist exhaustion flag in rotation_path too (for human audit)
    rotation_path.append({
        "agent": "__exhausted__",
        "at": str(now_datetime()),
        "reason": "All team members tried — escalating to senior team",
    })
    _save_rotation_path(doc, rotation_path)

    # Try escalation via the existing support-level hierarchy
    try:
        from helpdesk.api.escalation import _resolve_escalation_targets, _perform_escalation
        from_level_name, from_team, to_level, to_team = _resolve_escalation_targets(doc)
        _perform_escalation(
            doc=doc,
            from_level_name=from_level_name,
            to_level=to_level,
            from_team=from_team,
            to_team=to_team,
            reason=_(
                "Auto-escalated: all agents in team '{0}' were tried but none resolved "
                "the ticket before SLA breach."
            ).format(doc.agent_group),
            by="system",
            auto=True,
        )
    except frappe.ValidationError:
        # No parent team / no next level — fall back to notifying current team members
        # so the ticket is not silently dropped.
        _notify_team_exhaustion_fallback(doc)

    _add_internal_note(
        ticket=ticket_name,
        content=_(
            "All agents in team '{0}' were tried without resolving the ticket. "
            "Escalated to senior team."
        ).format(doc.agent_group or "unknown"),
    )


# ---------------------------------------------------------------------------
# Candidate discovery
# ---------------------------------------------------------------------------


def _find_rotation_candidates() -> list:
    """
    Return ticket names that are:
    - agreement_status = "Failed" (SLA breached)
    - Status is not Resolved/Closed/Duplicate
    - Assigned to a team
    - Not already in the exhausted dedup set
    - Last agent activity is more than rotation_minutes ago (agent hasn't worked on it)
    """
    rotation_minutes = _get_rotation_minutes()
    cutoff = add_to_date(now_datetime(), minutes=-rotation_minutes)

    rows = frappe.get_all(
        "HD Ticket",
        filters={
            "agreement_status": "Failed",
            "status": ["not in", ["Resolved", "Closed", "Duplicate"]],
            "agent_group": ["is", "set"],
        },
        or_filters=[
            ["last_agent_response", "<", cutoff],
            ["last_agent_response", "is", "not set"],
        ],
        fields=["name"],
    )

    candidates = []
    for row in rows:
        name = row["name"]
        # Skip tickets already rotated this window or fully exhausted
        if frappe.cache().get_value(f"hdrot:rotated:{name}"):
            continue
        if frappe.cache().get_value(f"hdrot:exhausted:{name}"):
            continue
        candidates.append(name)

    return candidates


# ---------------------------------------------------------------------------
# Notification helpers
# ---------------------------------------------------------------------------


def _notify_agent_breached_and_passed(
    agent_email: str, ticket_name: str, subject: str, next_agent: str
) -> None:
    """Tell the outgoing agent their SLA breached and the ticket has been passed."""
    try:
        msg = _(
            "SLA Breached — Ticket #{0} ({1}) has been passed to {2} because the "
            "SLA deadline was exceeded with no activity from you."
        ).format(ticket_name, subject, next_agent)

        from helpdesk.helpdesk.doctype.hd_notification.utils import create_notification
        create_notification(
            user_to=agent_email,
            notification_type="SLA Breach",
            message=msg,
            reference_ticket=ticket_name,
        )
        frappe.publish_realtime(
            event="sla_breached",
            message={"ticket": ticket_name, "subject": subject, "passed_to": next_agent},
            user=agent_email,
        )
    except Exception:
        frappe.log_error(frappe.get_traceback(), f"AgentRotation: breach+pass notify failed for {agent_email}")


def _notify_agent_received_from_breach(
    agent_email: str, ticket_name: str, subject: str, previous_agent: str
) -> None:
    """Tell the incoming agent why this ticket landed with them."""
    try:
        msg = _(
            "Ticket #{0} ({1}) has been assigned to you because {2} breached the SLA "
            "without resolving it. Please action this ticket urgently."
        ).format(ticket_name, subject, previous_agent)

        from helpdesk.helpdesk.doctype.hd_notification.utils import create_notification
        create_notification(
            user_to=agent_email,
            notification_type="Assignment",
            message=msg,
            reference_ticket=ticket_name,
        )
        frappe.publish_realtime(
            event="helpdesk:new-notification",
            message={"ticket": ticket_name, "subject": subject},
            user=agent_email,
        )
    except Exception:
        frappe.log_error(frappe.get_traceback(), f"AgentRotation: received-from-breach notify failed for {agent_email}")


def _notify_team_exhaustion_fallback(doc) -> None:
    """
    Fallback when no parent team exists: notify all current team members
    so the ticket is not silently dropped.
    """
    try:
        ticket_name = str(doc.name)
        subject = doc.subject or ticket_name
        members = frappe.get_all(
            "HD Team Member",
            filters={"parent": doc.agent_group, "parenttype": "HD Team"},
            pluck="user",
        )
        msg = _(
            "URGENT: Ticket #{0} ({1}) has been through all agents in team '{2}' "
            "without resolution. No escalation path is configured — please handle immediately."
        ).format(ticket_name, subject, doc.agent_group)

        from helpdesk.helpdesk.doctype.hd_notification.utils import create_notification
        for user_email in members:
            create_notification(
                user_to=user_email,
                notification_type="Escalation",
                message=msg,
                reference_ticket=ticket_name,
            )
    except Exception:
        frappe.log_error(frappe.get_traceback(), f"AgentRotation: exhaustion fallback notify failed for {doc.name}")


# ---------------------------------------------------------------------------
# Assignment helper
# ---------------------------------------------------------------------------


def _reassign_ticket(doc, new_agent_email: str) -> None:
    """Clear all current assignments and assign to new_agent_email."""
    from frappe.desk.form.assign_to import add as assign_to_add
    from frappe.desk.form.assign_to import clear as clear_assignments

    ticket_name = str(doc.name)

    # Clear existing assignments
    try:
        clear_assignments("HD Ticket", ticket_name)
    except Exception:
        frappe.log_error(frappe.get_traceback(), f"AgentRotation: clear assignments failed for {ticket_name}")

    # Assign to the new agent
    try:
        assign_to_add({
            "assign_to": [new_agent_email],
            "doctype": "HD Ticket",
            "name": ticket_name,
        })
    except Exception:
        frappe.log_error(frappe.get_traceback(), f"AgentRotation: assign to {new_agent_email} failed for {ticket_name}")


# ---------------------------------------------------------------------------
# Team / agent helpers
# ---------------------------------------------------------------------------


def _get_team_members(team_name: str) -> list:
    """Return list of user emails for all members of the given HD Team."""
    return frappe.get_all(
        "HD Team Member",
        filters={"parent": team_name, "parenttype": "HD Team"},
        pluck="user",
    )


def _get_current_agent(doc) -> str:
    """Extract the currently assigned agent email from the ticket's _assign field."""
    raw = getattr(doc, "_assign", None) or ""
    if isinstance(raw, str) and raw.strip().startswith("["):
        try:
            parsed = json.loads(raw)
            if isinstance(parsed, list) and parsed:
                return str(parsed[0]).strip()
        except (ValueError, TypeError):
            pass
    if isinstance(raw, str) and "@" in raw:
        return raw.strip()
    return ""


def _pick_next_agent(team_members: list, tried_agents: set, current_agent: str) -> str:
    """
    Return the first team member email not in tried_agents and not current_agent.
    Returns empty string if all members have been tried.
    """
    for member in team_members:
        if member not in tried_agents and member != current_agent:
            return member
    return ""


# ---------------------------------------------------------------------------
# Rotation path (JSON audit trail on ticket)
# ---------------------------------------------------------------------------


def _load_rotation_path(doc) -> list:
    """Parse agent_rotation_path JSON field; return list (empty if blank/invalid)."""
    raw = getattr(doc, "agent_rotation_path", None) or ""
    if not raw:
        return []
    try:
        return json.loads(raw)
    except (ValueError, TypeError):
        return []


def _save_rotation_path(doc, path: list) -> None:
    """Persist agent_rotation_path JSON to the ticket without full validation."""
    frappe.db.set_value(
        "HD Ticket",
        doc.name,
        "agent_rotation_path",
        json.dumps(path, default=str),
        update_modified=False,
    )


# ---------------------------------------------------------------------------
# Internal note
# ---------------------------------------------------------------------------


def _add_internal_note(ticket: str, content: str) -> None:
    """Insert an internal HD Ticket Comment for audit purposes."""
    try:
        frappe.get_doc({
            "doctype": "HD Ticket Comment",
            "reference_ticket": ticket,
            "commented_by": "Administrator",
            "content": content,
            "is_internal": 1,
            "is_pinned": 0,
        }).insert(ignore_permissions=True)
    except Exception:
        frappe.log_error(frappe.get_traceback(), f"AgentRotation: add internal note failed for {ticket}")


# ---------------------------------------------------------------------------
# Settings
# ---------------------------------------------------------------------------


def _get_rotation_minutes() -> int:
    """Read agent_rotation_minutes from HD Settings, default 30."""
    raw = frappe.db.get_single_value("HD Settings", "agent_rotation_minutes")
    if raw is not None:
        try:
            val = int(raw)
            return val if val > 0 else _DEFAULT_ROTATION_MINUTES
        except (TypeError, ValueError):
            pass
    return _DEFAULT_ROTATION_MINUTES
