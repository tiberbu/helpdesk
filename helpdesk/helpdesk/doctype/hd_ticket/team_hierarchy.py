"""
Hierarchical team visibility helpers for HD Ticket permission scoping.

Implements the County support tier model:
  L0 (level_order=0) — Sub-County: sees only tickets assigned to their own team
  L1 (level_order=1) — County: sees own team + all descendant L0 teams
  L2 (level_order≥2) — National: sees ALL tickets (no restriction)
  L3 (level_order=3) — Engineering: sees only tickets assigned to L3 teams
                        (i.e. explicitly escalated to engineering)

Used by permission_query() in hd_ticket.py.
"""

import frappe


def get_user_teams(user: str) -> list:
    """Return HD Team names where *user* is a member."""
    rows = frappe.get_all(
        "HD Team Member",
        filters={"user": user},
        fields=["parent"],
    )
    return [r["parent"] for r in rows]


def get_team_level_order(team_name: str):
    """Return the integer level_order for *team_name*'s support level, or None."""
    support_level = frappe.db.get_value("HD Team", team_name, "support_level")
    if not support_level:
        return None
    return frappe.db.get_value("HD Support Level", support_level, "level_order")


def get_descendant_teams(team_name: str) -> list:
    """Recursively return all child team names under *team_name* (BFS)."""
    descendants = []
    queue = [team_name]
    visited = set()

    while queue:
        current = queue.pop(0)
        if current in visited:
            continue
        visited.add(current)

        children = frappe.get_all(
            "HD Team",
            filters={"parent_team": current},
            pluck="name",
        )
        for child in children:
            descendants.append(child)
            queue.append(child)

    return descendants


def is_national_level(team_names: list) -> bool:
    """Return True if any team in *team_names* has level_order == 2 (L2 National only).

    L3 Engineering is NOT treated as national — it has its own restricted scope.
    """
    for team in team_names:
        order = get_team_level_order(team)
        if order is not None and order == 2:
            return True
    return False


# Sentinel: returned by get_scoped_teams_for_agent to signal "no support level
# hierarchy is configured" → caller should fall back to legacy team filter.
_LEGACY_FALLBACK = object()


def get_scoped_teams_for_agent(user: str):
    """
    Compute the set of team names whose tickets *user* is allowed to see.

    Returns:
        True              — L2 National: user should see ALL tickets (no restriction)
        _LEGACY_FALLBACK  — no support levels configured; use legacy team filter
        list              — team names whose agent_group tickets are visible (L0/L1/L3)
                            may be an empty list if agent has no teams

    Use ``result is True`` to detect the "see all" case.
    Use ``result is _LEGACY_FALLBACK`` to detect the legacy fallback case.
    """
    user_teams = get_user_teams(user)
    if not user_teams:
        return []  # no teams → no team-scoped tickets

    # Determine whether ANY team carries a support level (hierarchy in use)
    any_has_level = any(
        get_team_level_order(t) is not None for t in user_teams
    )
    if not any_has_level:
        # Legacy deployment: no support levels configured — use old behaviour
        return _LEGACY_FALLBACK

    # L2 National: unrestricted view
    if is_national_level(user_teams):
        return True  # signal: see all tickets

    # Build the scoped set (L0, L1, L3, or unknown)
    scoped = set()
    for team in user_teams:
        order = get_team_level_order(team)
        if order is None:
            # Team has no level → restrict to own team only
            scoped.add(team)
        elif order == 3:
            # L3 Engineering: only own L3 team (tickets explicitly escalated to engineering)
            scoped.add(team)
        elif order == 1:
            # L1 County: own team + all descendant teams (L0 sub-counties)
            scoped.add(team)
            for desc in get_descendant_teams(team):
                scoped.add(desc)
        else:
            # L0 Sub-County (or any other level): own team only
            scoped.add(team)

    return list(scoped)
