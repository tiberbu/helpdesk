"""
Migration patch: Story County-2 — HD Facility Mapping DocType + Auto-Routing Engine

- Creates the tabHD Facility Mapping table
- Adds 'facility' custom field to User DocType (for auto-routing lookup)

Safe to run multiple times (idempotent).
"""

import frappe


def execute():
	# Create / reload the HD Facility Mapping DocType
	frappe.reload_doctype("HD Facility Mapping", force=True)

	# Add 'facility' custom field to User (used in auto-routing before_insert)
	if not frappe.db.exists("Custom Field", "User-facility"):
		frappe.get_doc(
			{
				"doctype": "Custom Field",
				"dt": "User",
				"module": "Helpdesk",
				"fieldname": "facility",
				"fieldtype": "Data",
				"label": "Facility",
				"description": "Healthcare facility this user belongs to (used for ticket auto-routing)",
				"insert_after": "last_name",
			}
		).insert(ignore_permissions=True)

	frappe.db.commit()  # nosemgrep
