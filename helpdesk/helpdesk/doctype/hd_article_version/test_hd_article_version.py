# Copyright (c) 2026, Frappe Technologies and Contributors
# See license.txt

import frappe
from frappe.tests.utils import FrappeTestCase

from helpdesk.api.knowledge_base import get_article_versions, revert_article_to_version
from helpdesk.test_utils import create_agent

_AGENT_EMAIL = "version_test_agent@example.com"
_CATEGORY_NAME = "Version Test Category"


def _make_category():
    if not frappe.db.exists("HD Article Category", {"category_name": _CATEGORY_NAME}):
        return frappe.get_doc(
            {"doctype": "HD Article Category", "category_name": _CATEGORY_NAME}
        ).insert(ignore_permissions=True)
    return frappe.get_doc(
        "HD Article Category",
        frappe.db.get_value("HD Article Category", {"category_name": _CATEGORY_NAME}, "name"),
    )


def _make_article(category, title="Version Test Article", content="<p>Initial content</p>"):
    frappe.set_user(_AGENT_EMAIL)
    doc = frappe.get_doc(
        {
            "doctype": "HD Article",
            "title": title,
            "category": category,
            "content": content,
            "status": "Draft",
        }
    ).insert(ignore_permissions=True)
    frappe.set_user("Administrator")
    return doc


