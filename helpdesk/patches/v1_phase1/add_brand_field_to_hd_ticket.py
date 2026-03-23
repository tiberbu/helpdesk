"""
Patch: add_brand_field_to_hd_ticket
Adds the `brand` Link field (→ HD Brand) to HD Ticket (Story 3.8).
"""

import frappe


def execute():
    frappe.reload_doc("Helpdesk", "doctype", "hd_ticket", force=True)
