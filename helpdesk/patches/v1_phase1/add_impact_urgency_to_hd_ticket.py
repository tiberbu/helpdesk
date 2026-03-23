"""
Migration patch: Add impact and urgency Select fields to HD Ticket.

Ensures that on existing installations the new ITIL fields introduced in Story 1.2
(impact, urgency) are present on the HD Ticket table with NULL defaults, preserving
all existing ticket data.

Also ensures the priority_matrix JSON field exists on HD Settings with the default
3x3 ITIL matrix if not already added by the Story 1.1 patch.

Safe to run multiple times (idempotent).
"""

import json

import frappe

DEFAULT_PRIORITY_MATRIX = {
    "High-High": "Urgent",
    "High-Medium": "High",
    "High-Low": "Medium",
    "Medium-High": "High",
    "Medium-Medium": "Medium",
    "Medium-Low": "Low",
    "Low-High": "Medium",
    "Low-Medium": "Low",
    "Low-Low": "Low",
}


def execute():
    """Add impact and urgency columns to tabHD Ticket if absent."""
    _ensure_ticket_column("impact", "varchar(50) DEFAULT NULL")
    _ensure_ticket_column("urgency", "varchar(50) DEFAULT NULL")
    _ensure_priority_matrix_default()
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


def _ensure_priority_matrix_default():
    """Ensure priority_matrix field on HD Settings has its default value."""
    current = frappe.db.get_single_value("HD Settings", "priority_matrix")
    if current is None:
        frappe.db.set_value(
            "HD Settings",
            "HD Settings",
            "priority_matrix",
            json.dumps(DEFAULT_PRIORITY_MATRIX),
        )
