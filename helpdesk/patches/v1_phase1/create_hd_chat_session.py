"""
Patch: Create HD Chat Session DocType table.
Story: 3.2 -- Chat Session Management Backend
"""
import frappe


def execute():
	frappe.reload_doctype("HD Chat Session", force=True)
