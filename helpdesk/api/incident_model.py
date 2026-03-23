# Copyright (c) 2026, Frappe Technologies Pvt. Ltd. and contributors
# For license information, please see license.txt

import frappe
from frappe import _
from frappe.utils import now_datetime

from helpdesk.utils import is_agent


@frappe.whitelist()
def apply_incident_model(ticket: str, model: str) -> dict:
	"""
	Apply an HD Incident Model to a ticket.

	Populates ticket fields from the model's defaults and copies checklist
	items into the ticket's ticket_checklist child table.

	Returns:
	    {
	        "success": True,
	        "fields_applied": {"category": ..., "priority": ..., ...},
	        "checklist_items_count": int
	    }
	"""
	if not is_agent():
		frappe.throw(_("Not permitted"), frappe.PermissionError)
	frappe.has_permission("HD Ticket", "write", doc=ticket, throw=True)

	if not frappe.db.get_single_value("HD Settings", "itil_mode_enabled"):
		frappe.throw(_("Incident Models require ITIL mode to be enabled"), frappe.ValidationError)

	ticket_doc = frappe.get_doc("HD Ticket", ticket)
	model_doc = frappe.get_doc("HD Incident Model", model)

	fields_applied = {}

	# Apply default fields — only if the model value is non-empty
	field_map = {
		"default_category": "category",
		"default_sub_category": "sub_category",
		"default_priority": "priority",
		"default_team": "agent_group",
	}
	for model_field, ticket_field in field_map.items():
		value = model_doc.get(model_field)
		if value:
			ticket_doc.set(ticket_field, value)
			fields_applied[ticket_field] = value

	# Set the incident_model reference
	ticket_doc.incident_model = model
	fields_applied["incident_model"] = model

	# Replace checklist items — clear existing, copy from model
	ticket_doc.set("ticket_checklist", [])
	for model_item in model_doc.get("checklist_items", []):
		ticket_doc.append(
			"ticket_checklist",
			{
				"item": model_item.item,
				"is_mandatory": model_item.is_mandatory,
				"is_completed": 0,
			},
		)

	ticket_doc.save()

	return {
		"success": True,
		"fields_applied": fields_applied,
		"checklist_items_count": len(ticket_doc.ticket_checklist),
	}


@frappe.whitelist()
def complete_checklist_item(ticket: str, checklist_item_name: str) -> dict:
	"""
	Toggle the completion state of a single checklist item on a ticket.

	If currently incomplete: marks completed with timestamp and user.
	If currently complete: clears completion state (allows unchecking).

	Returns:
	    {
	        "success": True,
	        "is_completed": int,
	        "completed_by": str | None,
	        "completed_at": str | None
	    }
	"""
	if not is_agent():
		frappe.throw(_("Not permitted"), frappe.PermissionError)
	frappe.has_permission("HD Ticket", "write", doc=ticket, throw=True)

	if not frappe.db.get_single_value("HD Settings", "itil_mode_enabled"):
		frappe.throw(_("Incident Models require ITIL mode to be enabled"), frappe.ValidationError)

	ticket_doc = frappe.get_doc("HD Ticket", ticket)
	checklist_row = None
	for row in ticket_doc.get("ticket_checklist", []):
		if row.name == checklist_item_name:
			checklist_row = row
			break

	if not checklist_row:
		frappe.throw(
			_("Checklist item {0} not found on ticket {1}").format(
				checklist_item_name, ticket
			),
			frappe.DoesNotExistError,
		)

	if checklist_row.is_completed:
		# Toggle off — clear completion state
		checklist_row.is_completed = 0
		checklist_row.completed_by = None
		checklist_row.completed_at = None
	else:
		# Toggle on — record completion
		checklist_row.is_completed = 1
		checklist_row.completed_by = frappe.session.user
		checklist_row.completed_at = now_datetime()

	ticket_doc.save()

	return {
		"success": True,
		"is_completed": checklist_row.is_completed,
		"completed_by": checklist_row.completed_by,
		"completed_at": (
			str(checklist_row.completed_at) if checklist_row.completed_at else None
		),
	}
