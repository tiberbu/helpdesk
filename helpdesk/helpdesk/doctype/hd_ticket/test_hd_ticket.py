# Copyright (c) 2023, Frappe Technologies and Contributors
# See license.txt

from datetime import timedelta

import frappe
from frappe.tests import IntegrationTestCase
from frappe.utils import add_to_date, get_datetime, getdate, now_datetime

from helpdesk.helpdesk.doctype.hd_ticket.api import (
    merge_ticket,
    show_outside_hours_banner,
    split_ticket,
)
from helpdesk.test_utils import (
    add_comment,
    add_holiday,
    get_current_week_monday,
    get_priority_response_resolution_time,
    make_status,
    make_ticket,
    remove_holidays,
)

ERROR_MSG_RESPONSE = "Response time differs by more than 1 second"
ERROR_MSG_RESOLUTION = "Resolution time differs by more than 1 second"


def get_ticket_obj():
    return {
        "doctype": "HD Ticket",
        "subject": "Test Ticket",
        "description": "Test Ticket Description",
    }


non_agent = "non_agent@test.com"
agent = "agent@test.com"
agent2 = "agent2@test.com"


class TestHDTicket(IntegrationTestCase):
    def setUp(self):
        frappe.db.delete("HD Ticket")
        frappe.get_doc(
            {"doctype": "User", "first_name": "Non Agent", "email": non_agent}
        ).insert(ignore_if_duplicate=True)

        frappe.get_doc(
            {"doctype": "User", "first_name": "Agent", "email": agent}
        ).insert(ignore_if_duplicate=True)

        frappe.get_doc(
            {"doctype": "HD Agent", "user": agent, "agent_name": "agent"}
        ).insert(ignore_if_duplicate=True)

        frappe.get_doc(
            {"doctype": "User", "first_name": "Agent2", "email": agent2}
        ).insert(ignore_if_duplicate=True)
        frappe.get_doc(
            {"doctype": "HD Agent", "user": agent2, "agent_name": "agent2"}
        ).insert(ignore_if_duplicate=True)
        frappe.set_value("HD Settings", "HD Settings", "enable_outside_hours_banner", 1)

    def test_ticket_creation(self):
        ticket = frappe.get_doc(get_ticket_obj())
        ticket.insert()
        self.assertTrue(ticket.name)

    def test_agent_flow(self):
        ticket = frappe.get_doc(get_ticket_obj())
        ticket.insert()

        ticket.assign_agent(agent)
        ticket.assign_agent(agent2)
        notification = frappe.get_all(
            "HD Notification",
            filters={
                "reference_ticket": ticket.name,
                "notification_type": "Assignment",
                "user_to": ["in", [agent, agent2]],
                "user_from": "Administrator",
            },
        )
        self.assertEqual(len(notification), 2)
        ticket = frappe.get_doc("HD Ticket", ticket.name)
        ticket.status = "Replied"
        ticket.save()

        ticket.status = "Open"
        ticket.save()
        self.assertTrue(ticket)

        notification = frappe.get_all(
            "HD Notification",
            filters={
                "reference_ticket": ticket.name,
                "notification_type": "Reaction",
                "user_to": ["in", [agent, agent2]],
                "user_from": "Administrator",
            },
        )
        self.assertEqual(len(notification), 2)

        ticket.status = "Resolved"
        ticket.save()
        self.assertTrue(ticket)

        ticket.status = "Closed"
        ticket.save()
        self.assertTrue(ticket)

    def test_non_agent_flow(self):
        ticket = frappe.get_doc(get_ticket_obj())
        ticket.insert()

        ticket.assign_agent(non_agent)
        notification = frappe.get_all(
            "HD Notification",
            filters={
                "reference_ticket": ticket.name,
                "notification_type": "Assignment",
                "user_to": non_agent,
                "user_from": "Administrator",
            },
        )
        self.assertEqual(len(notification), 1)

        ticket = frappe.get_doc("HD Ticket", ticket.name)
        ticket.status = "Replied"
        ticket.save()
        self.assertTrue(ticket)

        ticket.status = "Open"
        ticket.save()
        self.assertTrue(ticket)

        ticket.status = "Resolved"
        ticket.save()
        self.assertTrue(ticket)

        ticket.status = "Closed"
        ticket.save()
        self.assertTrue(ticket)

    # Working hours default to 10:00 to 18:00 from Monday to Friday
    # And priorities default to
    # Low: 24 hour response, 72 hours resolution
    # Medium: 8 hour response, 24 hours resolution
    # High: 1 hour response, 4 hours resolution
    # Urgent: 30 minutes response, 2 hours resolution

    def test_response_resolution_working_day(self):
        ticket_creation = get_current_week_monday()
        ticket = make_ticket(
            priority="High", service_level_agreement_creation=ticket_creation
        )

        expected_response_by = add_to_date(ticket_creation, hours=1)  # 1 hour later
        expected_resolution_by = add_to_date(ticket_creation, hours=4)  # 4 hours later

        self.assertAlmostEqual(
            expected_response_by.timestamp(),
            ticket.response_by.timestamp(),
            delta=1,
            msg=ERROR_MSG_RESPONSE,
        )
        self.assertAlmostEqual(
            expected_resolution_by.timestamp(),
            ticket.resolution_by.timestamp(),
            delta=1,
            msg=ERROR_MSG_RESOLUTION,
        )

    def test_response_resolution_before_working_hours(self):
        day_start_time_hours = 10
        hours_before_working = 2
        ticket_creation = getdate(get_current_week_monday())
        ticket_creation = add_to_date(
            ticket_creation, hours=day_start_time_hours - hours_before_working
        )  # Monday 8:00 AM

        ticket = make_ticket(
            priority="High", service_level_agreement_creation=ticket_creation
        )

        # high priority has 1 hour response time and 4 hours resolution time
        first_response, resolution = get_priority_response_resolution_time(
            "Default", "High", ticket_creation, add_to_time=False
        )
        # start time = 10:00 AM
        # response time = 11:00 AM
        # resolution time = 14:00 PM
        first_response_hours = day_start_time_hours + (
            first_response / 3600
        )  # 1 hour later
        resolution_hours = day_start_time_hours + (resolution / 3600)  # 4 hours later
        expected_first_response = add_to_date(
            getdate(ticket_creation), hours=first_response_hours
        )  # 11:00 AM
        expected_resolution = add_to_date(
            getdate(ticket_creation), hours=resolution_hours
        )  # 4 hours from 10:00 AM

        self.assertAlmostEqual(
            expected_first_response.timestamp(),
            ticket.response_by.timestamp(),
            delta=1,
            msg=ERROR_MSG_RESPONSE,
        )
        self.assertAlmostEqual(
            expected_resolution.timestamp(),
            ticket.resolution_by.timestamp(),
            delta=1,
            msg=ERROR_MSG_RESOLUTION,
        )

    def test_response_resolution_after_working_hours(self):
        ticket_creation = get_current_week_monday(hours=20)  # Monday 8:00 PM
        ticket = make_ticket(
            priority="Urgent", service_level_agreement_creation=ticket_creation
        )  # 30 minutes response time, 2 hours resolution time
        expected_response_by = add_to_date(
            getdate(ticket_creation), days=1, hours=10, minutes=30
        )  # Tuesday 10:30 AM
        expected_resolution_by = add_to_date(
            getdate(ticket_creation), days=1, hours=12
        )  # Tuesday 12:00 PM

        self.assertAlmostEqual(
            expected_response_by.timestamp(),
            ticket.response_by.timestamp(),
            delta=1,
            msg=ERROR_MSG_RESPONSE,
        )
        self.assertAlmostEqual(
            expected_resolution_by.timestamp(),
            ticket.resolution_by.timestamp(),
            delta=1,
            msg=ERROR_MSG_RESOLUTION,
        )

    def test_response_resolution_non_working_day(self):
        ticket_creation = add_to_date(
            get_current_week_monday(hours=0), days=5, hours=15
        )  # Saturday 3:00 PM
        ticket = make_ticket(
            priority="Low", service_level_agreement_creation=ticket_creation
        )
        response_time, resolution_time = get_priority_response_resolution_time(
            ticket.sla, ticket.priority, add_to_time=False
        )

        expected_response_by = add_to_date(
            getdate(ticket_creation), days=4, hours=18
        )  # Next week wednesday at 6:00 PM
        expected_resolution_by = add_to_date(
            getdate(ticket_creation), days=12, hours=18
        )  # 12 Days after ticket creation at 6:00 PM

        self.assertAlmostEqual(
            expected_response_by.timestamp(),
            ticket.response_by.timestamp(),
            delta=1,
            msg=ERROR_MSG_RESPONSE,
        )
        self.assertAlmostEqual(
            expected_resolution_by.timestamp(),
            ticket.resolution_by.timestamp(),
            delta=1,
            msg=ERROR_MSG_RESOLUTION,
        )

    def test_response_resolution_friday_in_working_hours(self):
        mock_date = add_to_date(
            get_current_week_monday(hours=0), days=4, hours=17
        )  # Friday 5:00 PM
        ticket = make_ticket(
            priority="Urgent", service_level_agreement_creation=mock_date
        )
        expected_response_by = add_to_date(mock_date, minutes=30)  # 30 minutes later
        expected_resolution_by = add_to_date(
            getdate(mock_date), days=3, hours=11
        )  # Monday 11:00 AM, 1 hour from friday and 1 hour from monday

        self.assertEqual(expected_response_by, ticket.response_by)
        self.assertEqual(expected_resolution_by, ticket.resolution_by)

    def test_response_resolution_friday_after_working_hours(self):
        mock_date = add_to_date(
            get_current_week_monday(hours=0), days=4, hours=19
        )  # Friday 7:00 PM

        ticket = make_ticket(
            priority="High", service_level_agreement_creation=mock_date
        )

        expected_response_by = add_to_date(
            getdate(mock_date), days=3, hours=11
        )  # Monday 11:00 AM
        expected_resolution_by = add_to_date(
            getdate(mock_date), days=3, hours=14
        )  # Monday 2:00 PM

        self.assertEqual(expected_response_by, ticket.response_by)
        self.assertEqual(expected_resolution_by, ticket.resolution_by)

    def test_response_resolution_holiday(self):
        mock_date = add_to_date(
            get_current_week_monday(hours=0), days=3, hours=15
        )  # Thursday 3:00 PM
        holiday_date = getdate(mock_date)

        add_holiday(holiday_date, "Test Holiday")  # Thursday is set as a holiday
        add_holiday(
            add_to_date(holiday_date, days=1), "Test Holiday"
        )  # Friday is set as a holiday
        # Saturday and Sunday are already non-working days

        ticket = make_ticket(
            priority="Urgent", service_level_agreement_creation=mock_date
        )

        expected_response_by = add_to_date(
            getdate(mock_date), days=4, hours=10, minutes=30
        )  # Next week Monday at 10:30 AM
        expected_resolution_by = add_to_date(getdate(mock_date), days=4, hours=12)

        self.assertEqual(expected_response_by, ticket.response_by)
        self.assertEqual(expected_resolution_by, ticket.resolution_by)

    def test_response_resolution_with_holdtime(self):
        mock_date = add_to_date(get_current_week_monday(hours=0), days=3, hours=15)

        ticket = make_ticket(
            priority="Urgent", service_level_agreement_creation=mock_date
        )

        expected_response_by = add_to_date(mock_date, minutes=30)  # 30 minutes later
        expected_resolution_by = add_to_date(mock_date, hours=2)  # 2 hours later

        self.assertEqual(expected_response_by, ticket.response_by)
        self.assertEqual(expected_resolution_by, ticket.resolution_by)

        ticket.reload()
        ticket.status = "Replied"
        ticket.save()

        ticket.reload()
        ticket.total_hold_time = 3600  # 1 hour hold time
        ticket.save()

        ticket = ticket.reload()
        new_expected_resolution_by = add_to_date(expected_resolution_by, hours=1)

        self.assertEqual(new_expected_resolution_by, ticket.resolution_by)

        ticket.total_hold_time = 3601  # 1 hour + 1 second, hold time
        ticket.save()
        ticket = ticket.reload()

        new_expected_resolution_by = add_to_date(
            getdate(expected_resolution_by), days=1, hours=10, seconds=1
        )
        self.assertEqual(new_expected_resolution_by, ticket.resolution_by)

    def test_sla_status(self):
        ticket = make_ticket(
            priority="Urgent",
        )
        self.assertEqual(ticket.agreement_status, "First Response Due")

        ticket.reload()
        ticket.status = "Replied"
        ticket.save()
        self.assertEqual(ticket.agreement_status, "Paused")
        # First response fulfilled
        self.assertTrue(ticket.first_responded_on < ticket.response_by)

        ticket.reload()
        ticket.status = "Open"
        ticket.save()
        self.assertEqual(ticket.agreement_status, "Resolution Due")

        ticket.reload()
        ticket.status = "Resolved"
        ticket.save()
        self.assertEqual(ticket.agreement_status, "Fulfilled")

    def test_hold_time_resolution_time(self):
        # Keep the ticket in paused state for 30 minutes to test hold time, resolution_by should increase by 30 minutes
        ticket = None
        date = get_current_week_monday(hours=12)
        with self.freeze_time(date):
            ticket = make_ticket(priority="High")
            self.assertEqual(ticket.agreement_status, "First Response Due")
            self.assertEqual(ticket.response_by, add_to_date(date, hours=1))
            self.assertEqual(ticket.resolution_by, add_to_date(date, hours=4))

        ticket.reload()
        with self.freeze_time(add_to_date(date, minutes=30)):
            ticket.status = "Replied"
            ticket.save()
            self.assertEqual(ticket.first_responded_on, get_datetime())
            self.assertEqual(ticket.agreement_status, "Paused")

        ticket.reload()
        with self.freeze_time(add_to_date(date, hours=1)):
            ticket.status = "Open"
            ticket.save()
            ticket.reload()

            self.assertEqual(ticket.agreement_status, "Resolution Due")
            self.assertEqual(
                ticket.resolution_by, add_to_date(date, hours=4, minutes=30)
            )

        ticket.reload()
        with self.freeze_time(add_to_date(date, hours=1, minutes=30)):
            ticket.status = "Resolved"
            ticket.save()
            ticket = ticket.reload()

            self.assertEqual(ticket.agreement_status, "Fulfilled")
            # Resolution time should be 1 hour more than the original resolution time
            self.assertEqual(ticket.resolution_time, 60 * 60)

    def test_hold_time_resolution_time_with_holiday(self):
        # create friday as holiday
        # create ticket on thursday 5:30 PM with high priority
        # change status to replied on 5:50 PM
        # change status to open on 12:30 PM on Monday
        # total_hold_time should be 1 hour 40 minutes
        # change status to resolved on 13:00 PM on Monday
        # resolution time should be 3 hours 30 minutes
        add_holiday(
            getdate(add_to_date(get_current_week_monday(), days=4)),
            "Test Holiday",
        )
        ticket = None
        date = add_to_date(
            get_current_week_monday(hours=0), days=3, hours=17, minutes=30
        )
        with self.freeze_time(date):
            ticket = make_ticket(priority="High")
            ticket.reload()

        with self.freeze_time(add_to_date(date, minutes=20)):
            ticket.status = "Replied"
            ticket.save()
            self.assertEqual(ticket.first_responded_on, get_datetime())
            self.assertEqual(ticket.agreement_status, "Paused")

        ticket.reload()
        next_monday_date = add_to_date(
            get_current_week_monday(hours=0), days=7, hours=12, minutes=30
        )
        with self.freeze_time(next_monday_date):
            ticket.status = "Open"
            ticket.save()
            ticket = ticket.reload()

            self.assertEqual(ticket.agreement_status, "Resolution Due")
            # total hold time should be 10 minutes from 5:50 PM to 6:00 PM on Thursday
            #  + 10 to 12:30 pm on monday
            expected_hold_time = 10 * 60 + 150 * 60
            self.assertEqual(ticket.total_hold_time, expected_hold_time)

        ticket.reload()
        with self.freeze_time(add_to_date(next_monday_date, minutes=30)):
            ticket.status = "Resolved"
            ticket.save()
            ticket = ticket.reload()

            self.assertEqual(ticket.agreement_status, "Fulfilled")
            # Resolution time should be 1 hour more than the original resolution time
            expected_total_time_to_resolve = (60 * 60 * 3) + 30 * 60
            expected_resolution_time = (
                expected_total_time_to_resolve - ticket.total_hold_time
            )
            self.assertEqual(
                ticket.resolution_time, expected_resolution_time
            )  # 3 hours 30 minutes

    def test_default_status(self):
        # create a new status
        # go to hd settings and set it as default
        # create a new ticket, it should have the new status as default
        ticket = make_ticket()
        self.assertNotEqual(ticket.status, "New")

        status = make_status(name="New")
        frappe.db.set_single_value("HD Settings", "default_ticket_status", status.name)
        ticket2 = make_ticket()
        self.assertEqual(ticket2.status, status.name)

        ticket2.reload()
        ticket2.status = "Replied"
        ticket2.save()
        self.assertEqual(ticket2.status, "Replied")

        ticket2.reload()

        ticket2.create_communication_via_contact("Testing reply")
        ticket2.reload()
        # reopen the ticket

        # status remains default one unless agent replies
        self.assertEqual(ticket2.status, "New")

    def test_hold_time_resolution_time_with_holiday_with_custom_status(self):
        """
        same test case as test_hold_time_resolution_time_with_holiday
        but with custom statuses

        """
        add_holiday(
            getdate(add_to_date(get_current_week_monday(), days=4)),
            "Test Holiday",
        )
        paused_status = make_status(name="On Hold", category="Paused")
        resolved_status = make_status(name="Completed", category="Resolved")
        ticket = None
        date = add_to_date(
            get_current_week_monday(hours=0), days=3, hours=17, minutes=30
        )
        with self.freeze_time(date):
            ticket = make_ticket(priority="High")
            ticket.reload()

        with self.freeze_time(add_to_date(date, minutes=20)):
            ticket.status = paused_status.name
            ticket.save()
            self.assertEqual(ticket.first_responded_on, get_datetime())
            self.assertEqual(ticket.agreement_status, "Paused")

        ticket.reload()

        next_monday_date = add_to_date(
            get_current_week_monday(hours=0), days=7, hours=12, minutes=30
        )
        with self.freeze_time(next_monday_date):
            ticket.status = "Open"
            ticket.save()
            ticket = ticket.reload()

            self.assertEqual(ticket.agreement_status, "Resolution Due")
            # total hold time should be 10 minutes from 5:50 PM to 6:00 PM on Thursday
            #  + 10 to 12:30 pm on monday
            expected_hold_time = 10 * 60 + 150 * 60
            self.assertEqual(ticket.total_hold_time, expected_hold_time)

        ticket.reload()

        with self.freeze_time(add_to_date(next_monday_date, minutes=30)):
            ticket.status = resolved_status.name
            ticket.save()
            ticket = ticket.reload()

            self.assertEqual(ticket.agreement_status, "Fulfilled")
            # Resolution time should be 1 hour more than the original resolution time
            expected_total_time_to_resolve = (60 * 60 * 3) + 30 * 60
            expected_resolution_time = (
                expected_total_time_to_resolve - ticket.total_hold_time
            )
            self.assertEqual(ticket.resolution_time, expected_resolution_time)

    def test_resolve_closed_resolution_time(self):
        """
        Ticket resolution time should not change if ticket goes from resolved to closed
        """
        date = get_current_week_monday(hours=12)
        with self.freeze_time(date):
            ticket = make_ticket(priority="High")

        ticket.reload()
        with self.freeze_time(add_to_date(date, minutes=30)):
            ticket.status = "Resolved"
            ticket.save()
            self.assertEqual(ticket.resolution_time, 30 * 60)

        ticket.reload()
        with self.freeze_time(add_to_date(date, days=1)):
            ticket.status = "Closed"
            ticket.save()
            self.assertEqual(ticket.resolution_time, 30 * 60)

    def test_ticket_merge(self):
        ticket1 = make_ticket(description="Test Desc 1")
        add_comment(ticket1.name, "First comment on ticket 1")

        ticket2 = make_ticket(description="Test Desc 2")
        add_comment(ticket2.name, "First comment on ticket 2")

        merge_ticket(source=ticket1.name, target=ticket2.name)
        ticket1.reload()
        self.assertEqual(ticket1.status, "Closed")
        self.assertTrue(ticket1.is_merged)
        self.assertEqual(int(ticket1.merged_with), int(ticket2.name))

        ticket2.reload()
        comments = frappe.get_all(
            "HD Ticket Comment",
            filters={
                "reference_ticket": ticket2.name,
            },
            fields=["content", "name"],
        )
        self.assertEqual(
            len(comments), 3
        )  # 2 original comments + 1 merge comment (Ticket 1 merged into Ticket 2)

    def test_ticket_split(self):
        ticket1 = make_ticket(description="Test Desc for split")
        ticket1.reply_via_agent(message="Test reply to split")
        communcation_name = frappe.get_all(
            "Communication",
            filters={
                "reference_doctype": "HD Ticket",
                "reference_name": ticket1.name,
            },
            pluck="name",
        )[0]
        self.assertTrue(communcation_name)

        ticket2: str = split_ticket(
            subject="Split Ticket", communication_id=communcation_name
        )
        ticket2_doc = frappe.get_doc("HD Ticket", ticket2)
        self.assertTrue(ticket2_doc)
        self.assertEqual(ticket2_doc.subject, "Split Ticket")
        self.assertTrue(
            frappe.get_value("Communication", communcation_name, "reference_name"),
            ticket2_doc.name,
        )

    def test_ticket_inside_working_hours(self):
        inside_working_hour = get_current_week_monday(hours=14)
        with self.freeze_time(inside_working_hour):
            ticket = make_ticket(priority="High")
            self.assertFalse(ticket.raised_outside_working_hours)

    def test_ticket_inside_working_hours_currently_outside(self):
        inside_working_hour = get_current_week_monday(hours=14)
        with self.freeze_time(inside_working_hour):
            # Ticket created inside working hours
            ticket = make_ticket(priority="High")
            self.assertFalse(ticket.raised_outside_working_hours)
            banner_shown = show_outside_hours_banner(ticket.name)["show"]
            self.assertFalse(banner_shown)

        ticket.reload()
        with self.freeze_time(get_current_week_monday(hours=20)):
            banner_shown = show_outside_hours_banner(ticket.name)["show"]
            self.assertFalse(banner_shown)

    def test_ticket_outside_working_hours(self):
        outside_working_hour = get_current_week_monday(hours=8)
        with self.freeze_time(outside_working_hour):
            ticket = make_ticket(priority="High")
            banner_shown = show_outside_hours_banner(ticket.name)["show"]
            self.assertTrue(ticket.raised_outside_working_hours)
            self.assertTrue(banner_shown)

    def test_ticket_outside_working_hours_currently_in_working_hour(self):
        outside_working_hours = get_current_week_monday(hours=8)
        with self.freeze_time(outside_working_hours):
            ticket = make_ticket(priority="High")
            banner_shown = show_outside_hours_banner(ticket.name)["show"]
            self.assertTrue(ticket.raised_outside_working_hours)
            self.assertTrue(banner_shown)

        ticket.reload()
        newtime = add_to_date(get_current_week_monday(hours=14), days=1)
        with self.freeze_time(newtime):
            banner_shown = show_outside_hours_banner(ticket.name)["show"]
            self.assertFalse(banner_shown)
            self.assertTrue(ticket.raised_outside_working_hours)

    def test_ticket_outside_working_hours_weekend(self):
        weekend = add_to_date(get_current_week_monday(), days=5, hours=14)
        with self.freeze_time(weekend):
            ticket = make_ticket(priority="High")
            banner_shown = show_outside_hours_banner(ticket.name)["show"]
            self.assertTrue(ticket.raised_outside_working_hours)
            self.assertTrue(banner_shown)

    def test_ticket_outside_working_hours_agent_replied(self):
        outside_working_hour = get_current_week_monday(hours=8)
        with self.freeze_time(outside_working_hour):
            ticket = make_ticket(priority="High")
            ticket.reply_via_agent(message="Test reply to split")
            banner_shown = show_outside_hours_banner(ticket.name)["show"]
            self.assertTrue(ticket.raised_outside_working_hours)
            self.assertFalse(banner_shown)

    def test_if_banner_not_shown_after_next_working_day(self):
        outside_working_hour_day_1 = get_current_week_monday(hours=20)
        with self.freeze_time(outside_working_hour_day_1):
            ticket = make_ticket(priority="low")

        ticket.reload()
        next_working_day = add_to_date(get_current_week_monday(hours=20), days=1)
        with self.freeze_time(next_working_day):
            banner_shown = show_outside_hours_banner(ticket.name)["show"]
            self.assertFalse(banner_shown)

    def tearDown(self):
        remove_holidays()
        frappe.db.set_single_value("HD Settings", "default_ticket_status", "Open")
        frappe.delete_doc("HD Ticket Status", "New", force=True)


