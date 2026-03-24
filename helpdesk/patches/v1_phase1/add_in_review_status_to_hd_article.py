import frappe


def execute():
	"""Add 'In Review' option to HD Article status field and add reviewer_comment field.

	This patch is idempotent — safe to run multiple times.
	No existing article records are modified.
	"""
	# Reload the HD Article doctype to pick up the updated JSON schema
	frappe.reload_doc("helpdesk", "doctype", "hd_article")
