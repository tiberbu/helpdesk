"""
Session overrides for role-based redirects
"""

import frappe


def on_session_creation(login_manager):
    """
    Hook that runs after successful login.
    Redirects users based on their role.
    """
    try:
        # Skip if already redirecting
        if hasattr(frappe.local, 'response') and frappe.local.response.get("type") == "redirect":
            return

        # Skip for API calls and non-web requests
        if not hasattr(frappe.local, 'request') or not frappe.local.request:
            return

        # Get user roles
        user = frappe.session.user
        if user == "Administrator":
            redirect_url = "/desk"
        else:
            roles = frappe.get_roles(user)

            # Agents get full helpdesk interface
            if "Agent" in roles or "Agent Manager" in roles:
                redirect_url = "/helpdesk/home"
            # System Managers go to desk
            elif "System Manager" in roles:
                redirect_url = "/desk"
            # Everyone else (customers) goes to my-tickets portal
            else:
                redirect_url = "/helpdesk/my-tickets"

        # Set redirect
        if not hasattr(frappe.local, 'response'):
            frappe.local.response = frappe._dict()

        frappe.local.response["type"] = "redirect"
        frappe.local.response["location"] = redirect_url

    except Exception as e:
        # Log error but don't break login
        frappe.log_error(f"Session redirect error: {str(e)}", "Session Hook Error")
