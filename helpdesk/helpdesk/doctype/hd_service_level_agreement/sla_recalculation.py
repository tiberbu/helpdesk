# Copyright (c) 2026, Frappe Technologies Pvt. Ltd. and contributors
# For license information, please see license.txt

"""SLA recalculation background job.

Processes all open tickets in batches of 100, recomputing response_by and
resolution_by using the business-hours-aware SLA calculator.

Usage
-----
On demand (admin):
    frappe.enqueue(
        "helpdesk.helpdesk.doctype.hd_service_level_agreement.sla_recalculation"
        ".recalculate_sla_for_open_tickets",
        queue="long",
        timeout=300,
    )

Via whitelisted API:
    POST /api/method/helpdesk.helpdesk.doctype.hd_service_level_agreement
         .sla_recalculation.enqueue_sla_recalculation
"""

import frappe
from frappe import _
from frappe.utils import now_datetime, get_datetime

_BATCH_SIZE = 100
_QUEUE = "long"
_JOB_TIMEOUT = 300  # seconds

# Redis lock key — prevents concurrent recalculation runs
_LOCK_KEY = "sla:recalc:running"
_LOCK_TTL = 600  # 10 minutes max hold


@frappe.whitelist()
def enqueue_sla_recalculation():
    """Enqueue the SLA recalculation background job (admin/agent-manager only)."""
    frappe.only_for(["System Manager", "Agent Manager"])
    frappe.enqueue(
        "helpdesk.helpdesk.doctype.hd_service_level_agreement.sla_recalculation"
        ".recalculate_sla_for_open_tickets",
        queue=_QUEUE,
        timeout=_JOB_TIMEOUT,
        is_async=True,
    )
    return {"message": _("SLA recalculation enqueued.")}


def recalculate_sla_for_open_tickets():
    """Recalculate SLA deadlines for all open tickets.

    Iterates in batches of 100 to keep memory bounded and stay within the
    5-second target for 1000 tickets (NFR-P-04).  Redis caching inside the
    SLA controller ensures service-day config is loaded once per SLA, not
    once per ticket.
    """
    # Acquire run lock to avoid concurrent overlapping recalculations
    cache = frappe.cache()
    if cache.get_value(_LOCK_KEY):
        frappe.log_error(
            title="SLA Recalculation: already running, skipping this invocation",
            message="Another recalculation job is still active.",
        )
        return

    cache.set_value(_LOCK_KEY, 1, expires_in_sec=_LOCK_TTL)
    try:
        _do_recalculate()
    finally:
        cache.delete_value(_LOCK_KEY)


def _do_recalculate():
    """Inner function: iterate open tickets and update SLA fields."""
    # Identify status categories that are "active" (not resolved/closed)
    paused_categories = set(
        frappe.db.get_all("HD Ticket Status", {"category": "Paused"}, pluck="name") or []
    )
    closed_categories = set(
        frappe.db.get_all("HD Ticket Status", {"category": ["in", ["Resolved", "Closed"]]}, pluck="name") or []
    )

    # SLA document cache: sla_name -> HDServiceLevelAgreement doc
    sla_doc_cache: dict = {}

    offset = 0
    total_processed = 0

    while True:
        tickets = frappe.db.get_all(
            "HD Ticket",
            filters={
                "sla": ["is", "set"],
                "status": ["not in", list(closed_categories)],
            },
            fields=[
                "name", "sla", "priority", "status",
                "service_level_agreement_creation",
                "first_responded_on", "resolution_date",
                "total_hold_time", "on_hold_since",
                "response_by", "resolution_by",
                "agreement_status",
            ],
            limit_page_length=_BATCH_SIZE,
            limit_start=offset,
            order_by="creation asc",
        )

        if not tickets:
            break

        for ticket in tickets:
            try:
                _recalculate_ticket(ticket, sla_doc_cache, paused_categories)
            except Exception:
                frappe.log_error(
                    title=f"SLA Recalculation: error on ticket {ticket['name']}",
                    message=frappe.get_traceback(),
                )

        total_processed += len(tickets)
        offset += _BATCH_SIZE

        if len(tickets) < _BATCH_SIZE:
            break  # Last batch

    frappe.logger().info(f"SLA recalculation complete: {total_processed} tickets processed.")


def _recalculate_ticket(ticket: dict, sla_doc_cache: dict, paused_categories: set):
    """Recalculate and persist SLA deadlines for a single ticket."""
    sla_name = ticket["sla"]
    if not sla_name:
        return

    # Load and cache the SLA document
    if sla_name not in sla_doc_cache:
        sla_doc_cache[sla_name] = frappe.get_doc("HD Service Level Agreement", sla_name)
    sla = sla_doc_cache[sla_name]

    start_at = ticket.get("service_level_agreement_creation")
    if not start_at:
        return

    priority = ticket.get("priority")
    if not priority:
        return

    # Recompute response_by and resolution_by
    new_response_by = sla.calc_time(start_at, priority, "response_time")
    new_resolution_by = sla.calc_time(
        start_at,
        priority,
        "resolution_time",
        hold_time=ticket.get("total_hold_time") or 0,
    )

    # Determine updated agreement_status
    now = now_datetime()
    is_paused = ticket.get("status") in paused_categories

    if is_paused:
        new_agreement_status = "Paused"
    elif ticket.get("resolution_date"):
        resolution_failed = get_datetime(new_resolution_by) < get_datetime(ticket["resolution_date"])
        new_agreement_status = "Failed" if resolution_failed else "Fulfilled"
    elif not ticket.get("first_responded_on"):
        response_failed = get_datetime(new_response_by) < now
        new_agreement_status = "Failed" if response_failed else "First Response Due"
    else:
        resolution_failed = get_datetime(new_resolution_by) < now
        new_agreement_status = "Failed" if resolution_failed else "Resolution Due"

    # Persist only changed fields to avoid spurious history entries
    update_fields = {}
    if ticket.get("response_by") != new_response_by:
        update_fields["response_by"] = new_response_by
    if ticket.get("resolution_by") != new_resolution_by:
        update_fields["resolution_by"] = new_resolution_by
    if ticket.get("agreement_status") != new_agreement_status:
        update_fields["agreement_status"] = new_agreement_status

    if update_fields:
        frappe.db.set_value("HD Ticket", ticket["name"], update_fields)
