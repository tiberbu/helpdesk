# Copyright (c) 2026, Frappe Technologies Pvt. Ltd. and contributors
# For license information, please see license.txt

"""Integration tests for SLA monitor → automation engine pipeline (Story 2.3).

Tests:
    AC#1  - sla_warning trigger fires for matching automation rules at thresholds
    AC#2  - sla_breached trigger fires for matching automation rules on breach
    AC#4  - sla_warning action executes: rule with assign_to_team fires correctly
    AC#5  - In-app notification sent to assigned agent on sla_warning
    AC#6  - Threshold deduplication: each threshold fires exactly once
    AC#9  - automation_enabled=0 prevents rule evaluation
"""

import json
from datetime import timedelta
from unittest.mock import patch, call

import frappe
from frappe.tests.utils import FrappeTestCase
from frappe.utils import now_datetime, add_to_date

from helpdesk.helpdesk.automation.safety import SafetyGuard
from helpdesk.helpdesk.doctype.hd_service_level_agreement.sla_monitor import (
    check_sla_breaches,
    clear_warning_dedup,
    _get_warning_thresholds,
    _fire_warning,
    _fire_breached,
)
from helpdesk.test_utils import create_agent, make_ticket


def _make_rule(rule_name, trigger_type, conditions, actions, priority_order=10, enabled=1):
    """Create a test HD Automation Rule."""
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


def _make_team(name: str):
    """Create a minimal HD Team for action testing."""
    if not frappe.db.exists("HD Team", name):
        frappe.get_doc({"doctype": "HD Team", "team_name": name}).insert(ignore_permissions=True)


