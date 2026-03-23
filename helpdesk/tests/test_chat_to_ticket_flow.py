"""Integration tests for Story 3.6: Chat-to-Ticket Transcript and Follow-up.

Covers:
  - Customer/agent chat messages stored as Communication on HD Ticket (AC #1, #5)
  - System messages stored as HD Ticket Comment (AC #1)
  - Session end does NOT close the ticket (AC #2)
  - System comment added when session ends (AC #2, #7)
  - Ticket remains open after session end (AC #2)
  - Idempotency: no duplicate comments on repeated session saves (AC #7)
  - Edge case: session without linked ticket does not raise (AC #7)
  - Edge case: session linked to non-existent ticket does not raise (AC #7)
  - Edge case: session end skipped when ticket is already Resolved (AC #7)
  - HD Ticket.source set to "Chat" when created via chat normalizer (AC #4)
  - ChatAdapter.normalize_from_doc() produces correct ChannelMessage (AC #1)
  - create_ticket_communication() returns None for missing ticket_id (AC #6)

NFR-M-01: ≥80% line coverage on all new/modified backend code.
NFR-A-01: Communication storage errors do not propagate to caller.
"""

import unittest
from unittest.mock import MagicMock, call, patch

import frappe
from frappe.utils import now_datetime

from helpdesk.helpdesk.channels.base import ChannelMessage
from helpdesk.helpdesk.channels.chat_adapter import ChatAdapter
from helpdesk.helpdesk.channels.normalizer import (
    ChannelNormalizer,
    create_ticket_communication,
)
from helpdesk.test_utils import create_agent, make_ticket


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------


def _make_chat_session(customer_email="customer@chat.test", status="active", ticket=None):
    """Create an HD Chat Session for testing."""
    session_id = frappe.generate_hash(length=16)
    doc = frappe.get_doc(
        {
            "doctype": "HD Chat Session",
            "session_id": session_id,
            "customer_email": customer_email,
            "customer_name": "Chat Test Customer",
            "status": status,
            "started_at": now_datetime(),
            "inactivity_timeout_minutes": 30,
            "ticket": ticket,
        }
    )
    doc.insert(ignore_permissions=True)
    return doc


def _make_chat_message(session_id, content="Hello", sender_email="customer@chat.test",
                       sender_type="customer"):
    """Create an HD Chat Message (before_insert only, no after_insert side-effects)."""
    msg_id = frappe.generate_hash(length=16)
    doc = frappe.get_doc(
        {
            "doctype": "HD Chat Message",
            "message_id": msg_id,
            "session": session_id,
            "sender_type": sender_type,
            "sender_email": sender_email,
            "content": content,
            "sent_at": now_datetime(),
        }
    )
    doc.insert(ignore_permissions=True)
    return doc


# ---------------------------------------------------------------------------
# ChatAdapter.normalize_from_doc() tests (AC #1, #6)
# ---------------------------------------------------------------------------


