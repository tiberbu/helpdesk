"""Tests for Story 3.4: Real-Time Chat Communication.

Covers:
  - chat_handlers.handle_typing_start / handle_typing_stop: broadcast only, no DB write
  - chat_handlers.handle_message_delivered: broadcast only, no DB write
  - chat_handlers.handle_message_read: sets is_read=1 on HD Chat Message + broadcast
  - check_unanswered_sessions: sends auto-message to timed-out waiting sessions
  - New REST API endpoints: typing_start, typing_stop, message_delivered, mark_messages_read

NFR-M-01: ≥80% line coverage on new backend code.
NFR-SE-02: JWT validation enforced — invalid token raises AuthenticationError.
"""

import unittest
from unittest.mock import MagicMock, patch, call

import frappe
from frappe.utils import add_to_date, now_datetime

from helpdesk.test_utils import create_agent, make_ticket


class TestChatHandlers(unittest.TestCase):
    """Unit tests for helpdesk.helpdesk.realtime.chat_handlers."""

    def setUp(self):
        frappe.set_user("Administrator")
        self._sessions = []
        self._messages = []

    def tearDown(self):
        frappe.set_user("Administrator")
        for name in self._messages:
            try:
                frappe.delete_doc("HD Chat Message", name, ignore_missing=True, force=True)
            except Exception:
                pass
        for name in self._sessions:
            try:
                frappe.delete_doc("HD Chat Session", name, ignore_missing=True, force=True)
            except Exception:
                pass
        frappe.db.commit()

    # ── Helpers ──────────────────────────────────────────────────────────────

    def _make_session(self, email="customer@example.com"):
        """Create a minimal HD Chat Session and return (session_id, token)."""
        from helpdesk.helpdesk.chat.jwt_helper import generate_chat_token

        session_id = frappe.generate_hash(length=12)
        doc = frappe.get_doc({
            "doctype": "HD Chat Session",
            "session_id": session_id,
            "customer_email": email,
            "customer_name": "Test Customer",
            "status": "active",
            "started_at": now_datetime(),
            "inactivity_timeout_minutes": 30,
        })
        doc.insert(ignore_permissions=True)
        frappe.db.commit()
        self._sessions.append(doc.name)
        token = generate_chat_token(session_id, email)
        return session_id, token

    def _make_message(self, session_id, sender_type="agent", content="Hello", is_read=0):
        """Insert an HD Chat Message and return its message_id."""
        msg = frappe.get_doc({
            "doctype": "HD Chat Message",
            "session": session_id,
            "sender_type": sender_type,
            "content": content,
            "sent_at": now_datetime(),
            "is_read": is_read,
        })
        msg.insert(ignore_permissions=True)
        frappe.db.commit()
        self._messages.append(msg.name)
        return msg.message_id

    # ── handle_typing_start ───────────────────────────────────────────────────

    @patch("helpdesk.helpdesk.realtime.chat_handlers.frappe.publish_realtime")
    def test_typing_start_broadcasts_and_does_not_save(self, mock_publish):
        """typing_start must publish to the room but NOT create any DB record."""
        session_id, token = self._make_session()
        before_count = frappe.db.count("HD Chat Message", {"session": session_id})

        from helpdesk.helpdesk.realtime.chat_handlers import handle_typing_start
        handle_typing_start(session_id, token, sender_name="Alice")

        chat_calls = [c for c in mock_publish.call_args_list if c.kwargs.get("event") == "typing_start"]
        self.assertEqual(len(chat_calls), 1)
        self.assertEqual(chat_calls[0].kwargs["message"], {"session_id": session_id, "sender_name": "Alice"})
        self.assertEqual(chat_calls[0].kwargs["room"], f"chat:{session_id}")
        after_count = frappe.db.count("HD Chat Message", {"session": session_id})
        self.assertEqual(before_count, after_count, "typing_start must not insert DB records")

    @patch("helpdesk.helpdesk.realtime.chat_handlers.frappe.publish_realtime")
    def test_typing_start_invalid_token_raises(self, mock_publish):
        """Invalid JWT must raise AuthenticationError (NFR-SE-02)."""
        session_id, _ = self._make_session()
        from helpdesk.helpdesk.realtime.chat_handlers import handle_typing_start
        with self.assertRaises(frappe.AuthenticationError):
            handle_typing_start(session_id, "bad-token")
        chat_calls = [c for c in mock_publish.call_args_list if c.kwargs.get("event") == "typing_start"]
        self.assertEqual(len(chat_calls), 0, "No typing_start broadcast on invalid token")

    # ── handle_typing_stop ────────────────────────────────────────────────────

    @patch("helpdesk.helpdesk.realtime.chat_handlers.frappe.publish_realtime")
    def test_typing_stop_broadcasts_and_does_not_save(self, mock_publish):
        """typing_stop must publish to the room but NOT create any DB record."""
        session_id, token = self._make_session()

        from helpdesk.helpdesk.realtime.chat_handlers import handle_typing_stop
        handle_typing_stop(session_id, token)

        chat_calls = [c for c in mock_publish.call_args_list if c.kwargs.get("event") == "typing_stop"]
        self.assertEqual(len(chat_calls), 1)
        self.assertEqual(chat_calls[0].kwargs["message"], {"session_id": session_id})
        self.assertEqual(chat_calls[0].kwargs["room"], f"chat:{session_id}")

    # ── handle_message_delivered ──────────────────────────────────────────────

    @patch("helpdesk.helpdesk.realtime.chat_handlers.frappe.publish_realtime")
    def test_message_delivered_broadcasts_status(self, mock_publish):
        """message_delivered must broadcast 'delivered' status without DB write."""
        session_id, token = self._make_session()
        message_id = self._make_message(session_id)

        from helpdesk.helpdesk.realtime.chat_handlers import handle_message_delivered
        handle_message_delivered(session_id, token, message_id)

        delivered_calls = [
            c for c in mock_publish.call_args_list
            if c.kwargs.get("event") == "message_status"
            and c.kwargs.get("message", {}).get("status") == "delivered"
        ]
        self.assertEqual(len(delivered_calls), 1)
        self.assertEqual(delivered_calls[0].kwargs["message"]["message_id"], message_id)
        self.assertEqual(delivered_calls[0].kwargs["room"], f"chat:{session_id}")
        # is_read should NOT be changed by delivered event
        is_read = frappe.db.get_value("HD Chat Message", {"message_id": message_id}, "is_read")
        self.assertEqual(is_read, 0)

    # ── handle_message_read ───────────────────────────────────────────────────

    @patch("helpdesk.helpdesk.realtime.chat_handlers.frappe.publish_realtime")
    def test_message_read_sets_is_read_and_broadcasts(self, mock_publish):
        """handle_message_read must set is_read=1 and broadcast 'read' status."""
        session_id, token = self._make_session()
        mid1 = self._make_message(session_id, content="Msg 1")
        mid2 = self._make_message(session_id, content="Msg 2")

        from helpdesk.helpdesk.realtime.chat_handlers import handle_message_read
        handle_message_read(session_id, token, [mid1, mid2])

        # Both messages should be is_read=1
        is_read1 = frappe.db.get_value("HD Chat Message", {"message_id": mid1}, "is_read")
        is_read2 = frappe.db.get_value("HD Chat Message", {"message_id": mid2}, "is_read")
        self.assertEqual(is_read1, 1)
        self.assertEqual(is_read2, 1)

        # Broadcasts for both
        read_calls = [
            c for c in mock_publish.call_args_list
            if c.kwargs.get("event") == "message_status"
            and c.kwargs.get("message", {}).get("status") == "read"
        ]
        self.assertEqual(len(read_calls), 2)
        read_ids = {c.kwargs["message"]["message_id"] for c in read_calls}
        self.assertIn(mid1, read_ids)
        self.assertIn(mid2, read_ids)

    @patch("helpdesk.helpdesk.realtime.chat_handlers.frappe.publish_realtime")
    def test_message_read_invalid_token_raises(self, mock_publish):
        """Invalid JWT must raise AuthenticationError (NFR-SE-02)."""
        session_id, _ = self._make_session()
        mid = self._make_message(session_id)
        from helpdesk.helpdesk.realtime.chat_handlers import handle_message_read
        with self.assertRaises(frappe.AuthenticationError):
            handle_message_read(session_id, "bad-token", [mid])
        read_calls = [c for c in mock_publish.call_args_list if c.kwargs.get("event") == "message_status"]
        self.assertEqual(len(read_calls), 0, "No message_status broadcast on invalid token")

    @patch("helpdesk.helpdesk.realtime.chat_handlers.frappe.publish_realtime")
    def test_message_read_ignores_cross_session_ids(self, mock_publish):
        """message_ids from a different session must NOT be marked read."""
        session_id, token = self._make_session()
        session_id2, _ = self._make_session("other@example.com")
        mid_other = self._make_message(session_id2, content="Other session msg")

        from helpdesk.helpdesk.realtime.chat_handlers import handle_message_read
        # Try to mark a message from session2 using session1's token
        handle_message_read(session_id, token, [mid_other])

        is_read = frappe.db.get_value("HD Chat Message", {"message_id": mid_other}, "is_read")
        self.assertEqual(is_read, 0, "Cross-session message must not be marked read")
        read_calls = [c for c in mock_publish.call_args_list if c.kwargs.get("event") == "message_status"]
        self.assertEqual(len(read_calls), 0, "No message_status broadcast for cross-session message")

    @patch("helpdesk.helpdesk.realtime.chat_handlers.frappe.publish_realtime")
    def test_message_read_empty_list_is_noop(self, mock_publish):
        """Empty message_ids list must be a no-op."""
        session_id, token = self._make_session()
        from helpdesk.helpdesk.realtime.chat_handlers import handle_message_read
        handle_message_read(session_id, token, [])
        read_calls = [c for c in mock_publish.call_args_list if c.kwargs.get("event") == "message_status"]
        self.assertEqual(len(read_calls), 0, "Empty list must not trigger any broadcasts")


