"""
Patch: Create HD Chat Message DocType table.
Story: 3.2 -- Chat Session Management Backend
"""
import frappe


def execute():
	frappe.reload_doctype("HD Chat Message", force=True)
