# Copyright (c) 2026, Frappe Technologies Pvt. Ltd. and Contributors
# See license.txt

"""
Unit tests for Story 1.6: Related Ticket Linking

Covers:
- Bidirectional link creation for all three link types
- Correct inverse link type on remote ticket
- Auto-close and system comment for "Duplicate of"
- Self-link validation error
- Duplicate link validation error
- Unlink removes both directions
- Permission check (non-agent caller)
"""

import frappe
from frappe.tests.utils import FrappeTestCase

from helpdesk.api.incident import (
    DUPLICATE_STATUS,
    FALLBACK_CLOSE_STATUS,
    link_tickets,
    unlink_tickets,
)
from helpdesk.test_utils import create_agent, make_ticket


class TestRelatedTicketLinking(FrappeTestCase):
    """Unit tests for bidirectional related ticket linking (Story 1.6)."""

    def setUp(self):
        frappe.set_user("Administrator")

        # Create test agent user
        self.agent_email = "test.link.agent@example.com"
        create_agent(self.agent_email)

        # Create a non-agent customer user
        self.customer_email = "test.link.customer@example.com"
        if not frappe.db.exists("User", self.customer_email):
            frappe.get_doc(
                {
                    "doctype": "User",
                    "email": self.customer_email,
                    "first_name": "Test",
                    "last_name": "Customer",
                    "send_welcome_email": 0,
                }
            ).insert(ignore_permissions=True)

        # Create test tickets (names are stored as strings for API calls)
        ticket_a = make_ticket(
            subject="Ticket A for linking",
            raised_by=self.customer_email,
        )
        ticket_b = make_ticket(
            subject="Ticket B for linking",
            raised_by=self.customer_email,
        )
        ticket_c = make_ticket(
            subject="Ticket C for linking",
            raised_by=self.customer_email,
        )
        # Autoincrement names are integers; convert to str for API type validation
        self.ticket_a_name = str(ticket_a.name)
        self.ticket_b_name = str(ticket_b.name)
        self.ticket_c_name = str(ticket_c.name)

        # Run as agent for all link operations
        frappe.set_user(self.agent_email)

    def tearDown(self):
        frappe.set_user("Administrator")
        frappe.db.rollback()

    # ─── Bidirectionality ───────────────────────────────────────────────────

    def test_related_to_creates_bidirectional_links(self):
        """AC #1, #9: 'Related to' creates a forward and reverse link."""
        link_tickets(self.ticket_a_name, self.ticket_b_name, "Related to")

        forward = frappe.db.exists(
            "HD Related Ticket",
            {
                "parent": self.ticket_a_name,
                "parenttype": "HD Ticket",
                "ticket": self.ticket_b_name,
                "link_type": "Related to",
            },
        )
        reverse = frappe.db.exists(
            "HD Related Ticket",
            {
                "parent": self.ticket_b_name,
                "parenttype": "HD Ticket",
                "ticket": self.ticket_a_name,
                "link_type": "Related to",
            },
        )
        self.assertTrue(forward, "Forward 'Related to' link not created on Ticket A")
        self.assertTrue(reverse, "Reverse 'Related to' link not created on Ticket B")

    def test_caused_by_creates_correct_inverse(self):
        """AC #2, #9: 'Caused by' on A → 'Causes' on B."""
        link_tickets(self.ticket_a_name, self.ticket_b_name, "Caused by")

        a_type = frappe.db.get_value(
            "HD Related Ticket",
            {
                "parent": self.ticket_a_name,
                "parenttype": "HD Ticket",
                "ticket": self.ticket_b_name,
            },
            "link_type",
        )
        b_type = frappe.db.get_value(
            "HD Related Ticket",
            {
                "parent": self.ticket_b_name,
                "parenttype": "HD Ticket",
                "ticket": self.ticket_a_name,
            },
            "link_type",
        )
        self.assertEqual(a_type, "Caused by", "Ticket A should show 'Caused by'")
        self.assertEqual(b_type, "Causes", "Ticket B should show inverse 'Causes'")

    def test_duplicate_of_creates_correct_inverse(self):
        """AC #3: 'Duplicate of' on A → 'Duplicated by' on B."""
        link_tickets(self.ticket_a_name, self.ticket_b_name, "Duplicate of")

        b_type = frappe.db.get_value(
            "HD Related Ticket",
            {
                "parent": self.ticket_b_name,
                "parenttype": "HD Ticket",
                "ticket": self.ticket_a_name,
            },
            "link_type",
        )
        self.assertEqual(b_type, "Duplicated by", "Ticket B should show 'Duplicated by'")

    # ─── Auto-close for Duplicate ────────────────────────────────────────────

    def test_duplicate_of_auto_closes_ticket_a(self):
        """AC #3, #10: 'Duplicate of' auto-closes Ticket A."""
        link_tickets(self.ticket_a_name, self.ticket_b_name, "Duplicate of")

        status = frappe.db.get_value("HD Ticket", self.ticket_a_name, "status")
        expected = (
            DUPLICATE_STATUS
            if frappe.db.exists("HD Ticket Status", DUPLICATE_STATUS)
            else FALLBACK_CLOSE_STATUS
        )
        self.assertEqual(
            status,
            expected,
            f"Ticket A should be auto-closed as '{expected}', got '{status}'",
        )

    def test_duplicate_of_adds_system_comment_on_ticket_a(self):
        """AC #3, #10: A system comment mentioning Ticket B is added to Ticket A."""
        link_tickets(self.ticket_a_name, self.ticket_b_name, "Duplicate of")

        comments = frappe.get_all(
            "HD Ticket Comment",
            filters={
                "reference_ticket": self.ticket_a_name,
                "is_internal": 0,
            },
            fields=["content"],
        )
        self.assertTrue(len(comments) > 0, "No comment added to Ticket A after duplicate link")
        self.assertIn(
            self.ticket_b_name,
            comments[0]["content"],
            "System comment should mention the duplicate target ticket ID",
        )

    def test_duplicate_of_does_not_close_ticket_b(self):
        """AC #10: Ticket B must NOT be auto-closed."""
        original_status = frappe.db.get_value("HD Ticket", self.ticket_b_name, "status")
        link_tickets(self.ticket_a_name, self.ticket_b_name, "Duplicate of")
        status_after = frappe.db.get_value("HD Ticket", self.ticket_b_name, "status")
        self.assertEqual(
            original_status,
            status_after,
            "Ticket B (the original) must not be auto-closed",
        )

    # ─── Validation Errors ───────────────────────────────────────────────────

    def test_self_link_raises_validation_error(self):
        """AC #5, #9: Linking a ticket to itself must raise ValidationError."""
        with self.assertRaises(frappe.ValidationError):
            link_tickets(self.ticket_a_name, self.ticket_a_name, "Related to")

    def test_duplicate_link_raises_validation_error(self):
        """AC #5, #9: Creating a second link between the same two tickets must fail."""
        link_tickets(self.ticket_a_name, self.ticket_b_name, "Related to")
        with self.assertRaises(frappe.ValidationError):
            link_tickets(self.ticket_a_name, self.ticket_b_name, "Caused by")

    def test_reverse_duplicate_link_raises_validation_error(self):
        """AC #9: Duplicate check also catches reverse direction."""
        link_tickets(self.ticket_a_name, self.ticket_b_name, "Related to")
        with self.assertRaises(frappe.ValidationError):
            link_tickets(self.ticket_b_name, self.ticket_a_name, "Related to")

    def test_invalid_link_type_raises_validation_error(self):
        """AC #4: Invalid link type must raise ValidationError."""
        with self.assertRaises(frappe.ValidationError):
            link_tickets(self.ticket_a_name, self.ticket_b_name, "InvalidType")

    # ─── Unlink ──────────────────────────────────────────────────────────────

    def test_unlink_removes_both_directions(self):
        """AC #7: Unlinking removes forward and reverse child records."""
        link_tickets(self.ticket_a_name, self.ticket_b_name, "Related to")
        unlink_tickets(self.ticket_a_name, self.ticket_b_name)

        forward = frappe.db.exists(
            "HD Related Ticket",
            {"parent": self.ticket_a_name, "ticket": self.ticket_b_name},
        )
        reverse = frappe.db.exists(
            "HD Related Ticket",
            {"parent": self.ticket_b_name, "ticket": self.ticket_a_name},
        )
        self.assertFalse(forward, "Forward link should be removed after unlink")
        self.assertFalse(reverse, "Reverse link should be removed after unlink")

    # ─── Permissions ─────────────────────────────────────────────────────────

    def test_non_agent_cannot_link_tickets(self):
        """AC #11: Customer-role user must receive PermissionError."""
        frappe.set_user(self.customer_email)
        with self.assertRaises(frappe.PermissionError):
            link_tickets(self.ticket_a_name, self.ticket_b_name, "Related to")
        frappe.set_user(self.agent_email)

    def test_non_agent_cannot_unlink_tickets(self):
        """AC #11: Customer-role user cannot unlink either."""
        # First create a link as agent
        link_tickets(self.ticket_a_name, self.ticket_b_name, "Related to")
        # Now try to unlink as customer
        frappe.set_user(self.customer_email)
        with self.assertRaises(frappe.PermissionError):
            unlink_tickets(self.ticket_a_name, self.ticket_b_name)
        frappe.set_user(self.agent_email)
