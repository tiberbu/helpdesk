# Copyright (c) 2026, Frappe Technologies Pvt. Ltd. and contributors
# For license information, please see license.txt

import frappe
from frappe import _
from frappe.utils import now_datetime, get_datetime

from helpdesk.utils import is_agent

# Maps the user-facing link type to the inverse type stored on the remote ticket
INVERSE_LINK_TYPE = {
	"Related to": "Related to",
	"Caused by": "Causes",
	"Causes": "Caused by",
	"Duplicate of": "Duplicated by",
	"Duplicated by": "Duplicate of",
}

# Status name to use when auto-closing a duplicate ticket
DUPLICATE_STATUS = "Duplicate"
FALLBACK_CLOSE_STATUS = "Resolved"


@frappe.whitelist()
def link_tickets(ticket_a: str, ticket_b: str, link_type: str) -> dict:
	"""
	Create a bidirectional link between ticket_a and ticket_b.

	For "Duplicate of" link type, auto-closes ticket_a and adds a system comment.
	Returns {"success": True} on success.

	Raises frappe.ValidationError on invalid input or duplicate links.
	Raises frappe.PermissionError if caller lacks Agent role.
	"""
	if not is_agent():
		frappe.throw(_("Not permitted"), frappe.PermissionError)

	# Validate link type
	valid_types = list(INVERSE_LINK_TYPE.keys())
	if link_type not in valid_types:
		frappe.throw(
			_("Invalid link type '{0}'. Must be one of: {1}").format(
				link_type, ", ".join(["Related to", "Caused by", "Duplicate of"])
			),
			frappe.ValidationError,
		)

	# Prevent self-linking
	if ticket_a == ticket_b:
		frappe.throw(_("Cannot link a ticket to itself."), frappe.ValidationError)

	# Ensure both tickets exist
	if not frappe.db.exists("HD Ticket", ticket_a):
		frappe.throw(_("Ticket {0} not found.").format(ticket_a), frappe.DoesNotExistError)
	if not frappe.db.exists("HD Ticket", ticket_b):
		frappe.throw(_("Ticket {0} not found.").format(ticket_b), frappe.DoesNotExistError)

	# Check for existing link in either direction
	_assert_no_existing_link(ticket_a, ticket_b)

	doc_a = frappe.get_doc("HD Ticket", ticket_a)
	doc_b = frappe.get_doc("HD Ticket", ticket_b)

	now = now_datetime()
	user = frappe.session.user

	# Create forward link on Ticket A
	doc_a.append(
		"related_tickets",
		{
			"ticket": ticket_b,
			"link_type": link_type,
			"linked_by": user,
			"linked_on": now,
		},
	)
	doc_a.flags.ignore_permissions = True
	doc_a.save()

	# Create reverse link on Ticket B
	inverse = INVERSE_LINK_TYPE.get(link_type, link_type)
	doc_b.append(
		"related_tickets",
		{
			"ticket": ticket_a,
			"link_type": inverse,
			"linked_by": user,
			"linked_on": now,
		},
	)
	doc_b.flags.ignore_permissions = True
	doc_b.save()

	# Auto-close for "Duplicate of"
	if link_type == "Duplicate of":
		_auto_close_duplicate(doc_a, doc_b)

	frappe.db.commit()  # nosemgrep

	return {"success": True}


@frappe.whitelist()
def unlink_tickets(ticket_a: str, ticket_b: str) -> dict:
	"""
	Remove all links between ticket_a and ticket_b in both directions.
	"""
	if not is_agent():
		frappe.throw(_("Not permitted"), frappe.PermissionError)

	doc_a = frappe.get_doc("HD Ticket", ticket_a)
	doc_b = frappe.get_doc("HD Ticket", ticket_b)

	# Remove all links from A → B
	doc_a.related_tickets = [r for r in doc_a.related_tickets if r.ticket != ticket_b]
	doc_a.flags.ignore_permissions = True
	doc_a.save()

	# Remove all links from B → A
	doc_b.related_tickets = [r for r in doc_b.related_tickets if r.ticket != ticket_a]
	doc_b.flags.ignore_permissions = True
	doc_b.save()

	frappe.db.commit()  # nosemgrep

	return {"success": True}


