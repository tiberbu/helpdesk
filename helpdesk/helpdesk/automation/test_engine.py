# Copyright (c) 2026, Frappe Technologies Pvt. Ltd. and contributors
# For license information, please see license.txt

"""Integration tests for helpdesk.helpdesk.automation.engine.

Tests:
    AC#2  - Rule conditions evaluated and actions executed on ticket_created
    AC#3  - Multiple matching rules execute in priority_order (ASC)
    AC#4  - Loop detection blocks 6th+ execution within 60s
    AC#12 - automation_enabled flag gates execution
"""

import json

import frappe
from frappe.tests.utils import FrappeTestCase

from helpdesk.helpdesk.automation.engine import evaluate, _is_automation_enabled
from helpdesk.helpdesk.automation.safety import SafetyGuard
from helpdesk.test_utils import create_agent, make_ticket


def _make_rule(rule_name, trigger_type, conditions, actions, priority_order=10, enabled=1):
    """Helper to create a test HD Automation Rule."""
    return frappe.get_doc(
        {
            "doctype": "HD Automation Rule",
            "rule_name": rule_name,
            "trigger_type": trigger_type,
            "enabled": enabled,
            "conditions": json.dumps(conditions),
            "actions": json.dumps(actions),
            "priority_order": priority_order,
            "failure_count": 0,
        }
    ).insert(ignore_permissions=True)


