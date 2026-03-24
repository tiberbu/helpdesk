# -*- coding: utf-8 -*-
# Copyright (c) 2015, Frappe Technologies Pvt. Ltd. and contributors
# For license information, please see license.txt

from __future__ import unicode_literals

import json

import frappe
from frappe import _
from frappe.model.document import Document
from frappe.model.naming import append_number_if_name_exists
from frappe.realtime import get_website_room
from frappe.utils.jinja import validate_template

from helpdesk.helpdesk.doctype.hd_ticket.hd_ticket import (
    remove_guest_ticket_creation_permission,
    set_guest_ticket_creation_permission,
)


class HDSettings(Document):
    def validate(self):
        self.validate_auto_close_days()
        self.validate_email_contents()
        self.validate_send_feedback_when_ticket_closed()
        self.validate_priority_matrix()

    def validate_priority_matrix(self):
        """Validate the ITIL priority matrix when ITIL Mode is enabled.

        AC #5: All 9 Impact x Urgency combinations must be mapped.
        AC #4: Future calculations use the updated matrix.
        """
        if not self.itil_mode_enabled:
            return

        if not self.priority_matrix:
            return

        if isinstance(self.priority_matrix, str):
            try:
                matrix = json.loads(self.priority_matrix)
            except (json.JSONDecodeError, ValueError):
                frappe.throw(
                    _("Priority Matrix must be valid JSON"),
                    frappe.ValidationError,
                )
        else:
            matrix = self.priority_matrix

        required_keys = [
            "High-High",
            "High-Medium",
            "High-Low",
            "Medium-High",
            "Medium-Medium",
            "Medium-Low",
            "Low-High",
            "Low-Medium",
            "Low-Low",
        ]
        valid_priorities = {"Urgent", "High", "Medium", "Low"}

        missing_keys = [k for k in required_keys if k not in matrix]
        if missing_keys:
            frappe.throw(
                _("Priority Matrix is missing required combinations: {0}").format(
                    ", ".join(missing_keys)
                ),
                frappe.ValidationError,
            )

        invalid_values = [
            f"{k}: {v}"
            for k, v in matrix.items()
            if v not in valid_priorities
        ]
        if invalid_values:
            frappe.throw(
                _(
                    "Priority Matrix has invalid priority values (must be Urgent, High, Medium, or Low): {0}"
                ).format(", ".join(invalid_values)),
                frappe.ValidationError,
            )

    def validate_auto_close_days(self):
        if self.auto_close_tickets and self.auto_close_after_days <= 0:
            frappe.throw(
                _("Day count for auto closing tickets cannot be negative or zero")
            )

    def validate_send_feedback_when_ticket_closed(self):
        if not self.enable_email_ticket_feedback:
            return
        status_category = frappe.db.get_value(
            "HD Ticket Status", self.send_email_feedback_on_status, "category"
        )
        if status_category != "Resolved":
            frappe.throw(
                _(
                    "The status for sending feedback must be of <u>Resolved</u> category."
                )
            )

    def get_base_support_rotation(self):
        """Returns the base support rotation rule if it exists, else creats once and returns it"""

        if not self.base_support_rotation:
            self.create_base_support_rotation()

        return self.base_support_rotation

    def create_base_support_rotation(self):
        """Creates the base support rotation rule, and set it to frappe desk settings"""

        rule_doc = frappe.new_doc("Assignment Rule")
        rule_doc.name = append_number_if_name_exists(
            "Assignment Rule", "Support Rotation"
        )
        rule_doc.document_type = "HD Ticket"
        rule_doc.assign_condition = "status == 'Open'"
        rule_doc.assign_condition_json = '[["status", "==", "Open"]]'
        rule_doc.priority = 0
        rule_doc.disabled = True  # Disable the rule by default, when agents are added to the group, the rule will be enabled

        for day in [
            "Monday",
            "Tuesday",
            "Wednesday",
            "Thursday",
            "Friday",
            "Saturday",
            "Sunday",
        ]:
            day_doc = frappe.get_doc({"doctype": "Assignment Rule Day", "day": day})
            rule_doc.append("assignment_days", day_doc)

        rule_doc.save(ignore_permissions=True)
        self.base_support_rotation = rule_doc.name
        self.save(ignore_permissions=True)

        return

    def before_save(self):
        self.update_ticket_permissions()

    def on_update(self):
        event = "helpdesk:settings-updated"
        room = get_website_room()

        frappe.publish_realtime(event, room=room, after_commit=True)

    def update_ticket_permissions(self):
        if self.allow_anyone_to_create_tickets:
            set_guest_ticket_creation_permission()
        if not self.allow_anyone_to_create_tickets:
            remove_guest_ticket_creation_permission()

    def validate_email_contents(self):
        for content_field_name in [
            "feedback_email_content",
            "acknowledgement_email_content",
            "reply_email_to_agent_content",
            "reply_via_agent_email_content",
        ]:
            if not self.has_value_changed(content_field_name):
                continue
            validate_template(getattr(self, content_field_name))

    def get_kb_review_period_days(self) -> int:
        """Return the configured review period in days (default 90)."""
        return int(self.kb_review_period_days or 90)

    def get_kb_reviewer_emails(self) -> list[str]:
        """Return list of reviewer email addresses configured in HD Settings.

        Called by HDArticle notification helpers when an article is submitted for review.
        """
        emails = []
        for row in self.get("kb_reviewers") or []:
            if row.user:
                email = frappe.db.get_value("User", row.user, "email") or row.user
                emails.append(email)
        return emails

    @property
    def hd_search(self):
        from helpdesk.api.article import search

        return search
