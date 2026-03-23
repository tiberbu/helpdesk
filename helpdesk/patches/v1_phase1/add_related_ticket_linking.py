"""
Migration patch: Story 1.6 — Related Ticket Linking

- Creates the tabHD Related Ticket child table
- Adds the related_tickets Table field to HD Ticket
- Inserts a 'Duplicate' HD Ticket Status record (category: Resolved) if absent

Safe to run multiple times (idempotent).
"""

import frappe


def execute():
	# Reload the new HD Related Ticket DocType so Frappe creates its table
	frappe.reload_doctype("HD Related Ticket", force=True)

	# Reload HD Ticket to pick up the new related_tickets Table field
	frappe.reload_doctype("HD Ticket", force=True)

	# Create 'Duplicate' HD Ticket Status if it does not already exist
	if not frappe.db.exists("HD Ticket Status", "Duplicate"):
		frappe.get_doc(
			{
				"doctype": "HD Ticket Status",
				"label_agent": "Duplicate",
				"category": "Resolved",
				"color": "Orange",
				"enabled": 1,
				"order": 50,
			}
		).insert(ignore_permissions=True)

	frappe.db.commit()  # nosemgrep
