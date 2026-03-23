# Copyright (c) 2026, Frappe Technologies Pvt. Ltd. and Contributors
# See license.txt
# Story 3.8: HD Brand DocType unit tests

import frappe
from frappe.tests.utils import FrappeTestCase


class TestHDBrand(FrappeTestCase):
    """Unit tests for HD Brand DocType validation (Story 3.8, AC #1)."""

    def setUp(self):
        frappe.set_user("Administrator")
        # Clean up any brands created in previous test runs
        for name in frappe.db.get_all("HD Brand", pluck="name"):
            if name.startswith("Test Brand"):
                frappe.delete_doc("HD Brand", name, force=True)
        frappe.db.commit()

    def tearDown(self):
        frappe.set_user("Administrator")
        for name in frappe.db.get_all("HD Brand", pluck="name"):
            if name.startswith("Test Brand"):
                frappe.delete_doc("HD Brand", name, force=True)
        frappe.db.commit()

    def _make_brand(self, **kwargs):
        defaults = {
            "doctype": "HD Brand",
            "brand_name": "Test Brand Alpha",
            "support_email": "support@testbrand.example.com",
            "portal_domain": "support.testbrand.example.com",
            "primary_color": "#FF5733",
            "is_active": 1,
        }
        defaults.update(kwargs)
        doc = frappe.get_doc(defaults)
        doc.insert(ignore_permissions=True)
        frappe.db.commit()
        return doc

    # ------------------------------------------------------------------
    # AC #1: DocType exists and required fields are enforced
    # ------------------------------------------------------------------

    def test_brand_creation_succeeds(self):
        """Brand created with valid fields succeeds."""
        brand = self._make_brand()
        self.assertEqual(brand.brand_name, "Test Brand Alpha")
        self.assertEqual(brand.support_email, "support@testbrand.example.com")
        self.assertEqual(brand.primary_color, "#FF5733")
        self.assertTrue(brand.is_active)

    def test_brand_name_is_required(self):
        """brand_name (reqd=1) must be provided."""
        with self.assertRaises(frappe.exceptions.ValidationError):
            frappe.get_doc(
                {
                    "doctype": "HD Brand",
                    "support_email": "noop@example.com",
                    "is_active": 1,
                }
            ).insert(ignore_permissions=True)

    def test_invalid_support_email_raises(self):
        """An invalid support_email raises ValidationError."""
        with self.assertRaises(frappe.exceptions.ValidationError):
            self._make_brand(
                brand_name="Test Brand Bad Email",
                support_email="not-an-email",
            )

    def test_valid_support_email_accepted(self):
        """A valid support_email is accepted."""
        brand = self._make_brand(
            brand_name="Test Brand Valid Email",
            support_email="valid@acme.example.com",
        )
        self.assertEqual(brand.support_email, "valid@acme.example.com")

    def test_empty_support_email_allowed(self):
        """support_email is optional — empty string is allowed."""
        brand = self._make_brand(
            brand_name="Test Brand No Email",
            support_email="",
            portal_domain="no-email.example.com",
        )
        self.assertFalse(brand.support_email)

    def test_duplicate_portal_domain_raises(self):
        """Two brands cannot share the same portal_domain."""
        self._make_brand(
            brand_name="Test Brand Domain One",
            support_email="one@example.com",
            portal_domain="shared.example.com",
        )
        with self.assertRaises(frappe.exceptions.ValidationError):
            self._make_brand(
                brand_name="Test Brand Domain Two",
                support_email="two@example.com",
                portal_domain="shared.example.com",
            )

    def test_duplicate_portal_domain_same_brand_allowed(self):
        """Updating a brand does not trigger duplicate portal_domain error for itself."""
        brand = self._make_brand(
            brand_name="Test Brand Self Domain",
            support_email="self@example.com",
            portal_domain="self.example.com",
        )
        # Re-save should not raise
        brand.primary_color = "#000000"
        brand.save(ignore_permissions=True)
        frappe.db.commit()
        self.assertEqual(brand.primary_color, "#000000")

    def test_empty_portal_domain_no_duplicate_check(self):
        """Multiple brands can have empty portal_domain."""
        self._make_brand(
            brand_name="Test Brand Empty Domain A",
            support_email="a@example.com",
            portal_domain="",
        )
        # Second brand with empty portal_domain should not raise
        brand_b = self._make_brand(
            brand_name="Test Brand Empty Domain B",
            support_email="b@example.com",
            portal_domain="",
        )
        self.assertFalse(brand_b.portal_domain)
