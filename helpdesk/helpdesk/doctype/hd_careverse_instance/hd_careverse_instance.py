import frappe
from frappe.model.document import Document


class HDCareVerseInstance(Document):
	def validate(self):
		seen = set()
		for row in self.users:
			if row.careverse_user in seen:
				frappe.throw("CareVerse user IDs must be unique within an instance.")
			seen.add(row.careverse_user)
			if row.careverse_user in ("Guest", "Administrator") or row.helpdesk_user in (
				"Guest",
				"Administrator",
			):
				frappe.throw("Guest and Administrator cannot be mapped for mobile ticket access.")
