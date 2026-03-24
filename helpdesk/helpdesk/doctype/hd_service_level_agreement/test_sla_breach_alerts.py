# Copyright (c) 2026, Frappe Technologies Pvt. Ltd. and contributors
# For license information, please see license.txt

"""Unit tests for Story 4.2: Proactive SLA Breach Alerts.

Tests:
    AC#1  - Warning threshold configuration per SLA / HD Settings
    AC#5  - In-app notification (toast + badge) at each threshold
    AC#6  - Team manager notification at 15-min threshold only
    AC#7  - SLA breach sets agreement_status = "Failed", publishes sla_breached event
    AC#8  - sla_warning event fires automation engine
    AC#9  - sla_breached event fires automation engine (idempotency guard)
    AC#10 - Warning deduplication — each threshold fires exactly once
    AC#11 - SLA breach email enqueued via frappe.enqueue
    AC#12 - _get_manager_notification_threshold reads from HD Settings
"""

import json
from datetime import timedelta
from unittest.mock import call, patch

import frappe
from frappe.tests.utils import FrappeTestCase
from frappe.utils import now_datetime

from helpdesk.helpdesk.doctype.hd_service_level_agreement.sla_monitor import (
    _fire_breached,
    _fire_warning,
    _get_manager_notification_threshold,
    clear_warning_dedup,
)
from helpdesk.test_utils import create_agent, make_ticket


def _make_team(name: str, sla_manager: str = None):
    """Create a minimal HD Team, optionally with an sla_manager."""
    if frappe.db.exists("HD Team", name):
        team = frappe.get_doc("HD Team", name)
        if sla_manager is not None:
            team.sla_manager = sla_manager
            team.save(ignore_permissions=True)
        return team
    doc = frappe.get_doc({
        "doctype": "HD Team",
        "team_name": name,
        "sla_manager": sla_manager,
    })
    doc.insert(ignore_permissions=True)
    return doc


