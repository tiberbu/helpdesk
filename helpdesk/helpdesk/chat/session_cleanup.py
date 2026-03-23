"""Chat session cleanup background job.

Ends chat sessions that have been inactive beyond their configured timeout.
Scheduled to run every 5 minutes via hooks.py scheduler_events (ADR-12 / short queue).

A session is considered inactive if:
    started_at < now() - inactivity_timeout_minutes

For ended sessions: status is set to "ended" and a system message is appended.
"""

import frappe


def cleanup_inactive_sessions() -> int:
    """End all chat sessions that have exceeded their inactivity timeout.

    Returns
    -------
    int
        Number of sessions ended in this run.
    """
    active_sessions = frappe.db.get_all(
        "HD Chat Session",
        filters={"status": ["in", ["waiting", "active"]]},
        fields=["name", "session_id", "started_at", "inactivity_timeout_minutes"],
    )

    ended_count = 0
    now = frappe.utils.now_datetime()

    for session in active_sessions:
        timeout_minutes = session.get("inactivity_timeout_minutes") or 30
        cutoff = frappe.utils.add_to_date(now, minutes=-timeout_minutes)

        started_at = session.get("started_at")
        if not started_at:
            continue

        # Normalize to naive datetime for comparison
        if hasattr(started_at, "tzinfo") and started_at.tzinfo is not None:
            from datetime import timezone
            started_at = started_at.astimezone(timezone.utc).replace(tzinfo=None)

        if started_at < cutoff:
            _end_session_internal(session["session_id"], session["name"])
            ended_count += 1

    if ended_count:
        frappe.logger().info(
            "[ChatCleanup] Ended %d inactive chat session(s)", ended_count
        )

    return ended_count


def _end_session_internal(session_id: str, session_name: str) -> None:
    """End a session by updating status and appending a system message."""
    frappe.db.set_value(
        "HD Chat Session",
        session_name,
        {
            "status": "ended",
            "ended_at": frappe.utils.now_datetime(),
        },
    )

    # Append a system message to the session log
    try:
        msg = frappe.get_doc(
            {
                "doctype": "HD Chat Message",
                "session": session_name,
                "sender_type": "system",
                "content": "This chat has ended due to inactivity.",
                "sent_at": frappe.utils.now_datetime(),
            }
        )
        msg.insert(ignore_permissions=True)
    except Exception:
        frappe.log_error(frappe.get_traceback(), "ChatCleanup: system message insert failed")

    # Publish real-time event to notify connected clients
    try:
        frappe.publish_realtime(
            event="session_ended",
            message={"session_id": session_id, "reason": "inactivity"},
            room=f"chat:{session_id}",
        )
    except Exception:
        pass  # Real-time failure must not block cleanup
