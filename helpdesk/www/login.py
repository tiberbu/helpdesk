# Copyright (c) 2026, Frappe Technologies Pvt. Ltd. and contributors
# For license information, please see license.txt

"""
Helpdesk login surface — resolver, cached settings reader, and Sprint 8 cutover.

This module is BOTH:

1. The library that hosts the host-pattern brand resolver and the login-settings
   reader (consumed by login_preview.py and now login.html itself).

2. The page module behind /login as of Sprint 8. ``get_context()`` reads
   ``HD Settings.new_login_page_enabled``: when off (default), it falls through
   to the framework login by setting ``context.template`` to
   ``frappe/www/login.html`` and reusing the framework's get_context. When on,
   it builds the redesigned-page context (brand, i18n, telemetry, CSP) and
   selects the redesigned template body. Toggling the singleton flag is the
   one-step rollback path called for in AD-06.

References
----------
* PRD: ``_bmad-output/planning-artifacts/PRD.md`` (FR-AD-01, AD-06)
* Architecture: ``_bmad-output/planning-artifacts/architecture.md`` (AD-06, AD-09)
* Sprint 8 plan: ``_bmad-output/planning-artifacts/sprint-8/...``
"""

import fnmatch
import secrets
import uuid
from typing import Iterable

import frappe

# Cache namespaces -----------------------------------------------------------

# Per-host resolver result. Flushed by HDBrand.on_update / on_trash.
_HOST_CACHE_NAMESPACE = "hd_brand_by_host"
# Cached login-toggle reader. Flushed by HDSettings.on_update.
_SETTINGS_CACHE_KEY = "hd_login_settings_cache"

# Page render note ----------------------------------------------------------

# When the new page renders (Sprint 2+), Frappe-served HTML for /login should
# not be cached by intermediaries.
no_cache = True


# ---------------------------------------------------------------------------
# Settings reader
# ---------------------------------------------------------------------------


def get_login_settings() -> dict:
    """Cached read of the three Sprint 1 HD Settings fields.

    Returns a small dict with stable keys regardless of whether the singleton
    has been migrated yet (defensive defaults).
    """
    cached = frappe.cache().get_value(_SETTINGS_CACHE_KEY)
    if cached is not None:
        return cached

    settings = frappe.get_cached_doc("HD Settings")
    out = {
        "new_login_page_enabled": bool(
            settings.get("new_login_page_enabled") or 0
        ),
        "login_hero_audience": settings.get("login_hero_audience") or "both",
        "mfa_policy": settings.get("mfa_policy") or "optional",
    }
    frappe.cache().set_value(_SETTINGS_CACHE_KEY, out, expires_in_sec=60)
    return out


# ---------------------------------------------------------------------------
# Brand resolver
# ---------------------------------------------------------------------------


def resolve_brand(host: str) -> dict:
    """Return a brand dict for the given Host header.

    Resolution order:
      1. Cache hit on hd_brand_by_host:<host>.
      2. Exact match against any active HD Brand.host_patterns line.
      3. Most-specific wildcard match in host_patterns (longest fixed-suffix wins).
      4. Exact match against HD Brand.portal_domain (backward compat with the
         Phase 1 routing assumption — see G0.3 reconciliation 2026-05-14).
      5. The HD Brand with is_default=1 and is_active=1.
      6. Built-in fallback (helpdesk default; primary #5551FF).
    """
    host = (host or "").lower().strip()
    cache_key = f"{_HOST_CACHE_NAMESPACE}:{host}"
    cached = frappe.cache().get_value(cache_key)
    if cached is not None:
        return cached

    brand = _resolve_uncached(host)
    frappe.cache().set_value(cache_key, brand, expires_in_sec=3600)
    return brand


def invalidate_login_brand_cache() -> None:
    """Flush every per-host resolver cache entry.

    Wired into HDBrand.on_update / on_trash via hooks.py. The Phase 1
    ``hd_brand_email_map`` cache continues to be invalidated separately by
    the existing ``invalidate_brand_cache`` callback in
    ``helpdesk.overrides.hd_ticket_brand``.
    """
    frappe.cache().delete_keys(f"{_HOST_CACHE_NAMESPACE}:*")


def _resolve_uncached(host: str) -> dict:
    if not frappe.db.exists("DocType", "HD Brand"):
        return _builtin_fallback()

    enabled = frappe.get_all(
        "HD Brand",
        filters={"is_active": 1},
        fields=[
            "name",
            "is_default",
            "host_patterns",
            "portal_domain",
        ],
    )

    # 1. Exact match on host_patterns.
    for b in enabled:
        for line in _split_patterns(b["host_patterns"]):
            if "*" not in line and line == host:
                return _load_brand(b["name"])

    # 2. Wildcard on host_patterns — longest fixed-suffix wins.
    best_name = None
    best_suffix_len = -1
    for b in enabled:
        for line in _split_patterns(b["host_patterns"]):
            if "*" in line and fnmatch.fnmatch(host, line):
                suffix_len = len(line.replace("*", ""))
                if suffix_len > best_suffix_len:
                    best_name = b["name"]
                    best_suffix_len = suffix_len
    if best_name is not None:
        return _load_brand(best_name)

    # 3. Exact match on legacy portal_domain (Phase 1 backward compat).
    for b in enabled:
        portal = (b.get("portal_domain") or "").lower().strip()
        if portal and portal == host:
            return _load_brand(b["name"])

    # 4. Default brand.
    for b in enabled:
        if b["is_default"]:
            return _load_brand(b["name"])

    # 5. Built-in fallback.
    return _builtin_fallback()


