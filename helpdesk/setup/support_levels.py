"""
Shared HD Support Level seed module.

Creates the 4 default support level records used across the Kenya
administrative hierarchy.  Consumed by both the after_install hook and
migration patches.

Safe to call multiple times (idempotent).
"""

import frappe

# Ordered list of (level_name, level_order, display_name, color)
_SUPPORT_LEVELS = [
    ("L0 - Sub-County", 0, "Sub-County Support", "#4CAF50"),
    ("L1 - County", 1, "County Support", "#2196F3"),
    ("L2 - National", 2, "National Support", "#FF9800"),
    ("L3 - Engineering", 3, "Engineering Support", "#F44336"),
]


def seed_support_levels() -> None:
    """
    Insert the 4 default HD Support Level records if they don't exist.

    Idempotent — safe to call multiple times.
    """
    for level_name, level_order, display_name, color in _SUPPORT_LEVELS:
        if frappe.db.exists("HD Support Level", level_name):
            continue
        frappe.get_doc(
            {
                "doctype": "HD Support Level",
                "level_name": level_name,
                "level_order": level_order,
                "display_name": display_name,
                "color": color,
                "allow_escalation_to_next": 1,
                "auto_escalate_on_breach": 0,
                "auto_escalate_minutes": 60,
            }
        ).insert(ignore_permissions=True)

    frappe.db.commit()  # nosemgrep
