"""Persist the password-change flag consumed by Helpdesk's login bootstrap."""

from frappe.custom.doctype.custom_field.custom_field import create_custom_fields


def execute():
    create_custom_fields(
        {
            "User": [
                {
                    "fieldname": "force_password_change",
                    "label": "Force Password Change",
                    "fieldtype": "Check",
                    "default": "0",
                    "hidden": 1,
                    "read_only": 1,
                    "no_copy": 1,
                }
            ]
        }
    )