@frappe.whitelist()
def get_related_tickets(ticket: str) -> list:
	"""
	Return enriched related-ticket data for the given ticket.

	Each entry includes: name (child row name), ticket (linked ticket ID),
	link_type, linked_by, linked_on, ticket_subject, ticket_status.
	"""
	if not is_agent():
		frappe.throw(_("Not permitted"), frappe.PermissionError)

	child_rows = frappe.get_all(
		"HD Related Ticket",
		filters={"parent": ticket, "parenttype": "HD Ticket"},
		fields=["name", "ticket", "link_type", "linked_by", "linked_on"],
		order_by="linked_on asc",
	)

	if not child_rows:
		return []

	# Enrich with subject and status from linked tickets
	linked_ids = [r["ticket"] for r in child_rows]
	ticket_info = frappe.get_all(
		"HD Ticket",
		filters=[["name", "in", linked_ids]],
		fields=["name", "subject", "status"],
	)
	info_map = {str(t["name"]): t for t in ticket_info}

	for row in child_rows:
		info = info_map.get(str(row["ticket"]), {})
		row["ticket_subject"] = info.get("subject", "")
		row["ticket_status"] = info.get("status", "")

	return child_rows


def _assert_no_existing_link(ticket_a: str, ticket_b: str) -> None:
	"""Raise ValidationError if a link already exists between the two tickets (either direction)."""
	exists_ab = frappe.db.exists(
		"HD Related Ticket",
		{"parent": ticket_a, "parenttype": "HD Ticket", "ticket": ticket_b},
	)
	exists_ba = frappe.db.exists(
		"HD Related Ticket",
		{"parent": ticket_b, "parenttype": "HD Ticket", "ticket": ticket_a},
	)
	if exists_ab or exists_ba:
		frappe.throw(
			_("A link between {0} and {1} already exists.").format(ticket_a, ticket_b),
			frappe.ValidationError,
		)


@frappe.whitelist()
def flag_major_incident(ticket: str) -> dict:
	"""
	Flag or unflag a ticket as a major incident.

	Toggling on sets is_major_incident=1 and major_incident_flagged_at to now,
	and enqueues escalation notifications to major_incident_contacts.
	Toggling off clears both fields.

	Returns {"success": True, "is_major_incident": <new value>}.
	Raises frappe.PermissionError if caller lacks Agent role.
	"""
	if not is_agent():
		frappe.throw(_("Not permitted"), frappe.PermissionError)

	doc = frappe.get_doc("HD Ticket", ticket)

	if doc.is_major_incident:
		# Un-flag
		doc.is_major_incident = 0
		doc.major_incident_flagged_at = None
		doc.flags.ignore_permissions = True
		doc.save()
		frappe.db.commit()  # nosemgrep
		return {"success": True, "is_major_incident": 0}

	# Flag
	now = now_datetime()
	doc.is_major_incident = 1
	doc.major_incident_flagged_at = now
	doc.flags.ignore_permissions = True
	doc.save()

	frappe.enqueue(
		"helpdesk.api.incident._send_major_incident_notifications",
		queue="short",
		ticket=ticket,
	)

	frappe.db.commit()  # nosemgrep
	return {"success": True, "is_major_incident": 1}


@frappe.whitelist()
def propagate_update(ticket: str, message: str) -> dict:
	"""
	Post a public comment on the major incident ticket and on every
	directly linked ticket (HD Related Ticket child rows).

	Returns {"success": True, "count": <number of tickets updated>}.
	Raises frappe.PermissionError if caller lacks Agent role.
	Raises frappe.ValidationError if ticket is not flagged as a major incident.
	"""
	if not is_agent():
		frappe.throw(_("Not permitted"), frappe.PermissionError)

	if not frappe.db.get_value("HD Ticket", ticket, "is_major_incident"):
		frappe.throw(
			_("Ticket {0} is not a major incident.").format(ticket),
			frappe.ValidationError,
		)

	user = frappe.session.user
	message_escaped = frappe.utils.escape_html(message or "")

	def _post_comment(ref_ticket):
		comment = frappe.get_doc(
			{
				"doctype": "HD Ticket Comment",
				"reference_ticket": ref_ticket,
				"commented_by": user,
				"content": _(
					"[Major Incident Update from #{0}]: {1}"
				).format(ticket, message_escaped),
				"is_internal": 0,
				"is_pinned": 0,
			}
		)
		comment.insert(ignore_permissions=True)

	# Post on the major incident ticket itself
	_post_comment(ticket)

	# Post on all linked tickets
	linked_tickets = frappe.get_all(
		"HD Related Ticket",
		filters={"parent": ticket, "parenttype": "HD Ticket"},
		pluck="ticket",
	)
	for linked in linked_tickets:
		_post_comment(str(linked))

	frappe.db.commit()  # nosemgrep
	return {"success": True, "count": 1 + len(linked_tickets)}


