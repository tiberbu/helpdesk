# Copyright (c) 2026, Frappe Technologies Pvt. Ltd. and Contributors
# See license.txt
# Sprint 1 (Login Redesign): host-pattern brand resolver tests.

import frappe
from frappe.tests.utils import FrappeTestCase

from helpdesk.www.login import (
    _HOST_CACHE_NAMESPACE,
    _SETTINGS_CACHE_KEY,
    get_login_settings,
    invalidate_login_brand_cache,
    resolve_brand,
)

# Brand-name prefix used by every fixture this module creates so we can clean
# up without disturbing fixtures owned by other tests / Phase 1.
_TEST_PREFIX = "Test Resolver Brand "


class TestBrandResolver(FrappeTestCase):
    def setUp(self):
        frappe.set_user("Administrator")
        self._cleanup()
        invalidate_login_brand_cache()

    def tearDown(self):
        frappe.set_user("Administrator")
        self._cleanup()
        invalidate_login_brand_cache()

    # --- helpers --------------------------------------------------------

    def _cleanup(self):
        for name in frappe.db.get_all("HD Brand", pluck="name"):
            if name.startswith(_TEST_PREFIX):
                frappe.delete_doc("HD Brand", name, force=True)
        frappe.db.commit()

    def _make(self, suffix, **kwargs):
        defaults = {
            "doctype": "HD Brand",
            "brand_name": f"{_TEST_PREFIX}{suffix}",
            "is_active": 1,
        }
        defaults.update(kwargs)
        doc = frappe.get_doc(defaults)
        doc.insert(ignore_permissions=True)
        frappe.db.commit()
        return doc

    # --- resolver behaviour --------------------------------------------

    def test_exact_host_pattern_wins_over_wildcard(self):
        # Wildcard brand (*.tiberbu.health) and an exact brand
        # (erp.tiberbu.health). Exact should always win.
        self._make(
            "Wildcard",
            host_patterns="*.tiberbu.health",
        )
        self._make(
            "Exact",
            host_patterns="erp.tiberbu.health",
        )
        result = resolve_brand("erp.tiberbu.health")
        self.assertEqual(result["brand_name"], f"{_TEST_PREFIX}Exact")

    def test_longest_suffix_wildcard_wins(self):
        # Two wildcard brands; the more-specific should win.
        self._make(
            "Broad",
            host_patterns="*.tiberbu.app",
        )
        self._make(
            "Specific",
            host_patterns="*.b.tiberbu.app",
        )
        result = resolve_brand("a.b.tiberbu.app")
        self.assertEqual(result["brand_name"], f"{_TEST_PREFIX}Specific")

    def test_portal_domain_fallback_when_host_patterns_empty(self):
        # Brand with only portal_domain set (Phase 1 record shape).
        self._make(
            "Legacy",
            portal_domain="legacy.example.com",
        )
        result = resolve_brand("legacy.example.com")
        self.assertEqual(result["brand_name"], f"{_TEST_PREFIX}Legacy")

    def test_default_brand_when_nothing_matches(self):
        self._make(
            "Default",
            is_default=1,
        )
        result = resolve_brand("totally-unrelated.example.com")
        self.assertEqual(result["brand_name"], f"{_TEST_PREFIX}Default")

    def test_builtin_fallback_when_no_default_brand(self):
        # No fixtures match and there is no enabled default brand among
        # our test fixtures. The resolver may still return a Phase 1 default
        # brand if one exists in the DB; only assert the no-test-match path.
        self._make(
            "NotMatching",
            host_patterns="elsewhere.example.com",
            is_default=0,
        )
        result = resolve_brand("definitely-not-a-host.example.invalid")
        # Either the built-in fallback (no Phase 1 default seeded) or some
        # other default brand. We assert that the test-prefixed NotMatching
        # was NOT chosen.
        self.assertNotEqual(result["brand_name"], f"{_TEST_PREFIX}NotMatching")

    def test_disabled_brand_is_skipped(self):
        # Inactive brand with a matching host_pattern must not be returned.
        self._make(
            "Disabled",
            host_patterns="disabled.example.com",
            is_active=0,
        )
        result = resolve_brand("disabled.example.com")
        self.assertNotEqual(result["brand_name"], f"{_TEST_PREFIX}Disabled")

    def test_cache_invalidation_on_update(self):
        # First resolve populates the cache; then change the brand and
        # confirm the next resolve sees the new state.
        brand = self._make(
            "CacheTest",
            host_patterns="cache.example.com",
        )
        first = resolve_brand("cache.example.com")
        self.assertEqual(first["brand_name"], f"{_TEST_PREFIX}CacheTest")

        # Disable the brand. on_update flushes the cache namespace.
        brand.is_active = 0
        brand.save(ignore_permissions=True)
        frappe.db.commit()

        second = resolve_brand("cache.example.com")
        self.assertNotEqual(second["brand_name"], f"{_TEST_PREFIX}CacheTest")

    def test_cache_hit_on_second_call(self):
        # The second call for the same host should hit the Redis cache
        # rather than re-running the DB scan.
        self._make(
            "Cached",
            host_patterns="cached.example.com",
        )
        resolve_brand("cached.example.com")
        cached = frappe.cache().get_value(
            f"{_HOST_CACHE_NAMESPACE}:cached.example.com"
        )
        self.assertIsNotNone(cached)
        self.assertEqual(cached["brand_name"], f"{_TEST_PREFIX}Cached")

    def test_host_is_lowercased_before_match(self):
        self._make(
            "MixedCaseInput",
            host_patterns="erp.tiberbu.health",
        )
        # Caller passes a mixed-case Host header.
        result = resolve_brand("ERP.Tiberbu.Health")
        self.assertEqual(result["brand_name"], f"{_TEST_PREFIX}MixedCaseInput")


