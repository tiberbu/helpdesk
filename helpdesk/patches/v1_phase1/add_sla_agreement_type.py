import frappe


def execute():
	"""Set agreement_type = 'SLA' for all existing HD Service Level Agreement
	records that have a NULL or empty agreement_type value.
	This patch is idempotent — safe to run multiple times.
	"""
	# Bulk update using frappe.db.sql for performance (avoids per-record Python loop)
	frappe.db.sql(
		"""
		UPDATE `tabHD Service Level Agreement`
		SET agreement_type = 'SLA'
		WHERE agreement_type IS NULL OR agreement_type = ''
		"""
	)
	frappe.db.commit()
