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
	_TEST_STATUS_NAMES = ("Replied", "Resolved", "Closed")

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

	def test_closure_blocked_when_mandatory_items_incomplete(self):
		"""F-03: 'Closed' category path must also block incomplete mandatory checklist.

		validate_checklist_before_resolution() guards both "Resolved" and "Closed"
		status categories.  This test covers the "Closed" branch to prevent a
		regression where only "Resolved" was tested and a refactor could accidentally
		drop the Closed guard.
		"""
		# Ensure a "Closed" HD Ticket Status record exists
		if not frappe.db.exists("HD Ticket Status", "Closed"):
			frappe.set_user("Administrator")
			frappe.get_doc(
				{
					"doctype": "HD Ticket Status",
					"label_agent": "Closed",
					"category": "Closed",
					"is_default": 0,
				}
			).insert(ignore_permissions=True)
			frappe.set_user(self.agent_email)

		# Apply model so the ticket has mandatory checklist items (all incomplete)
		apply_incident_model(ticket=str(self.ticket.name), model=self.model.name)
		doc = frappe.get_doc("HD Ticket", self.ticket.name)
		self.assertTrue(len(doc.ticket_checklist) > 0, "Expected checklist rows after applying model")

		# Attempt to close the ticket with incomplete mandatory items
		doc.status = "Closed"
		# F-07: assertRaisesRegex confirms both the exception type and message
		with self.assertRaisesRegex(
			frappe.ValidationError,
			r"mandatory checklist item",
		):
			doc.save()

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
		# F-07: use assertRaisesRegex to verify the exception message content
		# (assertRaises with msg= only sets the test-failure message, it does NOT
		# assert on the exception message itself).
		with self.assertRaisesRegex(
			frappe.ValidationError,
			r"mandatory checklist item",
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

		# F-07: use assertRaisesRegex to verify the exception message content
		with self.assertRaisesRegex(
			frappe.ValidationError,
			r"ITIL mode",
		):
			complete_checklist_item(
				ticket=str(self.ticket.name), checklist_item_name=item.name
			)

		# Re-enable for remaining tearDown flow
		frappe.set_user("Administrator")
		frappe.db.set_single_value("HD Settings", "itil_mode_enabled", 1)
		frappe.set_user(self.agent_email)

	# ---------------------------------------------------------------
	# F-05 (QA report): Deleted HD Ticket Status raises ValidationError
	# ---------------------------------------------------------------

	def test_save_raises_validation_error_when_status_record_deleted(self):
		"""F-05: Saving a ticket whose HD Ticket Status record was deleted must
		raise our custom F-02 ValidationError with "no longer exists".

		set_status_category() runs in before_validate, which executes before
		Frappe's link validation (in validate).  This guarantees that our
		custom guard fires first and the error message contains "no longer
		exists", proving the F-02 guard is active — not just Frappe's built-in
		link validation ("Could not find Status: …").

		assertRaisesRegex(ValidationError, r"no longer exists") is used
		intentionally to prove the custom guard fires (not just any
		ValidationError subclass).
		"""
		# Create a throwaway HD Ticket Status record and point the ticket at it.
		ephemeral_status = f"EphemeralStatus-{frappe.generate_hash(length=6)}"
		frappe.set_user("Administrator")
		frappe.get_doc(
			{
				"doctype": "HD Ticket Status",
				"label_agent": ephemeral_status,
				"category": "Open",
				"is_default": 0,
			}
		).insert(ignore_permissions=True)
		frappe.db.commit()  # nosemgrep — commit so the insert is visible

		# Point the ticket at the new status and save (should succeed).
		doc = frappe.get_doc("HD Ticket", self.ticket.name)
		doc.status = ephemeral_status
		doc.save(ignore_permissions=True)
		frappe.db.commit()  # nosemgrep

		# Now delete the HD Ticket Status record to simulate a deleted status.
		frappe.delete_doc(
			"HD Ticket Status", ephemeral_status, ignore_permissions=True, force=True
		)
		# Invalidate the document cache so get_cached_value sees the deleted
		# state rather than returning the stale "Open" category from cache.
		frappe.clear_document_cache("HD Ticket Status", ephemeral_status)
		frappe.db.commit()  # nosemgrep — commit the delete

		# Reload and attempt to re-save — set_status_category() should detect
		# the missing record and raise ValidationError with a clear message.
		doc.reload()
		# Confirm the status field still points to the now-deleted record.
		self.assertEqual(doc.status, ephemeral_status)

		# Bypass Frappe's built-in link validation so our custom F-02 guard is
		# the error that surfaces.  In document.py, _validate_links() runs at
		# line 553 BEFORE run_before_save_methods() (line 554), which means
		# Frappe's LinkValidationError fires before before_validate reaches
		# set_status_category().  doc.flags.ignore_links = True is the standard
		# Frappe mechanism to suppress _validate_links() on a per-save basis,
		# letting our guard in before_validate run instead.
		doc.flags.ignore_links = True
		with self.assertRaisesRegex(frappe.ValidationError, r"no longer exists"):
			doc.save(ignore_permissions=True)

		# Restore ticket to a valid status so tearDown doesn't trip over it.
		frappe.set_value("HD Ticket", doc.name, "status", self.ticket.status)
		frappe.db.commit()  # nosemgrep
		frappe.set_user(self.agent_email)

	# ---------------------------------------------------------------
	# F-13: falsy status must clear status_category to None
	# ---------------------------------------------------------------

	def test_falsy_status_clears_status_category(self):
		"""F-13: When status is empty/falsy, set_status_category() must set
		status_category to None so downstream guards never see a stale value.

		Commit 0a45dc533 added this guard.  This test covers the specific path:
		  1. status_category has a non-None value ("Open")
		  2. status is set to empty string
		  3. set_status_category() is called (before_validate hook)
		  4. status_category must be None (not the stale "Open")
		"""
		doc = frappe.get_doc("HD Ticket", self.ticket.name)
		# Seed a known non-None status_category to prove it gets cleared.
		doc.status_category = "Open"
		# Clear status to simulate the falsy-status path (empty string).
		doc.status = ""
		# Call the hook directly — same path triggered by before_validate.
		doc.set_status_category()
		self.assertIsNone(
			doc.status_category,
			"Expected status_category=None when status is empty string, "
			"but got a stale non-None value — F-13 guard not working",
		)

		# Also verify None status (not just empty string) clears status_category.
		doc.status_category = "Open"
		doc.status = None
		doc.set_status_category()
		self.assertIsNone(
			doc.status_category,
			"Expected status_category=None when status is None, "
			"but got a stale non-None value — F-13 guard not working for None",
		)

	def test_save_raises_validation_error_when_status_has_no_category(self):
		"""F-02 path (b): Saving a ticket whose HD Ticket Status record exists
		but has an empty category field must raise ValidationError with the
		message "exists but has no category assigned".

		This tests the branch in set_status_category() that distinguishes:
		  (a) record does not exist → "no longer exists"
		  (b) record exists but category is blank → "exists but has no category assigned"

		We insert with a valid category first (so document validation passes),
		then directly wipe the category via frappe.db.set_value and clear the
		document cache so get_cached_value reflects the empty value.
		"""
		empty_cat_status = f"EmptyCatStatus-{frappe.generate_hash(length=6)}"
		frappe.set_user("Administrator")
		frappe.get_doc(
			{
				"doctype": "HD Ticket Status",
				"label_agent": empty_cat_status,
				"category": "Open",
				"is_default": 0,
			}
		).insert(ignore_permissions=True)
		# Directly wipe the category field in DB to simulate a status record
		# that exists but has no category assigned (bypasses doc validation
		# which would normally require category to be set).
		frappe.db.set_value("HD Ticket Status", empty_cat_status, "category", "")
		# Invalidate the document cache so get_cached_value sees the empty value.
		frappe.clear_document_cache("HD Ticket Status", empty_cat_status)
		frappe.db.commit()  # nosemgrep

		try:
			# Point the ticket at the status with empty category.
			doc = frappe.get_doc("HD Ticket", self.ticket.name)
			doc.status = empty_cat_status
			# set_status_category() must detect category="" and raise the
			# F-02 path (b) error: "exists but has no category assigned".
			with self.assertRaisesRegex(
				frappe.ValidationError,
				r"exists but has no category assigned",
			):
				doc.save(ignore_permissions=True)
		finally:
			# Clean up the throwaway status record.
			frappe.delete_doc(
				"HD Ticket Status", empty_cat_status, ignore_permissions=True, force=True
			)
			frappe.db.commit()  # nosemgrep
			frappe.set_user(self.agent_email)
