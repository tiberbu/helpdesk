# Copyright (c) 2026, Frappe Technologies Pvt. Ltd. and contributors
# For license information, please see license.txt

"""Redesigned /update-password page (flag-gated, same pattern as /login).

When ``HD Settings.new_login_page_enabled`` is on, helpdesk claims
/update-password and renders a brand-resolved reset page that matches the
redesigned sign-in surface. When off, we delegate to the framework default
template so behavior is byte-for-byte unchanged.

The actual password-set request still goes to
``frappe.core.doctype.user.user.update_password`` — this module only owns
the page chrome and the redesigned form.
"""

import secrets

import frappe

from helpdesk.www.login import (
    _user_can_preview,
    get_login_settings,
    resolve_brand,
)

no_cache = True


def get_context(context):
    settings = get_login_settings()

    if not settings["new_login_page_enabled"]:
        from frappe.www import update_password as _frappe_update_password

        _frappe_update_password.get_context(context)
        context["template"] = "frappe/www/update-password.html"
        return context

    return _build_reset_context(context)


def _build_reset_context(context):
    """Mirror _build_redesign_context but for the reset page.

    Reuses the same brand / i18n / CSP scaffolding as /login so the visual
    surface stays consistent across the auth journey.
    """
    from helpdesk.www.login_preview import (
        _build_csp,
        _build_i18n_map,
        _is_rtl,
        _telemetry_context_for,
    )

    host = (frappe.local.request.host or "").split(":")[0].lower()
    brand = resolve_brand(host)

    context.no_header = True
    context.no_cache = True
    context["title"] = (
        frappe._("Reset password") + " · " + (brand.get("brand_name") or "")
    )
    context["brand"] = brand
    context["settings"] = settings_for_template()
    context["csrf_token"] = (
        frappe.local.session.get("csrf_token")
        if getattr(frappe.local, "session", None)
        else ""
    )

    lang = frappe.local.lang or "en"
    context["lang"] = lang
    context["dir"] = "rtl" if _is_rtl(lang) else "ltr"
    context["i18n"] = _build_i18n_map()

    # The reset page reads ?key=<token> and ?password_expired=true. We pass
    # them straight to the template so the embedded form can carry them.
    args = getattr(frappe.local, "form_dict", {}) or {}
    context["reset_key"] = args.get("key") or ""
    context["password_expired"] = bool(args.get("password_expired"))

    nonce = secrets.token_urlsafe(16)
    context["csp_nonce"] = nonce
    context["telemetry"] = _telemetry_context_for(brand)

    if getattr(frappe.local, "response_headers", None) is not None:
        frappe.local.response_headers.set(
            "Content-Security-Policy", _build_csp(nonce)
        )
        frappe.local.response_headers.set("X-Frame-Options", "DENY")
        frappe.local.response_headers.set("X-Content-Type-Options", "nosniff")
        frappe.local.response_headers.set("Referrer-Policy", "no-referrer")
        frappe.local.response_headers.set(
            "Cache-Control", "no-store, no-cache, must-revalidate, private"
        )

    return context


def settings_for_template():
    """Subset of HD Settings exposed to the reset template."""
    return get_login_settings()
