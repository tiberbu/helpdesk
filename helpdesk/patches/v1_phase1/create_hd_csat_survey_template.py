"""
Patch: Create HD CSAT Survey Template DocType table.
Story: 3.7 -- CSAT Survey Infrastructure and Delivery
"""
import frappe


def execute():
	frappe.reload_doctype("HD CSAT Survey Template", force=True)
