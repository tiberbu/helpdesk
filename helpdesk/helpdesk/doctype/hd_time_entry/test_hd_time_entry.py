# Copyright (c) 2026, Frappe Technologies Pvt. Ltd. and contributors
# For license information, please see license.txt

import datetime

import frappe
from frappe.tests.utils import FrappeTestCase
from frappe.utils import now_datetime
from helpdesk.api.time_tracking import add_entry, stop_timer, get_summary, delete_entry, start_timer
from helpdesk.test_utils import (
	create_agent,
	ensure_agent_manager_user,
	ensure_hd_admin_user,
	ensure_sm_agent_user,
	ensure_system_manager_user,
	make_ticket,
)


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
		"""Create hd.admin.tt@test.com with HD Admin role only (no Agent/Agent Manager/System Manager roles).

		Delegates to shared ensure_hd_admin_user() in test_utils — see story-130 Finding #7.
		Asserts user does NOT hold unexpected roles (story-130 Finding #5).
		"""
		ensure_hd_admin_user()

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
		self.assertEqual(entry.description, "HD Admin manual entry")
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

	def test_hd_admin_can_stop_timer(self):
		"""
		HD Admin user (no Agent role) must be able to call stop_timer() and create
		a time entry — verifies is_agent() gate passes for HD Admin role on the
		stop_timer() path, which has previously had zero coverage.
		"""
		self._ensure_hd_admin_user()
		frappe.set_user("hd.admin.tt@test.com")
		result = stop_timer(
			ticket=self.ticket_name,
			started_at="2026-01-01 10:00:00",
			duration_minutes=20,
			description="HD Admin timer session",
			billable=0,
		)
		self.assertTrue(result.get("success"))
		entry = frappe.get_doc("HD Time Entry", result["name"])
		self.assertEqual(entry.duration_minutes, 20)
		self.assertEqual(entry.agent, "hd.admin.tt@test.com")
		self.assertEqual(entry.description, "HD Admin timer session")
		frappe.set_user("Administrator")

	def test_hd_admin_can_get_summary(self):
		"""
		HD Admin user (no Agent role) must be able to call get_summary() and receive
		time tracking data — verifies is_agent() gate passes for HD Admin role on the
		get_summary() path, which has previously had zero coverage.
		"""
		# Agent creates an entry that the HD Admin should be able to see in the summary
		result = add_entry(ticket=self.ticket_name, duration_minutes=30, billable=1)
		self.assertTrue(result.get("success"))

		self._ensure_hd_admin_user()
		frappe.set_user("hd.admin.tt@test.com")
		summary = get_summary(ticket=self.ticket_name)
		self.assertEqual(summary["total_minutes"], 30)
		self.assertEqual(summary["billable_minutes"], 30)
		self.assertEqual(len(summary["entries"]), 1)
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
		"""Create agent.mgr.tt@test.com with Agent Manager role if not present.

		Delegates to shared ensure_agent_manager_user() in test_utils — see story-130 Finding #7.
		"""
		ensure_agent_manager_user()

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

	def test_on_trash_blocks_system_manager_delete(self):
		"""
		The on_trash hook must BLOCK a bare System Manager user (no Agent/HD Admin role)
		from deleting another agent's entry via direct REST DELETE.
		System Manager was removed from PRIVILEGED_ROLES (story-148 fix) to eliminate
		the split-personality where delete_entry() blocked System Manager but the REST
		DELETE path allowed it.  on_trash() now raises PermissionError for bare SM.
		"""
		result = add_entry(ticket=self.ticket_name, duration_minutes=10, billable=0)
		entry_name = result["name"]
		entry_doc = frappe.get_doc("HD Time Entry", entry_name)

		self._ensure_system_manager_user()
		frappe.set_user("sys.mgr.tt@test.com")
		try:
			# on_trash() MUST raise PermissionError for bare System Manager
			with self.assertRaises(frappe.PermissionError):
				entry_doc.on_trash()
		finally:
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

	# --- System Manager pre-gate check (non-agent must be blocked) ---

	def _ensure_system_manager_user(self):
		"""Create sys.mgr.tt@test.com with System Manager role only (no Agent/HD Admin).

		Delegates to shared ensure_system_manager_user() in test_utils — see story-130 Finding #7.
		"""
		ensure_system_manager_user()

	def test_delete_entry_system_manager_blocked_at_pre_gate(self):
		"""
		A bare System Manager user (no Agent/HD Admin/Agent role) must be blocked
		by the is_agent() pre-gate in delete_entry() — the previous PRIVILEGED_ROLES
		inline check created an unintended wider permission surface (story-142 fix).

		Isolation note: no frappe.db.commit() is called here.  The entry is created
		within the test transaction; tearDown's frappe.db.rollback() will clean it up
		automatically, keeping the test isolated from its neighbours.
		"""
		# agent.tt creates an entry
		result = add_entry(ticket=self.ticket_name, duration_minutes=18, billable=0)
		entry_name = result["name"]

		self._ensure_system_manager_user()
		frappe.set_user("sys.mgr.tt@test.com")
		try:
			with self.assertRaises(frappe.PermissionError):
				delete_entry(name=entry_name)
		finally:
			frappe.set_user("Administrator")
			# tearDown rolls back the open transaction — no explicit delete needed.

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

	# --- P1 fix: OverflowError for inf/Infinity via stop_timer path ---

	def test_require_int_str_rejects_inf_via_stop_timer(self):
		"""
		_require_int_str must raise ValidationError for 'inf' / 'Infinity'.

		int(float('inf')) raises OverflowError, NOT ValueError.  Previously only
		ValueError was caught, so passing billable='inf' produced an unhandled 500.
		This test exercises the stop_timer integration path to verify the fix is
		wired end-to-end (not just in the helper).
		"""
		with self.assertRaises(frappe.ValidationError):
			stop_timer(
				ticket=self.ticket_name,
				started_at="2026-01-01 10:00:00",
				duration_minutes=10,
				billable="inf",
			)

	def test_require_int_str_rejects_infinity_string_duration(self):
		"""
		'Infinity' passed as duration_minutes must raise ValidationError (OverflowError fix).
		"""
		with self.assertRaises(frappe.ValidationError):
			stop_timer(
				ticket=self.ticket_name,
				started_at="2026-01-01 10:00:00",
				duration_minutes="Infinity",
			)

	# --- P2: Billable clamping boundary tests for stop_timer ---

	def test_stop_timer_clamps_billable_above_one(self):
		"""
		stop_timer must clamp billable=2 to 1 — a Check field only accepts 0 or 1.
		Mirrors test_add_entry_clamps_billable_above_one for the stop_timer path.
		"""
		result = stop_timer(
			ticket=self.ticket_name,
			started_at="2026-01-01 10:00:00",
			duration_minutes=10,
			billable=2,
		)
		self.assertTrue(result.get("success"))
		entry = frappe.get_doc("HD Time Entry", result["name"])
		self.assertEqual(entry.billable, 1, "billable=2 must be clamped to 1")

	def test_stop_timer_clamps_negative_billable_to_zero(self):
		"""
		stop_timer must clamp billable=-1 to 0.
		Negative values are truthy in Python (bool(-1) is True), so a naive
		`1 if cint(billable) else 0` guard would incorrectly set billable=1.
		The correct guard uses max(0, min(1, cint(billable))).
		Mirrors test_add_entry_clamps_negative_billable_to_zero for the stop_timer path.
		"""
		result = stop_timer(
			ticket=self.ticket_name,
			started_at="2026-01-01 10:00:00",
			duration_minutes=10,
			billable=-1,
		)
		self.assertTrue(result.get("success"))
		entry = frappe.get_doc("HD Time Entry", result["name"])
		self.assertEqual(entry.billable, 0, "billable=-1 must be clamped to 0")

	# --- P1 fix: _require_int_str must reject inf/nan (OverflowError + ValueError) ---

	def test_require_int_str_rejects_inf_string_as_duration_add_entry(self):
		"""
		'inf' passed as duration_minutes to add_entry() must raise ValidationError.

		int(float('inf')) raises OverflowError (NOT ValueError), so the except clause
		must catch both. Previously only ValueError was caught, causing an unhandled
		500 Internal Server Error (flagged in QA reports task-114 and task-126).
		"""
		with self.assertRaises(frappe.ValidationError):
			add_entry(ticket=self.ticket_name, duration_minutes="inf")

	def test_require_int_str_rejects_negative_inf_string_duration(self):
		"""
		'-inf' passed as duration_minutes must raise ValidationError.
		int(float('-inf')) raises OverflowError — same OverflowError path as 'inf'.
		"""
		with self.assertRaises(frappe.ValidationError):
			add_entry(ticket=self.ticket_name, duration_minutes="-inf")

	def test_require_int_str_rejects_nan_string_duration(self):
		"""
		'nan' passed as duration_minutes must raise ValidationError.
		int(float('nan')) raises ValueError (not OverflowError), but the combined
		except (ValueError, OverflowError) clause handles it correctly.
		"""
		with self.assertRaises(frappe.ValidationError):
			add_entry(ticket=self.ticket_name, duration_minutes="nan")

	# --- P2: Missing coverage — inf billable on add_entry, nan duration on stop_timer ---

	def test_add_entry_rejects_inf_billable(self):
		"""
		add_entry must raise ValidationError when billable='inf'.
		int(float('inf')) raises OverflowError, which _require_int_str must catch.
		Mirrors test_require_int_str_rejects_inf_via_stop_timer for the add_entry path.
		"""
		with self.assertRaises(frappe.ValidationError):
			add_entry(
				ticket=self.ticket_name,
				duration_minutes=10,
				billable="inf",
			)

	def test_stop_timer_rejects_nan_duration(self):
		"""
		stop_timer must raise ValidationError when duration_minutes='nan'.
		int(float('nan')) raises ValueError, which _require_int_str must catch.
		Mirrors test_require_int_str_rejects_nan_string_duration for the stop_timer path.
		"""
		with self.assertRaises(frappe.ValidationError):
			stop_timer(
				ticket=self.ticket_name,
				started_at="2026-01-01 10:00:00",
				duration_minutes="nan",
			)

	# --- P2-3: Python float NaN/Inf bypass guard (not string — previously silently coerced) ---

	def test_require_int_str_rejects_float_nan_python_float(self):
		"""
		float('nan') as a Python float must raise ValidationError.

		Previously _require_int_str only guarded string inputs (isinstance(value, str)),
		so float('nan') passed through silently and cint(float('nan')) returned 0,
		corrupting the duration with no error (P2-2 bug).
		"""
		with self.assertRaises(frappe.ValidationError):
			add_entry(ticket=self.ticket_name, duration_minutes=float("nan"))

	def test_require_int_str_rejects_float_inf_python_float(self):
		"""
		float('inf') as a Python float must raise ValidationError.

		Same bypass as float('nan'): isinstance(float('inf'), str) is False,
		so the string branch never fires, and cint(float('inf')) returns 0.
		"""
		with self.assertRaises(frappe.ValidationError):
			add_entry(ticket=self.ticket_name, duration_minutes=float("inf"))

	def test_require_int_str_rejects_float_negative_inf_python_float(self):
		"""
		float('-inf') as a Python float must raise ValidationError.
		"""
		with self.assertRaises(frappe.ValidationError):
			add_entry(ticket=self.ticket_name, duration_minutes=float("-inf"))

	# --- P2-1: 1e309 overflows to inf → OverflowError must be caught ---

	def test_require_int_str_rejects_1e309_overflow_duration(self):
		"""
		'1e309' passed as duration_minutes must raise ValidationError.

		float('1e309') evaluates to float('inf') because it overflows the IEEE 754
		double range, and int(float('inf')) raises OverflowError.  The task
		description for story-133 explicitly listed '1e309' as a required test case
		alongside 'inf', 'nan', '-inf', but it was omitted from the original
		implementation.
		"""
		with self.assertRaises(frappe.ValidationError):
			add_entry(ticket=self.ticket_name, duration_minutes="1e309")

	# --- P2-3: stop_timer with billable='nan' must be rejected ---

	def test_stop_timer_rejects_nan_billable(self):
		"""
		stop_timer must raise ValidationError when billable='nan'.

		int(float('nan')) raises ValueError, which _require_int_str must catch.
		This completes the inf/nan matrix: stop_timer + billable='inf' was already
		tested in test_require_int_str_rejects_inf_via_stop_timer, but the nan
		case on the billable param was missing (P2-3 from QA report task-140).
		"""
		with self.assertRaises(frappe.ValidationError):
			stop_timer(
				ticket=self.ticket_name,
				started_at="2026-01-01 10:00:00",
				duration_minutes=10,
				billable="nan",
			)

	# --- P2: Scientific notation string behavior (documented, not rejected) ---

	def test_require_int_str_documents_scientific_notation_accepted(self):
		"""
		Scientific notation strings like '1e2' are ACCEPTED by _require_int_str
		because float('1e2') == 100.0 is a valid float.  cint('1e2') also evaluates
		to 100, so the behavior is internally consistent.

		This test documents the deliberate decision to NOT reject scientific notation:
		- It is unlikely to appear from real browser inputs.
		- Rejecting it would require a regex, adding complexity with no practical benefit.
		- Behavior is consistent: '1e2' → 100 min, same as passing 100 directly.
		"""
		result = add_entry(
			ticket=self.ticket_name,
			duration_minutes="1e2",
			billable=0,
		)
		self.assertTrue(result.get("success"))
		entry = frappe.get_doc("HD Time Entry", result["name"])
		self.assertEqual(entry.duration_minutes, 100, "'1e2' must evaluate to 100")


	# --- Negative tests: bare System Manager blocked on all API endpoints ---

	def test_system_manager_cannot_add_entry(self):
		"""
		A bare System Manager user (no Agent/HD Admin role) must be blocked
		by the is_agent() pre-gate in add_entry() — verifies that the pre-gate
		is effective for all write endpoints, not just delete_entry.
		"""
		# Create an entry as agent first so the ticket exists in a valid state.
		# Then switch to System Manager to verify add_entry is blocked.
		self._ensure_system_manager_user()
		frappe.set_user("sys.mgr.tt@test.com")
		try:
			with self.assertRaises(frappe.PermissionError):
				add_entry(ticket=self.ticket_name, duration_minutes=10, billable=0)
		finally:
			frappe.set_user("Administrator")

	def test_system_manager_cannot_start_timer(self):
		"""
		A bare System Manager user (no Agent/HD Admin role) must be blocked
		by the is_agent() pre-gate in start_timer().
		"""
		self._ensure_system_manager_user()
		frappe.set_user("sys.mgr.tt@test.com")
		try:
			with self.assertRaises(frappe.PermissionError):
				start_timer(ticket=self.ticket_name)
		finally:
			frappe.set_user("Administrator")

	def test_system_manager_cannot_stop_timer(self):
		"""
		A bare System Manager user (no Agent/HD Admin role) must be blocked
		by the is_agent() pre-gate in stop_timer().
		"""
		self._ensure_system_manager_user()
		frappe.set_user("sys.mgr.tt@test.com")
		try:
			with self.assertRaises(frappe.PermissionError):
				stop_timer(
					ticket=self.ticket_name,
					started_at="2026-01-01 10:00:00",
					duration_minutes=10,
				)
		finally:
			frappe.set_user("Administrator")

	def test_system_manager_cannot_get_summary(self):
		"""
		A bare System Manager user (no Agent/HD Admin role) must be blocked
		by the is_agent() pre-gate in get_summary() — customers and non-agents
		must not see internal time tracking / billing data.
		"""
		# Create an entry as agent so the summary would have data if the block fails
		frappe.set_user("agent.tt@test.com")
		add_entry(ticket=self.ticket_name, duration_minutes=30, billable=1)

		self._ensure_system_manager_user()
		frappe.set_user("sys.mgr.tt@test.com")
		try:
			with self.assertRaises(frappe.PermissionError):
				get_summary(ticket=self.ticket_name)
		finally:
			frappe.set_user("Administrator")

	def test_system_manager_cannot_delete_via_on_trash(self):
		"""
		A bare System Manager user who owns their own entry (created via direct
		REST POST) must still be blocked by the is_agent() pre-gate in on_trash().

		This tests the specific vulnerability described in Finding 2 of
		qa-report-task-148.md: entry.agent == user passes _check_delete_permission,
		but the is_agent() pre-gate in on_trash() must catch it first.
		"""
		# Create an entry as agent, then load it and pretend System Manager owns it
		frappe.set_user("agent.tt@test.com")
		result = add_entry(ticket=self.ticket_name, duration_minutes=10, billable=0)
		entry_name = result["name"]

		# Manually set agent to sys.mgr.tt@test.com to simulate REST POST creation
		frappe.set_user("Administrator")
		frappe.db.set_value("HD Time Entry", entry_name, "agent", "sys.mgr.tt@test.com")
		entry_doc = frappe.get_doc("HD Time Entry", entry_name)

		self._ensure_system_manager_user()
		frappe.set_user("sys.mgr.tt@test.com")
		try:
			# on_trash() MUST raise PermissionError even when entry.agent == user
			with self.assertRaises(frappe.PermissionError):
				entry_doc.on_trash()
		finally:
			frappe.set_user("Administrator")

	# --- P2: Administrator short-circuit in _check_delete_permission ---

	def test_check_delete_permission_administrator_always_allowed(self):
		"""
		Administrator must always pass _check_delete_permission regardless of
		the entry's agent field value — the explicit 'if user == "Administrator":
		return' short-circuit must fire before any role lookup.

		This test exercises _check_delete_permission directly so the assertion
		is unambiguous: no PermissionError must be raised for Administrator even
		when entry.agent is a different user.
		"""
		from helpdesk.helpdesk.doctype.hd_time_entry.hd_time_entry import (
			_check_delete_permission,
		)

		# Create an entry owned by agent.tt (not Administrator)
		frappe.set_user("agent.tt@test.com")
		result = add_entry(ticket=self.ticket_name, duration_minutes=10, billable=0)
		entry_doc = frappe.get_doc("HD Time Entry", result["name"])

		# Administrator calling _check_delete_permission must not raise
		frappe.set_user("Administrator")
		try:
			_check_delete_permission(entry_doc, "Administrator")
			# No exception = test passes
		except frappe.PermissionError:
			self.fail(
				"_check_delete_permission raised PermissionError for Administrator — "
				"the explicit Administrator short-circuit guard is broken."
			)

	def test_check_delete_permission_raises_valueerror_for_mismatched_user_roles(self):
		"""
		_check_delete_permission() must raise ValueError when user_roles is
		pre-fetched for a different user than frappe.session.user.

		This mirrors the identity-contract enforcement in is_agent() (utils.py)
		to prevent silent permission mismatches where the caller passes
		user="X" with roles fetched for the session user "Y".

		See QA report task-184 Finding #8.
		"""
		from helpdesk.helpdesk.doctype.hd_time_entry.hd_time_entry import (
			_check_delete_permission,
		)

		# Create an entry as agent.tt
		frappe.set_user("agent.tt@test.com")
		result = add_entry(ticket=self.ticket_name, duration_minutes=10, billable=0)
		entry_doc = frappe.get_doc("HD Time Entry", result["name"])

		# Switch to a different session user, then try to pass roles for yet
		# another user — this must raise ValueError.
		frappe.set_user("agent.tt@test.com")
		try:
			# user_roles fetched for the session user is valid — should not raise
			session_roles = set(frappe.get_roles(frappe.session.user))
			try:
				_check_delete_permission(entry_doc, frappe.session.user, user_roles=session_roles)
				# No exception expected for matching user + session user
			except ValueError:
				self.fail(
					"_check_delete_permission() raised ValueError when user == "
					"frappe.session.user — the identity contract must allow matching users."
				)

			# Now pass user_roles for a DIFFERENT user — must raise ValueError
			with self.assertRaises(ValueError) as ctx:
				_check_delete_permission(
					entry_doc,
					user="other.user@test.com",
					user_roles=session_roles,
				)
			self.assertIn("other.user@test.com", str(ctx.exception))
			self.assertIn(frappe.session.user, str(ctx.exception))
		finally:
			frappe.set_user("Administrator")

	def test_delete_entry_administrator_can_delete_any_entry(self):
		"""
		Administrator must be able to delete any agent's entry via delete_entry()
		— end-to-end companion to test_check_delete_permission_administrator_always_allowed.
		"""
		# Create entry as agent.tt, then delete as Administrator
		frappe.set_user("agent.tt@test.com")
		result = add_entry(ticket=self.ticket_name, duration_minutes=10, billable=0)
		entry_name = result["name"]

		frappe.set_user("Administrator")
		del_result = delete_entry(name=entry_name)
		self.assertTrue(del_result.get("success"))
		self.assertFalse(frappe.db.exists("HD Time Entry", entry_name))

	# --- P2: Dual-role System Manager + Agent user ---

	def _ensure_sm_agent_user(self, email="sm.agent.tt@test.com"):
		"""Create a user with both System Manager and Agent roles plus an HD Agent record.

		Delegates to shared ensure_sm_agent_user() in test_utils so the helper is
		DRY and reusable across test modules (QA report task-155 Findings #1 and #7).
		Includes HD Agent record creation and role pollution guard.
		"""
		ensure_sm_agent_user(email)

	def test_system_manager_with_agent_role_can_delete_own_entry(self):
		"""
		A user who holds BOTH System Manager AND Agent roles must be allowed to
		delete their own time entry via delete_entry().

		The is_agent() pre-gate passes because Agent is in AGENT_ROLES.
		The ownership check passes because entry.agent == user.

		Previously, hardcoding the role set in delete_entry() without the Agent
		role would have incorrectly blocked this user.
		"""
		sm_agent_email = "sm.agent.tt@test.com"
		self._ensure_sm_agent_user(sm_agent_email)

		# Create entry as agent.tt (SM+Agent user may not have ticket write perms)
		frappe.set_user("agent.tt@test.com")
		result = add_entry(ticket=self.ticket_name, duration_minutes=5, billable=0)
		entry_name = result["name"]

		# Update agent field to sm_agent_email so ownership check passes
		frappe.set_user("Administrator")
		frappe.db.set_value("HD Time Entry", entry_name, "agent", sm_agent_email)

		# SM+Agent user deletes their own entry via delete_entry()
		frappe.set_user(sm_agent_email)
		try:
			del_result = delete_entry(name=entry_name)
			self.assertTrue(del_result.get("success"))
			self.assertFalse(frappe.db.exists("HD Time Entry", entry_name))
		finally:
			frappe.set_user("Administrator")

	def test_on_trash_system_manager_with_agent_role_can_delete_own_entry(self):
		"""
		The on_trash hook must allow a dual-role SM+Agent user to delete their
		own entry — the is_agent() pre-gate passes because Agent is in AGENT_ROLES,
		and the ownership check passes because entry.agent == user.
		"""
		sm_agent_email = "sm.agent.tt@test.com"
		self._ensure_sm_agent_user(sm_agent_email)

		# Create entry as agent.tt then reassign to sm_agent
		frappe.set_user("agent.tt@test.com")
		result = add_entry(ticket=self.ticket_name, duration_minutes=5, billable=0)
		entry_name = result["name"]

		frappe.set_user("Administrator")
		frappe.db.set_value("HD Time Entry", entry_name, "agent", sm_agent_email)
		entry_doc = frappe.get_doc("HD Time Entry", entry_name)

		# on_trash() must NOT raise PermissionError
		frappe.set_user(sm_agent_email)
		try:
			entry_doc.on_trash()
		except frappe.PermissionError:
			self.fail(
				"on_trash() raised PermissionError for a user with both SM and Agent "
				"roles — the is_agent() pre-gate incorrectly blocked a valid agent."
			)
		finally:
			frappe.set_user("Administrator")
