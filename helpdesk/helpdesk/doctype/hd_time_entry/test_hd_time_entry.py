# Copyright (c) 2026, Frappe Technologies Pvt. Ltd. and contributors
# For license information, please see license.txt

import frappe
from frappe.tests.utils import FrappeTestCase
from helpdesk.api.time_tracking import add_entry, stop_timer, get_summary, delete_entry, start_timer
from helpdesk.test_utils import create_agent, make_ticket


class TestHDTimeEntry(FrappeTestCase):
	"""Unit tests for Story 1.7: Per-Ticket Time Tracking."""

	def setUp(self):
		frappe.set_user("Administrator")
		create_agent("agent.tt@test.com", "Time", "Agent")
		ticket = make_ticket(
			subject="Time Tracking Test Ticket",
			raised_by="customer.tt@test.com",
		)
		# HD Ticket uses autoincrement naming; always use str() for API calls
		self.ticket_name = str(ticket.name)
		frappe.set_user("agent.tt@test.com")

	def tearDown(self):
		frappe.set_user("Administrator")
		frappe.db.rollback()

	# --- add_entry tests ---

	def test_add_entry_creates_time_entry(self):
		result = add_entry(
			ticket=self.ticket_name,
			duration_minutes=30,
			description="Investigated the issue",
			billable=1,
		)
		self.assertTrue(result.get("success"))
		entry = frappe.get_doc("HD Time Entry", result["name"])
		self.assertEqual(str(entry.ticket), self.ticket_name)
		self.assertEqual(entry.agent, "agent.tt@test.com")
		self.assertEqual(entry.duration_minutes, 30)
		self.assertEqual(entry.billable, 1)
		self.assertEqual(entry.description, "Investigated the issue")

	def test_add_entry_with_zero_duration_raises_validation_error(self):
		with self.assertRaises(frappe.ValidationError):
			add_entry(ticket=self.ticket_name, duration_minutes=0)

	def test_add_entry_with_negative_duration_raises_validation_error(self):
		with self.assertRaises(frappe.ValidationError):
			add_entry(ticket=self.ticket_name, duration_minutes=-5)

	# --- stop_timer tests ---

	def test_stop_timer_creates_entry_with_started_at(self):
		started_at = "2026-03-23 10:00:00"
		result = stop_timer(
			ticket=self.ticket_name,
			started_at=started_at,
			duration_minutes=45,
			description="Timer session",
			billable=0,
		)
		self.assertTrue(result.get("success"))
		entry = frappe.get_doc("HD Time Entry", result["name"])
		self.assertEqual(entry.duration_minutes, 45)
		self.assertEqual(str(entry.started_at), started_at)

	def test_stop_timer_rejects_future_started_at(self):
		"""started_at in the future must raise ValidationError."""
		with self.assertRaises(frappe.ValidationError):
			stop_timer(
				ticket=self.ticket_name,
				started_at="2099-01-01 00:00:00",
				duration_minutes=10,
			)

	def test_stop_timer_rejects_invalid_started_at_format(self):
		"""Unparseable started_at must raise ValidationError."""
		with self.assertRaises(frappe.ValidationError):
			stop_timer(
				ticket=self.ticket_name,
				started_at="not-a-datetime",
				duration_minutes=10,
			)

	# --- get_summary tests ---

	def test_get_summary_returns_correct_totals(self):
		add_entry(ticket=self.ticket_name, duration_minutes=60, billable=1)
		add_entry(ticket=self.ticket_name, duration_minutes=30, billable=0)
		add_entry(ticket=self.ticket_name, duration_minutes=15, billable=1)

		summary = get_summary(ticket=self.ticket_name)
		self.assertEqual(summary["total_minutes"], 105)
		self.assertEqual(summary["billable_minutes"], 75)
		self.assertEqual(len(summary["entries"]), 3)

	def test_get_summary_returns_zeroes_for_empty_ticket(self):
		summary = get_summary(ticket=self.ticket_name)
		self.assertEqual(summary["total_minutes"], 0)
		self.assertEqual(summary["billable_minutes"], 0)
		self.assertEqual(summary["entries"], [])

	def test_get_summary_entries_sorted_descending_by_timestamp(self):
		add_entry(ticket=self.ticket_name, duration_minutes=10, billable=0)
		add_entry(ticket=self.ticket_name, duration_minutes=20, billable=0)
		summary = get_summary(ticket=self.ticket_name)
		timestamps = [e["timestamp"] for e in summary["entries"]]
		self.assertEqual(
			timestamps,
			sorted(timestamps, reverse=True),
			"Entries should be sorted newest first",
		)

	def test_get_summary_blocked_for_customer(self):
		"""Customers should not be able to access time summary data."""
		add_entry(ticket=self.ticket_name, duration_minutes=30, billable=1)
		frappe.set_user("customer.tt@test.com")
		with self.assertRaises(frappe.PermissionError):
			get_summary(ticket=self.ticket_name)
		frappe.set_user("agent.tt@test.com")

	# --- delete_entry tests ---

	def test_delete_entry_removes_own_entry(self):
		result = add_entry(ticket=self.ticket_name, duration_minutes=20, billable=0)
		entry_name = result["name"]
		del_result = delete_entry(name=entry_name)
		self.assertTrue(del_result.get("success"))
		self.assertFalse(frappe.db.exists("HD Time Entry", entry_name))

	def test_delete_entry_raises_permission_error_for_other_agent(self):
		frappe.set_user("Administrator")
		create_agent("agent2.tt@test.com", "Agent", "Two")
		frappe.set_user("agent.tt@test.com")

		# agent.tt creates an entry
		result = add_entry(ticket=self.ticket_name, duration_minutes=10, billable=0)
		entry_name = result["name"]

		# agent2.tt tries to delete it
		frappe.set_user("agent2.tt@test.com")
		with self.assertRaises(frappe.PermissionError):
			delete_entry(name=entry_name)
		frappe.set_user("agent.tt@test.com")

	def test_delete_entry_admin_can_delete_any_entry(self):
		"""HD Admin role should be able to delete another agent's time entry."""
		# agent.tt creates an entry
		result = add_entry(ticket=self.ticket_name, duration_minutes=25, billable=0)
		entry_name = result["name"]

		# Create an admin user and assign HD Admin role
		frappe.set_user("Administrator")
		if not frappe.db.exists("User", "hd.admin.tt@test.com"):
			admin_user = frappe.get_doc({
				"doctype": "User",
				"email": "hd.admin.tt@test.com",
				"first_name": "HD",
				"last_name": "Admin",
				"send_welcome_email": 0,
			})
			admin_user.insert(ignore_permissions=True)
			admin_user.add_roles("HD Admin")

		frappe.set_user("hd.admin.tt@test.com")
		del_result = delete_entry(name=entry_name)
		self.assertTrue(del_result.get("success"))
		self.assertFalse(frappe.db.exists("HD Time Entry", entry_name))
		frappe.set_user("Administrator")

	# --- Permission tests ---

	def test_customer_cannot_add_entry(self):
		frappe.set_user("customer.tt@test.com")
		with self.assertRaises(frappe.PermissionError):
			add_entry(ticket=self.ticket_name, duration_minutes=30)
		frappe.set_user("agent.tt@test.com")

	def test_customer_cannot_delete_entry(self):
		"""Customers must not be able to call delete_entry (is_agent gate)."""
		result = add_entry(ticket=self.ticket_name, duration_minutes=10, billable=0)
		entry_name = result["name"]
		frappe.set_user("customer.tt@test.com")
		with self.assertRaises(frappe.PermissionError):
			delete_entry(name=entry_name)
		frappe.set_user("agent.tt@test.com")

	# --- start_timer tests ---

	def test_start_timer_returns_started_at(self):
		"""Happy-path: agent calls start_timer and gets a started_at timestamp."""
		result = start_timer(ticket=self.ticket_name)
		self.assertIn("started_at", result)
		self.assertIsInstance(result["started_at"], str)
		self.assertTrue(len(result["started_at"]) > 0)

	def test_start_timer_blocked_for_customer(self):
		"""Customers must not be able to call start_timer (is_agent gate)."""
		frappe.set_user("customer.tt@test.com")
		with self.assertRaises(frappe.PermissionError):
			start_timer(ticket=self.ticket_name)
		frappe.set_user("agent.tt@test.com")

	# --- description length validation tests ---

	def test_stop_timer_rejects_description_over_500_chars(self):
		"""stop_timer must reject descriptions longer than 500 characters."""
		long_description = "x" * 501
		with self.assertRaises(frappe.ValidationError):
			stop_timer(
				ticket=self.ticket_name,
				started_at="2026-03-23 10:00:00",
				duration_minutes=10,
				description=long_description,
			)

	def test_add_entry_rejects_description_over_500_chars(self):
		"""add_entry must reject descriptions longer than 500 characters."""
		long_description = "a" * 501
		with self.assertRaises(frappe.ValidationError):
			add_entry(
				ticket=self.ticket_name,
				duration_minutes=10,
				description=long_description,
			)

	def test_stop_timer_accepts_description_of_exactly_500_chars(self):
		"""500-character description is at the boundary and must be accepted."""
		boundary_description = "b" * 500
		result = stop_timer(
			ticket=self.ticket_name,
			started_at="2026-03-23 10:00:00",
			duration_minutes=5,
			description=boundary_description,
		)
		self.assertTrue(result.get("success"))

	def test_add_entry_accepts_description_of_exactly_500_chars(self):
		"""500-character description is at the boundary and must be accepted."""
		boundary_description = "c" * 500
		result = add_entry(
			ticket=self.ticket_name,
			duration_minutes=5,
			description=boundary_description,
		)
		self.assertTrue(result.get("success"))

	# --- Timezone-aware started_at tests (Issue #1 fix) ---

	def test_stop_timer_handles_tz_aware_started_at(self):
		"""
		stop_timer must not crash when started_at includes UTC offset (tz-aware datetime).
		Previously raised TypeError: can't compare offset-naive and offset-aware datetimes.
		"""
		# ISO 8601 with UTC offset — get_datetime() returns tz-aware for this format
		tz_aware_started_at = "2026-03-23T10:00:00+00:00"
		result = stop_timer(
			ticket=self.ticket_name,
			started_at=tz_aware_started_at,
			duration_minutes=15,
			description="Tz-aware session",
			billable=0,
		)
		self.assertTrue(result.get("success"))

	def test_stop_timer_tz_aware_future_still_rejected(self):
		"""
		A tz-aware started_at that is in the future must still be rejected,
		even though we strip tzinfo for comparison.
		"""
		with self.assertRaises(frappe.ValidationError):
			stop_timer(
				ticket=self.ticket_name,
				started_at="2099-06-01T00:00:00+00:00",
				duration_minutes=5,
			)

	# --- before_delete ownership hook tests (Issue #2 fix) ---

	def test_before_delete_hook_blocks_other_agent_from_direct_delete(self):
		"""
		The before_delete hook must raise PermissionError when a different agent calls it.
		This simulates the REST DELETE /api/resource/HD Time Entry/{name} bypass scenario.
		We call entry_doc.before_delete() directly because the Frappe test framework may
		run with elevated permissions that skip the doctype-level delete permission check.
		"""
		frappe.set_user("Administrator")
		create_agent("agent3.tt@test.com", "Agent", "Three")
		frappe.set_user("agent.tt@test.com")

		result = add_entry(ticket=self.ticket_name, duration_minutes=10, billable=0)
		entry_name = result["name"]

		# Load the entry doc as agent3 and invoke the hook directly
		entry_doc = frappe.get_doc("HD Time Entry", entry_name)
		frappe.set_user("agent3.tt@test.com")
		with self.assertRaises(frappe.PermissionError):
			entry_doc.before_delete()
		frappe.set_user("agent.tt@test.com")

	def test_before_delete_hook_allows_own_entry_direct_delete(self):
		"""
		The before_delete hook must allow an agent to delete their own entry via direct delete.
		"""
		result = add_entry(ticket=self.ticket_name, duration_minutes=10, billable=0)
		entry_name = result["name"]
		# Direct delete by owner — should succeed
		frappe.delete_doc("HD Time Entry", entry_name, ignore_permissions=True)
		self.assertFalse(frappe.db.exists("HD Time Entry", entry_name))

	# --- Issue #2 fix: tz-aware started_at with non-UTC offset ---

	def test_stop_timer_ist_offset_not_rejected_as_future(self):
		"""
		A started_at with +05:30 (IST) that is in the past relative to UTC must
		NOT be rejected as future.

		Previously, replace(tzinfo=None) kept the wall-clock time (e.g. 23:50)
		without converting, making it appear as "23:50 local" against a UTC server
		clock — incorrectly rejected as future when UTC equivalent was only 18:20.
		"""
		# 2020-01-01T23:50:00+05:30 = 2020-01-01T18:20:00Z — clearly in the past
		result = stop_timer(
			ticket=self.ticket_name,
			started_at="2020-01-01T23:50:00+05:30",
			duration_minutes=15,
			description="IST offset session",
			billable=0,
		)
		self.assertTrue(result.get("success"))

	# --- Issue #3/#4 fix: description length enforced at model layer (direct REST bypass) ---

	def test_validate_rejects_description_over_500_chars_via_direct_insert(self):
		"""
		validate() must catch description > 500 chars even on direct REST insert,
		bypassing the API layer check in time_tracking.py.
		"""
		with self.assertRaises(frappe.ValidationError):
			frappe.get_doc(
				{
					"doctype": "HD Time Entry",
					"ticket": self.ticket_name,
					"agent": "agent.tt@test.com",
					"duration_minutes": 10,
					"description": "x" * 501,
					"timestamp": frappe.utils.now_datetime(),
				}
			).insert(ignore_permissions=True)

	# --- Issue #13 fix: upper bound on duration_minutes ---

	def test_validate_rejects_duration_over_max(self):
		"""
		validate() must reject duration_minutes > MAX_DURATION_MINUTES (1440 / 24 h).
		"""
		from helpdesk.helpdesk.doctype.hd_time_entry.hd_time_entry import MAX_DURATION_MINUTES

		with self.assertRaises(frappe.ValidationError):
			add_entry(
				ticket=self.ticket_name,
				duration_minutes=MAX_DURATION_MINUTES + 1,
			)

	def test_validate_accepts_duration_at_max_boundary(self):
		"""Duration equal to MAX_DURATION_MINUTES (1440) must be accepted."""
		from helpdesk.helpdesk.doctype.hd_time_entry.hd_time_entry import MAX_DURATION_MINUTES

		result = add_entry(
			ticket=self.ticket_name,
			duration_minutes=MAX_DURATION_MINUTES,
		)
		self.assertTrue(result.get("success"))

	# --- P1 fix: is_agent gate for stop_timer ---

	def test_customer_cannot_stop_timer(self):
		"""Customers must not be able to call stop_timer (is_agent gate — P1 fix)."""
		frappe.set_user("customer.tt@test.com")
		with self.assertRaises(frappe.PermissionError):
			stop_timer(
				ticket=self.ticket_name,
				started_at="2026-03-23 10:00:00",
				duration_minutes=10,
			)
		frappe.set_user("agent.tt@test.com")

	# --- P1 fix: Agent Manager in exemption list for delete_entry and before_delete ---

	def _ensure_agent_manager_user(self):
		"""Create agent.mgr.tt@test.com with Agent Manager role if not present."""
		frappe.set_user("Administrator")
		if not frappe.db.exists("User", "agent.mgr.tt@test.com"):
			mgr_user = frappe.get_doc({
				"doctype": "User",
				"email": "agent.mgr.tt@test.com",
				"first_name": "Agent",
				"last_name": "Manager",
				"send_welcome_email": 0,
			})
			mgr_user.insert(ignore_permissions=True)
			mgr_user.add_roles("Agent Manager")

	def test_agent_manager_can_delete_any_entry_via_delete_entry(self):
		"""
		Agent Manager must be able to delete another agent's entry via delete_entry()
		— previously Agent Manager was excluded from privileged_roles causing a
		contradiction with delete:1 in the DocType JSON (P1 fix #1).
		"""
		result = add_entry(ticket=self.ticket_name, duration_minutes=20, billable=0)
		entry_name = result["name"]

		self._ensure_agent_manager_user()
		frappe.set_user("agent.mgr.tt@test.com")
		del_result = delete_entry(name=entry_name)
		self.assertTrue(del_result.get("success"))
		self.assertFalse(frappe.db.exists("HD Time Entry", entry_name))
		frappe.set_user("Administrator")

	def test_before_delete_hook_allows_agent_manager_to_delete_any_entry(self):
		"""
		The before_delete hook must allow an Agent Manager to delete another
		agent's entry via direct delete (REST bypass path — P1 fix #1).
		"""
		result = add_entry(ticket=self.ticket_name, duration_minutes=10, billable=0)
		entry_name = result["name"]
		entry_doc = frappe.get_doc("HD Time Entry", entry_name)

		self._ensure_agent_manager_user()
		frappe.set_user("agent.mgr.tt@test.com")
		# before_delete() must NOT raise PermissionError for Agent Manager
		try:
			entry_doc.before_delete()
		except frappe.PermissionError:
			self.fail("Agent Manager should be allowed to delete any entry via before_delete()")
		frappe.set_user("Administrator")
