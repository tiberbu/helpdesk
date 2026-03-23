# Copyright (c) 2024, Frappe Technologies and Contributors
# See license.txt
"""
Tests for the close_tickets_after_n_days scheduler function.

Covers:
  (a) happy path — eligible ticket is auto-closed
  (b) error isolation — a validation failure on one ticket does not prevent
      subsequent eligible tickets from being closed
  (c) checklist guard — a mandatory unchecked checklist item blocks auto-close

Implementation notes:
  - Communications must be inserted with sent_or_received="Sent" (outgoing) so
    the on_communication_update hook does not reset the ticket status to Open.
  - The communication must be created BEFORE setting the ticket status to the
    auto-close target (e.g. "Resolved") via the ORM, so that the hook's
    internal doc.save() fires while the ticket is still "Open" and does not
    trigger validate_checklist_before_resolution.
  - For checklist tests the status must be changed via raw SQL AFTER the
    communication is inserted, because an ORM save with "Resolved" status +
    unchecked mandatory items would raise ValidationError in the test itself.
"""

import frappe
from frappe.tests import IntegrationTestCase
from frappe.utils import add_to_date, now_datetime

from helpdesk.helpdesk.doctype.hd_ticket.hd_ticket import close_tickets_after_n_days
from helpdesk.test_utils import make_status, make_ticket


# ---------------------------------------------------------------------------
# Module-level constants
# ---------------------------------------------------------------------------

_AUTO_CLOSE_STATUS = "Resolved"
_CLOSED_STATUS = "Closed"


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------


def _setup_statuses():
    """Ensure both required HD Ticket Status records exist."""
    make_status(_AUTO_CLOSE_STATUS, "Resolved")
    make_status(_CLOSED_STATUS, "Closed")


def _configure_auto_close(status: str = _AUTO_CLOSE_STATUS, days: int = 1):
    """Enable auto-close in HD Settings."""
    _setup_statuses()
    frappe.db.set_single_value("HD Settings", "auto_close_tickets", 1)
    frappe.db.set_single_value("HD Settings", "auto_close_status", status)
    frappe.db.set_single_value("HD Settings", "auto_close_after_days", days)


def _make_old_communication(ticket_name, days_old: int = 5):
    """Insert an outgoing Communication dated *days_old* days in the past.

    Using sent_or_received="Sent" (agent reply) prevents on_communication_update
    from resetting the ticket status back to Open.  The communication_date is
    set far enough in the past to satisfy the auto-close threshold.
    """
    frappe.get_doc(
        {
            "doctype": "Communication",
            "communication_type": "Communication",
            "communication_medium": "Email",
            "subject": "Test agent reply",
            "reference_doctype": "HD Ticket",
            "reference_name": str(ticket_name),
            "communication_date": add_to_date(now_datetime(), days=-days_old),
            "sent_or_received": "Sent",
        }
    ).insert(ignore_permissions=True)


def _age_all_communications(ticket_name, days_old: int = 5):
    """Backdate every Communication linked to *ticket_name* to *days_old* days ago.

    The HD Ticket after_insert hook calls create_communication_via_contact(),
    which inserts a Communication with communication_date=NOW().  Because the
    auto-close SQL query uses MAX(communication_date), that fresh record would
    prevent the ticket from appearing in the result set.  This helper forces
    all communications — including the auto-created one — to be older than the
    auto-close threshold so the query finds the ticket as expected.
    """
    old_date = add_to_date(now_datetime(), days=-days_old)
    frappe.db.sql(
        "UPDATE `tabCommunication` SET communication_date = %s"
        " WHERE reference_doctype = 'HD Ticket' AND reference_name = %s",
        (old_date, str(ticket_name)),
    )


def _set_ticket_status_raw(ticket_name, status: str):
    """Update ticket status via raw SQL, bypassing the ORM validate() hooks.

    This is necessary for checklist-related tests where an ORM save with a
    "Resolved"/"Closed" status category would trigger
    validate_checklist_before_resolution and raise ValidationError in the
    test setup itself.
    """
    frappe.db.sql(
        "UPDATE `tabHD Ticket` SET `status` = %s WHERE `name` = %s",
        (status, ticket_name),
    )


