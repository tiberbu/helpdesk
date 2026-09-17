import frappe


def has_app_permission():
    """Check if the user has permission to access the app."""
    if frappe.session.user == "Administrator":
        return True

    roles = frappe.get_roles()
    helpdesk_roles = ["Agent", "Agent Manager", "Helpdesk Customer"]
    if any(role in roles for role in helpdesk_roles):
        return True

    # Allow anyone with desk access (for backwards compatibility)
    return True


def is_agent():
    """Check if current user is an agent."""
    if frappe.session.user == "Administrator":
        return True

    roles = frappe.get_roles()
    return "Agent" in roles or "Agent Manager" in roles or "System Manager" in roles


def is_customer():
    """Check if current user is a customer (not an agent)."""
    if frappe.session.user == "Administrator":
        return False

    roles = frappe.get_roles()
    return "Helpdesk Customer" in roles and not is_agent()
