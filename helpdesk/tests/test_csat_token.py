# Copyright (c) 2026, Frappe Technologies Pvt. Ltd. and contributors
# For license information, please see license.txt
"""
Unit tests for CSAT HMAC token utilities.
Story 3.7 / AC #7, #8, #12 — token generation, validation, expiry, tamper detection.
"""
import time

import frappe
from frappe.tests.utils import FrappeTestCase

from helpdesk.utils import generate_csat_token, validate_csat_token


class TestCsatToken(FrappeTestCase):
	"""Tests for generate_csat_token / validate_csat_token."""

	TICKET_ID = "1"
	EMAIL = "customer@example.com"

	# ------------------------------------------------------------------
	# generate_csat_token
	# ------------------------------------------------------------------

	def test_token_has_two_parts(self):
		"""Token must be <payload_b64>.<signature>."""
		token = generate_csat_token(self.TICKET_ID, self.EMAIL)
		parts = token.split(".")
		self.assertGreaterEqual(len(parts), 2, "Token must contain at least one '.'")

	def test_different_tickets_produce_different_tokens(self):
		t1 = generate_csat_token("1", self.EMAIL)
		t2 = generate_csat_token("2", self.EMAIL)
		self.assertNotEqual(t1, t2)

	def test_different_emails_produce_different_tokens(self):
		t1 = generate_csat_token(self.TICKET_ID, "a@a.com")
		t2 = generate_csat_token(self.TICKET_ID, "b@b.com")
		self.assertNotEqual(t1, t2)

	# ------------------------------------------------------------------
	# validate_csat_token — happy path
	# ------------------------------------------------------------------

	def test_valid_token_passes(self):
		token = generate_csat_token(self.TICKET_ID, self.EMAIL, expiry_days=7)
		result = validate_csat_token(token, self.TICKET_ID, self.EMAIL)
		self.assertTrue(result["valid"])
		self.assertFalse(result["expired"])
		self.assertIsNotNone(result["payload"])

	def test_payload_contains_expected_fields(self):
		token = generate_csat_token(self.TICKET_ID, self.EMAIL)
		result = validate_csat_token(token, self.TICKET_ID, self.EMAIL)
		self.assertEqual(result["payload"]["ticket_id"], self.TICKET_ID)
		self.assertEqual(result["payload"]["customer_email"], self.EMAIL)

	# ------------------------------------------------------------------
	# validate_csat_token — wrong ticket / email
	# ------------------------------------------------------------------

	def test_wrong_ticket_id_rejected(self):
		token = generate_csat_token(self.TICKET_ID, self.EMAIL)
		result = validate_csat_token(token, "99999", self.EMAIL)
		self.assertFalse(result["valid"])
		self.assertFalse(result["expired"])

	def test_wrong_email_rejected(self):
		token = generate_csat_token(self.TICKET_ID, self.EMAIL)
		result = validate_csat_token(token, self.TICKET_ID, "attacker@evil.com")
		self.assertFalse(result["valid"])

	# ------------------------------------------------------------------
	# validate_csat_token — tamper detection
	# ------------------------------------------------------------------

	def test_tampered_signature_rejected(self):
		token = generate_csat_token(self.TICKET_ID, self.EMAIL)
		payload_b64, _sig = token.rsplit(".", 1)
		tampered = f"{payload_b64}.deadbeef1234deadbeef1234deadbeef1234deadbeef1234deadbeef1234dead"
		result = validate_csat_token(tampered, self.TICKET_ID, self.EMAIL)
		self.assertFalse(result["valid"])

	def test_tampered_payload_rejected(self):
		import base64
		token = generate_csat_token(self.TICKET_ID, self.EMAIL)
		_payload_b64, sig = token.rsplit(".", 1)
		evil_payload = "99:attacker@evil.com:99999999999"
		evil_b64 = base64.urlsafe_b64encode(evil_payload.encode()).decode().rstrip("=")
		tampered = f"{evil_b64}.{sig}"
		result = validate_csat_token(tampered, "99", "attacker@evil.com")
		self.assertFalse(result["valid"])

	def test_garbage_token_rejected(self):
		result = validate_csat_token("notavalidtoken", self.TICKET_ID, self.EMAIL)
		self.assertFalse(result["valid"])
		self.assertFalse(result["expired"])

	def test_empty_token_rejected(self):
		result = validate_csat_token("", self.TICKET_ID, self.EMAIL)
		self.assertFalse(result["valid"])

	# ------------------------------------------------------------------
	# validate_csat_token — expiry
	# ------------------------------------------------------------------

	def test_expired_token_detected(self):
		"""Token with expiry in the past should be marked expired."""
		import base64
		import hashlib
		import hmac as hmac_mod

		# Build a token that expired 1 second ago
		expiry_ts = int(time.time()) - 1
		payload = f"{self.TICKET_ID}:{self.EMAIL}:{expiry_ts}"
		payload_b64 = base64.urlsafe_b64encode(payload.encode()).decode().rstrip("=")
		from frappe.utils.password import get_encryption_key
		secret = (frappe.local.conf.get("secret") or get_encryption_key()).encode()
		sig = hmac_mod.new(secret, payload.encode(), hashlib.sha256).hexdigest()
		expired_token = f"{payload_b64}.{sig}"

		result = validate_csat_token(expired_token, self.TICKET_ID, self.EMAIL)
		self.assertFalse(result["valid"])
		self.assertTrue(result["expired"])

	def test_expiry_days_zero_expires_immediately(self):
		"""A token generated with expiry_days=0 should already be expired."""
		# expiry_ts = now + 0 seconds = now; by the time validate runs, it's expired
		token = generate_csat_token(self.TICKET_ID, self.EMAIL, expiry_days=0)
		# Add a tiny sleep to ensure we're past the expiry
		time.sleep(1)
		result = validate_csat_token(token, self.TICKET_ID, self.EMAIL)
		# Either expired or invalid (expired_ts == now may round to 0 difference)
		self.assertFalse(result["valid"])
