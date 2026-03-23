# Copyright (c) 2026, Frappe Technologies Pvt. Ltd. and contributors
# For license information, please see license.txt

"""HD Automation Log DocType controller.

Log records are immutable audit trail entries created programmatically by
the automation engine via insert(ignore_permissions=True). No business logic
is needed in this controller.
"""

import frappe
from frappe.model.document import Document


class HDAutomationLog(Document):
    pass