class TestAutomationEngine(FrappeTestCase):
    """Integration tests for the AutomationEngine.evaluate() pipeline."""

    def setUp(self):
        frappe.set_user("Administrator")
        # Ensure automation is enabled for tests
        frappe.db.set_single_value("HD Settings", "automation_enabled", 1)
        self._created_rules = []
        self._guard = SafetyGuard()
        create_agent("engine.test.agent@test.com", "Engine", "Agent")

    def tearDown(self):
        frappe.set_user("Administrator")
        # Clean up rules explicitly (they use db.commit in record_failure/success)
        for rule_name in self._created_rules:
            # Delete linked log records first to avoid LinkExistsError
            frappe.db.delete("HD Automation Log", {"rule_name": rule_name})
            if frappe.db.exists("HD Automation Rule", rule_name):
                frappe.delete_doc("HD Automation Rule", rule_name, ignore_permissions=True)
        frappe.db.commit()  # nosemgrep
        frappe.db.set_single_value("HD Settings", "automation_enabled", 0)
        frappe.db.rollback()

    def _rule(self, *args, **kwargs):
        """Create a rule and track it for tearDown cleanup."""
        rule = _make_rule(*args, **kwargs)
        self._created_rules.append(rule.name)
        return rule

    # ------------------------------------------------------------------ #
    # AC#2: Conditions evaluated and actions executed                      #
    # ------------------------------------------------------------------ #

    def test_matching_rule_executes_action(self):
        """Given a rule with conditions matching the ticket, action fires."""
        self._rule(
            rule_name=f"eng-test-match-{frappe.generate_hash(length=6)}",
            trigger_type="ticket_created",
            conditions=[{"field": "priority", "operator": "equals", "value": "Urgent"}],
            actions=[{"type": "set_priority", "value": "High"}],
            priority_order=1,
        )

        ticket = make_ticket(
            subject="Engine Test — Matching Rule",
            raised_by="eng.customer@test.com",
            priority="Urgent",
        )
        self._guard.reset_loop_counter(str(ticket.name))

        evaluate(ticket, "ticket_created")

        # Action should have changed priority from Urgent → High
        priority = frappe.db.get_value("HD Ticket", ticket.name, "priority")
        self.assertEqual(priority, "High")

    def test_non_matching_rule_does_not_execute_action(self):
        """Given a rule whose conditions do NOT match, action must NOT fire."""
        self._rule(
            rule_name=f"eng-test-nomatch-{frappe.generate_hash(length=6)}",
            trigger_type="ticket_created",
            conditions=[{"field": "priority", "operator": "equals", "value": "Urgent"}],
            actions=[{"type": "set_priority", "value": "High"}],
            priority_order=2,
        )

        ticket = make_ticket(
            subject="Engine Test — Non-Matching Rule",
            raised_by="eng.customer2@test.com",
            priority="Low",
        )
        self._guard.reset_loop_counter(str(ticket.name))

        evaluate(ticket, "ticket_created")

        # Priority must remain Low (action did not fire)
        priority = frappe.db.get_value("HD Ticket", ticket.name, "priority")
        self.assertEqual(priority, "Low")

    # ------------------------------------------------------------------ #
    # AC#3: Priority ordering                                               #
    # ------------------------------------------------------------------ #

    def test_rules_execute_in_priority_order(self):
        """Lower priority_order number fires first.

        Rule A (priority 1): conditions match → set_priority = High
        Rule B (priority 2): conditions match → set_priority = Low

        After both fire, final priority must be Low (Rule B fired last).
        """
        suffix = frappe.generate_hash(length=6)
        cond = [{"field": "subject", "operator": "contains", "value": "PriorityOrder"}]

        self._rule(
            rule_name=f"eng-prio-a-{suffix}",
            trigger_type="ticket_updated",
            conditions=cond,
            actions=[{"type": "set_priority", "value": "High"}],
            priority_order=1,
        )
        self._rule(
            rule_name=f"eng-prio-b-{suffix}",
            trigger_type="ticket_updated",
            conditions=cond,
            actions=[{"type": "set_priority", "value": "Low"}],
            priority_order=2,
        )

        ticket = make_ticket(
            subject="PriorityOrder Test Ticket",
            raised_by="eng.prio.customer@test.com",
        )
        self._guard.reset_loop_counter(str(ticket.name))

        evaluate(ticket, "ticket_updated")

        priority = frappe.db.get_value("HD Ticket", ticket.name, "priority")
        self.assertEqual(priority, "Low", "Rule B (priority_order=2) should fire last → Low")

    # ------------------------------------------------------------------ #
    # AC#4: Loop detection                                                  #
    # ------------------------------------------------------------------ #

    def test_loop_detection_blocks_execution(self):
        """After 5 allowed executions, the 6th must be blocked (no action fired).

        We create a rule that changes priority on every call. After 5 calls it
        should have changed; on the 6th call the guard blocks and no further
        action occurs.
        """
        from helpdesk.helpdesk.automation.safety import MAX_EXECUTIONS_PER_WINDOW

        suffix = frappe.generate_hash(length=6)
        self._rule(
            rule_name=f"eng-loop-{suffix}",
            trigger_type="ticket_updated",
            conditions=[],  # always match
            actions=[{"type": "set_priority", "value": "High"}],
            priority_order=1,
        )

        ticket = make_ticket(
            subject=f"Loop Detection Test {suffix}",
            raised_by="eng.loop.customer@test.com",
        )
        ticket_name = str(ticket.name)
        self._guard.reset_loop_counter(ticket_name)

        # Run exactly MAX_EXECUTIONS_PER_WINDOW times (all should be allowed)
        for _ in range(MAX_EXECUTIONS_PER_WINDOW):
            evaluate(ticket, "ticket_updated")

        # Now reset priority back to something else to detect a 6th execution
        frappe.db.set_value("HD Ticket", ticket.name, "priority", "Low")

        # 6th execution — loop guard must block it
        evaluate(ticket, "ticket_updated")

        # Priority must remain Low (action did not fire on 6th call)
        priority_after_block = frappe.db.get_value("HD Ticket", ticket.name, "priority")
        self.assertEqual(priority_after_block, "Low", "Loop guard must have blocked the 6th call")

    # ------------------------------------------------------------------ #
    # AC#12: Feature flag                                                   #
    # ------------------------------------------------------------------ #

    def test_automation_disabled_skips_all_rules(self):
        """When automation_enabled=0, no rules execute."""
        frappe.db.set_single_value("HD Settings", "automation_enabled", 0)

        self._rule(
            rule_name=f"eng-flag-{frappe.generate_hash(length=6)}",
            trigger_type="ticket_created",
            conditions=[],
            actions=[{"type": "set_priority", "value": "Urgent"}],
            priority_order=1,
        )

        ticket = make_ticket(
            subject="Feature Flag Test Ticket",
            raised_by="eng.flag.customer@test.com",
            priority="Low",
        )
        self._guard.reset_loop_counter(str(ticket.name))

        evaluate(ticket, "ticket_created")

        # Priority must remain Low — engine returned early
        priority = frappe.db.get_value("HD Ticket", ticket.name, "priority")
        self.assertEqual(priority, "Low")

    def test_automation_enabled_flag_reads_settings(self):
        """_is_automation_enabled reflects the HD Settings value."""
        frappe.db.set_single_value("HD Settings", "automation_enabled", 1)
        self.assertTrue(_is_automation_enabled())
        frappe.db.set_single_value("HD Settings", "automation_enabled", 0)
        self.assertFalse(_is_automation_enabled())

    # ------------------------------------------------------------------ #
    # Disabled rule is skipped                                             #
    # ------------------------------------------------------------------ #

    def test_disabled_rule_is_skipped(self):
        """Rules with enabled=0 must not be fetched or executed."""
        self._rule(
            rule_name=f"eng-disabled-{frappe.generate_hash(length=6)}",
            trigger_type="ticket_created",
            conditions=[],
            actions=[{"type": "set_priority", "value": "Urgent"}],
            priority_order=1,
            enabled=0,
        )

        ticket = make_ticket(
            subject="Disabled Rule Test Ticket",
            raised_by="eng.disabled.customer@test.com",
            priority="Low",
        )
        self._guard.reset_loop_counter(str(ticket.name))

        evaluate(ticket, "ticket_created")

        priority = frappe.db.get_value("HD Ticket", ticket.name, "priority")
        self.assertEqual(priority, "Low", "Disabled rule must not execute")
