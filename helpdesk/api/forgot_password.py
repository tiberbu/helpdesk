# Copyright (c) 2026, Frappe Technologies Pvt. Ltd. and contributors
# For license information, please see license.txt

"""Branded forgot-password endpoint.

Layered on top of `frappe.core.doctype.user.user.reset_password`. We do the
same work — generate a one-shot reset token, store its hash on the User, send
the link — but with a brand-resolved HTML email template (and an SMS fallback
if the user has a mobile number and SMS Settings is configured) so the message
matches the redesigned login surface instead of the bare framework default.

Privacy-preserving: returns the same generic message regardless of whether
the email exists / the user is enabled / mail or SMS delivery actually
succeeded (CWE-204). Rate-limited to the same per-hour budget as the
framework's reset endpoint.
"""

import frappe
from frappe import _
from frappe.rate_limiter import rate_limit
from frappe.utils import get_url

from helpdesk.www.login import resolve_brand

PASSWORD_RESET_EMAIL_TEMPLATE = "templates/emails/hd_password_reset.html"
PASSWORD_RESET_EMAIL_SUBJECT = "Reset your password"


def _get_password_reset_limit() -> int:
    return (
        frappe.db.get_single_value(
            "System Settings", "password_reset_limit"
        )
        or 3
    )


@frappe.whitelist(allow_guest=True, methods=["POST"])
@rate_limit(limit=_get_password_reset_limit, seconds=60 * 60)
def request_reset(user: str) -> None:
    """Request a password-reset link for ``user`` (email).

    Always returns a generic success message — never confirms or denies
    whether the address is registered. The actual email/SMS delivery happens
    in the background and is fault-tolerant: failures are logged, never
    surfaced.
    """
    try:
        _send_reset_for(user)
    except frappe.DoesNotExistError:
        frappe.clear_messages()
    except frappe.OutgoingEmailError:
        frappe.clear_messages()
        frappe.log_error(
            title="HD password-reset email could not be sent",
            message=frappe.get_traceback(),
        )
    except Exception:
        frappe.clear_messages()
        frappe.log_error(
            title="HD password-reset failed unexpectedly",
            message=frappe.get_traceback(),
        )

    frappe.msgprint(
        msg=_(
            "If this email is registered with us, we have sent password "
            "reset instructions to it. Please check your inbox."
        ),
        title=_("Password Reset"),
    )


def _send_reset_for(user: str) -> None:
    user_doc = frappe.get_doc("User", user)
    if user_doc.name == "Administrator" or not user_doc.enabled:
        return

    user_doc.validate_reset_password()

    # Reuse the framework's token-generation path so the existing
    # /update-password key-verification flow keeps working unchanged.
    link = user_doc._reset_password(send_email=False)

    brand = _safe_brand()
    expiry_minutes = _expiry_minutes()

    _send_branded_email(user_doc, link, brand, expiry_minutes)
    _maybe_send_sms(user_doc, link, brand, expiry_minutes)


def _safe_brand() -> dict:
    """Resolve the active brand by host header, falling back gracefully."""
    try:
        host = (frappe.local.request.host or "").split(":")[0].lower()
    except Exception:
        host = ""
    return resolve_brand(host)


def _expiry_minutes() -> int:
    seconds = (
        frappe.db.get_single_value(
            "System Settings", "reset_password_link_expiry_duration"
        )
        or 1200
    )
    return max(1, int(seconds) // 60)


def _send_branded_email(user_doc, link: str, brand: dict, expiry_minutes: int) -> None:
    args = {
        "first_name": user_doc.first_name or user_doc.last_name or _("there"),
        "user_email": user_doc.email or user_doc.name,
        "link": link,
        "expiry_minutes": expiry_minutes,
        "brand": brand,
        "site_url": get_url(),
        "support_email": brand.get("support_email"),
    }

    frappe.sendmail(
        recipients=[user_doc.email or user_doc.name],
        subject=_(PASSWORD_RESET_EMAIL_SUBJECT)
        + " · "
        + (brand.get("brand_name") or _("Helpdesk")),
        template=None,
        message=frappe.render_template(PASSWORD_RESET_EMAIL_TEMPLATE, args),
        now=True,
        retry=3,
        header=[_("Reset your password"), "blue"],
    )


def _maybe_send_sms(user_doc, link: str, brand: dict, expiry_minutes: int) -> None:
    """Best-effort SMS fallback. No-op unless:

    * the user has a mobile number;
    * SMS Settings has a sms_gateway_url configured.

    Failures are logged but never raised — SMS is a courtesy, not a blocker.
    """
    mobile = (user_doc.mobile_no or "").strip()
    if not mobile:
        return

    gateway = frappe.db.get_single_value("SMS Settings", "sms_gateway_url")
    if not gateway:
        return

    brand_name = brand.get("brand_name") or "Helpdesk"
    body = _(
        "{brand_name} password reset: {link} (valid for {minutes} min). "
        "Ignore if not requested."
    ).format(brand_name=brand_name, link=link, minutes=expiry_minutes)

    try:
        from frappe.core.doctype.sms_settings.sms_settings import send_sms

        send_sms([mobile], body, success_msg=False)
    except Exception:
        frappe.log_error(
            title="HD password-reset SMS failed",
            message=frappe.get_traceback(),
        )
