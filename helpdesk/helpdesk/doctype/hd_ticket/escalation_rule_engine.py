# Copyright (c) 2026, Frappe Technologies Pvt. Ltd. and contributors
# For license information, please see license.txt

"""
Escalation Rule Engine — evaluates HD Escalation Rules against a ticket.

Entry points:
  evaluate_rules(ticket_doc, trigger)  — called from hooks/scheduler
  run_age_based_rules()                — called by cron every 5 min

Triggers:
  ticket_age     — ticket open >= rule.age_hours with no resolution
  sla_breach     — ticket SLA has been breached (agreement_status == Failed)
  priority_match — ticket priority matches rule.match_priority
  status_change  — ticket status changed to rule.target_status

Deduplication:
  Redis key  helpdesk:esc_rule:{rule_name}:{ticket_name}
  TTL        24 hours — prevents the same rule firing twice on the same ticket in a day.
  For ticket_age rules, the TTL is extended to 25 hours so daily re-fires are prevented.
"""

import frappe
from frappe import _
from frappe.utils import now_datetime, add_to_date


# ---------------------------------------------------------------------------
# Public entry points
# ---------------------------------------------------------------------------

def evaluate_rules(ticket_doc, trigger: str) -> None:
    """
    Evaluate all enabled rules with the given trigger against ticket_doc.
    Safe to call from doc hooks — catches all exceptions to avoid breaking saves.
    """
    try:
        rules = _get_enabled_rules(trigger)
        for rule in rules:
            if _matches_conditions(ticket_doc, rule) and not _already_fired(rule.name, ticket_doc.name):
                _fire_rule(rule, ticket_doc, trigger)
                _mark_fired(rule.name, ticket_doc.name)
    except Exception:
        frappe.log_error(frappe.get_traceback(), f"Escalation Rule Engine error [{trigger}] on {getattr(ticket_doc, 'name', '?')}")


def run_age_based_rules() -> None:
    """
    Scheduler entry point (runs every 5 min alongside auto_escalate_tickets).
    Finds open tickets that match ticket_age rules and fires them.
    """
    rules = _get_enabled_rules("ticket_age")
    if not rules:
        return

    for rule in rules:
        age_hours = rule.get("age_hours") or 24
        cutoff = add_to_date(now_datetime(), hours=-age_hours)

        tickets = frappe.get_all(
            "HD Ticket",
            filters={
                "status": ["not in", ["Resolved", "Closed", "Duplicate"]],
                "creation": ["<", cutoff],
            },
            fields=["name", "priority", "agent_group", "ticket_type", "status", "raised_by", "subject"],
        )

        for t in tickets:
            if _already_fired(rule.name, t.name):
                continue
            # Build a lightweight dict-like object for condition matching
            ticket_stub = frappe._dict(t)
            if _matches_conditions(ticket_stub, rule):
                try:
                    ticket_doc = frappe.get_doc("HD Ticket", t.name)
                    frappe.set_user("Administrator")
                    _fire_rule(rule, ticket_doc, "ticket_age")
                    _mark_fired(rule.name, t.name, ttl_hours=25)
                    frappe.db.commit()  # nosemgrep
                except Exception:
                    frappe.log_error(
                        frappe.get_traceback(),
                        f"Age-based escalation rule '{rule.name}' failed for ticket {t.name}",
                    )


# ---------------------------------------------------------------------------
# Condition matching
# ---------------------------------------------------------------------------

def _get_enabled_rules(trigger: str) -> list:
    return frappe.get_all(
        "HD Escalation Rule",
        filters={"is_enabled": 1, "trigger": trigger},
        fields=["name", "rule_name", "trigger", "match_priority", "match_team",
                "match_ticket_type", "match_status", "age_hours", "target_status", "rule_order"],
        order_by="rule_order asc",
    )


def _matches_conditions(ticket, rule) -> bool:
    """Return True if all non-blank conditions on the rule match the ticket."""
    if rule.get("match_priority") and ticket.get("priority") != rule["match_priority"]:
        return False
    if rule.get("match_team") and ticket.get("agent_group") != rule["match_team"]:
        return False
    if rule.get("match_ticket_type") and ticket.get("ticket_type") != rule["match_ticket_type"]:
        return False
    if rule.get("match_status") and ticket.get("status") != rule["match_status"]:
        return False
    return True


# ---------------------------------------------------------------------------
# Action execution
# ---------------------------------------------------------------------------

def _fire_rule(rule, ticket_doc, trigger: str) -> None:
    """Load the full rule doc and execute all its actions."""
    rule_doc = frappe.get_doc("HD Escalation Rule", rule["name"])
    changed = False

    for action in rule_doc.actions_table:
        try:
            _execute_action(action, ticket_doc, rule_doc, trigger)
            changed = True
        except Exception:
            frappe.log_error(
                frappe.get_traceback(),
                f"Escalation action '{action.action_type}' failed for rule '{rule_doc.rule_name}' on ticket {ticket_doc.name}",
            )

    if changed:
        # Always add a system note so there's a traceable audit entry on the ticket
        _add_audit_note(ticket_doc, rule_doc, trigger)