def _split_patterns(blob: str) -> Iterable[str]:
    return [
        ln.strip().lower()
        for ln in (blob or "").splitlines()
        if ln.strip()
    ]


def _load_brand(name: str) -> dict:
    doc = frappe.get_doc("HD Brand", name)
    return {
        "name": doc.name,
        "brand_name": doc.brand_name,
        "is_default": bool(doc.get("is_default")),
        "logo": doc.get("logo"),
        "wordmark": doc.get("wordmark"),
        "favicon": doc.get("favicon"),
        "bg_image": doc.get("bg_image"),
        "primary_color": doc.get("primary_color") or "#5551FF",
        "accent_color": doc.get("accent_color") or "#7B78FF",
        "bg_tint_color": doc.get("bg_tint_color") or "#F5F5FF",
        "headline": doc.get("headline") or "Welcome back",
        "supporting_copy": doc.get("supporting_copy") or "",
        "support_email": doc.get("support_email"),
        "perks": [
            {"icon": p.get("icon"), "text": p.get("text")}
            for p in (doc.get("perks") or [])
        ],
        "trust_stats": [
            {"value": s.get("value"), "label": s.get("label")}
            for s in (doc.get("trust_stats") or [])
        ],
    }


def _builtin_fallback() -> dict:
    return {
        "name": None,
        "brand_name": "Helpdesk Platform",
        "is_default": False,
        "logo": "/assets/helpdesk/desk/desk.png",
        "wordmark": None,
        "favicon": "/assets/helpdesk/desk/favicon.svg",
        "bg_image": None,
        "primary_color": "#5551FF",
        "accent_color": "#7B78FF",
        "bg_tint_color": "#F5F5FF",
        "headline": "Welcome back",
        "supporting_copy": "Sign in to Helpdesk",
        "support_email": None,
        "perks": [],
        "trust_stats": [],
    }


# ---------------------------------------------------------------------------
# Helpers — used by login_preview.py
# ---------------------------------------------------------------------------


def _user_can_preview() -> bool:
    """True when the current session user is a System Manager or HD Admin."""
    if not getattr(frappe.local, "session", None):
        return False
    user = frappe.local.session.user
    if not user or user == "Guest":
        return False
    roles = set(frappe.get_roles(user))
    return bool(roles & {"System Manager", "HD Admin"})


# ---------------------------------------------------------------------------
# Sprint 8 cutover — /login flag-gated rendering
# ---------------------------------------------------------------------------
#
# The colocated www/login.html template at apps/helpdesk/helpdesk/www/login.html
# claims /login because helpdesk is iterated before frappe in the app resolver
# (apps reversed). When HD Settings.new_login_page_enabled is OFF (default),
# get_context() points context.template at "frappe/www/login.html" so the
# framework's original page renders — byte-for-byte equivalent to the legacy
# behaviour. When ON, it builds the redesigned-page context and points
# context.template at our shared body include. Flipping the singleton flag
# rolls back instantly with no deploy (AD-06).


def get_context(context):
    """Render /login. Branches on HD Settings.new_login_page_enabled (AD-06)."""
    settings = get_login_settings()

    if not settings["new_login_page_enabled"]:
        # Flag off → framework default. Delegate to frappe.www.login.get_context
        # to populate logo/app_name/oauth providers/etc., then redirect Jinja
        # to the framework template. Logged-in users may be redirected to
        # /helpdesk by the framework get_context — that's the existing behavior
        # and we want to preserve it exactly.
        from frappe.www import login as _frappe_login

        _frappe_login.get_context(context)
        # Bypass the SSI 'web.html' wrap — the framework template already
        # extends templates/web.html, but our colocated template path won.
        # By pointing context.template at the framework login template, the
        # template_page renderer renders THAT file directly.
        context["template"] = "frappe/www/login.html"
        return context

    # Flag on → redesigned page. Same context computation as login_preview.py,
    # minus the admin gate.
    return _build_redesign_context(context, is_preview=False)


def _build_redesign_context(context, *, is_preview: bool):
    """Populate ``context`` for the redesigned login page.

    Shared between /login (Sprint 8 cutover) and /login_preview (admin-only).
    Mirrors login_preview.get_context's body — kept here so the canonical
    context shape lives next to the resolver. login_preview.py delegates here.
    """
    # Late imports keep this module loadable in the legacy-flag path even if
    # the preview helpers haven't been touched yet.
    from helpdesk.www.login_preview import (
        _build_csp,
        _build_i18n_map,
        _is_rtl,
        _telemetry_context_for,
    )

    host = (frappe.local.request.host or "").split(":")[0].lower()
    brand = resolve_brand(host)

    tenant_override = frappe.local.form_dict.get("tenant")
    if tenant_override and (is_preview or _user_can_preview()):
        # Tenant override is admin-only by FR-BR-04. On /login (non-preview)
        # we honour it iff the requester is already a System Manager / HD
        # Admin; for everyone else the host-resolved brand stands.
        try:
            brand = _load_brand(tenant_override)
        except frappe.DoesNotExistError:
            pass

    context.no_header = True
    context.no_cache = True
    context["title"] = (
        frappe._("Sign in") + " · " + (brand.get("brand_name") or "")
    )
    context["brand"] = brand
    context["settings"] = get_login_settings()
    context["is_preview"] = is_preview
    context["csrf_token"] = (
        frappe.local.session.get("csrf_token")
        if getattr(frappe.local, "session", None)
        else ""
    )

    lang = frappe.local.lang or "en"
    context["lang"] = lang
    context["dir"] = "rtl" if _is_rtl(lang) else "ltr"
    context["i18n"] = _build_i18n_map()

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
