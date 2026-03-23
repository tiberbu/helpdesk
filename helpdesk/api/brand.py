# Copyright (c) 2026, Frappe Technologies Pvt. Ltd. and contributors
# For license information, please see license.txt

"""Brand API endpoints for portal theming and brand config.

Whitelisted methods:
    get_brand_config  — Returns branding config for the given portal domain.
                        Called by the portal frontend on load to apply theming.
    get_brands        — Returns list of active brands (agent-side, for filters).
"""

import frappe
from frappe import _


@frappe.whitelist(allow_guest=True)
def get_brand_config(portal_domain: str = "") -> dict:
    """Return brand configuration for the customer portal based on domain.

    Called by the portal frontend on page load.  When a match is found the
    portal applies brand-specific logo, primary_color, and filters KB articles
    by brand.

    Parameters
    ----------
    portal_domain : str
        The hostname of the portal (e.g. ``support.acme.com``).  When empty
        or no brand matches, returns ``None`` so the portal uses defaults.

    Returns
    -------
    dict | None
        ``{name, brand_name, logo, primary_color, portal_domain}``
        or ``None`` when no brand matches the given domain.
    """
    if not portal_domain:
        return None

    # HD Brand DocType may not exist yet on fresh installs
    if not frappe.db.exists("DocType", "HD Brand"):
        return None

    brand = frappe.db.get_value(
        "HD Brand",
        {"portal_domain": portal_domain, "is_active": 1},
        ["name", "brand_name", "logo", "primary_color", "portal_domain"],
        as_dict=True,
    )

    if not brand:
        return None

    return {
        "name": brand.name,
        "brand_name": brand.brand_name,
        "logo": brand.logo,
        "primary_color": brand.primary_color or "#4F46E5",
        "portal_domain": brand.portal_domain,
    }


@frappe.whitelist()
def get_brands() -> list:
    """Return list of active HD Brand records for agent-side filtering.

    Returns
    -------
    list[dict]
        Each dict has ``name`` and ``brand_name`` for use in filter dropdowns.
    """
    if not frappe.db.exists("DocType", "HD Brand"):
        return []

    return frappe.db.get_all(
        "HD Brand",
        filters={"is_active": 1},
        fields=["name", "brand_name"],
        order_by="brand_name asc",
    )
