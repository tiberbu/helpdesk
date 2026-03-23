"""
Email channel adapter.

Wraps existing Frappe email processing into a ChannelMessage.
This adapter does NOT replace the existing email flow — it provides a
normalize() method that can translate an InboundMail (or a plain dict)
into the standard ChannelMessage format so that other parts of the system
can work with emails through the unified channel interface.

The existing hooks.py doc_events / CustomEmailAccount.get_inbound_mails()
pipeline is left completely intact (regression-safe, AC #6, #8).
"""

from datetime import UTC, datetime
from typing import Any

from helpdesk.helpdesk.channels.base import ChannelAdapter, ChannelMessage


class EmailAdapter(ChannelAdapter):
    """
    Normalizes email messages into ChannelMessage format.

    Accepts two raw_message forms:
      1. A Frappe InboundMail object (the type returned by get_inbound_mails()).
      2. A plain dict with keys: sender, sender_full_name, subject, content,
         attachments, in_reply_to, date.
    """

    SOURCE = "email"

    def can_handle(self, source: str) -> bool:
        return source == self.SOURCE

    def normalize(self, raw_message: Any) -> ChannelMessage:
        """
        Convert an InboundMail or email dict into a ChannelMessage.

        InboundMail attributes used (all optional — falls back to empty):
          .mail.get("From"), .mail.get("Subject"), .get_content(),
          .attachments, .reply_to_ticket_name
        """
        if isinstance(raw_message, dict):
            return self._from_dict(raw_message)
        # Assume InboundMail-like object
        return self._from_inbound_mail(raw_message)

    # ------------------------------------------------------------------
    # Private helpers
    # ------------------------------------------------------------------

    def _from_inbound_mail(self, mail) -> ChannelMessage:
        """Normalize a Frappe InboundMail object."""
        # InboundMail exposes .from_email and .from_real_name after parsing
        sender_email = getattr(mail, "from_email", "") or ""
        sender_name = getattr(mail, "from_real_name", "") or sender_email

        subject = getattr(mail, "subject", "") or ""

        # Content — InboundMail.get_content() returns the decoded body
        content = ""
        if hasattr(mail, "get_content"):
            try:
                content = mail.get_content() or ""
            except Exception:
                pass

        # Frappe InboundMail stores attachments as a list of dicts
        attachments = getattr(mail, "attachments", []) or []

        # ticket_id: InboundMail sets .reply_to_ticket_name when it detects a reply
        ticket_id = getattr(mail, "reply_to_ticket_name", None) or None

        # Timestamp from email Date header
        timestamp = _parse_mail_date(getattr(mail, "date", None))

        return ChannelMessage(
            source=self.SOURCE,
            sender_email=sender_email,
            sender_name=sender_name,
            subject=subject,
            content=content,
            attachments=list(attachments),
            metadata={"inbound_mail": True},
            ticket_id=ticket_id,
            timestamp=timestamp,
        )

    def _from_dict(self, d: dict) -> ChannelMessage:
        """Normalize a plain email dict."""
        sender_email = d.get("sender") or d.get("sender_email") or ""
        sender_name = d.get("sender_full_name") or d.get("sender_name") or sender_email
        subject = d.get("subject") or ""
        content = d.get("content") or d.get("message") or ""
        attachments = d.get("attachments") or []
        ticket_id = d.get("in_reply_to") or d.get("ticket_id") or None
        timestamp = _parse_mail_date(d.get("date"))

        return ChannelMessage(
            source=self.SOURCE,
            sender_email=sender_email,
            sender_name=sender_name,
            subject=subject,
            content=content,
            attachments=list(attachments),
            metadata=d.get("metadata") or {},
            ticket_id=ticket_id,
            timestamp=timestamp,
        )


def _parse_mail_date(date_value) -> datetime:
    """Return a datetime from an email date value or utcnow() as fallback."""
    if date_value is None:
        return datetime.now(UTC).replace(tzinfo=None)
    if isinstance(date_value, datetime):
        return date_value
    try:
        from email.utils import parsedate_to_datetime

        return parsedate_to_datetime(str(date_value)).replace(tzinfo=None)
    except Exception:
        return datetime.now(UTC).replace(tzinfo=None)
