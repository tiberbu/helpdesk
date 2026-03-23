"""
Patch: Add chat availability fields for Story 3.5.

- HD Agent: chat_availability (Select: Online/Away/Offline, default Online)
- HD Settings: max_concurrent_chats (Int, default 5)
- HD Chat Session: accepted_at (Datetime)
"""
import frappe


def execute():
	frappe.reload_doctype("HD Agent", force=True)
	frappe.reload_doctype("HD Settings", force=True)
	frappe.reload_doctype("HD Chat Session", force=True)

	# Set all existing agents to Online availability
	frappe.db.sql(
		"UPDATE `tabHD Agent` SET chat_availability = 'Online' WHERE chat_availability IS NULL OR chat_availability = ''"
	)

	# Set default max_concurrent_chats if not already set
	if not frappe.db.get_single_value("HD Settings", "max_concurrent_chats"):
		frappe.db.set_value("HD Settings", None, "max_concurrent_chats", 5)
