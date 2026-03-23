"""
Regression and unit tests for EmailAdapter.

These tests verify:
1. EmailAdapter produces valid ChannelMessage from dict and InboundMail-like objects.
2. can_handle() returns True for "email" only.
3. The existing email processing hooks path is not modified (regression-safe).

AC references: AC #6, #8, #10
"""

import unittest
from datetime import datetime
from unittest.mock import MagicMock, patch

from helpdesk.helpdesk.channels.base import ChannelMessage
from helpdesk.helpdesk.channels.email_adapter import EmailAdapter, _parse_mail_date


class TestEmailAdapterCanHandle(unittest.TestCase):
    """Verify source routing."""

    def setUp(self):
        self.adapter = EmailAdapter()

    def test_handles_email(self):
        self.assertTrue(self.adapter.can_handle("email"))

    def test_does_not_handle_chat(self):
        self.assertFalse(self.adapter.can_handle("chat"))

    def test_does_not_handle_sms(self):
        self.assertFalse(self.adapter.can_handle("sms"))

    def test_does_not_handle_portal(self):
        self.assertFalse(self.adapter.can_handle("portal"))


class TestEmailAdapterFromDict(unittest.TestCase):
    """Verify dict normalization path."""

    def setUp(self):
        self.adapter = EmailAdapter()

    def test_basic_dict_normalization(self):
        d = {
            "sender": "alice@example.com",
            "sender_full_name": "Alice",
            "subject": "Support needed",
            "content": "<p>I need help.</p>",
        }
        msg = self.adapter.normalize(d)
        self.assertIsInstance(msg, ChannelMessage)
        self.assertEqual(msg.source, "email")
        self.assertEqual(msg.sender_email, "alice@example.com")
        self.assertEqual(msg.sender_name, "Alice")
        self.assertEqual(msg.subject, "Support needed")
        self.assertEqual(msg.content, "<p>I need help.</p>")

    def test_sender_email_alias(self):
        d = {
            "sender_email": "bob@example.com",
            "subject": "Hi",
            "content": "test",
        }
        msg = self.adapter.normalize(d)
        self.assertEqual(msg.sender_email, "bob@example.com")

    def test_sender_name_falls_back_to_email(self):
        d = {"sender": "x@y.com", "subject": "S", "content": "C"}
        msg = self.adapter.normalize(d)
        self.assertEqual(msg.sender_name, "x@y.com")

    def test_ticket_id_from_in_reply_to(self):
        d = {
            "sender": "a@b.com",
            "subject": "Re: ticket",
            "content": "reply",
            "in_reply_to": "HDT-10",
        }
        msg = self.adapter.normalize(d)
        self.assertEqual(msg.ticket_id, "HDT-10")

    def test_ticket_id_from_ticket_id_key(self):
        d = {
            "sender": "a@b.com",
            "subject": "Re: ticket",
            "content": "reply",
            "ticket_id": "HDT-20",
        }
        msg = self.adapter.normalize(d)
        self.assertEqual(msg.ticket_id, "HDT-20")

    def test_no_ticket_id_returns_none(self):
        d = {"sender": "a@b.com", "subject": "New", "content": "first message"}
        msg = self.adapter.normalize(d)
        self.assertIsNone(msg.ticket_id)

    def test_attachments_passed_through(self):
        d = {
            "sender": "a@b.com",
            "subject": "With attachment",
            "content": "see attached",
            "attachments": [{"filename": "doc.pdf"}],
        }
        msg = self.adapter.normalize(d)
        self.assertEqual(msg.attachments, [{"filename": "doc.pdf"}])

    def test_metadata_passed_through(self):
        d = {
            "sender": "a@b.com",
            "subject": "S",
            "content": "C",
            "metadata": {"email_id": "12345"},
        }
        msg = self.adapter.normalize(d)
        self.assertEqual(msg.metadata.get("email_id"), "12345")

    def test_message_key_used_as_content_fallback(self):
        d = {"sender": "a@b.com", "subject": "S", "message": "body text"}
        msg = self.adapter.normalize(d)
        self.assertEqual(msg.content, "body text")

    def test_empty_dict_produces_valid_message(self):
        msg = self.adapter.normalize({})
        self.assertIsInstance(msg, ChannelMessage)
        self.assertEqual(msg.source, "email")
        self.assertEqual(msg.sender_email, "")


