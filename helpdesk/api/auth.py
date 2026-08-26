import frappe

from helpdesk.helpdesk.doctype.hd_ticket.team_hierarchy import (
    get_scoped_teams_for_agent,
    _LEGACY_FALLBACK,
)
from helpdesk.utils import get_agents_team
from helpdesk.utils import is_agent as _is_agent


@frappe.whitelist()
def get_user():
    current_user = frappe.session.user
    filters = {"name": current_user}
    fields = [
        "first_name",
        "full_name",
        "name",
        "user_image",
        "username",
        "time_zone",
        "language",
        "mobile_no",
    ]
    user = frappe.get_value(
        doctype="User",
        filters=filters,
        fieldname=fields,
        as_dict=True,
    )

    roles = frappe.get_roles(current_user)
    is_agent = _is_agent()
    is_admin = ("System Manager" in roles or "Administrator" in roles)
    is_manager = "Agent Manager" in roles
    is_customer = "Helpdesk Customer" in roles and not is_agent
    has_desk_access = is_agent or is_admin

    # True only for L2-National agents (can set Closed status)
    scoped = get_scoped_teams_for_agent(current_user)
    is_national_agent = scoped is True
    user_image = user.user_image
    user_first_name = user.first_name
    user_name = user.full_name
    user_id = user.name
    username = user.username
    user_team = get_agents_team()
    user_team_names = [team["team_name"] for team in user_team]
    language = user.language or frappe.db.get_single_value(
        "System Settings", "language"
    )

    force_password_change = bool(
        frappe.db.get_value("User", current_user, "force_password_change")
    )

    return {
        "has_desk_access": has_desk_access,
        "is_admin": is_admin,
        "is_agent": is_agent,
        "user_id": user_id,
        "is_manager": is_manager,
        "is_customer": is_customer,
        "user_image": user_image,
        "user_first_name": user_first_name,
        "user_name": user_name,
        "username": username,
        "time_zone": user.time_zone,
        "user_teams": user_team_names,
        "language": language,
        "is_national_agent": is_national_agent,
        "force_password_change": force_password_change,
        "mobile_no": user.mobile_no,
    }


@frappe.whitelist()
def complete_forced_password_change():
    """
    Called by the frontend immediately after a user successfully sets a new
    password following a forced password change. Clears the flag so they
    aren't redirected back to /update-password on their next request.
    """
    user = frappe.session.user
    if user in ("Administrator", "Guest"):
        return
    frappe.db.set_value("User", user, "force_password_change", 0)
    frappe.db.commit()
    return {"success": True}
