"""
Warns implementers when they're about to raise a ticket that's similar to
one already reported — not scoped to the same facility or raiser, since the
same underlying issue can legitimately be reported by many different
facilities/counties at once (e.g. a system-wide outage).

Uses the existing SQLite FTS search index, restricted to still-open tickets.
"""

import re

import frappe

_MARK_TAG_RE = re.compile(r"</?mark>")

# Skip the check entirely for very short subjects — too little text to
# produce a meaningful match, and it'd just be noisy false positives.
_MIN_SUBJECT_LENGTH = 8

# How many similar tickets to surface at most.
_MAX_RESULTS = 5


@frappe.whitelist()
def check_similar_tickets(subject: str):
    subject = (subject or "").strip()
    if len(subject) < _MIN_SUBJECT_LENGTH:
        return {"matches": []}

    from helpdesk.search_sqlite import HelpdeskSearch

    search = HelpdeskSearch()
    if not search.index_exists():
        return {"matches": []}

    result = search.search(subject, filters={"doctype": ["HD Ticket"]})

    open_statuses = frappe.get_all(
        "HD Ticket Status",
        filters={"category": ["!=", "Resolved"]},
        pluck="name",
    )

    matches = []
    for row in result.get("results", []):
        ticket_name = row.get("name")
        status = row.get("status")
        if not ticket_name or status not in open_statuses:
            continue

        matches.append({
            "name": ticket_name,
            "title": _MARK_TAG_RE.sub("", row.get("title") or ""),
            "status": status,
            "agreement_status": row.get("agreement_status"),
            "modified": row.get("modified"),
        })

        if len(matches) >= _MAX_RESULTS:
            break

    return {"matches": matches}
