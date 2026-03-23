"""Chat session cleanup background job.

Ends chat sessions that have been inactive beyond their configured timeout.
Scheduled to run every 5 minutes via hooks.py scheduler_events (ADR-12 / short queue).

A session is considered inactive if:
    last_activity_at < now() - inactivity_timeout_minutes

where ``last_activity_at`` is the MAX(sent_at) of all HD Chat Messages in the
session, falling back to ``started_at`` when no messages have been sent yet.

For ended sessions: status is set to "ended" and a system message is appended.
"""

import frappe


def _get_last_activity(session_name: str, started_at):
    """Return the timestamp of the most recent activity for a session.

    Queries MAX(sent_at) from HD Chat Message. Falls back to ``started_at``
    when the session has no messages yet.

    Parameters
    ----------
    session_name : str
        The ``name`` (== session_id) of the HD Chat Session document.
    started_at :
        The session's ``started_at`` datetime (fallback value).

    Returns
    -------
    datetime
        The latest activity datetime (naive UTC).
    """
    from datetime import timezone

    result = frappe.db.sql(
        """
        SELECT MAX(sent_at) AS last_sent
        FROM `tabHD Chat Message`
        WHERE session = %s
        """,
        session_name,
        as_dict=True,
    )
    last_sent = result[0].get("last_sent") if result else None

    activity = last_sent if last_sent is not None else started_at

    # Normalize to naive datetime for comparison
    if activity and hasattr(activity, "tzinfo") and activity.tzinfo is not None:
        activity = activity.astimezone(timezone.utc).replace(tzinfo=None)

    return activity


def cleanup_inactive_sessions() -> int:
    """End all chat sessions that have exceeded their inactivity timeout.

    Returns
    -------
    int
        Number of sessions ended in this run.
    """
    from datetime import timezone

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

        # Normalize cutoff to naive datetime for comparison
        if hasattr(cutoff, "tzinfo") and cutoff.tzinfo is not None:
            cutoff = cutoff.astimezone(timezone.utc).replace(tzinfo=None)

        # Use last message time as the activity reference; fall back to started_at
        last_activity = _get_last_activity(session["session_id"], started_at)
        if last_activity is None:
            continue

        if last_activity < cutoff:
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
