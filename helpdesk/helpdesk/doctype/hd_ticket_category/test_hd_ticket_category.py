# Copyright (c) 2026, Frappe Technologies and Contributors
# See license.txt
# Tests for HD Ticket Category DocType — full implementation in Task 7.

import frappe
from frappe.tests import IntegrationTestCase


class TestHDTicketCategory(IntegrationTestCase):
    """
    Unit tests for Story 1.3: Multi-Level Ticket Categorization.

    Covers:
    - AC #1: DocType CRUD (create top-level and sub-category records)
    - AC #2: Hierarchical structure; self-referential link rejection
    - AC #1: is_active defaults to 1
    """

    def _make_category(self, name, parent_category=None, is_active=1):
        """Helper: create and insert an HD Ticket Category for testing."""
        doc = frappe.get_doc(
            {
                "doctype": "HD Ticket Category",
                "name": name,
                "parent_category": parent_category,
                "is_active": is_active,
            }
        )
        doc.insert(ignore_permissions=True)
        self.addCleanup(
            frappe.delete_doc,
            "HD Ticket Category",
            name,
            force=True,
            ignore_missing=True,
        )
        return doc

    # ------------------------------------------------------------------
    # AC #1: Top-level category CRUD
    # ------------------------------------------------------------------

    def test_create_top_level_category(self):
        """A category without parent_category saves successfully (AC #1)."""
        doc = self._make_category("Test-Hardware-TL")
        self.assertEqual(doc.name, "Test-Hardware-TL")
        self.assertIsNone(doc.parent_category or None)

    # ------------------------------------------------------------------
    # AC #1 / #2: Sub-category creation
    # ------------------------------------------------------------------

    def test_create_sub_category(self):
        """A category with a valid parent_category saves successfully (AC #1, #2)."""
        self._make_category("Test-Network-Parent")
        child = self._make_category(
            "Test-VPN-Child", parent_category="Test-Network-Parent"
        )
        self.assertEqual(child.parent_category, "Test-Network-Parent")

    # ------------------------------------------------------------------
    # AC #2: Self-referential links are rejected
    # ------------------------------------------------------------------

    def test_self_referential_rejected(self):
        """Setting parent_category to self raises ValidationError (AC #2)."""
        # Insert without self-reference first so the record exists
        doc = frappe.get_doc(
            {
                "doctype": "HD Ticket Category",
                "name": "Test-SelfRef",
                "is_active": 1,
            }
        )
        doc.insert(ignore_permissions=True)
        self.addCleanup(
            frappe.delete_doc,
            "HD Ticket Category",
            "Test-SelfRef",
            force=True,
            ignore_missing=True,
        )

        doc.parent_category = "Test-SelfRef"
        self.assertRaises(frappe.ValidationError, doc.validate)

    # ------------------------------------------------------------------
    # AC #1: is_active defaults to 1
    # ------------------------------------------------------------------

    def test_is_active_defaults_to_1(self):
        """is_active field defaults to 1 when not explicitly set (AC #1)."""
        doc = frappe.get_doc(
            {
                "doctype": "HD Ticket Category",
                "name": "Test-IsActive-Default",
            }
        )
        doc.insert(ignore_permissions=True)
        self.addCleanup(
            frappe.delete_doc,
            "HD Ticket Category",
            "Test-IsActive-Default",
            force=True,
            ignore_missing=True,
        )
        self.assertEqual(doc.is_active, 1)
