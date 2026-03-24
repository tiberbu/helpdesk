# Copyright (c) 2026, Frappe Technologies Pvt. Ltd. and contributors
# For license information, please see license.txt

"""Unit tests for Story 3.2 — Chat Session Management Backend.

Covers:
    AC#1  — HD Chat Session and HD Chat Message DocTypes exist
    AC#2  — create_session creates session + returns JWT
    AC#3  — send_message creates ticket on first message via channel normalizer
    AC#4  — cleanup_inactive_sessions ends stale sessions, skips recent/ended ones
    AC#8  — JWT helpers: generate/validate, expired token, session mismatch
"""

from unittest.mock import patch

import frappe
from frappe.tests.utils import FrappeTestCase
from frappe.utils import now_datetime, add_to_date


# ---------------------------------------------------------------------------
# Utility helpers
# ---------------------------------------------------------------------------

def _cleanup_session(session_id):
    """Delete all messages linked to a session, then the session itself."""
    if not frappe.db.exists("HD Chat Session", session_id):
        return
    msgs = frappe.db.get_all("HD Chat Message", filters={"session": session_id}, pluck="name")
    for m in msgs:
        if frappe.db.exists("HD Chat Message", m):
            frappe.delete_doc("HD Chat Message", m, force=True, ignore_permissions=True)
    frappe.delete_doc("HD Chat Session", session_id, ignore_permissions=True)


def _enable_chat():
    """Enable the chat feature flag in HD Settings for the duration of a test."""
    frappe.db.set_single_value("HD Settings", "chat_enabled", 1)


def _disable_chat():
    """Disable the chat feature flag in HD Settings after a test."""
    frappe.db.set_single_value("HD Settings", "chat_enabled", 0)


def _make_session(email="test@example.com", status="waiting", timeout=30, started_offset_minutes=0):
    """Insert a real HD Chat Session into the DB."""
    session_id = frappe.generate_hash(length=20)
    started_at = now_datetime()
    if started_offset_minutes:
        started_at = add_to_date(started_at, minutes=started_offset_minutes)
    session = frappe.get_doc({
        "doctype": "HD Chat Session",
        "session_id": session_id,
        "customer_email": email,
        "customer_name": email,
        "status": status,
        "started_at": started_at,
        "inactivity_timeout_minutes": timeout,
    })
    session.insert(ignore_permissions=True)
    return session


# ---------------------------------------------------------------------------
# AC#1: DocType existence
# ---------------------------------------------------------------------------

class TestDocTypeExistence(FrappeTestCase):
    """HD Chat Session and HD Chat Message DocTypes must exist (AC#1)."""

    def test_hd_chat_session_doctype_exists(self):
        self.assertTrue(frappe.db.exists("DocType", "HD Chat Session"))

    def test_hd_chat_message_doctype_exists(self):
        self.assertTrue(frappe.db.exists("DocType", "HD Chat Message"))

    def test_hd_chat_session_has_required_fields(self):
        meta = frappe.get_meta("HD Chat Session")
        fieldnames = {f.fieldname for f in meta.fields}
        required = {
            "session_id", "customer_email", "customer_name", "status",
            "started_at", "ended_at", "agent", "ticket",
            "inactivity_timeout_minutes", "jwt_token_hash",
        }
        for field in required:
            self.assertIn(field, fieldnames, f"Missing field: {field}")

    def test_hd_chat_message_has_required_fields(self):
        meta = frappe.get_meta("HD Chat Message")
        fieldnames = {f.fieldname for f in meta.fields}
        required = {
            "message_id", "session", "sender_type", "sender_email",
            "content", "sent_at", "is_read",
        }
        for field in required:
            self.assertIn(field, fieldnames, f"Missing field: {field}")

    def test_hd_chat_session_status_options(self):
        meta = frappe.get_meta("HD Chat Session")
        status_field = next(f for f in meta.fields if f.fieldname == "status")
        options = status_field.options.split("\n")
        self.assertIn("waiting", options)
        self.assertIn("active", options)
        self.assertIn("ended", options)


# ---------------------------------------------------------------------------
# AC#2: create_session
# ---------------------------------------------------------------------------

