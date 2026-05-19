# Copyright (c) 2026, Frappe Technologies Pvt. Ltd. and Contributors
# See license.txt
# Sprint 7 — server-side telemetry / CSP plumbing on /login_preview.

import frappe
from frappe.tests.utils import FrappeTestCase

from helpdesk.www.login_preview import (
    _TELEMETRY_EVENT_ALLOW_LIST,
    _TELEMETRY_PROPERTY_ALLOW_LIST,
    _build_csp,
    _build_i18n_map,
    _telemetry_context_for,
)


class TestCSPBuilder(FrappeTestCase):
    """The CSP string is the security boundary for the redesigned login page;
    every directive matters. These tests pin the contract so a future
    refactor doesn't accidentally relax it.
    """

    def test_default_src_is_self_only(self):
        csp = _build_csp("nonce123")
        self.assertIn("default-src 'self'", csp)

    def test_script_src_uses_nonce_not_unsafe_inline(self):
        csp = _build_csp("nonce123")
        self.assertIn("script-src 'self' 'nonce-nonce123'", csp)
        self.assertNotIn("'unsafe-inline'", csp)
        self.assertNotIn("'unsafe-eval'", csp)

    def test_style_src_uses_nonce_not_unsafe_inline(self):
        csp = _build_csp("nonce123")
        self.assertIn("style-src 'self' 'nonce-nonce123'", csp)

    def test_img_src_allows_first_party_and_data_only(self):
        # FR-BR-05 / R-16 — no third-party images, no remote logos.
        csp = _build_csp("n")
        self.assertIn("img-src 'self' data:", csp)
        self.assertNotIn("https:", csp.split("img-src", 1)[1].split(";", 1)[0])

    def test_frame_ancestors_blocks_clickjacking(self):
        csp = _build_csp("n")
        self.assertIn("frame-ancestors 'none'", csp)

    def test_form_action_self_only(self):
        # Login forms must not be exfiltrable to an external origin.
        csp = _build_csp("n")
        self.assertIn("form-action 'self'", csp)

    def test_connect_src_includes_posthog_when_configured(self):
        original = frappe.conf.get("posthog_host")
        try:
            frappe.conf["posthog_host"] = "https://posthog.example"
            csp = _build_csp("n")
            connect = csp.split("connect-src", 1)[1].split(";", 1)[0]
            self.assertIn("https://posthog.example", connect)
        finally:
            if original is None:
                frappe.conf.pop("posthog_host", None)
            else:
                frappe.conf["posthog_host"] = original

    def test_connect_src_falls_back_to_self_only_when_posthog_unconfigured(self):
        original = frappe.conf.get("posthog_host")
        try:
            frappe.conf.pop("posthog_host", None)
            csp = _build_csp("n")
            connect = csp.split("connect-src", 1)[1].split(";", 1)[0].strip()
            # Trim trailing whitespace; should be exactly "'self'".
            self.assertEqual(connect, "'self'")
        finally:
            if original is not None:
                frappe.conf["posthog_host"] = original


class TestTelemetryContext(FrappeTestCase):
    """The window.__hdTelemetry payload is the audit point for client-side
    PII emission. The allow-lists must be exposed verbatim, request_id must
    be unique per call, and brand_slug must trace the resolved record.
    """

    def test_allow_lists_are_exposed_to_the_client(self):
        ctx = _telemetry_context_for({"name": "Tiberbu"})
        self.assertEqual(
            list(ctx["event_allow_list"]),
            list(_TELEMETRY_EVENT_ALLOW_LIST),
        )
        self.assertEqual(
            list(ctx["property_allow_list"]),
            list(_TELEMETRY_PROPERTY_ALLOW_LIST),
        )

    def test_request_id_is_unique_per_call(self):
        a = _telemetry_context_for({"name": "Tiberbu"})
        b = _telemetry_context_for({"name": "Tiberbu"})
        self.assertNotEqual(a["request_id"], b["request_id"])
        self.assertEqual(len(a["request_id"]), 32)  # uuid4 hex

    def test_brand_slug_traces_resolved_record(self):
        ctx = _telemetry_context_for({"name": "DHA"})
        self.assertEqual(ctx["brand_slug"], "DHA")

    def test_brand_slug_empty_for_builtin_fallback(self):
        ctx = _telemetry_context_for({"name": None})
        self.assertEqual(ctx["brand_slug"], "")

    def test_property_allow_list_does_not_leak_known_pii_keys(self):
        # If anyone ever adds 'email' or 'password' to the property allow-list
        # this test rings the alarm. AD-07 says: never.
        for forbidden in ("email", "password", "otp", "tmp_id", "ip", "user_agent"):
            self.assertNotIn(
                forbidden,
                _TELEMETRY_PROPERTY_ALLOW_LIST,
                f"PII key {forbidden!r} must never be on the allow-list",
            )

    def test_telemetry_disabled_when_posthog_unconfigured(self):
        # Sanity: with no posthog_host configured, ctx['enabled'] is False
        # so client-side track() short-circuits and never tries to send.
        original = frappe.conf.get("posthog_host")
        try:
            frappe.conf.pop("posthog_host", None)
            ctx = _telemetry_context_for({"name": "Tiberbu"})
            self.assertFalse(ctx["enabled"])
        finally:
            if original is not None:
                frappe.conf["posthog_host"] = original


class TestI18nMapStability(FrappeTestCase):
    """Sprint 6 wired the i18n map; Sprint 7 doesn't change the contents,
    but the map's keys are part of the JS controller's contract. Pinning
    them here means a stray rename in login_preview.py can't silently break
    a translated string client-side.
    """

    def test_every_view_announcement_key_is_present(self):
        m = _build_i18n_map()
        for view in (
            "sign_in",
            "mfa",
            "forgot",
            "reset_success",
            "locked_out",
            "new_password",
        ):
            self.assertIn(f"view_announcement_{view}", m)

    def test_seconds_placeholders_survive_translation(self):
        m = _build_i18n_map()
        # On a default `lang=en` site the English source is returned
        # verbatim; ensure the placeholder syntax is preserved.
        self.assertIn("{seconds}", m["locked_out_countdown"])
        self.assertIn("{seconds}", m["resend_in"])
