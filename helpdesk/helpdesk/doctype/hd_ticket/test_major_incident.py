# Copyright (c) 2026, Frappe Technologies and Contributors
# See license.txt
# Story 1.8: Major Incident Flag and Workflow

import frappe
from frappe.tests.utils import FrappeTestCase

from helpdesk.api.incident import (
    flag_major_incident,
    get_major_incident_summary,
    propagate_update,
)
from helpdesk.test_utils import create_agent, make_ticket


class TestMajorIncidentFlagAndWorkflow(FrappeTestCase):
    """
    Story 1.8: Verify major incident flag, propagate update, and summary API.
    """

    def setUp(self):
        frappe.set_user("Administrator")
        frappe.db.set_single_value("HD Settings", "skip_email_workflow", 1)

        self.agent_email = "mi_agent@example.com"
        self.customer_email = "mi_customer@example.com"
        create_agent(self.agent_email)

        self.ticket = make_ticket(
            subject="Major Incident Test Ticket",
            raised_by=self.customer_email,
        )
        self.ticket_id = str(self.ticket.name)

    def tearDown(self):
        frappe.set_user("Administrator")
        frappe.db.set_single_value("HD Settings", "skip_email_workflow", 0)

        # Clean up comments created during tests
        for comment in frappe.get_all(
            "HD Ticket Comment",
            filters={"reference_ticket": self.ticket_id},
            pluck="name",
        ):
            frappe.delete_doc("HD Ticket Comment", comment, force=True)

        frappe.db.rollback()

    # ------------------------------------------------------------------
    # AC-1 / AC-2: Flag and unflag
    # ------------------------------------------------------------------

    def test_agent_can_flag_major_incident(self):
        frappe.set_user(self.agent_email)
        result = flag_major_incident(self.ticket_id)

        self.assertTrue(result["success"])
        self.assertEqual(result["is_major_incident"], 1)

        doc = frappe.get_doc("HD Ticket", self.ticket_id)
        self.assertEqual(doc.is_major_incident, 1)
        self.assertIsNotNone(doc.major_incident_flagged_at)

    def test_agent_can_unflag_major_incident(self):
        frappe.set_user(self.agent_email)
        flag_major_incident(self.ticket_id)  # flag first

        result = flag_major_incident(self.ticket_id)  # then unflag
        self.assertTrue(result["success"])
        self.assertEqual(result["is_major_incident"], 0)

        doc = frappe.get_doc("HD Ticket", self.ticket_id)
        self.assertEqual(doc.is_major_incident, 0)
        self.assertIsNone(doc.major_incident_flagged_at)

    def test_non_agent_cannot_flag_major_incident(self):
        frappe.set_user(self.customer_email)
        with self.assertRaises(frappe.PermissionError):
            flag_major_incident(self.ticket_id)

    # ------------------------------------------------------------------
    # AC-3: flagged_at is set when flagged
    # ------------------------------------------------------------------

    def test_flagged_at_is_set_on_flag(self):
        frappe.set_user(self.agent_email)
        flag_major_incident(self.ticket_id)

        flagged_at = frappe.db.get_value(
            "HD Ticket", self.ticket_id, "major_incident_flagged_at"
        )
        self.assertIsNotNone(flagged_at)

    def test_flagged_at_cleared_on_unflag(self):
        frappe.set_user(self.agent_email)
        flag_major_incident(self.ticket_id)
        flag_major_incident(self.ticket_id)  # unflag

        flagged_at = frappe.db.get_value(
            "HD Ticket", self.ticket_id, "major_incident_flagged_at"
        )
        self.assertIsNone(flagged_at)

    # ------------------------------------------------------------------
    # AC-4: propagate_update posts comments
    # ------------------------------------------------------------------

    def test_propagate_update_posts_comment_on_major_incident_ticket(self):
        frappe.set_user(self.agent_email)
        flag_major_incident(self.ticket_id)

        result = propagate_update(self.ticket_id, "Update: investigating root cause")
        self.assertTrue(result["success"])
        self.assertGreaterEqual(result["count"], 1)

        comments = frappe.get_all(
            "HD Ticket Comment",
            filters={"reference_ticket": self.ticket_id},
            pluck="content",
        )
        self.assertTrue(
            any("Major Incident Update" in c for c in comments),
            "Expected a Major Incident Update comment on the ticket",
        )

    def test_propagate_update_fails_on_non_major_incident(self):
        frappe.set_user(self.agent_email)
        with self.assertRaises(frappe.ValidationError):
            propagate_update(self.ticket_id, "Should fail")

    def test_propagate_update_non_agent_forbidden(self):
        frappe.set_user(self.agent_email)
        flag_major_incident(self.ticket_id)
        frappe.set_user(self.customer_email)
        with self.assertRaises(frappe.PermissionError):
            propagate_update(self.ticket_id, "Not allowed")

    # ------------------------------------------------------------------
    # AC-5: get_major_incident_summary
    # ------------------------------------------------------------------

    def test_get_major_incident_summary_returns_flagged_tickets(self):
        frappe.set_user(self.agent_email)
        flag_major_incident(self.ticket_id)

        summary = get_major_incident_summary()
        names = [str(inc["name"]) for inc in summary]
        self.assertIn(self.ticket_id, names)

    def test_get_major_incident_summary_excludes_unflagged(self):
        frappe.set_user(self.agent_email)
        # Ensure this ticket is NOT flagged
        doc = frappe.get_doc("HD Ticket", self.ticket_id)
        doc.is_major_incident = 0
        doc.flags.ignore_permissions = True
        doc.save()

        summary = get_major_incident_summary()
        names = [str(inc["name"]) for inc in summary]
        self.assertNotIn(self.ticket_id, names)

    def test_get_major_incident_summary_includes_elapsed_minutes(self):
        frappe.set_user(self.agent_email)
        flag_major_incident(self.ticket_id)

        summary = get_major_incident_summary()
        incident = next(
            (inc for inc in summary if str(inc["name"]) == self.ticket_id), None
        )
        self.assertIsNotNone(incident)
        self.assertIn("elapsed_minutes", incident)
        self.assertGreaterEqual(incident["elapsed_minutes"], 0)

    def test_get_major_incident_summary_non_agent_forbidden(self):
        frappe.set_user(self.customer_email)
        with self.assertRaises(frappe.PermissionError):
            get_major_incident_summary()
