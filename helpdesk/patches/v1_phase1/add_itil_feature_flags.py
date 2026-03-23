"""
Migration patch: Add ITIL feature flag defaults to HD Settings.

Ensures that on existing installations the new fields introduced in Story 1.1
(itil_mode_enabled, chat_enabled, csat_enabled, automation_enabled) carry their
correct default values of 0 (disabled).  Fresh installs already receive the
defaults from the DocType JSON, so the patch is safe to run multiple times.
"""

import frappe


def execute():
    """Set default values for ITIL / feature-flag fields on HD Settings."""

    fields_with_defaults = {
        "itil_mode_enabled": 0,
        "chat_enabled": 0,
        "csat_enabled": 0,
        "automation_enabled": 0,
    }

    settings = frappe.get_single("HD Settings")

    changed = False
    for fieldname, default_value in fields_with_defaults.items():
        current = getattr(settings, fieldname, None)
        # Only update when the column is genuinely NULL (not yet persisted)
        if current is None:
            frappe.db.set_value(
                "HD Settings", "HD Settings", fieldname, default_value
            )
            changed = True

    if changed:
        frappe.db.commit()
