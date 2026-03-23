# Copyright (c) 2026, Frappe Technologies and Contributors
# See license.txt
# NFR-SE-01: Internal notes permission boundary tests

import frappe
from frappe.tests.utils import FrappeTestCase

from helpdesk.helpdesk.doctype.hd_ticket.api import get_comments, get_one
from helpdesk.test_utils import create_agent, make_ticket


class TestInternalNotesPermissionBoundary(FrappeTestCase):
    """
    NFR-SE-01: Verify internal notes are never exposed to non-agent users.
    All paths through which a customer might access ticket data must filter
    internal notes out.
    """

    def setUp(self):
        # Create a customer/non-agent user
        self.customer_email = "customer_note_test@example.com"
        if not frappe.db.exists("User", self.customer_email):
            frappe.get_doc(
                {
                    "doctype": "User",
                    "email": self.customer_email,
                    "first_name": "Customer",
                    "last_name": "TestUser",
                    "send_welcome_email": 0,
                }
            ).insert(ignore_permissions=True)

        # Create an agent
        self.agent_email = "agent_note_test@example.com"
        create_agent(self.agent_email)

        # Create a ticket raised by the customer
        frappe.set_user("Administrator")
        self.ticket = make_ticket(
            subject="Internal Note Permission Test",
            raised_by=self.customer_email,
        )

        # Create a regular (public) comment
        self.public_comment = frappe.get_doc(
            {
                "doctype": "HD Ticket Comment",
                "reference_ticket": self.ticket.name,
                "content": "<p>Public comment visible to all</p>",
                "commented_by": self.agent_email,
                "is_internal": 0,
            }
        ).insert(ignore_permissions=True)

        # Create an internal note (agent-only)
        self.internal_note = frappe.get_doc(
            {
                "doctype": "HD Ticket Comment",
                "reference_ticket": self.ticket.name,
                "content": "<p>SECRET: Internal agent-only note</p>",
                "commented_by": self.agent_email,
                "is_internal": 1,
            }
        ).insert(ignore_permissions=True)

    def tearDown(self):
        frappe.set_user("Administrator")

        for name in [self.internal_note.name, self.public_comment.name]:
            if frappe.db.exists("HD Ticket Comment", name):
                frappe.delete_doc("HD Ticket Comment", name, force=True)

        if frappe.db.exists("HD Ticket", self.ticket.name):
            frappe.delete_doc("HD Ticket", self.ticket.name, force=True)

        for email in [self.customer_email, self.agent_email]:
            if frappe.db.exists("User", email):
                frappe.delete_doc("User", email, force=True)

    # ------------------------------------------------------------------ #
    # get_comments() — server-side filter                                  #
    # ------------------------------------------------------------------ #

    def test_internal_note_hidden_from_non_agent_get_comments(self):
        """
        NFR-SE-01: get_comments() must exclude is_internal=1 comments
        when the caller is not an agent.
        """
        frappe.set_user(self.customer_email)
        comments = get_comments(self.ticket.name)
        names = [c["name"] for c in comments]
        self.assertNotIn(
            self.internal_note.name,
            names,
            "Internal note must NOT be returned to non-agent user via get_comments()",
        )

    def test_no_comments_returned_to_non_agent_without_doctype_perm(self):
        """
        HD Ticket Comment doctype is restricted to Agent/System Manager.
        Non-agents receive an empty list from get_comments() — safe by default.
        The critical guarantee is that internal notes are never present.
        """
        frappe.set_user(self.customer_email)
        comments = get_comments(self.ticket.name)
        self.assertIsInstance(comments, list)
        names = [c["name"] for c in comments]
        self.assertNotIn(
            self.internal_note.name,
            names,
            "Internal note must NOT be returned to non-agent",
        )

    def test_internal_note_visible_to_agent_get_comments(self):
        """
        Agents must be able to see internal notes via get_comments().
        """
        frappe.set_user(self.agent_email)
        comments = get_comments(self.ticket.name)
        names = [c["name"] for c in comments]
        self.assertIn(
            self.internal_note.name,
            names,
            "Internal note MUST be visible to agent via get_comments()",
        )

    # ------------------------------------------------------------------ #
    # get_one() API — full ticket payload                                   #
    # ------------------------------------------------------------------ #

    def test_internal_note_hidden_in_get_one_for_non_agent(self):
        """
        NFR-SE-01: get_one() must not include internal notes in `comments`
        when called by a non-agent.
        """
        frappe.set_user(self.customer_email)
        ticket_data = get_one(self.ticket.name, is_customer_portal=True)
        comment_names = [c["name"] for c in ticket_data.get("comments", [])]
        self.assertNotIn(
            self.internal_note.name,
            comment_names,
            "Internal note must NOT appear in get_one() response for non-agent",
        )

    def test_internal_note_visible_in_get_one_for_agent(self):
        """
        Agents must see internal notes when fetching the full ticket.
        """
        frappe.set_user(self.agent_email)
        ticket_data = get_one(self.ticket.name)
        comment_names = [c["name"] for c in ticket_data.get("comments", [])]
        self.assertIn(
            self.internal_note.name,
            comment_names,
            "Internal note MUST appear in get_one() response for agent",
        )

    def test_internal_note_content_not_leaked_to_non_agent(self):
        """
        Ensure the secret content of the internal note is not present
        in any comment returned to the non-agent.
        """
        frappe.set_user(self.customer_email)
        ticket_data = get_one(self.ticket.name, is_customer_portal=True)
        all_content = " ".join(
            c.get("content", "") for c in ticket_data.get("comments", [])
        )
        self.assertNotIn(
            "SECRET",
            all_content,
            "Internal note content must not be leaked to non-agent via get_one()",
        )

    # ------------------------------------------------------------------ #
    # new_internal_note() — creation permission                            #
    # ------------------------------------------------------------------ #

    def test_non_agent_cannot_create_internal_note(self):
        """
        NFR-SE-01: Non-agents must not be able to create internal notes
        via new_internal_note().
        """
        frappe.set_user(self.customer_email)
        ticket_doc = frappe.get_doc("HD Ticket", self.ticket.name)
        with self.assertRaises(frappe.PermissionError):
            ticket_doc.new_internal_note(content="<p>Unauthorized note</p>")

    def test_agent_can_create_internal_note(self):
        """
        Agents must be able to create internal notes via new_internal_note().
        """
        frappe.set_user(self.agent_email)
        ticket_doc = frappe.get_doc("HD Ticket", self.ticket.name)
        # Should not raise
        ticket_doc.new_internal_note(content="<p>Agent internal note</p>")

        # Verify it was created with is_internal=1
        notes = frappe.get_all(
            "HD Ticket Comment",
            filters={
                "reference_ticket": self.ticket.name,
                "is_internal": 1,
                "content": "<p>Agent internal note</p>",
            },
        )
        self.assertEqual(len(notes), 1, "Internal note must be created with is_internal=1")

        # Cleanup
        frappe.set_user("Administrator")
        frappe.delete_doc("HD Ticket Comment", notes[0].name, force=True)

    # ------------------------------------------------------------------ #
    # is_internal flag integrity                                           #
    # ------------------------------------------------------------------ #

    def test_new_comment_is_not_internal(self):
        """
        new_comment() must always set is_internal=False regardless of input.
        """
        frappe.set_user(self.agent_email)
        ticket_doc = frappe.get_doc("HD Ticket", self.ticket.name)
        ticket_doc.new_comment(content="<p>Regular comment via new_comment</p>")

        comments = frappe.get_all(
            "HD Ticket Comment",
            filters={
                "reference_ticket": self.ticket.name,
                "content": "<p>Regular comment via new_comment</p>",
            },
            fields=["name", "is_internal"],
        )
        self.assertEqual(len(comments), 1)
        self.assertEqual(
            comments[0].is_internal,
            0,
            "new_comment() must NOT set is_internal=1",
        )

        # Cleanup
        frappe.set_user("Administrator")
        frappe.delete_doc("HD Ticket Comment", comments[0].name, force=True)

    def test_new_internal_note_sets_is_internal_flag(self):
        """
        new_internal_note() must set is_internal=1 on the created comment.
        """
        frappe.set_user(self.agent_email)
        ticket_doc = frappe.get_doc("HD Ticket", self.ticket.name)
        ticket_doc.new_internal_note(content="<p>Check is_internal flag</p>")

        notes = frappe.get_all(
            "HD Ticket Comment",
            filters={
                "reference_ticket": self.ticket.name,
                "content": "<p>Check is_internal flag</p>",
            },
            fields=["name", "is_internal"],
        )
        self.assertEqual(len(notes), 1)
        self.assertEqual(
            notes[0].is_internal,
            1,
            "new_internal_note() must set is_internal=1",
        )

        # Cleanup
        frappe.set_user("Administrator")
        frappe.delete_doc("HD Ticket Comment", notes[0].name, force=True)
