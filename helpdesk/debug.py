import frappe


def disable_test_smtp():
    """One-shot: disable the _Test Comm Account 1 default-outgoing fixture
    that ERPNext's test bootstrap left behind on support.tiberbu.app.
    The fixture points at smtp.example.com which fails DNS, crashing
    every request that flushes the email queue on commit.
    """
    name = "_Test Comm Account 1"
    if not frappe.db.exists("Email Account", name):
        print("Test account not found; nothing to do.")
        return

    before = frappe.db.get_value(
        "Email Account",
        name,
        ["default_outgoing", "enable_outgoing", "smtp_server"],
        as_dict=True,
    )
    print("Before:", before)

    doc = frappe.get_doc("Email Account", name)
    doc.default_outgoing = 0
    doc.enable_outgoing = 0
    doc.save(ignore_permissions=True)
    frappe.db.commit()

    after = frappe.db.get_value(
        "Email Account",
        name,
        ["default_outgoing", "enable_outgoing", "smtp_server"],
        as_dict=True,
    )
    print("After:", after)

    other_default = frappe.db.get_all(
        "Email Account",
        filters={"default_outgoing": 1},
        fields=["name", "email_id", "smtp_server"],
    )
    print("Other default_outgoing accounts:", other_default)
