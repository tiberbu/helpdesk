import frappe


def execute():
    """Add review_date, reviewed_by, and last_reminder_sent fields to HD Article.

    These fields support Story 5.3 — Review Dates and Expiry Reminders.
    No back-fill is performed; existing articles start with null values.
    """
    doctype = "HD Article"

    columns_to_add = [
        {"fieldname": "review_date", "fieldtype": "Date"},
        {"fieldname": "reviewed_by", "fieldtype": "Link", "options": "User"},
        {"fieldname": "last_reminder_sent", "fieldtype": "Date"},
    ]

    for col in columns_to_add:
        if not frappe.db.has_column(doctype, col["fieldname"]):
            frappe.db.add_column(doctype, col["fieldname"], col["fieldtype"])

    frappe.db.commit()  # nosemgrep
