# Copyright (c) 2026, Frappe Technologies Pvt. Ltd. and contributors
# For license information, please see license.txt

"""
Helpdesk Redesigned Login — Preview Route (Sprint 2)

Why a separate route?
---------------------
Frappe's page resolver is single-shot: once it picks an app's www/login.py
+ login.html for /login, the framework's default at
apps/frappe/frappe/www/login.html becomes unreachable. Until we flip the
feature flag at Sprint 4, /login MUST serve the framework default exactly
as today.

Solution: ship the redesigned page at /login_preview. Stakeholders, design
reviewers, and System Managers / HD Admins can hit this URL today to
evaluate the redesign without disturbing /login. Sprint 4 will replace
/login's content with this same template (or claim /login outright).

Authorisation
-------------
Only System Manager and HD Admin can access /login_preview. Anonymous users
get a 404 to avoid leaking the redesigned brand surface before launch.
"""

import secrets
import uuid

import frappe

from helpdesk.www.login import (
    _load_brand,
    _user_can_preview,
    get_login_settings,
    resolve_brand,
)

# Sprint 7 — Telemetry property allow-list.
#
# Per AD-07 / FR-TEL-01, every event login.js emits flows through track() and
# only the keys named here survive. This is the single audit point for PII
# leakage. To add a property: extend this tuple AND update FR-TEL-01 in the
# PRD AND mention it in the Sprint 7 report. Anything else is a code-review
# rejection.
_TELEMETRY_PROPERTY_ALLOW_LIST = (
    "route",
    "mfa_method",
    "failure_category",
    "reduced_motion",
    "viewport_bucket",
    "request_id",
    "brand_slug",  # FR-BR-06; resolved per request.
)

# Sprint 7 — Event-name allow-list.
#
# Every name login.js may emit is enumerated here. Anything outside this set
# is dropped client-side by track(). Mirrors FR-TEL-01.
_TELEMETRY_EVENT_ALLOW_LIST = (
    "login_page_view",
    "login_attempt",
    "login_success",
    "login_failed",
    "mfa_step_shown",
    "mfa_success",
    "mfa_failed",
    "mfa_resend_requested",
    "forgot_password_clicked",
    "reset_link_requested",
    "lockout_triggered",
)

# Sprint 6 — Client-side strings.
#
# Every string the JS module renders into the DOM must come from this map so
# Frappe's translation layer (Crowdin-fed) can localise it. Adding a new visible
# string means: (1) wrap server-rendered text in __() in login_preview.html;
# (2) for client-rendered text, add a key here AND reference it from login.js
# via window.__hdLoginI18n. Never inline a string in JS — a lint rule in
# Sprint 7 will start enforcing this.
_CLIENT_I18N_KEYS = (
    "show_password",
    "hide_password",
    "https_required",
    "network_error",
    "bad_credentials",
    "bad_otp",
    "locked_out",
    "locked_out_countdown",  # Has {seconds} placeholder.
    "submitting",
    "reset_submitting",
    "reset_success",
    "post_reset_banner",
    "passwords_dont_match",
    "resend_in",  # Has {seconds} placeholder.
    "resend_code",
    "view_announcement_sign_in",
    "view_announcement_mfa",
    "view_announcement_forgot",
    "view_announcement_reset_success",
    "view_announcement_locked_out",
    "view_announcement_new_password",
)

_CLIENT_I18N_SOURCE = {
    "show_password": "Show password",
    "hide_password": "Hide password",
    "https_required": "This page must be served over HTTPS to sign in.",
    "network_error": (
        "Couldn't reach the server. Check your connection and try again."
    ),
    "bad_credentials": "Email or password is incorrect.",
    "bad_otp": "That code didn't work. Try again.",
    "locked_out": (
        "Your account is temporarily locked. Try again later or reset your"
        " password."
    ),
    "locked_out_countdown": (
        "Too many attempts. Try again in {seconds} seconds, or reset your"
        " password."
    ),
    "submitting": "Signing in…",
    "reset_submitting": "Sending…",
    "reset_success": (
        "If an account exists for this address, we've sent a reset link."
        " Check your inbox."
    ),
    "post_reset_banner": "Password updated. Please sign in.",
    "passwords_dont_match": "Passwords don't match.",
    "resend_in": "Resend in {seconds}s",
    "resend_code": "Resend code",
    "view_announcement_sign_in": "Sign in form.",
    "view_announcement_mfa": (
        "One-time code required. Enter the 6-digit code from your"
        " authenticator app."
    ),
    "view_announcement_forgot": "Reset your password.",
    "view_announcement_reset_success": "Reset link sent if the account exists.",
    "view_announcement_locked_out": "Account temporarily locked.",
    "view_announcement_new_password": "Set a new password.",
}


