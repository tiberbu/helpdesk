"""
Keeps the ticket-raising agent's saved phone number (User.mobile_no) in sync
with whatever phone number they enter on a new ticket, so it can be reliably
pre-filled next time without ever forcing them to re-enter it. Also enforces
that, when provided, the number is a valid Kenyan mobile number.
"""

import re

import frappe
from frappe import _

# Local: 0 + (7 or 1) + 8 more digits = 10 digits total, e.g. 0712345678
# International: +254 + (7 or 1) + 8 more digits, e.g. +254712345678
_KE_PHONE_RE = re.compile(r"^(0[17]\d{8}|\+254[17]\d{8})$")


def validate_phone_format(doc, method=None):
    """Optional field — only validated if a value was actually provided."""
    raw = (doc.get("custom_phone") or "").strip()
    if not raw:
        return

    # Normalize: strip spaces/dashes so "0712 345 678" and "0712-345-678"
    # are treated the same as "0712345678".
    normalized = re.sub(r"[\s-]", "", raw)

    if not _KE_PHONE_RE.match(normalized):
        frappe.throw(
            _(
                "Phone number must be a valid Kenyan number: either 10 digits "
                "starting with 07 or 01 (e.g. 0712345678), or in international "
                "format starting with +254 (e.g. +254712345678)."
            )
        )

    doc.custom_phone = normalized


def sync_owner_mobile_no(doc, method=None):
    phone = (doc.get("custom_phone") or "").strip()
    if not phone:
        return

    owner = doc.owner
    if not owner or owner in ("Administrator", "Guest"):
        return

    current = frappe.db.get_value("User", owner, "mobile_no")
    if current != phone:
        frappe.db.set_value("User", owner, "mobile_no", phone, update_modified=False)
