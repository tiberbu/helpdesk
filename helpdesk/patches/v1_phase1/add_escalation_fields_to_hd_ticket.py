"""
Migration patch: Story County-4 — Escalation chain fields on HD Ticket

- Reloads HD Ticket to pick up escalation_count and escalation_path fields
- Safe to run multiple times (idempotent).
"""

import frappe


def execute():
	# Reload HD Ticket to pick up escalation_count and escalation_path fields
	frappe.reload_doctype("HD Ticket", force=True)

	frappe.db.commit()  # nosemgrep
