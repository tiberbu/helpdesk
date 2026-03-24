# Copyright (c) 2021, Frappe Technologies and Contributors
# See license.txt

import frappe
from frappe.tests.utils import FrappeTestCase

from helpdesk.api.knowledge_base import (
    approve_article,
    archive_article,
    get_agent_articles,
    get_article,
    get_category_articles,
    reject_article,
    request_changes,
    submit_for_review,
)
from helpdesk.test_utils import create_agent


_AGENT_EMAIL = "kb_test_agent@example.com"
_REVIEWER_EMAIL = "kb_test_reviewer@example.com"
_CUSTOMER_EMAIL = "kb_test_customer@example.com"


def _make_category(name="KB Test Category"):
    if not frappe.db.exists("HD Article Category", {"category_name": name}):
        return frappe.get_doc(
            {"doctype": "HD Article Category", "category_name": name}
        ).insert(ignore_permissions=True)
    return frappe.get_doc(
        "HD Article Category", frappe.db.get_value("HD Article Category", {"category_name": name}, "name")
    )


def _make_article(category, title="Test Article", content="<p>Content</p>", status="Draft"):
    frappe.set_user(_AGENT_EMAIL)
    doc = frappe.get_doc(
        {
            "doctype": "HD Article",
            "title": title,
            "category": category,
            "content": content,
            "status": status,
        }
    ).insert(ignore_permissions=True)
    frappe.set_user("Administrator")
    return doc


