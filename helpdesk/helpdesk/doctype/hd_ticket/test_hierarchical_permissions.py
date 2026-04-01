# Copyright (c) 2026, Frappe Technologies and Contributors
# Tests for County-3: Hierarchical visibility and permission scoping

import frappe
from frappe.tests import IntegrationTestCase

from helpdesk.test_utils import create_agent, make_ticket
from helpdesk.helpdesk.doctype.hd_ticket.team_hierarchy import (
    get_user_teams,
    get_descendant_teams,
    is_national_level,
    get_scoped_teams_for_agent,
    get_team_level_order,
)
from helpdesk.helpdesk.doctype.hd_ticket.hd_ticket import permission_query


# ---------------------------------------------------------------------------
# Fixtures helpers
# ---------------------------------------------------------------------------

def _make_support_level(level_name, level_order):
    if frappe.db.exists("HD Support Level", level_name):
        return frappe.get_doc("HD Support Level", level_name)
    doc = frappe.get_doc(
        {
            "doctype": "HD Support Level",
            "level_name": level_name,
            "level_order": level_order,
            "display_name": level_name,
        }
    )
    doc.insert(ignore_permissions=True)
    return doc


def _make_team(team_name, support_level=None, parent_team=None):
    """Create an HD Team without triggering Assignment Rule creation."""
    if frappe.db.exists("HD Team", team_name):
        return frappe.get_doc("HD Team", team_name)
    doc = frappe.get_doc(
        {
            "doctype": "HD Team",
            "team_name": team_name,
            "support_level": support_level,
            "parent_team": parent_team,
        }
    )
    doc.insert(ignore_permissions=True)
    return doc


def _add_team_member(team_name, user_email):
    team = frappe.get_doc("HD Team", team_name)
    already = any(m.user == user_email for m in team.users)
    if not already:
        team.append("users", {"user": user_email})
        team.save(ignore_permissions=True)


# ---------------------------------------------------------------------------
# Test class
# ---------------------------------------------------------------------------


