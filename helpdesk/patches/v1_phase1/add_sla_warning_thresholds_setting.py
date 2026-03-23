# Copyright (c) 2026, Frappe Technologies Pvt. Ltd. and contributors
# For license information, please see license.txt

"""Migration patch: add sla_warning_thresholds default to HD Settings.

Sets the default value of [30, 15, 5] for the new sla_warning_thresholds
JSON field on HD Settings if it has not already been configured.
"""

import frappe


def execute():
    current = frappe.db.get_single_value("HD Settings", "sla_warning_thresholds")
    if not current:
        frappe.db.set_single_value(
            "HD Settings",
            "sla_warning_thresholds",
            "[30, 15, 5]",
        )
        frappe.db.commit()  # nosemgrep