DEFAULT_PRIORITY_MATRIX = {
    "High-High": "Urgent",
    "High-Medium": "High",
    "High-Low": "Medium",
    "Medium-High": "High",
    "Medium-Medium": "Medium",
    "Medium-Low": "Low",
    "Low-High": "Medium",
    "Low-Medium": "Low",
    "Low-Low": "Low",
}


def _enable_itil_mode():
    """Enable ITIL mode and ensure default priority matrix is set."""
    import json

    frappe.db.set_single_value("HD Settings", "itil_mode_enabled", 1)
    frappe.db.set_single_value(
        "HD Settings", "priority_matrix", json.dumps(DEFAULT_PRIORITY_MATRIX)
    )


def _disable_itil_mode():
    """Restore ITIL mode to disabled (default)."""
    frappe.db.set_single_value("HD Settings", "itil_mode_enabled", 0)


def _make_itil_ticket(impact, urgency, priority=None):
    """Create and insert a ticket with given impact/urgency values."""
    kwargs = {"impact": impact, "urgency": urgency}
    if priority:
        kwargs["priority"] = priority
    return make_ticket(**kwargs)


class TestPriorityMatrix(IntegrationTestCase):
    """
    Unit tests for Story 1.2: Impact x Urgency → Priority auto-calculation.

    Covers all 9 matrix combinations (AC #2, #9), legacy ticket backward
    compatibility (AC #6), ITIL mode disabled guard (AC #10), custom matrix
    (AC #4), and matrix validation (AC #5).
    """

    def setUp(self):
        frappe.db.delete("HD Ticket")
        _enable_itil_mode()

    def addCleanup_settings(self):
        """Register cleanup to restore HD Settings to defaults after each test."""
        self.addCleanup(_disable_itil_mode)

    # ------------------------------------------------------------------
    # AC #2 / #9: All 9 Impact × Urgency combinations
    # ------------------------------------------------------------------

    def _assert_matrix(self, impact, urgency, expected_priority):
        """Helper: insert ticket, assert calculated priority matches expected."""
        self.addCleanup(_disable_itil_mode)
        ticket = _make_itil_ticket(impact, urgency)
        self.assertEqual(
            ticket.priority,
            expected_priority,
            f"Expected {impact}-{urgency} → {expected_priority}, got {ticket.priority}",
        )

    def test_priority_matrix_high_high(self):
        self._assert_matrix("High", "High", "Urgent")

    def test_priority_matrix_high_medium(self):
        self._assert_matrix("High", "Medium", "High")

    def test_priority_matrix_high_low(self):
        self._assert_matrix("High", "Low", "Medium")

    def test_priority_matrix_medium_high(self):
        self._assert_matrix("Medium", "High", "High")

    def test_priority_matrix_medium_medium(self):
        self._assert_matrix("Medium", "Medium", "Medium")

    def test_priority_matrix_medium_low(self):
        self._assert_matrix("Medium", "Low", "Low")

    def test_priority_matrix_low_high(self):
        self._assert_matrix("Low", "High", "Medium")

    def test_priority_matrix_low_medium(self):
        self._assert_matrix("Low", "Medium", "Low")

    def test_priority_matrix_low_low(self):
        self._assert_matrix("Low", "Low", "Low")

    # ------------------------------------------------------------------
    # AC #6: Legacy tickets (empty impact/urgency) retain their priority
    # ------------------------------------------------------------------

    def test_legacy_ticket_retains_priority(self):
        """Ticket with no impact/urgency keeps its manually-set priority in ITIL mode."""
        self.addCleanup(_disable_itil_mode)
        ticket = make_ticket(priority="High")  # no impact or urgency
        self.assertEqual(ticket.priority, "High")

    def test_legacy_ticket_retains_priority_after_update(self):
        """Saving a legacy ticket (no impact/urgency) does not change priority."""
        self.addCleanup(_disable_itil_mode)
        ticket = make_ticket(priority="Low")
        ticket.reload()
        ticket.subject = "Updated subject"
        ticket.save()
        self.assertEqual(ticket.priority, "Low")

    # ------------------------------------------------------------------
    # AC #10: ITIL mode disabled — matrix logic is not invoked
    # ------------------------------------------------------------------

    def test_itil_mode_off_no_calculation(self):
        """When ITIL mode is disabled, impact+urgency do NOT trigger matrix."""
        _disable_itil_mode()
        # Priority set explicitly; matrix should not override it
        ticket = _make_itil_ticket("High", "High", priority="Low")
        self.assertEqual(
            ticket.priority,
            "Low",
            "Priority must not be overridden when ITIL mode is off",
        )

    # ------------------------------------------------------------------
    # AC #4: Custom matrix is used for calculation
    # ------------------------------------------------------------------

    def test_custom_matrix_used_when_set(self):
        """Calculations use the custom matrix stored in HD Settings."""
        import json

        self.addCleanup(_disable_itil_mode)
        # Override High-High to map to Low (non-default)
        custom_matrix = {**DEFAULT_PRIORITY_MATRIX, "High-High": "Low"}
        frappe.db.set_single_value(
            "HD Settings", "priority_matrix", json.dumps(custom_matrix)
        )
        ticket = _make_itil_ticket("High", "High")
        self.assertEqual(ticket.priority, "Low")

    # ------------------------------------------------------------------
    # AC #5: HD Settings validate rejects invalid / incomplete matrix
    # ------------------------------------------------------------------

    def test_custom_matrix_validation_missing_keys(self):
        """Saving HD Settings with an incomplete matrix raises ValidationError."""
        import json

        self.addCleanup(_disable_itil_mode)
        settings = frappe.get_single("HD Settings")
        settings.itil_mode_enabled = 1
        # Matrix with only 1 key — missing 8 required combinations
        settings.priority_matrix = json.dumps({"High-High": "Urgent"})
        self.assertRaises(frappe.ValidationError, settings.validate_priority_matrix)

    def test_custom_matrix_validation_invalid_priority_value(self):
        """Saving HD Settings with invalid priority values raises ValidationError."""
        import json

        self.addCleanup(_disable_itil_mode)
        settings = frappe.get_single("HD Settings")
        settings.itil_mode_enabled = 1
        bad_matrix = {**DEFAULT_PRIORITY_MATRIX, "High-High": "Critical"}  # invalid
        settings.priority_matrix = json.dumps(bad_matrix)
        self.assertRaises(frappe.ValidationError, settings.validate_priority_matrix)

    def test_custom_matrix_validation_malformed_json(self):
        """Saving HD Settings with non-JSON string raises ValidationError."""
        self.addCleanup(_disable_itil_mode)
        settings = frappe.get_single("HD Settings")
        settings.itil_mode_enabled = 1
        settings.priority_matrix = "not valid json {"
        self.assertRaises(frappe.ValidationError, settings.validate_priority_matrix)

    def test_matrix_validation_skipped_when_itil_mode_off(self):
        """validate_priority_matrix does not raise when ITIL mode is disabled."""
        import json

        settings = frappe.get_single("HD Settings")
        settings.itil_mode_enabled = 0
        settings.priority_matrix = json.dumps({"High-High": "Urgent"})  # incomplete
        # Should NOT raise even though matrix is incomplete
        settings.validate_priority_matrix()  # no exception expected

    def tearDown(self):
        frappe.db.delete("HD Ticket")
        _disable_itil_mode()
