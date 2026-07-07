import frappe

CUSTOMER_NOTIFICATION_TYPES = ["Ticket Reply", "Ticket Status Change"]


@frappe.whitelist()
def get_customer_notifications():
    """Return notifications for the logged-in customer. Safe for any authenticated user."""
    user = frappe.session.user
    if user in ("Administrator", "Guest"):
        return []
    return frappe.get_all(
        "HD Notification",
        filters={
            "user_to": user,
            "notification_type": ["in", CUSTOMER_NOTIFICATION_TYPES],
        },
        fields=[
            "name", "creation", "message", "notification_type",
            "read", "reference_comment", "reference_ticket", "user_from",
        ],
        order_by="modified desc",
        ignore_permissions=True,
    )


@frappe.whitelist()
def clear_customer_notifications(ticket=None):
    """Mark customer notifications as read. Always scoped to session user."""
    user = frappe.session.user
    filters = {
        "user_to": user,
        "read": 0,
        "notification_type": ["in", CUSTOMER_NOTIFICATION_TYPES],
    }
    if ticket:
        filters["reference_ticket"] = ticket
    for name in frappe.get_all("HD Notification", filters=filters, pluck="name", ignore_permissions=True):
        frappe.db.set_value("HD Notification", name, "read", 1, update_modified=False)


def create_notification(
    user_to: str,
    notification_type: str,
    message: str,
    reference_ticket: str | None = None,
    user_from: str = "Administrator",
) -> None:
    """
    Insert an HD Notification record so it appears in the bell panel.
    Safe to call from schedulers — catches all exceptions.
    """
    try:
        if not user_to:
            return
        frappe.get_doc({
            "doctype": "HD Notification",
            "user_from": user_from,
            "user_to": user_to,
            "notification_type": notification_type,
            "message": message,
            "reference_ticket": reference_ticket,
            "read": 0,
        }).insert(ignore_permissions=True)
        frappe.db.commit()  # nosemgrep
    except Exception:
        frappe.log_error(frappe.get_traceback(), f"Failed to create {notification_type} notification for {user_to}")


@frappe.whitelist()
def clear(ticket: str | int | None = None, comment: str | None = None):
    """
    Mark notifications as read. No arguments will clear all notifications for `user`.

    :param ticket: Ticket to clear notifications for
    :param comment: Comment to clear notifications for
    """
    filters = {"user_to": frappe.session.user, "read": False}
    if ticket:
        filters["reference_ticket"] = ticket
    if comment:
        filters["reference_comment"] = comment
    for notification in frappe.get_all(
        "HD Notification", filters=filters, pluck="name"
    ):
        frappe.db.set_value(
            "HD Notification", notification, "read", 1, update_modified=False
        )
