"""
Migration patch: Ensure is_internal column exists on HD Ticket Comment.

The is_internal Check field was introduced in Story 1.4 to support
internal-only notes visible exclusively to agents.

Safe to run multiple times (idempotent).
"""

import frappe


def execute():
    """Add is_internal column to tabHD Ticket Comment if absent."""
    db_name = frappe.conf.db_name
    exists = frappe.db.sql(
        """
        SELECT COUNT(*)
        FROM information_schema.COLUMNS
        WHERE TABLE_SCHEMA = %(db_name)s
          AND TABLE_NAME   = 'tabHD Ticket Comment'
          AND COLUMN_NAME  = 'is_internal'
        """,
        {"db_name": db_name},
    )[0][0]

    if not exists:
        frappe.db.sql(
            "ALTER TABLE `tabHD Ticket Comment` "
            "ADD COLUMN `is_internal` int(1) NOT NULL DEFAULT 0"
        )

    frappe.db.commit()
