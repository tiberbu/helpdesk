# Copyright (c) 2026, Frappe Technologies Pvt. Ltd. and contributors
# For license information, please see license.txt

import datetime

import frappe
from frappe.tests.utils import FrappeTestCase
from frappe.utils import now_datetime
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
		# Use a safely past date to avoid time-of-day fragility after duration cross-check
		started_at = "2026-01-01 10:00:00"
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

	def _ensure_hd_admin_user(self):
		"""Create hd.admin.tt@test.com with HD Admin role only (no Agent role)."""
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

	def test_delete_entry_admin_can_delete_any_entry(self):
		"""HD Admin role should be able to delete another agent's time entry."""
		# agent.tt creates an entry
		result = add_entry(ticket=self.ticket_name, duration_minutes=25, billable=0)
		entry_name = result["name"]

		self._ensure_hd_admin_user()
		frappe.set_user("hd.admin.tt@test.com")
		del_result = delete_entry(name=entry_name)
		self.assertTrue(del_result.get("success"))
		self.assertFalse(frappe.db.exists("HD Time Entry", entry_name))
		frappe.set_user("Administrator")

	# --- HD Admin add_entry / start_timer tests ---

	def test_hd_admin_can_add_entry(self):
		"""
		HD Admin user (no Agent role) must be able to call add_entry() and create
		a time entry — verifies the full is_agent() permission chain for HD Admin.
		"""
		self._ensure_hd_admin_user()
		frappe.set_user("hd.admin.tt@test.com")
		result = add_entry(
			ticket=self.ticket_name,
			duration_minutes=15,
			description="HD Admin manual entry",
			billable=0,
		)
		self.assertTrue(result.get("success"))
		entry = frappe.get_doc("HD Time Entry", result["name"])
		self.assertEqual(entry.duration_minutes, 15)
		self.assertEqual(entry.agent, "hd.admin.tt@test.com")
		frappe.set_user("Administrator")

	def test_hd_admin_can_start_timer(self):
		"""
		HD Admin user (no Agent role) must be able to call start_timer() and receive
		a started_at timestamp — verifies is_agent() gate passes for HD Admin role.
		"""
		self._ensure_hd_admin_user()
		frappe.set_user("hd.admin.tt@test.com")
		result = start_timer(ticket=self.ticket_name)
		self.assertIn("started_at", result)
		self.assertIsInstance(result["started_at"], str)
		self.assertTrue(len(result["started_at"]) > 0)
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
				started_at="2026-01-01 10:00:00",
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
			started_at="2026-01-01 10:00:00",
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
		# Use a safely past date to avoid duration cross-check fragility
		tz_aware_started_at = "2026-01-01T10:00:00+00:00"
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

	# --- on_trash ownership hook tests (Issue #2 fix) ---

	def test_on_trash_blocks_other_agent_from_direct_delete(self):
		"""
		The on_trash hook must raise PermissionError when a different agent calls it.
		This simulates the REST DELETE /api/resource/HD Time Entry/{name} bypass scenario.
		We call entry_doc.on_trash() directly because the Frappe test framework may
		run with elevated permissions that skip the doctype-level delete permission check.
		Note: Frappe calls on_trash (not before_delete) from frappe.delete_doc().
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
			entry_doc.on_trash()
		frappe.set_user("agent.tt@test.com")

	def test_on_trash_allows_own_entry_direct_delete(self):
		"""
		The on_trash hook must allow an agent to delete their own entry via direct delete.
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
				started_at="2026-01-01 10:00:00",
				duration_minutes=10,
			)
		frappe.set_user("agent.tt@test.com")

	# --- P1 fix: Agent Manager in exemption list for delete_entry and on_trash ---

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

	def test_on_trash_allows_agent_manager_to_delete_any_entry(self):
		"""
		The on_trash hook must allow an Agent Manager to delete another
		agent's entry via direct delete (REST bypass path — P1 fix #1).
		Note: Frappe calls on_trash (not before_delete) from frappe.delete_doc().
		"""
		result = add_entry(ticket=self.ticket_name, duration_minutes=10, billable=0)
		entry_name = result["name"]
		entry_doc = frappe.get_doc("HD Time Entry", entry_name)

		self._ensure_agent_manager_user()
		frappe.set_user("agent.mgr.tt@test.com")
		# on_trash() must NOT raise PermissionError for Agent Manager
		entry_doc.on_trash()
		frappe.set_user("Administrator")

	def test_on_trash_allows_system_manager_to_delete_any_entry(self):
		"""
		The on_trash hook must allow a bare System Manager user (no Agent/HD Admin role)
		to delete another agent's entry via direct delete (REST bypass path).
		System Manager is in PRIVILEGED_ROLES so on_trash() must not raise PermissionError.
		"""
		result = add_entry(ticket=self.ticket_name, duration_minutes=10, billable=0)
		entry_name = result["name"]
		entry_doc = frappe.get_doc("HD Time Entry", entry_name)

		self._ensure_system_manager_user()
		frappe.set_user("sys.mgr.tt@test.com")
		# on_trash() must NOT raise PermissionError for System Manager
		entry_doc.on_trash()
		frappe.set_user("Administrator")

	def test_on_trash_allows_hd_admin_to_delete_any_entry(self):
		"""
		The on_trash hook must allow an HD Admin user (no Agent role) to delete
		another agent's entry via direct delete (REST bypass path).
		HD Admin is in PRIVILEGED_ROLES so on_trash() must not raise PermissionError.
		"""
		result = add_entry(ticket=self.ticket_name, duration_minutes=10, billable=0)
		entry_name = result["name"]
		entry_doc = frappe.get_doc("HD Time Entry", entry_name)

		self._ensure_hd_admin_user()
		frappe.set_user("hd.admin.tt@test.com")
		# on_trash() must NOT raise PermissionError for HD Admin
		entry_doc.on_trash()
		frappe.set_user("Administrator")

	# --- P2-3: API-layer MAX_DURATION_MINUTES enforcement for stop_timer ---

	def test_stop_timer_rejects_duration_over_max_at_api_layer(self):
		"""
		stop_timer must reject duration_minutes > MAX_DURATION_MINUTES (1440) at the API
		layer, before the document is constructed.
		"""
		from helpdesk.helpdesk.doctype.hd_time_entry.hd_time_entry import MAX_DURATION_MINUTES

		with self.assertRaises(frappe.ValidationError):
			stop_timer(
				ticket=self.ticket_name,
				started_at="2020-01-01 00:00:00",
				duration_minutes=MAX_DURATION_MINUTES + 1,
			)

	def test_stop_timer_accepts_duration_at_max_boundary(self):
		"""
		stop_timer must accept duration_minutes == MAX_DURATION_MINUTES (1440).
		"""
		from helpdesk.helpdesk.doctype.hd_time_entry.hd_time_entry import MAX_DURATION_MINUTES

		result = stop_timer(
			ticket=self.ticket_name,
			started_at="2020-01-01 00:00:00",
			duration_minutes=MAX_DURATION_MINUTES,
		)
		self.assertTrue(result.get("success"))

	# --- Story 102: non-numeric input validation (regression tests for cint() fix) ---

	def test_add_entry_rejects_non_numeric_duration(self):
		"""
		add_entry must raise ValidationError when duration_minutes is a non-numeric
		string — cint('abc') silently returns 0, which would be a confusing error.
		"""
		with self.assertRaises(frappe.ValidationError):
			add_entry(ticket=self.ticket_name, duration_minutes="abc")

	def test_stop_timer_rejects_non_numeric_billable(self):
		"""
		stop_timer must raise ValidationError when billable is a non-numeric string
		— cint('xyz') silently returns 0, coercing invalid input to non-billable.
		"""
		with self.assertRaises(frappe.ValidationError):
			stop_timer(
				ticket=self.ticket_name,
				started_at="2026-01-01 10:00:00",
				duration_minutes=10,
				billable="xyz",
			)

	def test_stop_timer_rejects_duration_exceeding_elapsed_time(self):
		"""
		stop_timer must raise ValidationError when duration_minutes exceeds the
		actual elapsed time since started_at (billing fraud prevention).
		Timer started ~2 minutes ago; claiming MAX_DURATION_MINUTES (1440 min) must fail.
		"""
		from helpdesk.helpdesk.doctype.hd_time_entry.hd_time_entry import MAX_DURATION_MINUTES

		# started_at = 2 minutes ago; timer cannot have run for 1440 minutes
		started_at = str(now_datetime() - datetime.timedelta(minutes=2))
		with self.assertRaises(frappe.ValidationError):
			stop_timer(
				ticket=self.ticket_name,
				started_at=started_at,
				duration_minutes=MAX_DURATION_MINUTES,
			)

	# --- P1: System Manager can delete any entry ---

	def _ensure_system_manager_user(self):
		"""Create sys.mgr.tt@test.com with System Manager role only (no Agent/HD Admin)."""
		frappe.set_user("Administrator")
		if not frappe.db.exists("User", "sys.mgr.tt@test.com"):
			sys_mgr_user = frappe.get_doc({
				"doctype": "User",
				"email": "sys.mgr.tt@test.com",
				"first_name": "Sys",
				"last_name": "Manager",
				"send_welcome_email": 0,
			})
			sys_mgr_user.insert(ignore_permissions=True)
			sys_mgr_user.add_roles("System Manager")

	def test_delete_entry_system_manager_can_delete_any_entry(self):
		"""
		A bare System Manager user (no Agent/HD Admin role) must be able to delete
		another agent's entry via delete_entry() — System Manager is in PRIVILEGED_ROLES.
		"""
		# agent.tt creates an entry
		result = add_entry(ticket=self.ticket_name, duration_minutes=18, billable=0)
		entry_name = result["name"]

		self._ensure_system_manager_user()
		frappe.set_user("sys.mgr.tt@test.com")
		del_result = delete_entry(name=entry_name)
		self.assertTrue(del_result.get("success"))
		self.assertFalse(frappe.db.exists("HD Time Entry", entry_name))
		frappe.set_user("Administrator")

	# --- P1: stop_timer must reject non-numeric duration_minutes ---

	def test_stop_timer_rejects_non_numeric_duration(self):
		"""
		stop_timer must raise ValidationError when duration_minutes is a non-numeric
		string — mirrors test_add_entry_rejects_non_numeric_duration for stop_timer.
		cint('abc') silently returns 0, which would be a confusing downstream error.
		"""
		with self.assertRaises(frappe.ValidationError):
			stop_timer(
				ticket=self.ticket_name,
				started_at="2026-01-01 10:00:00",
				duration_minutes="abc",
			)

	# --- P2: Missing coverage — non-numeric billable on add_entry ---

	def test_add_entry_rejects_non_numeric_billable(self):
		"""
		add_entry must raise ValidationError when billable is a non-numeric string.
		cint('xyz') silently returns 0, coercing invalid input to non-billable.
		Mirrors test_stop_timer_rejects_non_numeric_billable for the add_entry path.
		"""
		with self.assertRaises(frappe.ValidationError):
			add_entry(
				ticket=self.ticket_name,
				duration_minutes=10,
				billable="xyz",
			)

	# --- P2: Billable clamping boundary tests ---

	def test_add_entry_clamps_billable_above_one(self):
		"""
		add_entry must clamp billable=2 to 1 — a Check field only accepts 0 or 1.
		Values > 1 arise from programmatic callers passing raw integers.
		"""
		result = add_entry(
			ticket=self.ticket_name,
			duration_minutes=10,
			billable=2,
		)
		self.assertTrue(result.get("success"))
		entry = frappe.get_doc("HD Time Entry", result["name"])
		self.assertEqual(entry.billable, 1, "billable=2 must be clamped to 1")

	def test_add_entry_clamps_negative_billable_to_zero(self):
		"""
		add_entry must clamp billable=-1 to 0.
		Negative values are truthy in Python (bool(-1) is True), so a naive
		`1 if cint(billable) else 0` guard would incorrectly set billable=1.
		The correct guard uses max(0, min(1, cint(billable))).
		"""
		result = add_entry(
			ticket=self.ticket_name,
			duration_minutes=10,
			billable=-1,
		)
		self.assertTrue(result.get("success"))
		entry = frappe.get_doc("HD Time Entry", result["name"])
		self.assertEqual(entry.billable, 0, "billable=-1 must be clamped to 0")

	# --- P1 fix: _require_int_str edge cases (float strings, empty, whitespace, etc.) ---

	def test_require_int_str_accepts_float_string_duration(self):
		"""
		_require_int_str must accept float strings like '3.5' because cint('3.5') == 3
		(truncates). Previously int('3.5') raised ValueError, causing a P1 regression
		where valid browser inputs like '30.0' would be incorrectly rejected.
		"""
		# "30.0" is a common output of JS Number.toString() — must be accepted
		result = add_entry(
			ticket=self.ticket_name,
			duration_minutes="30.0",
			description="Float string duration",
			billable=0,
		)
		self.assertTrue(result.get("success"))
		entry = frappe.get_doc("HD Time Entry", result["name"])
		self.assertEqual(entry.duration_minutes, 30, "'30.0' must truncate to 30")

	def test_require_int_str_accepts_fractional_float_string_duration(self):
		"""
		'3.5' must be accepted and truncated to 3, matching cint('3.5') == 3 behavior.
		"""
		result = add_entry(
			ticket=self.ticket_name,
			duration_minutes="3.5",
			billable=0,
		)
		self.assertTrue(result.get("success"))
		entry = frappe.get_doc("HD Time Entry", result["name"])
		self.assertEqual(entry.duration_minutes, 3, "'3.5' must truncate to 3")

	def test_require_int_str_accepts_whitespace_padded_integer(self):
		"""
		'  10  ' (whitespace-padded) must be accepted — strip() is applied before parsing.
		"""
		result = add_entry(
			ticket=self.ticket_name,
			duration_minutes="  10  ",
			billable=0,
		)
		self.assertTrue(result.get("success"))
		entry = frappe.get_doc("HD Time Entry", result["name"])
		self.assertEqual(entry.duration_minutes, 10, "Whitespace-padded '  10  ' must parse to 10")

	def test_require_int_str_rejects_empty_string_duration(self):
		"""
		'' (empty string) must raise ValidationError — float('') raises ValueError.
		cint('') returns 0 and then the < 1 check would catch it, but _require_int_str
		must reject it first with a clear 'must be a valid integer' message.
		"""
		with self.assertRaises(frappe.ValidationError):
			add_entry(ticket=self.ticket_name, duration_minutes="")

	def test_require_int_str_rejects_whitespace_only_duration(self):
		"""
		'   ' (whitespace-only) must raise ValidationError — float('') raises ValueError
		after strip(). Prevents silent 0 from cint() leading to confusing error later.
		"""
		with self.assertRaises(frappe.ValidationError):
			add_entry(ticket=self.ticket_name, duration_minutes="   ")

	def test_require_int_str_accepts_boolean_true_duration(self):
		"""
		True (Python bool) must be accepted — booleans are not strings so _require_int_str
		passes through; cint(True) == 1. The < 1 check then rejects it (1 min minimum).
		This test documents the pass-through behavior for non-string types.
		"""
		# True coerces to 1 minute via cint(True)==1, which is >= 1 (valid)
		result = add_entry(ticket=self.ticket_name, duration_minutes=True, billable=0)
		self.assertTrue(result.get("success"))
		entry = frappe.get_doc("HD Time Entry", result["name"])
		self.assertEqual(entry.duration_minutes, 1, "True must coerce to 1 via cint()")

	def test_require_int_str_accepts_none_duration_as_zero_then_rejects(self):
		"""
		None is not a string so _require_int_str passes through; cint(None) == 0,
		which then fails the < 1 validation. Documents that None is handled gracefully.
		"""
		with self.assertRaises(frappe.ValidationError):
			add_entry(ticket=self.ticket_name, duration_minutes=None)

	def test_require_int_str_accepts_float_string_billable(self):
		"""
		'0.9' as billable must be accepted — cint('0.9') would truncate to 0 (non-billable).
		This covers stop_timer's billable param as well, using add_entry for simplicity.
		"""
		result = add_entry(
			ticket=self.ticket_name,
			duration_minutes=10,
			billable="0.9",
		)
		self.assertTrue(result.get("success"))
		entry = frappe.get_doc("HD Time Entry", result["name"])
		self.assertEqual(entry.billable, 0, "'0.9' must truncate to 0 (non-billable)")


