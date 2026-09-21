import frappe
from frappe.custom.doctype.custom_field.custom_field import create_custom_fields


def execute():
	create_custom_fields(
		{
			"HD Settings": [
				{
					"fieldname": "sso_allowed_email_domains",
					"label": "SSO Allowed Email Domains",
					"fieldtype": "Small Text",
					"description": "Comma-separated list of email domains allowed to sign in via Microsoft SSO (e.g. tiberbu.com,tiberbu.app). Leave blank to allow any domain.",
				},
			]
		}
	)