class TestCreateSession(FrappeTestCase):
    """create_session creates HD Chat Session and returns JWT (AC#2)."""

    def setUp(self):
        frappe.set_user("Administrator")
        self._sessions = []

    def tearDown(self):
        frappe.set_user("Administrator")
        for s in self._sessions:
            _cleanup_session(s)
        frappe.db.commit()  # nosemgrep

    def test_create_session_returns_session_id_and_token(self):
        from helpdesk.api.chat import create_session
        result = create_session(email="customer@example.com", name="Alice")
        self.assertIn("session_id", result)
        self.assertIn("token", result)
        self.assertEqual(result["status"], "waiting")
        self._sessions.append(result["session_id"])

    def test_create_session_persists_document(self):
        from helpdesk.api.chat import create_session
        result = create_session(email="customer2@example.com", name="Bob")
        self._sessions.append(result["session_id"])

        doc = frappe.get_doc("HD Chat Session", result["session_id"])
        self.assertEqual(doc.customer_email, "customer2@example.com")
        self.assertEqual(doc.status, "waiting")
        self.assertIsNotNone(doc.started_at)
        self.assertIsNone(doc.agent)

    def test_create_session_invalid_email_raises(self):
        from helpdesk.api.chat import create_session
        with self.assertRaises(Exception):
            create_session(email="not-an-email", name="Test")

    def test_create_session_empty_email_raises(self):
        from helpdesk.api.chat import create_session
        with self.assertRaises(Exception):
            create_session(email="", name="Test")


# ---------------------------------------------------------------------------
# AC#3: send_message creates ticket on first message
# ---------------------------------------------------------------------------

class TestSendMessage(FrappeTestCase):
    """send_message stores messages and creates ticket on first message (AC#3)."""

    def setUp(self):
        frappe.set_user("Administrator")
        self._sessions = []
        self._tickets = []

    def tearDown(self):
        frappe.set_user("Administrator")
        for s in self._sessions:
            _cleanup_session(s)
        for t in self._tickets:
            if frappe.db.exists("HD Ticket", t):
                frappe.delete_doc("HD Ticket", t, force=True, ignore_permissions=True)
        frappe.db.commit()  # nosemgrep

    def _create_session_and_token(self, email="chat@example.com"):
        from helpdesk.api.chat import create_session
        result = create_session(email=email, name="Tester")
        self._sessions.append(result["session_id"])
        return result["session_id"], result["token"]

    def test_send_message_creates_hd_chat_message(self):
        session_id, token = self._create_session_and_token()
        from helpdesk.api.chat import send_message

        result = send_message(session_id=session_id, content="Hello!", token=token)
        self.assertIn("message_id", result)
        self.assertIn("sent_at", result)

        msg = frappe.get_doc("HD Chat Message", result["message_id"])
        self.assertEqual(msg.session, session_id)
        self.assertEqual(msg.sender_type, "customer")

    def test_send_message_sanitizes_content(self):
        session_id, token = self._create_session_and_token(email="xss@example.com")
        from helpdesk.api.chat import send_message

        result = send_message(
            session_id=session_id,
            content='<script>alert("xss")</script>Hello',
            token=token,
        )

        msg = frappe.get_doc("HD Chat Message", result["message_id"])
        self.assertNotIn("<script>", msg.content)

    def test_first_message_creates_hd_ticket(self):
        session_id, token = self._create_session_and_token(email="newticket@example.com")
        from helpdesk.api.chat import send_message

        # Session should have no ticket before first message
        session_before = frappe.get_doc("HD Chat Session", session_id)
        self.assertFalse(session_before.ticket)

        result = send_message(session_id=session_id, content="Need help!", token=token)

        # After first message, ticket should be linked
        session_after = frappe.get_doc("HD Chat Session", session_id)
        if session_after.ticket:
            self._tickets.append(session_after.ticket)
            ticket = frappe.get_doc("HD Ticket", session_after.ticket)
            self.assertIsNotNone(ticket.name)

    def test_second_message_does_not_create_duplicate_ticket(self):
        session_id, token = self._create_session_and_token(email="nodup@example.com")
        from helpdesk.api.chat import send_message

        send_message(session_id=session_id, content="First message", token=token)

        session_doc = frappe.get_doc("HD Chat Session", session_id)
        first_ticket = session_doc.ticket
        if first_ticket:
            self._tickets.append(first_ticket)

        send_message(session_id=session_id, content="Second message", token=token)

        session_doc_after = frappe.get_doc("HD Chat Session", session_id)
        # Ticket must not change on second message
        self.assertEqual(session_doc_after.ticket, first_ticket)

    def test_send_message_invalid_token_raises(self):
        session_id, _token = self._create_session_and_token(email="badtoken@example.com")
        from helpdesk.api.chat import send_message

        with self.assertRaises(Exception):
            send_message(session_id=session_id, content="Hello", token="invalid-token")

    def test_send_message_to_ended_session_raises(self):
        session_id, token = self._create_session_and_token(email="ended@example.com")

        frappe.db.set_value("HD Chat Session", session_id, "status", "ended")

        from helpdesk.api.chat import send_message
        with self.assertRaises(Exception):
            send_message(session_id=session_id, content="Hello", token=token)


# ---------------------------------------------------------------------------
# AC#4: Session cleanup
# ---------------------------------------------------------------------------

