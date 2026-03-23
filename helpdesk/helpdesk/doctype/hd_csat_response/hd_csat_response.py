# Copyright (c) 2026, Frappe Technologies Pvt. Ltd. and contributors
# For license information, please see license.txt

import frappe
from frappe import _
from frappe.model.document import Document


class HDCSATResponse(Document):
	def validate(self):
		self._validate_rating()

	def _validate_rating(self):
		"""Rating must be between 1 and 5 if provided."""
		if self.rating is None:
			return
		if not (1 <= self.rating <= 5):
			frappe.throw(
				_("Rating must be between 1 and 5."),
				frappe.ValidationError,
			)
