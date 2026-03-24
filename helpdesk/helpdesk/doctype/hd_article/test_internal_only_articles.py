# Copyright (c) 2024, Frappe Technologies and Contributors
# See license.txt

import frappe
from frappe.tests.utils import FrappeTestCase

from helpdesk.api.knowledge_base import (
    get_agent_articles,
    get_article,
    get_categories,
    get_category_articles,
)
from helpdesk.test_utils import create_agent

_AGENT_EMAIL = "internal_only_agent@example.com"
_CUSTOMER_EMAIL = "internal_only_customer@example.com"


def _make_category(name="Internal Only Test Category"):
    if not frappe.db.exists("HD Article Category", {"category_name": name}):
        return frappe.get_doc(
            {"doctype": "HD Article Category", "category_name": name}
        ).insert(ignore_permissions=True)
    return frappe.get_doc(
        "HD Article Category",
        frappe.db.get_value("HD Article Category", {"category_name": name}, "name"),
    )


def _make_article(category, title="Test Article", status="Published", internal_only=0):
    frappe.set_user(_AGENT_EMAIL)
    doc = frappe.get_doc(
        {
            "doctype": "HD Article",
            "title": title,
            "category": category,
            "content": "<p>Test content</p>",
            "status": status,
            "internal_only": internal_only,
        }
    ).insert(ignore_permissions=True)
    frappe.set_user("Administrator")
    return doc


class TestInternalOnlyArticles(FrappeTestCase):
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
                    "first_name": "Internal",
                    "last_name": "Customer",
                    "send_welcome_email": 0,
                }
            ).insert(ignore_permissions=True)

        cls.category = _make_category()
        frappe.db.commit()  # nosemgrep

    @classmethod
    def tearDownClass(cls):
        frappe.set_user("Administrator")
        frappe.db.delete("HD Article", {"category": cls.category.name})
        if frappe.db.exists("HD Article Category", cls.category.name):
            frappe.db.delete("HD Article Category", {"name": cls.category.name})
        for email in [_AGENT_EMAIL, _CUSTOMER_EMAIL]:
            if frappe.db.exists("User", email):
                frappe.delete_doc("User", email, force=True)
        frappe.db.commit()  # nosemgrep
        super().tearDownClass()

    def setUp(self):
        super().setUp()
        frappe.set_user("Administrator")
        frappe.flags.mute_emails = True

    def tearDown(self):
        frappe.set_user("Administrator")
        frappe.flags.mute_emails = False
        frappe.db.delete("HD Article", {"category": self.category.name})
        frappe.db.commit()  # nosemgrep
        super().tearDown()

    def test_internal_article_excluded_from_get_category_articles(self):
        """AC#2: Internal articles must not appear in customer portal category listing."""
        _make_article(self.category.name, title="Public Article", internal_only=0)
        _make_article(self.category.name, title="Internal Article", internal_only=1)

        frappe.set_user(_CUSTOMER_EMAIL)
        articles = get_category_articles(self.category.name)
        titles = [a["title"] for a in articles]

        self.assertIn("Public Article", titles)
        self.assertNotIn("Internal Article", titles)

    def test_internal_article_blocked_via_get_article(self):
        """AC#3: Non-agent fetching an internal article by name must get PermissionError."""
        article = _make_article(self.category.name, title="Secret Article", internal_only=1)

        frappe.set_user(_CUSTOMER_EMAIL)
        with self.assertRaises(frappe.PermissionError):
            get_article(article.name)

    def test_agent_can_access_internal_article(self):
        """AC#4: Agents must be able to access internal articles."""
        article = _make_article(self.category.name, title="Agent Internal Article", internal_only=1)

        frappe.set_user(_AGENT_EMAIL)
        result = get_article(article.name)
        self.assertEqual(result["title"], "Agent Internal Article")
        self.assertEqual(result["internal_only"], 1)

    def test_internal_only_flag_in_get_agent_articles(self):
        """AC#4: get_agent_articles returns internal_only field so agents can identify them."""
        internal = _make_article(self.category.name, title="My Internal Article", internal_only=1)

        frappe.set_user(_AGENT_EMAIL)
        articles = get_agent_articles(category=self.category.name)
        found = next((a for a in articles if a["name"] == internal.name), None)

        self.assertIsNotNone(found, "Internal article must appear in agent articles list")
        self.assertEqual(found["internal_only"], 1)

    def test_internal_article_excluded_from_get_categories_count(self):
        """AC#2: Category article count shown in portal must exclude internal articles."""
        _make_article(self.category.name, title="Visible Article", internal_only=0)
        _make_article(self.category.name, title="Hidden Internal Article", internal_only=1)

        frappe.set_user(_CUSTOMER_EMAIL)
        categories = get_categories()
        cat = next((c for c in categories if c["name"] == self.category.name), None)

        # Category should appear with count of 1 (only the public article)
        self.assertIsNotNone(cat, "Category with public articles must appear in portal")
        self.assertEqual(cat["article_count"], 1)
