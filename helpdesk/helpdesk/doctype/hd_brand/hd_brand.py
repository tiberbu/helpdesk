# Copyright (c) 2026, Frappe Technologies Pvt. Ltd. and contributors
# For license information, please see license.txt

import frappe
from frappe import _
from frappe.model.document import Document


class HDBrand(Document):
    def validate(self):
        self._validate_support_email()
        self._validate_portal_domain_unique()

    def _validate_support_email(self):
        if self.support_email and not frappe.utils.validate_email_address(
            self.support_email
        ):
            frappe.throw(
                _("Support Email {0} is not a valid email address").format(
                    self.support_email
                ),
                frappe.ValidationError,
            )

    def _validate_portal_domain_unique(self):
        if not self.portal_domain:
            return
        existing = frappe.db.get_value(
            "HD Brand",
            {"portal_domain": self.portal_domain, "name": ["!=", self.name]},
            "name",
        )
        if existing:
            frappe.throw(
                _("Portal domain {0} is already used by brand {1}").format(
                    self.portal_domain, existing
                ),
                frappe.ValidationError,
            )