class TestHierarchicalPermissions(IntegrationTestCase):
    """
    Tests for the County support-tier visibility model.

    Tier hierarchy:
        L0  (order=0) Sub-County  — sees own team only
        L1  (order=1) County      — sees own + all L0 child teams
        L2  (order=2) National    — sees everything
        L3  (order=3) Engineering — sees only L3 team tickets
    """

    def setUp(self):
        frappe.set_user("Administrator")

        # Support levels
        self.sl_l0 = _make_support_level("L0 - Sub-County", 0)
        self.sl_l1 = _make_support_level("L1 - County", 1)
        self.sl_l2 = _make_support_level("L2 - National", 2)
        self.sl_l3 = _make_support_level("L3 - Engineering", 3)

        # Teams: county → 2 sub-county teams
        self.county_team = _make_team("County-Nairobi", support_level="L1 - County")
        self.subcounty_westlands = _make_team(
            "SubCounty-Westlands",
            support_level="L0 - Sub-County",
            parent_team="County-Nairobi",
        )
        self.subcounty_langata = _make_team(
            "SubCounty-Langata",
            support_level="L0 - Sub-County",
            parent_team="County-Nairobi",
        )
        self.national_team = _make_team("National-Team", support_level="L2 - National")
        self.eng_team = _make_team("Engineering-Team", support_level="L3 - Engineering")

        # Agents
        self.l0_agent = create_agent("l0agent@county.test")
        self.l1_agent = create_agent("l1agent@county.test")
        self.l2_agent = create_agent("l2agent@county.test")
        self.l3_agent = create_agent("l3agent@county.test")

        _add_team_member("SubCounty-Westlands", "l0agent@county.test")
        _add_team_member("County-Nairobi", "l1agent@county.test")
        _add_team_member("National-Team", "l2agent@county.test")
        _add_team_member("Engineering-Team", "l3agent@county.test")

        # Enable team restrictions so permission_query applies filters
        frappe.db.set_single_value("HD Settings", "restrict_tickets_by_agent_group", 1)
        frappe.db.set_single_value(
            "HD Settings", "do_not_restrict_tickets_without_an_agent_group", 0
        )

    def tearDown(self):
        frappe.set_user("Administrator")
        frappe.db.set_single_value("HD Settings", "restrict_tickets_by_agent_group", 0)

        # Use direct DB delete to avoid Comment/activity-log deadlocks during teardown
        for team in [
            "SubCounty-Westlands",
            "SubCounty-Langata",
            "County-Nairobi",
            "National-Team",
            "Engineering-Team",
        ]:
            frappe.db.delete("HD Team Member", {"parent": team})
            frappe.db.delete("HD Team", {"name": team})

        for level in ["L0 - Sub-County", "L1 - County", "L2 - National", "L3 - Engineering"]:
            frappe.db.delete("HD Support Level", {"name": level})

        frappe.db.commit()

    # ------------------------------------------------------------------
    # Helper: unit tests for individual helpers
    # ------------------------------------------------------------------

    def test_get_user_teams_returns_members_teams(self):
        teams = get_user_teams("l0agent@county.test")
        self.assertIn("SubCounty-Westlands", teams)
        self.assertNotIn("County-Nairobi", teams)

    def test_get_team_level_order(self):
        self.assertEqual(get_team_level_order("County-Nairobi"), 1)
        self.assertEqual(get_team_level_order("SubCounty-Westlands"), 0)
        self.assertEqual(get_team_level_order("National-Team"), 2)
        self.assertEqual(get_team_level_order("Engineering-Team"), 3)

    def test_get_descendant_teams_finds_children(self):
        descendants = get_descendant_teams("County-Nairobi")
        self.assertIn("SubCounty-Westlands", descendants)
        self.assertIn("SubCounty-Langata", descendants)
        # National team is not under County-Nairobi
        self.assertNotIn("National-Team", descendants)

    def test_is_national_level_true_for_l2(self):
        self.assertTrue(is_national_level(["National-Team"]))

    def test_is_national_level_false_for_l3(self):
        # L3 Engineering is NOT treated as national (level_order=3, only level_order==2 is national)
        self.assertFalse(is_national_level(["Engineering-Team"]))

    def test_is_national_level_false_for_l0(self):
        self.assertFalse(is_national_level(["SubCounty-Westlands"]))

    # ------------------------------------------------------------------
    # get_scoped_teams_for_agent
    # ------------------------------------------------------------------

    def test_scoped_teams_l0_returns_own_team_only(self):
        scoped = get_scoped_teams_for_agent("l0agent@county.test")
        self.assertIsNotNone(scoped)
        self.assertIn("SubCounty-Westlands", scoped)
        self.assertNotIn("County-Nairobi", scoped)
        self.assertNotIn("SubCounty-Langata", scoped)

    def test_scoped_teams_l1_includes_descendant_l0_teams(self):
        scoped = get_scoped_teams_for_agent("l1agent@county.test")
        self.assertIsNotNone(scoped)
        self.assertIn("County-Nairobi", scoped)
        self.assertIn("SubCounty-Westlands", scoped)
        self.assertIn("SubCounty-Langata", scoped)

    def test_scoped_teams_l2_returns_true_for_see_all(self):
        # L2 national returns True sentinel (see all tickets, no restriction)
        scoped = get_scoped_teams_for_agent("l2agent@county.test")
        self.assertIs(scoped, True)

    def test_scoped_teams_l3_returns_own_engineering_team_only(self):
        scoped = get_scoped_teams_for_agent("l3agent@county.test")
        self.assertIsNotNone(scoped)
        self.assertIn("Engineering-Team", scoped)
        self.assertNotIn("County-Nairobi", scoped)
        self.assertNotIn("SubCounty-Westlands", scoped)

    def test_scoped_teams_no_team_returns_empty_list(self):
        create_agent("noTeamAgent@county.test")
        scoped = get_scoped_teams_for_agent("noTeamAgent@county.test")
        # agent has no teams → empty list
        self.assertEqual(scoped, [])

    # ------------------------------------------------------------------
    # permission_query integration tests
    # ------------------------------------------------------------------

    def test_permission_query_l0_filters_by_subcounty_team(self):
        sql = permission_query("l0agent@county.test")
        self.assertIn("SubCounty-Westlands", sql)
        self.assertNotIn("County-Nairobi", sql)
        self.assertNotIn("SubCounty-Langata", sql)

    def test_permission_query_l1_includes_county_and_subcounty(self):
        sql = permission_query("l1agent@county.test")
        self.assertIn("County-Nairobi", sql)
        self.assertIn("SubCounty-Westlands", sql)
        self.assertIn("SubCounty-Langata", sql)

    def test_permission_query_l2_returns_none(self):
        # L2 national agent should see everything — permission_query returns None
        # (no WHERE clause → unrestricted access)
        result = permission_query("l2agent@county.test")
        self.assertIsNone(result)

    def test_permission_query_l3_filters_to_engineering_team(self):
        sql = permission_query("l3agent@county.test")
        self.assertIn("Engineering-Team", sql)
        self.assertNotIn("County-Nairobi", sql)
        self.assertNotIn("SubCounty-Westlands", sql)

    def test_permission_query_disabled_restrictions_returns_none(self):
        """When restrict_tickets_by_agent_group=0, all agents see all tickets."""
        frappe.db.set_single_value("HD Settings", "restrict_tickets_by_agent_group", 0)
        result = permission_query("l0agent@county.test")
        self.assertIsNone(result)
