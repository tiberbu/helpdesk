import frappe


@frappe.whitelist(allow_guest=True)
def confirm(key: str, answer: str):
	"""
	Called from the resolution confirmation email links.
	answer: "yes" → close ticket, "no" → reopen ticket
	"""
	if answer not in ("yes", "no"):
		frappe.throw("Invalid response.")

	ticket_name = frappe.db.get_value("HD Ticket", {"key": key}, "name")
	if not ticket_name:
		frappe.throw("Invalid or expired confirmation link.")

	ticket = frappe.get_doc("HD Ticket", ticket_name)

	if ticket.status_category not in ("Resolved",):
		# Already acted on or re-opened by agent — just redirect gracefully
		return _redirect(ticket_name, already_handled=True)

	if answer == "yes":
		frappe.db.set_value("HD Ticket", ticket_name, "status", "Closed")
		frappe.db.commit()
		return _redirect(ticket_name, closed=True)
	else:
		frappe.db.set_value("HD Ticket", ticket_name, "status", "Open")
		frappe.db.commit()
		return _redirect(ticket_name, closed=False)


def _redirect(ticket_name: str, closed: bool = False, already_handled: bool = False):
	if already_handled:
		msg = "This ticket has already been updated."
	elif closed:
		msg = "Thank you! Your ticket has been closed."
	else:
		msg = "Your ticket has been reopened. Our team will follow up shortly."

	frappe.local.response["type"] = "redirect"
	frappe.local.response["location"] = (
		f"/helpdesk/my-tickets/{ticket_name}?resolution_msg={frappe.utils.cstr(msg)}"
	)
