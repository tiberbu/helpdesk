"""
Base classes for the channel abstraction layer.

ChannelMessage: Normalized message format for all channels.
ChannelAdapter: Abstract base class all channel adapters must implement.
"""

from abc import ABC, abstractmethod
from dataclasses import dataclass, field
from datetime import UTC, datetime
from typing import Any


@dataclass
class ChannelMessage:
    """
    Normalized representation of an inbound message from any channel.

    All channel adapters must produce a ChannelMessage so the rest of the
    application can process messages without knowing the originating channel.

    Fields
    ------
    source      : Channel identifier — "email", "chat", "portal", etc.
    sender_email: Sender's email address (used as raised_by on new tickets).
    sender_name : Human-readable sender name.
    subject     : Message subject. For email this is the email subject;
                  for chat it is auto-generated as "Chat session {id}".
    content     : HTML-sanitized message body.
    content_type: MIME type of content — defaults to "text/html".
    attachments : List of attachment dicts [{filename, content, content_type}].
    metadata    : Channel-specific data (e.g. chat_session_id, message_id).
    ticket_id   : Existing HD Ticket name if this is a reply; None for new tickets.
    is_internal : True for internal (agent-only) communications.
    timestamp   : When the message was originally sent/received.
    """

    source: str
    sender_email: str
    sender_name: str
    subject: str
    content: str
    content_type: str = "text/html"
    attachments: list = field(default_factory=list)
    metadata: dict = field(default_factory=dict)
    ticket_id: str | None = None
    is_internal: bool = False
    timestamp: datetime = field(default_factory=lambda: datetime.now(UTC).replace(tzinfo=None))


class ChannelAdapter(ABC):
    """
    Abstract base class for all channel adapters.

    Each adapter knows how to normalize raw channel-specific messages into
    the unified ChannelMessage format.

    To add a new channel:
    1. Subclass ChannelAdapter.
    2. Implement normalize() and can_handle().
    3. Register your adapter: registry.register(MyAdapter()).
    """

    @abstractmethod
    def normalize(self, raw_message: Any) -> ChannelMessage:
        """
        Convert a raw channel-specific message into a ChannelMessage.

        Parameters
        ----------
        raw_message : Any
            Channel-specific message object (InboundMail for email,
            dict for chat, etc.).

        Returns
        -------
        ChannelMessage
            Normalized message ready for processing.
        """

    @abstractmethod
    def can_handle(self, source: str) -> bool:
        """
        Return True if this adapter handles the given source identifier.

        Parameters
        ----------
        source : str
            Channel source string, e.g. "email", "chat".
        """
