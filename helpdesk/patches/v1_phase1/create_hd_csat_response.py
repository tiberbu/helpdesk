"""
Patch: Create HD CSAT Response DocType table.
Story: 3.7 -- CSAT Survey Infrastructure and Delivery
"""
import frappe


def execute():
	frappe.reload_doctype("HD CSAT Response", force=True)
