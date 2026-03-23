# Copyright (c) 2026, Frappe Technologies Pvt. Ltd. and contributors
# For license information, please see license.txt

"""HD Chat Session DocType controller.

Represents a single live-chat conversation between a customer and an agent.
Sessions are created on pre-chat form submission and managed by the chat API.
"""

import frappe
from frappe import _
from frappe.model.document import Document


class HDChatSession(Document):
    def before_insert(self):
        """Auto-set started_at and ensure session_id on creation."""
        if not self.started_at:
            self.started_at = frappe.utils.now_datetime()
        if not self.session_id:
            self.session_id = frappe.generate_hash(length=20)
        if not self.inactivity_timeout_minutes:
            self.inactivity_timeout_minutes = 30

    def on_update(self):
        """React to status transitions.

        When a session transitions to 'ended', add a system communication to
        the linked HD Ticket so the agent sees the chat ended in the timeline.
        The ticket status is intentionally NOT changed — it remains open for
        email follow-up (Story 3.6 AC #2, #7).
        """
        if self.has_value_changed("status") and self.status == "ended":
            self._mark_session_ended_on_ticket()

    # ------------------------------------------------------------------
    # Private helpers
    # ------------------------------------------------------------------

    def _mark_session_ended_on_ticket(self):
        """Add system comment to ticket when chat session ends.

        Idempotent: skips insertion if a session-ended comment already exists
        for this ticket (guards against repeated on_update calls).
        Does NOT modify ticket.status.
        """
        if not self.ticket:
            return

        try:
            ticket = frappe.get_doc("HD Ticket", self.ticket)
        except frappe.DoesNotExistError:
            frappe.log_error(
                "HD Ticket {0} not found for chat session {1}".format(
                    self.ticket, self.name
                ),
                "ChatSessionEndedWarning",
            )
            return

        # Skip if ticket is already closed/resolved
        if ticket.status in ("Resolved", "Closed"):
            return

        # Idempotency: don't insert duplicate system comments
        existing = frappe.db.exists(
            "HD Ticket Comment",
            {
                "reference_ticket": self.ticket,
                "content": ["like", "%Chat session ended%"],
                "commented_by": "Administrator",
                "is_internal": 0,
            },
        )
        if existing:
            return

        comment = frappe.new_doc("HD Ticket Comment")
        comment.reference_ticket = self.ticket
        comment.content = _("Chat session ended. Follow up via email.")
        comment.commented_by = "Administrator"
        comment.is_pinned = False
        comment.is_internal = False
        comment.insert(ignore_permissions=True)
        frappe.db.commit()
