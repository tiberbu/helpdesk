import frappe

def create():
    # Create the API user
    user = frappe.get_doc({
        "doctype": "User",
        "email": "hmis-api@tiberbu.com",
        "first_name": "HMIS",
        "last_name": "API",
        "user_type": "System User",
        "enabled": 1,
        "send_welcome_email": 0,
        "roles": [
            {"role": "Administrator"},
            {"role": "System Manager"},
        ]
    })
    user.flags.ignore_permissions = True
    user.insert()
    frappe.db.commit()

    # Generate API key and secret
    user.api_key = frappe.generate_hash(length=15)
    user.api_secret = frappe.generate_hash(length=15)
    user.save()
    frappe.db.commit()

    print(f"User created: hmis-api@tiberbu.com")
    print(f"API Key:    {user.api_key}")
    print(f"API Secret: {user.get_password('api_secret')}")
