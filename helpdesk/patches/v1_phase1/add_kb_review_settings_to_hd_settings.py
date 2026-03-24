import frappe


def execute():
    """Set default kb_review_period_days value in HD Settings.

    HD Settings is a Single DocType (tabSingles), so no column add is needed.
    The field is already declared in the JSON; this patch only seeds the default.
    Supports Story 5.3 — Review Dates and Expiry Reminders.
    """
    # Reload the DocType so the new field is recognised
    frappe.reload_doc("helpdesk", "doctype", "hd_settings")

    # Set default value on the singleton record if not already set
    current = frappe.db.get_single_value("HD Settings", "kb_review_period_days")
    if not current:
        frappe.db.set_single_value("HD Settings", "kb_review_period_days", 90)

    frappe.db.commit()  # nosemgrep
