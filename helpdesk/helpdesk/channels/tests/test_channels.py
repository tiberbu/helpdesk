"""
Unit tests for the channel abstraction layer.

Tests ChannelMessage, ChannelRegistry, ChannelNormalizer, and ChatAdapter
without requiring a live Frappe database (uses unittest.mock for Frappe calls).

AC references: AC #1–#5, #7, #9
"""

import unittest
from datetime import datetime
from unittest.mock import MagicMock, patch

from helpdesk.helpdesk.channels.base import ChannelAdapter, ChannelMessage
from helpdesk.helpdesk.channels.chat_adapter import ChatAdapter
from helpdesk.helpdesk.channels.normalizer import ChannelNormalizer
from helpdesk.helpdesk.channels.registry import ChannelRegistry


# ---------------------------------------------------------------------------
# ChannelMessage tests (AC #2)
# ---------------------------------------------------------------------------


class TestChannelMessage(unittest.TestCase):
    """Verify ChannelMessage dataclass fields and defaults."""

    def test_required_fields(self):
        msg = ChannelMessage(
            source="email",
            sender_email="user@example.com",
            sender_name="User",
            subject="Hello",
            content="<p>Hi</p>",
        )
        self.assertEqual(msg.source, "email")
        self.assertEqual(msg.sender_email, "user@example.com")
        self.assertEqual(msg.sender_name, "User")
        self.assertEqual(msg.subject, "Hello")
        self.assertEqual(msg.content, "<p>Hi</p>")

    def test_default_content_type(self):
        msg = ChannelMessage(
            source="chat", sender_email="a@b.com", sender_name="A",
            subject="S", content="C"
        )
        self.assertEqual(msg.content_type, "text/html")

    def test_default_attachments_is_empty_list(self):
        msg = ChannelMessage(
            source="email", sender_email="a@b.com", sender_name="A",
            subject="S", content="C"
        )
        self.assertEqual(msg.attachments, [])

    def test_default_metadata_is_empty_dict(self):
        msg = ChannelMessage(
            source="email", sender_email="a@b.com", sender_name="A",
            subject="S", content="C"
        )
        self.assertEqual(msg.metadata, {})

    def test_default_ticket_id_is_none(self):
        msg = ChannelMessage(
            source="email", sender_email="a@b.com", sender_name="A",
            subject="S", content="C"
        )
        self.assertIsNone(msg.ticket_id)

    def test_default_is_internal_false(self):
        msg = ChannelMessage(
            source="email", sender_email="a@b.com", sender_name="A",
            subject="S", content="C"
        )
        self.assertFalse(msg.is_internal)

    def test_default_timestamp_is_datetime(self):
        msg = ChannelMessage(
            source="email", sender_email="a@b.com", sender_name="A",
            subject="S", content="C"
        )
        self.assertIsInstance(msg.timestamp, datetime)

    def test_custom_values(self):
        ts = datetime(2026, 1, 1, 12, 0, 0)
        msg = ChannelMessage(
            source="chat",
            sender_email="x@y.com",
            sender_name="X",
            subject="My subject",
            content="hello",
            content_type="text/plain",
            attachments=[{"name": "file.txt"}],
            metadata={"session_id": "abc"},
            ticket_id="HDT-001",
            is_internal=True,
            timestamp=ts,
        )
        self.assertEqual(msg.content_type, "text/plain")
        self.assertEqual(msg.attachments, [{"name": "file.txt"}])
        self.assertEqual(msg.metadata, {"session_id": "abc"})
        self.assertEqual(msg.ticket_id, "HDT-001")
        self.assertTrue(msg.is_internal)
        self.assertEqual(msg.timestamp, ts)

    def test_attachments_not_shared_between_instances(self):
        """Mutable default_factory must not share state between instances."""
        msg1 = ChannelMessage(
            source="email", sender_email="a@b.com", sender_name="A",
            subject="S", content="C"
        )
        msg2 = ChannelMessage(
            source="email", sender_email="a@b.com", sender_name="A",
            subject="S", content="C"
        )
        msg1.attachments.append("x")
        self.assertEqual(msg2.attachments, [])

    def test_metadata_not_shared_between_instances(self):
        msg1 = ChannelMessage(
            source="email", sender_email="a@b.com", sender_name="A",
            subject="S", content="C"
        )
        msg2 = ChannelMessage(
            source="email", sender_email="a@b.com", sender_name="A",
            subject="S", content="C"
        )
        msg1.metadata["key"] = "val"
        self.assertNotIn("key", msg2.metadata)


