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
