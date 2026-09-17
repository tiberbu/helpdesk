import frappe


def notify_hd_ticket_assignment(doc, method=None):
    """Create an HD Notification when a ToDo assigns someone to an HD Ticket.

    frappe.desk.form.assign_to.add updates _assign via frappe.db.set_value
    (bypassing on_update), so we hook into ToDo.after_insert instead.
    Only fires for HD Ticket reference types and skips self-assignment.
    """
    if doc.reference_type != "HD Ticket":
        return
    if not doc.reference_name or not doc.allocated_to:
        return
    if doc.allocated_to == frappe.session.user:
        return

    try:
        frappe.get_doc({
            "doctype": "HD Notification",
            "user_from": frappe.session.user,
            "user_to": doc.allocated_to,
            "notification_type": "Assignment",
            "reference_ticket": doc.reference_name,
        }).insert(ignore_permissions=True)
    except Exception:
        frappe.log_error(
            title=f"HD Ticket: assignment notification failed for {doc.reference_name}",
            message=frappe.get_traceback(),
        )
