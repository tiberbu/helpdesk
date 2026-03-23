"""
Channel Abstraction Layer for Frappe Helpdesk.

Normalizes inbound messages from any channel (email, chat, future WhatsApp/SMS)
into a unified ChannelMessage format before HD Ticket processing.

ADR-07: Channel Abstraction Layer
"""

from helpdesk.helpdesk.channels.base import ChannelAdapter, ChannelMessage
from helpdesk.helpdesk.channels.normalizer import ChannelNormalizer
from helpdesk.helpdesk.channels.registry import ChannelRegistry

# Module-level default registry — populated lazily to avoid circular imports
_default_registry: "ChannelRegistry | None" = None


def get_default_registry() -> ChannelRegistry:
    """Return (and lazily initialize) the application-wide channel registry."""
    global _default_registry
    if _default_registry is None:
        from helpdesk.helpdesk.channels.chat_adapter import ChatAdapter
        from helpdesk.helpdesk.channels.email_adapter import EmailAdapter

        _default_registry = ChannelRegistry()
        _default_registry.register(EmailAdapter())
        _default_registry.register(ChatAdapter())
    return _default_registry


__all__ = [
    "ChannelMessage",
    "ChannelAdapter",
    "ChannelNormalizer",
    "ChannelRegistry",
    "get_default_registry",
]
