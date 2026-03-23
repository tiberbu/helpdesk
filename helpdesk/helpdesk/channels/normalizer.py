"""
Channel normalizer: converts ChannelMessage → HD Ticket communications.

This is the bridge between the channel abstraction layer and the Frappe
HD Ticket DocType. It handles:
  - New ticket creation (ticket_id is None)
  - Reply communications on existing tickets (ticket_id set)
  - Internal note marking (is_internal=True)
"""

import frappe

from helpdesk.helpdesk.channels.base import ChannelMessage


class ChannelNormalizer:
    """
    Processes a ChannelMessage and creates the appropriate Frappe document.

    For new tickets:
        Creates an HD Ticket with subject, raised_by, description from the message.

    For replies:
        Fetches the existing ticket and calls create_communication_via_contact().
    """

    def process(self, msg: ChannelMessage):
        """
        Process a normalized ChannelMessage into HD Ticket infrastructure.

        Parameters
        ----------
        msg : ChannelMessage
            Normalized inbound message.

        Returns
        -------
        Document
            The created or updated HD Ticket document.
        """
        if msg.ticket_id:
            return self._process_reply(msg)
        return self._create_ticket(msg)

    # ------------------------------------------------------------------
    # Internal helpers
    # ------------------------------------------------------------------

    def _create_ticket(self, msg: ChannelMessage):
        """Create a new HD Ticket from a ChannelMessage."""
        content = self._sanitize_content(msg.content)

        ticket = frappe.new_doc("HD Ticket")
        ticket.subject = msg.subject or f"Message from {msg.sender_name or msg.sender_email}"
        ticket.raised_by = msg.sender_email
        ticket.via_customer_portal = msg.source == "portal"
        ticket.description = content
        ticket.insert(ignore_permissions=True)

        if msg.is_internal:
            self._insert_internal_note(
                ticket_name=ticket.name,
                content=content,
                sender_email=msg.sender_email,
            )

        return ticket

    def _process_reply(self, msg: ChannelMessage):
        """Add a reply communication to an existing ticket."""
        content = self._sanitize_content(msg.content)

        ticket = frappe.get_doc("HD Ticket", msg.ticket_id)
        if msg.is_internal:
            self._insert_internal_note(
                ticket_name=ticket.name,
                content=content,
                sender_email=msg.sender_email,
            )
        else:
            ticket.create_communication_via_contact(
                message=content,
                attachments=msg.attachments or [],
            )
        return ticket

    def _insert_internal_note(self, ticket_name: str, content: str, sender_email: str):
        """Directly insert an HD Ticket Comment with is_internal=1 (system-level, bypasses agent check)."""
        note = frappe.new_doc("HD Ticket Comment")
        note.reference_ticket = ticket_name
        note.content = content
        note.commented_by = sender_email
        note.is_pinned = False
        note.is_internal = True
        note.insert(ignore_permissions=True)

    def _sanitize_content(self, content: str) -> str:
        """HTML-sanitize message content before storage (NFR-SE-06)."""
        if not content:
            return ""
        try:
            return frappe.utils.html_utils.clean_html(content)
        except Exception:
            # Fallback: strip tags via bleach/markupsafe if clean_html fails
            return frappe.utils.strip_html(content)
