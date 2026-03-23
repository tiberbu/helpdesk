# Copyright (c) 2026, Frappe Technologies and contributors
# For license information, please see license.txt

import frappe
from frappe import _
from frappe.model.document import Document


class HDTicketCategory(Document):
    def validate(self):
        self._validate_no_self_reference()

    def _validate_no_self_reference(self):
        """Prevent a category from referencing itself as its parent (AC #2)."""
        if self.parent_category and self.parent_category == self.name:
            frappe.throw(
                _("A category cannot be its own parent category."),
                frappe.ValidationError,
            )