class TestHDArticleVersion(FrappeTestCase):
    def setUp(self):
        frappe.set_user("Administrator")
        create_agent(_AGENT_EMAIL)
        self._category = _make_category()
        self._articles_to_delete = []

    def tearDown(self):
        frappe.set_user("Administrator")
        for article_name in self._articles_to_delete:
            # Delete versions first
            frappe.db.delete("HD Article Version", {"article": article_name})
            if frappe.db.exists("HD Article", article_name):
                frappe.delete_doc("HD Article", article_name, ignore_permissions=True, force=True)
        frappe.db.commit()

    def _article(self, **kwargs):
        doc = _make_article(self._category.name, **kwargs)
        self._articles_to_delete.append(doc.name)
        return doc

    # ── AC #1: version created on content change ──────────────────────────────

    def test_version_created_on_content_change(self):
        """Saving an article with changed content creates one version record."""
        article = self._article(content="<p>Initial</p>")
        # First insert also triggers on_update; clear those versions for a clean slate
        frappe.db.delete("HD Article Version", {"article": article.name})
        frappe.db.commit()

        # Reload to get fresh timestamps before next save
        frappe.set_user(_AGENT_EMAIL)
        article = frappe.get_doc("HD Article", article.name)
        article.content = "<p>Updated content</p>"
        article.save()
        frappe.set_user("Administrator")

        count = frappe.db.count("HD Article Version", {"article": article.name})
        self.assertEqual(count, 1)

        version = frappe.get_last_doc(
            "HD Article Version", filters={"article": article.name}
        )
        self.assertEqual(version.content, "<p>Updated content</p>")
        self.assertEqual(version.author, _AGENT_EMAIL)
        self.assertIsNotNone(version.timestamp)

    # ── AC #1: no version on unchanged save ───────────────────────────────────

    def test_no_version_on_unchanged_save(self):
        """Saving an article without changing content/title/category does not create a version."""
        article = self._article(content="<p>Static</p>")
        frappe.db.delete("HD Article Version", {"article": article.name})
        frappe.db.commit()

        # Reload and save without any content change
        frappe.set_user(_AGENT_EMAIL)
        article = frappe.get_doc("HD Article", article.name)
        article.save()
        frappe.set_user("Administrator")

        count = frappe.db.count("HD Article Version", {"article": article.name})
        self.assertEqual(count, 0)

    # ── AC #8: version numbers increment sequentially ────────────────────────

    def test_version_number_increments(self):
        """Successive content changes produce version numbers 1, 2, 3 in order."""
        article = self._article(content="<p>v0</p>")
        frappe.db.delete("HD Article Version", {"article": article.name})
        frappe.db.commit()

        frappe.set_user(_AGENT_EMAIL)
        for i in range(1, 4):
            # Reload each time to get fresh modified timestamp
            doc = frappe.get_doc("HD Article", article.name)
            doc.content = f"<p>Version {i}</p>"
            doc.save()
        frappe.set_user("Administrator")

        versions = frappe.get_all(
            "HD Article Version",
            filters={"article": article.name},
            fields=["version_number"],
            order_by="version_number asc",
        )
        numbers = [v["version_number"] for v in versions]
        self.assertEqual(numbers, [1, 2, 3])

    # ── AC #6: revert creates new version with correct summary ────────────────

    def test_revert_creates_new_version(self):
        """Reverting to version 1 from version 3 creates version 4 with reverted content."""
        article = self._article(content="<p>v0</p>")
        frappe.db.delete("HD Article Version", {"article": article.name})
        frappe.db.commit()

        frappe.set_user(_AGENT_EMAIL)
        for i in range(1, 4):
            doc = frappe.get_doc("HD Article", article.name)
            doc.content = f"<p>Content {i}</p>"
            doc.save()

        # Get version 1 (oldest)
        version_1 = frappe.get_all(
            "HD Article Version",
            filters={"article": article.name, "version_number": 1},
            fields=["name", "content"],
        )[0]

        # Revert to version 1
        result = revert_article_to_version(article.name, version_1["name"])
        frappe.set_user("Administrator")

        self.assertTrue(result["success"])

        # There should now be 4 versions
        count = frappe.db.count("HD Article Version", {"article": article.name})
        self.assertEqual(count, 4)

        # Version 4 should have v1 content and a "Reverted" change summary
        version_4 = frappe.get_last_doc(
            "HD Article Version", filters={"article": article.name}
        )
        self.assertEqual(version_4.content, version_1["content"])
        self.assertIn("Reverted to version #1", version_4.change_summary)

    # ── AC #7: revert preserves workflow state ────────────────────────────────

    def test_revert_does_not_change_status(self):
        """Revert restores content without changing article workflow state."""
        article = self._article(content="<p>Original</p>")
        # Manually set status to Published (bypassing workflow for test)
        frappe.db.set_value("HD Article", article.name, "status", "Published")
        frappe.db.commit()

        frappe.db.delete("HD Article Version", {"article": article.name})
        frappe.db.commit()

        frappe.set_user(_AGENT_EMAIL)
        doc = frappe.get_doc("HD Article", article.name)
        doc.content = "<p>New content</p>"
        doc.save()

        version_1 = frappe.get_last_doc(
            "HD Article Version", filters={"article": article.name}
        )

        revert_article_to_version(article.name, version_1.name)
        frappe.set_user("Administrator")

        status = frappe.db.get_value("HD Article", article.name, "status")
        self.assertEqual(status, "Published")

    # ── AC #10: guest access denied ──────────────────────────────────────────

    def test_guest_cannot_access_versions(self):
        """Guest user calling get_article_versions raises PermissionError."""
        article = self._article()

        frappe.set_user("Guest")
        self.addCleanup(frappe.set_user, "Administrator")

        with self.assertRaises(frappe.PermissionError):
            get_article_versions(article.name)

    # ── AC #10: agent access allowed ─────────────────────────────────────────

    def test_agent_can_access_versions(self):
        """Agent calling get_article_versions receives version list."""
        article = self._article(content="<p>Readable</p>")
        # Ensure at least 1 version exists
        frappe.db.delete("HD Article Version", {"article": article.name})
        frappe.db.commit()

        frappe.set_user(_AGENT_EMAIL)
        doc = frappe.get_doc("HD Article", article.name)
        doc.content = "<p>Changed</p>"
        doc.save()

        result = get_article_versions(article.name)
        frappe.set_user("Administrator")

        self.assertIsInstance(result, list)
        self.assertGreaterEqual(len(result), 1)
        self.assertIn("version_number", result[0])
        self.assertIn("author_full_name", result[0])
