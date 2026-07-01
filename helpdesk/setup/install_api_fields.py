"""
Install custom fields for HMIS API Integration
Run with: bench --site support.tiberbu.app execute helpdesk.setup.install_api_fields.install
"""

import frappe


def install():
    """Install custom fields for external API integration"""

    print("Installing HMIS API Integration custom fields...")

    # Install HD Settings fields
    install_hd_settings_fields()

    # Install HD Ticket fields
    install_hd_ticket_fields()

    frappe.db.commit()
    print("✅ Custom fields installed successfully!")


def install_hd_settings_fields():
    """Add API configuration fields to HD Settings"""

    fields = [
        {
            "fieldname": "external_api_section",
            "label": "External API Integration",
            "fieldtype": "Section Break",
            "insert_after": "enable_email_threads",
            "collapsible": 1
        },
        {
            "fieldname": "enable_external_api",
            "label": "Enable External API",
            "fieldtype": "Check",
            "insert_after": "external_api_section",
            "default": "0",
            "description": "Enable API integration for external systems (HMIS, etc.)"
        },
        {
            "fieldname": "external_api_key",
            "label": "API Key",
            "fieldtype": "Data",
            "insert_after": "enable_external_api",
            "depends_on": "eval:doc.enable_external_api==1",
            "description": "API Key for external systems to authenticate"
        },
        {
            "fieldname": "external_api_secret",
            "label": "API Secret",
            "fieldtype": "Password",
            "insert_after": "external_api_key",
            "depends_on": "eval:doc.enable_external_api==1",
            "description": "API Secret for external systems to authenticate (keep this secure)"
        },
    ]

    for field in fields:
        create_custom_field("HD Settings", field)


def install_hd_ticket_fields():
    """Add HMIS reference fields to HD Ticket"""

    fields = [
        {
            "fieldname": "external_integration_section",
            "label": "External System Integration",
            "fieldtype": "Section Break",
            "insert_after": "via_customer_portal",
            "collapsible": 1,
            "collapsible_depends_on": "custom_external_reference"
        },
        {
            "fieldname": "custom_external_reference",
            "label": "External Reference ID",
            "fieldtype": "Data",
            "insert_after": "external_integration_section",
            "read_only": 1,
            "in_list_view": 0,
            "description": "Reference ID from external system (e.g., HMIS issue ID)"
        },
        {
            "fieldname": "custom_hmis_module",
            "label": "HMIS Module",
            "fieldtype": "Data",
            "insert_after": "custom_external_reference",
            "read_only": 1,
            "in_list_view": 0,
            "description": "HMIS module that raised this ticket"
        },
        {
            "fieldname": "column_break_external",
            "fieldtype": "Column Break",
            "insert_after": "custom_hmis_module"
        },
        {
            "fieldname": "custom_external_system",
            "label": "External System",
            "fieldtype": "Select",
            "insert_after": "column_break_external",
            "options": "\nHMIS\nCRM\nOther",
            "default": "HMIS",
            "read_only": 1,
            "in_list_view": 0
        },
    ]

    for field in fields:
        create_custom_field("HD Ticket", field)


def create_custom_field(doctype, field_dict):
    """Create or update a custom field"""

    fieldname = field_dict.get("fieldname")

    # Check if field already exists
    existing = frappe.db.get_value(
        "Custom Field",
        {"dt": doctype, "fieldname": fieldname},
        "name"
    )

    if existing:
        print(f"  ↻ Updating {doctype}.{fieldname}")
        doc = frappe.get_doc("Custom Field", existing)
        doc.update(field_dict)
        doc.save()
    else:
        print(f"  + Creating {doctype}.{fieldname}")
        doc = frappe.get_doc({
            "doctype": "Custom Field",
            "dt": doctype,
            **field_dict
        })
        doc.insert()


if __name__ == "__main__":
    install()
