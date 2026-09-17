"""Helper script to create customer users for testing"""

import frappe


def create_customer_user(email, first_name, last_name="", send_welcome_email=False):
    """
    Create a customer user with Helpdesk Customer role.

    Args:
        email: User email address
        first_name: User first name
        last_name: User last name (optional)
        send_welcome_email: Whether to send welcome email (default: False)

    Returns:
        User document
    """
    if frappe.db.exists("User", email):
        print(f"❌ User already exists: {email}")
        return frappe.get_doc("User", email)

    user = frappe.new_doc("User")
    user.email = email
    user.first_name = first_name
    if last_name:
        user.last_name = last_name
    user.enabled = 1
    user.send_welcome_email = 1 if send_welcome_email else 0

    # Add Helpdesk Customer role
    user.append("roles", {"role": "Helpdesk Customer"})

    # Add basic roles
    user.append("roles", {"role": "All"})
    user.append("roles", {"role": "Guest"})

    user.insert(ignore_permissions=True)
    frappe.db.commit()

    print(f"✅ Created customer user: {email}")
    print(f"   Name: {user.full_name}")
    print(f"   Roles: Helpdesk Customer")
    print(f"   Login URL: https://support.tiberbu.app/login")
    print(f"   After login, will be redirected to: /helpdesk/my-tickets")

    return user


if __name__ == "__main__":
    # Example: Create a test customer
    create_customer_user(
        email="testcustomer@tiberbu.com",
        first_name="Test",
        last_name="Customer",
        send_welcome_email=False
    )