class TestLoginSettingsReader(FrappeTestCase):
    """Verifies the cached HD Settings reader exposed by login.py."""

    def setUp(self):
        frappe.set_user("Administrator")
        frappe.cache().delete_value(_SETTINGS_CACHE_KEY)
        # Restore defaults
        frappe.db.set_value("HD Settings", "HD Settings", "new_login_page_enabled", 0)
        frappe.db.set_value("HD Settings", "HD Settings", "login_hero_audience", "both")
        frappe.db.set_value("HD Settings", "HD Settings", "mfa_policy", "optional")
        frappe.db.commit()

    def tearDown(self):
        frappe.set_user("Administrator")
        frappe.db.set_value("HD Settings", "HD Settings", "new_login_page_enabled", 0)
        frappe.db.set_value("HD Settings", "HD Settings", "login_hero_audience", "both")
        frappe.db.set_value("HD Settings", "HD Settings", "mfa_policy", "optional")
        frappe.db.commit()
        frappe.cache().delete_value(_SETTINGS_CACHE_KEY)

    def test_returns_defaults_on_fresh_singleton(self):
        result = get_login_settings()
        self.assertEqual(result["new_login_page_enabled"], False)
        self.assertEqual(result["login_hero_audience"], "both")
        self.assertEqual(result["mfa_policy"], "optional")

    def test_reflects_field_change_after_cache_invalidation(self):
        # First call caches the False value.
        self.assertFalse(get_login_settings()["new_login_page_enabled"])
        # Toggle the field via the singleton and clear the cache directly.
        frappe.db.set_value("HD Settings", "HD Settings", "new_login_page_enabled", 1)
        frappe.db.commit()
        frappe.cache().delete_value(_SETTINGS_CACHE_KEY)
        # Frappe's per-request doc cache also holds HD Settings; clear it.
        frappe.clear_cache(doctype="HD Settings")

        self.assertTrue(get_login_settings()["new_login_page_enabled"])


class TestSeededTenantBrands(FrappeTestCase):
    """Sprint 5 — verifies the Tiberbu / DHA records seeded by the
    seed_tenant_brands patch resolve correctly from real-world host headers.
    """

    def setUp(self):
        frappe.set_user("Administrator")
        invalidate_login_brand_cache()

    def tearDown(self):
        invalidate_login_brand_cache()

    def test_tiberbu_health_subdomain_resolves_tiberbu(self):
        if not frappe.db.exists("HD Brand", "Tiberbu"):
            self.skipTest("Tiberbu brand fixture not seeded on this site")
        result = resolve_brand("erp.tiberbu.health")
        self.assertEqual(result["brand_name"], "Tiberbu")
        self.assertEqual(result["primary_color"], "#5551FF")

    def test_tiberbu_app_subdomain_resolves_tiberbu(self):
        if not frappe.db.exists("HD Brand", "Tiberbu"):
            self.skipTest("Tiberbu brand fixture not seeded on this site")
        result = resolve_brand("support.tiberbu.app")
        self.assertEqual(result["brand_name"], "Tiberbu")

    def test_dha_subdomain_resolves_dha(self):
        if not frappe.db.exists("HD Brand", "DHA"):
            self.skipTest("DHA brand fixture not seeded on this site")
        result = resolve_brand("app.dha.gov.ae")
        self.assertEqual(result["brand_name"], "DHA")
        self.assertEqual(result["primary_color"], "#1A8755")
        self.assertIn("DHA", result["headline"])

    def test_unrelated_host_falls_through(self):
        result = resolve_brand("unknown.example.com")
        self.assertNotIn(result["brand_name"], {"Tiberbu", "DHA"})

    def test_two_seeded_brands_have_distinct_palettes(self):
        if not (
            frappe.db.exists("HD Brand", "Tiberbu")
            and frappe.db.exists("HD Brand", "DHA")
        ):
            self.skipTest("Both Tiberbu and DHA must be seeded for this test")
        tiberbu = resolve_brand("erp.tiberbu.health")
        dha = resolve_brand("app.dha.gov.ae")
        self.assertNotEqual(tiberbu["primary_color"], dha["primary_color"])
        self.assertNotEqual(tiberbu["headline"], dha["headline"])
