# Copyright (c) 2026, Frappe Technologies Pvt. Ltd. and contributors
# For license information, please see license.txt

import frappe
from frappe.tests.utils import FrappeTestCase
from helpdesk.api.time_tracking import add_entry, stop_timer, get_summary, delete_entry
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
