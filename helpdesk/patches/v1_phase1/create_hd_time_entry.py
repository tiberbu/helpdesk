"""
Patch: Create HD Time Entry DocType table.
Story: 1.7 -- Per-Ticket Time Tracking
"""
import frappe


def execute():
	frappe.reload_doctype("HD Time Entry", force=True)
