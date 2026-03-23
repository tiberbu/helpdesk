# Copyright (c) 2024, Frappe Technologies and Contributors
# See license.txt
"""
Tests for the close_tickets_after_n_days scheduler function.

Covers:
  (a) happy path — eligible ticket is auto-closed
  (b) error isolation — a validation failure on one ticket does not prevent
      subsequent eligible tickets from being closed
  (c) checklist guard — a mandatory unchecked checklist item blocks auto-close
"""

import frappe
from frappe.tests import IntegrationTestCase
from frappe.utils import add_to_date, now_datetime

from helpdesk.helpdesk.doctype.hd_ticket.hd_ticket import close_tickets_after_n_days
from helpdesk.test_utils import make_status, make_ticket


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------

_AUTO_CLOSE_STATUS = "Resolved"
_CLOSED_STATUS = "Closed"


def _setup_statuses():
    """Ensure the required HD Ticket Status records exist."""
    make_status(_AUTO_CLOSE_STATUS, "Resolved")
    make_status(_CLOSED_STATUS, "Closed")


def _configure_auto_close(status: str = _AUTO_CLOSE_STATUS, days: int = 1):
    """Enable auto-close in HD Settings and point it at *status*."""
    _setup_statuses()
    frappe.db.set_single_value("HD Settings", "auto_close_tickets", 1)
    frappe.db.set_single_value("HD Settings", "auto_close_status", status)
    frappe.db.set_single_value("HD Settings", "auto_close_after_days", days)


def _set_ticket_status(ticket_name, status: str):
    """Directly write status into DB without triggering document hooks."""
    frappe.db.sql(
        "UPDATE `tabHD Ticket` SET `status` = %s WHERE `name` = %s",
        [status, ticket_name],
    )


def _make_old_communication(ticket_name, days_old: int = 5):
    """Insert a Communication record dated *days_old* days in the past."""
    frappe.get_doc(
        {
            "doctype": "Communication",
            "communication_type": "Communication",
            "communication_medium": "Email",
            "subject": "Test communication",
            "reference_doctype": "HD Ticket",
            "reference_name": str(ticket_name),
            "communication_date": add_to_date(now_datetime(), days=-days_old),
            "sent_or_received": "Received",
        }
    ).insert(ignore_permissions=True)


# ---------------------------------------------------------------------------
# Test class
# ---------------------------------------------------------------------------


