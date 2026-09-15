"""Service transport and signed reporter remain independent identities."""
import base64
import hashlib
import secrets
import unittest
from datetime import datetime, timezone
from types import SimpleNamespace
from unittest.mock import patch
from urllib.parse import urlencode

import frappe
from cryptography.hazmat.primitives import serialization
from cryptography.hazmat.primitives.asymmetric.ed25519 import Ed25519PrivateKey
from werkzeug.test import EnvironBuilder
from werkzeug.wrappers import Request
from helpdesk.api import mobile_signing as signing


class TestServiceAuth(unittest.TestCase):
    def test_signature_accepts_new_reporter_without_mapping(self):
        for reporter in ("new@example.test", "Administrator"):
            with self.subTest(reporter=reporter):
                request, trusted = self.signed(reporter)
                user, _ = signing.verify_request(request, trusted, "get_bootstrap")
                self.assertEqual(user, reporter)

    def test_signature_rejects_guest_reporter(self):
        request, trusted = self.signed("Guest")
        with patch.object(signing, "_deny", side_effect=frappe.AuthenticationError), self.assertRaises(frappe.AuthenticationError):
            signing.verify_request(request, trusted, "get_bootstrap")

    def signed(self, reporter):
        key = Ed25519PrivateKey.generate()
        stamp = datetime.now(timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ")
        path = "/api/method/helpdesk.api.plugin.get_bootstrap"
        query = urlencode({"user_id": reporter, "request_id": secrets.token_hex(16)})
        canonical = "\n".join(["GET", path + "?" + query, stamp, hashlib.sha256(b"").hexdigest()])
        signature = base64.b64encode(key.sign(canonical.encode())).decode()
        request = Request(EnvironBuilder(path=path, query_string=query, method="GET", headers={"X-AC-Timestamp": stamp, "X-AC-Key-Id": "test", "X-AC-Signature": signature}).get_environ())
        public = key.public_key().public_bytes(serialization.Encoding.PEM, serialization.PublicFormat.SubjectPublicKeyInfo).decode()
        return request, {"test": {"public_key_pem": public}}

    def test_cookie_without_service_token_rejected(self):
        request = Request(EnvironBuilder(headers={"Cookie": "sid=" + secrets.token_urlsafe(16)}).get_environ())
        with patch.object(signing, "_deny", side_effect=frappe.AuthenticationError), self.assertRaises(frappe.AuthenticationError):
            signing._service_user(request)

    def test_token_must_match_native_authenticated_user(self):
        token = secrets.token_hex(16) + ":" + secrets.token_hex(20)
        request = Request(EnvironBuilder(headers={"Authorization": "token " + token}).get_environ())
        with patch.object(signing.frappe, "session", SimpleNamespace(user="service@example.test")), patch.object(signing.frappe, "db", SimpleNamespace(exists=lambda *args: False)), patch.object(signing, "_deny", side_effect=frappe.AuthenticationError), self.assertRaises(frappe.AuthenticationError):
            signing._service_user(request)

    def test_valid_service_token_preserves_service_identity(self):
        token = secrets.token_hex(16) + ":" + secrets.token_hex(20)
        request = Request(EnvironBuilder(headers={"Authorization": "token " + token}).get_environ())
        with patch.object(signing.frappe, "session", SimpleNamespace(user="service@example.test")), patch.object(signing.frappe, "db", SimpleNamespace(exists=lambda *args: True)):
            self.assertEqual(signing._service_user(request), "service@example.test")
