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

	# Well-known status records that individual tests may create.
	_TEST_STATUS_NAMES = ("Replied", "Resolved")

	def setUp(self):
		frappe.set_user("Administrator")
		frappe.db.set_single_value("HD Settings", "skip_email_workflow", 1)
		# Incident Models are an ITIL feature — enable ITIL mode for all tests
		frappe.db.set_single_value("HD Settings", "itil_mode_enabled", 1)
		# Disable category-required-on-resolution so resolution tests don't need a category
		frappe.db.set_single_value("HD Settings", "category_required_on_resolution", 0)

		# F-03: snapshot which HD Ticket Status records exist BEFORE the test so
		# tearDown can delete only ones that were created by the test, not
		# pre-existing records from fixtures or other test suites.
		self._pre_existing_statuses = set(
			frappe.db.get_all("HD Ticket Status", pluck="name")
		)

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
		# F-03: delete any HD Ticket Status records that were created by this test
		# (db.rollback() is a no-op when a commit occurred mid-test).
		for status_name in self._TEST_STATUS_NAMES:
			if status_name not in self._pre_existing_statuses and frappe.db.exists(
				"HD Ticket Status", status_name
			):
				frappe.delete_doc(
					"HD Ticket Status", status_name, ignore_permissions=True, force=True
				)
		# F-06: explicitly delete the non-agent test user so it doesn't persist
		# across test runs (db.rollback() is a no-op when a commit occurred mid-test).
		noagent_email = "im_customer_noagent@example.com"
		if frappe.db.exists("User", noagent_email):
			frappe.delete_doc("User", noagent_email, ignore_permissions=True, force=True)
		frappe.db.commit()
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

	# ---------------------------------------------------------------
	# F-02: Regression test — status_category must update when status changes
	# ---------------------------------------------------------------

	def test_status_category_updates_when_status_changes(self):
		"""F-02 regression: stale status_category bypass must not occur.

		Uses the real agent user workflow (no ignore_permissions=True) so that
		check_update_perms() and all before_validate hooks run — the same path
		as a production save from the agent portal.

		Sequence:
		  1. Save ticket as Replied (category Paused) — as agent, no bypass
		  2. Change status to Resolved — as agent, no bypass
		  3. Verify status_category is Resolved, not stale Paused
		"""
		# Ensure Replied status with category Paused exists
		if not frappe.db.exists("HD Ticket Status", "Replied"):
			frappe.set_user("Administrator")
			frappe.get_doc(
				{
					"doctype": "HD Ticket Status",
					"label_agent": "Replied",
					"category": "Paused",
					"is_default": 0,
				}
			).insert(ignore_permissions=True)
			frappe.set_user(self.agent_email)

		if not frappe.db.exists("HD Ticket Status", "Resolved"):
			frappe.set_user("Administrator")
			frappe.get_doc(
				{
					"doctype": "HD Ticket Status",
					"label_agent": "Resolved",
					"category": "Resolved",
					"is_default": 0,
				}
			).insert(ignore_permissions=True)
			frappe.set_user(self.agent_email)

		# Step 1: Set ticket status to Replied → category should become Paused.
		# Saved as the agent user (real production path — no ignore_permissions).
		doc = frappe.get_doc("HD Ticket", self.ticket.name)
		doc.status = "Replied"
		doc.save()
		doc.reload()
		self.assertEqual(
			doc.status_category,
			"Paused",
			"Expected status_category=Paused after setting status=Replied",
		)

		# Step 2: Change status to Resolved — still as agent, no bypass.
		doc.status = "Resolved"
		doc.save()
		doc.reload()

		# Step 3: Verify status_category is now Resolved (not stale Paused)
		self.assertEqual(
			doc.status_category,
			"Resolved",
			"Expected status_category=Resolved after status changed to Resolved, "
			"but got stale Paused — bypass regression detected",
		)

	def test_replied_to_resolved_blocked_by_incomplete_checklist(self):
		"""F-03 regression: Replied→Resolved with incomplete mandatory checklist
		must raise ValidationError.

		This is the original P1 bug scenario: if status_category stayed stale as
		'Paused' when status changed to 'Resolved', validate_checklist_before_resolution()
		would short-circuit (seeing non-Resolved category) and allow the save.

		With the F-01 fix (set_status_category always re-derives), status_category is
		corrected to 'Resolved' before validate() runs, so the checklist guard fires.
		"""
		# Ensure required HD Ticket Status records exist
		if not frappe.db.exists("HD Ticket Status", "Replied"):
			frappe.set_user("Administrator")
			frappe.get_doc(
				{
					"doctype": "HD Ticket Status",
					"label_agent": "Replied",
					"category": "Paused",
					"is_default": 0,
				}
			).insert(ignore_permissions=True)
			frappe.set_user(self.agent_email)

		if not frappe.db.exists("HD Ticket Status", "Resolved"):
			frappe.set_user("Administrator")
			frappe.get_doc(
				{
					"doctype": "HD Ticket Status",
					"label_agent": "Resolved",
					"category": "Resolved",
					"is_default": 0,
				}
			).insert(ignore_permissions=True)
			frappe.set_user(self.agent_email)

		# Apply model — creates 2 mandatory + 1 optional checklist items, all incomplete
		apply_incident_model(ticket=str(self.ticket.name), model=self.model.name)

		# Move ticket to Replied (Paused category) via real save
		doc = frappe.get_doc("HD Ticket", self.ticket.name)
		doc.status = "Replied"
		doc.save()
		doc.reload()
		self.assertEqual(doc.status_category, "Paused")

		# Attempt Replied→Resolved with NO mandatory items completed.
		# set_status_category() will re-derive status_category to "Resolved",
		# then validate_checklist_before_resolution() must fire and block the save.
		doc.status = "Resolved"
		with self.assertRaises(
			frappe.ValidationError,
			msg=(
				"Expected ValidationError when resolving a ticket with incomplete "
				"mandatory checklist items — checklist guard was bypassed"
			),
		):
			doc.save()

	# ---------------------------------------------------------------
	# F-04: Permission guard — non-agent (customer) must get PermissionError
	# ---------------------------------------------------------------

	def test_apply_model_raises_permission_error_for_non_agent(self):
		"""Customer user must not be able to apply an incident model (F-04)."""
		self._noagent_email = "im_customer_noagent@example.com"
		# Create a plain user without Agent role — simulates a portal customer
		frappe.set_user("Administrator")
		if not frappe.db.exists("User", self._noagent_email):
			frappe.get_doc(
				{
					"doctype": "User",
					"email": self._noagent_email,
					"first_name": "Customer",
					"last_name": "NoAgent",
					"send_welcome_email": 0,
				}
			).insert(ignore_permissions=True)
		frappe.set_user(self.agent_email)

		# Switch to the non-agent user and attempt to call apply_incident_model
		frappe.set_user(self._noagent_email)
		with self.assertRaises(frappe.PermissionError):
			apply_incident_model(ticket=str(self.ticket.name), model=self.model.name)

		# Restore agent user for tearDown
		frappe.set_user(self.agent_email)

	# ---------------------------------------------------------------
	# F-07: Permission guard for complete_checklist_item
	# ---------------------------------------------------------------

	def test_complete_checklist_item_raises_permission_error_for_non_agent(self):
		"""Customer user must not be able to complete a checklist item (F-07)."""
		# Apply model to get checklist rows
		apply_incident_model(ticket=str(self.ticket.name), model=self.model.name)
		doc = frappe.get_doc("HD Ticket", self.ticket.name)
		self.assertTrue(len(doc.ticket_checklist) > 0, "Expected checklist rows after applying model")
		item = doc.ticket_checklist[0]

		noagent_email = "im_customer_noagent@example.com"
		frappe.set_user("Administrator")
		if not frappe.db.exists("User", noagent_email):
			frappe.get_doc(
				{
					"doctype": "User",
					"email": noagent_email,
					"first_name": "Customer",
					"last_name": "NoAgent",
					"send_welcome_email": 0,
				}
			).insert(ignore_permissions=True)
		frappe.set_user(self.agent_email)

		# Switch to non-agent and attempt to complete a checklist item
		frappe.set_user(noagent_email)
		with self.assertRaises(frappe.PermissionError):
			complete_checklist_item(
				ticket=str(self.ticket.name), checklist_item_name=item.name
			)

		# Restore agent user for tearDown
		frappe.set_user(self.agent_email)

	# ---------------------------------------------------------------
	# F-05: ITIL-mode-disabled rejection — ValidationError when ITIL off
	# ---------------------------------------------------------------

	def test_apply_model_raises_validation_error_when_itil_disabled(self):
		"""apply_incident_model must reject when itil_mode_enabled=0 (F-05)."""
		# Disable ITIL mode mid-test (setUp has it enabled)
		frappe.set_user("Administrator")
		frappe.db.set_single_value("HD Settings", "itil_mode_enabled", 0)
		frappe.set_user(self.agent_email)

		with self.assertRaises(frappe.ValidationError):
			apply_incident_model(ticket=str(self.ticket.name), model=self.model.name)

		# Re-enable for remaining tearDown flow
		frappe.set_user("Administrator")
		frappe.db.set_single_value("HD Settings", "itil_mode_enabled", 1)
		frappe.set_user(self.agent_email)

	def test_complete_checklist_item_raises_when_itil_disabled(self):
		"""F-06: complete_checklist_item must reject when itil_mode_enabled=0.

		This was the original F-08 finding — no test existed to prove that the
		ITIL-disabled guard on complete_checklist_item actually fires.
		"""
		# First apply the model while ITIL is enabled (setUp enables it)
		apply_incident_model(ticket=str(self.ticket.name), model=self.model.name)
		doc = frappe.get_doc("HD Ticket", self.ticket.name)
		self.assertTrue(
			len(doc.ticket_checklist) > 0,
			"Expected checklist rows after applying model",
		)
		item = doc.ticket_checklist[0]

		# Disable ITIL mode
		frappe.set_user("Administrator")
		frappe.db.set_single_value("HD Settings", "itil_mode_enabled", 0)
		frappe.set_user(self.agent_email)

		with self.assertRaises(
			frappe.ValidationError,
			msg=(
				"Expected ValidationError when calling complete_checklist_item "
				"with ITIL mode disabled"
			),
		):
			complete_checklist_item(
				ticket=str(self.ticket.name), checklist_item_name=item.name
			)

		# Re-enable for remaining tearDown flow
		frappe.set_user("Administrator")
		frappe.db.set_single_value("HD Settings", "itil_mode_enabled", 1)
		frappe.set_user(self.agent_email)