# ---------------------------------------------------------------------------
# ChannelAdapter ABC tests (AC #3)
# ---------------------------------------------------------------------------


class TestChannelAdapterABC(unittest.TestCase):
    """Verify that ChannelAdapter cannot be instantiated directly."""

    def test_cannot_instantiate_abstract(self):
        with self.assertRaises(TypeError):
            ChannelAdapter()  # type: ignore

    def test_concrete_must_implement_both_methods(self):
        """A partial implementation that misses one method still raises."""
        class PartialAdapter(ChannelAdapter):
            def normalize(self, raw_message):
                return None  # pragma: no cover

        with self.assertRaises(TypeError):
            PartialAdapter()

    def test_concrete_implementation_works(self):
        class ConcreteAdapter(ChannelAdapter):
            def normalize(self, raw_message):
                return ChannelMessage(
                    source="test", sender_email="", sender_name="",
                    subject="", content=""
                )

            def can_handle(self, source: str) -> bool:
                return source == "test"

        adapter = ConcreteAdapter()
        self.assertTrue(adapter.can_handle("test"))
        self.assertFalse(adapter.can_handle("email"))


# ---------------------------------------------------------------------------
# ChannelRegistry tests (AC #4)
# ---------------------------------------------------------------------------


def _make_mock_adapter(source_name: str) -> ChannelAdapter:
    """Helper: create a mock adapter for a named source.

    NOTE: Each call creates a distinct class type — intentional for most
    registry tests.  For re-registration tests that need two instances of the
    *same* class, use ``_EmailMockAdapter`` / ``_ChatMockAdapter`` below.
    """
    class _Adapter(ChannelAdapter):
        def normalize(self, raw_message):
            return ChannelMessage(
                source=source_name, sender_email="", sender_name="",
                subject="", content=""
            )

        def can_handle(self, source: str) -> bool:
            return source == source_name

    return _Adapter()


# Persistent class for same-type replacement tests (type identity is stable)
class _EmailMockAdapter(ChannelAdapter):
    def normalize(self, raw_message):
        return ChannelMessage(
            source="email", sender_email="", sender_name="", subject="", content=""
        )

    def can_handle(self, source: str) -> bool:
        return source == "email"


