"""Location helpers — county / sub-county lookups and per-account remembering.

Story 354: County + Sub-County picker on ticket creation with auto-remember.
"""

import frappe
from frappe import _


@frappe.whitelist(allow_guest=True)
def get_counties() -> list[str]:
    """Return a sorted list of distinct county names from HD Facility Mapping."""
    rows = frappe.db.get_all(
        "HD Facility Mapping",
        fields=["county"],
        distinct=True,
        order_by="county asc",
    )
    return sorted({r.county for r in rows if r.county})


@frappe.whitelist(allow_guest=True)
def get_sub_counties(county: str) -> list[str]:
    """Return a sorted list of distinct sub-county names for the given county."""
    if not county:
        return []
    rows = frappe.db.get_all(
        "HD Facility Mapping",
        filters={"county": county},
        fields=["sub_county"],
        distinct=True,
        order_by="sub_county asc",
    )
    return sorted({r.sub_county for r in rows if r.sub_county})


@frappe.whitelist()
def get_contact_location() -> dict:
    """Return the saved county + sub_county for the current session's HD Customer.

    Looks up the HD Customer linked to the current user's Contact record.
    Returns ``{"county": "...", "sub_county": "..."}`` or an empty dict.
    """
    user = frappe.session.user
    if not user or user == "Guest":
        return {}

    # Find contact by email
    contact_name = frappe.db.get_value("Contact", {"email_id": user})
    if not contact_name:
        return {}

    # Get customer linked to this contact
    from helpdesk.utils import get_customer

    customers = get_customer(contact_name)
    if not customers:
        return {}

    customer_name = customers[0]
    customer = frappe.db.get_value(
        "HD Customer",
        customer_name,
        ["county", "sub_county"],
        as_dict=True,
    )
    if not customer:
        return {}

    return {
        "county": customer.county or "",
        "sub_county": customer.sub_county or "",
    }
