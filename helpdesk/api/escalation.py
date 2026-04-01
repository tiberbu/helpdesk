# Copyright (c) 2026, Frappe Technologies Pvt. Ltd. and contributors
# For license information, please see license.txt

"""
Escalation chain API for County-4 support hierarchy.

Provides:
- escalate_ticket(ticket, reason) — manual escalation by agent
- de_escalate_ticket(ticket, reason, target_team) — de-escalation by higher-tier agent
- get_escalation_path(ticket) — return audit trail of escalations
- _perform_escalation(...) — shared internal logic used by API + scheduler
"""

import json

import frappe
from frappe import _
from frappe.utils import now_datetime

from helpdesk.utils import is_agent


# ---------------------------------------------------------------------------
# Public whitelisted endpoints
# ---------------------------------------------------------------------------


@frappe.whitelist()
def escalate_ticket(ticket: str, reason: str) -> dict:
	"""
	Manually escalate a ticket to the next support level.

	Steps:
	1. Verify caller is an agent.
	2. Check ticket.support_level.allow_escalation_to_next.
	3. Find next support level (level_order + 1).
	4. Find parent_team of current assigned team.
	5. Reassign ticket to parent team.
	6. Update support_level + escalation_count.
	7. Add internal note.
	8. Append to escalation_path audit trail.
	9. Notify new team.

	Returns {"success": True, "new_support_level": "<name>", "new_team": "<name>"}.
	"""
	if not is_agent():
		frappe.throw(_("Not permitted"), frappe.PermissionError)

	if not reason or not reason.strip():
		frappe.throw(_("Escalation reason is required."), frappe.ValidationError)

	doc = frappe.get_doc("HD Ticket", ticket)

	from_level_name, from_team, to_level, to_team = _resolve_escalation_targets(doc)

	_perform_escalation(
		doc=doc,
		from_level_name=from_level_name,
		to_level=to_level,
		from_team=from_team,
		to_team=to_team,
		reason=reason,
		by=frappe.session.user,
		auto=False,
	)

	frappe.db.commit()  # nosemgrep

	return {
		"success": True,
		"new_support_level": to_level.name,
		"new_team": to_team,
	}


@frappe.whitelist()
def de_escalate_ticket(ticket: str, reason: str, target_team: str = None) -> dict:
	"""
	De-escalate a ticket back to a lower support level.

	The previous level is determined from the escalation_path audit trail (one step back).
	If target_team is not specified, the child team is derived from the previous escalation entry.

	Returns {"success": True, "new_support_level": "<name>", "new_team": "<name>"}.
	"""
	if not is_agent():
		frappe.throw(_("Not permitted"), frappe.PermissionError)

	if not reason or not reason.strip():
		frappe.throw(_("De-escalation reason is required."), frappe.ValidationError)

	doc = frappe.get_doc("HD Ticket", ticket)

	# Determine current and previous levels from audit trail
	path = _load_escalation_path(doc)
	if not path:
		frappe.throw(
			_("No escalation history found for ticket {0}.").format(ticket),
			frappe.ValidationError,
		)

	last_entry = path[-1]
	from_level_name = last_entry.get("to_level") or doc.support_level
	to_level_name = last_entry.get("from_level")

	if not to_level_name:
		frappe.throw(
			_("Cannot determine previous support level for de-escalation."),
			frappe.ValidationError,
		)

	to_level_doc = frappe.get_doc("HD Support Level", to_level_name)

	# Determine team to assign to
	resolved_team = target_team or last_entry.get("from_team") or doc.agent_group

	user = frappe.session.user
	now = now_datetime()

	# Update ticket fields
	doc.support_level = to_level_name
	doc.agent_group = resolved_team or doc.agent_group
	doc.flags.ignore_permissions = True
	doc.save()

	# Add internal note
	_add_internal_note(
		ticket=ticket,
		content=_(
			"De-escalated from {0} to {1} by {2}. Reason: {3}"
		).format(from_level_name, to_level_name, user, reason),
	)

	# Append to audit trail
	entry = {
		"from_level": from_level_name,
		"to_level": to_level_name,
		"from_team": doc.agent_group,
		"to_team": resolved_team,
		"by": user,
		"reason": reason,
		"auto": False,
		"direction": "de-escalation",
		"at": str(now),
	}
	path.append(entry)
	_save_escalation_path(doc, path)

	# Notify new (lower) team
	frappe.enqueue(
		"helpdesk.api.escalation._notify_team",
		queue="short",
		ticket=ticket,
		team=resolved_team,
		message=_("Ticket #{0} has been de-escalated to your team.").format(ticket),
	)

	frappe.db.commit()  # nosemgrep

	return {
		"success": True,
		"new_support_level": to_level_name,
		"new_team": resolved_team,
	}


@frappe.whitelist()
def get_escalation_path(ticket: str) -> list:
	"""Return the escalation audit trail for the given ticket."""
	if not is_agent():
		frappe.throw(_("Not permitted"), frappe.PermissionError)

	doc = frappe.get_doc("HD Ticket", ticket)
	return _load_escalation_path(doc)


# ---------------------------------------------------------------------------
# Internal shared helpers
# ---------------------------------------------------------------------------


