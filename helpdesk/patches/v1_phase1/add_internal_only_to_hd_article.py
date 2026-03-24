import frappe


def execute():
    """Add internal_only field to HD Article.

    Field is defined in the DocType JSON; this patch ensures the schema
    migration runs for existing installations.
    """
    frappe.reload_doc("helpdesk", "doctype", "hd_article")
