# Copyright (c) 2026, Frappe Technologies Pvt. Ltd. and contributors
# For license information, please see license.txt

"""Unit tests for helpdesk.helpdesk.automation.actions.ActionExecutor."""

import frappe
from frappe.tests.utils import FrappeTestCase

from helpdesk.helpdesk.automation.actions import ActionExecutor
from helpdesk.test_utils import create_agent, make_ticket


class TestActionExecutor(FrappeTestCase):
    def setUp(self):
        frappe.set_user("Administrator")
        self.executor = ActionExecutor()
        create_agent("action.test.agent@test.com", "Action", "Agent")
        self.ticket = make_ticket(
            subject="Action Executor Test Ticket",
            raised_by="action.customer@test.com",
        )

    def tearDown(self):
        frappe.set_user("Administrator")
        frappe.db.rollback()

    # ------------------------------------------------------------------ #
    # assign_to_team                                                        #
    # ------------------------------------------------------------------ #

    def test_assign_to_team(self):
        # Create a test team if it doesn't exist
        if not frappe.db.exists("HD Team", "Test Auto Team"):
            frappe.get_doc(
                {"doctype": "HD Team", "team_name": "Test Auto Team"}
            ).insert(ignore_permissions=True)

        results = self.executor.execute(
            self.ticket, [{"type": "assign_to_team", "value": "Test Auto Team"}]
        )
        self.assertEqual(len(results), 1)
        self.assertTrue(results[0]["success"], results[0].get("error"))
        val = frappe.db.get_value("HD Ticket", self.ticket.name, "agent_group")
        self.assertEqual(val, "Test Auto Team")

    # ------------------------------------------------------------------ #
    # set_priority                                                          #
    # ------------------------------------------------------------------ #

    def test_set_priority(self):
        results = self.executor.execute(
            self.ticket, [{"type": "set_priority", "value": "High"}]
        )
        self.assertEqual(len(results), 1)
        self.assertTrue(results[0]["success"], results[0].get("error"))
        val = frappe.db.get_value("HD Ticket", self.ticket.name, "priority")
        self.assertEqual(val, "High")

    # ------------------------------------------------------------------ #
    # set_status                                                            #
    # ------------------------------------------------------------------ #

    def test_set_status(self):
        # Get a valid status value
        statuses = frappe.get_all("HD Ticket Status", pluck="name", limit=1)
        if not statuses:
            self.skipTest("No HD Ticket Status records available")
        target_status = statuses[0]

        results = self.executor.execute(
            self.ticket, [{"type": "set_status", "value": target_status}]
        )
        self.assertEqual(len(results), 1)
        self.assertTrue(results[0]["success"], results[0].get("error"))
        val = frappe.db.get_value("HD Ticket", self.ticket.name, "status")
        self.assertEqual(val, target_status)

    # ------------------------------------------------------------------ #
    # add_internal_note                                                     #
    # ------------------------------------------------------------------ #

    def test_add_internal_note(self):
        results = self.executor.execute(
            self.ticket,
            [{"type": "add_internal_note", "value": "Auto-generated internal note"}],
        )
        self.assertEqual(len(results), 1)
        self.assertTrue(results[0]["success"], results[0].get("error"))
        # Verify comment was created
        comment = frappe.db.get_value(
            "HD Ticket Comment",
            {"reference_ticket": self.ticket.name, "is_internal": 1},
            ["content", "is_internal"],
            as_dict=True,
        )
        self.assertIsNotNone(comment)
        self.assertIn("Auto-generated internal note", comment["content"])
        self.assertEqual(comment["is_internal"], 1)

    # ------------------------------------------------------------------ #
    # Unknown action type                                                   #
    # ------------------------------------------------------------------ #

    def test_unknown_action_type_returns_failure(self):
        results = self.executor.execute(
            self.ticket, [{"type": "send_carrier_pigeon", "value": "test"}]
        )
        self.assertEqual(len(results), 1)
        self.assertFalse(results[0]["success"])
        self.assertIn("Unknown action type", results[0]["error"])

    # ------------------------------------------------------------------ #
    # Multiple actions                                                      #
    # ------------------------------------------------------------------ #

    def test_multiple_actions_execute_in_order(self):
        results = self.executor.execute(
            self.ticket,
            [
                {"type": "set_priority", "value": "Urgent"},
                {"type": "add_internal_note", "value": "Priority escalated"},
            ],
        )
        self.assertEqual(len(results), 2)
        self.assertTrue(results[0]["success"])
        self.assertTrue(results[1]["success"])
        priority = frappe.db.get_value("HD Ticket", self.ticket.name, "priority")
        self.assertEqual(priority, "Urgent")

    # ------------------------------------------------------------------ #
    # JSON string input                                                     #
    # ------------------------------------------------------------------ #

    def test_json_string_actions_input(self):
        import json

        actions = json.dumps([{"type": "set_priority", "value": "Low"}])
        results = self.executor.execute(self.ticket, actions)
        self.assertTrue(results[0]["success"])