@frappe.whitelist()
def get_major_incident_summary() -> list:
	"""
	Return all open major incidents with enriched data.

	Each entry includes: name, subject, status, major_incident_flagged_at,
	priority, linked_ticket_count, elapsed_minutes.
	"""
	if not is_agent():
		frappe.throw(_("Not permitted"), frappe.PermissionError)

	incidents = frappe.get_all(
		"HD Ticket",
		filters={"is_major_incident": 1},
		fields=["name", "subject", "status", "major_incident_flagged_at", "priority"],
		order_by="major_incident_flagged_at desc",
	)

	now = now_datetime()
	for inc in incidents:
		# Count linked tickets
		inc["linked_ticket_count"] = frappe.db.count(
			"HD Related Ticket",
			{"parent": inc["name"], "parenttype": "HD Ticket"},
		)

		# Elapsed time in minutes since flagged
		flagged_at = inc.get("major_incident_flagged_at")
		if flagged_at:
			delta = now - get_datetime(flagged_at)
			inc["elapsed_minutes"] = int(delta.total_seconds() / 60)
		else:
			inc["elapsed_minutes"] = 0

	return incidents


def _send_major_incident_notifications(ticket: str) -> None:
	"""
	Send email + in-app (Socket.IO) notifications to major_incident_contacts
	when a major incident is flagged.  Runs in a background job.
	"""
	settings = frappe.get_single("HD Settings")
	contacts_raw = getattr(settings, "major_incident_contacts", None) or ""

	emails = [e.strip() for e in contacts_raw.replace("\n", ",").split(",") if e.strip()]
	if not emails:
		return

	ticket_doc = frappe.get_doc("HD Ticket", ticket)
	ticket_url = f"/helpdesk/tickets/{ticket}"
	ticket_subject_escaped = frappe.utils.escape_html(ticket_doc.subject or str(ticket))
	ticket_link = f"<a href='{ticket_url}'>{ticket_subject_escaped} (#{ticket})</a>"

	subject = _("Major Incident Declared: #{0} — {1}").format(ticket, ticket_doc.subject or "")

	# Build simple email body (template may not exist in all envs)
	try:
		body = frappe.render_template(
			"helpdesk/templates/major_incident_alert.html",
			{"ticket": ticket_doc, "ticket_link": ticket_link},
		)
	except Exception:
		body = _(
			"A major incident has been declared: {0}.<br>Please review immediately."
		).format(ticket_link)

	for email in emails:
		# Email notification
		frappe.sendmail(
			recipients=[email],
			subject=subject,
			message=body,
			delayed=False,
		)

		# In-app realtime notification (Socket.IO room per agent email)
		frappe.publish_realtime(
			event="major_incident_declared",
			message={
				"ticket": ticket,
				"subject": ticket_doc.subject or "",
				"url": ticket_url,
			},
			room=f"agent:{email}",
		)


def _auto_close_duplicate(doc_a, doc_b) -> None:
	"""
	Set Ticket A's status to 'Duplicate' (or 'Resolved' as fallback) and add a
	system comment explaining the closure.
	"""
	# Determine which status to use
	target_status = (
		DUPLICATE_STATUS
		if frappe.db.exists("HD Ticket Status", DUPLICATE_STATUS)
		else FALLBACK_CLOSE_STATUS
	)

	doc_a.status = target_status
	doc_a.flags.ignore_permissions = True
	doc_a.save()

	# Add a public comment on Ticket A
	b_url = f"/helpdesk/tickets/{doc_b.name}"
	b_subject_escaped = frappe.utils.escape_html(doc_b.subject or doc_b.name)
	b_link = f"<a href='{b_url}'>{b_subject_escaped} ({doc_b.name})</a>"

	comment = frappe.get_doc(
		{
			"doctype": "HD Ticket Comment",
			"reference_ticket": doc_a.name,
			"commented_by": frappe.session.user,
			"content": _("This ticket has been closed as a duplicate of {0}.").format(b_link),
			"is_internal": 0,
			"is_pinned": 0,
		}
	)
	comment.insert(ignore_permissions=True)
