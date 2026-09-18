"""Unit tests for Entra ID SSO — fully offline, no real tenant or network calls.

Tokens are signed with a throwaway RSA key generated per test run; the public
key is passed directly to validate_id_token via its injectable signing_key
parameter, bypassing the real JWKS fetch entirely.
"""

import base64
import json
import time
import unittest
from unittest.mock import MagicMock, patch

import jwt
from cryptography.hazmat.primitives.asymmetric import rsa

from helpdesk.sso import entra

TENANT_ID = "test-tenant-id"
CLIENT_ID = "test-client-id"
ISSUER = f"{entra.AUTHORITY}/{TENANT_ID}/v2.0"


def _make_keypair():
    private_key = rsa.generate_private_key(public_exponent=65537, key_size=2048)
    return private_key, private_key.public_key()


def _make_token(private_key, **overrides):
    now = int(time.time())
    claims = {
        "iss": ISSUER,
        "aud": CLIENT_ID,
        "tid": TENANT_ID,
        "sub": "test-subject-id",
        "exp": now + 3600,
        "iat": now,
        "email": "person@tiberbu.com",
    }
    claims.update(overrides)
    return jwt.encode(claims, private_key, algorithm="RS256")


class TestValidateIdToken(unittest.TestCase):
    def setUp(self):
        self.private_key, self.public_key = _make_keypair()

    def test_valid_token_passes(self):
        token = _make_token(self.private_key)
        claims = entra.validate_id_token(token, TENANT_ID, CLIENT_ID, signing_key=self.public_key)
        self.assertEqual(claims["sub"], "test-subject-id")

    def test_wrong_audience_rejected(self):
        token = _make_token(self.private_key, aud="someone-else")
        with self.assertRaises(entra.SSOError):
            entra.validate_id_token(token, TENANT_ID, CLIENT_ID, signing_key=self.public_key)

    def test_wrong_issuer_rejected(self):
        token = _make_token(self.private_key, iss="https://not-microsoft.example/v2.0")
        with self.assertRaises(entra.SSOError):
            entra.validate_id_token(token, TENANT_ID, CLIENT_ID, signing_key=self.public_key)

    def test_wrong_tenant_rejected(self):
        token = _make_token(self.private_key, tid="a-different-tenant")
        with self.assertRaises(entra.SSOError):
            entra.validate_id_token(token, TENANT_ID, CLIENT_ID, signing_key=self.public_key)

    def test_expired_token_rejected(self):
        now = int(time.time())
        token = _make_token(self.private_key, exp=now - 100, iat=now - 200)
        with self.assertRaises(entra.SSOError):
            entra.validate_id_token(token, TENANT_ID, CLIENT_ID, signing_key=self.public_key)

    def test_signature_from_wrong_key_rejected(self):
        other_private_key, _ = _make_keypair()
        token = _make_token(other_private_key)  # signed with a DIFFERENT key
        with self.assertRaises(entra.SSOError):
            entra.validate_id_token(token, TENANT_ID, CLIENT_ID, signing_key=self.public_key)

    def test_none_algorithm_rejected(self):
        now = int(time.time())
        claims = {"iss": ISSUER, "aud": CLIENT_ID, "tid": TENANT_ID, "sub": "x", "exp": now + 3600, "iat": now}
        forged = jwt.encode(claims, key="", algorithm="none")
        with self.assertRaises(entra.SSOError):
            entra.validate_id_token(forged, TENANT_ID, CLIENT_ID, signing_key=self.public_key)