class TestHDArticleReviewWorkflow(FrappeTestCase):
    @classmethod
    def setUpClass(cls):
        super().setUpClass()
        frappe.set_user("Administrator")
        # Agent user
        create_agent(_AGENT_EMAIL)

        # Reviewer user (System Manager)
        if not frappe.db.exists("User", _REVIEWER_EMAIL):
            frappe.get_doc(
                {
                    "doctype": "User",
                    "email": _REVIEWER_EMAIL,
                    "first_name": "KB",
                    "last_name": "Reviewer",
                    "send_welcome_email": 0,
                }
            ).insert(ignore_permissions=True)
        reviewer = frappe.get_doc("User", _REVIEWER_EMAIL)
        if "System Manager" not in frappe.get_roles(_REVIEWER_EMAIL):
            reviewer.add_roles("System Manager")

        # Customer (non-agent)
        if not frappe.db.exists("User", _CUSTOMER_EMAIL):
            frappe.get_doc(
                {
                    "doctype": "User",
                    "email": _CUSTOMER_EMAIL,
                    "first_name": "KB",
                    "last_name": "Customer",
                    "send_welcome_email": 0,
                }
            ).insert(ignore_permissions=True)

        # Category
        cls.category = _make_category()
        frappe.db.commit()  # nosemgrep

    @classmethod
    def tearDownClass(cls):
        frappe.set_user("Administrator")
        # Use low-level delete to bypass on_trash category-length check
        frappe.db.delete("HD Article", {"category": cls.category.name})
        if frappe.db.exists("HD Article Category", cls.category.name):
            frappe.db.delete("HD Article Category", {"name": cls.category.name})
        for email in [_AGENT_EMAIL, _REVIEWER_EMAIL, _CUSTOMER_EMAIL]:
            if frappe.db.exists("User", email):
                frappe.delete_doc("User", email, force=True)
        frappe.db.commit()  # nosemgrep
        super().tearDownClass()

    def setUp(self):
        super().setUp()
        frappe.flags.mute_emails = True
        frappe.set_user("Administrator")
        self.article = _make_article(self.category.name)

    def tearDown(self):
        frappe.set_user("Administrator")
        frappe.flags.mute_emails = False
        # Use low-level delete to bypass on_trash category-length check
        frappe.db.delete("HD Article", {"name": self.article.name})
        frappe.db.commit()  # nosemgrep
        super().tearDown()

    # ------------------------------------------------------------------
    # AC #1: Default status is Draft
    # ------------------------------------------------------------------
    def test_new_article_defaults_to_draft(self):
        self.assertEqual(self.article.status, "Draft")

    # ------------------------------------------------------------------
    # AC #2: submit_for_review — Draft → In Review
    # ------------------------------------------------------------------
    def test_submit_for_review_transitions_to_in_review(self):
        frappe.set_user(_AGENT_EMAIL)
        result = submit_for_review(self.article.name)
        self.assertEqual(result["status"], "In Review")
        self.article.reload()
        self.assertEqual(self.article.status, "In Review")

    def test_submit_for_review_clears_reviewer_comment(self):
        # Seed a prior reviewer comment
        frappe.db.set_value("HD Article", self.article.name, "reviewer_comment", "Please fix X")
        frappe.set_user(_AGENT_EMAIL)
        submit_for_review(self.article.name)
        self.article.reload()
        self.assertFalse(self.article.reviewer_comment)

    def test_submit_for_review_requires_agent(self):
        frappe.set_user(_CUSTOMER_EMAIL)
        with self.assertRaises(frappe.PermissionError):
            submit_for_review(self.article.name)

    def test_submit_for_review_requires_draft_status(self):
        frappe.db.set_value("HD Article", self.article.name, "status", "Published")
        frappe.set_user(_AGENT_EMAIL)
        with self.assertRaises(frappe.ValidationError):
            submit_for_review(self.article.name)

    # ------------------------------------------------------------------
    # AC #3: approve_article — In Review → Published
    # ------------------------------------------------------------------
    def test_approve_transitions_to_published(self):
        frappe.db.set_value("HD Article", self.article.name, "status", "In Review")
        frappe.set_user(_REVIEWER_EMAIL)
        result = approve_article(self.article.name)
        self.assertEqual(result["status"], "Published")
        self.article.reload()
        self.assertEqual(self.article.status, "Published")

    def test_approve_requires_reviewer_role(self):
        frappe.db.set_value("HD Article", self.article.name, "status", "In Review")
        frappe.set_user(_AGENT_EMAIL)
        with self.assertRaises(frappe.PermissionError):
            approve_article(self.article.name)

    def test_approve_requires_in_review_status(self):
        # Article is Draft — cannot approve
        frappe.set_user(_REVIEWER_EMAIL)
        with self.assertRaises(frappe.ValidationError):
            approve_article(self.article.name)

    # ------------------------------------------------------------------
    # AC #4: request_changes — In Review → Draft with comment
    # ------------------------------------------------------------------
    def test_request_changes_transitions_to_draft_with_comment(self):
        frappe.db.set_value("HD Article", self.article.name, "status", "In Review")
        frappe.set_user(_REVIEWER_EMAIL)
        result = request_changes(self.article.name, "Please rewrite the introduction.")
        self.assertEqual(result["status"], "Draft")
        self.article.reload()
        self.assertEqual(self.article.status, "Draft")
        self.assertEqual(self.article.reviewer_comment, "Please rewrite the introduction.")

    def test_request_changes_requires_non_empty_comment(self):
        frappe.db.set_value("HD Article", self.article.name, "status", "In Review")
        frappe.set_user(_REVIEWER_EMAIL)
        with self.assertRaises(frappe.ValidationError):
            request_changes(self.article.name, "   ")

    def test_request_changes_requires_reviewer_role(self):
        frappe.db.set_value("HD Article", self.article.name, "status", "In Review")
        frappe.set_user(_AGENT_EMAIL)
        with self.assertRaises(frappe.PermissionError):
            request_changes(self.article.name, "Some comment")

    # ------------------------------------------------------------------
    # AC #5: reject_article — In Review → Archived
    # ------------------------------------------------------------------
    def test_reject_transitions_to_archived(self):
        frappe.db.set_value("HD Article", self.article.name, "status", "In Review")
        frappe.set_user(_REVIEWER_EMAIL)
        result = reject_article(self.article.name)
        self.assertEqual(result["status"], "Archived")
        self.article.reload()
        self.assertEqual(self.article.status, "Archived")

    def test_reject_requires_reviewer_role(self):
        frappe.db.set_value("HD Article", self.article.name, "status", "In Review")
        frappe.set_user(_AGENT_EMAIL)
        with self.assertRaises(frappe.PermissionError):
            reject_article(self.article.name)

    # ------------------------------------------------------------------
    # AC #6: archive_article — Published → Archived
    # ------------------------------------------------------------------
    def test_archive_transitions_to_archived(self):
        frappe.db.set_value("HD Article", self.article.name, "status", "Published")
        frappe.set_user(_REVIEWER_EMAIL)
        result = archive_article(self.article.name)
        self.assertEqual(result["status"], "Archived")

    def test_archive_requires_published_status(self):
        # Article is Draft — cannot archive via this endpoint
        frappe.set_user(_REVIEWER_EMAIL)
        with self.assertRaises(frappe.ValidationError):
            archive_article(self.article.name)

    # ------------------------------------------------------------------
    # AC #7: Portal visibility — non-agents only see Published articles
    # ------------------------------------------------------------------
    def test_get_article_denies_non_agent_access_to_in_review(self):
        frappe.db.set_value("HD Article", self.article.name, "status", "In Review")
        frappe.set_user(_CUSTOMER_EMAIL)
        with self.assertRaises(frappe.PermissionError):
            get_article(self.article.name)

    def test_get_article_allows_agent_access_to_in_review(self):
        frappe.db.set_value("HD Article", self.article.name, "status", "In Review")
        frappe.set_user(_AGENT_EMAIL)
        data = get_article(self.article.name)
        self.assertEqual(data["status"], "In Review")

    def test_get_category_articles_returns_only_published(self):
        # Create a published article alongside our draft
        published = _make_article(
            self.category.name,
            title="Published Article",
            content="<p>Published</p>",
            status="Published",
        )
        try:
            frappe.set_user(_CUSTOMER_EMAIL)
            articles = get_category_articles(self.category.name)
            statuses = {a["name"]: a for a in articles}
            self.assertIn(published.name, statuses)
            self.assertNotIn(self.article.name, statuses)
        finally:
            frappe.set_user("Administrator")
            frappe.db.delete("HD Article", {"name": published.name})
            frappe.db.commit()  # nosemgrep

    # ------------------------------------------------------------------
    # AC #8: get_agent_articles — agents see In Review articles too
    # ------------------------------------------------------------------
    def test_get_agent_articles_includes_in_review(self):
        frappe.db.set_value("HD Article", self.article.name, "status", "In Review")
        frappe.set_user(_AGENT_EMAIL)
        articles = get_agent_articles(category=self.category.name)
        names = [a["name"] for a in articles]
        self.assertIn(self.article.name, names)

    def test_get_agent_articles_excludes_archived(self):
        frappe.db.set_value("HD Article", self.article.name, "status", "Archived")
        frappe.set_user(_AGENT_EMAIL)
        articles = get_agent_articles(category=self.category.name)
        names = [a["name"] for a in articles]
        self.assertNotIn(self.article.name, names)

    def test_get_agent_articles_requires_agent(self):
        frappe.set_user(_CUSTOMER_EMAIL)
        with self.assertRaises(frappe.PermissionError):
            get_agent_articles()