def _execute_action(action, ticket_doc, rule_doc, trigger: str) -> None:
    action_type = action.action_type

    if action_type == "notify_agent":
        _notify_specific_agent(action.notify_agent, ticket_doc, rule_doc)

    elif action_type == "notify_manager":
        _notify_team_manager(ticket_doc, rule_doc)

    elif action_type == "reassign_agent":
        if action.assign_to_agent:
            agent_user = frappe.db.get_value("HD Agent", action.assign_to_agent, "user")
            if agent_user:
                ticket_doc.flags.ignore_permissions = True
                ticket_doc.db_set("assigned_to", agent_user, update_modified=False)

    elif action_type == "reassign_team":
        if action.assign_to_team:
            ticket_doc.flags.ignore_permissions = True
            ticket_doc.db_set("agent_group", action.assign_to_team, update_modified=False)

    elif action_type == "change_priority":
        if action.set_priority:
            old_priority = ticket_doc.priority
            ticket_doc.flags.ignore_permissions = True
            ticket_doc.db_set("priority", action.set_priority, update_modified=False)
            frappe.log_error(
                title=f"Priority changed by escalation rule",
                message=f"Ticket {ticket_doc.name}: {old_priority} → {action.set_priority} by rule '{rule_doc.rule_name}'"
            ) if False else None  # kept as no-op; audit note below handles this

    elif action_type == "add_note":
        content = action.note_content or f"Escalation rule '{rule_doc.rule_name}' fired."
        _insert_internal_note(ticket_doc.name, content)


def _add_audit_note(ticket_doc, rule_doc, trigger: str) -> None:
    """Add a single internal note summarising what the rule did."""
    trigger_labels = {
        "ticket_age": f"open for ≥{rule_doc.get('age_hours', 24)} hours",
        "sla_breach": "SLA breach",
        "priority_match": f"priority matched '{rule_doc.match_priority}'",
        "status_change": f"status changed to '{rule_doc.target_status}'",
    }
    reason = trigger_labels.get(trigger, trigger)
    actions_summary = ", ".join(a.action_type for a in rule_doc.actions_table)
    content = _(
        "Escalation rule <strong>{0}</strong> fired ({1}). Actions: {2}."
    ).format(rule_doc.rule_name, reason, actions_summary)
    _insert_internal_note(ticket_doc.name, content)


# ---------------------------------------------------------------------------
# Notification helpers
# ---------------------------------------------------------------------------

def _notify_specific_agent(agent_name: str, ticket_doc, rule_doc) -> None:
    if not agent_name:
        return
    agent_user = frappe.db.get_value("HD Agent", agent_name, "user")
    if not agent_user:
        return
    message = _("Escalation rule <b>{0}</b> flagged ticket #{1}: {2}").format(
        rule_doc.rule_name, ticket_doc.name, ticket_doc.subject
    )
    # In-app bell notification
    from helpdesk.helpdesk.doctype.hd_notification.utils import create_notification
    create_notification(
        user_to=agent_user,
        notification_type="Escalation",
        message=message,
        reference_ticket=ticket_doc.name,
    )
    # Email
    ticket_url = frappe.utils.get_url(f"/helpdesk/tickets/{ticket_doc.name}")
    frappe.sendmail(
        recipients=[agent_user],
        subject=_("Escalation alert: Ticket #{0}").format(ticket_doc.name),
        message=_(
            "Escalation rule <b>{0}</b> has flagged ticket <b>#{1}</b>: {2}.<br><br>"
            "<a href='{3}'>View Ticket</a>"
        ).format(rule_doc.rule_name, ticket_doc.name, ticket_doc.subject, ticket_url),
        delayed=False,
    )


def _notify_team_manager(ticket_doc, rule_doc) -> None:
    """Notify members of the ticket's assigned team."""
    team = ticket_doc.agent_group
    if not team:
        return
    members = frappe.get_all(
        "HD Team Member",
        filters={"parent": team, "parenttype": "HD Team"},
        pluck="user",
    )
    if not members:
        return
    from helpdesk.helpdesk.doctype.hd_notification.utils import create_notification
    message = _("Escalation rule <b>{0}</b> flagged ticket #{1}: {2}").format(
        rule_doc.rule_name, ticket_doc.name, ticket_doc.subject
    )
    ticket_url = frappe.utils.get_url(f"/helpdesk/tickets/{ticket_doc.name}")
    for user_email in members:
        # In-app bell notification
        create_notification(
            user_to=user_email,
            notification_type="Escalation",
            message=message,
            reference_ticket=ticket_doc.name,
        )
        # Email
        frappe.sendmail(
            recipients=[user_email],
            subject=_("Escalation alert: Ticket #{0}").format(ticket_doc.name),
            message=_(
                "Escalation rule <b>{0}</b> has flagged ticket <b>#{1}</b>: {2}.<br><br>"
                "<a href='{3}'>View Ticket</a>"
            ).format(rule_doc.rule_name, ticket_doc.name, ticket_doc.subject, ticket_url),
            delayed=False,
        )


def _insert_internal_note(ticket_name: str, content: str) -> None:
    frappe.get_doc({
        "doctype": "HD Ticket Comment",
        "reference_ticket": ticket_name,
        "commented_by": frappe.session.user,
        "content": content,
        "is_internal": 1,
        "is_pinned": 0,
    }).insert(ignore_permissions=True)


# ---------------------------------------------------------------------------
# Redis deduplication
# ---------------------------------------------------------------------------

def _redis_key(rule_name: str, ticket_name: str) -> str:
    return f"helpdesk:esc_rule:{rule_name}:{ticket_name}"


def _already_fired(rule_name: str, ticket_name: str) -> bool:
    try:
        return bool(frappe.cache().get(_redis_key(rule_name, ticket_name)))
    except Exception:
        return False


def _mark_fired(rule_name: str, ticket_name: str, ttl_hours: int = 24) -> None:
    try:
        frappe.cache().set_value(
            _redis_key(rule_name, ticket_name),
            1,
            expires_in_sec=ttl_hours * 3600,
        )
    except Exception:
        pass
