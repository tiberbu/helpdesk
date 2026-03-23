# Copyright (c) 2026, Frappe Technologies Pvt. Ltd. and contributors
# For license information, please see license.txt

"""Chat session API endpoints.

Whitelisted methods:
    create_session   — pre-chat form submission; creates session + returns JWT
    send_message     — customer/agent sends a message to a session
    end_session      — end a chat session (customer via JWT or agent via role)
    get_sessions     — list active/waiting sessions (agent-only)
    transfer_session — transfer session to another agent (agent-only)

Security model (NFR-SE-02, ADR-05):
    - Customers authenticate via short-lived JWT in every send_message call.
    - Agent endpoints require HD Agent / System Manager / HD Admin role.
    - All message content is HTML-sanitized before storage (NFR-SE-06).
"""

import frappe
from frappe import _

from helpdesk.helpdesk.chat.jwt_helper import generate_chat_token, validate_chat_token


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------

def _check_chat_enabled():
    """Raise if the chat feature flag is disabled in HD Settings."""
    enabled = frappe.db.get_single_value("HD Settings", "chat_enabled")
    if not enabled:
        frappe.throw(_("Live chat is not enabled."), frappe.ValidationError)


def _sanitize(content: str) -> str:
    """HTML-sanitize message content (NFR-SE-06)."""
    if not content:
        return ""
    try:
        return frappe.utils.html_utils.clean_html(content)
    except Exception:
        return frappe.utils.strip_html(content)


def _is_agent() -> bool:
    """Return True if the current user has an agent-level role."""
    user_roles = frappe.get_roles()
    return bool({"HD Agent", "HD Admin", "System Manager", "Administrator"} & set(user_roles))


def _append_system_message(session_name: str, text: str) -> None:
    """Insert a system-type HD Chat Message into the session."""
    frappe.get_doc(
        {
            "doctype": "HD Chat Message",
            "session": session_name,
            "sender_type": "system",
            "content": text,
            "sent_at": frappe.utils.now_datetime(),
        }
    ).insert(ignore_permissions=True)


# ---------------------------------------------------------------------------
# Public API
# ---------------------------------------------------------------------------

@frappe.whitelist(allow_guest=True)
def create_session(email: str, name: str = "", subject: str = "", brand: str = "") -> dict:
    """Create a new HD Chat Session and return a JWT token.

    Called when a customer submits the pre-chat form.

    Parameters
    ----------
    email   : str  Customer email address (required).
    name    : str  Customer display name (optional).
    subject : str  Initial subject / question (optional).
    brand   : str  HD Brand name (optional).

    Returns
    -------
    dict with keys: session_id, token, status
    """
    # Validate email format
    if not email or not frappe.utils.validate_email_address(email):
        frappe.throw(_("A valid email address is required to start a chat."), frappe.ValidationError)

    session_id = frappe.generate_hash(length=20)

    session_doc = frappe.get_doc(
        {
            "doctype": "HD Chat Session",
            "session_id": session_id,
            "customer_email": email.strip().lower(),
            "customer_name": (name or "").strip() or email.strip().lower(),
            "status": "waiting",
            "started_at": frappe.utils.now_datetime(),
            "inactivity_timeout_minutes": 30,
            "brand": brand or None,
        }
    )
    session_doc.insert(ignore_permissions=True)

    token = generate_chat_token(session_id, email)

    return {
        "session_id": session_id,
        "token": token,
        "status": "waiting",
    }


@frappe.whitelist(allow_guest=True)
def send_message(session_id: str, content: str, token: str, attachment: str = "") -> dict:
    """Send a message within a chat session.

    Validates the JWT, sanitizes content, creates an HD Chat Message, and
    on the first customer message creates an HD Ticket via the channel normalizer.

    Parameters
    ----------
    session_id  : str  The HD Chat Session session_id.
    content     : str  Message body (plain text or HTML).
    token       : str  JWT issued by create_session.
    attachment  : str  Optional file URL (Frappe Attach field value).

    Returns
    -------
    dict with keys: message_id, sent_at
    """
    # Authenticate customer
    validate_chat_token(token, session_id)

    session_doc = frappe.get_doc("HD Chat Session", session_id)

    if session_doc.status == "ended":
        frappe.throw(_("This chat session has already ended."), frappe.ValidationError)

    sanitized = _sanitize(content)

    msg = frappe.get_doc(
        {
            "doctype": "HD Chat Message",
            "session": session_id,
            "sender_type": "customer",
            "sender_email": session_doc.customer_email,
            "content": sanitized,
            "sent_at": frappe.utils.now_datetime(),
            "attachment": attachment or None,
        }
    )
    msg.insert(ignore_permissions=True)

    # First customer message → create HD Ticket via channel normalizer
    if not session_doc.ticket:
        _create_ticket_for_session(session_doc, sanitized)

    # Publish real-time event (AR-07 room naming: chat:{session_id})
    try:
        frappe.publish_realtime(
            event="chat_message",
            message={
                "session_id": session_id,
                "message_id": msg.message_id,
                "content": sanitized,
                "sender_type": "customer",
                "sent_at": str(msg.sent_at),
            },
            room=f"chat:{session_id}",
        )
    except Exception:
        pass  # Real-time failure must not block message delivery (NFR-A-01)

    return {
        "message_id": msg.message_id,
        "sent_at": str(msg.sent_at),
    }


