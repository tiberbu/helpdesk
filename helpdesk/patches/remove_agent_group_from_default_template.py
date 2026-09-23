import frappe


def execute():
    if not frappe.db.exists("HD Ticket Template", "Default"):
        return

    t = frappe.get_doc("HD Ticket Template", "Default")
    before = len(t.fields)
    t.fields = [f for f in t.fields if f.fieldname != "agent_group"]

    if len(t.fields) < before:
        t.save(ignore_permissions=True)
        frappe.db.commit()
