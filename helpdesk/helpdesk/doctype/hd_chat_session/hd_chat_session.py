# Copyright (c) 2026, Frappe Technologies Pvt. Ltd. and contributors
# For license information, please see license.txt

"""HD Chat Session DocType controller.

Represents a single live-chat conversation between a customer and an agent.
Sessions are created on pre-chat form submission and managed by the chat API.
"""

import frappe
from frappe.model.document import Document


class HDChatSession(Document):
    def before_insert(self):
        """Auto-set started_at and ensure session_id on creation."""
        if not self.started_at:
            self.started_at = frappe.utils.now_datetime()
        if not self.session_id:
            self.session_id = frappe.generate_hash(length=20)
        if not self.inactivity_timeout_minutes:
            self.inactivity_timeout_minutes = 30