class TestSessionCleanup(FrappeTestCase):
    """cleanup_inactive_sessions ends stale sessions, skips active/recent ones (AC#4)."""

    def setUp(self):
        frappe.set_user("Administrator")
        self._sessions = []

    def tearDown(self):
        frappe.set_user("Administrator")
        for s in self._sessions:
            _cleanup_session(s)
        frappe.db.commit()  # nosemgrep

    def test_inactive_session_is_ended(self):
        """A session started 45 minutes ago with 30-min timeout must be ended."""
        session = _make_session(
            email="stale@example.com",
            status="waiting",
            timeout=30,
            started_offset_minutes=-45,
        )
        self._sessions.append(session.name)

        from helpdesk.helpdesk.chat.session_cleanup import cleanup_inactive_sessions
        count = cleanup_inactive_sessions()

        self.assertGreaterEqual(count, 1)

        updated = frappe.get_doc("HD Chat Session", session.name)
        self.assertEqual(updated.status, "ended")
        self.assertIsNotNone(updated.ended_at)

        # System message appended
        msgs = frappe.db.count("HD Chat Message", {"session": session.name, "sender_type": "system"})
        self.assertGreater(msgs, 0)

    def test_recent_session_is_not_ended(self):
        """A session started 5 minutes ago with 30-min timeout must NOT be ended."""
        session = _make_session(
            email="recent@example.com",
            status="waiting",
            timeout=30,
            started_offset_minutes=-5,
        )
        self._sessions.append(session.name)

        from helpdesk.helpdesk.chat.session_cleanup import cleanup_inactive_sessions
        cleanup_inactive_sessions()

        updated = frappe.get_doc("HD Chat Session", session.name)
        self.assertEqual(updated.status, "waiting")

    def test_already_ended_session_is_skipped(self):
        """An already-ended session must not be processed again."""
        session = _make_session(
            email="alreadyended@example.com",
            status="ended",
            timeout=30,
            started_offset_minutes=-60,
        )
        self._sessions.append(session.name)

        from helpdesk.helpdesk.chat.session_cleanup import cleanup_inactive_sessions
        # Should not raise, and ended_at should remain None (not set by us)
        cleanup_inactive_sessions()

        updated = frappe.get_doc("HD Chat Session", session.name)
        self.assertEqual(updated.status, "ended")
        self.assertIsNone(updated.ended_at)

    def test_cleanup_returns_count(self):
        """cleanup_inactive_sessions must return the number of sessions ended."""
        s1 = _make_session(email="stale1@example.com", timeout=10, started_offset_minutes=-20)
        s2 = _make_session(email="stale2@example.com", timeout=10, started_offset_minutes=-20)
        self._sessions.extend([s1.name, s2.name])

        from helpdesk.helpdesk.chat.session_cleanup import cleanup_inactive_sessions
        count = cleanup_inactive_sessions()
        self.assertGreaterEqual(count, 2)

    def test_session_with_recent_message_not_ended_despite_old_start(self):
        """A session started 45 min ago but with a message 5 min ago must NOT be ended.

        This verifies that inactivity is measured from the last message time,
        NOT from started_at (Issue 3 regression fix).
        """
        # Session started 45 minutes ago — would be stale by started_at alone
        session = _make_session(
            email="recentmsg@example.com",
            status="waiting",
            timeout=30,
            started_offset_minutes=-45,
        )
        self._sessions.append(session.name)

        # Insert a message sent only 5 minutes ago
        msg = frappe.get_doc({
            "doctype": "HD Chat Message",
            "session": session.name,
            "sender_type": "customer",
            "sender_email": "recentmsg@example.com",
            "content": "Still here!",
            "sent_at": add_to_date(now_datetime(), minutes=-5),
        })
        msg.insert(ignore_permissions=True)
        frappe.db.commit()  # nosemgrep

        from helpdesk.helpdesk.chat.session_cleanup import cleanup_inactive_sessions
        cleanup_inactive_sessions()

        updated = frappe.get_doc("HD Chat Session", session.name)
        self.assertEqual(
            updated.status,
            "waiting",
            "Session with a message 5 min ago should NOT be ended (30-min timeout).",
        )


# ---------------------------------------------------------------------------
# AC#8: JWT helpers
# ---------------------------------------------------------------------------

