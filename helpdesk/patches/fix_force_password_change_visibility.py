"""
The original add_user_force_password_change patch created this field as
hidden + read_only, meaning admins had no visible way to control it from
the User form. This corrects those properties on any site where the field
already exists (idempotent — safe to run whether or not it's already been
manually fixed).
"""

import frappe


def execute():
    if not frappe.db.exists("Custom Field", "User-force_password_change"):
        return

    frappe.db.set_value(
        "Custom Field",
        "User-force_password_change",
        {
            "hidden": 0,
            "read_only": 0,
            "default": "1",
        },
    )
    frappe.clear_cache(doctype="User")
