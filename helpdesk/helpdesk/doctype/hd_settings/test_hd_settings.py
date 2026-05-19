# -*- coding: utf-8 -*-
# Copyright (c) 2018, Frappe Technologies Pvt. Ltd. and Contributors
# See license.txt
from __future__ import unicode_literals

import frappe
from frappe.tests import IntegrationTestCase


class TestHDSettingsFeatureFlags(IntegrationTestCase):
    """Unit tests for HD Settings feature flag infrastructure (Story 1.1)."""

    def setUp(self):
        # Reset feature flags to known defaults before each test
        frappe.db.set_value("HD Settings", "HD Settings", "itil_mode_enabled", 0)
        frappe.db.set_value("HD Settings", "HD Settings", "chat_enabled", 0)
        frappe.db.set_value("HD Settings", "HD Settings", "csat_enabled", 0)
        frappe.db.set_value("HD Settings", "HD Settings", "automation_enabled", 0)
        frappe.db.commit()

    # ------------------------------------------------------------------
    # AC1: itil_mode_enabled defaults to OFF and is persisted correctly
    # ------------------------------------------------------------------

    def test_itil_mode_enabled_defaults_to_off(self):
        """itil_mode_enabled field default is 0 (OFF)."""
        meta = frappe.get_meta("HD Settings")
        field = meta.get_field("itil_mode_enabled")
        self.assertIsNotNone(field, "itil_mode_enabled field must exist on HD Settings")
        self.assertEqual(
            str(field.default),
            "0",
            "itil_mode_enabled must default to 0 (OFF)",
        )

    def test_itil_mode_enabled_persists_when_toggled_on(self):
        """Toggling itil_mode_enabled to ON is saved and readable."""
        frappe.db.set_value("HD Settings", "HD Settings", "itil_mode_enabled", 1)
        frappe.db.commit()

        value = frappe.db.get_single_value("HD Settings", "itil_mode_enabled")
        self.assertEqual(value, 1, "itil_mode_enabled should be 1 after being enabled")

    def test_itil_mode_enabled_persists_when_toggled_off(self):
        """Toggling itil_mode_enabled to OFF is saved and readable."""
        # Enable then disable
        frappe.db.set_value("HD Settings", "HD Settings", "itil_mode_enabled", 1)
        frappe.db.set_value("HD Settings", "HD Settings", "itil_mode_enabled", 0)
        frappe.db.commit()

        value = frappe.db.get_single_value("HD Settings", "itil_mode_enabled")
        self.assertEqual(value, 0, "itil_mode_enabled should be 0 after being disabled")

    # ------------------------------------------------------------------
    # Feature flag fields exist and default to OFF
    # ------------------------------------------------------------------

    def test_chat_enabled_field_exists_and_defaults_to_off(self):
        """chat_enabled field is present with default 0."""
        meta = frappe.get_meta("HD Settings")
        field = meta.get_field("chat_enabled")
        self.assertIsNotNone(field, "chat_enabled field must exist on HD Settings")
        self.assertEqual(
            str(field.default), "0", "chat_enabled must default to 0 (OFF)"
        )

    def test_csat_enabled_field_exists_and_defaults_to_off(self):
        """csat_enabled field is present with default 0."""
        meta = frappe.get_meta("HD Settings")
        field = meta.get_field("csat_enabled")
        self.assertIsNotNone(field, "csat_enabled field must exist on HD Settings")
        self.assertEqual(
            str(field.default), "0", "csat_enabled must default to 0 (OFF)"
        )

    def test_automation_enabled_field_exists_and_defaults_to_off(self):
        """automation_enabled field is present with default 0."""
        meta = frappe.get_meta("HD Settings")
        field = meta.get_field("automation_enabled")
        self.assertIsNotNone(field, "automation_enabled field must exist on HD Settings")
        self.assertEqual(
            str(field.default), "0", "automation_enabled must default to 0 (OFF)"
        )

    # ------------------------------------------------------------------
    # Feature flags can be toggled independently
    # ------------------------------------------------------------------

    def test_chat_enabled_can_be_toggled_on(self):
        """chat_enabled can be set to 1 and read back correctly."""
        frappe.db.set_value("HD Settings", "HD Settings", "chat_enabled", 1)
        frappe.db.commit()
        value = frappe.db.get_single_value("HD Settings", "chat_enabled")
        self.assertEqual(value, 1)

    def test_csat_enabled_can_be_toggled_on(self):
        """csat_enabled can be set to 1 and read back correctly."""
        frappe.db.set_value("HD Settings", "HD Settings", "csat_enabled", 1)
        frappe.db.commit()
        value = frappe.db.get_single_value("HD Settings", "csat_enabled")
        self.assertEqual(value, 1)

    def test_automation_enabled_can_be_toggled_on(self):
        """automation_enabled can be set to 1 and read back correctly."""
        frappe.db.set_value("HD Settings", "HD Settings", "automation_enabled", 1)
        frappe.db.commit()
        value = frappe.db.get_single_value("HD Settings", "automation_enabled")
        self.assertEqual(value, 1)

    def test_feature_flags_are_independent(self):
        """Each feature flag can be toggled independently without affecting others."""
        # Enable only chat
        frappe.db.set_value("HD Settings", "HD Settings", "chat_enabled", 1)
        frappe.db.set_value("HD Settings", "HD Settings", "csat_enabled", 0)
        frappe.db.set_value("HD Settings", "HD Settings", "automation_enabled", 0)
        frappe.db.commit()

        self.assertEqual(frappe.db.get_single_value("HD Settings", "chat_enabled"), 1)
        self.assertEqual(frappe.db.get_single_value("HD Settings", "csat_enabled"), 0)
        self.assertEqual(
            frappe.db.get_single_value("HD Settings", "automation_enabled"), 0
        )

    # ------------------------------------------------------------------
    # AC2/AC3: ITIL fields are hidden by default (mode OFF); visible when ON
    # Verified via HD Ticket metadata and the field hidden property
    # ------------------------------------------------------------------

    def test_itil_ticket_fields_hidden_by_default_in_meta(self):
        """impact, urgency, category, sub_category fields are hidden=1 in HD Ticket meta."""
        meta = frappe.get_meta("HD Ticket")
        for fieldname in ["impact", "urgency", "category", "sub_category"]:
            field = meta.get_field(fieldname)
            self.assertIsNotNone(
                field, f"Field '{fieldname}' must exist on HD Ticket"
            )
            self.assertEqual(
                field.hidden,
                1,
                f"Field '{fieldname}' must be hidden=1 in meta (client script controls visibility)",
            )

    def test_priority_field_exists_on_hd_ticket(self):
        """priority field exists on HD Ticket (becomes read-only in ITIL mode via client script)."""
        meta = frappe.get_meta("HD Ticket")
        field = meta.get_field("priority")
        self.assertIsNotNone(field, "priority field must exist on HD Ticket")

    # ------------------------------------------------------------------
    # HD Settings is a Single DocType — itil_mode_enabled is available globally
    # ------------------------------------------------------------------

    def test_itil_mode_readable_as_single_value(self):
        """itil_mode_enabled is accessible via get_single_value (available to all forms)."""
        frappe.db.set_value("HD Settings", "HD Settings", "itil_mode_enabled", 1)
        frappe.db.commit()

        value = frappe.db.get_single_value("HD Settings", "itil_mode_enabled")
        self.assertIsNotNone(value)
        self.assertEqual(value, 1)

    def tearDown(self):
        # Restore defaults after each test
        frappe.db.set_value("HD Settings", "HD Settings", "itil_mode_enabled", 0)
        frappe.db.set_value("HD Settings", "HD Settings", "chat_enabled", 0)
        frappe.db.set_value("HD Settings", "HD Settings", "csat_enabled", 0)
        frappe.db.set_value("HD Settings", "HD Settings", "automation_enabled", 0)
        frappe.db.set_value("HD Settings", "HD Settings", "new_login_page_enabled", 0)
        frappe.db.commit()


