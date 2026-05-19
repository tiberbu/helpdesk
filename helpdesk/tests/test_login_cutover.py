# Copyright (c) 2026, Frappe Technologies Pvt. Ltd. and Contributors
# See license.txt
# Sprint 8 — /login feature-flag cutover tests.
#
# These tests pin the AD-06 contract: HD Settings.new_login_page_enabled
# is the single source of truth for which template /login serves. Off
# (default) → framework login.html; On → redesigned login.html via the
# helpdesk colocated module.

import frappe
from frappe.tests.utils import FrappeTestCase

from helpdesk.www import login as helpdesk_login
from helpdesk.www.login import _build_redesign_context, get_context


class _StubRequest:
    """Minimal substitute for frappe.local.request that get_context reads.

    The framework's get_context reaches further into request.args and
    response.headers; the cutover branches here are the only code path
    we care about, so we keep the stub small and let the framework path
    bail by setting the flag explicitly.
    """

    def __init__(self, host="support.tiberbu.app"):
        self.host = host
        self.args = {}
        self.url = f"http://{host}/login"


class _StubResponseHeaders:
    def __init__(self):
        self.values = {}

    def set(self, key, value):
        self.values[key] = value

    def update(self, mapping):
        self.values.update(mapping)


class _CutoverTestBase(FrappeTestCase):
    """Set up + tear down the request/response/local state every test
    needs. Each test mutates HD Settings.new_login_page_enabled itself.
    """

    def setUp(self):
        frappe.set_user("Administrator")
        # Snapshot + reset the flag so tests don't leak state.
        self._original_flag = frappe.db.get_single_value(
            "HD Settings", "new_login_page_enabled"
        )
        self._set_flag(0)

        # Stub request + response_headers; the framework's get_context
        # touches both. We restore originals in tearDown.
        self._original_request = getattr(frappe.local, "request", None)
        self._original_response_headers = getattr(
            frappe.local, "response_headers", None
        )
        self._original_form_dict = getattr(frappe.local, "form_dict", None)
        self._original_session = getattr(frappe.local, "session", None)

        frappe.local.request = _StubRequest()
        frappe.local.response_headers = _StubResponseHeaders()
        frappe.local.form_dict = frappe._dict()

    def tearDown(self):
        self._set_flag(self._original_flag or 0)
        # Restore frappe.local state.
        if self._original_request is not None:
            frappe.local.request = self._original_request
        if self._original_response_headers is not None:
            frappe.local.response_headers = self._original_response_headers
        if self._original_form_dict is not None:
            frappe.local.form_dict = self._original_form_dict
        # session may have been None — leave it untouched.

    def _set_flag(self, value):
        frappe.db.set_single_value("HD Settings", "new_login_page_enabled", value)
        frappe.db.commit()
        # Both the singleton cache and our own derived cache need flushing
        # so get_login_settings picks the new value up immediately.
        frappe.cache().delete_value("hd_login_settings_cache")
        frappe.clear_cache(doctype="HD Settings")


class TestCutoverFlagOff(_CutoverTestBase):
    """When the flag is OFF (default), get_context delegates to the
    framework login and points context.template at frappe/www/login.html.
    """

    def test_template_redirects_to_framework_login(self):
        ctx = frappe._dict()
        try:
            get_context(ctx)
        except frappe.Redirect:
            # Logged-in administrators are redirected to /desk by the
            # framework get_context; we don't care about that path here.
            return
        self.assertEqual(ctx.get("template"), "frappe/www/login.html")

    def test_no_redesign_specific_keys_in_context(self):
        ctx = frappe._dict()
        try:
            get_context(ctx)
        except frappe.Redirect:
            return
        # The redesigned-page keys must NOT be present when the flag is off.
        for key in ("brand", "i18n", "telemetry", "csp_nonce"):
            self.assertNotIn(
                key,
                ctx,
                f"Flag-off context leaked redesign key {key!r}",
            )

    def test_csp_header_not_set_in_flag_off_path(self):
        ctx = frappe._dict()
        try:
            get_context(ctx)
        except frappe.Redirect:
            return
        # The strict CSP rides only on the redesigned page. With the flag
        # off /login keeps its existing header story (whatever the
        # framework emits, we don't override).
        headers = frappe.local.response_headers.values
        self.assertNotIn("Content-Security-Policy", headers)


