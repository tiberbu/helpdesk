"""
Migration patch: Add missing HD Ticket Category records.

Supplements create_default_categories.py with:
- "Access & Accounts" top-level (AC10 requires >= 5 top-level)
  - "Password Reset", "New User Access", "Permission Request"
- "Billing" top-level (AC5 requires Billing > Invoice Dispute + Refund Request)
  - "Invoice Dispute", "Refund Request", "Subscription Change"
- "General" sub-categories (AC10 requires each parent to have >= 2)
  - "General Inquiry", "Other"

Safe to run multiple times (idempotent — skips records that already exist).
"""

import frappe

ADDITIONAL_CATEGORIES = [
    # New top-level categories
    ("Access & Accounts", None),
    ("Billing", None),
    # Access & Accounts sub-categories
    ("Password Reset", "Access & Accounts"),
    ("New User Access", "Access & Accounts"),
    ("Permission Request", "Access & Accounts"),
    # Billing sub-categories (AC5 explicitly requires these two)
    ("Invoice Dispute", "Billing"),
    ("Refund Request", "Billing"),
    ("Subscription Change", "Billing"),
    # General sub-categories (AC10 requires at least 2)
    ("General Inquiry", "General"),
    ("Other", "General"),
]


def execute():
    for name, parent_category in ADDITIONAL_CATEGORIES:
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