# RTL languages we explicitly mark — Frappe ships some of these as locales and
# Crowdin produces translations for them. The list is conservative; anything
# else falls through to ltr. Adding a language here is enough to flip the
# layout via dir="rtl" in login_preview.html.
_RTL_LANGS = frozenset({"ar", "fa", "he", "ur", "ps", "ckb"})


def _build_i18n_map() -> dict:
    """Return the localised client-string map for the current request lang.

    Each value flows through Frappe's __() so Crowdin-fed translations apply
    when the active locale provides them.
    """
    return {key: frappe._(_CLIENT_I18N_SOURCE[key]) for key in _CLIENT_I18N_KEYS}


def _is_rtl(lang: str) -> bool:
    if not lang:
        return False
    base = lang.split("-")[0].split("_")[0].lower()
    return base in _RTL_LANGS


def _build_csp(nonce: str) -> str:
    """Strict CSP for the redesigned login surface.

    Constraints derived from the architecture doc:
      - default-src 'self' — first-party only.
      - script-src 'self' + nonce so the inline boot block in login_preview.html
        can run without 'unsafe-inline'. (Frappe's bundled posthog.js is loaded
        with src=, no nonce needed there.)
      - style-src 'self' + nonce for the inline brand-token <style> block.
      - img-src 'self' data: — FR-BR-05 + R-16; brand assets live under
        /files/, no third-party loads.
      - connect-src 'self' + the configured PostHog host (if telemetry is
        enabled) so capture() can POST without being blocked.
      - frame-ancestors 'none' — defence in depth against clickjacking.
    """
    posthog_host = frappe.conf.get("posthog_host") or ""
    connect_src = "'self'"
    if posthog_host:
        connect_src += f" {posthog_host}"

    return "; ".join(
        [
            "default-src 'self'",
            f"script-src 'self' 'nonce-{nonce}'",
            f"style-src 'self' 'nonce-{nonce}'",
            "img-src 'self' data:",
            "font-src 'self' data:",
            f"connect-src {connect_src}",
            "frame-ancestors 'none'",
            "base-uri 'self'",
            "form-action 'self'",
        ]
    )


def _viewport_bucket_default() -> str:
    """Server-side default for the viewport_bucket telemetry property.

    The real value is computed client-side after first paint (login.js reads
    window.innerWidth and binds resize). The server seeds 'unknown' so that
    `login_page_view` events fired before resize-binding still validate
    against the allow-list.
    """
    return "unknown"


def _telemetry_context_for(brand: dict) -> dict:
    """Build the dict written into window.__hdTelemetry."""
    posthog_enabled = bool(
        frappe.conf.get("posthog_host") and frappe.conf.get("posthog_project_id")
    )
    try:
        posthog_enabled = posthog_enabled and bool(
            frappe.get_system_settings("enable_telemetry")
        )
    except Exception:
        # System Settings may not be reachable on a fresh test site; treat
        # that as telemetry off rather than crashing the login page.
        posthog_enabled = False

    return {
        "enabled": posthog_enabled,
        "posthog_host": frappe.conf.get("posthog_host") or "",
        "posthog_project_id": frappe.conf.get("posthog_project_id") or "",
        "request_id": uuid.uuid4().hex,
        # The PRD names this as `brand_slug`; we expose the brand record's
        # primary key (brand_name) under that key so dashboards can group
        # without us renaming the column. Empty when on the built-in
        # fallback brand.
        "brand_slug": brand.get("name") or "",
        "viewport_bucket": _viewport_bucket_default(),
        "event_allow_list": list(_TELEMETRY_EVENT_ALLOW_LIST),
        "property_allow_list": list(_TELEMETRY_PROPERTY_ALLOW_LIST),
    }


def get_context(context):
    """Render the admin-only redesigned-login preview.

    Delegates context-building to ``helpdesk.www.login._build_redesign_context``
    so /login_preview and /login (when the feature flag is on) render with
    identical context shape.
    """
    if not _user_can_preview():
        # Quietly hide the route from anonymous users.
        raise frappe.DoesNotExistError

    # Late import — login.py imports symbols from this module at module-load
    # time, so importing back at module-load would form a cycle.
    from helpdesk.www.login import _build_redesign_context

    return _build_redesign_context(context, is_preview=True)
