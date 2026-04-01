# Copyright (c) 2026, Frappe Technologies and Contributors
# See license.txt
# Story County-2: HD Facility Mapping DocType + Auto-Routing Engine tests

import frappe
from frappe.tests.utils import FrappeTestCase

from helpdesk.test_utils import create_agent, make_ticket


FACILITY_USER = "facility_user_test@example.com"
AGENT_EMAIL = "facility_agent_test@example.com"
TEAM_L0 = "Test L0 Sub-County Team"
TEAM_L1 = "Test L1 County Team"
TEAM_NATIONAL = "Test National Team"
SUPPORT_LEVEL_L0 = "L0 - Sub-County"
SUPPORT_LEVEL_L2 = "L2 - National"
FACILITY_NAME = "Test Health Centre Nairobi"
FACILITY_CODE = "99999"
SUB_COUNTY = "Westlands"
COUNTY = "Nairobi"


def _ensure_support_level(name, level_order):
	if not frappe.db.exists("HD Support Level", name):
		frappe.get_doc(
			{
				"doctype": "HD Support Level",
				"level_name": name,
				"level_order": level_order,
				"display_name": name,
				"allow_escalation_to_next": 1,
				"auto_escalate_on_breach": 0,
			}
		).insert(ignore_permissions=True)


def _ensure_team(team_name, support_level=None, parent_team=None):
	if not frappe.db.exists("HD Team", team_name):
		doc = frappe.get_doc(
			{
				"doctype": "HD Team",
				"team_name": team_name,
				"support_level": support_level,
				"parent_team": parent_team,
			}
		)
		doc.insert(ignore_permissions=True)
	return team_name


def _ensure_facility_user(email, facility=None):
	if not frappe.db.exists("User", email):
		frappe.get_doc(
			{
				"doctype": "User",
				"email": email,
				"first_name": "FacilityUser",
				"send_welcome_email": 0,
			}
		).insert(ignore_permissions=True)
	if facility is not None:
		frappe.db.set_value("User", email, "facility", facility)


