# Copyright (c) 2022, Frappe Technologies and contributors
# For license information, please see license.txt

import frappe
from frappe.model.document import Document


class HDTicketActivity(Document):
    pass


def log_ticket_activity(ticket, action):
    return frappe.get_doc(
        {"doctype": "HD Ticket Activity", "ticket": ticket, "action": action}
    ).insert(ignore_permissions=True)


def has_permission(doc, user=None, permission_type=None):
    """Activity access never exceeds access to its parent ticket."""
    if not doc or not doc.get("ticket"):
        return None
    return frappe.has_permission("HD Ticket", "read", doc.ticket, user=user)


def permission_query(user=None):
    from helpdesk.helpdesk.doctype.hd_ticket.hd_ticket import permission_query as ticket_query
    condition = ticket_query(user or frappe.session.user)
    if not condition:
        return ""
    return "`tabHD Ticket Activity`.ticket IN (SELECT `tabHD Ticket`.name FROM `tabHD Ticket` WHERE (" + condition + "))"
