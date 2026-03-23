# Copyright (c) 2026, Frappe Technologies Pvt. Ltd. and contributors
# For license information, please see license.txt

import frappe
from frappe import _
from frappe.utils import now_datetime, get_datetime, cint

from helpdesk.utils import is_agent
from helpdesk.helpdesk.doctype.hd_time_entry.hd_time_entry import (
	MAX_DESCRIPTION_LENGTH,
	MAX_DURATION_MINUTES,
	PRIVILEGED_ROLES,
	_check_delete_permission,
)


@frappe.whitelist()
def start_timer(ticket: str) -> dict:
	"""
	Validate agent has write access to the ticket and return server-side
	start timestamp for the client to store in localStorage.

	Returns: { "started_at": "<ISO datetime string>" }
	"""
	if not is_agent():
		frappe.throw(_("Not permitted"), frappe.PermissionError)
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
	if not is_agent():
		frappe.throw(_("Not permitted"), frappe.PermissionError)
	frappe.has_permission("HD Ticket", "write", doc=ticket, throw=True)

	# Defense-in-depth: validate description length here so callers receive a clear
	# HTTP 417 with a user-facing message before the document is even constructed.
	# HDTimeEntry.validate() also enforces this limit, so both layers are intentional.
	if description and len(description) > MAX_DESCRIPTION_LENGTH:
		frappe.throw(
			_("Description must not exceed {0} characters.").format(MAX_DESCRIPTION_LENGTH),
			frappe.ValidationError,
		)

	# Validate started_at: must be parseable and not in the future
	try:
		started_at_dt = get_datetime(started_at)
	except Exception:
		frappe.throw(_("Invalid started_at datetime format."), frappe.ValidationError)

	# Convert to server local time before stripping tzinfo for correct comparison with
	# now_datetime() (which returns naive local time).
	# Use astimezone(tz=None) rather than convert_utc_to_system_timezone() because the
	# latter contract requires UTC input — started_at may carry any tz offset from the
	# client, so we must let Python perform the proper IANA-aware conversion first.
	if started_at_dt.tzinfo is not None:
		started_at_naive = started_at_dt.astimezone(tz=None).replace(tzinfo=None)
	else:
		started_at_naive = started_at_dt
	if started_at_naive > now_datetime():
		frappe.throw(_("started_at cannot be in the future."), frappe.ValidationError)

	duration_minutes = cint(duration_minutes)
	if duration_minutes < 1:
		frappe.throw(_("Duration must be at least 1 minute."), frappe.ValidationError)
	if duration_minutes > MAX_DURATION_MINUTES:
		frappe.throw(
			_("Duration must not exceed {0} minutes (24 hours).").format(MAX_DURATION_MINUTES),
			frappe.ValidationError,
		)

	entry = frappe.get_doc(
		{
			"doctype": "HD Time Entry",
			"ticket": ticket,
			"agent": frappe.session.user,
			"duration_minutes": duration_minutes,
			"billable": cint(billable),
			"description": description or "",
			"timestamp": now_datetime(),
			# Store as naive datetime string — MariaDB DATETIME col rejects tz-offset format
			"started_at": started_at_naive,
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
	if not is_agent():
		frappe.throw(_("Not permitted"), frappe.PermissionError)
	frappe.has_permission("HD Ticket", "write", doc=ticket, throw=True)

	# Defense-in-depth: validate description length here so callers receive a clear
	# HTTP 417 with a user-facing message before the document is even constructed.
	# HDTimeEntry.validate() also enforces this limit, so both layers are intentional.
	if description and len(description) > MAX_DESCRIPTION_LENGTH:
		frappe.throw(
			_("Description must not exceed {0} characters.").format(MAX_DESCRIPTION_LENGTH),
			frappe.ValidationError,
		)

	duration_minutes = cint(duration_minutes)
	if duration_minutes < 1:
		frappe.throw(_("Duration must be at least 1 minute."), frappe.ValidationError)
	if duration_minutes > MAX_DURATION_MINUTES:
		frappe.throw(
			_("Duration must not exceed {0} minutes (24 hours).").format(MAX_DURATION_MINUTES),
			frappe.ValidationError,
		)

	entry = frappe.get_doc(
		{
			"doctype": "HD Time Entry",
			"ticket": ticket,
			"agent": frappe.session.user,
			"duration_minutes": duration_minutes,
			"billable": cint(billable),
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

	Agents may only delete their own entries; HD Admin / Agent Manager /
	System Manager may delete any.

	Returns: { "success": True }
	"""
	entry = frappe.get_doc("HD Time Entry", name)

	# Pre-gate: only agents may delete time entries.
	# Ownership and privileged-role checks are delegated entirely to
	# _check_delete_permission (single source of truth — no duplication).
	if not is_agent():
		frappe.throw(_("Not permitted"), frappe.PermissionError)

	_check_delete_permission(entry, frappe.session.user)

	# Use ignore_permissions=True since we've already done our own permission check above
	frappe.delete_doc("HD Time Entry", name, ignore_permissions=True)
	return {"success": True}


@frappe.whitelist()
def get_summary(ticket: str) -> dict:
	"""
	Return time summary for a ticket: totals and entry list.

	Only accessible to agents — customers cannot see internal time/billing data.

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

	# Only agents may access time tracking data — customers cannot see billing/time info
	if not is_agent():
		frappe.throw(_("Not permitted"), frappe.PermissionError)

	# limit=0 fetches ALL entries — default limit_page_length=20 would truncate and
	# produce incorrect totals for tickets with more than 20 entries (Issue #13).
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
		limit=0,
	)

	# Bulk-resolve agent full names in a single query to avoid N+1 per entry (Issue #1)
	unique_agents = {e["agent"] for e in entries}
	user_name_map: dict = {}
	if unique_agents:
		users = frappe.get_all(
			"User",
			filters={"name": ["in", list(unique_agents)]},
			fields=["name", "first_name", "last_name"],
		)
		for u in users:
			last_initial = (u.get("last_name") or "")[:1]
			user_name_map[u["name"]] = (
				f"{u['first_name']} {last_initial}." if last_initial else u["first_name"]
			)

	for entry in entries:
		entry["agent_name"] = user_name_map.get(entry["agent"], entry["agent"])

	total_minutes = sum(e["duration_minutes"] for e in entries)
	billable_minutes = sum(e["duration_minutes"] for e in entries if e["billable"])

	return {
		"total_minutes": total_minutes,
		"billable_minutes": billable_minutes,
		"entries": entries,
	}
