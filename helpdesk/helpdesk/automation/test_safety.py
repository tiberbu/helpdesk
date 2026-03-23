# Copyright (c) 2026, Frappe Technologies Pvt. Ltd. and contributors
# For license information, please see license.txt

"""Unit tests for helpdesk.helpdesk.automation.safety.SafetyGuard."""

import frappe
from frappe.tests.utils import FrappeTestCase

from unittest.mock import patch

from helpdesk.helpdesk.automation.safety import (
    MAX_CONSECUTIVE_FAILURES,
    MAX_EXECUTIONS_PER_WINDOW,
    SafetyGuard,
    _notify_rule_creator,
)
from helpdesk.test_utils import create_agent, make_ticket


class TestSafetyGuard(FrappeTestCase):
    def setUp(self):
        frappe.set_user("Administrator")
        self.guard = SafetyGuard()
        # Use a unique ticket name per test to avoid key collisions
        self.ticket_name = f"TEST-SAFETY-{frappe.generate_hash(length=6)}"

    def tearDown(self):
        frappe.set_user("Administrator")
        self.guard.reset_loop_counter(self.ticket_name)
        frappe.db.rollback()

    # ------------------------------------------------------------------ #
    # Loop detection                                                        #
    # ------------------------------------------------------------------ #

    def test_first_executions_are_allowed(self):
        """First MAX_EXECUTIONS_PER_WINDOW calls must all return True."""
        for i in range(MAX_EXECUTIONS_PER_WINDOW):
            result = self.guard.check_loop(self.ticket_name)
            self.assertTrue(result, f"Call #{i + 1} should be allowed")

    def test_execution_beyond_limit_is_blocked(self):
        """Call #(MAX+1) must return False."""
        for _ in range(MAX_EXECUTIONS_PER_WINDOW):
            self.guard.check_loop(self.ticket_name)
        # Next call must be blocked
        self.assertFalse(self.guard.check_loop(self.ticket_name))

    def test_reset_clears_counter(self):
        """After reset, counter returns to zero and executions are allowed."""
        for _ in range(MAX_EXECUTIONS_PER_WINDOW):
            self.guard.check_loop(self.ticket_name)
        self.guard.reset_loop_counter(self.ticket_name)
        self.assertTrue(self.guard.check_loop(self.ticket_name))

    def test_different_tickets_have_independent_counters(self):
        """Loop counter is per-ticket; a different ticket name is unaffected."""
        other_ticket = f"TEST-OTHER-{frappe.generate_hash(length=6)}"
        try:
            for _ in range(MAX_EXECUTIONS_PER_WINDOW):
                self.guard.check_loop(self.ticket_name)
            # This ticket is now at the limit, but other_ticket is untouched
            self.assertTrue(self.guard.check_loop(other_ticket))
        finally:
            self.guard.reset_loop_counter(other_ticket)

    # ------------------------------------------------------------------ #
    # Auto-disable on consecutive failures                                 #
    # ------------------------------------------------------------------ #

    def test_record_failure_increments_counter(self):
        """record_failure should increment the failure_count field."""
        rule = frappe.get_doc(
            {
                "doctype": "HD Automation Rule",
                "rule_name": f"safety-test-{frappe.generate_hash(length=6)}",
                "trigger_type": "ticket_created",
                "enabled": 1,
                "conditions": "[]",
                "actions": "[]",
                "failure_count": 0,
            }
        ).insert(ignore_permissions=True)
        try:
            self.guard.record_failure(rule.name)
            count = frappe.db.get_value("HD Automation Rule", rule.name, "failure_count")
            self.assertEqual(int(count), 1)
        finally:
            frappe.delete_doc("HD Automation Rule", rule.name, ignore_permissions=True)
            frappe.db.commit()  # nosemgrep

    def test_auto_disable_after_max_failures(self):
        """Rule must be disabled after MAX_CONSECUTIVE_FAILURES failures."""
        rule = frappe.get_doc(
            {
                "doctype": "HD Automation Rule",
                "rule_name": f"safety-disable-{frappe.generate_hash(length=6)}",
                "trigger_type": "ticket_created",
                "enabled": 1,
                "conditions": "[]",
                "actions": "[]",
                "failure_count": MAX_CONSECUTIVE_FAILURES - 1,
            }
        ).insert(ignore_permissions=True)
        try:
            # One more failure pushes it to the threshold
            self.guard.record_failure(rule.name)
            enabled = frappe.db.get_value("HD Automation Rule", rule.name, "enabled")
            self.assertEqual(int(enabled), 0, "Rule must be auto-disabled")
        finally:
            frappe.delete_doc("HD Automation Rule", rule.name, ignore_permissions=True)
            frappe.db.commit()  # nosemgrep

    def test_record_success_resets_failure_count(self):
        """record_success should reset the failure_count to 0."""
        rule = frappe.get_doc(
            {
                "doctype": "HD Automation Rule",
                "rule_name": f"safety-reset-{frappe.generate_hash(length=6)}",
                "trigger_type": "ticket_created",
                "enabled": 1,
                "conditions": "[]",
                "actions": "[]",
                "failure_count": 5,
            }
        ).insert(ignore_permissions=True)
        try:
            self.guard.record_success(rule.name)
            count = frappe.db.get_value("HD Automation Rule", rule.name, "failure_count")
            self.assertEqual(int(count), 0)
        finally:
            frappe.delete_doc("HD Automation Rule", rule.name, ignore_permissions=True)
            frappe.db.commit()  # nosemgrep

    def test_auto_disable_triggers_notification(self):
        """Auto-disable must call sendmail and publish_realtime for rule owner."""
        rule = frappe.get_doc(
            {
                "doctype": "HD Automation Rule",
                "rule_name": f"safety-notify-{frappe.generate_hash(length=6)}",
                "trigger_type": "ticket_created",
                "enabled": 1,
                "conditions": "[]",
                "actions": "[]",
                "failure_count": MAX_CONSECUTIVE_FAILURES - 1,
            }
        ).insert(ignore_permissions=True)
        try:
            with patch("frappe.sendmail") as mock_mail, \
                 patch("frappe.publish_realtime") as mock_rt:
                self.guard.record_failure(rule.name)
                # Rule should be disabled
                enabled = frappe.db.get_value("HD Automation Rule", rule.name, "enabled")
                self.assertEqual(int(enabled), 0)
                # sendmail must have been called once for the owner
                self.assertEqual(mock_mail.call_count, 1)
                # publish_realtime must have been called with event="notification"
                notification_calls = [
                    c for c in mock_rt.call_args_list
                    if c.kwargs.get("event") == "notification"
                    or (c.args and c.args[0] == "notification")
                ]
                self.assertGreaterEqual(len(notification_calls), 1, "Expected notification realtime event")
        finally:
            frappe.delete_doc("HD Automation Rule", rule.name, ignore_permissions=True)
            frappe.db.commit()  # nosemgrep

    def test_notification_not_sent_before_threshold(self):
        """Notification must NOT be sent when failure count is below threshold."""
        rule = frappe.get_doc(
            {
                "doctype": "HD Automation Rule",
                "rule_name": f"safety-no-notify-{frappe.generate_hash(length=6)}",
                "trigger_type": "ticket_created",
                "enabled": 1,
                "conditions": "[]",
                "actions": "[]",
                "failure_count": MAX_CONSECUTIVE_FAILURES - 3,
            }
        ).insert(ignore_permissions=True)
        try:
            with patch("frappe.sendmail") as mock_mail, \
                 patch("frappe.publish_realtime") as mock_rt:
                self.guard.record_failure(rule.name)
                # Should still be enabled (not at threshold yet)
                enabled = frappe.db.get_value("HD Automation Rule", rule.name, "enabled")
                self.assertEqual(int(enabled), 1)
                # No notification should have been sent
                mock_mail.assert_not_called()
                mock_rt.assert_not_called()
        finally:
            frappe.delete_doc("HD Automation Rule", rule.name, ignore_permissions=True)
            frappe.db.commit()  # nosemgrep

    def test_notify_rule_creator_swallows_exceptions(self):
        """_notify_rule_creator() must not raise even if sendmail fails."""
        with patch("frappe.sendmail", side_effect=Exception("SMTP error")):
            try:
                _notify_rule_creator("some-nonexistent-rule")
            except Exception as e:
                self.fail(f"_notify_rule_creator raised: {e}")
