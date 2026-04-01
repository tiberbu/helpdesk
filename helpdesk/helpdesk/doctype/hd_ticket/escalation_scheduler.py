# Copyright (c) 2026, Frappe Technologies Pvt. Ltd. and contributors
# For license information, please see license.txt

"""
SLA Auto-Escalation Scheduler — runs every 5 minutes.

Finds open tickets where:
- ticket.support_level has auto_escalate_on_breach = True
- Ticket has had no agent response for > auto_escalate_minutes
- Ticket is not already at the highest support level
- Ticket has a valid parent_team to escalate to

For each matching ticket, performs auto-escalation using the shared
_perform_escalation() helper from helpdesk.api.escalation.
"""

import frappe
from frappe import _
from frappe.utils import now_datetime, add_to_date


def auto_escalate_tickets() -> None:
	"""
	Entry point called by the scheduler every 5 minutes.
	Enqueues individual ticket escalations to avoid blocking the scheduler.
	"""
	candidates = _find_auto_escalation_candidates()
	for ticket_name in candidates:
		frappe.enqueue(
			"helpdesk.helpdesk.doctype.hd_ticket.escalation_scheduler._auto_escalate_single",
			queue="short",
			ticket_name=ticket_name,
			job_id=f"auto_escalate_{ticket_name}",
			deduplicate=True,
		)


def _find_auto_escalation_candidates() -> list:
	"""
	Return list of ticket names that qualify for auto-escalation.

	Criteria:
	1. Ticket status is open (not Resolved/Closed/Duplicate/On Hold).
	2. Ticket has a support_level with auto_escalate_on_breach = 1.
	3. Ticket has had no agent response for > auto_escalate_minutes.
	4. There is a next support level (not the highest).
	5. The assigned team has a parent_team to escalate to.
	"""
	# Get all support levels that have auto_escalate_on_breach enabled
	auto_escalate_levels = frappe.get_all(
		"HD Support Level",
		filters={"auto_escalate_on_breach": 1},
		fields=["name", "level_order", "auto_escalate_minutes"],
	)
	if not auto_escalate_levels:
		return []

	# Highest level_order in the system (to skip terminal level tickets)
	max_order = frappe.db.sql(
		"SELECT MAX(level_order) FROM `tabHD Support Level`"
	)[0][0] or 0

	candidates = []
	now = now_datetime()

	for level in auto_escalate_levels:
		# Skip if already at the highest level
		if level["level_order"] >= max_order:
			continue

		minutes = level["auto_escalate_minutes"] or 60
		cutoff = add_to_date(now, minutes=-minutes)

		# Find open tickets at this support level with no recent agent response
		tickets = frappe.get_all(
			"HD Ticket",
			filters={
				"support_level": level["name"],
				"status": ["not in", ["Resolved", "Closed", "Duplicate"]],
				"agent_group": ["is", "set"],
			},
			or_filters=[
				["last_agent_response", "<", cutoff],
				["last_agent_response", "is", "not set"],
			],
			fields=["name", "agent_group"],
		)

		for ticket in tickets:
			# Verify the assigned team has a parent_team
			if ticket.get("agent_group"):
				parent_team = frappe.db.get_value(
					"HD Team", ticket["agent_group"], "parent_team"
				)
				if parent_team:
					candidates.append(ticket["name"])

	return candidates


def _auto_escalate_single(ticket_name: str) -> None:
	"""
	Perform auto-escalation for a single ticket.
	Runs as a background job. Handles its own exception to prevent scheduler crashes.
	"""
	try:
		# Re-fetch the ticket fresh (it may have changed since the scan)
		doc = frappe.get_doc("HD Ticket", ticket_name)

		# Re-validate the ticket is still eligible (guard against race conditions)
		if not doc.support_level:
			return
		if doc.status in ("Resolved", "Closed", "Duplicate"):
			return

		from helpdesk.api.escalation import _resolve_escalation_targets, _perform_escalation

		# Run as system user for background job
		frappe.set_user("Administrator")

		try:
			from_level_name, from_team, to_level, to_team = _resolve_escalation_targets(doc)
		except frappe.ValidationError:
			# Ticket is no longer eligible (e.g. level changed, team changed)
			return

		level_doc = frappe.get_doc("HD Support Level", doc.support_level)
		minutes = level_doc.auto_escalate_minutes or 60
		reason = _(
			"Auto-escalated due to no agent response within {0} minutes at {1}"
		).format(minutes, from_level_name)

		_perform_escalation(
			doc=doc,
			from_level_name=from_level_name,
			to_level=to_level,
			from_team=from_team,
			to_team=to_team,
			reason=reason,
			by="system",
			auto=True,
		)

		frappe.db.commit()  # nosemgrep

	except Exception:
		frappe.log_error(
			title=f"Auto-escalation failed for ticket {ticket_name}",
			message=frappe.get_traceback(),
		)
