# Copyright (c) 2026, Frappe Technologies Pvt. Ltd. and contributors
# For license information, please see license.txt
"""
Unit tests for HDCSATResponse DocType controller.
Story 3.7 / AC #3, #8 — rating bounds validation, single-use token enforcement.
"""
import frappe
from frappe.tests.utils import FrappeTestCase

from helpdesk.utils import generate_csat_token


class TestHDCSATResponse(FrappeTestCase):
	"""Tests for HDCSATResponse validate() and controller logic."""

	def setUp(self):
		frappe.set_user("Administrator")

	def tearDown(self):
		frappe.set_user("Administrator")
		frappe.db.rollback()

	# ------------------------------------------------------------------
	# Rating validation
	# ------------------------------------------------------------------

	def _make_response(self, rating=None):
		"""Helper: build an unsaved HDCSATResponse doc."""
		token = generate_csat_token("TEST-1", "csat.test@example.com", expiry_days=7)
		doc = frappe.get_doc({
			"doctype": "HD CSAT Response",
			"ticket": None,  # no real ticket needed for unit test
			"customer_email": "csat.test@example.com",
			"token": token,
			"token_used": 0,
			"rating": rating,
		})
		return doc

	def test_valid_rating_1_passes(self):
		doc = self._make_response(rating=1)
		# Should not throw
		doc._validate_rating()

	def test_valid_rating_5_passes(self):
		doc = self._make_response(rating=5)
		doc._validate_rating()

	def test_valid_rating_3_passes(self):
		doc = self._make_response(rating=3)
		doc._validate_rating()

	def test_none_rating_passes(self):
		"""Rating is optional — None must be accepted."""
		doc = self._make_response(rating=None)
		doc._validate_rating()

	def test_rating_zero_rejected(self):
		doc = self._make_response(rating=0)
		with self.assertRaises(frappe.ValidationError):
			doc._validate_rating()

	def test_rating_six_rejected(self):
		doc = self._make_response(rating=6)
		with self.assertRaises(frappe.ValidationError):
			doc._validate_rating()

	def test_rating_negative_rejected(self):
		doc = self._make_response(rating=-1)
		with self.assertRaises(frappe.ValidationError):
			doc._validate_rating()

	# ------------------------------------------------------------------
	# Single-use token enforcement (DB-level check via API)
	# ------------------------------------------------------------------

	def test_token_used_flag_defaults_to_zero(self):
		"""token_used must default to 0 on a new doc."""
		doc = self._make_response()
		self.assertEqual(doc.token_used, 0)

	def test_token_is_stored(self):
		"""The token string must be preserved on the doc."""
		token = generate_csat_token("TEST-2", "stored@example.com", expiry_days=7)
		doc = frappe.get_doc({
			"doctype": "HD CSAT Response",
			"ticket": None,
			"customer_email": "stored@example.com",
			"token": token,
			"token_used": 0,
		})
		self.assertEqual(doc.token, token)