class TestResolveEmail(unittest.TestCase):
    def setUp(self):
        self.conf = {"allowed_email_domains": ["tiberbu.com", "kns.co.ke"], "allow_guests": False}

    def test_prefers_email_claim(self):
        claims = {"email": "A@tiberbu.com", "upn": "other@tiberbu.com"}
        self.assertEqual(entra.resolve_email(claims, self.conf), "a@tiberbu.com")

    def test_falls_back_to_upn(self):
        claims = {"upn": "B@tiberbu.com"}
        self.assertEqual(entra.resolve_email(claims, self.conf), "b@tiberbu.com")

    def test_falls_back_to_preferred_username(self):
        claims = {"preferred_username": "C@kns.co.ke"}
        self.assertEqual(entra.resolve_email(claims, self.conf), "c@kns.co.ke")

    def test_domain_outside_allowlist_rejected(self):
        claims = {"email": "person@notallowed.com"}
        with self.assertRaises(entra.SSOError):
            entra.resolve_email(claims, self.conf)

    def test_guest_upn_rejected_by_default(self):
        claims = {"email": "guest_person_gmail.com#EXT#@tiberbu.onmicrosoft.com",
                   "upn": "guest_person_gmail.com#EXT#@tiberbu.onmicrosoft.com"}
        with self.assertRaises(entra.SSOError):
            entra.resolve_email(claims, self.conf)

    def test_guest_allowed_when_configured(self):
        conf = dict(self.conf, allow_guests=True)
        claims = {"email": "guest#EXT#@tiberbu.com"}
        # Should pass the guest check; domain is still in allowlist
        email = entra.resolve_email(claims, conf)
        self.assertIn("@tiberbu.com", email)

    def test_no_email_claim_rejected(self):
        with self.assertRaises(entra.SSOError):
            entra.resolve_email({}, self.conf)


class TestEnforceIdentityPin(unittest.TestCase):
    TEST_EMAIL = "sso-pin-test@tiberbu.com"

    def setUp(self):
        import frappe
        self.frappe = frappe
        if not frappe.db.exists("User", self.TEST_EMAIL):
            frappe.get_doc({
                "doctype": "User",
                "email": self.TEST_EMAIL,
                "first_name": "SSO Pin Test",
                "send_welcome_email": 0,
            }).insert(ignore_permissions=True)

    def tearDown(self):
        if self.frappe.db.exists("User", self.TEST_EMAIL):
            self.frappe.delete_doc("User", self.TEST_EMAIL, ignore_permissions=True, force=True)
        self.frappe.db.commit()

    def test_no_existing_user_passes(self):
        entra.enforce_identity_pin("nonexistent-user@tiberbu.com", "any-subject")

    def test_no_existing_social_login_row_passes(self):
        entra.enforce_identity_pin(self.TEST_EMAIL, "subject-a")

    def test_matching_subject_passes(self):
        self.frappe.get_doc({
            "doctype": "User Social Login",
            "parent": self.TEST_EMAIL,
            "parenttype": "User",
            "parentfield": "social_logins",
            "provider": entra.PROVIDER,
            "userid": "subject-a",
        }).insert(ignore_permissions=True)
        entra.enforce_identity_pin(self.TEST_EMAIL, "subject-a")

    def test_mismatched_subject_rejected(self):
        self.frappe.get_doc({
            "doctype": "User Social Login",
            "parent": self.TEST_EMAIL,
            "parenttype": "User",
            "parentfield": "social_logins",
            "provider": entra.PROVIDER,
            "userid": "subject-a",
        }).insert(ignore_permissions=True)
        with self.assertRaises(entra.SSOError):
            entra.enforce_identity_pin(self.TEST_EMAIL, "subject-b-different")


class TestSanitizeState(unittest.TestCase):
    HOST = "support.tiberbu.app"

    def _state(self, redirect_to=None):
        payload = {"token": "abc123"}
        if redirect_to is not None:
            payload["redirect_to"] = redirect_to
        return base64.b64encode(json.dumps(payload).encode()).decode()

    def test_relative_path_kept(self):
        result = entra.sanitize_state(self._state("/app/tickets"), self.HOST)
        self.assertEqual(result["redirect_to"], "/app/tickets")

    def test_same_host_absolute_kept_as_path(self):
        result = entra.sanitize_state(self._state(f"https://{self.HOST}/app/home"), self.HOST)
        self.assertEqual(result["redirect_to"], "/app/home")

    def test_other_host_rejected(self):
        result = entra.sanitize_state(self._state("https://evil.example/steal"), self.HOST)
        self.assertIsNone(result["redirect_to"])

    def test_protocol_relative_rejected(self):
        result = entra.sanitize_state(self._state("//evil.example/steal"), self.HOST)
        self.assertIsNone(result["redirect_to"])

    def test_backslash_rejected(self):
        result = entra.sanitize_state(self._state("/\\evil.example"), self.HOST)
        self.assertIsNone(result["redirect_to"])

    def test_javascript_scheme_rejected(self):
        result = entra.sanitize_state(self._state("javascript:alert(1)"), self.HOST)
        self.assertIsNone(result["redirect_to"])

    def test_missing_token_rejected(self):
        payload = base64.b64encode(json.dumps({"no_token_here": True}).encode()).decode()
        with self.assertRaises(entra.SSOError):
            entra.sanitize_state(payload, self.HOST)

    def test_bad_base64_rejected(self):
        with self.assertRaises(entra.SSOError):
            entra.sanitize_state("not-valid-base64!!!", self.HOST)