class TestResponseTimeout(unittest.TestCase):
    """Unit tests for helpdesk.helpdesk.chat.response_timeout."""

    def setUp(self):
        frappe.set_user("Administrator")
        self._sessions = []
        self._messages = []

    def tearDown(self):
        frappe.set_user("Administrator")
        for name in self._messages:
            try:
                frappe.delete_doc("HD Chat Message", name, ignore_missing=True, force=True)
            except Exception:
                pass
        for name in self._sessions:
            try:
                frappe.delete_doc("HD Chat Session", name, ignore_missing=True, force=True)
            except Exception:
                pass
        frappe.db.commit()

    def _make_waiting_session(self, started_minutes_ago=5, notified=False):
        session_id = frappe.generate_hash(length=12)
        doc = frappe.get_doc({
            "doctype": "HD Chat Session",
            "session_id": session_id,
            "customer_email": "wait@example.com",
            "customer_name": "Waiting Customer",
            "status": "waiting",
            "started_at": add_to_date(now_datetime(), minutes=-started_minutes_ago),
            "inactivity_timeout_minutes": 30,
            "timeout_notified_at": now_datetime() if notified else None,
        })
        doc.insert(ignore_permissions=True)
        frappe.db.commit()
        self._sessions.append(doc.name)
        return doc, session_id

    # ── check_unanswered_sessions ─────────────────────────────────────────────

    @patch("helpdesk.helpdesk.chat.response_timeout.frappe.publish_realtime")
    def test_sends_auto_message_to_timed_out_session(self, mock_publish):
        """A waiting session past the timeout threshold must receive the auto-message."""
        # Override timeout to 60s; session started 5 minutes ago
        frappe.db.set_value("HD Settings", None, "chat_response_timeout_seconds", 60)

        doc, session_id = self._make_waiting_session(started_minutes_ago=5)

        from helpdesk.helpdesk.chat.response_timeout import check_unanswered_sessions
        notified_count = check_unanswered_sessions()

        self.assertGreaterEqual(notified_count, 1)

        # Verify auto-message was inserted
        msgs = frappe.db.get_all(
            "HD Chat Message",
            {"session": session_id, "sender_type": "system"},
            ["content"],
        )
        self.assertEqual(len(msgs), 1)
        self.assertIn("high volume", msgs[0].content)
        self._messages.extend(
            frappe.db.get_all("HD Chat Message", {"session": session_id}, pluck="name")
        )

        # Verify timeout_notified_at was set
        notified_at = frappe.db.get_value("HD Chat Session", doc.name, "timeout_notified_at")
        self.assertIsNotNone(notified_at)

        # Verify broadcast — at least one chat room publish
        chat_room_calls = [c for c in mock_publish.call_args_list if str(c.kwargs.get("room", "")).startswith("chat:")]
        self.assertGreater(len(chat_room_calls), 0, "Must broadcast to chat room on timeout")

        # Reset HD Settings
        frappe.db.set_value("HD Settings", None, "chat_response_timeout_seconds", 120)
        frappe.db.commit()

    @patch("helpdesk.helpdesk.chat.response_timeout.frappe.publish_realtime")
    def test_does_not_send_to_already_notified_session(self, mock_publish):
        """A session that already received the auto-message must not receive it again."""
        frappe.db.set_value("HD Settings", None, "chat_response_timeout_seconds", 60)
        _, session_id = self._make_waiting_session(started_minutes_ago=5, notified=True)

        from helpdesk.helpdesk.chat.response_timeout import check_unanswered_sessions
        check_unanswered_sessions()

        msgs = frappe.db.get_all(
            "HD Chat Message", {"session": session_id, "sender_type": "system"}, ["name"]
        )
        self._messages.extend([m.name for m in msgs])
        self.assertEqual(len(msgs), 0, "Already-notified session must not get duplicate message")

        frappe.db.set_value("HD Settings", None, "chat_response_timeout_seconds", 120)
        frappe.db.commit()

    @patch("helpdesk.helpdesk.chat.response_timeout.frappe.publish_realtime")
    def test_does_not_send_to_recent_session(self, mock_publish):
        """A session that started only 10 seconds ago must not receive auto-message."""
        frappe.db.set_value("HD Settings", None, "chat_response_timeout_seconds", 120)
        _, session_id = self._make_waiting_session(started_minutes_ago=0)

        from helpdesk.helpdesk.chat.response_timeout import check_unanswered_sessions
        check_unanswered_sessions()

        msgs = frappe.db.get_all(
            "HD Chat Message", {"session": session_id, "sender_type": "system"}, ["name"]
        )
        self._messages.extend([m.name for m in msgs])
        self.assertEqual(len(msgs), 0)
        chat_room_calls = [c for c in mock_publish.call_args_list if str(c.kwargs.get("room", "")).startswith("chat:")]
        self.assertEqual(len(chat_room_calls), 0, "Recent session must not receive broadcast")

        frappe.db.commit()

    @patch("helpdesk.helpdesk.chat.response_timeout.frappe.publish_realtime")
    def test_skips_session_with_agent_message(self, mock_publish):
        """A session where agent already replied must not receive the auto-message."""
        frappe.db.set_value("HD Settings", None, "chat_response_timeout_seconds", 60)
        doc, session_id = self._make_waiting_session(started_minutes_ago=5)

        # Insert an agent message
        agent_msg = frappe.get_doc({
            "doctype": "HD Chat Message",
            "session": session_id,
            "sender_type": "agent",
            "content": "Hello! How can I help you?",
            "sent_at": now_datetime(),
        })
        agent_msg.insert(ignore_permissions=True)
        frappe.db.commit()
        self._messages.append(agent_msg.name)

        from helpdesk.helpdesk.chat.response_timeout import check_unanswered_sessions
        check_unanswered_sessions()

        system_msgs = frappe.db.get_all(
            "HD Chat Message", {"session": session_id, "sender_type": "system"}, ["name"]
        )
        self._messages.extend([m.name for m in system_msgs])
        self.assertEqual(len(system_msgs), 0, "Session with agent reply must not get auto-message")

        frappe.db.set_value("HD Settings", None, "chat_response_timeout_seconds", 120)
        frappe.db.commit()


