"""Create a test ticket to verify auto-assignment."""

import frappe
import json


def create():
    """Create a test ticket and check assignment."""

    print("\n🎫 Creating test ticket...\n")

    # Get or create a contact
    contact_email = "test@example.com"
    if not frappe.db.exists("Contact", {"email_id": contact_email}):
        contact = frappe.new_doc("Contact")
        contact.first_name = "Test"
        contact.last_name = "User"
        contact.append("email_ids", {"email_id": contact_email, "is_primary": 1})
        contact.insert(ignore_permissions=True)
        print(f"✅ Created contact: {contact.name}")
    else:
        contact_name = frappe.db.get_value("Contact", {"email_id": contact_email})
        contact = frappe.get_doc("Contact", contact_name)
        print(f"✅ Using existing contact: {contact.name}")

    # Create ticket
    ticket = frappe.new_doc("HD Ticket")
    ticket.subject = "Test Ticket - Auto Assignment"
    ticket.description = "<p>Testing automatic round-robin assignment</p>"
    ticket.raised_by = contact_email
    ticket.contact = contact.name

    # Don't set status - let it use default

    print(f"Creating ticket...")
    ticket.insert(ignore_permissions=True)
    frappe.db.commit()

    print(f"\n✅ Ticket created: {ticket.name}")
    print(f"   Subject: {ticket.subject}")
    print(f"   Status: {ticket.status}")
    print(f"   Contact: {ticket.contact}")

    # Wait a moment and reload
    import time
    time.sleep(2)
    ticket.reload()

    # Check assignment
    if ticket._assign:
        assignees = json.loads(ticket._assign)
        print(f"\n✅ ASSIGNED TO: {assignees[0]}")
        print(f"\n🎉 Success! Auto-assignment is working!")
    else:
        print(f"\n❌ NOT ASSIGNED")
        print(f"\nDebugging info:")
        print(f"  Ticket status: {ticket.status}")

        # Check assignment rule
        rule = frappe.get_doc("Assignment Rule", "Auto-Assign All Tickets")
        print(f"  Assignment Rule:")
        print(f"    - Disabled: {rule.disabled}")
        print(f"    - Condition: {rule.assign_condition}")
        print(f"    - Users: {[u.user for u in rule.users]}")

        # Try to manually trigger
        print(f"\n  Trying manual assignment...")
        from frappe.automation.doctype.assignment_rule.assignment_rule import apply
        apply(doc=ticket)
        frappe.db.commit()

        ticket.reload()
        if ticket._assign:
            assignees = json.loads(ticket._assign)
            print(f"  ✅ Manual assignment worked: {assignees[0]}")
        else:
            print(f"  ❌ Manual assignment also failed")


if __name__ == "__main__":
    create()
