"""
Migration patch: Story 5.4 — Ticket-Article Linking

- Creates the HD Ticket Article child table
- Adds the linked_articles Table field to HD Ticket (via reload)

Safe to run multiple times (idempotent).
"""

import frappe


def execute():
	# Reload the new HD Ticket Article DocType so Frappe creates its table
	frappe.reload_doctype("HD Ticket Article", force=True)

	# Reload HD Ticket to pick up the new linked_articles Table field
	frappe.reload_doctype("HD Ticket", force=True)

	frappe.db.commit()  # nosemgrep