class TestChannelRegistry(unittest.TestCase):
    """Verify ChannelRegistry registration, dispatch, and error handling."""

    def setUp(self):
        self.registry = ChannelRegistry()

    def test_register_and_get_adapter(self):
        adapter = _make_mock_adapter("email")
        self.registry.register(adapter)
        retrieved = self.registry.get_adapter("email")
        self.assertIs(retrieved, adapter)

    def test_get_adapter_unknown_source_raises(self):
        with self.assertRaises(ValueError) as ctx:
            self.registry.get_adapter("whatsapp")
        self.assertIn("whatsapp", str(ctx.exception))

    def test_register_multiple_adapters(self):
        email_adapter = _make_mock_adapter("email")
        chat_adapter = _make_mock_adapter("chat")
        self.registry.register(email_adapter)
        self.registry.register(chat_adapter)

        self.assertIs(self.registry.get_adapter("email"), email_adapter)
        self.assertIs(self.registry.get_adapter("chat"), chat_adapter)

    def test_re_register_same_type_replaces(self):
        # Use a persistent class so both instances share the same type identity
        a1 = _EmailMockAdapter()
        a2 = _EmailMockAdapter()
        self.registry.register(a1)
        self.registry.register(a2)
        # a2 should replace a1 since same class type
        result = self.registry.get_adapter("email")
        self.assertIs(result, a2)

    def test_list_adapters_returns_copy(self):
        adapter = _make_mock_adapter("email")
        self.registry.register(adapter)
        lst = self.registry.list_adapters()
        lst.append(_make_mock_adapter("x"))
        # Original should not be modified
        self.assertEqual(len(self.registry.list_adapters()), 1)

    def test_normalize_convenience_method(self):
        chat_adapter = _make_mock_adapter("chat")
        self.registry.register(chat_adapter)
        msg = self.registry.normalize("chat", {})
        self.assertIsInstance(msg, ChannelMessage)
        self.assertEqual(msg.source, "chat")

    def test_error_message_lists_registered_adapters(self):
        self.registry.register(_make_mock_adapter("email"))
        with self.assertRaises(ValueError) as ctx:
            self.registry.get_adapter("sms")
        self.assertIn("_Adapter", str(ctx.exception))


# ---------------------------------------------------------------------------
# ChatAdapter tests (AC #7)
# ---------------------------------------------------------------------------


class TestChatAdapter(unittest.TestCase):
    """Verify ChatAdapter.normalize() with typical chat messages."""

    def setUp(self):
        self.adapter = ChatAdapter()

    def test_can_handle_chat(self):
        self.assertTrue(self.adapter.can_handle("chat"))

    def test_cannot_handle_email(self):
        self.assertFalse(self.adapter.can_handle("email"))

    def test_basic_normalization(self):
        raw = {
            "sender_email": "customer@example.com",
            "sender_name": "Alice",
            "content": "Hello, I need help.",
            "chat_session_id": "sess-123",
        }
        msg = self.adapter.normalize(raw)
        self.assertIsInstance(msg, ChannelMessage)
        self.assertEqual(msg.source, "chat")
        self.assertEqual(msg.sender_email, "customer@example.com")
        self.assertEqual(msg.sender_name, "Alice")
        self.assertEqual(msg.content, "Hello, I need help.")
        self.assertEqual(msg.metadata["chat_session_id"], "sess-123")

    def test_auto_generated_subject(self):
        raw = {
            "sender_email": "a@b.com",
            "sender_name": "A",
            "content": "Hi",
            "chat_session_id": "sess-456",
        }
        msg = self.adapter.normalize(raw)
        self.assertEqual(msg.subject, "Chat session sess-456")

    def test_custom_subject_respected(self):
        raw = {
            "sender_email": "a@b.com",
            "sender_name": "A",
            "content": "Hi",
            "chat_session_id": "sess-789",
            "subject": "My custom subject",
        }
        msg = self.adapter.normalize(raw)
        self.assertEqual(msg.subject, "My custom subject")

    def test_ticket_id_for_reply(self):
        raw = {
            "sender_email": "a@b.com",
            "sender_name": "A",
            "content": "Follow-up",
            "chat_session_id": "sess-001",
            "ticket_id": "HDT-42",
        }
        msg = self.adapter.normalize(raw)
        self.assertEqual(msg.ticket_id, "HDT-42")

    def test_no_ticket_id_for_new(self):
        raw = {
            "sender_email": "a@b.com",
            "sender_name": "A",
            "content": "New chat",
            "chat_session_id": "sess-002",
        }
        msg = self.adapter.normalize(raw)
        self.assertIsNone(msg.ticket_id)

    def test_sender_name_falls_back_to_email(self):
        raw = {
            "sender_email": "anon@example.com",
            "content": "hi",
            "chat_session_id": "sess-003",
        }
        msg = self.adapter.normalize(raw)
        self.assertEqual(msg.sender_name, "anon@example.com")

    def test_extra_keys_stored_in_metadata(self):
        raw = {
            "sender_email": "a@b.com",
            "content": "hi",
            "chat_session_id": "sess-004",
            "custom_field": "custom_value",
        }
        msg = self.adapter.normalize(raw)
        self.assertEqual(msg.metadata.get("custom_field"), "custom_value")

    def test_non_dict_raises_type_error(self):
        with self.assertRaises(TypeError):
            self.adapter.normalize("not a dict")

    def test_empty_chat_session_id(self):
        raw = {
            "sender_email": "a@b.com",
            "content": "hi",
        }
        msg = self.adapter.normalize(raw)
        self.assertEqual(msg.subject, "Chat message")

    def test_timestamp_defaults_to_datetime(self):
        raw = {
            "sender_email": "a@b.com",
            "content": "hi",
            "chat_session_id": "sess-005",
        }
        msg = self.adapter.normalize(raw)
        self.assertIsInstance(msg.timestamp, datetime)

    def test_timestamp_from_datetime(self):
        ts = datetime(2026, 3, 1, 10, 0, 0)
        raw = {
            "sender_email": "a@b.com",
            "content": "hi",
            "chat_session_id": "sess-006",
            "timestamp": ts,
        }
        msg = self.adapter.normalize(raw)
        self.assertEqual(msg.timestamp, ts)

    def test_attachments_passed_through(self):
        raw = {
            "sender_email": "a@b.com",
            "content": "hi",
            "chat_session_id": "sess-007",
            "attachments": [{"file_url": "/files/img.png"}],
        }
        msg = self.adapter.normalize(raw)
        self.assertEqual(msg.attachments, [{"file_url": "/files/img.png"}])


