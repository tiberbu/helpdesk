# Copyright (c) 2023, Frappe Technologies and contributors
# For license information, please see license.txt

import frappe
from frappe import _
from frappe.model.document import Document

from helpdesk.utils import capture_event, publish_event


class HDEscalationRule(Document):
    def validate(self):
        self._validate_actions()
        self._validate_trigger_opts()

    def after_insert(self):
        capture_event("escalation_rule_created")
        publish_event("helpdesk:new-escalation-rule", self)

    def on_update(self):
        capture_event("escalation_rule_updated")
        publish_event("helpdesk:update-escalation-rule", self)

    def after_delete(self):
        capture_event("escalation_rule_deleted")
        publish_event("helpdesk:delete-escalation-rule", self)

    def _validate_actions(self):
        if not self.actions_table:
            frappe.throw(_("At least one action is required."))
        for row in self.actions_table:
            if row.action_type == "notify_agent" and not row.notify_agent:
                frappe.throw(_("Row {0}: Agent to Notify is required for 'notify_agent' action.").format(row.idx))
            if row.action_type == "reassign_agent" and not row.assign_to_agent:
                frappe.throw(_("Row {0}: Assign to Agent is required for 'reassign_agent' action.").format(row.idx))
            if row.action_type == "reassign_team" and not row.assign_to_team:
                frappe.throw(_("Row {0}: Assign to Team is required for 'reassign_team' action.").format(row.idx))
            if row.action_type == "change_priority" and not row.set_priority:
                frappe.throw(_("Row {0}: Set Priority is required for 'change_priority' action.").format(row.idx))

    def _validate_trigger_opts(self):
        if self.trigger == "ticket_age" and not self.age_hours:
            frappe.throw(_("Age (hours) is required when trigger is 'ticket_age'."))
        if self.trigger == "status_change" and not self.target_status:
            frappe.throw(_("Target Status is required when trigger is 'status_change'."))