@frappe.whitelist(allow_guest=True)
def end_session(session_id: str, token: str = "") -> dict:
    """End a chat session.

    Callable by the owning customer (with valid JWT) or any agent (role check).

    Parameters
    ----------
    session_id : str  The HD Chat Session session_id.
    token      : str  JWT (required for guest callers; optional for agents).

    Returns
    -------
    dict with keys: session_id, status
    """
    if not _is_agent():
        if not token:
            frappe.throw(_("Authentication token required."), frappe.AuthenticationError)
        validate_chat_token(token, session_id)

    session_doc = frappe.get_doc("HD Chat Session", session_id)

    if session_doc.status == "ended":
        return {"session_id": session_id, "status": "ended"}

    session_doc.status = "ended"
    session_doc.ended_at = frappe.utils.now_datetime()
    session_doc.save(ignore_permissions=True)

    _append_system_message(session_id, "This chat has ended.")

    try:
        frappe.publish_realtime(
            event="session_ended",
            message={"session_id": session_id},
            room=f"chat:{session_id}",
        )
    except Exception:
        pass

    return {"session_id": session_id, "status": "ended"}


@frappe.whitelist()
def get_sessions(status: str = "") -> list:
    """Return a list of active/waiting chat sessions (agent-only).

    Parameters
    ----------
    status : str  Optional filter: "waiting", "active", or "ended".

    Returns
    -------
    list of dicts, ordered by started_at ascending.
    """
    if not _is_agent():
        frappe.throw(_("Only agents can list chat sessions."), frappe.PermissionError)

    filters = {}
    if status:
        filters["status"] = status
    else:
        filters["status"] = ["in", ["waiting", "active"]]

    sessions = frappe.db.get_all(
        "HD Chat Session",
        filters=filters,
        fields=[
            "session_id",
            "customer_email",
            "customer_name",
            "status",
            "started_at",
            "agent",
            "ticket",
        ],
        order_by="started_at asc",
    )

    # Annotate with message count
    for session in sessions:
        session["message_count"] = frappe.db.count(
            "HD Chat Message", {"session": session["session_id"]}
        )

    return sessions


@frappe.whitelist()
def transfer_session(session_id: str, target_agent_email: str) -> dict:
    """Transfer a chat session to another agent.

    Parameters
    ----------
    session_id         : str  The HD Chat Session session_id.
    target_agent_email : str  Email of the agent to transfer to.

    Returns
    -------
    dict with keys: session_id, agent
    """
    if not _is_agent():
        frappe.throw(_("Only agents can transfer chat sessions."), frappe.PermissionError)

    # Verify target agent exists
    agent_name = frappe.db.get_value("HD Agent", {"user": target_agent_email}, "name")
    if not agent_name:
        frappe.throw(
            _("Agent with email '{0}' not found.").format(target_agent_email),
            frappe.DoesNotExistError,
        )

    session_doc = frappe.get_doc("HD Chat Session", session_id)

    if session_doc.status == "ended":
        frappe.throw(_("Cannot transfer an ended session."), frappe.ValidationError)

    session_doc.agent = agent_name
    session_doc.save(ignore_permissions=True)

    _append_system_message(
        session_id,
        f"Chat transferred to agent {target_agent_email}.",
    )

    # Notify both the session room and the new agent's room (AR-07)
    try:
        frappe.publish_realtime(
            event="session_transferred",
            message={"session_id": session_id, "new_agent": target_agent_email},
            room=f"chat:{session_id}",
        )
        frappe.publish_realtime(
            event="chat_assigned",
            message={"session_id": session_id},
            room=f"agent:{target_agent_email}",
        )
    except Exception:
        pass

    return {"session_id": session_id, "agent": agent_name}


# ---------------------------------------------------------------------------
# Internal helpers
# ---------------------------------------------------------------------------

def _create_ticket_for_session(session_doc, first_message_content: str):
    """Create an HD Ticket for the session's first customer message.

    Uses the channel normalizer (Story 3.1 / ADR-07) to ensure all
    channel sources produce tickets through the same pathway.
    """
    try:
        from helpdesk.helpdesk.channels.base import ChannelMessage
        from helpdesk.helpdesk.channels.normalizer import ChannelNormalizer

        channel_msg = ChannelMessage(
            source="chat",
            sender_email=session_doc.customer_email,
            sender_name=session_doc.customer_name or session_doc.customer_email,
            subject=f"Chat session {session_doc.session_id}",
            content=first_message_content,
            metadata={"chat_session_id": session_doc.session_id},
        )

        normalizer = ChannelNormalizer()
        ticket = normalizer.process(channel_msg)

        # Link the ticket back to the session
        frappe.db.set_value("HD Chat Session", session_doc.session_id, "ticket", ticket.name)

    except Exception:
        frappe.log_error(
            frappe.get_traceback(),
            "ChatAPI: failed to create ticket for session {0}".format(session_doc.session_id),
        )
