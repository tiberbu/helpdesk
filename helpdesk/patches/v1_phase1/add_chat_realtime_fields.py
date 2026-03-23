"""
Patch: Add real-time chat fields for Story 3.4.

- HD Settings: chat_response_timeout_seconds (Int, default 120)
- HD Chat Session: timeout_notified_at (Datetime)
"""
import frappe


def execute():
	frappe.reload_doctype("HD Settings", force=True)
	frappe.reload_doctype("HD Chat Session", force=True)

	# Set default timeout value if not already set
	if not frappe.db.get_single_value("HD Settings", "chat_response_timeout_seconds"):
		frappe.db.set_value("HD Settings", None, "chat_response_timeout_seconds", 120)
