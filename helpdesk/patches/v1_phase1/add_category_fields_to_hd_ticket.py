"""
Migration patch: Ensure category and sub_category columns exist on HD Ticket.

The category and sub_category Link fields were introduced in Story 1.3.
This patch ensures the columns are present on existing installations with
NULL defaults, preserving all existing ticket data.

Also ensures category_required_on_resolution exists on HD Settings.

Safe to run multiple times (idempotent).
"""

import frappe


def execute():
    """Add category and sub_category columns to tabHD Ticket if absent."""
    _ensure_ticket_column("category", "varchar(140) DEFAULT NULL")
    _ensure_ticket_column("sub_category", "varchar(140) DEFAULT NULL")
    _ensure_hd_settings_column()
    frappe.db.commit()


def _ensure_ticket_column(fieldname, column_definition):
    """Add column to tabHD Ticket if it does not already exist."""
    db_name = frappe.conf.db_name
    exists = frappe.db.sql(
        """
        SELECT COUNT(*)
        FROM information_schema.COLUMNS
        WHERE TABLE_SCHEMA = %(db_name)s
          AND TABLE_NAME   = 'tabHD Ticket'
          AND COLUMN_NAME  = %(fieldname)s
        """,
        {"db_name": db_name, "fieldname": fieldname},
    )[0][0]

    if not exists:
        frappe.db.sql(
            f"ALTER TABLE `tabHD Ticket` ADD COLUMN `{fieldname}` {column_definition}"
        )


def _ensure_hd_settings_column():
    """Ensure category_required_on_resolution column exists in HD Settings."""
    db_name = frappe.conf.db_name

    # Guard: skip if the HD Settings table itself does not yet exist
    table_exists = frappe.db.sql(
        """
        SELECT COUNT(*)
        FROM information_schema.TABLES
        WHERE TABLE_SCHEMA = %(db_name)s
          AND TABLE_NAME   = 'tabHD Settings'
        """,
        {"db_name": db_name},
    )[0][0]
    if not table_exists:
        return

    exists = frappe.db.sql(
        """
        SELECT COUNT(*)
        FROM information_schema.COLUMNS
        WHERE TABLE_SCHEMA = %(db_name)s
          AND TABLE_NAME   = 'tabHD Settings'
          AND COLUMN_NAME  = 'category_required_on_resolution'
        """,
        {"db_name": db_name},
    )[0][0]

    if not exists:
        frappe.db.sql(
            "ALTER TABLE `tabHD Settings` "
            "ADD COLUMN `category_required_on_resolution` int(1) DEFAULT 0"
        )
