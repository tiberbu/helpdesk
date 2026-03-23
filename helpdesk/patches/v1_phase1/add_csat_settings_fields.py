"""
Patch: Add CSAT survey configuration fields to HD Settings.
Story: 3.7 -- CSAT Survey Infrastructure and Delivery
"""
import frappe


def execute():
	frappe.reload_doctype("HD Settings", force=True)