class TestChatAPIEndpoints(unittest.TestCase):
    """Integration tests for new REST API endpoints in helpdesk.api.chat (Story 3.4)."""

    def setUp(self):
        frappe.set_user("Administrator")
        self._sessions = []

    def tearDown(self):
        frappe.set_user("Administrator")
        for name in self._sessions:
            try:
                frappe.delete_doc("HD Chat Session", name, ignore_missing=True, force=True)
            except Exception:
                pass
        frappe.db.commit()

    def _make_session(self, email="api_test@example.com"):
        from helpdesk.helpdesk.chat.jwt_helper import generate_chat_token
        session_id = frappe.generate_hash(length=12)
        doc = frappe.get_doc({
            "doctype": "HD Chat Session",
            "session_id": session_id,
            "customer_email": email,
            "status": "active",
            "started_at": now_datetime(),
            "inactivity_timeout_minutes": 30,
        })
        doc.insert(ignore_permissions=True)
        frappe.db.commit()
        self._sessions.append(doc.name)
        return session_id, generate_chat_token(session_id, email)

    @patch("helpdesk.helpdesk.realtime.chat_handlers.frappe.publish_realtime")
    @patch("helpdesk.api.chat.frappe.db.get_single_value", return_value=1)
    def test_typing_start_endpoint(self, mock_setting, mock_publish):
        """typing_start endpoint broadcasts and returns ok."""
        session_id, token = self._make_session()
        from helpdesk.api.chat import typing_start
        result = typing_start(session_id=session_id, token=token, sender_name="Alice")
        self.assertTrue(result.get("ok"))
        chat_calls = [c for c in mock_publish.call_args_list if c.kwargs.get("event") == "typing_start"]
        self.assertEqual(len(chat_calls), 1)

    @patch("helpdesk.helpdesk.realtime.chat_handlers.frappe.publish_realtime")
    @patch("helpdesk.api.chat.frappe.db.get_single_value", return_value=1)
    def test_typing_stop_endpoint(self, mock_setting, mock_publish):
        """typing_stop endpoint broadcasts and returns ok."""
        session_id, token = self._make_session()
        from helpdesk.api.chat import typing_stop
        result = typing_stop(session_id=session_id, token=token)
        self.assertTrue(result.get("ok"))
        chat_calls = [c for c in mock_publish.call_args_list if c.kwargs.get("event") == "typing_stop"]
        self.assertEqual(len(chat_calls), 1)

    @patch("helpdesk.helpdesk.realtime.chat_handlers.frappe.publish_realtime")
    @patch("helpdesk.api.chat.frappe.db.get_single_value", return_value=1)
    def test_mark_messages_read_endpoint(self, mock_setting, mock_publish):
        """mark_messages_read endpoint sets is_read and returns ok."""
        session_id, token = self._make_session()
        msg = frappe.get_doc({
            "doctype": "HD Chat Message",
            "session": session_id,
            "sender_type": "agent",
            "content": "hi",
            "sent_at": now_datetime(),
        })
        msg.insert(ignore_permissions=True)
        frappe.db.commit()

        from helpdesk.api.chat import mark_messages_read
        result = mark_messages_read(
            session_id=session_id,
            token=token,
            message_ids=[msg.message_id],
        )
        self.assertTrue(result.get("ok"))

        # Cleanup
        frappe.delete_doc("HD Chat Message", msg.name, force=True)
        frappe.db.commit()

    def test_send_message_returns_status_sent(self):
        """send_message must include status='sent' in the response (AC #2)."""
        session_id, token = self._make_session()
        with (
            patch("helpdesk.api.chat.frappe.db.get_single_value", return_value=1),
            patch("helpdesk.api.chat._create_ticket_for_session"),
            patch("helpdesk.api.chat.frappe.publish_realtime"),
        ):
            from helpdesk.api.chat import send_message
            result = send_message(
                session_id=session_id,
                content="Hello from test",
                token=token,
            )
        self.assertEqual(result.get("status"), "sent", "send_message must return status='sent'")
        self.assertIn("message_id", result)

        # Cleanup inserted message
        frappe.db.delete("HD Chat Message", {"session": session_id})
        frappe.db.commit()
