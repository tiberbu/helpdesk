"""
Channel adapter registry.

Maintains a mapping of source → ChannelAdapter and dispatches
normalize() calls to the correct adapter.
"""

from helpdesk.helpdesk.channels.base import ChannelAdapter, ChannelMessage


class ChannelRegistry:
    """
    Registry of ChannelAdapter instances keyed by source identifier.

    Usage
    -----
    registry = ChannelRegistry()
    registry.register(EmailAdapter())
    registry.register(ChatAdapter())

    adapter = registry.get_adapter("email")
    msg = adapter.normalize(raw_email)
    """

    def __init__(self) -> None:
        self._adapters: list[ChannelAdapter] = []

    def register(self, adapter: ChannelAdapter) -> None:
        """
        Register a channel adapter.

        If an adapter for the same source already exists it is replaced.

        Parameters
        ----------
        adapter : ChannelAdapter
            Adapter to register.
        """
        # Remove any existing adapter that handles overlapping sources
        self._adapters = [
            a for a in self._adapters if not _adapters_overlap(a, adapter)
        ]
        self._adapters.append(adapter)

    def get_adapter(self, source: str) -> ChannelAdapter:
        """
        Return the registered adapter for a given source.

        Parameters
        ----------
        source : str
            Channel source string (e.g. "email", "chat").

        Raises
        ------
        ValueError
            If no adapter is registered for the source.
        """
        for adapter in self._adapters:
            if adapter.can_handle(source):
                return adapter
        registered = [type(a).__name__ for a in self._adapters]
        raise ValueError(
            f"No channel adapter registered for source '{source}'. "
            f"Registered adapters: {registered}"
        )

    def list_adapters(self) -> list[ChannelAdapter]:
        """Return a copy of the registered adapters list."""
        return list(self._adapters)

    def normalize(self, source: str, raw_message) -> ChannelMessage:
        """
        Convenience: get the adapter for *source* and normalize *raw_message*.

        Parameters
        ----------
        source      : str  — Channel source identifier.
        raw_message : Any  — Raw channel-specific message.
        """
        return self.get_adapter(source).normalize(raw_message)


def _adapters_overlap(existing: ChannelAdapter, new: ChannelAdapter) -> bool:
    """Return True if *existing* handles any source that *new* also handles."""
    # We probe a known set of common sources; adapters declare ownership via
    # can_handle(), so check if the new adapter's own source is claimed by old.
    # Because we don't have a static "source" property on the ABC we use a
    # simple heuristic: same class type → overlap.
    return type(existing) is type(new)
