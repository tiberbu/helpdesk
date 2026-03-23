"""Migration patch: add source field to HD Ticket.

Adds a Select field 'source' (Email / Chat / Portal) so that tickets
created via live chat can be identified and filtered by source.

Story 3.6: Chat-to-Ticket Transcript and Follow-up (AC #4).
"""

import frappe


def execute():
    """Set source='Chat' on existing tickets linked to an HD Chat Session."""
    if not frappe.db.has_column("HD Ticket", "source"):
        return

    # Back-fill source="Chat" for tickets linked via HD Chat Session
    sessions_with_tickets = frappe.db.get_all(
        "HD Chat Session",
        filters={"ticket": ["is", "set"]},
        pluck="ticket",
    )
    if sessions_with_tickets:
        frappe.db.sql(
            """
            UPDATE `tabHD Ticket`
            SET source = 'Chat'
            WHERE name IN ({placeholders})
              AND (source IS NULL OR source = '')
            """.format(
                placeholders=", ".join(["%s"] * len(sessions_with_tickets))
            ),
            sessions_with_tickets,
        )

    frappe.db.commit()