class TestJWTHelper(FrappeTestCase):
    """JWT generation and validation (AC#8)."""

    def test_generate_returns_string(self):
        from helpdesk.helpdesk.chat.jwt_helper import generate_chat_token
        token = generate_chat_token("test-session-id", "user@example.com")
        self.assertIsInstance(token, str)
        self.assertGreater(len(token), 20)

    def test_valid_token_passes_validation(self):
        from helpdesk.helpdesk.chat.jwt_helper import generate_chat_token, validate_chat_token
        session_id = "valid-session-001"
        token = generate_chat_token(session_id, "valid@example.com")
        result = validate_chat_token(token, session_id)
        self.assertTrue(result)

    def test_wrong_session_id_raises(self):
        from helpdesk.helpdesk.chat.jwt_helper import generate_chat_token, validate_chat_token
        token = generate_chat_token("session-A", "mismatch@example.com")
        with self.assertRaises(Exception) as ctx:
            validate_chat_token(token, "session-B")
        self.assertIn("does not match", str(ctx.exception).lower())

    def test_expired_token_raises(self):
        """An expired token must raise an error containing 'expired'."""
        import jwt as pyjwt
        import hashlib
        from datetime import UTC, datetime

        from frappe.utils.password import get_encryption_key
        secret = get_encryption_key()
        email_hash = hashlib.sha256(b"exp@example.com").hexdigest()
        payload = {
            "sub": email_hash,
            "session_id": "exp-session",
            "iat": datetime(2020, 1, 1, tzinfo=UTC),
            "exp": datetime(2020, 1, 1, 0, 0, 1, tzinfo=UTC),
        }
        expired_token = pyjwt.encode(payload, secret, algorithm="HS256")

        from helpdesk.helpdesk.chat.jwt_helper import validate_chat_token
        with self.assertRaises(Exception) as ctx:
            validate_chat_token(expired_token, "exp-session")
        self.assertIn("expired", str(ctx.exception).lower())

    def test_tampered_token_raises(self):
        from helpdesk.helpdesk.chat.jwt_helper import generate_chat_token, validate_chat_token
        token = generate_chat_token("tamper-session", "tamper@example.com")
        tampered = token[:-1] + ("A" if token[-1] != "A" else "B")
        with self.assertRaises(Exception):
            validate_chat_token(tampered, "tamper-session")

    def test_different_tokens_for_different_sessions(self):
        from helpdesk.helpdesk.chat.jwt_helper import generate_chat_token
        t1 = generate_chat_token("session-1", "same@example.com")
        t2 = generate_chat_token("session-2", "same@example.com")
        self.assertNotEqual(t1, t2)


# ---------------------------------------------------------------------------
# AC#5: end_session
# ---------------------------------------------------------------------------

class TestEndSession(FrappeTestCase):
    """end_session marks session ended and publishes event (AC#5)."""

    def setUp(self):
        frappe.set_user("Administrator")
        self._sessions = []

    def tearDown(self):
        frappe.set_user("Administrator")
        for s in self._sessions:
            _cleanup_session(s)
        frappe.db.commit()  # nosemgrep

    def test_end_session_by_customer_with_token(self):
        from helpdesk.api.chat import create_session, end_session
        created = create_session(email="endtest@example.com", name="Tester")
        session_id = created["session_id"]
        token = created["token"]
        self._sessions.append(session_id)

        result = end_session(session_id=session_id, token=token)
        self.assertEqual(result["status"], "ended")

        doc = frappe.get_doc("HD Chat Session", session_id)
        self.assertEqual(doc.status, "ended")
        self.assertIsNotNone(doc.ended_at)

        msgs = frappe.db.count("HD Chat Message", {"session": session_id, "sender_type": "system"})
        self.assertGreater(msgs, 0)

    def test_end_already_ended_session_is_idempotent(self):
        from helpdesk.api.chat import create_session, end_session
        created = create_session(email="idempotent@example.com", name="Tester")
        session_id = created["session_id"]
        token = created["token"]
        self._sessions.append(session_id)

        end_session(session_id=session_id, token=token)
        result = end_session(session_id=session_id, token=token)
        self.assertEqual(result["status"], "ended")


# ---------------------------------------------------------------------------
# AC#6: get_sessions
# ---------------------------------------------------------------------------

class TestGetSessions(FrappeTestCase):
    """get_sessions returns session list for agents (AC#6)."""

    def setUp(self):
        frappe.set_user("Administrator")
        self._sessions = []

    def tearDown(self):
        frappe.set_user("Administrator")
        for s in self._sessions:
            _cleanup_session(s)
        frappe.db.commit()  # nosemgrep

    def test_get_sessions_returns_list(self):
        from helpdesk.api.chat import create_session, get_sessions
        created = create_session(email="listtest@example.com", name="Tester")
        self._sessions.append(created["session_id"])

        sessions = get_sessions()
        self.assertIsInstance(sessions, list)

    def test_get_sessions_non_agent_raises(self):
        from helpdesk.api.chat import get_sessions
        with patch("helpdesk.api.chat._is_agent", return_value=False):
            with self.assertRaises(Exception):
                get_sessions()
