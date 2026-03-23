# Copyright (c) 2026, Frappe Technologies Pvt. Ltd. and contributors
# For license information, please see license.txt
"""
CSAT Survey scheduling background job.
Story 3.7 -- CSAT Survey Infrastructure and Delivery
AC #5, #9: hourly cron enqueues survey emails with frequency-limit checking.
"""
import json

import frappe
from frappe.utils import add_days, now_datetime

from helpdesk.utils import generate_csat_token


def send_pending_surveys() -> None:
	"""Hourly cron: find resolved tickets eligible for CSAT survey and enqueue emails.

	Guards:
	- ``csat_enabled`` must be 1 in HD Settings (AC #1 / AR-06).
	- Ticket must have been resolved at least ``csat_delay_hours`` hours ago.
	- No existing HD CSAT Response with ``survey_sent_at`` set for this ticket.
	- Customer email must not be in the unsubscribed list (AC #6).
	- Customer must not have received a survey in the last ``csat_frequency_days`` days (AC #5).
	"""
	settings = frappe.db.get_singles_dict("HD Settings")

	if not settings.get("csat_enabled"):
		return  # Feature flag off

	delay_hours = int(settings.get("csat_delay_hours") or 24)
	frequency_days = int(settings.get("csat_frequency_days") or 7)
	expiry_days = int(settings.get("csat_token_expiry_days") or 7)

	# Cutoff: tickets resolved at least delay_hours ago
	cutoff_dt = frappe.utils.add_to_date(now_datetime(), hours=-delay_hours)

	# Load unsubscribed emails once
	raw_unsub = settings.get("csat_unsubscribed_emails")
	try:
		unsubscribed_emails: set = set(json.loads(raw_unsub) if raw_unsub else [])
	except (ValueError, TypeError):
		unsubscribed_emails = set()

	# Find resolved tickets modified (resolved) before the cutoff
	# "Resolved" category statuses
	resolved_statuses = frappe.db.get_all(
		"HD Ticket Status",
		filters={"category": "Resolved"},
		pluck="name",
	)
	if not resolved_statuses:
		return

	tickets = frappe.db.get_all(
		"HD Ticket",
		filters={
			"status": ["in", resolved_statuses],
			"modified": ["<=", cutoff_dt],
		},
		fields=["name", "raised_by", "modified"],
		order_by="modified asc",
		limit=200,  # process up to 200 per run to avoid timeouts
	)

	if not tickets:
		return

	frequency_cutoff = add_days(now_datetime(), -frequency_days)

	for ticket in tickets:
		customer_email = ticket.get("raised_by")
		if not customer_email:
			continue

		# Skip unsubscribed customers
		if customer_email in unsubscribed_emails:
			continue

		# Skip if a survey was already sent for this exact ticket
		already_sent = frappe.db.exists(
			"HD CSAT Response",
			{"ticket": ticket["name"], "survey_sent_at": ["!=", None]},
		)
		if already_sent:
			continue

		# Frequency limit: skip if customer received ANY survey recently (AC #5)
		recent = frappe.db.get_all(
			"HD CSAT Response",
			filters={
				"customer_email": customer_email,
				"survey_sent_at": [">", frequency_cutoff],
			},
			limit=1,
		)
		if recent:
			continue

		# Generate token and create the HD CSAT Response record
		token = generate_csat_token(ticket["name"], customer_email, expiry_days)
		try:
			response_doc = frappe.get_doc({
				"doctype": "HD CSAT Response",
				"ticket": ticket["name"],
				"customer_email": customer_email,
				"token": token,
				"token_used": 0,
				"survey_sent_at": now_datetime(),
			})
			response_doc.insert(ignore_permissions=True)
			frappe.db.commit()  # nosemgrep
		except Exception:
			frappe.log_error(
				title="CSAT Survey Error",
				message=f"Failed to create HD CSAT Response for ticket {ticket['name']}",
			)
			continue

		# Enqueue the email send (long queue — not time-critical)
		frappe.enqueue(
			"helpdesk.helpdesk.doctype.hd_csat_response.csat_scheduler._send_csat_email",
			queue="long",
			timeout=120,
			ticket_id=ticket["name"],
			csat_response_name=response_doc.name,
		)


def _send_csat_email(ticket_id: str, csat_response_name: str) -> None:
	"""Fetch template, render HTML email, and send via frappe.sendmail.

	:param ticket_id: HD Ticket name.
	:param csat_response_name: HD CSAT Response name.
	"""
	try:
		response = frappe.get_doc("HD CSAT Response", csat_response_name)
		ticket = frappe.get_doc("HD Ticket", ticket_id)

		# Fetch survey template: brand-specific first, then default fallback
		from helpdesk.helpdesk.doctype.hd_csat_survey_template.hd_csat_survey_template import (
			get_default_template,
		)
		template = _get_brand_template(ticket) or get_default_template()

		base_url = frappe.utils.get_url()

		# Render Jinja template
		html = frappe.render_template(
			"helpdesk/templates/csat_survey.html",
			{
				"subject": template.subject,
				"intro_text": template.intro_text,
				"logo_url": template.logo_url or "",
				"primary_color": template.primary_color or "#4F46E5",
				"ticket_id": ticket_id,
				"ticket_subject": ticket.subject or "",
				"token": response.token,
				"base_url": base_url,
			},
		)

		frappe.sendmail(
			recipients=[response.customer_email],
			subject=template.subject,
			message=html,
			reference_doctype="HD CSAT Response",
			reference_name=csat_response_name,
			now=True,
		)
	except Exception:
		frappe.log_error(
			title="CSAT Survey Error",
			message=f"Failed to send CSAT email for ticket {ticket_id} (response {csat_response_name})",
		)


def _get_brand_template(ticket) -> "frappe._dict | None":
	"""Return the CSAT survey template linked to the ticket's brand, or None.

	Looks up ``HD Brand.csat_template`` for the ticket's brand, then fetches
	that template's fields.  Returns ``None`` when the ticket has no brand, the
	brand has no template, or the template document does not exist.
	"""
	brand_name = getattr(ticket, "brand", None)
	if not brand_name:
		return None

	if not frappe.db.exists("DocType", "HD Brand"):
		return None

	csat_template_name = frappe.db.get_value("HD Brand", brand_name, "csat_template")
	if not csat_template_name:
		return None

	template = frappe.db.get_value(
		"HD CSAT Survey Template",
		csat_template_name,
		["template_name", "subject", "intro_text", "logo_url", "primary_color"],
		as_dict=True,
	)
	return template or None
