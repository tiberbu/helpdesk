# Copyright (c) 2026, Frappe Technologies Pvt. Ltd. and contributors
# For license information, please see license.txt

"""Trigger type registry for the automation engine.

Maps Frappe doc event hook names to the automation trigger_type values
stored on HD Automation Rule records.
"""

# Ordered list of supported trigger types (also the valid Select options
# on the HD Automation Rule DocType).
TRIGGER_TYPES = [
    "ticket_created",
    "ticket_updated",
    "ticket_assigned",
    "ticket_resolved",
    "ticket_reopened",
]

# Maps Frappe doc event -> trigger_type.
# after_insert fires once on document creation (ticket_created).
# on_update fires on every save after creation (ticket_updated, and
# the specialised ticket_assigned / ticket_resolved / ticket_reopened
# variants that the engine derives from field-change context).
DOC_EVENT_TO_TRIGGER = {
    "after_insert": "ticket_created",
    "on_update": "ticket_updated",
}


def get_trigger_type_for_event(event: str) -> str | None:
    """Return the base trigger_type for a Frappe doc event name."""
    return DOC_EVENT_TO_TRIGGER.get(event)


def resolve_trigger_type(doc, method: str) -> list[str]:
    """Resolve all applicable trigger_types for a ticket doc event.

    For ``on_update`` events we inspect the doc for change context so we
    can fire the more precise variants (ticket_assigned, ticket_resolved,
    ticket_reopened) in addition to the generic ticket_updated trigger.

    Returns a list so that rules registered on ``ticket_updated`` always
    fire alongside any specialised trigger — e.g. a resolution event fires
    both ``ticket_resolved`` and ``ticket_updated`` rules.

    Args:
        doc: The HD Ticket document.
        method: Frappe doc event name (e.g. "after_insert", "on_update").

    Returns:
        List of resolved trigger_type strings.
    """
    if method == "after_insert":
        return ["ticket_created"]

    # Derive specialised trigger for on_update
    if method == "on_update":
        status = getattr(doc, "status", None)
        if status:
            if isinstance(status, str):
                status_name = status
            else:
                status_name = getattr(status, "name", str(status))

            # Resolved/closed states — also fire ticket_updated
            if status_name in ("Resolved", "Closed"):
                return ["ticket_resolved", "ticket_updated"]

            # Re-opened: was previously resolved/closed, now active — also fire ticket_updated
            if hasattr(doc, "_doc_before_save"):
                prev = doc._doc_before_save
                if prev:
                    prev_status = getattr(prev, "status", None)
                    if prev_status in ("Resolved", "Closed") and status_name not in (
                        "Resolved",
                        "Closed",
                    ):
                        return ["ticket_reopened", "ticket_updated"]

        # Agent assignment change — also fire ticket_updated
        if hasattr(doc, "_doc_before_save") and doc._doc_before_save:
            prev = doc._doc_before_save
            prev_assignees = getattr(prev, "_assign", None) or "[]"
            curr_assignees = getattr(doc, "_assign", None) or "[]"
            if prev_assignees != curr_assignees:
                return ["ticket_assigned", "ticket_updated"]

        return ["ticket_updated"]

    base = DOC_EVENT_TO_TRIGGER.get(method, "ticket_updated")
    return [base]
