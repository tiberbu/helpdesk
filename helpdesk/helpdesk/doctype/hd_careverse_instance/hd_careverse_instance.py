from urllib.parse import urlsplit

import frappe
from frappe.model.document import Document


class HDCareVerseInstance(Document):
	def validate(self):
		self.base_url = (self.base_url or "").strip().rstrip("/")
		url = urlsplit(self.base_url)
		if (
			url.scheme != "https"
			or not url.netloc
			or url.username
			or url.password
			or url.path
			or url.query
			or url.fragment
		):
			frappe.throw("CareVerse URL must be an HTTPS origin without a path or credentials.")
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