class TestHDSettingsLoginFields(IntegrationTestCase):
    """Tests for the Authentication section added in Sprint 1 (Login Redesign)."""

    def setUp(self):
        frappe.set_user("Administrator")
        frappe.cache().delete_value("hd_login_settings_cache")

    def tearDown(self):
        frappe.set_user("Administrator")
        frappe.db.set_value("HD Settings", "HD Settings", "new_login_page_enabled", 0)
        frappe.db.set_value("HD Settings", "HD Settings", "login_hero_audience", "both")
        frappe.db.set_value("HD Settings", "HD Settings", "mfa_policy", "optional")
        frappe.db.commit()
        frappe.cache().delete_value("hd_login_settings_cache")

    def test_new_login_page_enabled_field_exists_and_defaults_off(self):
        meta = frappe.get_meta("HD Settings")
        field = meta.get_field("new_login_page_enabled")
        self.assertIsNotNone(field)
        self.assertEqual(str(field.default), "0")

    def test_login_hero_audience_field_exists_and_defaults_both(self):
        meta = frappe.get_meta("HD Settings")
        field = meta.get_field("login_hero_audience")
        self.assertIsNotNone(field)
        self.assertEqual(field.default, "both")

    def test_mfa_policy_field_exists_and_defaults_optional(self):
        meta = frappe.get_meta("HD Settings")
        field = meta.get_field("mfa_policy")
        self.assertIsNotNone(field)
        self.assertEqual(field.default, "optional")

    def test_on_update_invalidates_login_settings_cache(self):
        """Saving HD Settings clears the hd_login_settings_cache key.

        We avoid a full .save() because HD Settings has cross-cutting mandatory
        fields (default_ticket_status, ticket_reopen_status) that aren't always
        populated on a freshly bootstrapped test site. Instead we invoke the
        document's on_update handler directly — that's the contract under test.
        """
        frappe.cache().set_value("hd_login_settings_cache", {"sentinel": True})
        self.assertEqual(
            frappe.cache().get_value("hd_login_settings_cache"),
            {"sentinel": True},
        )
        doc = frappe.get_doc("HD Settings")
        doc.run_method("on_update")
        self.assertIsNone(frappe.cache().get_value("hd_login_settings_cache"))
