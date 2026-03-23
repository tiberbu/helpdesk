# Copyright (c) 2026, Frappe Technologies Pvt. Ltd. and contributors
# For license information, please see license.txt

"""HD Chat Message DocType controller.

Individual messages within a chat session. Stored as standalone documents
(not child table) for efficient per-session queries without loading the full
session document.
"""

import frappe
from frappe.model.document import Document


class HDChatMessage(Document):
    def before_insert(self):
        """Auto-set message_id and sent_at on creation."""
        if not self.message_id:
            self.message_id = frappe.generate_hash(length=20)
        if not self.sent_at:
            self.sent_at = frappe.utils.now_datetime()

    def after_insert(self):
        """Store chat message as HD Ticket communication via channel normalizer.

        Uses the ChatAdapter (Story 3.1 / ADR-07) to normalize the message
        into a ChannelMessage, then persists a Communication doc on the linked
        HD Ticket. Errors are swallowed so real-time chat is never interrupted
        by communication-storage failures (NFR-A-01, Story 3.6 AC #1, #6).
        """
        if not frappe.db.get_single_value("HD Settings", "chat_enabled"):
            return
        try:
            from helpdesk.helpdesk.channels.chat_adapter import ChatAdapter
            from helpdesk.helpdesk.channels.normalizer import create_ticket_communication

            adapter = ChatAdapter()
            channel_message = adapter.normalize_from_doc(self)
            create_ticket_communication(channel_message)
        except Exception:
            frappe.log_error(
                frappe.get_traceback(),
                "HDChatMessage: failed to store communication for message {0}".format(
                    self.name
                ),
            )
