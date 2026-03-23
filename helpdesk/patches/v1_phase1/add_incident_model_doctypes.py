"""
Patch: Create HD Incident Model, HD Incident Checklist Item,
and HD Ticket Checklist Item DocTypes; add incident_model and
ticket_checklist fields to HD Ticket.
Story: 1.9 -- Incident Models / Templates
"""

import frappe


def execute():
	frappe.reload_doctype("HD Incident Checklist Item", force=True)
	frappe.reload_doctype("HD Incident Model", force=True)
	frappe.reload_doctype("HD Ticket Checklist Item", force=True)
	frappe.reload_doctype("HD Ticket", force=True)
