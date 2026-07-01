import frappe


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