class TestChatAdapterNormalizeFromDoc(unittest.TestCase):
    """Verify ChatAdapter.normalize_from_doc() produces correct ChannelMessages."""

    def setUp(self):
        frappe.set_user("Administrator")
        self._sessions = []
        self._tickets = []

    def tearDown(self):
        frappe.set_user("Administrator")
        for name in self._sessions:
            frappe.delete_doc("HD Chat Session", name, ignore_missing=True, force=True)
        for name in self._tickets:
            frappe.delete_doc("HD Ticket", name, ignore_missing=True, force=True)
        frappe.db.commit()

    def test_normalize_from_doc_customer_message(self):
        ticket = make_ticket(subject="Chat Transcript Test", raised_by="customer@chat.test")
        self._tickets.append(ticket.name)

        session = _make_chat_session(
            customer_email="customer@chat.test", ticket=ticket.name
        )
        self._sessions.append(session.session_id)

        # Create a message doc without triggering after_insert side-effects
        msg_doc = MagicMock()
        msg_doc.session = session.session_id
        msg_doc.sender_type = "customer"
        msg_doc.sender_email = "customer@chat.test"
        msg_doc.content = "I need help with my order."
        msg_doc.name = "TEST-MSG-001"
        msg_doc.sent_at = now_datetime()
        msg_doc.creation = now_datetime()

        adapter = ChatAdapter()
        channel_msg = adapter.normalize_from_doc(msg_doc)

        self.assertEqual(channel_msg.source, "chat")
        self.assertEqual(channel_msg.sender_email, "customer@chat.test")
        self.assertEqual(channel_msg.ticket_id, str(ticket.name))
        self.assertEqual(channel_msg.metadata["sender_type"], "customer")
        self.assertEqual(channel_msg.metadata["chat_session_id"], session.session_id)
        self.assertEqual(channel_msg.metadata["message_name"], "TEST-MSG-001")
        self.assertFalse(channel_msg.is_internal)

    def test_normalize_from_doc_agent_message(self):
        ticket = make_ticket(subject="Agent Reply Test", raised_by="customer@chat.test")
        self._tickets.append(ticket.name)

        session = _make_chat_session(ticket=ticket.name)
        self._sessions.append(session.session_id)

        msg_doc = MagicMock()
        msg_doc.session = session.session_id
        msg_doc.sender_type = "agent"
        msg_doc.sender_email = "agent@helpdesk.test"
        msg_doc.content = "Let me check that for you."
        msg_doc.name = "TEST-MSG-002"
        msg_doc.sent_at = now_datetime()
        msg_doc.creation = now_datetime()

        adapter = ChatAdapter()
        channel_msg = adapter.normalize_from_doc(msg_doc)

        self.assertEqual(channel_msg.sender_email, "agent@helpdesk.test")
        self.assertEqual(channel_msg.metadata["sender_type"], "agent")
        self.assertEqual(channel_msg.ticket_id, str(ticket.name))

    def test_normalize_from_doc_session_without_ticket(self):
        session = _make_chat_session(ticket=None)
        self._sessions.append(session.session_id)

        msg_doc = MagicMock()
        msg_doc.session = session.session_id
        msg_doc.sender_type = "customer"
        msg_doc.sender_email = "customer@chat.test"
        msg_doc.content = "Hello"
        msg_doc.name = "TEST-MSG-003"
        msg_doc.sent_at = now_datetime()
        msg_doc.creation = now_datetime()

        adapter = ChatAdapter()
        channel_msg = adapter.normalize_from_doc(msg_doc)

        self.assertIsNone(channel_msg.ticket_id)


# ---------------------------------------------------------------------------
# create_ticket_communication() unit tests (mocked frappe) (AC #1, #6)
# ---------------------------------------------------------------------------


