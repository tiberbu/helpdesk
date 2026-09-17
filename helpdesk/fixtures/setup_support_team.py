"""
Setup script for Support Team with automatic round-robin assignment.

This creates:
1. HD Team: "Support Team" with keneth@tiberbu.com and kagai@tiberbu.com
2. Assignment Rule: Round-robin distribution between the two agents
3. Auto-assignment trigger: When agent_group is set to "Support Team"

Run with: bench execute helpdesk.fixtures.setup_support_team.setup
"""

import frappe


def setup():
    """Main setup function to create team and assignment rule."""

    # Step 1: Ensure both users exist as HD Agents
    agents = [
        {"email": "keneth@tiberbu.com", "full_name": "Kenneth"},
        {"email": "kagai@tiberbu.com", "full_name": "Karen"}
    ]

    for agent in agents:
        ensure_agent_exists(agent["email"], agent["full_name"])

    # Step 2: Create or update the Support Team
    team = create_support_team(agents)

    # Step 3: Configure assignment rule for round-robin
    configure_assignment_rule(team, agents)

    frappe.db.commit()

    print("\n✅ Setup Complete!")
    print(f"Team: {team.name}")
    print(f"Assignment Rule: {team.assignment_rule}")
    print(f"Members: {', '.join([a['email'] for a in agents])}")
    print("\n📋 Usage:")
    print("   When creating/updating a ticket:")
    print("   - Set 'Team' field to 'Support Team'")
    print("   - Agent will be automatically assigned in round-robin")


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
        agent.name = email
        agent.user = email
        agent.insert(ignore_permissions=True)
        print(f"✅ Created HD Agent: {email}")


def create_support_team(agents):
    """Create or update Support Team with the given agents."""

    team_name = "Support Team"

    if frappe.db.exists("HD Team", team_name):
        print(f"Updating existing team: {team_name}")
        team = frappe.get_doc("HD Team", team_name)
    else:
        print(f"Creating new team: {team_name}")
        team = frappe.new_doc("HD Team")
        team.team_name = team_name

    # Clear existing members and add fresh
    team.users = []
    for agent in agents:
        team.append("users", {"user": agent["email"]})

    team.ignore_restrictions = 0  # Apply normal restrictions

    # Get or create default support level
    support_level = ensure_support_level_exists()
    team.support_level = support_level

    team.save(ignore_permissions=True)
    print(f"✅ Team '{team_name}' configured with {len(agents)} agents")

    return team


def ensure_support_level_exists():
    """Ensure a default support level exists."""

    level_name = "L1 - General Support"

    if not frappe.db.exists("HD Support Level", level_name):
        level = frappe.new_doc("HD Support Level")
        level.name = level_name
        level.level_order = 1
        level.insert(ignore_permissions=True)
        print(f"✅ Created support level: {level_name}")

    return level_name


def configure_assignment_rule(team, agents):
    """Configure the assignment rule for round-robin distribution."""

    if not team.assignment_rule:
        print("⚠️  No assignment rule found for team. Creating one...")
        team.create_assignment_rule()
        team.reload()

    rule = frappe.get_doc("Assignment Rule", team.assignment_rule)

    # Set to Round Robin mode
    rule.rule = "Round Robin"
    rule.disabled = 0  # Enable the rule
    rule.priority = 1

    # Ensure condition matches team
    rule.assign_condition = f"status == 'Open' and agent_group == '{team.name}'"
    rule.assign_condition_json = f'[["status","==","Open"],"and",["agent_group","==","{team.name}"]]'

    # Clear existing users and add fresh
    rule.users = []
    for agent in agents:
        rule.append("users", {"user": agent["email"]})

    # Reset round-robin counter
    rule.last_user = None

    # Ensure all days are enabled
    if not rule.assignment_days:
        for day in ["Monday", "Tuesday", "Wednesday", "Thursday", "Friday", "Saturday", "Sunday"]:
            rule.append("assignment_days", {"day": day})

    rule.save(ignore_permissions=True)
    print(f"✅ Assignment rule configured: Round Robin with {len(agents)} agents")


if __name__ == "__main__":
    setup()