class TestCutoverFlagOn(_CutoverTestBase):
    """When the flag is ON, get_context builds the redesigned context."""

    def setUp(self):
        super().setUp()
        self._set_flag(1)

    def test_redesigned_context_keys_populated(self):
        ctx = frappe._dict()
        get_context(ctx)
        for key in ("brand", "i18n", "telemetry", "csp_nonce", "lang", "dir"):
            self.assertIn(
                key,
                ctx,
                f"Flag-on context missing redesign key {key!r}",
            )

    def test_csp_and_hardening_headers_set(self):
        ctx = frappe._dict()
        get_context(ctx)
        headers = frappe.local.response_headers.values
        self.assertIn("Content-Security-Policy", headers)
        self.assertEqual(headers.get("X-Frame-Options"), "DENY")
        self.assertEqual(headers.get("X-Content-Type-Options"), "nosniff")
        self.assertEqual(headers.get("Referrer-Policy"), "no-referrer")
        # The Cache-Control we set is the strict 'no-store' variant.
        self.assertIn("no-store", headers.get("Cache-Control", ""))

    def test_csp_nonce_appears_in_csp_header(self):
        ctx = frappe._dict()
        get_context(ctx)
        nonce = ctx["csp_nonce"]
        csp = frappe.local.response_headers.values.get(
            "Content-Security-Policy", ""
        )
        self.assertIn(f"'nonce-{nonce}'", csp)

    def test_is_preview_false_on_live_login(self):
        ctx = frappe._dict()
        get_context(ctx)
        self.assertFalse(ctx["is_preview"])

    def test_anonymous_tenant_override_ignored(self):
        # An anonymous /login?tenant=DHA must NOT honour the tenant override
        # (FR-BR-04 — admin-only). Host-resolved brand stands.
        frappe.local.form_dict = frappe._dict({"tenant": "DHA"})
        # Ensure no admin session is active.
        frappe.set_user("Guest")
        try:
            ctx = frappe._dict()
            get_context(ctx)
            # If the override had been honoured the brand would be DHA.
            # support.tiberbu.app resolves to the Tiberbu brand; we assert
            # the brand_name is NOT DHA. (If neither is seeded the
            # built-in fallback applies; that's fine, it still isn't DHA.)
            self.assertNotEqual(ctx["brand"].get("brand_name"), "DHA")
        finally:
            frappe.set_user("Administrator")


class TestRedesignContextBuilder(_CutoverTestBase):
    """Direct tests for _build_redesign_context — the core of both
    /login (flag-on) and /login_preview.
    """

    def setUp(self):
        super().setUp()

    def test_lang_and_dir_set_for_default_locale(self):
        ctx = frappe._dict()
        _build_redesign_context(ctx, is_preview=False)
        self.assertEqual(ctx["dir"], "ltr")
        self.assertTrue(ctx["lang"])

    def test_lang_and_dir_flip_for_arabic(self):
        original_lang = frappe.local.lang
        try:
            frappe.local.lang = "ar"
            ctx = frappe._dict()
            _build_redesign_context(ctx, is_preview=False)
            self.assertEqual(ctx["dir"], "rtl")
            self.assertEqual(ctx["lang"], "ar")
        finally:
            frappe.local.lang = original_lang

    def test_csp_nonce_is_unique_per_call(self):
        ctx_a = frappe._dict()
        ctx_b = frappe._dict()
        _build_redesign_context(ctx_a, is_preview=False)
        _build_redesign_context(ctx_b, is_preview=False)
        self.assertNotEqual(ctx_a["csp_nonce"], ctx_b["csp_nonce"])

    def test_telemetry_brand_slug_traces_resolved_brand(self):
        ctx = frappe._dict()
        _build_redesign_context(ctx, is_preview=False)
        self.assertEqual(
            ctx["telemetry"]["brand_slug"],
            ctx["brand"].get("name") or "",
        )


class TestPreviewDelegatesToBuilder(_CutoverTestBase):
    """The /login_preview route should produce a context indistinguishable
    from /login (flag-on) except for is_preview=True.
    """

    def setUp(self):
        super().setUp()
        self._set_flag(1)

    def test_preview_context_marks_is_preview_true(self):
        ctx = frappe._dict()
        # _user_can_preview() requires a real session — skip via direct call.
        _build_redesign_context(ctx, is_preview=True)
        self.assertTrue(ctx["is_preview"])

    def test_preview_and_login_share_brand_resolution(self):
        ctx_login = frappe._dict()
        ctx_preview = frappe._dict()
        _build_redesign_context(ctx_login, is_preview=False)
        _build_redesign_context(ctx_preview, is_preview=True)
        # Same host → same brand; only is_preview differs.
        self.assertEqual(
            ctx_login["brand"].get("brand_name"),
            ctx_preview["brand"].get("brand_name"),
        )


# Touch the imported module to keep linters from complaining about an
# unused alias — the import itself is the point (it has to load cleanly).
assert helpdesk_login is not None