class TestSLAMonitorAutomation(FrappeTestCase):
    """Integration tests: SLA monitor → automation engine → action execution."""

    def setUp(self):
        frappe.set_user("Administrator")
        frappe.db.set_single_value("HD Settings", "automation_enabled", 1)
        frappe.db.set_single_value("HD Settings", "sla_warning_thresholds", json.dumps([30, 15, 5]))
        self._created_rules = []
        self._created_tickets = []
        self._guard = SafetyGuard()
        create_agent("sla.monitor.agent@test.com", "SLA", "Monitor")

    def tearDown(self):
        frappe.set_user("Administrator")
        # Delete rules explicitly (they use db.commit internally)
        for rule_name in self._created_rules:
            if frappe.db.exists("HD Automation Rule", rule_name):
                frappe.delete_doc("HD Automation Rule", rule_name, ignore_permissions=True)
        frappe.db.commit()  # nosemgrep
        frappe.db.set_single_value("HD Settings", "automation_enabled", 0)
        frappe.db.set_single_value("HD Settings", "sla_warning_thresholds", json.dumps([30, 15, 5]))
        frappe.db.rollback()

    def _rule(self, *args, **kwargs):
        rule = _make_rule(*args, **kwargs)
        self._created_rules.append(rule.name)
        return rule

    def _ticket_near_breach(self, minutes_to_breach: float = 10.0, subject=None):
        """Create a ticket with resolution_by set N minutes from now."""
        subject = subject or f"SLA Test Ticket {frappe.generate_hash(length=6)}"
        ticket = make_ticket(subject=subject, raised_by="sla.customer@test.com")
        resolution_by = now_datetime() + timedelta(minutes=minutes_to_breach)
        frappe.db.set_value("HD Ticket", ticket.name, "resolution_by", resolution_by)
        self._guard.reset_loop_counter(str(ticket.name))
        clear_warning_dedup(str(ticket.name))
        return frappe.get_doc("HD Ticket", ticket.name)

    def _ticket_breached(self, minutes_past_breach: float = 5.0, subject=None):
        """Create a ticket whose resolution_by is already in the past."""
        subject = subject or f"Breached Ticket {frappe.generate_hash(length=6)}"
        ticket = make_ticket(subject=subject, raised_by="sla.customer@test.com")
        resolution_by = now_datetime() - timedelta(minutes=minutes_past_breach)
        frappe.db.set_value("HD Ticket", ticket.name, "resolution_by", resolution_by)
        self._guard.reset_loop_counter(str(ticket.name))
        clear_warning_dedup(str(ticket.name))
        return frappe.get_doc("HD Ticket", ticket.name)

    # ------------------------------------------------------------------ #
    # AC#1 — sla_warning trigger fires matching rules                      #
    # ------------------------------------------------------------------ #

    def test_sla_warning_rule_fires_on_threshold(self):
        """Given a rule with trigger sla_warning, when threshold is crossed, action executes."""
        suffix = frappe.generate_hash(length=6)
        self._rule(
            rule_name=f"sla-warn-fire-{suffix}",
            trigger_type="sla_warning",
            conditions=[],  # always match
            actions=[{"type": "set_priority", "value": "Urgent"}],
            priority_order=1,
        )
        ticket = self._ticket_near_breach(minutes_to_breach=10.0)

        # Directly call _fire_warning (simulates what check_sla_breaches would do)
        _fire_warning(
            ticket_name=str(ticket.name),
            assigned_to="",
            threshold=15,  # 10 min remaining is within 15-min threshold
            minutes_remaining=10.0,
            resolution_by=now_datetime() + timedelta(minutes=10),
        )

        priority = frappe.db.get_value("HD Ticket", ticket.name, "priority")
        self.assertEqual(priority, "Urgent", "sla_warning rule must have set priority to Urgent")

    # ------------------------------------------------------------------ #
    # AC#2 — sla_breached trigger fires matching rules                     #
    # ------------------------------------------------------------------ #

    def test_sla_breached_rule_fires_on_breach(self):
        """Given a rule with trigger sla_breached, when breach detected, action executes."""
        suffix = frappe.generate_hash(length=6)
        self._rule(
            rule_name=f"sla-breached-fire-{suffix}",
            trigger_type="sla_breached",
            conditions=[],  # always match
            actions=[{"type": "set_priority", "value": "Urgent"}],
            priority_order=1,
        )
        ticket = self._ticket_breached(minutes_past_breach=5.0)

        _fire_breached(ticket_name=str(ticket.name), assigned_to="")

        priority = frappe.db.get_value("HD Ticket", ticket.name, "priority")
        self.assertEqual(priority, "Urgent", "sla_breached rule must have set priority to Urgent")

    # ------------------------------------------------------------------ #
    # AC#4 — assign_to_team action executes on sla_warning                 #
    # ------------------------------------------------------------------ #

    def test_sla_warning_assign_to_team_action(self):
        """Given rule: trigger=sla_warning, action=assign_to_team:Escalation → team updated."""
        _make_team("Escalation")
        suffix = frappe.generate_hash(length=6)
        self._rule(
            rule_name=f"sla-warn-team-{suffix}",
            trigger_type="sla_warning",
            conditions=[],
            actions=[{"type": "assign_to_team", "value": "Escalation"}],
            priority_order=1,
        )
        ticket = self._ticket_near_breach(minutes_to_breach=8.0)

        _fire_warning(
            ticket_name=str(ticket.name),
            assigned_to="",
            threshold=15,
            minutes_remaining=8.0,
            resolution_by=now_datetime() + timedelta(minutes=8),
        )

        team = frappe.db.get_value("HD Ticket", ticket.name, "agent_group")
        self.assertEqual(team, "Escalation", "Ticket must be reassigned to Escalation team")

    # ------------------------------------------------------------------ #
    # AC#5 — In-app notification sent to assigned agent                    #
    # ------------------------------------------------------------------ #

    def test_notify_agent_sla_warning_calls_publish_realtime(self):
        """notify_agent_sla_warning publishes to agent:{email} room."""
        from helpdesk.helpdesk.automation.notifications import notify_agent_sla_warning

        ticket = self._ticket_near_breach(minutes_to_breach=12.0)
        agent_email = "sla.monitor.agent@test.com"
        resolution_by = now_datetime() + timedelta(minutes=12)

        with patch("frappe.publish_realtime") as mock_publish:
            notify_agent_sla_warning(
                ticket_name=str(ticket.name),
                assigned_to=agent_email,
                threshold_minutes=15,
                minutes_remaining=12.0,
                resolution_by=resolution_by,
            )

        mock_publish.assert_called_once()
        call_kwargs = mock_publish.call_args
        # event must be "sla_warning"
        self.assertEqual(call_kwargs[1].get("event") or call_kwargs[0][0], "sla_warning")
        # room must be agent:{email}
        room = call_kwargs[1].get("room") or call_kwargs[0][2]
        self.assertEqual(room, f"agent:{agent_email}")

    def test_notify_agent_sla_warning_unassigned_is_noop(self):
        """notify_agent_sla_warning does nothing when ticket is unassigned."""
        from helpdesk.helpdesk.automation.notifications import notify_agent_sla_warning

        with patch("frappe.publish_realtime") as mock_publish:
            notify_agent_sla_warning(
                ticket_name="FAKE-001",
                assigned_to="",
                threshold_minutes=15,
                minutes_remaining=10.0,
                resolution_by=now_datetime(),
            )

        mock_publish.assert_not_called()

    def test_notify_agent_extracts_email_from_json_list(self):
        """_extract_agent_email handles _assign JSON list format."""
        from helpdesk.helpdesk.automation.notifications import _extract_agent_email

        self.assertEqual(_extract_agent_email('["agent@example.com"]'), "agent@example.com")
        self.assertEqual(_extract_agent_email('["a@b.com", "c@d.com"]'), "a@b.com")
        self.assertEqual(_extract_agent_email("agent@example.com"), "agent@example.com")
        self.assertEqual(_extract_agent_email(""), "")
        self.assertEqual(_extract_agent_email("not-an-email"), "")

    # ------------------------------------------------------------------ #
    # AC#6 — Threshold deduplication                                       #
    # ------------------------------------------------------------------ #

    def test_threshold_fires_exactly_once(self):
        """Each warning threshold fires at most once per SLA cycle."""
        suffix = frappe.generate_hash(length=6)
        self._rule(
            rule_name=f"sla-dedup-{suffix}",
            trigger_type="sla_warning",
            conditions=[],
            actions=[{"type": "set_priority", "value": "Urgent"}],
            priority_order=1,
        )
        ticket = self._ticket_near_breach(minutes_to_breach=10.0)
        resolution_by = now_datetime() + timedelta(minutes=10)

        # First fire — should execute the action
        _fire_warning(str(ticket.name), "", 15, 10.0, resolution_by)
        priority_after_first = frappe.db.get_value("HD Ticket", ticket.name, "priority")
        self.assertEqual(priority_after_first, "Urgent")

        # Reset priority to detect second execution
        frappe.db.set_value("HD Ticket", ticket.name, "priority", "Low")

        # Second fire for same threshold — should be deduplicated (no action)
        self._guard.reset_loop_counter(str(ticket.name))
        _fire_warning(str(ticket.name), "", 15, 10.0, resolution_by)
        priority_after_second = frappe.db.get_value("HD Ticket", ticket.name, "priority")
        self.assertEqual(priority_after_second, "Low", "Duplicate threshold fire must be blocked")

    def test_breach_fires_exactly_once(self):
        """sla_breached fires at most once per breach cycle."""
        suffix = frappe.generate_hash(length=6)
        self._rule(
            rule_name=f"sla-breach-dedup-{suffix}",
            trigger_type="sla_breached",
            conditions=[],
            actions=[{"type": "set_priority", "value": "Urgent"}],
            priority_order=1,
        )
        ticket = self._ticket_breached(minutes_past_breach=5.0)

        # First fire
        _fire_breached(str(ticket.name), "")
        priority_after_first = frappe.db.get_value("HD Ticket", ticket.name, "priority")
        self.assertEqual(priority_after_first, "Urgent")

        # Reset priority
        frappe.db.set_value("HD Ticket", ticket.name, "priority", "Low")
        self._guard.reset_loop_counter(str(ticket.name))

        # Second fire — deduplication blocks it
        _fire_breached(str(ticket.name), "")
        priority_after_second = frappe.db.get_value("HD Ticket", ticket.name, "priority")
        self.assertEqual(priority_after_second, "Low", "Duplicate breach fire must be blocked")

    def test_clear_warning_dedup_allows_refiring(self):
        """clear_warning_dedup resets dedup keys so thresholds fire again."""
        suffix = frappe.generate_hash(length=6)
        self._rule(
            rule_name=f"sla-clear-dedup-{suffix}",
            trigger_type="sla_warning",
            conditions=[],
            actions=[{"type": "set_priority", "value": "Urgent"}],
            priority_order=1,
        )
        ticket = self._ticket_near_breach(minutes_to_breach=10.0)
        resolution_by = now_datetime() + timedelta(minutes=10)

        # Fire once — executes action
        _fire_warning(str(ticket.name), "", 15, 10.0, resolution_by)
        self.assertEqual(
            frappe.db.get_value("HD Ticket", ticket.name, "priority"), "Urgent"
        )

        # Reset dedup keys
        frappe.db.set_value("HD Ticket", ticket.name, "priority", "Low")
        clear_warning_dedup(str(ticket.name))
        self._guard.reset_loop_counter(str(ticket.name))

        # Fire again — should execute because dedup was cleared
        _fire_warning(str(ticket.name), "", 15, 10.0, resolution_by)
        self.assertEqual(
            frappe.db.get_value("HD Ticket", ticket.name, "priority"),
            "Urgent",
            "After clear_warning_dedup, threshold must fire again",
        )

    # ------------------------------------------------------------------ #
    # AC#9 — automation_enabled=0 suppresses rule evaluation               #
    # ------------------------------------------------------------------ #

    def test_automation_disabled_prevents_sla_trigger(self):
        """When automation_enabled=0, sla_warning rule must NOT execute."""
        frappe.db.set_single_value("HD Settings", "automation_enabled", 0)

        suffix = frappe.generate_hash(length=6)
        self._rule(
            rule_name=f"sla-disabled-{suffix}",
            trigger_type="sla_warning",
            conditions=[],
            actions=[{"type": "set_priority", "value": "Urgent"}],
            priority_order=1,
        )
        ticket = self._ticket_near_breach(minutes_to_breach=10.0)

        _fire_warning(
            str(ticket.name), "", 15, 10.0,
            now_datetime() + timedelta(minutes=10),
        )

        priority = frappe.db.get_value("HD Ticket", ticket.name, "priority")
        self.assertNotEqual(priority, "Urgent", "Rule must not fire when automation_enabled=0")

    # ------------------------------------------------------------------ #
    # Threshold configuration                                              #
    # ------------------------------------------------------------------ #

    def test_get_warning_thresholds_default(self):
        """_get_warning_thresholds returns default [30,15,5] sorted descending."""
        frappe.db.set_single_value("HD Settings", "sla_warning_thresholds", None)
        thresholds = _get_warning_thresholds()
        self.assertEqual(thresholds, [30, 15, 5])

    def test_get_warning_thresholds_custom(self):
        """_get_warning_thresholds reads custom values from HD Settings."""
        frappe.db.set_single_value("HD Settings", "sla_warning_thresholds", json.dumps([60, 20, 10]))
        thresholds = _get_warning_thresholds()
        self.assertEqual(thresholds, [60, 20, 10])  # sorted descending


class TestNotificationHelper(FrappeTestCase):
    """Unit tests for notifications.py helpers."""

    def setUp(self):
        frappe.set_user("Administrator")

    def tearDown(self):
        frappe.set_user("Administrator")

    def test_notify_sends_correct_payload(self):
        """notify_agent_sla_warning sends correct event, room, and message fields."""
        from helpdesk.helpdesk.automation.notifications import notify_agent_sla_warning

        ticket = make_ticket(subject="Notify Test Ticket", raised_by="notify.customer@test.com")
        resolution_by = now_datetime() + timedelta(minutes=12)

        with patch("frappe.publish_realtime") as mock_pub:
            notify_agent_sla_warning(
                ticket_name=str(ticket.name),
                assigned_to="agent@example.com",
                threshold_minutes=15,
                minutes_remaining=12.0,
                resolution_by=resolution_by,
            )

        self.assertTrue(mock_pub.called)
        _, kwargs = mock_pub.call_args
        msg = kwargs.get("message", {})
        self.assertEqual(msg["ticket"], str(ticket.name))
        self.assertEqual(msg["threshold_minutes"], 15)
        self.assertEqual(kwargs["room"], "agent:agent@example.com")
        self.assertEqual(kwargs["event"], "sla_warning")
