# Copyright (c) 2026, Frappe Technologies and Contributors
# See license.txt
# Story 5.4: Ticket-Article Linking — backend unit tests

import frappe
from frappe.tests.utils import FrappeTestCase

from helpdesk.api.knowledge_base import (
    get_linked_tickets,
    link_article_to_ticket,
    prefill_article_from_ticket,
    remove_article_link,
    search_articles,
)
from helpdesk.test_utils import create_agent, make_ticket


_AGENT_EMAIL = "kb_link_agent@example.com"
_CUSTOMER_EMAIL = "kb_link_customer@example.com"


def _make_category(name="KB Link Test Category"):
    if not frappe.db.exists("HD Article Category", {"category_name": name}):
        return frappe.get_doc(
            {"doctype": "HD Article Category", "category_name": name}
        ).insert(ignore_permissions=True)
    return frappe.get_doc(
        "HD Article Category",
        frappe.db.get_value("HD Article Category", {"category_name": name}, "name"),
    )


def _make_article(category, title="Test Article", status="Published"):
    doc = frappe.get_doc(
        {
            "doctype": "HD Article",
            "title": title,
            "category": category,
            "content": "<p>Content</p>",
            "status": status,
        }
    ).insert(ignore_permissions=True)
    return doc


class TestTicketArticleLinking(FrappeTestCase):
    """Unit tests for Story 5.4 Ticket-Article Linking (AC #2–#11)."""

    @classmethod
    def setUpClass(cls):
        super().setUpClass()
        frappe.set_user("Administrator")

        create_agent(_AGENT_EMAIL)

        if not frappe.db.exists("User", _CUSTOMER_EMAIL):
            frappe.get_doc(
                {
                    "doctype": "User",
                    "email": _CUSTOMER_EMAIL,
                    "first_name": "Link",
                    "last_name": "Customer",
                    "send_welcome_email": 0,
                }
            ).insert(ignore_permissions=True)

        cls.category = _make_category()
        cls.published_article = _make_article(cls.category.name, title="Published Linking Article")
        cls.draft_article = _make_article(cls.category.name, title="Draft Linking Article", status="Draft")

        ticket = make_ticket(
            subject="Link Article Test Ticket",
            raised_by=_CUSTOMER_EMAIL,
        )
        cls.ticket = ticket
        cls.ticket_name = str(ticket.name)
        frappe.db.commit()  # nosemgrep

    @classmethod
    def tearDownClass(cls):
        frappe.set_user("Administrator")
        frappe.db.delete("HD Article", {"category": cls.category.name})
        if frappe.db.exists("HD Article Category", cls.category.name):
            frappe.db.delete("HD Article Category", {"name": cls.category.name})
        if frappe.db.exists("HD Ticket", cls.ticket_name):
            frappe.delete_doc("HD Ticket", cls.ticket_name, force=True)
        if frappe.db.exists("User", _CUSTOMER_EMAIL):
            frappe.delete_doc("User", _CUSTOMER_EMAIL, force=True)
        frappe.db.commit()  # nosemgrep
        super().tearDownClass()

    def setUp(self):
        super().setUp()
        frappe.set_user("Administrator")
        # Remove any linked articles from the ticket so each test starts clean
        frappe.db.delete(
            "HD Ticket Article",
            {"parent": self.ticket_name, "parenttype": "HD Ticket"},
        )
        frappe.db.commit()  # nosemgrep

    def tearDown(self):
        frappe.set_user("Administrator")
        frappe.db.delete(
            "HD Ticket Article",
            {"parent": self.ticket_name, "parenttype": "HD Ticket"},
        )
        frappe.db.commit()  # nosemgrep
        super().tearDown()

    # ------------------------------------------------------------------
    # AC #2: search_articles only returns Published articles
    # ------------------------------------------------------------------
    def test_search_articles_returns_only_published(self):
        frappe.set_user(_AGENT_EMAIL)
        results = search_articles(query="Linking Article")
        names = [r["name"] for r in results]
        self.assertIn(self.published_article.name, names)
        self.assertNotIn(self.draft_article.name, names)

    def test_search_articles_filters_by_query(self):
        frappe.set_user(_AGENT_EMAIL)
        results = search_articles(query="Published Linking")
        names = [r["name"] for r in results]
        self.assertIn(self.published_article.name, names)

    def test_search_articles_returns_category_name(self):
        frappe.set_user(_AGENT_EMAIL)
        results = search_articles(query="Published Linking")
        hit = next((r for r in results if r["name"] == self.published_article.name), None)
        self.assertIsNotNone(hit)
        self.assertIn("category_name", hit)

    # ------------------------------------------------------------------
    # AC #3: link_article_to_ticket creates child row
    # ------------------------------------------------------------------
    def test_link_article_creates_child_row(self):
        frappe.set_user(_AGENT_EMAIL)
        result = link_article_to_ticket(
            ticket=self.ticket_name, article=self.published_article.name
        )
        self.assertEqual(result["article"], self.published_article.name)
        exists = frappe.db.exists(
            "HD Ticket Article",
            {
                "parent": self.ticket_name,
                "parenttype": "HD Ticket",
                "article": self.published_article.name,
            },
        )
        self.assertTrue(exists)

    def test_link_article_requires_agent(self):
        frappe.set_user(_CUSTOMER_EMAIL)
        with self.assertRaises(Exception):
            link_article_to_ticket(
                ticket=self.ticket_name, article=self.published_article.name
            )

    # ------------------------------------------------------------------
    # AC #4: Duplicate prevention
    # ------------------------------------------------------------------
    def test_link_article_prevents_duplicate(self):
        frappe.set_user(_AGENT_EMAIL)
        link_article_to_ticket(
            ticket=self.ticket_name, article=self.published_article.name
        )
        with self.assertRaises(frappe.ValidationError):
            link_article_to_ticket(
                ticket=self.ticket_name, article=self.published_article.name
            )

    # ------------------------------------------------------------------
    # AC #5: remove_article_link removes the child row
    # ------------------------------------------------------------------
    def test_remove_article_link_removes_row(self):
        frappe.set_user(_AGENT_EMAIL)
        link_article_to_ticket(
            ticket=self.ticket_name, article=self.published_article.name
        )
        remove_article_link(ticket=self.ticket_name, article=self.published_article.name)
        exists = frappe.db.exists(
            "HD Ticket Article",
            {
                "parent": self.ticket_name,
                "parenttype": "HD Ticket",
                "article": self.published_article.name,
            },
        )
        self.assertFalse(exists)

    def test_remove_article_link_raises_if_not_found(self):
        frappe.set_user(_AGENT_EMAIL)
        with self.assertRaises(frappe.ValidationError):
            remove_article_link(
                ticket=self.ticket_name, article=self.published_article.name
            )

    def test_remove_article_link_requires_agent(self):
        frappe.set_user("Administrator")
        link_article_to_ticket(
            ticket=self.ticket_name, article=self.published_article.name
        )
        frappe.set_user(_CUSTOMER_EMAIL)
        with self.assertRaises(Exception):
            remove_article_link(
                ticket=self.ticket_name, article=self.published_article.name
            )

    # ------------------------------------------------------------------
    # AC #8: get_linked_tickets returns count and tickets list
    # ------------------------------------------------------------------
    def test_get_linked_tickets_returns_correct_count(self):
        frappe.set_user(_AGENT_EMAIL)
        link_article_to_ticket(
            ticket=self.ticket_name, article=self.published_article.name
        )
        result = get_linked_tickets(article=self.published_article.name)
        self.assertGreaterEqual(result["count"], 1)
        ticket_names = [t["name"] for t in result["tickets"]]
        self.assertIn(self.ticket_name, [str(n) for n in ticket_names])

    def test_get_linked_tickets_returns_subject_and_status(self):
        frappe.set_user(_AGENT_EMAIL)
        link_article_to_ticket(
            ticket=self.ticket_name, article=self.published_article.name
        )
        result = get_linked_tickets(article=self.published_article.name)
        ticket_row = next(
            (t for t in result["tickets"] if str(t["name"]) == self.ticket_name),
            None,
        )
        self.assertIsNotNone(ticket_row)
        self.assertIn("subject", ticket_row)
        self.assertIn("status", ticket_row)

    def test_get_linked_tickets_returns_zero_count_when_none(self):
        result = get_linked_tickets(article=self.draft_article.name)
        self.assertEqual(result["count"], 0)
        self.assertEqual(result["tickets"], [])

    # ------------------------------------------------------------------
    # AC #6: prefill_article_from_ticket returns expected fields
    # ------------------------------------------------------------------
    def test_prefill_article_from_ticket_returns_title(self):
        frappe.set_user(_AGENT_EMAIL)
        result = prefill_article_from_ticket(ticket=self.ticket_name)
        self.assertEqual(result["title"], self.ticket.subject)  # ticket.subject is still accessible from the doc object

    def test_prefill_article_from_ticket_returns_source_ticket(self):
        frappe.set_user(_AGENT_EMAIL)
        result = prefill_article_from_ticket(ticket=self.ticket_name)
        self.assertEqual(str(result["source_ticket"]), self.ticket_name)

    def test_prefill_article_from_ticket_requires_agent(self):
        frappe.set_user(_CUSTOMER_EMAIL)
        with self.assertRaises(Exception):
            prefill_article_from_ticket(ticket=self.ticket_name)

    def test_prefill_article_content_excludes_internal_notes(self):
        """Internal notes must not appear in the pre-fill content (NFR-SE-01)."""
        # Create an internal note comment — should NOT be fetched
        # (prefill only fetches sent Communications, not ticket comments)
        frappe.set_user("Administrator")
        internal = frappe.get_doc(
            {
                "doctype": "HD Ticket Comment",
                "reference_ticket": self.ticket_name,
                "content": "<p>SECRET INTERNAL NOTE</p>",
                "commented_by": _AGENT_EMAIL,
                "is_internal": 1,
            }
        ).insert(ignore_permissions=True)
        try:
            frappe.set_user(_AGENT_EMAIL)
            result = prefill_article_from_ticket(ticket=self.ticket_name)
            self.assertNotIn("SECRET INTERNAL NOTE", result.get("content", ""))
        finally:
            frappe.set_user("Administrator")
            frappe.delete_doc("HD Ticket Comment", internal.name, force=True)
            frappe.db.commit()  # nosemgrep
