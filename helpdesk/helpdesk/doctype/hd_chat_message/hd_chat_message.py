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
