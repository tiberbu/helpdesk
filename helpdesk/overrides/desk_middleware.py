"""
Middleware to block customers from accessing /desk backend
"""

import frappe
from frappe import _


def block_customer_desk_access():
    """
    Block Helpdesk Customers from accessing /desk
    This runs before processing /desk requests
    """
    # Skip for non-desk routes
    if not hasattr(frappe.local, 'request') or not frappe.local.request:
        return

    path = frappe.local.request.path
    if not path.startswith("/desk") and not path.startswith("/app"):
        return

    # Allow for Administrator
    if frappe.session.user == "Administrator":
        return

    # Check roles
    roles = frappe.get_roles(frappe.session.user)

    # Block if only has Helpdesk Customer role (and not Agent/System Manager)
    is_customer_only = (
        "Helpdesk Customer" in roles and
        "Agent" not in roles and
        "Agent Manager" not in roles and
        "System Manager" not in roles
    )

    if is_customer_only:
        frappe.throw(
            _("Access Denied: You don't have permission to access the backend. Please use the customer portal at /helpdesk/my-tickets"),
            frappe.PermissionError
        )


def enforce_password_change():
    """
    Block API access for users who have been flagged (via HelpdeskUser.validate)
    to change their password. Page loads (the SPA shell) are always allowed
    through unmodified — the frontend router guard handles redirecting them
    to /set-password once the app boots and reads their user info.
    """
    if not hasattr(frappe.local, 'request') or not frappe.local.request:
        return

    user = frappe.session.user
    if user in ("Administrator", "Guest"):
        return

    path = frappe.local.request.path

    # Only enforce on API calls — page/asset loads pass through untouched
    if not path.startswith("/api/"):
        return

    allowed_prefixes = (
        "/api/method/frappe.core.doctype.user.user.update_password",
        "/api/method/frappe.core.doctype.user.user.test_password_strength",
        "/api/method/helpdesk.api.auth.complete_forced_password_change",
        "/api/method/helpdesk.api.auth.get_user",
        "/api/method/logout",
        "/api/method/login",
        "/api/method/ping",
    )
    if any(path.startswith(p) for p in allowed_prefixes):
        return

    if frappe.db.get_value("User", user, "force_password_change"):
        frappe.throw(
            _("You must set a new password before continuing."),
            frappe.PermissionError,
        )