def _resolve_escalation_targets(doc):
	"""
	Validate that the ticket can be escalated and return:
	  (from_level_name, from_team, to_level_doc, to_team_name)

	Raises ValidationError/PermissionError if escalation is blocked.
	"""
	if not doc.support_level:
		frappe.throw(
			_("Ticket {0} has no support level assigned. Cannot escalate.").format(doc.name),
			frappe.ValidationError,
		)

	from_level = frappe.get_doc("HD Support Level", doc.support_level)

	if not from_level.allow_escalation_to_next:
		frappe.throw(
			_("This tier does not allow escalation"),
			frappe.ValidationError,
		)

	# Find next level (level_order + 1)
	next_level = frappe.get_all(
		"HD Support Level",
		filters={"level_order": from_level.level_order + 1},
		fields=["name", "level_order", "display_name", "allow_escalation_to_next"],
		limit=1,
	)
	if not next_level:
		frappe.throw(
			_("No next support level found above {0}.").format(from_level.level_name),
			frappe.ValidationError,
		)
	to_level = frappe.get_doc("HD Support Level", next_level[0]["name"])

	# Find parent_team of current assigned team
	current_team = doc.agent_group
	if not current_team:
		frappe.throw(
			_("Ticket {0} has no assigned team. Cannot escalate.").format(doc.name),
			frappe.ValidationError,
		)

	parent_team = frappe.db.get_value("HD Team", current_team, "parent_team")
	if not parent_team:
		frappe.throw(
			_("Team '{0}' has no parent team configured. Cannot escalate.").format(current_team),
			frappe.ValidationError,
		)

	return from_level.level_name, current_team, to_level, parent_team


def _perform_escalation(
	doc,
	from_level_name: str,
	to_level,
	from_team: str,
	to_team: str,
	reason: str,
	by: str,
	auto: bool = False,
) -> None:
	"""
	Core escalation logic shared by manual and auto-escalation:
	1. Reassign ticket to parent team (to_team).
	2. Update support_level to to_level.
	3. Increment escalation_count.
	4. Add internal note.
	5. Append to escalation_path audit trail.
	6. Enqueue team notification.
	"""
	now = now_datetime()

	doc.agent_group = to_team
	doc.support_level = to_level.name
	doc.escalation_count = (doc.escalation_count or 0) + 1
	doc.flags.ignore_permissions = True
	doc.save()

	# Internal note
	if auto:
		note_content = _(
			"Auto-escalated from {0} to {1} due to no agent response within the configured time. Reason: {2}"
		).format(from_level_name, to_level.level_name, reason)
	else:
		note_content = _(
			"Escalated from {0} to {1} by {2}. Reason: {3}"
		).format(from_level_name, to_level.level_name, by, reason)

	_add_internal_note(ticket=str(doc.name), content=note_content)

	# Append to escalation_path audit trail
	path = _load_escalation_path(doc)
	entry = {
		"from_level": from_level_name,
		"to_level": to_level.level_name,
		"from_team": from_team,
		"to_team": to_team,
		"by": by if not auto else "system",
		"reason": reason,
		"auto": auto,
		"direction": "escalation",
		"at": str(now),
	}
	path.append(entry)
	_save_escalation_path(doc, path)

	# Notify new team
	frappe.enqueue(
		"helpdesk.api.escalation._notify_team",
		queue="short",
		ticket=str(doc.name),
		team=to_team,
		message=_("Ticket #{0} has been escalated to your team ({1}).").format(
			doc.name, to_level.level_name
		),
	)


def _load_escalation_path(doc) -> list:
	"""Parse escalation_path JSON field; return list (empty if blank/invalid)."""
	raw = getattr(doc, "escalation_path", None) or ""
	if not raw:
		return []
	try:
		return json.loads(raw)
	except (ValueError, TypeError):
		return []


def _save_escalation_path(doc, path: list) -> None:
	"""Persist escalation_path JSON to the ticket without triggering full validation."""
	frappe.db.set_value(
		"HD Ticket",
		doc.name,
		"escalation_path",
		json.dumps(path, default=str),
		update_modified=False,
	)


def _add_internal_note(ticket: str, content: str) -> None:
	"""Insert an internal HD Ticket Comment."""
	comment = frappe.get_doc(
		{
			"doctype": "HD Ticket Comment",
			"reference_ticket": ticket,
			"commented_by": frappe.session.user,
			"content": content,
			"is_internal": 1,
			"is_pinned": 0,
		}
	)
	comment.insert(ignore_permissions=True)


def _notify_team(ticket: str, team: str, message: str) -> None:
	"""
	Send in-app + email notification to members of the given HD Team when a ticket
	is escalated/de-escalated to them.  Runs as a background job.
	"""
	members = frappe.get_all(
		"HD Team Member",
		filters={"parent": team, "parenttype": "HD Team"},
		pluck="user",
	)
	if not members:
		return

	ticket_url = f"/helpdesk/tickets/{ticket}"

	for user_email in members:
		# In-app realtime notification
		frappe.publish_realtime(
			event="escalation_notification",
			message={
				"ticket": ticket,
				"team": team,
				"message": message,
				"url": ticket_url,
			},
			room=f"user:{user_email}",
		)

		# Email notification
		frappe.sendmail(
			recipients=[user_email],
			subject=_("Ticket #{0} assigned to your team").format(ticket),
			message=f"{message}<br><a href='{ticket_url}'>View Ticket #{ticket}</a>",
			delayed=False,
		)