class TestCloseTicketsAfterNDays(IntegrationTestCase):
    """Integration tests for the auto-close cron job."""

    # ------------------------------------------------------------------
    # Setup / teardown
    # ------------------------------------------------------------------

    def setUp(self):
        # Preserve original settings so each test starts clean.
        self._orig_auto_close = frappe.db.get_single_value(
            "HD Settings", "auto_close_tickets"
        )
        self._orig_status = frappe.db.get_single_value(
            "HD Settings", "auto_close_status"
        )
        self._orig_days = frappe.db.get_single_value(
            "HD Settings", "auto_close_after_days"
        )
        frappe.db.delete("HD Ticket")
        frappe.db.delete("Communication", {"reference_doctype": "HD Ticket"})

    def tearDown(self):
        frappe.db.set_single_value(
            "HD Settings", "auto_close_tickets", self._orig_auto_close or 0
        )
        frappe.db.set_single_value(
            "HD Settings", "auto_close_status", self._orig_status or ""
        )
        frappe.db.set_single_value(
            "HD Settings", "auto_close_after_days", self._orig_days or 14
        )
        frappe.db.delete("HD Ticket")
        frappe.db.delete("Communication", {"reference_doctype": "HD Ticket"})
        frappe.db.commit()  # nosemgrep

    # ------------------------------------------------------------------
    # (a) Happy path — eligible ticket is auto-closed
    # ------------------------------------------------------------------

    def test_auto_close_happy_path(self):
        """A ticket in the auto-close status with old communication is closed."""
        _configure_auto_close(days=1)

        ticket = make_ticket(subject="Auto-close candidate")
        # Directly set the status via raw SQL to avoid triggering ORM hooks.
        _set_ticket_status(ticket.name, _AUTO_CLOSE_STATUS)
        _make_old_communication(ticket.name, days_old=5)

        close_tickets_after_n_days()

        ticket.reload()
        self.assertEqual(
            ticket.status,
            _CLOSED_STATUS,
            "Ticket should have been auto-closed by the scheduler.",
        )

    # ------------------------------------------------------------------
    # (a2) Feature-flag off — nothing happens
    # ------------------------------------------------------------------

    def test_no_action_when_feature_disabled(self):
        """When auto_close_tickets=0 the function exits early; tickets untouched."""
        _setup_statuses()
        frappe.db.set_single_value("HD Settings", "auto_close_tickets", 0)
        frappe.db.set_single_value("HD Settings", "auto_close_status", _AUTO_CLOSE_STATUS)
        frappe.db.set_single_value("HD Settings", "auto_close_after_days", 1)

        ticket = make_ticket(subject="Should not close")
        _set_ticket_status(ticket.name, _AUTO_CLOSE_STATUS)
        _make_old_communication(ticket.name, days_old=5)

        close_tickets_after_n_days()

        ticket.reload()
        self.assertEqual(
            ticket.status,
            _AUTO_CLOSE_STATUS,
            "Ticket must not be closed when auto-close is disabled.",
        )

    # ------------------------------------------------------------------
    # (b) Error isolation — failing ticket does not block subsequent ones
    # ------------------------------------------------------------------

    def test_error_isolation_between_tickets(self):
        """A ValidationError on ticket A must not prevent ticket B from closing."""
        _configure_auto_close(days=1)

        # Ticket A — add a mandatory unchecked checklist item WHILE status is
        # still "Open" (so validate() doesn't throw on save), then set status
        # to the auto-close value via raw SQL so the cron picks it up.
        ticket_a = make_ticket(subject="Checklist-blocked ticket")
        ticket_a.reload()
        ticket_a.append(
            "ticket_checklist",
            {"item": "Required step", "is_mandatory": 1, "is_completed": 0},
        )
        ticket_a.save(ignore_permissions=True)  # status still "Open" → no guard
        _set_ticket_status(ticket_a.name, _AUTO_CLOSE_STATUS)
        _make_old_communication(ticket_a.name, days_old=5)

        # Ticket B — clean, should close normally
        ticket_b = make_ticket(subject="Normal auto-close ticket")
        _set_ticket_status(ticket_b.name, _AUTO_CLOSE_STATUS)
        _make_old_communication(ticket_b.name, days_old=5)

        # Should not raise even though ticket_a will fail checklist validation
        close_tickets_after_n_days()

        ticket_a.reload()
        ticket_b.reload()

        self.assertNotEqual(
            ticket_a.status,
            _CLOSED_STATUS,
            "Ticket A should NOT be closed because its checklist is incomplete.",
        )
        self.assertEqual(
            ticket_b.status,
            _CLOSED_STATUS,
            "Ticket B should be closed despite ticket A failing — error isolation required.",
        )

    # ------------------------------------------------------------------
    # (c) Checklist guard — mandatory item blocks auto-close
    # ------------------------------------------------------------------

    def test_checklist_validation_blocks_auto_close(self):
        """Mandatory unchecked checklist items must prevent auto-close."""
        _configure_auto_close(days=1)

        # Add checklist while status is "Open" (no guard), then set status in DB.
        ticket = make_ticket(subject="Checklist test")
        ticket.reload()
        ticket.append(
            "ticket_checklist",
            {"item": "Must be done first", "is_mandatory": 1, "is_completed": 0},
        )
        ticket.save(ignore_permissions=True)  # status still "Open" → no guard
        _set_ticket_status(ticket.name, _AUTO_CLOSE_STATUS)
        _make_old_communication(ticket.name, days_old=5)

        # An error log entry should be created for this ticket
        log_count_before = frappe.db.count(
            "Error Log", {"method": ["like", "%Auto-close failed%"]}
        )

        close_tickets_after_n_days()

        ticket.reload()
        self.assertNotEqual(
            ticket.status,
            _CLOSED_STATUS,
            "Ticket with incomplete mandatory checklist must NOT be auto-closed.",
        )

        log_count_after = frappe.db.count(
            "Error Log", {"method": ["like", "%Auto-close failed%"]}
        )
        self.assertGreater(
            log_count_after,
            log_count_before,
            "An error log entry should be written when auto-close fails due to validation.",
        )