# ---------------------------------------------------------------------------
# Test class
# ---------------------------------------------------------------------------


class TestCloseTicketsAfterNDays(IntegrationTestCase):
    """Integration tests for the auto-close cron job."""

    # ------------------------------------------------------------------
    # Setup / teardown
    # ------------------------------------------------------------------

    def setUp(self):
        # Preserve HD Settings so each test starts from a known state.
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
        # Create outgoing communication first (status still "Open") so the
        # on_communication_update hook fires without triggering any guards.
        _make_old_communication(ticket.name, days_old=5)
        # Now promote status to the auto-close target via ORM save.
        ticket.reload()
        ticket.status = _AUTO_CLOSE_STATUS
        ticket.save(ignore_permissions=True)
        # Backdate ALL communications (including the one auto-created by
        # after_insert) so MAX(communication_date) satisfies the threshold.
        _age_all_communications(ticket.name, days_old=5)

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
        _make_old_communication(ticket.name, days_old=5)
        ticket.reload()
        ticket.status = _AUTO_CLOSE_STATUS
        ticket.save(ignore_permissions=True)
        _age_all_communications(ticket.name, days_old=5)

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

        # --- Ticket A: mandatory unchecked checklist item → will block auto-close ---
        ticket_a = make_ticket(subject="Checklist-blocked ticket")
        ticket_a.reload()
        ticket_a.append(
            "ticket_checklist",
            {"item": "Required step", "is_mandatory": 1, "is_completed": 0},
        )
        ticket_a.save(ignore_permissions=True)  # status still "Open" → guard inactive
        # Create communication while still "Open" so hook fires safely.
        _make_old_communication(ticket_a.name, days_old=5)
        # Set status via raw SQL to avoid triggering validate_checklist_before_resolution.
        _set_ticket_status_raw(ticket_a.name, _AUTO_CLOSE_STATUS)
        _age_all_communications(ticket_a.name, days_old=5)

        # --- Ticket B: clean ticket, should close normally ---
        ticket_b = make_ticket(subject="Normal auto-close ticket")
        _make_old_communication(ticket_b.name, days_old=5)
        ticket_b.reload()
        ticket_b.status = _AUTO_CLOSE_STATUS
        ticket_b.save(ignore_permissions=True)
        _age_all_communications(ticket_b.name, days_old=5)

        # Must not raise even though ticket_a will fail checklist validation.
        close_tickets_after_n_days()

        ticket_a.reload()
        ticket_b.reload()

        self.assertNotEqual(
            ticket_a.status,
            _CLOSED_STATUS,
            "Ticket A should NOT be closed because its mandatory checklist is incomplete.",
        )
        self.assertEqual(
            ticket_b.status,
            _CLOSED_STATUS,
            "Ticket B should be closed despite ticket A failing — savepoint isolation required.",
        )

    # ------------------------------------------------------------------
    # (c) Checklist guard — mandatory item blocks auto-close
    # ------------------------------------------------------------------

    def test_checklist_validation_blocks_auto_close(self):
        """Mandatory unchecked checklist items must prevent auto-close."""
        _configure_auto_close(days=1)

        ticket = make_ticket(subject="Checklist test")
        ticket.reload()
        ticket.append(
            "ticket_checklist",
            {"item": "Must be done first", "is_mandatory": 1, "is_completed": 0},
        )
        ticket.save(ignore_permissions=True)  # status still "Open" → guard inactive
        # Create communication while still "Open" so hook fires safely.
        _make_old_communication(ticket.name, days_old=5)
        # Set status via raw SQL to avoid triggering validate_checklist_before_resolution.
        _set_ticket_status_raw(ticket.name, _AUTO_CLOSE_STATUS)
        _age_all_communications(ticket.name, days_old=5)

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
