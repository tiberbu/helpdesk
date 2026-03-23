# Copyright (c) 2026, Frappe Technologies Pvt. Ltd. and contributors
# For license information, please see license.txt

import frappe
from frappe import _
from frappe.utils import now_datetime


@frappe.whitelist()
def start_timer(ticket: str) -> dict:
	"""
	Validate agent has write access to the ticket and return server-side
	start timestamp for the client to store in localStorage.

	Returns: { "started_at": "<ISO datetime string>" }
	"""
	frappe.has_permission("HD Ticket", "write", doc=ticket, throw=True)
	started_at = now_datetime()
	return {"started_at": str(started_at)}


@frappe.whitelist()
def stop_timer(
	ticket: str,
	started_at: str,
	duration_minutes: int,
	description: str = "",
	billable: int = 0,
) -> dict:
	"""
	Create an HD Time Entry from a stopped timer session.

	Returns: { "name": "<entry_name>", "success": True }
	"""
	frappe.has_permission("HD Ticket", "write", doc=ticket, throw=True)

	duration_minutes = int(duration_minutes)
	if duration_minutes < 1:
		frappe.throw(_("Duration must be at least 1 minute."), frappe.ValidationError)

	entry = frappe.get_doc(
		{
			"doctype": "HD Time Entry",
			"ticket": ticket,
			"agent": frappe.session.user,
			"duration_minutes": duration_minutes,
			"billable": int(billable),
			"description": description or "",
			"timestamp": now_datetime(),
			"started_at": started_at,
		}
	)
	entry.insert()

	return {"name": entry.name, "success": True}


@frappe.whitelist()
def add_entry(
	ticket: str,
	duration_minutes: int,
	description: str = "",
	billable: int = 0,
) -> dict:
	"""
	Create an HD Time Entry via manual entry form.

	Returns: { "name": "<entry_name>", "success": True }
	"""
	frappe.has_permission("HD Ticket", "write", doc=ticket, throw=True)

	duration_minutes = int(duration_minutes)
	if duration_minutes < 1:
		frappe.throw(_("Duration must be at least 1 minute."), frappe.ValidationError)

	entry = frappe.get_doc(
		{
			"doctype": "HD Time Entry",
			"ticket": ticket,
			"agent": frappe.session.user,
			"duration_minutes": duration_minutes,
			"billable": int(billable),
			"description": description or "",
			"timestamp": now_datetime(),
		}
	)
	entry.insert()

	return {"name": entry.name, "success": True}


@frappe.whitelist()
def delete_entry(name: str) -> dict:
	"""
	Delete an HD Time Entry.

	Agents may only delete their own entries; HD Admin / System Manager may delete any.

	Returns: { "success": True }
	"""
	entry = frappe.get_doc("HD Time Entry", name)

	is_admin = frappe.db.get_value(
		"Has Role",
		{"parent": frappe.session.user, "role": ["in", ["HD Admin", "System Manager"]]},
		"name",
	)

	if entry.agent != frappe.session.user and not is_admin:
		frappe.throw(_("You can only delete your own time entries."), frappe.PermissionError)

	frappe.delete_doc("HD Time Entry", name)
	return {"success": True}


@frappe.whitelist()
def get_summary(ticket: str) -> dict:
	"""
	Return time summary for a ticket: totals and entry list.

	Returns:
	{
	    "total_minutes": int,
	    "billable_minutes": int,
	    "entries": [
	        {
	            "name": str,
	            "agent": str,
	            "agent_name": str,
	            "duration_minutes": int,
	            "billable": int,
	            "description": str,
	            "timestamp": str
	        },
	        ...
	    ]
	}
	"""
	frappe.has_permission("HD Ticket", "read", doc=ticket, throw=True)

	entries = frappe.get_all(
		"HD Time Entry",
		filters={"ticket": ticket},
		fields=[
			"name",
			"agent",
			"duration_minutes",
			"billable",
			"description",
			"timestamp",
		],
		order_by="timestamp desc",
	)

	# Resolve agent full names
	for entry in entries:
		user = frappe.db.get_value(
			"User", entry["agent"], ["first_name", "last_name"], as_dict=True
		)
		if user:
			last_initial = (user.last_name or "")[:1]
			entry["agent_name"] = (
				f"{user.first_name} {last_initial}." if last_initial else user.first_name
			)
		else:
			entry["agent_name"] = entry["agent"]

	total_minutes = sum(e["duration_minutes"] for e in entries)
	billable_minutes = sum(e["duration_minutes"] for e in entries if e["billable"])

	return {
		"total_minutes": total_minutes,
		"billable_minutes": billable_minutes,
		"entries": entries,
	}
