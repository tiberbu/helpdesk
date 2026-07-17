import frappe


@frappe.whitelist(allow_guest=True)
def confirm(key: str, answer: str):
	"""
	Handle customer Yes/No resolution response.
	Called either via email link (guest, redirects) or via portal call() (authenticated, returns JSON).
	answer: "yes" → close ticket, "no" → reopen ticket
	"""
	if answer not in ("yes", "no"):
		frappe.throw("Invalid response.")

	ticket_name = frappe.db.get_value("HD Ticket", {"key": key}, "name")
	if not ticket_name:
		frappe.throw("Invalid or expired confirmation link.")

	ticket_doc = frappe.get_doc("HD Ticket", ticket_name)

	if ticket_doc.status_category not in ("Resolved",):
		# Already acted on — return gracefully
		if frappe.session.user and frappe.session.user != "Guest":
			return {"status": "already_handled", "ticket": ticket_name}
		return _redirect(ticket_name, already_handled=True)

	new_status = "Closed" if answer == "yes" else "Open"
	frappe.db.set_value("HD Ticket", ticket_name, "status", new_status)
	frappe.db.commit()

	# If called from portal (authenticated), return JSON — caller handles UI
	if frappe.session.user and frappe.session.user != "Guest":
		return {"status": "ok", "new_status": new_status, "ticket": ticket_name}

	# If called from email link (guest), redirect to portal with message
	closed = answer == "yes"
	return _redirect(ticket_name, closed=closed)


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
