"""
Add ticket_type, priority, and agent_group as customer-visible fields
on the Default ticket template so users can select them when submitting.
"""
import frappe


def execute():
    if not frappe.db.exists("HD Ticket Template", "Default"):
        return

    t = frappe.get_doc("HD Ticket Template", "Default")

    existing = {f.fieldname for f in t.fields}

    fields_to_add = [
        {"fieldname": "ticket_type", "required": 0, "hide_from_customer": 0},
        {"fieldname": "priority",    "required": 0, "hide_from_customer": 0},
        {"fieldname": "agent_group", "required": 0, "hide_from_customer": 0},
    ]

    changed = False
    for f in fields_to_add:
        if f["fieldname"] not in existing:
            t.append("fields", f)
            changed = True

    if changed:
        t.save(ignore_permissions=True)
        frappe.db.commit()
