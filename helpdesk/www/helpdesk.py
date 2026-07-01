"""
Main helpdesk app entry point with role-based access control
"""

import frappe
from frappe import _


def get_context(context):
    """
    Entry point for /helpdesk route.
    Enforces role-based access control.
    """
    # Check if user is logged in
    if frappe.session.user == "Guest":
        frappe.local.flags.redirect_location = "/login?redirect-to=/helpdesk"
        raise frappe.Redirect

    # Get user roles
    roles = frappe.get_roles(frappe.session.user)

    # Check if user is an agent (has access to full helpdesk)
    is_agent = ("Agent" in roles or "Agent Manager" in roles or
                "System Manager" in roles or
                frappe.session.user == "Administrator")

    # Get the requested path
    request_path = frappe.local.request.path if hasattr(frappe.local, 'request') else ""

    # If customer trying to access agent-only routes, redirect to customer portal
    if not is_agent:
        # Allow customer portal routes
        customer_allowed_paths = [
            "/helpdesk/my-tickets",
            "/helpdesk/kb-public",
        ]

        # Check if current path is allowed for customers
        is_allowed = any(request_path.startswith(path) for path in customer_allowed_paths)

        if not is_allowed:
            # Customer trying to access agent interface - redirect to customer portal
            frappe.local.flags.redirect_location = "/helpdesk/my-tickets"
            raise frappe.Redirect

    # Set context for the SPA
    context.no_cache = 1
    context.show_sidebar = False

    return context
