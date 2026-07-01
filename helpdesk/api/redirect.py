"""
Role-based redirect logic for Helpdesk
Prevents customers from accessing agent interfaces
"""

import frappe
from frappe import _


def get_redirect_after_login():
    """
    Determine where to redirect user after login based on their role.

    Priority:
    1. Agents/Agent Managers -> /helpdesk/home (full agent interface)
    2. System Manager -> /desk (backend)
    3. Helpdesk Customers -> /helpdesk/my-tickets (customer portal only)
    4. Default -> /helpdesk/my-tickets
    """
    user = frappe.session.user

    if user == "Administrator":
        return "/desk"

    roles = frappe.get_roles(user)

    # Agents get full helpdesk interface
    if "Agent" in roles or "Agent Manager" in roles:
        return "/helpdesk/home"

    # System Managers go to desk
    if "System Manager" in roles:
        return "/desk"

    # Everyone else (customers) goes to my-tickets portal
    return "/helpdesk/my-tickets"


@frappe.whitelist(allow_guest=True)
def check_access(path=None):
    """
    Check if current user can access a specific helpdesk path.
    Used to prevent customers from accessing agent interfaces.
    """
    user = frappe.session.user

    if user == "Guest":
        return {"allowed": False, "redirect": "/login"}

    if user == "Administrator":
        return {"allowed": True}

    roles = frappe.get_roles(user)

    # Parse the path
    if not path:
        path = frappe.local.request.path if frappe.local.request else ""

    # Agent-only paths
    agent_paths = [
        "/helpdesk/home",
        "/helpdesk/tickets",
        "/helpdesk/dashboard",
        "/helpdesk/reports",
        "/helpdesk/settings",
        "/helpdesk/knowledge-base/edit",
        "/helpdesk/agents",
        "/helpdesk/teams",
    ]

    # Check if path is agent-only
    is_agent_path = any(path.startswith(p) for p in agent_paths)

    # If it's an agent path, require Agent role
    if is_agent_path:
        if "Agent" in roles or "Agent Manager" in roles or "System Manager" in roles:
            return {"allowed": True}
        else:
            return {"allowed": False, "redirect": "/helpdesk/my-tickets"}

    # /desk is for System Managers and Agents only
    if path.startswith("/desk") or path.startswith("/app"):
        if "System Manager" in roles or "Agent" in roles or "Agent Manager" in roles:
            return {"allowed": True}
        else:
            return {"allowed": False, "redirect": "/helpdesk/my-tickets"}

    # Customer portal paths are accessible to everyone
    return {"allowed": True}


def redirect_based_on_role():
    """
    Middleware-style function to redirect users away from unauthorized pages.
    Call this from page controllers.
    """
    if frappe.session.user == "Guest":
        return

    path = frappe.local.request.path if frappe.local.request else ""
    access_check = check_access(path)

    if not access_check.get("allowed"):
        redirect_url = access_check.get("redirect", "/helpdesk/my-tickets")
        frappe.local.flags.redirect_location = redirect_url
        raise frappe.Redirect
