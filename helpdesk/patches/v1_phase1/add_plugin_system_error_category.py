"""Provide the category used by the HMIS plugin contract without changing existing types."""

import frappe


def execute():
    if not frappe.db.exists("HD Ticket Type", "System Error"):
        frappe.get_doc(
            {
                "doctype": "HD Ticket Type",
                "name": "System Error",
                "description": "Application or integration failure reported by HMIS or mobile.",
            }
        ).insert()
