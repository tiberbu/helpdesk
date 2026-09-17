"""Create teams and add all agents to them."""

import frappe


def create_teams():
    """Create all teams with Kenneth, Karen, and Austine as members."""

    # 1. Create support level if it doesn't exist
    if not frappe.db.exists("HD Support Level", "Level 1 - Regional"):
        support_level = frappe.new_doc("HD Support Level")
        support_level.level_name = "Level 1 - Regional"
        support_level.level_order = 1
        support_level.display_name = "Level 1"
        support_level.insert(ignore_permissions=True)
        print("✅ Created Support Level: Level 1 - Regional")

    # 2. Define all teams
    team_names = [
        "Central Region",
        "Coast Region",
        "Eastern Region",
        "Nairobi",
        "Nairobi Metropolitan",
        "National Support",
        "Nyanza Region",
        "Rift Valley North",
        "Rift Valley South",
        "Western Region"
    ]

    # 3. Define agents
    agents = [
        'keneth@tiberbu.com',
        'kagai@tiberbu.com',
        'austine@tiberbu.com'
    ]

    # 4. Create each team
    for team_name in team_names:
        if not frappe.db.exists('HD Team', team_name):
            team = frappe.new_doc('HD Team')
            team.team_name = team_name
            team.support_level = "Level 1 - Regional"

            # Add all three agents to this team
            for agent_email in agents:
                team.append('users', {'user': agent_email})

            team.insert(ignore_permissions=True)
            print(f"✅ Created team: {team_name} with 3 agents")
        else:
            # Team exists, make sure all agents are added
            team = frappe.get_doc('HD Team', team_name)
            existing_users = [u.user for u in team.users]

            added = False
            for agent_email in agents:
                if agent_email not in existing_users:
                    team.append('users', {'user': agent_email})
                    added = True

            if added:
                team.save(ignore_permissions=True)
                print(f"✅ Updated team: {team_name} - added missing agents")
            else:
                print(f"✓ Team exists: {team_name} - all agents already members")

    frappe.db.commit()

    print(f"\n🎉 All {len(team_names)} teams ready!")
    print(f"Each team has:")
    for agent in agents:
        print(f"  - {agent}")


if __name__ == "__main__":
    create_teams()
