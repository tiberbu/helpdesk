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