class TestSLAManagerNotification(FrappeTestCase):
    """AC#6 — Team manager receives notification at manager_threshold only."""

    def setUp(self):
        frappe.set_user("Administrator")
        frappe.db.set_single_value("HD Settings", "sla_warning_thresholds", json.dumps([30, 15, 5]))
        frappe.db.set_single_value("HD Settings", "sla_manager_notification_threshold", 15)
        create_agent("sla.mgr.agent@test.com", "SLA", "Manager")
        create_agent("sla.mgr.manager@test.com", "SLA", "Mgr")
        self._team = _make_team("SLATestTeam-42", sla_manager="sla.mgr.manager@test.com")
        self._tickets = []

    def tearDown(self):
        frappe.set_user("Administrator")
        for t in self._tickets:
            if frappe.db.exists("HD Ticket", t):
                frappe.delete_doc("HD Ticket", t, ignore_permissions=True, force=True)
        frappe.db.commit()  # nosemgrep
        frappe.db.rollback()
        frappe.db.set_single_value("HD Settings", "sla_manager_notification_threshold", 15)

    def _ticket(self, minutes_to_breach=10.0):
        t = make_ticket(
            subject=f"Mgr Test {frappe.generate_hash(length=6)}",
            raised_by="mgr.customer@test.com",
        )
        resolution_by = now_datetime() + timedelta(minutes=minutes_to_breach)
        frappe.db.set_value("HD Ticket", t.name, {
            "resolution_by": resolution_by,
            "agent_group": self._team.name,
        })
        clear_warning_dedup(str(t.name))
        self._tickets.append(t.name)
        return frappe.get_doc("HD Ticket", t.name)

    def test_manager_notified_at_15min_threshold(self):
        """Manager receives notification when threshold == manager_notification_threshold (15)."""
        ticket = self._ticket(minutes_to_breach=10.0)
        resolution_by = now_datetime() + timedelta(minutes=10)

        with patch("frappe.publish_realtime") as mock_pub:
            _fire_warning(
                str(ticket.name),
                assigned_to="sla.mgr.agent@test.com",
                threshold=15,
                minutes_remaining=10.0,
                resolution_by=resolution_by,
                agent_group=self._team.name,
                manager_threshold=15,
            )

        # Should have been called at least twice: agent + manager
        calls = mock_pub.call_args_list
        users = [c[1].get("user") for c in calls]
        self.assertIn(
            "sla.mgr.agent@test.com", users,
            "Agent must receive sla_warning notification"
        )
        manager_email = frappe.db.get_value("HD Agent", "sla.mgr.manager@test.com", "user")
        self.assertIn(
            manager_email, users,
            "Manager must receive sla_warning notification at 15-min threshold"
        )

    def test_manager_not_notified_at_30min_threshold(self):
        """Manager does NOT receive notification at the 30-min threshold."""
        ticket = self._ticket(minutes_to_breach=25.0)
        resolution_by = now_datetime() + timedelta(minutes=25)

        with patch("frappe.publish_realtime") as mock_pub:
            _fire_warning(
                str(ticket.name),
                assigned_to="sla.mgr.agent@test.com",
                threshold=30,
                minutes_remaining=25.0,
                resolution_by=resolution_by,
                agent_group=self._team.name,
                manager_threshold=15,
            )

        calls = mock_pub.call_args_list
        users = [c[1].get("user") for c in calls]
        manager_email = frappe.db.get_value("HD Agent", "sla.mgr.manager@test.com", "user")
        self.assertNotIn(
            manager_email, users,
            "Manager must NOT receive notification at 30-min threshold"
        )

    def test_manager_not_notified_at_5min_threshold(self):
        """Manager does NOT receive notification at the 5-min threshold."""
        ticket = self._ticket(minutes_to_breach=3.0)
        resolution_by = now_datetime() + timedelta(minutes=3)

        with patch("frappe.publish_realtime") as mock_pub:
            _fire_warning(
                str(ticket.name),
                assigned_to="sla.mgr.agent@test.com",
                threshold=5,
                minutes_remaining=3.0,
                resolution_by=resolution_by,
                agent_group=self._team.name,
                manager_threshold=15,
            )

        calls = mock_pub.call_args_list
        users = [c[1].get("user") for c in calls]
        manager_email = frappe.db.get_value("HD Agent", "sla.mgr.manager@test.com", "user")
        self.assertNotIn(
            manager_email, users,
            "Manager must NOT receive notification at 5-min threshold"
        )

    def test_manager_notification_skipped_when_no_sla_manager(self):
        """No manager notification when team has no sla_manager set."""
        team_no_mgr = _make_team("SLATestTeamNoMgr-42", sla_manager=None)
        ticket = make_ticket(
            subject=f"No Mgr {frappe.generate_hash(length=6)}",
            raised_by="nomgr.customer@test.com",
        )
        frappe.db.set_value("HD Ticket", ticket.name, {
            "resolution_by": now_datetime() + timedelta(minutes=10),
            "agent_group": team_no_mgr.name,
        })
        clear_warning_dedup(str(ticket.name))
        self._tickets.append(ticket.name)
        resolution_by = now_datetime() + timedelta(minutes=10)

        with patch("frappe.publish_realtime") as mock_pub:
            _fire_warning(
                str(ticket.name),
                assigned_to="sla.mgr.agent@test.com",
                threshold=15,
                minutes_remaining=10.0,
                resolution_by=resolution_by,
                agent_group=team_no_mgr.name,
                manager_threshold=15,
            )

        calls = mock_pub.call_args_list
        # Only the agent notification should be present (1 call for agent)
        self.assertEqual(
            len([c for c in calls if c[1].get("event") == "sla_warning"]),
            1,
            "Only agent notification must fire when team has no sla_manager"
        )

    def test_manager_notification_skipped_when_no_agent_group(self):
        """No manager notification attempt when ticket has no agent_group."""
        ticket = self._ticket(minutes_to_breach=10.0)
        resolution_by = now_datetime() + timedelta(minutes=10)

        with patch("frappe.publish_realtime") as mock_pub:
            _fire_warning(
                str(ticket.name),
                assigned_to="sla.mgr.agent@test.com",
                threshold=15,
                minutes_remaining=10.0,
                resolution_by=resolution_by,
                agent_group="",  # No team
                manager_threshold=15,
            )

        calls = mock_pub.call_args_list
        self.assertEqual(
            len([c for c in calls if c[1].get("event") == "sla_warning"]),
            1,
            "Only agent notification must fire when ticket has no agent_group"
        )


