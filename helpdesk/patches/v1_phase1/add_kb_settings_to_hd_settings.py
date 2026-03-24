import frappe


def execute():
	"""Add kb_reviewers Table field to HD Settings and create HD KB Reviewer doctype.

	This patch is idempotent — safe to run multiple times.
	"""
	frappe.reload_doc("helpdesk", "doctype", "hd_kb_reviewer")
	frappe.reload_doc("helpdesk", "doctype", "hd_settings")
