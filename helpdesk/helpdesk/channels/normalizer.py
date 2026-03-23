"""
Channel normalizer: converts ChannelMessage → HD Ticket communications.

This is the bridge between the channel abstraction layer and the Frappe
HD Ticket DocType. It handles:
  - New ticket creation (ticket_id is None)
  - Reply communications on existing tickets (ticket_id set)
  - Internal note marking (is_internal=True)
  - Chat transcript storage via create_ticket_communication() (Story 3.6)
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
        if msg.source and msg.source != "portal":
            ticket.source = msg.source.capitalize()
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


def create_ticket_communication(channel_message: ChannelMessage) -> str | None:
    """
    Store a chat message as a Communication on the linked HD Ticket.

    Unlike ChannelNormalizer.process(), this function does NOT reopen the
    ticket status or send emails to agents — it only stores the transcript
    entry. Called from HD Chat Message.after_insert (Story 3.6, AC #1).

    System-typed messages (sender_type="system") are stored as HD Ticket
    Comments (is_internal=False) rather than Communications so they appear
    in the timeline without triggering email pipelines.

    Parameters
    ----------
    channel_message : ChannelMessage
        Normalized message with ticket_id set.

    Returns
    -------
    str | None
        Name of the created Communication or HD Ticket Comment, or None if
        ticket_id is missing.
    """
    if not channel_message.ticket_id:
        frappe.log_error(
            "create_ticket_communication: no ticket_id in ChannelMessage "
            "(session: {0})".format(channel_message.metadata.get("chat_session_id", "")),
            "ChatNormalizerWarning",
        )
        return None

    sender_type = channel_message.metadata.get("sender_type", "customer")

    if sender_type == "system":
        return _store_system_chat_comment(
            ticket_id=channel_message.ticket_id,
            content=channel_message.content,
        )

    return _store_chat_communication(channel_message, sender_type)


def _store_chat_communication(channel_message: ChannelMessage, sender_type: str) -> str:
    """Insert a Communication doc for a customer or agent chat message."""
    sanitizer = ChannelNormalizer()
    content = sanitizer._sanitize_content(channel_message.content)

    sent_or_received = "Received" if sender_type == "customer" else "Sent"

    comm = frappe.new_doc("Communication")
    comm.communication_type = "Communication"
    comm.communication_medium = "Chat"
    comm.sent_or_received = sent_or_received
    comm.email_status = "Open"
    comm.subject = channel_message.subject or ""
    comm.sender = channel_message.sender_email
    comm.sender_full_name = channel_message.sender_name
    comm.content = content
    comm.status = "Linked"
    comm.reference_doctype = "HD Ticket"
    comm.reference_name = channel_message.ticket_id
    comm.ignore_permissions = True
    comm.ignore_mandatory = True
    comm.save(ignore_permissions=True)
    frappe.db.commit()
    return comm.name


def _store_system_chat_comment(ticket_id: str, content: str) -> str:
    """Insert an HD Ticket Comment (non-internal) for a system chat event."""
    comment = frappe.new_doc("HD Ticket Comment")
    comment.reference_ticket = ticket_id
    comment.content = content
    comment.commented_by = "Administrator"
    comment.is_pinned = False
    comment.is_internal = False
    comment.insert(ignore_permissions=True)
    frappe.db.commit()
    return comment.name
