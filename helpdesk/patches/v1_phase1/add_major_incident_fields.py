"""
Add major incident fields to HD Ticket and major_incident_contacts to HD Settings.

Story 1.8: Major Incident Flag and Workflow
"""

import frappe


def execute():
    # Add fields to HD Ticket if missing (schema sync handles DDL; this handles data defaults)
    if not frappe.db.has_column("HD Ticket", "is_major_incident"):
        frappe.db.sql(
            "ALTER TABLE `tabHD Ticket` ADD COLUMN `is_major_incident` INT(1) NOT NULL DEFAULT 0"
        )

    if not frappe.db.has_column("HD Ticket", "major_incident_flagged_at"):
        frappe.db.sql(
            "ALTER TABLE `tabHD Ticket` ADD COLUMN `major_incident_flagged_at` DATETIME NULL DEFAULT NULL"
        )

    if not frappe.db.has_column("HD Ticket", "root_cause_summary"):
        frappe.db.sql(
            "ALTER TABLE `tabHD Ticket` ADD COLUMN `root_cause_summary` LONGTEXT NULL DEFAULT NULL"
        )

    if not frappe.db.has_column("HD Ticket", "corrective_actions"):
        frappe.db.sql(
            "ALTER TABLE `tabHD Ticket` ADD COLUMN `corrective_actions` LONGTEXT NULL DEFAULT NULL"
        )

    if not frappe.db.has_column("HD Ticket", "prevention_measures"):
        frappe.db.sql(
            "ALTER TABLE `tabHD Ticket` ADD COLUMN `prevention_measures` LONGTEXT NULL DEFAULT NULL"
        )

    frappe.db.commit()  # nosemgrep
