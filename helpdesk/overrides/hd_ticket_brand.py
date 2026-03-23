# Copyright (c) 2026, Frappe Technologies Pvt. Ltd. and contributors
# For license information, please see license.txt

"""
Email-to-brand matching for HD Ticket.

Registered as a before_insert doc_event for HD Ticket.  When a ticket is
created via email, the inbound "to" address is matched against all active
HD Brand ``support_email`` values (case-insensitive).  On match the ticket's
``brand``, ``agent_group`` (team), and ``sla`` fields are populated if they
are not already set.

Brand data is cached in Redis for 5 minutes to avoid per-ticket DB queries.
"""

import frappe

_CACHE_KEY = "hd_brand_email_map"
_CACHE_TTL = 300  # seconds


def _get_brand_email_map() -> dict:
    """Return {lower(support_email): brand_doc_dict} from cache or DB."""
    cached = frappe.cache().get_value(_CACHE_KEY)
    if cached is not None:
        return cached

    brands = frappe.db.get_all(
        "HD Brand",
        filters={"is_active": 1, "support_email": ["!=", ""]},
        fields=["name", "support_email", "default_team", "default_sla"],
    )

    email_map = {}
    for b in brands:
        if b.get("support_email"):
            email_map[b["support_email"].lower()] = b

    frappe.cache().set_value(_CACHE_KEY, email_map, expires_in_sec=_CACHE_TTL)
    return email_map


def invalidate_brand_cache(doc=None, method=None):
    """Call this when an HD Brand is created/updated/deleted."""
    frappe.cache().delete_value(_CACHE_KEY)


def assign_brand_from_email(doc, method=None):
    """Before-insert hook — tag ticket with brand based on inbound email.

    Also sets default_team and default_sla from the brand when they are not
    already specified on the ticket.
    """
    # Skip if brand already set
    if doc.brand:
        return

    # HD Brand DocType may not exist yet (fresh install without migration)
    if not frappe.db.exists("DocType", "HD Brand"):
        return

    email_map = _get_brand_email_map()
    if not email_map:
        return

    # Try to match against the email account the ticket was received on.
    # HD Ticket stores the receiving account in `email_account`; the actual
    # inbound address is the email account's email_id.
    inbound_address = None

    if doc.email_account:
        inbound_address = frappe.db.get_value(
            "Email Account", doc.email_account, "email_id"
        )

    if not inbound_address:
        return

    brand = email_map.get(inbound_address.lower())
    if not brand:
        return

    doc.brand = brand["name"]

    if not doc.agent_group and brand.get("default_team"):
        doc.agent_group = brand["default_team"]

    if not doc.sla and brand.get("default_sla"):
        doc.sla = brand["default_sla"]
