"""
Patch: Reload HD Incident Model to pick up the default_priority field type
change from Select to Link (HD Ticket Priority).

This is required for existing deployments that already ran
add_incident_model_doctypes.py but have not yet had the column updated.
Story: 68 — Fix P1 QA findings (status_category bypass + migration patch)
"""

import frappe


def execute():
	# F-05: Reload both the parent doctype and the child checklist table so all
	# schema changes (column types, new fields) are reflected in the database.
	frappe.reload_doctype("HD Incident Model", force=True)
	frappe.reload_doctype("HD Incident Checklist Item", force=True)

	# F-04: Guard against the tabHD Ticket Priority table not existing yet
	# (e.g. fresh install where the priority migration hasn't run yet).
	try:
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
	except Exception:
		# Table may not exist on a clean install — skip validation in that case.
		frappe.logger().warning(
			"reload_incident_model_for_link_field: tabHD Ticket Priority not found, "
			"skipping invalid default_priority cleanup"
		)
		frappe.db.commit()  # F-03
		return

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

	# F-03: Commit so the patch changes are durably persisted.
	frappe.db.commit()  # nosemgrep
