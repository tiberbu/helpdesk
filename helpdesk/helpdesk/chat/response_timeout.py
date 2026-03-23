"""Agent response timeout background job (Story 3.4, AC #5).

Detects chat sessions where no agent has responded within the configured
timeout window and sends an automated system message to the customer.

Registered in hooks.py as a cron job running every minute on the ``short``
Redis queue so the customer receives the auto-message promptly.

Configuration:
    HD Settings.chat_response_timeout_seconds  (int, default 120)
"""

import frappe
from frappe.utils import add_to_date, now_datetime


_DEFAULT_TIMEOUT_SECONDS = 120
_AUTO_MESSAGE = (
    "We're experiencing high volume. "
    "You can wait or leave a message and we'll email you."
)


def check_unanswered_sessions() -> int:
    """Send auto-message to waiting sessions with no agent response.

    Returns
    -------
    int
        Number of sessions that received the auto-message.
    """
    timeout_seconds = (
        frappe.db.get_single_value("HD Settings", "chat_response_timeout_seconds")
        or _DEFAULT_TIMEOUT_SECONDS
    )

    cutoff = add_to_date(now_datetime(), seconds=-int(timeout_seconds))

    # Waiting sessions started before the cutoff that haven't been notified yet
    sessions = frappe.db.get_all(
        "HD Chat Session",
        filters={
            "status": "waiting",
            "started_at": ["<", cutoff],
            "timeout_notified_at": ["is", "not set"],
        },
        fields=["name", "session_id", "customer_name"],
    )

    notified = 0
    for session in sessions:
        # Guard: skip if an agent message already exists (agent responded race)
        agent_msg_count = frappe.db.count(
            "HD Chat Message",
            {"session": session.session_id or session.name, "sender_type": "agent"},
        )
        if agent_msg_count > 0:
            continue

        session_key = session.session_id or session.name

        # Insert system message
        msg = frappe.get_doc(
            {
                "doctype": "HD Chat Message",
                "session": session_key,
                "sender_type": "system",
                "content": _AUTO_MESSAGE,
                "sent_at": now_datetime(),
            }
        )
        msg.insert(ignore_permissions=True)

        # Broadcast to the session room (AR-07)
        try:
            frappe.publish_realtime(
                event="chat_message",
                message={
                    "session_id": session_key,
                    "message_id": msg.message_id,
                    "content": _AUTO_MESSAGE,
                    "sender_type": "system",
                    "sent_at": str(msg.sent_at),
                    "status": "sent",
                },
                room=f"chat:{session_key}",
            )
        except Exception:
            pass  # Broadcast failure must not block the DB write

        # Mark as notified so we don't send duplicate messages
        frappe.db.set_value(
            "HD Chat Session",
            session.name,
            "timeout_notified_at",
            now_datetime(),
        )
        notified += 1

    if notified:
        frappe.db.commit()
        frappe.logger().info(f"[Chat Timeout] Sent auto-message to {notified} session(s)")

    return notified
