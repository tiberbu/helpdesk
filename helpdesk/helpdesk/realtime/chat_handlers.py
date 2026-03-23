"""Real-time chat event handlers (Story 3.4).

These functions are called by whitelisted REST API endpoints in
``helpdesk.api.chat`` and are kept here to separate business logic from the
HTTP layer.  Each handler:

  1. Validates the customer JWT (prevents cross-session eavesdropping).
  2. Performs the requested operation (DB write or pure broadcast).
  3. Publishes a Socket.IO event to room ``chat:{session_id}`` via
     ``frappe.publish_realtime`` so the other party receives it instantly.

AR-07: Socket.IO room naming convention — ``chat:{session_id}``.
NFR-SE-02: JWT validation on every handler.
NFR-SE-06: All content sanitized before DB storage (done in send_message;
           typing handlers never touch content).
"""

import frappe
from helpdesk.helpdesk.chat.jwt_helper import validate_chat_token


# ---------------------------------------------------------------------------
# Typing indicators
# ---------------------------------------------------------------------------

def handle_typing_start(session_id: str, token: str, sender_name: str = "") -> None:
    """Broadcast a 'typing_start' event to room ``chat:{session_id}``.

    Does NOT persist to DB — typing events are ephemeral (AC #3, AR-07).

    Parameters
    ----------
    session_id  : HD Chat Session session_id
    token       : Customer JWT (NFR-SE-02)
    sender_name : Display name shown in the typing indicator
    """
    validate_chat_token(token, session_id)

    frappe.publish_realtime(
        event="typing_start",
        message={
            "session_id": session_id,
            "sender_name": sender_name or "Customer",
        },
        room=f"chat:{session_id}",
    )


def handle_typing_stop(session_id: str, token: str) -> None:
    """Broadcast a 'typing_stop' event to clear the remote typing indicator.

    Does NOT persist to DB (AC #3, AR-07).

    Parameters
    ----------
    session_id : HD Chat Session session_id
    token      : Customer JWT (NFR-SE-02)
    """
    validate_chat_token(token, session_id)

    frappe.publish_realtime(
        event="typing_stop",
        message={"session_id": session_id},
        room=f"chat:{session_id}",
    )


# ---------------------------------------------------------------------------
# Message delivery/read receipts
# ---------------------------------------------------------------------------

def handle_message_delivered(session_id: str, token: str, message_id: str) -> None:
    """Broadcast a 'message_status' event with status='delivered'.

    Called by the recipient's client immediately upon receiving a
    ``chat_message`` event (AC #2).  No DB write — delivered status is not
    persisted (only ``is_read`` is stored for the read receipt).

    Parameters
    ----------
    session_id : HD Chat Session session_id
    token      : JWT of the party confirming delivery
    message_id : HD Chat Message message_id
    """
    validate_chat_token(token, session_id)

    frappe.publish_realtime(
        event="message_status",
        message={
            "session_id": session_id,
            "message_id": message_id,
            "status": "delivered",
        },
        room=f"chat:{session_id}",
    )


def handle_message_read(session_id: str, token: str, message_ids: list) -> None:
    """Persist is_read=1 for each message and broadcast 'message_status' events.

    Called when the recipient opens the chat panel or scrolls to new messages
    (AC #2, FR-LC-02).

    Parameters
    ----------
    session_id  : HD Chat Session session_id
    token       : JWT of the party marking messages as read
    message_ids : List of HD Chat Message message_id values to mark read
    """
    validate_chat_token(token, session_id)

    if not message_ids:
        return

    for mid in message_ids:
        # Only mark messages belonging to this session (prevent cross-session injection)
        if frappe.db.exists("HD Chat Message", {"message_id": mid, "session": session_id}):
            frappe.db.set_value("HD Chat Message", {"message_id": mid}, "is_read", 1)
            frappe.publish_realtime(
                event="message_status",
                message={
                    "session_id": session_id,
                    "message_id": mid,
                    "status": "read",
                },
                room=f"chat:{session_id}",
            )

    frappe.db.commit()
