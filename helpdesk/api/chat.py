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
    - Agent endpoints require Agent / Agent Manager / HD Admin role (see helpdesk.utils.is_agent).
    - All message content is HTML-sanitized before storage (NFR-SE-06).
"""

import frappe
from frappe import _

from helpdesk.helpdesk.chat.jwt_helper import generate_chat_token, validate_chat_token
from helpdesk.utils import is_agent


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
    """Return True if the current user has an agent-level role.

    Delegates to the canonical ``helpdesk.utils.is_agent`` so role names stay
    consistent across the whole app.
    """
    return is_agent()


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
    _check_chat_enabled()

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
            "brand": brand if (brand and brand != "default") else None,
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
    _check_chat_enabled()

    is_agent_sender = _is_agent()
    if not is_agent_sender:
        # Authenticate customer via JWT
        validate_chat_token(token, session_id)

    session_doc = frappe.get_doc("HD Chat Session", session_id)

    if session_doc.status == "ended":
        frappe.throw(_("This chat session has already ended."), frappe.ValidationError)

    sanitized = _sanitize(content)

    msg = frappe.get_doc(
        {
            "doctype": "HD Chat Message",
            "session": session_id,
            "sender_type": "agent" if is_agent_sender else "customer",
            "sender_email": frappe.session.user if is_agent_sender else session_doc.customer_email,
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
                "sender_type": "agent" if is_agent_sender else "customer",
                "sent_at": str(msg.sent_at),
            },
            room=f"chat:{session_id}",
        )
    except Exception:
        pass  # Real-time failure must not block message delivery (NFR-A-01)

    return {
        "message_id": msg.message_id,
        "sent_at": str(msg.sent_at),
        "status": "sent",
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
    _check_chat_enabled()

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
    _check_chat_enabled()

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
    _check_chat_enabled()

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

@frappe.whitelist(allow_guest=True)
def get_availability(brand: str = "") -> dict:
    """Return whether any agents are currently available to chat.

    Used by the widget to decide whether to show PreChatForm (online) or
    OfflineForm (offline).

    Parameters
    ----------
    brand : str  Optional HD Brand name — reserved for future team filtering.

    Returns
    -------
    dict with key: available (bool)
    """
    count = frappe.db.count("HD Agent", {"is_active": 1, "chat_availability": "Online"})
    return {"available": count > 0}


@frappe.whitelist(allow_guest=True)
def get_widget_config(brand: str = "") -> dict:
    """Return branding configuration for the chat widget.

    Parameters
    ----------
    brand : str  Optional HD Brand name.  Returns defaults when omitted or
                 when HD Brand DocType does not exist yet.

    Returns
    -------
    dict with keys: primary_color, logo, greeting, name
    """
    defaults = {
        "primary_color": "#4f46e5",
        "logo": None,
        "greeting": "Hi! How can we help you today?",
        "name": "Support",
    }

    if not brand or brand == "default":
        return defaults

    # HD Brand DocType may not exist yet — guard gracefully
    if not frappe.db.exists("DocType", "HD Brand"):
        return defaults

    brand_doc = frappe.db.get_value(
        "HD Brand",
        brand,
        ["primary_color", "logo", "chat_greeting", "name"],
        as_dict=True,
    )
    if not brand_doc:
        return defaults

    return {
        "primary_color": brand_doc.get("primary_color") or defaults["primary_color"],
        "logo": brand_doc.get("logo"),
        "greeting": brand_doc.get("chat_greeting") or defaults["greeting"],
        "name": brand_doc.get("name") or defaults["name"],
    }


@frappe.whitelist(allow_guest=True)
def create_offline_ticket(
    name: str,
    email: str,
    subject: str,
    message: str,
    brand: str = "",
) -> dict:
    """Create an HD Ticket from the widget's offline "Leave a message" form.

    Does NOT create a chat session — the customer will be followed up via
    email using normal ticket workflow.

    Parameters
    ----------
    name    : str  Customer display name.
    email   : str  Customer email address.
    subject : str  Ticket subject.
    message : str  Message body.
    brand   : str  HD Brand name (optional).

    Returns
    -------
    dict with key: ticket_id
    """
    if not email or not frappe.utils.validate_email_address(email):
        frappe.throw(_("A valid email address is required."), frappe.ValidationError)

    sanitized_message = _sanitize(message)

    # Elevate to Administrator: Guest lacks HD Ticket create permission (NFR-SE-02).
    original_user = frappe.session.user
    frappe.set_user("Administrator")
    try:
        from helpdesk.helpdesk.channels.base import ChannelMessage
        from helpdesk.helpdesk.channels.normalizer import ChannelNormalizer

        channel_msg = ChannelMessage(
            source="portal",
            sender_email=email.strip().lower(),
            sender_name=(name or "").strip() or email.strip().lower(),
            subject=subject.strip() or f"Message from {email}",
            content=sanitized_message,
            metadata={"brand": brand or None, "offline_form": True},
        )
        normalizer = ChannelNormalizer()
        ticket = normalizer.process(channel_msg)
        return {"ticket_id": ticket.name}

    except Exception:
        # Fallback: create ticket directly without channel normalizer
        frappe.log_error(
            frappe.get_traceback(),
            "ChatAPI: create_offline_ticket channel normalizer failed — using fallback",
        )
        ticket = frappe.get_doc(
            {
                "doctype": "HD Ticket",
                "subject": subject.strip() or f"Message from {email}",
                "raised_by": email.strip().lower(),
                "description": sanitized_message,
                "via_customer_portal": 1,
            }
        )
        ticket.insert(ignore_permissions=True)
        return {"ticket_id": ticket.name}

    finally:
        frappe.set_user(original_user)


@frappe.whitelist(allow_guest=True)
def get_messages(session_id: str, token: str) -> list:
    """Return all messages for a chat session (paginated from oldest to newest).

    Parameters
    ----------
    session_id : str  The HD Chat Session session_id.
    token      : str  JWT issued by create_session (customer authentication).

    Returns
    -------
    list of message dicts ordered by sent_at ascending.
    """
    validate_chat_token(token, session_id)

    messages = frappe.db.get_all(
        "HD Chat Message",
        filters={"session": session_id},
        fields=["message_id", "sender_type", "sender_email", "content", "sent_at", "is_read"],
        order_by="sent_at asc",
    )
    return messages


# ---------------------------------------------------------------------------
# Internal helpers
# ---------------------------------------------------------------------------


@frappe.whitelist(allow_guest=True)
def typing_start(session_id: str, token: str, sender_name: str = "") -> dict:
    """Broadcast a typing-start indicator to the chat room (AC #3, Story 3.4).

    Parameters
    ----------
    session_id  : str  HD Chat Session session_id.
    token       : str  Customer JWT.
    sender_name : str  Display name shown in the typing indicator.

    Returns
    -------
    dict with key: ok (bool)
    """
    _check_chat_enabled()
    from helpdesk.helpdesk.realtime.chat_handlers import handle_typing_start
    handle_typing_start(session_id, token, sender_name)
    return {"ok": True}


@frappe.whitelist(allow_guest=True)
def typing_stop(session_id: str, token: str) -> dict:
    """Broadcast a typing-stop event to clear the remote typing indicator (AC #3, Story 3.4).

    Parameters
    ----------
    session_id : str  HD Chat Session session_id.
    token      : str  Customer JWT.

    Returns
    -------
    dict with key: ok (bool)
    """
    _check_chat_enabled()
    from helpdesk.helpdesk.realtime.chat_handlers import handle_typing_stop
    handle_typing_stop(session_id, token)
    return {"ok": True}


@frappe.whitelist(allow_guest=True)
def message_delivered(session_id: str, token: str, message_id: str) -> dict:
    """Notify the sender that their message was delivered (AC #2, Story 3.4).

    Parameters
    ----------
    session_id : str  HD Chat Session session_id.
    token      : str  Recipient JWT.
    message_id : str  HD Chat Message message_id that was delivered.

    Returns
    -------
    dict with key: ok (bool)
    """
    _check_chat_enabled()
    from helpdesk.helpdesk.realtime.chat_handlers import handle_message_delivered
    handle_message_delivered(session_id, token, message_id)
    return {"ok": True}


@frappe.whitelist(allow_guest=True)
def mark_messages_read(session_id: str, token: str, message_ids: list) -> dict:
    """Mark messages as read and notify the sender (AC #2, Story 3.4).

    Parameters
    ----------
    session_id  : str   HD Chat Session session_id.
    token       : str   Recipient JWT.
    message_ids : list  List of HD Chat Message message_id values.

    Returns
    -------
    dict with key: ok (bool)
    """
    _check_chat_enabled()
    from helpdesk.helpdesk.realtime.chat_handlers import handle_message_read
    if isinstance(message_ids, str):
        import json as _json
        message_ids = _json.loads(message_ids)
    handle_message_read(session_id, token, message_ids)
    return {"ok": True}


@frappe.whitelist()
def accept_session(session_id: str) -> dict:
    """Agent accepts a waiting chat session.

    Marks the session as active, sets accepted_at, links the session to the
    accepting agent, and publishes a real-time event to the session room.

    Parameters
    ----------
    session_id : str  The HD Chat Session session_id.

    Returns
    -------
    dict with keys: session_id, status, agent
    """
    _check_chat_enabled()

    if not _is_agent():
        frappe.throw(_("Only agents can accept chat sessions."), frappe.PermissionError)

    # Enforce max_concurrent_chats limit
    agent_name = frappe.db.get_value("HD Agent", {"user": frappe.session.user}, "name")
    if not agent_name:
        frappe.throw(_("Current user is not a registered agent."), frappe.PermissionError)

    max_chats = frappe.db.get_single_value("HD Settings", "max_concurrent_chats") or 5
    active_count = frappe.db.count(
        "HD Chat Session",
        {"agent": agent_name, "status": "active"},
    )
    if active_count >= max_chats:
        frappe.throw(
            _("You have reached the maximum of {0} concurrent chats.").format(max_chats),
            frappe.ValidationError,
        )

    session_doc = frappe.get_doc("HD Chat Session", session_id)

    if session_doc.status == "ended":
        frappe.throw(_("Cannot accept an ended session."), frappe.ValidationError)

    session_doc.status = "active"
    session_doc.agent = agent_name
    session_doc.accepted_at = frappe.utils.now_datetime()
    session_doc.save(ignore_permissions=True)

    try:
        frappe.publish_realtime(
            event="session_accepted",
            message={
                "session_id": session_id,
                "agent": agent_name,
                "agent_email": frappe.session.user,
            },
            room=f"chat:{session_id}",
        )
    except Exception:
        pass

    return {"session_id": session_id, "status": "active", "agent": agent_name}


@frappe.whitelist()
def set_availability(availability: str) -> dict:
    """Set the current agent's chat availability status.

    Parameters
    ----------
    availability : str  One of: Online, Away, Offline.

    Returns
    -------
    dict with keys: agent, availability
    """
    _check_chat_enabled()

    if not _is_agent():
        frappe.throw(_("Only agents can set availability."), frappe.PermissionError)

    valid = {"Online", "Away", "Offline"}
    if availability not in valid:
        frappe.throw(
            _("Invalid availability value. Must be one of: Online, Away, Offline."),
            frappe.ValidationError,
        )

    agent_name = frappe.db.get_value("HD Agent", {"user": frappe.session.user}, "name")
    if not agent_name:
        frappe.throw(_("Current user is not a registered agent."), frappe.PermissionError)

    frappe.db.set_value("HD Agent", agent_name, "chat_availability", availability)

    # Notify the agent's personal room so other tabs/devices update
    try:
        frappe.publish_realtime(
            event="availability_changed",
            message={"agent": agent_name, "availability": availability},
            room=f"agent:{frappe.session.user}",
        )
    except Exception:
        pass

    return {"agent": agent_name, "availability": availability}


@frappe.whitelist()
def get_agent_sessions(status: str = "") -> list:
    """Return chat sessions assigned to the current agent.

    Parameters
    ----------
    status : str  Optional filter: "waiting", "active", or "ended".

    Returns
    -------
    list of session dicts ordered by started_at ascending.
    """
    _check_chat_enabled()

    if not _is_agent():
        frappe.throw(_("Only agents can list their sessions."), frappe.PermissionError)

    agent_name = frappe.db.get_value("HD Agent", {"user": frappe.session.user}, "name")
    if not agent_name:
        return []

    _fields = [
        "session_id",
        "customer_email",
        "customer_name",
        "status",
        "started_at",
        "accepted_at",
        "agent",
        "ticket",
    ]

    if status:
        # Filtered view: only return sessions matching the requested status
        filters = {"agent": agent_name, "status": status}
        sessions = frappe.db.get_all(
            "HD Chat Session",
            filters=filters,
            fields=_fields,
            order_by="started_at asc",
        )
    else:
        # Default view: agent's own active sessions + all unassigned waiting sessions (queue)
        assigned_active = frappe.db.get_all(
            "HD Chat Session",
            filters={"agent": agent_name, "status": "active"},
            fields=_fields,
            order_by="started_at asc",
        )
        # Unassigned waiting sessions form the chat queue visible to all agents
        waiting_queue = frappe.db.get_all(
            "HD Chat Session",
            filters={"agent": ["in", ["", None]], "status": "waiting"},
            fields=_fields,
            order_by="started_at asc",
        )
        # Merge, deduplicating by session_id (in case agent has a waiting session assigned)
        seen = {s["session_id"] for s in assigned_active}
        sessions = assigned_active + [s for s in waiting_queue if s["session_id"] not in seen]

    for session in sessions:
        session["unread_count"] = frappe.db.count(
            "HD Chat Message",
            {"session": session["session_id"], "sender_type": "customer", "is_read": 0},
        )
        session["message_count"] = frappe.db.count(
            "HD Chat Message", {"session": session["session_id"]}
        )

    return sessions


@frappe.whitelist()
def get_transfer_targets() -> list:
    """Return agents available to receive a chat transfer.

    Returns agents who are Online and active, excluding the current agent.

    Returns
    -------
    list of dicts: agent_name, user, chat_availability
    """
    _check_chat_enabled()

    if not _is_agent():
        frappe.throw(_("Only agents can list transfer targets."), frappe.PermissionError)

    current_agent_name = frappe.db.get_value(
        "HD Agent", {"user": frappe.session.user}, "name"
    )

    agents = frappe.db.get_all(
        "HD Agent",
        filters={"is_active": 1, "chat_availability": "Online"},
        fields=["name", "user", "agent_name", "chat_availability", "user_image"],
    )

    # Exclude self
    return [a for a in agents if a["name"] != current_agent_name]


def _create_ticket_for_session(session_doc, first_message_content: str):
    """Create an HD Ticket for the session's first customer message.

    Uses the channel normalizer (Story 3.1 / ADR-07) to ensure all
    channel sources produce tickets through the same pathway.

    Runs as Administrator so that guest-initiated chat sessions (send_message
    is allow_guest=True) can create HD Tickets without a permission error.
    """
    original_user = frappe.session.user
    try:
        # Elevate to Administrator: Guest lacks HD Ticket create permission.
        frappe.set_user("Administrator")

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
    finally:
        frappe.set_user(original_user)