class TestSLABreachBehavior(FrappeTestCase):
    """AC#7 — Breach sets agreement_status=Failed, publishes sla_breached, enqueues email."""

    def setUp(self):
        frappe.set_user("Administrator")
        frappe.db.set_single_value("HD Settings", "automation_enabled", 0)
        self._tickets = []

    def tearDown(self):
        frappe.set_user("Administrator")
        for t in self._tickets:
            if frappe.db.exists("HD Ticket", t):
                frappe.delete_doc("HD Ticket", t, ignore_permissions=True, force=True)
        frappe.db.commit()  # nosemgrep
        frappe.db.rollback()

    def _ticket_breached(self):
        t = make_ticket(
            subject=f"Breach Test {frappe.generate_hash(length=6)}",
            raised_by="breach.customer@test.com",
        )
        resolution_by = now_datetime() - timedelta(minutes=5)
        frappe.db.set_value("HD Ticket", t.name, "resolution_by", resolution_by)
        clear_warning_dedup(str(t.name))
        self._tickets.append(t.name)
        return frappe.get_doc("HD Ticket", t.name)

    def test_breach_sets_agreement_status_failed(self):
        """_fire_breached() sets agreement_status = 'Failed' on the ticket."""
        ticket = self._ticket_breached()
        with patch("frappe.publish_realtime"):
            with patch("frappe.enqueue"):
                _fire_breached(str(ticket.name), assigned_to="")

        status = frappe.db.get_value("HD Ticket", ticket.name, "agreement_status")
        self.assertEqual(status, "Failed", "agreement_status must be set to 'Failed' on breach")

    def test_breach_publishes_sla_breached_event(self):
        """_fire_breached() publishes sla_breached real-time event to assigned agent."""
        create_agent("sla.breach.notify@test.com", "Breach", "Notify")
        ticket = self._ticket_breached()

        with patch("frappe.publish_realtime") as mock_pub:
            with patch("frappe.enqueue"):
                _fire_breached(str(ticket.name), assigned_to="sla.breach.notify@test.com")

        events = [c[1].get("event") for c in mock_pub.call_args_list]
        self.assertIn("sla_breached", events, "sla_breached realtime event must be published on breach")

    def test_breach_enqueues_email(self):
        """_fire_breached() enqueues send_breach_email on the short queue."""
        create_agent("sla.breach.email@test.com", "Breach", "Email")
        ticket = self._ticket_breached()

        with patch("frappe.publish_realtime"):
            with patch("frappe.enqueue") as mock_enqueue:
                _fire_breached(str(ticket.name), assigned_to="sla.breach.email@test.com")

        enqueued_funcs = [c[0][0] for c in mock_enqueue.call_args_list if c[0]]
        self.assertTrue(
            any("send_breach_email" in f for f in enqueued_funcs),
            "send_breach_email must be enqueued on breach"
        )
        # Verify short queue
        queue_args = [c[1].get("queue") for c in mock_enqueue.call_args_list]
        self.assertIn("short", queue_args, "Breach email must be enqueued on 'short' queue")

    def test_breach_idempotency_no_double_fire(self):
        """_fire_breached() is a no-op on second call for same ticket (dedup guard)."""
        ticket = self._ticket_breached()

        with patch("frappe.publish_realtime"):
            with patch("frappe.enqueue"):
                _fire_breached(str(ticket.name), assigned_to="")

        # Reset status to detect re-fire
        frappe.db.set_value("HD Ticket", ticket.name, "agreement_status", "Resolution Due")

        with patch("frappe.publish_realtime") as mock_pub2:
            with patch("frappe.enqueue") as mock_enq2:
                _fire_breached(str(ticket.name), assigned_to="")

        # Second call should be blocked by dedup
        self.assertFalse(mock_pub2.called, "sla_breached event must not fire a second time")
        self.assertFalse(mock_enq2.called, "Breach email must not be enqueued a second time")
        status = frappe.db.get_value("HD Ticket", ticket.name, "agreement_status")
        self.assertEqual(status, "Resolution Due", "agreement_status must not change on second breach call")


class TestManagerThresholdConfig(FrappeTestCase):
    """AC#1, AC#12 — Manager notification threshold reads from HD Settings."""

    def setUp(self):
        frappe.set_user("Administrator")

    def tearDown(self):
        frappe.set_user("Administrator")
        frappe.db.set_single_value("HD Settings", "sla_manager_notification_threshold", 15)

    def test_default_manager_threshold_is_15(self):
        """Default manager notification threshold is 15 when setting is None."""
        frappe.db.set_single_value("HD Settings", "sla_manager_notification_threshold", None)
        threshold = _get_manager_notification_threshold()
        self.assertEqual(threshold, 15)

    def test_custom_manager_threshold_reads_from_settings(self):
        """_get_manager_notification_threshold reads custom value from HD Settings."""
        frappe.db.set_single_value("HD Settings", "sla_manager_notification_threshold", 10)
        threshold = _get_manager_notification_threshold()
        self.assertEqual(threshold, 10)

    def test_zero_manager_threshold_falls_back_to_default(self):
        """Zero value in HD Settings falls back to default 15."""
        frappe.db.set_single_value("HD Settings", "sla_manager_notification_threshold", 0)
        threshold = _get_manager_notification_threshold()
        self.assertEqual(threshold, 15)


