"""Test round-robin ticket assignment."""

import frappe
import time


def test():
    """Create test tickets and verify round-robin assignment."""

    print("\n🧪 Testing Round-Robin Assignment...\n")

    # Create 4 test tickets
    for i in range(1, 5):
        ticket = frappe.get_doc({
            'doctype': 'HD Ticket',
            'subject': f'Test Ticket #{i} - Round Robin Assignment',
            'status': 'Open',
            'raised_by': 'Administrator',
            'description': f'Testing automatic assignment - Ticket {i}'
        })
        ticket.insert(ignore_permissions=True)
        frappe.db.commit()

        # Wait a moment for assignment rule to trigger
        time.sleep(1)

        # Check who it was assigned to
        ticket.reload()
        assigned_to = None
        if ticket._assign:
            import json
            assignees = json.loads(ticket._assign)
            if assignees:
                assigned_to = assignees[0]

        print(f"Ticket #{ticket.name}: {ticket.subject}")
        print(f"   Assigned to: {assigned_to or 'NOT ASSIGNED'}")
        print()

    print("✅ Test complete! Check if assignment alternates between:")
    print("   - keneth@tiberbu.com")
    print("   - kagai@tiberbu.com")


if __name__ == "__main__":
    test()