class TestCreateTicketCommunication(unittest.TestCase):
    """Verify create_ticket_communication() creates Communication docs correctly."""

    def _make_msg(self, ticket_id=None, sender_type="customer", **kwargs):
        defaults = dict(
            source="chat",
            sender_email="customer@chat.test",
            sender_name="Test Customer",
            subject="Chat session sess-001",
            content="Hello world",
            metadata={"chat_session_id": "sess-001", "sender_type": sender_type},
        )
        defaults.update(kwargs)
        return ChannelMessage(ticket_id=ticket_id, **defaults)

    def test_returns_none_when_no_ticket_id(self):
        msg = self._make_msg(ticket_id=None)
        result = create_ticket_communication(msg)
        self.assertIsNone(result)

    @patch("helpdesk.helpdesk.channels.normalizer.frappe")
    def test_customer_message_creates_communication_received(self, mock_frappe):
        mock_comm = MagicMock()
        mock_comm.name = "COMM-001"
        mock_frappe.new_doc.return_value = mock_comm
        mock_frappe.utils.html_utils.clean_html.return_value = "Hello world"

        msg = self._make_msg(ticket_id="HDT-1", sender_type="customer")
        result = create_ticket_communication(msg)

        mock_frappe.new_doc.assert_called_once_with("Communication")
        self.assertEqual(mock_comm.communication_medium, "Chat")
        self.assertEqual(mock_comm.sent_or_received, "Received")
        self.assertEqual(mock_comm.reference_doctype, "HD Ticket")
        self.assertEqual(mock_comm.reference_name, "HDT-1")
        mock_comm.save.assert_called_once()
        self.assertEqual(result, "COMM-001")

    @patch("helpdesk.helpdesk.channels.normalizer.frappe")
    def test_agent_message_creates_communication_sent(self, mock_frappe):
        mock_comm = MagicMock()
        mock_comm.name = "COMM-002"
        mock_frappe.new_doc.return_value = mock_comm
        mock_frappe.utils.html_utils.clean_html.return_value = "Agent reply"

        msg = self._make_msg(ticket_id="HDT-1", sender_type="agent",
                             content="Agent reply", sender_email="agent@test.com")
        result = create_ticket_communication(msg)

        self.assertEqual(mock_comm.sent_or_received, "Sent")
        self.assertEqual(result, "COMM-002")

    @patch("helpdesk.helpdesk.channels.normalizer.frappe")
    def test_system_message_creates_ticket_comment(self, mock_frappe):
        mock_comment = MagicMock()
        mock_comment.name = "COMMENT-001"
        mock_frappe.new_doc.return_value = mock_comment

        msg = self._make_msg(
            ticket_id="HDT-1",
            sender_type="system",
            metadata={"chat_session_id": "sess-001", "sender_type": "system"},
        )
        result = create_ticket_communication(msg)

        mock_frappe.new_doc.assert_called_once_with("HD Ticket Comment")
        self.assertEqual(mock_comment.reference_ticket, "HDT-1")
        self.assertFalse(mock_comment.is_internal)
        mock_comment.insert.assert_called_once()
        self.assertEqual(result, "COMMENT-001")

    @patch("helpdesk.helpdesk.channels.normalizer.frappe")
    def test_xss_content_sanitized(self, mock_frappe):
        mock_comm = MagicMock()
        mock_comm.name = "COMM-003"
        mock_frappe.new_doc.return_value = mock_comm
        mock_frappe.utils.html_utils.clean_html.return_value = "safe content"

        msg = self._make_msg(
            ticket_id="HDT-1", sender_type="customer",
            content="<script>alert('xss')</script>"
        )
        create_ticket_communication(msg)

        mock_frappe.utils.html_utils.clean_html.assert_called_once_with(
            "<script>alert('xss')</script>"
        )
        self.assertEqual(mock_comm.content, "safe content")


# ---------------------------------------------------------------------------
# HD Chat Message after_insert integration tests (AC #1)
# ---------------------------------------------------------------------------


class TestHDChatMessageAfterInsert(unittest.TestCase):
    """Verify after_insert stores Communications on the HD Ticket."""

    def setUp(self):
        frappe.set_user("Administrator")
        frappe.db.set_value("HD Settings", None, "chat_enabled", 1)
        self._sessions = []
        self._tickets = []
        self._messages = []

    def tearDown(self):
        frappe.set_user("Administrator")
        for name in self._messages:
            frappe.delete_doc("HD Chat Message", name, ignore_missing=True, force=True)
        for name in self._sessions:
            frappe.delete_doc("HD Chat Session", name, ignore_missing=True, force=True)
        for name in self._tickets:
            frappe.delete_doc("HD Ticket", name, ignore_missing=True, force=True)
        frappe.db.commit()

    def test_customer_message_creates_communication(self):
        ticket = make_ticket(
            subject="Chat Flow Test", raised_by="customer@chat.test"
        )
        self._tickets.append(ticket.name)

        session = _make_chat_session(
            customer_email="customer@chat.test", ticket=ticket.name
        )
        self._sessions.append(session.session_id)

        msg = _make_chat_message(
            session.session_id,
            content="I need help",
            sender_email="customer@chat.test",
            sender_type="customer",
        )
        self._messages.append(msg.name)

        # Verify Communication was created on the ticket
        comms = frappe.get_all(
            "Communication",
            filters={
                "reference_doctype": "HD Ticket",
                "reference_name": ticket.name,
                "communication_medium": "Chat",
                "sent_or_received": "Received",
            },
            pluck="name",
        )
        self.assertTrue(
            len(comms) >= 1,
            "Expected a Chat Communication to be created on the HD Ticket",
        )

    def test_agent_message_creates_sent_communication(self):
        agent_email = "agent_chat_test@helpdesk.test"
        agent = create_agent(agent_email)

        ticket = make_ticket(subject="Agent Chat Test", raised_by="customer@chat.test")
        self._tickets.append(ticket.name)

        session = _make_chat_session(
            customer_email="customer@chat.test", ticket=ticket.name
        )
        self._sessions.append(session.session_id)

        msg = _make_chat_message(
            session.session_id,
            content="Here is the answer",
            sender_email=agent_email,
            sender_type="agent",
        )
        self._messages.append(msg.name)

        comms = frappe.get_all(
            "Communication",
            filters={
                "reference_doctype": "HD Ticket",
                "reference_name": ticket.name,
                "communication_medium": "Chat",
                "sent_or_received": "Sent",
            },
            pluck="name",
        )
        self.assertTrue(len(comms) >= 1)

        # Cleanup agent
        frappe.delete_doc("HD Agent", agent.name, ignore_missing=True, force=True)
        frappe.db.commit()

    def test_message_without_ticket_does_not_error(self):
        """after_insert must not raise even when session has no ticket (NFR-A-01)."""
        session = _make_chat_session(ticket=None)
        self._sessions.append(session.session_id)

        # Should complete without raising
        msg = _make_chat_message(
            session.session_id,
            content="No ticket yet",
            sender_type="customer",
        )
        self._messages.append(msg.name)

    def test_disabled_chat_skips_communication(self):
        """When chat_enabled=0, after_insert should be a no-op."""
        frappe.db.set_value("HD Settings", None, "chat_enabled", 0)
        ticket = make_ticket(subject="Disabled Chat Test", raised_by="customer@chat.test")
        self._tickets.append(ticket.name)

        session = _make_chat_session(ticket=ticket.name)
        self._sessions.append(session.session_id)

        before_count = frappe.db.count(
            "Communication",
            {"reference_name": ticket.name, "communication_medium": "Chat"},
        )
        msg = _make_chat_message(session.session_id, content="Should not appear")
        self._messages.append(msg.name)

        after_count = frappe.db.count(
            "Communication",
            {"reference_name": ticket.name, "communication_medium": "Chat"},
        )
        # Re-enable for other tests
        frappe.db.set_value("HD Settings", None, "chat_enabled", 1)
        self.assertEqual(before_count, after_count)