class TestIsAgentExplicitUser(FrappeTestCase):
	"""
	Dedicated tests for is_agent(user=...) explicit user parameter.

	P1-2 fix: is_admin(user) parameter was silently added to is_agent() without tests.
	The change has global scope — all callers that pass user= must check THAT user,
	not frappe.session.user.
	"""

	def setUp(self):
		frappe.set_user("Administrator")
		# Create an agent user for is_agent() checks
		create_agent("is.agent.check@test.com", "IsAgent", "Check")
		# Create a non-agent (customer) user
		if not frappe.db.exists("User", "not.an.agent@test.com"):
			frappe.get_doc({
				"doctype": "User",
				"email": "not.an.agent@test.com",
				"first_name": "NotAgent",
				"last_name": "User",
				"send_welcome_email": 0,
			}).insert(ignore_permissions=True)

	def tearDown(self):
		frappe.set_user("Administrator")
		frappe.db.rollback()

	def test_is_agent_with_explicit_agent_user(self):
		"""
		is_agent(user='is.agent.check@test.com') must return True even when the
		current session user is someone else (e.g. the customer). This verifies the
		user parameter is actually used, not frappe.session.user.
		"""
		from helpdesk.utils import is_agent

		# Session user is NOT an agent
		frappe.set_user("not.an.agent@test.com")
		# But checking the explicit agent user must still return True
		result = is_agent(user="is.agent.check@test.com")
		self.assertTrue(
			result,
			"is_agent(user='is.agent.check@test.com') must return True regardless of session user",
		)

	def test_is_agent_with_explicit_non_agent_user(self):
		"""
		is_agent(user='not.an.agent@test.com') must return False even when the
		current session user IS an agent. Verifies the parameter is not ignored.
		"""
		from helpdesk.utils import is_agent

		# Session user IS an agent
		frappe.set_user("is.agent.check@test.com")
		# But checking the non-agent user must return False
		result = is_agent(user="not.an.agent@test.com")
		self.assertFalse(
			result,
			"is_agent(user='not.an.agent@test.com') must return False regardless of session user",
		)

	def test_is_agent_defaults_to_session_user_when_no_param(self):
		"""
		is_agent() with no arguments must check frappe.session.user, not a cached value.
		"""
		from helpdesk.utils import is_agent

		# Session is the agent — should return True
		frappe.set_user("is.agent.check@test.com")
		self.assertTrue(is_agent(), "is_agent() must return True when session user is an agent")

		# Session is the customer — should return False
		frappe.set_user("not.an.agent@test.com")
		self.assertFalse(is_agent(), "is_agent() must return False when session user is not an agent")

	def test_is_agent_administrator_always_returns_true(self):
		"""
		is_agent(user='Administrator') must always return True.
		Administrator is handled via is_admin() inside is_agent().
		"""
		from helpdesk.utils import is_agent

		frappe.set_user("not.an.agent@test.com")
		self.assertTrue(
			is_agent(user="Administrator"),
			"is_agent(user='Administrator') must always return True",
		)
