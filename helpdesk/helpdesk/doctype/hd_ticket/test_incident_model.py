# Copyright (c) 2026, Frappe Technologies and Contributors
# See license.txt
# Story 1.9: Incident Models / Templates

import frappe
from frappe.tests.utils import FrappeTestCase

from helpdesk.api.incident_model import apply_incident_model, complete_checklist_item
from helpdesk.test_utils import create_agent, make_ticket


def _make_model(priority="High", num_mandatory=2, num_optional=1):
	"""Helper: create a test HD Incident Model with checklist items."""
	suffix = frappe.generate_hash(length=8)
	checklist = [
		{"item": f"Mandatory item {i+1}", "is_mandatory": 1}
		for i in range(num_mandatory)
	]
	checklist += [
		{"item": f"Optional item {j+1}", "is_mandatory": 0}
		for j in range(num_optional)
	]
	doc = frappe.get_doc(
		{
			"doctype": "HD Incident Model",
			"model_name": f"Test Model {suffix}",
			"description": "Test model for unit tests",
			"default_priority": priority,
			"checklist_items": checklist,
		}
	)
	doc.insert(ignore_permissions=True)
	return doc


class TestIncidentModelApplication(FrappeTestCase):
	"""Unit tests for Story 1.9: Incident Models / Templates."""

	def setUp(self):
		frappe.set_user("Administrator")
		frappe.db.set_single_value("HD Settings", "skip_email_workflow", 1)
		# Incident Models are an ITIL feature — enable ITIL mode for all tests
		frappe.db.set_single_value("HD Settings", "itil_mode_enabled", 1)

		self.agent_email = "im_agent@example.com"
		create_agent(self.agent_email)
		frappe.set_user(self.agent_email)

		self.model = _make_model(priority="High", num_mandatory=2, num_optional=1)
		self.ticket = make_ticket(
			subject="Test Ticket for Incident Model",
			raised_by="im_customer@example.com",
		)

	def tearDown(self):
		frappe.set_user("Administrator")
		frappe.db.set_single_value("HD Settings", "itil_mode_enabled", 0)
		frappe.db.rollback()

	# ---------------------------------------------------------------
	# apply_incident_model
	# ---------------------------------------------------------------

	def test_apply_model_sets_priority(self):
		result = apply_incident_model(ticket=str(self.ticket.name), model=self.model.name)
		self.assertTrue(result["success"])
		self.assertIn("priority", result["fields_applied"])
		doc = frappe.get_doc("HD Ticket", self.ticket.name)
		self.assertEqual(doc.priority, "High")

	def test_apply_model_sets_incident_model_reference(self):
		apply_incident_model(ticket=str(self.ticket.name), model=self.model.name)
		doc = frappe.get_doc("HD Ticket", self.ticket.name)
		self.assertEqual(doc.incident_model, self.model.name)

	def test_apply_model_skips_blank_fields(self):
		"""Model with no default_category should NOT overwrite ticket category."""
		self.assertFalse(self.model.default_category)
		self.ticket.reload()
		original_category = self.ticket.category

		apply_incident_model(ticket=str(self.ticket.name), model=self.model.name)
		doc = frappe.get_doc("HD Ticket", self.ticket.name)
		self.assertEqual(doc.category, original_category)

	def test_apply_model_creates_checklist_rows(self):
		result = apply_incident_model(ticket=str(self.ticket.name), model=self.model.name)
		# model has 2 mandatory + 1 optional = 3 items
		self.assertEqual(result["checklist_items_count"], 3)
		doc = frappe.get_doc("HD Ticket", self.ticket.name)
		self.assertEqual(len(doc.ticket_checklist), 3)
		items = [row.item for row in doc.ticket_checklist]
		self.assertIn("Mandatory item 1", items)
		self.assertIn("Optional item 1", items)

	def test_apply_model_replaces_existing_checklist(self):
		apply_incident_model(ticket=str(self.ticket.name), model=self.model.name)
		# Apply again — should replace, not duplicate
		result = apply_incident_model(ticket=str(self.ticket.name), model=self.model.name)
		doc = frappe.get_doc("HD Ticket", self.ticket.name)
		# Should still be exactly 3, not 6
		self.assertEqual(len(doc.ticket_checklist), 3)
		self.assertEqual(result["checklist_items_count"], 3)

	def test_apply_model_marks_checklist_uncompleted(self):
		apply_incident_model(ticket=str(self.ticket.name), model=self.model.name)
		doc = frappe.get_doc("HD Ticket", self.ticket.name)
		for row in doc.ticket_checklist:
			self.assertEqual(row.is_completed, 0)

	# ---------------------------------------------------------------
	# complete_checklist_item
	# ---------------------------------------------------------------

	def test_complete_checklist_item_sets_completed(self):
		apply_incident_model(ticket=str(self.ticket.name), model=self.model.name)
		doc = frappe.get_doc("HD Ticket", self.ticket.name)
		item = doc.ticket_checklist[0]

		result = complete_checklist_item(
			ticket=str(self.ticket.name), checklist_item_name=item.name
		)
		self.assertTrue(result["success"])
		self.assertEqual(result["is_completed"], 1)
		self.assertEqual(result["completed_by"], frappe.session.user)
		self.assertIsNotNone(result["completed_at"])

	def test_complete_checklist_item_toggles_off(self):
		apply_incident_model(ticket=str(self.ticket.name), model=self.model.name)
		doc = frappe.get_doc("HD Ticket", self.ticket.name)
		item = doc.ticket_checklist[0]

		# Mark completed
		complete_checklist_item(
			ticket=str(self.ticket.name), checklist_item_name=item.name
		)
		# Unmark
		result = complete_checklist_item(
			ticket=str(self.ticket.name), checklist_item_name=item.name
		)
		self.assertEqual(result["is_completed"], 0)
		self.assertIsNone(result["completed_by"])
		self.assertIsNone(result["completed_at"])

	# ---------------------------------------------------------------
	# resolution validation
	# ---------------------------------------------------------------

	def test_resolution_blocked_when_mandatory_items_incomplete(self):
		apply_incident_model(ticket=str(self.ticket.name), model=self.model.name)
		doc = frappe.get_doc("HD Ticket", self.ticket.name)

		# Make a "Resolved" status exist
		if not frappe.db.exists("HD Ticket Status", "Resolved"):
			frappe.get_doc(
				{
					"doctype": "HD Ticket Status",
					"label_agent": "Resolved",
					"category": "Resolved",
					"is_default": 0,
				}
			).insert(ignore_permissions=True)

		doc.status = "Resolved"
		with self.assertRaises(frappe.ValidationError):
			doc.save()

	def test_resolution_allowed_when_all_mandatory_items_complete(self):
		apply_incident_model(ticket=str(self.ticket.name), model=self.model.name)
		doc = frappe.get_doc("HD Ticket", self.ticket.name)

		# Complete all mandatory items
		for row in doc.ticket_checklist:
			if row.is_mandatory:
				complete_checklist_item(
					ticket=str(self.ticket.name), checklist_item_name=row.name
				)

		if not frappe.db.exists("HD Ticket Status", "Resolved"):
			frappe.get_doc(
				{
					"doctype": "HD Ticket Status",
					"label_agent": "Resolved",
					"category": "Resolved",
					"is_default": 0,
				}
			).insert(ignore_permissions=True)

		doc.reload()
		doc.status = "Resolved"
		try:
			doc.save()
		except frappe.ValidationError as e:
			self.fail(f"Resolution should be allowed but got: {e}")

	def test_resolution_allowed_when_no_checklist(self):
		"""Ticket with no checklist should resolve without error."""
		doc = frappe.get_doc("HD Ticket", self.ticket.name)
		self.assertEqual(len(doc.ticket_checklist), 0)

		if not frappe.db.exists("HD Ticket Status", "Resolved"):
			frappe.get_doc(
				{
					"doctype": "HD Ticket Status",
					"label_agent": "Resolved",
					"category": "Resolved",
					"is_default": 0,
				}
			).insert(ignore_permissions=True)

		doc.status = "Resolved"
		try:
			doc.save()
		except frappe.ValidationError as e:
			self.fail(f"Resolution without checklist should be allowed: {e}")