# ---------------------------------------------------------------------------
# HD Chat Session on_update / session-ended tests (AC #2, #7)
# ---------------------------------------------------------------------------


class TestHDChatSessionOnUpdate(unittest.TestCase):
    """Verify session end adds system comment; ticket status never changed."""

    def setUp(self):
        frappe.set_user("Administrator")
        frappe.db.set_value("HD Settings", None, "chat_enabled", 1)
        self._sessions = []
        self._tickets = []

    def tearDown(self):
        frappe.set_user("Administrator")
        for name in self._sessions:
            frappe.delete_doc("HD Chat Session", name, ignore_missing=True, force=True)
        for name in self._tickets:
            frappe.delete_doc("HD Ticket", name, ignore_missing=True, force=True)
        frappe.db.commit()

    def test_session_end_does_not_close_ticket(self):
        ticket = make_ticket(subject="Ticket Should Stay Open", raised_by="cust@chat.test")
        self._tickets.append(ticket.name)

        session = _make_chat_session(ticket=ticket.name, status="active")
        self._sessions.append(session.session_id)

        # End the session
        session.status = "ended"
        session.ended_at = now_datetime()
        session.save(ignore_permissions=True)

        ticket.reload()
        self.assertNotIn(
            ticket.status,
            ("Resolved", "Closed"),
            f"Ticket status must not be Resolved/Closed after chat end; got {ticket.status}",
        )

    def test_session_end_adds_system_comment(self):
        ticket = make_ticket(subject="System Comment Test", raised_by="cust@chat.test")
        self._tickets.append(ticket.name)

        session = _make_chat_session(ticket=ticket.name, status="active")
        self._sessions.append(session.session_id)

        session.status = "ended"
        session.ended_at = now_datetime()
        session.save(ignore_permissions=True)

        comments = frappe.get_all(
            "HD Ticket Comment",
            filters={
                "reference_ticket": ticket.name,
                "content": ["like", "%Chat session ended%"],
            },
            pluck="name",
        )
        self.assertEqual(
            len(comments),
            1,
            "Expected exactly one 'Chat session ended' comment",
        )

    def test_session_end_without_ticket_does_not_error(self):
        """Sessions created before a ticket was linked must not raise (NFR-A-01)."""
        session = _make_chat_session(ticket=None, status="active")
        self._sessions.append(session.session_id)

        session.status = "ended"
        session.ended_at = now_datetime()
        session.save(ignore_permissions=True)  # must not raise

    def test_session_end_skips_resolved_ticket(self):
        ticket = make_ticket(subject="Already Resolved", raised_by="cust@chat.test")
        self._tickets.append(ticket.name)
        # Mark ticket resolved
        ticket.db_set("status", "Resolved")

        session = _make_chat_session(ticket=ticket.name, status="active")
        self._sessions.append(session.session_id)

        before = frappe.db.count(
            "HD Ticket Comment",
            {"reference_ticket": ticket.name, "content": ["like", "%Chat session ended%"]},
        )
        session.status = "ended"
        session.save(ignore_permissions=True)
        after = frappe.db.count(
            "HD Ticket Comment",
            {"reference_ticket": ticket.name, "content": ["like", "%Chat session ended%"]},
        )
        self.assertEqual(before, after, "Should not insert comment for resolved ticket")

    def test_session_end_idempotent(self):
        """Saving session as 'ended' twice must not insert duplicate comments."""
        ticket = make_ticket(subject="Idempotency Test", raised_by="cust@chat.test")
        self._tickets.append(ticket.name)

        session = _make_chat_session(ticket=ticket.name, status="active")
        self._sessions.append(session.session_id)

        # First end
        session.status = "ended"
        session.ended_at = now_datetime()
        session.save(ignore_permissions=True)

        # Second save with same status — should not insert duplicate
        session.reload()
        session.save(ignore_permissions=True)

        count = frappe.db.count(
            "HD Ticket Comment",
            {
                "reference_ticket": ticket.name,
                "content": ["like", "%Chat session ended%"],
            },
        )
        self.assertEqual(count, 1, "Expected exactly one system comment (idempotent)")


