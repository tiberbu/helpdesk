# Copyright (c) 2026, Frappe Technologies Pvt. Ltd. and contributors
# For license information, please see license.txt

"""Migration patch: reload HD Team DocType to add sla_manager field.

Adds the ``sla_manager`` Link field (→ HD Agent) to HD Team so that
teams can designate a manager who receives in-app SLA warning notifications
at the 15-minute threshold.

Existing teams get ``sla_manager = None`` (no notification by default).
"""

import frappe


def execute():
    frappe.reload_doctype("HD Team")
