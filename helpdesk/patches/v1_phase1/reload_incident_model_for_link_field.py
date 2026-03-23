"""
Patch: Reload HD Incident Model to pick up the default_priority field type
change from Select to Link (HD Ticket Priority).

This is required for existing deployments that already ran
add_incident_model_doctypes.py but have not yet had the column updated.
Story: 68 — Fix P1 QA findings (status_category bypass + migration patch)
"""

import frappe


def execute():
	# Reload the doctype schema so the column is updated to VARCHAR/Link
	frappe.reload_doctype("HD Incident Model", force=True)

	# Validate existing default_priority values: if any row references a
	# priority that no longer exists as an HD Ticket Priority doc, clear it
	# to prevent broken link references.
	invalid_models = frappe.db.sql(
		"""
		SELECT im.name, im.default_priority
		FROM `tabHD Incident Model` im
		WHERE im.default_priority IS NOT NULL
		  AND im.default_priority != ''
		  AND NOT EXISTS (
		      SELECT 1 FROM `tabHD Ticket Priority` tp
		      WHERE tp.name = im.default_priority
		  )
		""",
		as_dict=True,
	)

	if invalid_models:
		names = [r["name"] for r in invalid_models]
		frappe.db.sql(
			"""
			UPDATE `tabHD Incident Model`
			SET default_priority = NULL
			WHERE name IN ({placeholders})
			""".format(placeholders=", ".join(["%s"] * len(names))),
			tuple(names),
		)
		frappe.logger().warning(
			f"reload_incident_model_for_link_field: cleared invalid default_priority "
			f"on {len(names)} HD Incident Model(s): {names}"
		)
