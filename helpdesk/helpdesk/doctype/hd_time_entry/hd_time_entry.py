# Copyright (c) 2026, Frappe Technologies Pvt. Ltd. and contributors
# For license information, please see license.txt

import frappe
from frappe import _
from frappe.model.document import Document


class HDTimeEntry(Document):
	def validate(self):
		if self.duration_minutes < 1:
			frappe.throw(
				_("Duration must be at least 1 minute."),
				frappe.ValidationError,
			)

	def before_delete(self):
		"""
		Enforce ownership on direct REST DELETE calls (e.g. DELETE /api/resource/HD Time Entry/{name}).
		Agents may only delete their own entries; HD Admin / System Manager may delete any.
		This mirrors the logic in helpdesk.api.time_tracking.delete_entry and prevents REST bypass.
		"""
		is_hd_admin = frappe.db.get_value(
			"Has Role",
			{"parent": frappe.session.user, "role": ["in", ["HD Admin", "System Manager"]]},
			"name",
		)
		if self.agent != frappe.session.user and not is_hd_admin:
			frappe.throw(_("You can only delete your own time entries."), frappe.PermissionError)