class TestNotifyManagerSLAWarning(FrappeTestCase):
    """Unit tests for notifications.notify_manager_sla_warning()."""

    def setUp(self):
        frappe.set_user("Administrator")
        create_agent("notif.manager.test@test.com", "Notif", "ManagerTest")
        self._team = _make_team("NotifMgrTeam-42", sla_manager="notif.manager.test@test.com")
        self._tickets = []

    def tearDown(self):
        frappe.set_user("Administrator")
        for t in self._tickets:
            if frappe.db.exists("HD Ticket", t):
                frappe.delete_doc("HD Ticket", t, ignore_permissions=True, force=True)
        frappe.db.commit()  # nosemgrep
        frappe.db.rollback()

    def _ticket(self):
        t = make_ticket(
            subject=f"Notif Mgr {frappe.generate_hash(length=6)}",
            raised_by="nm.customer@test.com",
        )
        self._tickets.append(t.name)
        return t

    def test_notify_manager_publishes_sla_warning_to_manager_email(self):
        """notify_manager_sla_warning publishes sla_warning event to manager's user email."""
        from helpdesk.helpdesk.automation.notifications import notify_manager_sla_warning

        ticket = self._ticket()
        resolution_by = now_datetime() + timedelta(minutes=12)
        manager_user_email = frappe.db.get_value(
            "HD Agent", "notif.manager.test@test.com", "user"
        )

        with patch("frappe.publish_realtime") as mock_pub:
            notify_manager_sla_warning(
                ticket_name=str(ticket.name),
                team_name=self._team.name,
                threshold_minutes=15,
                minutes_remaining=12.0,
                resolution_by=resolution_by,
            )

        mock_pub.assert_called_once()
        kwargs = mock_pub.call_args[1]
        self.assertEqual(kwargs["event"], "sla_warning")
        self.assertEqual(kwargs["user"], manager_user_email)
        self.assertTrue(kwargs["message"].get("is_manager_notification"))

    def test_notify_manager_noop_when_no_team(self):
        """notify_manager_sla_warning is a no-op when team_name is empty."""
        from helpdesk.helpdesk.automation.notifications import notify_manager_sla_warning

        with patch("frappe.publish_realtime") as mock_pub:
            notify_manager_sla_warning(
                ticket_name="FAKE-001",
                team_name="",
                threshold_minutes=15,
                minutes_remaining=10.0,
                resolution_by=now_datetime(),
            )

        mock_pub.assert_not_called()

    def test_notify_manager_noop_when_team_has_no_sla_manager(self):
        """notify_manager_sla_warning is a no-op when team.sla_manager is not set."""
        from helpdesk.helpdesk.automation.notifications import notify_manager_sla_warning

        team_no_mgr = _make_team("NMNoMgr-42", sla_manager=None)

        with patch("frappe.publish_realtime") as mock_pub:
            notify_manager_sla_warning(
                ticket_name="FAKE-002",
                team_name=team_no_mgr.name,
                threshold_minutes=15,
                minutes_remaining=10.0,
                resolution_by=now_datetime(),
            )

        mock_pub.assert_not_called()

    def test_notify_manager_payload_includes_is_manager_flag(self):
        """Manager notification payload contains is_manager_notification=True."""
        from helpdesk.helpdesk.automation.notifications import notify_manager_sla_warning

        ticket = self._ticket()
        with patch("frappe.publish_realtime") as mock_pub:
            notify_manager_sla_warning(
                ticket_name=str(ticket.name),
                team_name=self._team.name,
                threshold_minutes=15,
                minutes_remaining=12.0,
                resolution_by=now_datetime() + timedelta(minutes=12),
            )

        msg = mock_pub.call_args[1]["message"]
        self.assertTrue(
            msg.get("is_manager_notification"),
            "Manager notification payload must have is_manager_notification=True"
        )
        self.assertEqual(msg["threshold_minutes"], 15)
        self.assertEqual(msg["ticket"], str(ticket.name))
