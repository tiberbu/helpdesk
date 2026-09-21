import frappe


def execute():
	# The allowlist used to be a Custom Field created by a post_model_sync patch,
	# which fresh installs mark as done without running, so the field never existed
	# there. It is now a standard HD Settings field; drop the Custom Field before the
	# model sync adds the standard one. The stored value lives in tabSingles and is kept.
	name = frappe.db.get_value(
		"Custom Field", {"dt": "HD Settings", "fieldname": "sso_allowed_email_domains"}
	)
	if name:
		frappe.delete_doc("Custom Field", name, ignore_permissions=True, force=True)