class TestLoginViaEntra(unittest.TestCase):
    @patch("helpdesk.sso.entra._fail")
    def test_provider_error_fails_cleanly(self, mock_fail):
        entra.login_via_entra(code=None, state=None, error="access_denied")
        mock_fail.assert_called_once()

    @patch("helpdesk.sso.entra.login_oauth_user")
    @patch("helpdesk.sso.entra.enforce_identity_pin")
    @patch("helpdesk.sso.entra.resolve_email")
    @patch("helpdesk.sso.entra.validate_id_token")
    @patch("helpdesk.sso.entra._exchange_code_for_id_token")
    @patch("helpdesk.sso.entra.sanitize_state")
    @patch("helpdesk.sso.entra._conf")
    def test_happy_path_calls_login_oauth_user_with_sanitized_state(
        self, mock_conf, mock_sanitize, mock_exchange, mock_validate, mock_resolve, mock_pin, mock_login
    ):
        # sanitize_state itself is already thoroughly tested separately (TestSanitizeState);
        # here we only care that login_via_entra wires everything together correctly,
        # so we mock it directly rather than touching frappe.local (which is too deep/
        # pervasive an object for unittest.mock.patch to safely replace wholesale).
        mock_conf.return_value = {"tenant_id": TENANT_ID, "allowed_email_domains": ["tiberbu.com"]}
        mock_sanitize.return_value = {"token": "abc", "redirect_to": "/app"}
        mock_exchange.return_value = ("fake-raw-token", CLIENT_ID)
        mock_validate.return_value = {"sub": "subj-1", "given_name": "Test"}
        mock_resolve.return_value = "person@tiberbu.com"

        state = base64.b64encode(json.dumps({"token": "abc", "redirect_to": "/app"}).encode()).decode()

        # frappe.local.request.host is read as an argument expression before
        # sanitize_state is even called, so it must genuinely exist here —
        # mocking sanitize_state alone doesn't prevent that evaluation.
        import frappe
        from types import SimpleNamespace
        original_request = getattr(frappe.local, "request", None)
        frappe.local.request = SimpleNamespace(host="support.tiberbu.app")
        try:
            entra.login_via_entra(code="fake-code", state=state)
        finally:
            frappe.local.request = original_request

        mock_login.assert_called_once()
        _, kwargs = mock_login.call_args
        self.assertEqual(kwargs["provider"], entra.PROVIDER)
        self.assertEqual(kwargs["state"]["redirect_to"], "/app")


class TestConfigureEntraSso(unittest.TestCase):
    def setUp(self):
        import frappe
        self.frappe = frappe
        self.existed_before = frappe.db.exists("Social Login Key", entra.PROVIDER)
        self.mock_conf = {
            "tenant_id": TENANT_ID,
            "client_id": CLIENT_ID,
            "client_secret": "fake-secret-for-test",
            "allowed_email_domains": ["tiberbu.com"],
        }

    def tearDown(self):
        if not self.existed_before and self.frappe.db.exists("Social Login Key", entra.PROVIDER):
            self.frappe.delete_doc("Social Login Key", entra.PROVIDER, ignore_permissions=True, force=True)
            self.frappe.db.commit()

    @patch("helpdesk.sso.entra._conf")
    def test_idempotent_single_key_with_tenant_urls(self, mock_conf):
        mock_conf.return_value = self.mock_conf

        entra.configure_entra_sso()
        entra.configure_entra_sso()  # run twice deliberately

        count = self.frappe.db.count("Social Login Key", {"name": entra.PROVIDER})
        self.assertEqual(count, 1)

        doc = self.frappe.get_doc("Social Login Key", entra.PROVIDER)
        self.assertIn(TENANT_ID, doc.authorize_url)
        self.assertIn(TENANT_ID, doc.access_token_url)
        self.assertEqual(doc.sign_ups, "Deny")


if __name__ == "__main__":
    unittest.main()
