"""
Migration patch: Story County-1 — HD Support Level DocType + HD Team/Ticket hierarchy fields

- Creates the tabHD Support Level table
- Reloads HD Team to pick up parent_team, support_level, territory, is_group fields
- Reloads HD Ticket to pick up facility, sub_county, county, support_level fields
- Seeds the four default support levels

Safe to run multiple times (idempotent).
"""

import frappe


def execute():
	# Create the new HD Support Level DocType table
	frappe.reload_doctype("HD Support Level", force=True)

	# Reload HD Team to pick up new hierarchy fields
	frappe.reload_doctype("HD Team", force=True)

	# Reload HD Ticket to pick up new county/facility fields
	frappe.reload_doctype("HD Ticket", force=True)

	# Seed the four default support levels
	seed_data = [
		{
			"level_name": "L0 - Sub-County",
			"level_order": 0,
			"display_name": "Sub-County Support",
			"allow_escalation_to_next": 1,
			"auto_escalate_on_breach": 1,
			"auto_escalate_minutes": 60,
		},
		{
			"level_name": "L1 - County",
			"level_order": 1,
			"display_name": "County Support",
			"allow_escalation_to_next": 1,
			"auto_escalate_on_breach": 1,
			"auto_escalate_minutes": 120,
		},
		{
			"level_name": "L2 - National",
			"level_order": 2,
			"display_name": "National Support",
			"allow_escalation_to_next": 1,
			"auto_escalate_on_breach": 0,
		},
		{
			"level_name": "L3 - Engineering",
			"level_order": 3,
			"display_name": "Engineering",
			"allow_escalation_to_next": 0,
			"auto_escalate_on_breach": 0,
		},
	]

	for entry in seed_data:
		if not frappe.db.exists("HD Support Level", entry["level_name"]):
			frappe.get_doc({"doctype": "HD Support Level", **entry}).insert(
				ignore_permissions=True
			)

	frappe.db.commit()  # nosemgrep
