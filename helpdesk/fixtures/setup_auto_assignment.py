"""
Auto-assignment setup for all new tickets with round-robin distribution.

This creates an Assignment Rule that automatically assigns every new ticket
to either keneth@tiberbu.com or kagai@tiberbu.com in round-robin fashion.

Run with: bench --site erp.local execute helpdesk.fixtures.setup_auto_assignment.setup
"""

import frappe


def setup():
    """Main setup function for automatic round-robin assignment."""

    # Step 1: Ensure both users exist as HD Agents
    agents = [
        {"email": "keneth@tiberbu.com", "full_name": "Kenneth"},
        {"email": "kagai@tiberbu.com", "full_name": "Karen"}
    ]

    print("\n🔧 Setting up automatic ticket assignment...\n")

    for agent in agents:
        ensure_agent_exists(agent["email"], agent["full_name"])

    # Step 2: Create/update assignment rule for all new tickets
    rule = create_auto_assignment_rule(agents)

    frappe.db.commit()

    print("\n✅ Setup Complete!")
    print(f"Assignment Rule: {rule.name}")
    print(f"Mode: Round Robin")
    print(f"Assignees: {', '.join([a['email'] for a in agents])}")
    print(f"Status: {'Enabled' if not rule.disabled else 'Disabled'}")
    print("\n📋 How it works:")
    print("   - Every new ticket with status='Open' is auto-assigned")
    print("   - Assignment alternates between Kenneth and Karen")
    print("   - First ticket → Kenneth, Second → Karen, Third → Kenneth, etc.")
    print("\n💡 To test:")
    print("   Create a new ticket and check the 'Assigned To' field")


def ensure_agent_exists(email, full_name=None):
    """Ensure user exists and is set up as an HD Agent."""

    # Check if user exists
    if not frappe.db.exists("User", email):
        print(f"⚠️  User {email} does not exist. Creating...")
        user = frappe.new_doc("User")
        user.email = email
        user.first_name = full_name or email.split("@")[0]
        user.enabled = 1
        user.send_welcome_email = 0
        user.append("roles", {"role": "Agent"})
        user.insert(ignore_permissions=True)
        print(f"✅ Created user: {email}")
    else:
        # Ensure Agent role exists
        user = frappe.get_doc("User", email)
        has_agent_role = any(r.role == "Agent" for r in user.roles)
        if not has_agent_role:
            user.append("roles", {"role": "Agent"})
            user.save(ignore_permissions=True)
            print(f"✅ Added Agent role to: {email}")

    # Check if HD Agent profile exists
    if not frappe.db.exists("HD Agent", email):
        print(f"Creating HD Agent profile for {email}...")
        agent = frappe.new_doc("HD Agent")
        agent.user = email
        agent.agent_name = full_name or email.split("@")[0]
        agent.is_active = 1
        agent.insert(ignore_permissions=True)
        print(f"✅ Created HD Agent: {email}")


def create_auto_assignment_rule(agents):
    """Create or update the global auto-assignment rule."""

    rule_name = "Auto-Assign All Tickets"

    if frappe.db.exists("Assignment Rule", rule_name):
        print(f"Updating existing rule: {rule_name}")
        rule = frappe.get_doc("Assignment Rule", rule_name)
    else:
        print(f"Creating new rule: {rule_name}")
        rule = frappe.new_doc("Assignment Rule")
        rule.name = rule_name

    # Configure for HD Ticket doctype
    rule.document_type = "HD Ticket"
    rule.description = "Automatically assigns all open tickets to support agents in round-robin"

    # Set condition: trigger on open tickets
    rule.assign_condition = "status == 'Open'"
    rule.assign_condition_json = '[["status", "==", "Open"]]'

    # Set to Round Robin mode
    rule.rule = "Round Robin"
    rule.disabled = 0  # Enable the rule
    rule.priority = 0  # Highest priority (runs first)

    # Clear existing users and add fresh
    rule.users = []
    for agent in agents:
        rule.append("users", {"user": agent["email"]})

    # Reset round-robin counter
    rule.last_user = None

    # Ensure all days are enabled (assignment works every day)
    if not rule.assignment_days:
        for day in ["Monday", "Tuesday", "Wednesday", "Thursday", "Friday", "Saturday", "Sunday"]:
            rule.append("assignment_days", {"day": day})

    rule.save(ignore_permissions=True)
    print(f"✅ Assignment rule configured: Round Robin with {len(agents)} agents")

    return rule


if __name__ == "__main__":
    setup()
