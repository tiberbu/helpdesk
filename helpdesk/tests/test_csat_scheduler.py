# Copyright (c) 2026, Frappe Technologies Pvt. Ltd. and contributors
# For license information, please see license.txt
"""
Unit tests for CSAT scheduler guards.
Story 3.7 / AC #1, #5, #6, #9 — csat_enabled guard, frequency limit, unsubscribe skip.

These tests mock DB calls so no real HD Ticket / HD Settings records are required.
"""
from unittest.mock import MagicMock, patch

import frappe
from frappe.tests.utils import FrappeTestCase

from helpdesk.api.csat import _mark_unsubscribed, is_unsubscribed


class TestCsatSchedulerGuards(FrappeTestCase):
	"""Guard-logic tests for send_pending_surveys()."""

	def setUp(self):
		frappe.set_user("Administrator")

	def tearDown(self):
		frappe.set_user("Administrator")
		frappe.db.rollback()

	# ------------------------------------------------------------------
	# csat_enabled feature-flag guard (AC #1)
	# ------------------------------------------------------------------

	def test_disabled_flag_returns_early(self):
		"""send_pending_surveys must do nothing when csat_enabled is falsy."""
		from helpdesk.helpdesk.doctype.hd_csat_response.csat_scheduler import (
			send_pending_surveys,
		)

		with patch("frappe.db.get_singles_dict") as mock_settings, \
		     patch("frappe.db.get_all") as mock_get_all:
			mock_settings.return_value = {"csat_enabled": 0}
			send_pending_surveys()
			mock_get_all.assert_not_called()

	def test_enabled_flag_proceeds(self):
		"""When csat_enabled=1 but no resolved statuses exist, exits cleanly."""
		from helpdesk.helpdesk.doctype.hd_csat_response.csat_scheduler import (
			send_pending_surveys,
		)

		with patch("frappe.db.get_singles_dict") as mock_settings, \
		     patch("frappe.db.get_all") as mock_get_all:
			mock_settings.return_value = {
				"csat_enabled": 1,
				"csat_delay_hours": "24",
				"csat_frequency_days": "7",
				"csat_token_expiry_days": "7",
				"csat_unsubscribed_emails": None,
			}
			# No resolved statuses → exits before ticket query
			mock_get_all.return_value = []
			send_pending_surveys()
			# get_all called once (for HD Ticket Status)
			self.assertEqual(mock_get_all.call_count, 1)

	# ------------------------------------------------------------------
	# Unsubscribe helpers (AC #6)
	# ------------------------------------------------------------------

	def test_mark_unsubscribed_adds_email(self):
		"""_mark_unsubscribed must add the email to HD Settings JSON list."""
		test_email = "unsub.csat.test@example.com"

		with patch("frappe.db.get_single_value") as mock_get, \
		     patch("frappe.db.set_single_value") as mock_set:
			mock_get.return_value = "[]"
			_mark_unsubscribed(test_email)
			mock_set.assert_called_once()
			# The second argument to set_single_value is the field name
			args = mock_set.call_args[0]
			self.assertEqual(args[1], "csat_unsubscribed_emails")
			import json
			stored = json.loads(args[2])
			self.assertIn(test_email, stored)

	def test_mark_unsubscribed_idempotent(self):
		"""Calling _mark_unsubscribed twice must not duplicate the email."""
		import json
		test_email = "dup.unsub@example.com"
		existing = json.dumps([test_email])

		with patch("frappe.db.get_single_value") as mock_get, \
		     patch("frappe.db.set_single_value") as mock_set:
			mock_get.return_value = existing
			_mark_unsubscribed(test_email)
			# Already in list → set_single_value must NOT be called again
			mock_set.assert_not_called()

	def test_is_unsubscribed_true_for_listed_email(self):
		import json
		email = "listed@example.com"
		with patch("frappe.db.get_single_value") as mock_get:
			mock_get.return_value = json.dumps([email])
			self.assertTrue(is_unsubscribed(email))

	def test_is_unsubscribed_false_for_unlisted_email(self):
		import json
		with patch("frappe.db.get_single_value") as mock_get:
			mock_get.return_value = json.dumps(["other@example.com"])
			self.assertFalse(is_unsubscribed("notlisted@example.com"))

	def test_is_unsubscribed_false_on_empty_list(self):
		with patch("frappe.db.get_single_value") as mock_get:
			mock_get.return_value = "[]"
			self.assertFalse(is_unsubscribed("anyone@example.com"))

	def test_is_unsubscribed_false_on_null_setting(self):
		with patch("frappe.db.get_single_value") as mock_get:
			mock_get.return_value = None
			self.assertFalse(is_unsubscribed("anyone@example.com"))

	# ------------------------------------------------------------------
	# Frequency limit logic (AC #5) — via scheduler with mocked DB
	# ------------------------------------------------------------------

	def test_frequency_limit_skips_recent_recipient(self):
		"""A customer who received a survey recently must be skipped."""
		from helpdesk.helpdesk.doctype.hd_csat_response.csat_scheduler import (
			send_pending_surveys,
		)

		ticket = frappe._dict(name="T-001", raised_by="freq.test@example.com", modified="2026-01-01")

		def fake_get_all(doctype, **kwargs):
			if doctype == "HD Ticket Status":
				return ["Resolved"]
			if doctype == "HD Ticket":
				return [ticket]
			if doctype == "HD CSAT Response":
				# Simulate: recent survey found for this customer
				if kwargs.get("filters", {}).get("customer_email") == "freq.test@example.com":
					return [frappe._dict(name="CSAT-OLD")]
			return []

		with patch("frappe.db.get_singles_dict") as mock_settings, \
		     patch("frappe.db.get_all", side_effect=fake_get_all), \
		     patch("frappe.db.exists", return_value=None), \
		     patch("frappe.get_doc") as mock_get_doc, \
		     patch("frappe.enqueue"):
			mock_settings.return_value = {
				"csat_enabled": 1,
				"csat_delay_hours": "0",
				"csat_frequency_days": "7",
				"csat_token_expiry_days": "7",
				"csat_unsubscribed_emails": None,
			}
			send_pending_surveys()
			# get_doc should NOT be called (no new HD CSAT Response created)
			mock_get_doc.assert_not_called()