# ---------------------------------------------------------------------------
# ChannelNormalizer tests (AC #5, #9)
# ---------------------------------------------------------------------------


class TestChannelNormalizer(unittest.TestCase):
    """Verify ChannelNormalizer.process() with mocked Frappe calls."""

    def setUp(self):
        self.normalizer = ChannelNormalizer()

    def _make_msg(self, ticket_id=None, **kwargs):
        defaults = dict(
            source="chat",
            sender_email="user@example.com",
            sender_name="User",
            subject="Test subject",
            content="<p>Hello</p>",
        )
        defaults.update(kwargs)
        return ChannelMessage(ticket_id=ticket_id, **defaults)

    @patch("helpdesk.helpdesk.channels.normalizer.frappe")
    def test_new_ticket_created_when_no_ticket_id(self, mock_frappe):
        """process() with ticket_id=None should create a new HD Ticket."""
        mock_ticket = MagicMock()
        mock_frappe.new_doc.return_value = mock_ticket
        mock_frappe.utils.html_utils.clean_html.return_value = "<p>Hello</p>"

        msg = self._make_msg(ticket_id=None)
        result = self.normalizer.process(msg)

        mock_frappe.new_doc.assert_called_once_with("HD Ticket")
        mock_ticket.insert.assert_called_once()
        self.assertEqual(mock_ticket.subject, "Test subject")
        self.assertEqual(mock_ticket.raised_by, "user@example.com")
        self.assertIs(result, mock_ticket)

    @patch("helpdesk.helpdesk.channels.normalizer.frappe")
    def test_via_customer_portal_set_for_portal_source(self, mock_frappe):
        mock_ticket = MagicMock()
        mock_frappe.new_doc.return_value = mock_ticket
        mock_frappe.utils.html_utils.clean_html.return_value = "content"

        msg = self._make_msg(ticket_id=None, source="portal")
        self.normalizer.process(msg)

        self.assertTrue(mock_ticket.via_customer_portal)

    @patch("helpdesk.helpdesk.channels.normalizer.frappe")
    def test_via_customer_portal_false_for_chat_source(self, mock_frappe):
        mock_ticket = MagicMock()
        mock_frappe.new_doc.return_value = mock_ticket
        mock_frappe.utils.html_utils.clean_html.return_value = "content"

        msg = self._make_msg(ticket_id=None, source="chat")
        self.normalizer.process(msg)

        self.assertFalse(mock_ticket.via_customer_portal)

    @patch("helpdesk.helpdesk.channels.normalizer.frappe")
    def test_reply_calls_create_communication_via_contact(self, mock_frappe):
        """process() with ticket_id set should call create_communication_via_contact."""
        mock_ticket = MagicMock()
        mock_frappe.get_doc.return_value = mock_ticket
        mock_frappe.utils.html_utils.clean_html.return_value = "<p>Hello</p>"

        msg = self._make_msg(ticket_id="HDT-1")
        result = self.normalizer.process(msg)

        mock_frappe.get_doc.assert_called_once_with("HD Ticket", "HDT-1")
        mock_ticket.create_communication_via_contact.assert_called_once()
        self.assertIs(result, mock_ticket)

    @patch("helpdesk.helpdesk.channels.normalizer.frappe")
    def test_content_sanitized_before_use(self, mock_frappe):
        """Content must pass through sanitization (NFR-SE-06)."""
        mock_ticket = MagicMock()
        mock_frappe.new_doc.return_value = mock_ticket
        mock_frappe.utils.html_utils.clean_html.return_value = "safe content"

        msg = self._make_msg(ticket_id=None, content="<script>xss</script>")
        self.normalizer.process(msg)

        mock_frappe.utils.html_utils.clean_html.assert_called_once_with(
            "<script>xss</script>"
        )
        self.assertEqual(mock_ticket.description, "safe content")

    @patch("helpdesk.helpdesk.channels.normalizer.frappe")
    def test_sanitize_fallback_on_clean_html_failure(self, mock_frappe):
        """If clean_html raises, falls back to strip_html."""
        mock_ticket = MagicMock()
        mock_frappe.new_doc.return_value = mock_ticket
        mock_frappe.utils.html_utils.clean_html.side_effect = Exception("fail")
        mock_frappe.utils.strip_html.return_value = "stripped"

        msg = self._make_msg(ticket_id=None, content="<p>text</p>")
        self.normalizer.process(msg)

        mock_frappe.utils.strip_html.assert_called_once_with("<p>text</p>")
        self.assertEqual(mock_ticket.description, "stripped")

    @patch("helpdesk.helpdesk.channels.normalizer.frappe")
    def test_empty_content_handled(self, mock_frappe):
        mock_ticket = MagicMock()
        mock_frappe.new_doc.return_value = mock_ticket
        # clean_html won't be called for empty content
        mock_frappe.utils.html_utils.clean_html.return_value = ""

        msg = self._make_msg(ticket_id=None, content="")
        self.normalizer.process(msg)
        # Should not raise; description set to ""
        self.assertEqual(mock_ticket.description, "")

    @patch("helpdesk.helpdesk.channels.normalizer.frappe")
    def test_new_ticket_is_internal_creates_internal_note(self, mock_frappe):
        """When is_internal=True on a new ticket, an HD Ticket Comment with is_internal=1 is created."""
        mock_ticket = MagicMock()
        mock_ticket.name = "HDT-99"
        mock_note = MagicMock()
        mock_frappe.new_doc.side_effect = [mock_ticket, mock_note]
        mock_frappe.utils.html_utils.clean_html.return_value = "<p>Internal</p>"

        msg = self._make_msg(ticket_id=None, is_internal=True, content="<p>Internal</p>")
        result = self.normalizer.process(msg)

        # Ticket created
        mock_ticket.insert.assert_called_once()
        # Second new_doc call for the HD Ticket Comment
        self.assertEqual(mock_frappe.new_doc.call_count, 2)
        mock_frappe.new_doc.assert_any_call("HD Ticket Comment")
        self.assertEqual(mock_note.reference_ticket, "HDT-99")
        self.assertEqual(mock_note.content, "<p>Internal</p>")
        self.assertTrue(mock_note.is_internal)
        mock_note.insert.assert_called_once()
        self.assertIs(result, mock_ticket)

    @patch("helpdesk.helpdesk.channels.normalizer.frappe")
    def test_new_ticket_not_internal_no_comment_created(self, mock_frappe):
        """When is_internal=False, no HD Ticket Comment is created for a new ticket."""
        mock_ticket = MagicMock()
        mock_frappe.new_doc.return_value = mock_ticket
        mock_frappe.utils.html_utils.clean_html.return_value = "content"

        msg = self._make_msg(ticket_id=None, is_internal=False)
        self.normalizer.process(msg)

        # Only one new_doc call (for the ticket itself, no comment)
        mock_frappe.new_doc.assert_called_once_with("HD Ticket")

    @patch("helpdesk.helpdesk.channels.normalizer.frappe")
    def test_reply_is_internal_creates_internal_note_not_communication(self, mock_frappe):
        """When is_internal=True on a reply, creates internal note instead of communication."""
        mock_ticket = MagicMock()
        mock_ticket.name = "HDT-42"
        mock_note = MagicMock()
        mock_frappe.get_doc.return_value = mock_ticket
        mock_frappe.new_doc.return_value = mock_note
        mock_frappe.utils.html_utils.clean_html.return_value = "<p>Agent note</p>"

        msg = self._make_msg(ticket_id="HDT-42", is_internal=True, content="<p>Agent note</p>")
        result = self.normalizer.process(msg)

        # create_communication_via_contact must NOT be called
        mock_ticket.create_communication_via_contact.assert_not_called()
        # HD Ticket Comment created instead
        mock_frappe.new_doc.assert_called_once_with("HD Ticket Comment")
        self.assertEqual(mock_note.reference_ticket, "HDT-42")
        self.assertEqual(mock_note.content, "<p>Agent note</p>")
        self.assertTrue(mock_note.is_internal)
        mock_note.insert.assert_called_once()
        self.assertIs(result, mock_ticket)

    @patch("helpdesk.helpdesk.channels.normalizer.frappe")
    def test_reply_not_internal_uses_communication(self, mock_frappe):
        """When is_internal=False on a reply, uses create_communication_via_contact (unchanged)."""
        mock_ticket = MagicMock()
        mock_frappe.get_doc.return_value = mock_ticket
        mock_frappe.utils.html_utils.clean_html.return_value = "reply"

        msg = self._make_msg(ticket_id="HDT-5", is_internal=False)
        self.normalizer.process(msg)

        mock_ticket.create_communication_via_contact.assert_called_once()
        mock_frappe.new_doc.assert_not_called()


# ---------------------------------------------------------------------------
# Default registry integration test
# ---------------------------------------------------------------------------


class TestDefaultRegistry(unittest.TestCase):
    """Verify the module-level default registry is populated correctly."""

    def test_default_registry_has_email_adapter(self):
        from helpdesk.helpdesk.channels import get_default_registry
        registry = get_default_registry()
        adapter = registry.get_adapter("email")
        from helpdesk.helpdesk.channels.email_adapter import EmailAdapter
        self.assertIsInstance(adapter, EmailAdapter)

    def test_default_registry_has_chat_adapter(self):
        from helpdesk.helpdesk.channels import get_default_registry
        registry = get_default_registry()
        adapter = registry.get_adapter("chat")
        self.assertIsInstance(adapter, ChatAdapter)

    def test_default_registry_raises_for_unknown(self):
        from helpdesk.helpdesk.channels import get_default_registry
        registry = get_default_registry()
        with self.assertRaises(ValueError):
            registry.get_adapter("sms")


if __name__ == "__main__":
    unittest.main()
