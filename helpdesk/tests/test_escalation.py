# Copyright (c) 2026, Frappe Technologies Pvt. Ltd. and contributors
# For license information, please see license.txt
"""
Tests for County-4: Escalation chain with restrictions + SLA auto-escalation.

Covers:
- Manual escalation (happy path)
- Escalation blocked when allow_escalation_to_next = False (terminal tier)
- Escalation blocked when no parent_team
- Escalation blocked when no support_level
- Escalation increments escalation_count
- Escalation appends to escalation_path audit trail
- Internal note added on escalation
- De-escalation (happy path)
- De-escalation blocked when no history
- get_escalation_path returns audit trail
- Auto-escalation candidate detection
- Engineering (L3) terminal tier blocks escalation
"""

import json

import frappe
from frappe.tests.utils import FrappeTestCase

from helpdesk.test_utils import create_agent, make_ticket


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------


def _make_support_level(level_name, level_order, allow_escalation=True, auto_escalate=False, auto_minutes=60):
	"""Create or return an HD Support Level record."""
	if frappe.db.exists("HD Support Level", level_name):
		return frappe.get_doc("HD Support Level", level_name)
	doc = frappe.get_doc({
		"doctype": "HD Support Level",
		"level_name": level_name,
		"level_order": level_order,
		"display_name": level_name,
		"allow_escalation_to_next": 1 if allow_escalation else 0,
		"auto_escalate_on_breach": 1 if auto_escalate else 0,
		"auto_escalate_minutes": auto_minutes,
	})
	doc.insert(ignore_permissions=True)
	return doc


def _make_team(team_name, support_level=None, parent_team=None):
	"""Create or return an HD Team record."""
	if frappe.db.exists("HD Team", team_name):
		return frappe.get_doc("HD Team", team_name)
	doc = frappe.get_doc({
		"doctype": "HD Team",
		"team_name": team_name,
		"support_level": support_level,
		"parent_team": parent_team,
	})
	doc.insert(ignore_permissions=True)
	return doc