class TestEmailAdapterFromInboundMail(unittest.TestCase):
    """Verify InboundMail-like object normalization path."""

    def setUp(self):
        self.adapter = EmailAdapter()

    def _make_inbound_mail(self, **kwargs):
        """Create a mock InboundMail with configurable attributes."""
        mail = MagicMock()
        mail.from_email = kwargs.get("from_email", "sender@example.com")
        mail.from_real_name = kwargs.get("from_real_name", "Sender Name")
        mail.subject = kwargs.get("subject", "Test Email")
        mail.get_content.return_value = kwargs.get("content", "<p>body</p>")
        mail.attachments = kwargs.get("attachments", [])
        mail.reply_to_ticket_name = kwargs.get("reply_to_ticket_name", None)
        mail.date = kwargs.get("date", None)
        return mail

    def test_basic_inbound_mail_normalization(self):
        mail = self._make_inbound_mail()
        msg = self.adapter.normalize(mail)
        self.assertIsInstance(msg, ChannelMessage)
        self.assertEqual(msg.source, "email")
        self.assertEqual(msg.sender_email, "sender@example.com")
        self.assertEqual(msg.sender_name, "Sender Name")
        self.assertEqual(msg.subject, "Test Email")
        self.assertEqual(msg.content, "<p>body</p>")

    def test_reply_ticket_id_extracted(self):
        mail = self._make_inbound_mail(reply_to_ticket_name="HDT-5")
        msg = self.adapter.normalize(mail)
        self.assertEqual(msg.ticket_id, "HDT-5")

    def test_new_email_has_no_ticket_id(self):
        mail = self._make_inbound_mail(reply_to_ticket_name=None)
        msg = self.adapter.normalize(mail)
        self.assertIsNone(msg.ticket_id)

    def test_attachments_from_inbound_mail(self):
        atts = [{"filename": "a.pdf", "content": b"data"}]
        mail = self._make_inbound_mail(attachments=atts)
        msg = self.adapter.normalize(mail)
        self.assertEqual(msg.attachments, atts)

    def test_metadata_contains_inbound_mail_flag(self):
        mail = self._make_inbound_mail()
        msg = self.adapter.normalize(mail)
        self.assertTrue(msg.metadata.get("inbound_mail"))

    def test_get_content_exception_returns_empty_content(self):
        mail = self._make_inbound_mail()
        mail.get_content.side_effect = Exception("decode error")
        msg = self.adapter.normalize(mail)
        self.assertEqual(msg.content, "")

    def test_missing_from_email_returns_empty_string(self):
        mail = MagicMock(spec=[])  # No attributes
        mail.get_content = MagicMock(return_value="")
        msg = self.adapter.normalize(mail)
        self.assertEqual(msg.sender_email, "")


class TestParseMaillDate(unittest.TestCase):
    """Verify _parse_mail_date handles various input forms."""

    def test_none_returns_datetime(self):
        result = _parse_mail_date(None)
        self.assertIsInstance(result, datetime)

    def test_datetime_passthrough(self):
        dt = datetime(2026, 1, 15, 8, 0, 0)
        self.assertEqual(_parse_mail_date(dt), dt)

    def test_rfc_2822_string(self):
        result = _parse_mail_date("Mon, 23 Mar 2026 10:30:00 +0000")
        self.assertIsInstance(result, datetime)
        self.assertEqual(result.year, 2026)
        self.assertEqual(result.month, 3)

    def test_invalid_string_returns_datetime(self):
        result = _parse_mail_date("not-a-date")
        self.assertIsInstance(result, datetime)


class TestEmailAdapterRegressionSafety(unittest.TestCase):
    """
    Verify the existing email processing pipeline is UNCHANGED (AC #8).

    The EmailAdapter is purely additive — it wraps/delegates but does not
    modify helpdesk/overrides/email_account.py or hooks.py.
    """

    def test_custom_email_account_still_importable(self):
        """CustomEmailAccount override must remain importable (regression)."""
        from helpdesk.overrides.email_account import CustomEmailAccount
        from frappe.email.doctype.email_account.email_account import EmailAccount

        self.assertTrue(issubclass(CustomEmailAccount, EmailAccount))

    def test_email_adapter_source_is_email(self):
        adapter = EmailAdapter()
        self.assertEqual(adapter.SOURCE, "email")

    def test_email_adapter_does_not_modify_hooks(self):
        """EmailAdapter must not alter the hooks.py email pipeline."""
        import importlib
        import helpdesk.hooks as hooks_module
        hooks_module = importlib.reload(hooks_module)

        # The email_account override must still be present after importing adapter
        from helpdesk.helpdesk.channels.email_adapter import EmailAdapter  # noqa: F401

        override = getattr(hooks_module, "override_doctype_class", {})
        self.assertIn("Email Account", override)
        self.assertIn(
            "helpdesk.overrides.email_account.CustomEmailAccount",
            override.get("Email Account", []),
        )


if __name__ == "__main__":
    unittest.main()
