"""
Migration patch: Create default HD Ticket Category records.

Seeds the HD Ticket Category DocType with a minimal set of top-level
categories and sub-categories for out-of-the-box usability.

Safe to run multiple times (idempotent — skips records that already exist).
"""

import frappe

DEFAULT_CATEGORIES = [
    # (name, parent_category)
    ("Hardware", None),
    ("Software", None),
    ("Network", None),
    ("General", None),
    # Hardware sub-categories
    ("Laptop / Desktop", "Hardware"),
    ("Printer / Scanner", "Hardware"),
    ("Mobile Device", "Hardware"),
    # Software sub-categories
    ("Operating System", "Software"),
    ("Application", "Software"),
    ("Security / Antivirus", "Software"),
    # Network sub-categories
    ("VPN", "Network"),
    ("Wi-Fi", "Network"),
    ("Email", "Network"),
]


def execute():
    for name, parent_category in DEFAULT_CATEGORIES:
        if not frappe.db.exists("HD Ticket Category", name):
            frappe.get_doc(
                {
                    "doctype": "HD Ticket Category",
                    "name": name,
                    "parent_category": parent_category,
                    "is_active": 1,
                }
            ).insert(ignore_permissions=True)
    frappe.db.commit()
