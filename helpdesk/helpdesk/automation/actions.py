# Copyright (c) 2026, Frappe Technologies Pvt. Ltd. and contributors
# For license information, please see license.txt

"""Action executors for HD Automation Rules.

Supported action types:
    assign_to_agent   - Set ticket assignee (via Frappe assignment API)
    assign_to_team    - Set ticket agent_group (team) field
    set_priority      - Set ticket priority field
    set_status        - Set ticket status field
    add_tag           - Add a tag to the ticket
    add_internal_note - Create an internal HD Ticket Comment
"""

import frappe
from frappe import _


class ActionExecutor:
    """Executes a list of actions against an HD Ticket document."""

    # Map action type -> handler method name
    _HANDLERS = {
        "assign_to_agent": "_action_assign_to_agent",
        "assign_to_team": "_action_assign_to_team",
        "set_priority": "_action_set_priority",
        "set_status": "_action_set_status",
        "add_tag": "_action_add_tag",
        "add_internal_note": "_action_add_internal_note",
    }

    def execute(self, ticket, actions_raw) -> list[dict]:
        """Execute all actions in order.

        Args:
            ticket: HD Ticket frappe.Document.
            actions_raw: List of action dicts or JSON string.

        Returns:
            List of result dicts — one per action — with keys:
                type (str), success (bool), error (str|None).
        """
        import json

        if isinstance(actions_raw, str):
            try:
                actions = json.loads(actions_raw)
            except (json.JSONDecodeError, TypeError):
                frappe.log_error(
                    title="AutomationRule: invalid actions JSON",
                    message=str(actions_raw),
                )
                return []
        else:
            actions = actions_raw or []

        results = []
        for action in actions:
            if not isinstance(action, dict):
                continue
            action_type = action.get("type", "")
            result = self._dispatch(ticket, action_type, action)
            results.append(result)
        return results

    def _dispatch(self, ticket, action_type: str, action: dict) -> dict:
        """Dispatch to the appropriate handler method."""
        handler_name = self._HANDLERS.get(action_type)
        if not handler_name:
            msg = f"Unknown action type: '{action_type}'"
            frappe.log_error(title="AutomationRule: unknown action", message=msg)
            return {"type": action_type, "success": False, "error": msg}

        handler = getattr(self, handler_name)
        try:
            handler(ticket, action)
            return {"type": action_type, "success": True, "error": None}
        except Exception as e:
            frappe.log_error(
                title=f"AutomationRule: action '{action_type}' failed",
                message=frappe.get_traceback(),
            )
            return {"type": action_type, "success": False, "error": str(e)}

    # ------------------------------------------------------------------ #
    # Action handlers                                                       #
    # ------------------------------------------------------------------ #

    def _action_assign_to_agent(self, ticket, action: dict):
        """Assign the ticket to a specific agent (user email)."""
        agent = action.get("value")
        if not agent:
            frappe.throw(_("assign_to_agent: 'value' must be a user email."))
        from frappe.desk.form.assign_to import add as frappe_assign

        frappe_assign(
            {
                "assign_to": [agent],
                "doctype": "HD Ticket",
                "name": ticket.name,
                "bulk_assign": True,
            }
        )

    def _action_assign_to_team(self, ticket, action: dict):
        """Set the team (agent_group) field on the ticket."""
        team = action.get("value")
        if not team:
            frappe.throw(_("assign_to_team: 'value' must be a team name."))
        frappe.db.set_value("HD Ticket", ticket.name, "agent_group", team)

    def _action_set_priority(self, ticket, action: dict):
        """Set the priority field on the ticket."""
        priority = action.get("value")
        if not priority:
            frappe.throw(_("set_priority: 'value' must be a priority name."))
        frappe.db.set_value("HD Ticket", ticket.name, "priority", priority)

    def _action_set_status(self, ticket, action: dict):
        """Set the status field on the ticket."""
        status = action.get("value")
        if not status:
            frappe.throw(_("set_status: 'value' must be a status name."))
        frappe.db.set_value("HD Ticket", ticket.name, "status", status)

    def _action_add_tag(self, ticket, action: dict):
        """Add a tag to the ticket document."""
        tag = action.get("value")
        if not tag:
            frappe.throw(_("add_tag: 'value' must be a tag string."))
        frappe.get_doc("HD Ticket", ticket.name).add_tag(tag)

    def _action_add_internal_note(self, ticket, action: dict):
        """Create an internal note (HD Ticket Comment) on the ticket."""
        note_content = action.get("value", "")
        if not note_content:
            frappe.throw(_("add_internal_note: 'value' must be the note content."))
        frappe.get_doc(
            {
                "doctype": "HD Ticket Comment",
                "reference_ticket": ticket.name,
                "content": note_content,
                "commented_by": frappe.session.user,
                "is_internal": 1,
            }
        ).insert(ignore_permissions=True)