class TestEscalationChain(FrappeTestCase):
	"""Unit tests for helpdesk.api.escalation module."""

	def setUp(self):
		frappe.set_user("Administrator")
		self._cleanup = []  # track names for tearDown

		# Build 4-tier support level hierarchy
		self.l0 = _make_support_level("Test-L0", 900, allow_escalation=True, auto_escalate=True, auto_minutes=30)
		self.l1 = _make_support_level("Test-L1", 901, allow_escalation=True, auto_escalate=True, auto_minutes=60)
		self.l2 = _make_support_level("Test-L2", 902, allow_escalation=True, auto_escalate=False)
		self.l3 = _make_support_level("Test-L3-Terminal", 903, allow_escalation=False, auto_escalate=False)
		self._cleanup += [
			("HD Support Level", "Test-L0"),
			("HD Support Level", "Test-L1"),
			("HD Support Level", "Test-L2"),
			("HD Support Level", "Test-L3-Terminal"),
		]

		# Build team hierarchy: l0_team → l1_team → l2_team
		self.l2_team = _make_team("EscTest-L2-Team", support_level=self.l2.name)
		self.l1_team = _make_team("EscTest-L1-Team", support_level=self.l1.name, parent_team=self.l2_team.name)
		self.l0_team = _make_team("EscTest-L0-Team", support_level=self.l0.name, parent_team=self.l1_team.name)
		self._cleanup += [
			("HD Team", "EscTest-L0-Team"),
			("HD Team", "EscTest-L1-Team"),
			("HD Team", "EscTest-L2-Team"),
		]

		# Create an agent
		self.agent = create_agent("escalation.test.agent@test.com")
		self._cleanup.append(("HD Agent", {"user": "escalation.test.agent@test.com"}))

		frappe.set_user("escalation.test.agent@test.com")

	def tearDown(self):
		frappe.set_user("Administrator")
		for doctype, name_or_filter in self._cleanup:
			try:
				if isinstance(name_or_filter, dict):
					rec = frappe.db.exists(doctype, name_or_filter)
					if rec:
						frappe.delete_doc(doctype, rec, force=True, ignore_permissions=True)
				else:
					if frappe.db.exists(doctype, name_or_filter):
						frappe.delete_doc(doctype, name_or_filter, force=True, ignore_permissions=True)
			except Exception:
				pass
		frappe.db.commit()  # nosemgrep

	def _make_ticket(self, support_level=None, agent_group=None, **kwargs):
		"""Helper: create a ticket and register for cleanup."""
		ticket = make_ticket(
			subject="Escalation Test Ticket",
			support_level=support_level or self.l0.name,
			agent_group=agent_group or self.l0_team.name,
			**kwargs,
		)
		self._cleanup.append(("HD Ticket", str(ticket.name)))
		# Also cleanup HD Ticket Comment records created during escalation
		return ticket

	# -----------------------------------------------------------------------
	# Escalation — happy path
	# -----------------------------------------------------------------------

	def test_escalate_ticket_success(self):
		"""Manual escalation moves ticket from L0 team to L1 team, updates support_level."""
		from helpdesk.api.escalation import escalate_ticket

		ticket = self._make_ticket()
		result = escalate_ticket(str(ticket.name), reason="Customer unresolved for 2 hours")

		self.assertTrue(result["success"])
		self.assertEqual(result["new_support_level"], self.l1.name)
		self.assertEqual(result["new_team"], self.l1_team.name)

		# Verify ticket was updated in DB
		updated = frappe.get_doc("HD Ticket", ticket.name)
		self.assertEqual(updated.support_level, self.l1.name)
		self.assertEqual(updated.agent_group, self.l1_team.name)
		self.assertEqual(updated.escalation_count, 1)

	def test_escalate_increments_count(self):
		"""Each escalation increments escalation_count by 1."""
		from helpdesk.api.escalation import escalate_ticket

		ticket = self._make_ticket()
		escalate_ticket(str(ticket.name), reason="First escalation")

		# Ticket is now at L1; escalate again to L2
		escalate_ticket(str(ticket.name), reason="Second escalation")

		updated = frappe.get_doc("HD Ticket", ticket.name)
		self.assertEqual(updated.escalation_count, 2)
		self.assertEqual(updated.support_level, self.l2.name)

	def test_escalate_appends_audit_trail(self):
		"""Escalation appends a well-formed entry to escalation_path."""
		from helpdesk.api.escalation import escalate_ticket, get_escalation_path

		ticket = self._make_ticket()
		escalate_ticket(str(ticket.name), reason="Audit trail test")

		path = get_escalation_path(str(ticket.name))
		self.assertEqual(len(path), 1)

		entry = path[0]
		self.assertEqual(entry["from_level"], self.l0.name)
		self.assertEqual(entry["to_level"], self.l1.name)
		self.assertEqual(entry["direction"], "escalation")
		self.assertFalse(entry["auto"])
		self.assertIn("reason", entry)
		self.assertIn("at", entry)

	def test_escalate_adds_internal_note(self):
		"""Escalation creates an internal HD Ticket Comment."""
		from helpdesk.api.escalation import escalate_ticket

		ticket = self._make_ticket()
		escalate_ticket(str(ticket.name), reason="Adding note test")

		notes = frappe.get_all(
			"HD Ticket Comment",
			filters={"reference_ticket": ticket.name, "is_internal": 1},
			pluck="content",
		)
		self.assertTrue(
			any("Escalated from" in n and "Adding note test" in n for n in notes),
			f"Expected internal note with escalation text. Found: {notes}",
		)

	# -----------------------------------------------------------------------
	# Escalation — blocked cases
	# -----------------------------------------------------------------------

	def test_escalate_blocked_terminal_tier(self):
		"""Escalation from a terminal tier (allow_escalation_to_next=False) is blocked."""
		from helpdesk.api.escalation import escalate_ticket

		# L3 terminal team (no parent needed because escalation will be blocked before team check)
		l3_team = _make_team("EscTest-L3-Team", support_level=self.l3.name)
		self._cleanup.append(("HD Team", "EscTest-L3-Team"))

		ticket = self._make_ticket(
			support_level=self.l3.name,
			agent_group=l3_team.name,
		)
		with self.assertRaises(frappe.ValidationError) as ctx:
			escalate_ticket(str(ticket.name), reason="Try escalate from terminal")
		self.assertIn("does not allow escalation", str(ctx.exception))

	def test_escalate_blocked_no_parent_team(self):
		"""Escalation blocked when assigned team has no parent_team."""
		from helpdesk.api.escalation import escalate_ticket

		orphan_team = _make_team("EscTest-Orphan-Team", support_level=self.l0.name, parent_team=None)
		self._cleanup.append(("HD Team", "EscTest-Orphan-Team"))

		# Force no parent_team
		frappe.db.set_value("HD Team", orphan_team.name, "parent_team", None)

		ticket = self._make_ticket(
			support_level=self.l0.name,
			agent_group=orphan_team.name,
		)
		with self.assertRaises(frappe.ValidationError) as ctx:
			escalate_ticket(str(ticket.name), reason="No parent team")
		self.assertIn("no parent team", str(ctx.exception))

	def test_escalate_blocked_no_support_level(self):
		"""Escalation blocked when ticket has no support_level assigned."""
		from helpdesk.api.escalation import escalate_ticket

		ticket = make_ticket(subject="No Support Level Ticket")
		self._cleanup.append(("HD Ticket", str(ticket.name)))
		# Clear support_level
		frappe.db.set_value("HD Ticket", ticket.name, "support_level", None)

		with self.assertRaises(frappe.ValidationError) as ctx:
			escalate_ticket(str(ticket.name), reason="No level")
		self.assertIn("no support level", str(ctx.exception).lower())

	def test_escalate_blocked_no_reason(self):
		"""Escalation requires a non-empty reason."""
		from helpdesk.api.escalation import escalate_ticket

		ticket = self._make_ticket()
		with self.assertRaises(frappe.ValidationError) as ctx:
			escalate_ticket(str(ticket.name), reason="")
		self.assertIn("reason is required", str(ctx.exception))

	def test_escalate_blocked_non_agent(self):
		"""Non-agents cannot escalate tickets."""
		from helpdesk.api.escalation import escalate_ticket

		ticket = self._make_ticket()

		frappe.set_user("Administrator")  # Administrator has all roles but not Agent in test
		# Create a customer user
		if not frappe.db.exists("User", "customer.esc@test.com"):
			frappe.get_doc({
				"doctype": "User",
				"email": "customer.esc@test.com",
				"first_name": "Customer",
				"send_welcome_email": 0,
			}).insert(ignore_permissions=True)
		self._cleanup.append(("User", "customer.esc@test.com"))

		frappe.set_user("customer.esc@test.com")
		with self.assertRaises(frappe.PermissionError):
			escalate_ticket(str(ticket.name), reason="Unauthorized")
		frappe.set_user("escalation.test.agent@test.com")

	# -----------------------------------------------------------------------
	# De-escalation
	# -----------------------------------------------------------------------

	def test_de_escalate_success(self):
		"""De-escalation moves ticket back to previous support level."""
		from helpdesk.api.escalation import escalate_ticket, de_escalate_ticket

		ticket = self._make_ticket()
		# First escalate to L1
		escalate_ticket(str(ticket.name), reason="Escalate first")

		# Now de-escalate back to L0
		result = de_escalate_ticket(str(ticket.name), reason="Resolved at L1, returning to L0")
		self.assertTrue(result["success"])

		updated = frappe.get_doc("HD Ticket", ticket.name)
		self.assertEqual(updated.support_level, self.l0.name)

	def test_de_escalate_adds_audit_entry(self):
		"""De-escalation appends a de-escalation entry to escalation_path."""
		from helpdesk.api.escalation import escalate_ticket, de_escalate_ticket, get_escalation_path

		ticket = self._make_ticket()
		escalate_ticket(str(ticket.name), reason="Escalate")
		de_escalate_ticket(str(ticket.name), reason="De-escalate")

		path = get_escalation_path(str(ticket.name))
		self.assertEqual(len(path), 2)
		self.assertEqual(path[1]["direction"], "de-escalation")

	def test_de_escalate_blocked_no_history(self):
		"""De-escalation requires at least one prior escalation in the path."""
		from helpdesk.api.escalation import de_escalate_ticket

		ticket = self._make_ticket()
		with self.assertRaises(frappe.ValidationError) as ctx:
			de_escalate_ticket(str(ticket.name), reason="No history")
		self.assertIn("No escalation history", str(ctx.exception))

	def test_de_escalate_adds_internal_note(self):
		"""De-escalation creates an internal HD Ticket Comment."""
		from helpdesk.api.escalation import escalate_ticket, de_escalate_ticket

		ticket = self._make_ticket()
		escalate_ticket(str(ticket.name), reason="Escalate")
		de_escalate_ticket(str(ticket.name), reason="De-escalate reason here")

		notes = frappe.get_all(
			"HD Ticket Comment",
			filters={"reference_ticket": ticket.name, "is_internal": 1},
			pluck="content",
		)
		self.assertTrue(
			any("De-escalated" in n and "De-escalate reason here" in n for n in notes),
			f"Expected de-escalation note. Found: {notes}",
		)

	# -----------------------------------------------------------------------
	# get_escalation_path
	# -----------------------------------------------------------------------

	def test_get_escalation_path_empty_initially(self):
		"""A new ticket has an empty escalation path."""
		from helpdesk.api.escalation import get_escalation_path

		ticket = self._make_ticket()
		path = get_escalation_path(str(ticket.name))
		self.assertEqual(path, [])

	def test_get_escalation_path_non_agent_blocked(self):
		"""Non-agents cannot retrieve escalation path."""
		from helpdesk.api.escalation import get_escalation_path

		ticket = self._make_ticket()
		if not frappe.db.exists("User", "customer2.esc@test.com"):
			frappe.get_doc({
				"doctype": "User",
				"email": "customer2.esc@test.com",
				"first_name": "Customer2",
				"send_welcome_email": 0,
			}).insert(ignore_permissions=True)
		self._cleanup.append(("User", "customer2.esc@test.com"))

		frappe.set_user("customer2.esc@test.com")
		with self.assertRaises(frappe.PermissionError):
			get_escalation_path(str(ticket.name))
		frappe.set_user("escalation.test.agent@test.com")

	# -----------------------------------------------------------------------
	# Auto-escalation scheduler candidate detection
	# -----------------------------------------------------------------------

	def test_auto_escalation_candidate_detected(self):
		"""Tickets with old last_agent_response at an auto-escalate level are detected."""
		from helpdesk.helpdesk.doctype.hd_ticket.escalation_scheduler import (
			_find_auto_escalation_candidates,
		)
		from frappe.utils import add_to_date, now_datetime

		ticket = self._make_ticket(support_level=self.l0.name, agent_group=self.l0_team.name)

		# Simulate no agent response: set last_agent_response to 2 hours ago
		old_time = add_to_date(now_datetime(), hours=-2)
		frappe.db.set_value("HD Ticket", ticket.name, "last_agent_response", old_time)

		candidates = _find_auto_escalation_candidates()
		self.assertIn(str(ticket.name), [str(c) for c in candidates])

	def test_auto_escalation_skips_non_auto_level(self):
		"""Tickets at a level with auto_escalate_on_breach=False are NOT auto-escalated."""
		from helpdesk.helpdesk.doctype.hd_ticket.escalation_scheduler import (
			_find_auto_escalation_candidates,
		)
		from frappe.utils import add_to_date, now_datetime

		ticket = self._make_ticket(support_level=self.l2.name, agent_group=self.l2_team.name)
		old_time = add_to_date(now_datetime(), hours=-5)
		frappe.db.set_value("HD Ticket", ticket.name, "last_agent_response", old_time)

		candidates = _find_auto_escalation_candidates()
		self.assertNotIn(str(ticket.name), [str(c) for c in candidates])

	def test_auto_escalation_skips_terminal_level(self):
		"""Tickets at the highest level (terminal) are not auto-escalated."""
		from helpdesk.helpdesk.doctype.hd_ticket.escalation_scheduler import (
			_find_auto_escalation_candidates,
		)
		from frappe.utils import add_to_date, now_datetime

		# L3 terminal level has auto_escalate_on_breach=False anyway, but also has max order
		ticket = self._make_ticket(support_level=self.l3.name, agent_group=self.l2_team.name)
		old_time = add_to_date(now_datetime(), hours=-5)
		frappe.db.set_value("HD Ticket", ticket.name, "last_agent_response", old_time)

		candidates = _find_auto_escalation_candidates()
		self.assertNotIn(str(ticket.name), [str(c) for c in candidates])

	def test_auto_escalation_skips_resolved_ticket(self):
		"""Resolved tickets are not auto-escalated."""
		from helpdesk.helpdesk.doctype.hd_ticket.escalation_scheduler import (
			_find_auto_escalation_candidates,
		)
		from frappe.utils import add_to_date, now_datetime

		ticket = self._make_ticket(support_level=self.l0.name, agent_group=self.l0_team.name)
		old_time = add_to_date(now_datetime(), hours=-2)
		frappe.db.set_value("HD Ticket", ticket.name, "last_agent_response", old_time)

		# Close the ticket
		frappe.db.set_value("HD Ticket", ticket.name, "status", "Resolved")

		candidates = _find_auto_escalation_candidates()
		self.assertNotIn(str(ticket.name), [str(c) for c in candidates])

	def test_auto_escalation_skips_recent_response(self):
		"""Tickets with recent agent response are not auto-escalated."""
		from helpdesk.helpdesk.doctype.hd_ticket.escalation_scheduler import (
			_find_auto_escalation_candidates,
		)
		from frappe.utils import add_to_date, now_datetime

		ticket = self._make_ticket(support_level=self.l0.name, agent_group=self.l0_team.name)
		# Set last_agent_response to just 5 minutes ago (< auto_escalate_minutes=30)
		recent_time = add_to_date(now_datetime(), minutes=-5)
		frappe.db.set_value("HD Ticket", ticket.name, "last_agent_response", recent_time)

		candidates = _find_auto_escalation_candidates()
		self.assertNotIn(str(ticket.name), [str(c) for c in candidates])
