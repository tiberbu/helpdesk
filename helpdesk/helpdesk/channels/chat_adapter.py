"""
Chat channel adapter.

Normalizes incoming chat messages (from HD Chat Session / Socket.IO) into
ChannelMessage format. Chat is a Phase 1 feature (Story 3.2+) but this
adapter is created here so the channel layer is complete before live chat
is built (AR-01).

Raw message format (dict):
  {
    "sender_email"   : str,          # required
    "sender_name"    : str,          # optional, falls back to email
    "content"        : str,          # message body (plain text or HTML)
    "chat_session_id": str,          # required — stored in metadata
    "ticket_id"      : str | None,   # existing ticket for replies
    "subject"        : str | None,   # optional override
    "timestamp"      : datetime | str | None,
  }
"""

from datetime import UTC, datetime
from typing import Any

from helpdesk.helpdesk.channels.base import ChannelAdapter, ChannelMessage


class ChatAdapter(ChannelAdapter):
    """
    Normalizes chat messages into ChannelMessage format.

    The source identifier is "chat".
    """

    SOURCE = "chat"

    def can_handle(self, source: str) -> bool:
        return source == self.SOURCE

    def normalize(self, raw_message: Any) -> ChannelMessage:
        """
        Convert a chat message dict into a ChannelMessage.

        Parameters
        ----------
        raw_message : dict
            Chat message dict (see module docstring for expected keys).

        Returns
        -------
        ChannelMessage with source="chat" and chat_session_id in metadata.
        """
        if not isinstance(raw_message, dict):
            raise TypeError(
                f"ChatAdapter.normalize() expects a dict, got {type(raw_message).__name__}"
            )

        sender_email = raw_message.get("sender_email") or ""
        sender_name = raw_message.get("sender_name") or sender_email
        chat_session_id = raw_message.get("chat_session_id") or ""
        content = raw_message.get("content") or ""
        ticket_id = raw_message.get("ticket_id") or None

        # Auto-generate subject when not provided
        subject = raw_message.get("subject") or (
            f"Chat session {chat_session_id}" if chat_session_id else "Chat message"
        )

        # Collect any extra keys into metadata
        known_keys = {
            "sender_email", "sender_name", "content", "chat_session_id",
            "ticket_id", "subject", "timestamp",
        }
        extra_metadata = {k: v for k, v in raw_message.items() if k not in known_keys}
        metadata = {"chat_session_id": chat_session_id, **extra_metadata}

        timestamp = _parse_chat_timestamp(raw_message.get("timestamp"))

        return ChannelMessage(
            source=self.SOURCE,
            sender_email=sender_email,
            sender_name=sender_name,
            subject=subject,
            content=content,
            attachments=raw_message.get("attachments") or [],
            metadata=metadata,
            ticket_id=ticket_id,
            timestamp=timestamp,
        )

    def normalize_from_doc(self, hd_chat_message) -> ChannelMessage:
        """
        Convert an HD Chat Message Frappe document into a ChannelMessage.

        Used by the HD Chat Message after_insert hook (Story 3.6) to store
        every chat message as an HD Ticket communication.

        Parameters
        ----------
        hd_chat_message : frappe.model.document.Document
            An HD Chat Message document with fields: session, sender_type,
            sender_email, content, sent_at.

        Returns
        -------
        ChannelMessage with source="chat", ticket_id resolved from the
        linked HD Chat Session, and sender_type in metadata.
        """
        import frappe

        session_id = hd_chat_message.session or ""
        ticket_id = None
        if session_id:
            ticket_id = frappe.db.get_value("HD Chat Session", session_id, "ticket") or None

        sender_email = hd_chat_message.sender_email or ""
        # For agent messages the email is set; for system messages use "System"
        sender_name = sender_email or "System"
        sender_type = hd_chat_message.sender_type or "customer"

        content = hd_chat_message.content or ""

        subject = f"Chat session {session_id}" if session_id else "Chat message"

        timestamp = _parse_chat_timestamp(
            getattr(hd_chat_message, "sent_at", None)
            or getattr(hd_chat_message, "creation", None)
        )

        return ChannelMessage(
            source=self.SOURCE,
            sender_email=sender_email,
            sender_name=sender_name,
            subject=subject,
            content=content,
            attachments=[],
            metadata={
                "chat_session_id": session_id,
                "message_name": hd_chat_message.name,
                "sender_type": sender_type,
            },
            ticket_id=ticket_id,
            timestamp=timestamp,
        )


def _parse_chat_timestamp(value) -> datetime:
    """Return a datetime from various timestamp representations."""
    if value is None:
        return datetime.now(UTC).replace(tzinfo=None)
    if isinstance(value, datetime):
        return value
    try:
        from dateutil import parser as dp

        return dp.parse(str(value)).replace(tzinfo=None)
    except Exception:
        return datetime.now(UTC).replace(tzinfo=None)
