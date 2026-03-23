"""
Patch: create_hd_brand
Records the installation of the HD Brand DocType (Story 3.8).

The DocType is created via the JSON file; this patch ensures the migration
is recorded so it does not re-run on subsequent bench migrate calls.
"""

import frappe


def execute():
    # Reload DocType from JSON to ensure the schema is up-to-date
    if frappe.db.exists("DocType", "HD Brand"):
        frappe.reload_doc("Helpdesk", "doctype", "hd_brand", force=True)