class TestHDFacilityMapping(FrappeTestCase):
	"""Tests for HD Facility Mapping DocType and auto-routing engine (Story County-2)."""

	def setUp(self):
		frappe.set_user("Administrator")

		# Ensure support levels exist
		_ensure_support_level(SUPPORT_LEVEL_L0, 0)
		_ensure_support_level("L1 - County", 1)
		_ensure_support_level(SUPPORT_LEVEL_L2, 2)

		# Ensure teams exist
		_ensure_team(TEAM_L1, "L1 - County")
		_ensure_team(TEAM_L0, SUPPORT_LEVEL_L0, parent_team=TEAM_L1)
		_ensure_team(TEAM_NATIONAL, SUPPORT_LEVEL_L2)

		# Ensure facility user
		_ensure_facility_user(FACILITY_USER)

		# Ensure agent
		create_agent(AGENT_EMAIL)

	def tearDown(self):
		frappe.set_user("Administrator")
		frappe.db.delete("HD Ticket", {"raised_by": FACILITY_USER})
		frappe.db.delete("HD Facility Mapping", {"facility_name": FACILITY_NAME})
		frappe.db.commit()  # nosemgrep

	# -------------------------------------------------------------------------
	# DocType CRUD tests
	# -------------------------------------------------------------------------

	def test_create_facility_mapping(self):
		"""Can create an HD Facility Mapping record with required fields."""
		doc = frappe.get_doc(
			{
				"doctype": "HD Facility Mapping",
				"facility_name": FACILITY_NAME,
				"facility_code": FACILITY_CODE,
				"sub_county": SUB_COUNTY,
				"county": COUNTY,
				"l0_team": TEAM_L0,
			}
		).insert(ignore_permissions=True)

		self.assertEqual(doc.facility_name, FACILITY_NAME)
		self.assertEqual(doc.sub_county, SUB_COUNTY)
		self.assertEqual(doc.county, COUNTY)
		self.assertEqual(doc.l0_team, TEAM_L0)

	def test_auto_resolve_l1_team_from_l0_parent(self):
		"""l1_team is auto-resolved from l0_team.parent_team when not explicitly set."""
		doc = frappe.get_doc(
			{
				"doctype": "HD Facility Mapping",
				"facility_name": FACILITY_NAME,
				"sub_county": SUB_COUNTY,
				"county": COUNTY,
				"l0_team": TEAM_L0,
				# l1_team intentionally NOT set
			}
		).insert(ignore_permissions=True)

		# Should be auto-resolved from TEAM_L0.parent_team = TEAM_L1
		self.assertEqual(doc.l1_team, TEAM_L1)

	def test_explicit_l1_team_not_overridden(self):
		"""Explicitly set l1_team is not overridden during auto-resolution."""
		doc = frappe.get_doc(
			{
				"doctype": "HD Facility Mapping",
				"facility_name": FACILITY_NAME,
				"sub_county": SUB_COUNTY,
				"county": COUNTY,
				"l0_team": TEAM_L0,
				"l1_team": TEAM_L1,
			}
		).insert(ignore_permissions=True)

		self.assertEqual(doc.l1_team, TEAM_L1)

	def test_facility_name_is_unique(self):
		"""Creating a duplicate facility_name raises an error."""
		frappe.get_doc(
			{
				"doctype": "HD Facility Mapping",
				"facility_name": FACILITY_NAME,
				"sub_county": SUB_COUNTY,
				"county": COUNTY,
				"l0_team": TEAM_L0,
			}
		).insert(ignore_permissions=True)

		with self.assertRaises(frappe.exceptions.DuplicateEntryError):
			frappe.get_doc(
				{
					"doctype": "HD Facility Mapping",
					"facility_name": FACILITY_NAME,
					"sub_county": "Other Sub-County",
					"county": COUNTY,
					"l0_team": TEAM_L0,
				}
			).insert(ignore_permissions=True)

	# -------------------------------------------------------------------------
	# Auto-routing tests
	# -------------------------------------------------------------------------

	def test_ticket_auto_routed_to_l0_team(self):
		"""Ticket created by a facility user is auto-assigned to L0 team."""
		# Set up facility mapping
		frappe.get_doc(
			{
				"doctype": "HD Facility Mapping",
				"facility_name": FACILITY_NAME,
				"sub_county": SUB_COUNTY,
				"county": COUNTY,
				"l0_team": TEAM_L0,
			}
		).insert(ignore_permissions=True)

		# Set facility on user
		frappe.db.set_value("User", FACILITY_USER, "facility", FACILITY_NAME)

		ticket = make_ticket(
			subject="Test Auto-Routing",
			raised_by=FACILITY_USER,
		)

		self.assertEqual(ticket.agent_group, TEAM_L0)

	def test_ticket_county_and_sub_county_auto_populated(self):
		"""ticket.county and ticket.sub_county are auto-populated from facility mapping."""
		frappe.get_doc(
			{
				"doctype": "HD Facility Mapping",
				"facility_name": FACILITY_NAME,
				"sub_county": SUB_COUNTY,
				"county": COUNTY,
				"l0_team": TEAM_L0,
			}
		).insert(ignore_permissions=True)

		frappe.db.set_value("User", FACILITY_USER, "facility", FACILITY_NAME)

		ticket = make_ticket(
			subject="Test County Population",
			raised_by=FACILITY_USER,
		)

		self.assertEqual(ticket.county, COUNTY)
		self.assertEqual(ticket.sub_county, SUB_COUNTY)

	def test_ticket_facility_stamped(self):
		"""ticket.facility is stamped from the user's facility field."""
		frappe.get_doc(
			{
				"doctype": "HD Facility Mapping",
				"facility_name": FACILITY_NAME,
				"sub_county": SUB_COUNTY,
				"county": COUNTY,
				"l0_team": TEAM_L0,
			}
		).insert(ignore_permissions=True)

		frappe.db.set_value("User", FACILITY_USER, "facility", FACILITY_NAME)

		ticket = make_ticket(
			subject="Test Facility Stamp",
			raised_by=FACILITY_USER,
		)

		self.assertEqual(ticket.facility, FACILITY_NAME)

	def test_ticket_support_level_set_to_l0(self):
		"""ticket.support_level is set to the L0 team's support level."""
		frappe.get_doc(
			{
				"doctype": "HD Facility Mapping",
				"facility_name": FACILITY_NAME,
				"sub_county": SUB_COUNTY,
				"county": COUNTY,
				"l0_team": TEAM_L0,
			}
		).insert(ignore_permissions=True)

		frappe.db.set_value("User", FACILITY_USER, "facility", FACILITY_NAME)

		ticket = make_ticket(
			subject="Test Support Level",
			raised_by=FACILITY_USER,
		)

		self.assertEqual(ticket.support_level, SUPPORT_LEVEL_L0)

	def test_no_mapping_falls_back_to_national_team(self):
		"""Ticket raised by a user with a facility but no mapping falls back to national team."""
		# Ensure no mapping exists for this facility
		unknown_facility = "Unknown Rural Clinic XYZ"
		frappe.db.set_value("User", FACILITY_USER, "facility", unknown_facility)

		# Ensure no mapping
		frappe.db.delete("HD Facility Mapping", {"facility_name": unknown_facility})

		ticket = make_ticket(
			subject="Test Fallback Routing",
			raised_by=FACILITY_USER,
		)

		# Should be assigned to national team (L2 or higher)
		self.assertEqual(ticket.agent_group, TEAM_NATIONAL)

	def test_no_facility_user_unaffected(self):
		"""Ticket raised by a user with no facility set is unaffected by routing."""
		# Clear facility
		frappe.db.set_value("User", FACILITY_USER, "facility", None)

		ticket = make_ticket(
			subject="Test No Facility",
			raised_by=FACILITY_USER,
		)

		# agent_group should remain unset (no routing happened)
		self.assertFalse(ticket.agent_group)

	def test_explicit_team_not_overridden(self):
		"""Explicitly set agent_group is not overridden by auto-routing."""
		frappe.get_doc(
			{
				"doctype": "HD Facility Mapping",
				"facility_name": FACILITY_NAME,
				"sub_county": SUB_COUNTY,
				"county": COUNTY,
				"l0_team": TEAM_L0,
			}
		).insert(ignore_permissions=True)

		frappe.db.set_value("User", FACILITY_USER, "facility", FACILITY_NAME)

		# Explicitly set agent_group to something else
		ticket = make_ticket(
			subject="Test Explicit Team",
			raised_by=FACILITY_USER,
			agent_group=TEAM_L1,
		)

		# Should NOT be overridden by auto-routing
		self.assertEqual(ticket.agent_group, TEAM_L1)
