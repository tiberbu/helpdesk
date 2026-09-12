"""Internal ticket services for the signed plugin RPCs; not public endpoints."""

from html import escape

import frappe
from frappe.utils import strip_html

from helpdesk.api import location
from helpdesk.helpdesk.doctype.hd_ticket import api as ticket_api
from helpdesk.utils import is_agent

TICKET_FIELDS = [
    "name",
    "subject",
    "status",
    "priority",
    "ticket_type",
    "county",
    "sub_county",
    "facility",
    "agent_group",
    "creation",
    "modified",
    "raised_by",
]


def _user():
    if frappe.session.user == "Guest":
        frappe.throw("Sign in to Helpdesk first.", frappe.AuthenticationError)
    return frappe.session.user


def _result(data):
    return {"api_version": 1, "data": data}


def _ticket(ticket_id):
    user = _user()
    doc = frappe.get_doc("HD Ticket", ticket_id)
    doc.check_permission("read")
    if not is_agent() and doc.raised_by != user:
        frappe.throw("You can only access tickets you raised.", frappe.PermissionError)
    return doc


def _page(offset, limit):
    try:
        offset, limit = int(offset), int(limit)
    except (ValueError, TypeError):
        frappe.throw("offset and limit must be integers.")
    if offset < 0 or not 1 <= limit <= 100:
        frappe.throw("offset must be nonnegative; limit must be between 1 and 100.")
    return offset, limit


def _text(value, label, maximum):
    if not isinstance(value, str) or not value.strip() or len(value) > maximum:
        frappe.throw(f"{label} must contain 1-{maximum} characters.")
    return value.strip()


def _link(doctype, name):
    if not name:
        frappe.throw(f"{doctype} is required.")
    if not frappe.get_list(
        doctype, filters={"name": name}, fields=["name"], limit_page_length=1
    ):
        frappe.throw(f"Invalid or inaccessible {doctype}.")


def get_bootstrap():
    user = _user()
    return _result(
        {
            "user_id": user,
            "is_agent": bool(is_agent()),
            "priorities": frappe.get_list(
                "HD Ticket Priority",
                fields=["name"],
                order_by="integer_value asc",
                limit_page_length=100,
            ),
            "ticket_types": frappe.get_list(
                "HD Ticket Type",
                filters={"disabled": 0},
                fields=["name"],
                limit_page_length=100,
            ),
            "statuses": frappe.get_list(
                "HD Ticket Status", fields=["name"], limit_page_length=100
            ),
            "capabilities": {
                "ticket_messages": True,
                "attachments": False,
                "typing": False,
                "read_receipts": False,
                "push_notifications": False,
            },
            "thread_poll_seconds": 10,
            "site_timezone": frappe.db.get_single_value("System Settings", "time_zone"),
        }
    )


def get_counties():
    _user()
    return _result(
        {
            "items": frappe.get_list(
                "HD County",
                fields=["name", "county_name"],
                order_by="county_name asc",
                limit_page_length=100,
            )
        }
    )


def get_subcounties(county):
    _user()
    _link("HD County", county)
    return _result(
        {
            "items": frappe.get_list(
                "HD Subcounty",
                filters={"county": county},
                fields=["name", "subcounty_name", "county"],
                order_by="subcounty_name asc",
                limit_page_length=500,
            )
        }
    )


def get_facilities(county=None, sub_county=None, offset=0, limit=50):
    _user()
    offset, limit = _page(offset, limit)
    # Reuse the existing public facility catalogue; customers lack DocType read permission.
    rows = [
        {**r, "subcounty": r["sub_county"]}
        for r in location.get_facilities()
        if (not county or r["county"] == county)
        and (not sub_county or r["sub_county"] == sub_county)
    ]
    rows.sort(key=lambda r: r["name"])
    rows = rows[offset : offset + limit + 1]
    return _result(
        {
            "items": rows[:limit],
            "has_more": len(rows) > limit,
            "next_offset": offset + limit if len(rows) > limit else None,
        }
    )


def get_thread(ticket_id, offset=0, limit=50):
    doc = _ticket(ticket_id)
    offset, limit = _page(offset, limit)
    events = []
    for c in ticket_api.get_comments(doc.name):
        if c.is_internal:
            continue
        events.append(
            {
                "id": "comment:" + c.name,
                "kind": "message",
                "author": c.commented_by,
                "created_at": str(c.creation),
                "content_html": c.content,
                "content_text": strip_html(c.content or ""),
            }
        )
    for c in ticket_api.get_communications(doc.name):
        events.append(
            {
                "id": "communication:" + c.name,
                "kind": "reply",
                "author": c.sender,
                "created_at": str(c.creation),
                "content_html": c.content,
                "content_text": strip_html(c.content or ""),
            }
        )
    for h in ticket_api.get_history(doc.name):
        events.append(
            {
                "id": "activity:" + h.name,
                "kind": "activity",
                "author": h.owner,
                "created_at": str(h.creation),
                "content_text": strip_html(h.action or ""),
            }
        )
    events.sort(key=lambda row: (row["created_at"], row["id"]))
    more = len(events) > offset + limit
    return _result(
        {
            "items": events[offset : offset + limit],
            "has_more": more,
            "next_offset": offset + limit if more else None,
        }
    )


def send_message(ticket_id, content):
    doc = _ticket(ticket_id)
    content = _text(content, "content", 10000)
    # Existing controller preserves public-note notifications and realtime events.
    doc.new_comment(escape(content).replace("\n", "<br>"))
    return _result({"ticket_id": doc.name, "accepted": True})