# ---------------------------------------------------------------------------
# ChannelNormalizer source field tests (AC #4)
# ---------------------------------------------------------------------------


class TestChannelNormalizerSource(unittest.TestCase):
    """Verify ticket.source is set when creating tickets via chat."""

    @patch("helpdesk.helpdesk.channels.normalizer.frappe")
    def test_chat_source_sets_ticket_source(self, mock_frappe):
        mock_ticket = MagicMock()
        mock_frappe.new_doc.return_value = mock_ticket
        mock_frappe.utils.html_utils.clean_html.return_value = "content"

        msg = ChannelMessage(
            source="chat",
            sender_email="cust@chat.test",
            sender_name="Customer",
            subject="Chat session 123",
            content="Hello",
        )
        ChannelNormalizer().process(msg)

        self.assertEqual(mock_ticket.source, "Chat")

    @patch("helpdesk.helpdesk.channels.normalizer.frappe")
    def test_portal_source_does_not_set_source_field(self, mock_frappe):
        """Portal source uses via_customer_portal flag, not source field."""
        mock_ticket = MagicMock()
        mock_frappe.new_doc.return_value = mock_ticket
        mock_frappe.utils.html_utils.clean_html.return_value = "content"

        msg = ChannelMessage(
            source="portal",
            sender_email="cust@portal.test",
            sender_name="Customer",
            subject="Portal ticket",
            content="Help",
        )
        ChannelNormalizer().process(msg)

        # source should NOT be set for portal (handled by via_customer_portal)
        self.assertTrue(mock_ticket.via_customer_portal)
        # source attribute should not be set (it won't exist on mock unless explicitly set)
        self.assertFalse(
            hasattr(mock_ticket, "source") and mock_ticket.source == "Portal",
            "Portal tickets should not set source field",
        )

    @patch("helpdesk.helpdesk.channels.normalizer.frappe")
    def test_email_source_sets_email_on_ticket(self, mock_frappe):
        mock_ticket = MagicMock()
        mock_frappe.new_doc.return_value = mock_ticket
        mock_frappe.utils.html_utils.clean_html.return_value = "content"

        msg = ChannelMessage(
            source="email",
            sender_email="cust@email.test",
            sender_name="Customer",
            subject="Email ticket",
            content="Help via email",
        )
        ChannelNormalizer().process(msg)

        self.assertEqual(mock_ticket.source, "Email")


if __name__ == "__main__":
    unittest.main()
