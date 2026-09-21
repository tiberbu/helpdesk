"""Tests for Entra ID SSO — fully offline, no real tenant or network calls.

Tokens are signed with a throwaway RSA key generated per test run; the public
key is passed directly to validate_id_token via its injectable signing_key
parameter (or patched into the JWKS client for the end-to-end flow test).
"""

import base64
import json
import time
import unittest
from threading import Thread
from types import SimpleNamespace
from unittest.mock import MagicMock, patch
from urllib.parse import parse_qs, urlparse

import frappe
import jwt
import requests
from cryptography.hazmat.primitives.asymmetric import rsa
from frappe.utils import get_test_client
from frappe.utils.password import get_decrypted_password

from helpdesk.sso import entra

TENANT_ID = "11111111-2222-3333-4444-555555555555"
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


def _state(payload):
	return base64.urlsafe_b64encode(json.dumps(payload).encode()).decode()


def _stash_social_login_key():
	"""Remove any real office_365 key for the test and return a function restoring it,
	so running the suite on a configured site never clobbers its SSO settings."""
	saved = None
	if frappe.db.exists("Social Login Key", entra.PROVIDER):
		saved = frappe.get_doc("Social Login Key", entra.PROVIDER).as_dict()
		saved["client_secret"] = get_decrypted_password(
			"Social Login Key", entra.PROVIDER, "client_secret", raise_exception=False
		)
		frappe.delete_doc("Social Login Key", entra.PROVIDER, ignore_permissions=True, force=True)
		frappe.db.commit()

	def restore():
		if frappe.db.exists("Social Login Key", entra.PROVIDER):
			frappe.delete_doc("Social Login Key", entra.PROVIDER, ignore_permissions=True, force=True)
		if saved:
			doc = frappe.get_doc(saved)
			doc.flags.ignore_validate = True
			doc.insert(ignore_permissions=True)
		frappe.clear_cache(doctype="Social Login Key")
		frappe.db.commit()

	return restore


class TestValidateIdToken(unittest.TestCase):
	def setUp(self):
		self.private_key, self.public_key = _make_keypair()

	def _validate(self, token, nonce=None):
		return entra.validate_id_token(token, TENANT_ID, CLIENT_ID, nonce=nonce, signing_key=self.public_key)

	def test_valid_token_passes(self):
		self.assertEqual(self._validate(_make_token(self.private_key))["sub"], "test-subject-id")

	def test_wrong_audience_rejected(self):
		with self.assertRaises(entra.SSOError):
			self._validate(_make_token(self.private_key, aud="someone-else"))

	def test_wrong_issuer_rejected(self):
		with self.assertRaises(entra.SSOError):
			self._validate(_make_token(self.private_key, iss="https://not-microsoft.example/v2.0"))

	def test_v1_issuer_rejected_with_reason(self):
		token = _make_token(self.private_key, iss=f"https://sts.windows.net/{TENANT_ID}/")
		with self.assertRaises(entra.SSOError) as ctx:
			self._validate(token)
		self.assertIn("issuer", ctx.exception.detail.lower())

	def test_wrong_tenant_rejected(self):
		with self.assertRaises(entra.SSOError):
			self._validate(_make_token(self.private_key, tid="a-different-tenant"))

	def test_expired_token_rejected(self):
		now = int(time.time())
		with self.assertRaises(entra.SSOError):
			self._validate(_make_token(self.private_key, exp=now - 500, iat=now - 600))

	def test_signature_from_wrong_key_rejected(self):
		other_private_key, _ = _make_keypair()
		with self.assertRaises(entra.SSOError):
			self._validate(_make_token(other_private_key))

	def test_none_algorithm_rejected(self):
		now = int(time.time())
		claims = {"iss": ISSUER, "aud": CLIENT_ID, "tid": TENANT_ID, "sub": "x", "exp": now + 3600, "iat": now}
		forged = jwt.encode(claims, key="", algorithm="none")
		with self.assertRaises(entra.SSOError):
			self._validate(forged)

	def test_nonce_must_match(self):
		token = _make_token(self.private_key, nonce="expected")
		self.assertEqual(self._validate(token, nonce="expected")["nonce"], "expected")
		with self.assertRaises(entra.SSOError):
			self._validate(token, nonce="other")
		with self.assertRaises(entra.SSOError):
			self._validate(_make_token(self.private_key), nonce="expected")


class TestResolveEmail(unittest.TestCase):
	def setUp(self):
		self.conf = {"allowed_email_domains": ["tiberbu.com", "kns.co.ke"], "allow_guests": False}

	def test_prefers_email_claim(self):
		claims = {"email": "A@tiberbu.com", "upn": "other@tiberbu.com"}
		self.assertEqual(entra.resolve_email(claims, self.conf), "a@tiberbu.com")

	def test_falls_back_to_upn(self):
		self.assertEqual(entra.resolve_email({"upn": "B@tiberbu.com"}, self.conf), "b@tiberbu.com")

	def test_falls_back_to_preferred_username(self):
		self.assertEqual(entra.resolve_email({"preferred_username": "C@kns.co.ke"}, self.conf), "c@kns.co.ke")

	def test_domain_outside_allowlist_rejected(self):
		with self.assertRaises(entra.SSOError):
			entra.resolve_email({"email": "person@notallowed.com"}, self.conf)

	def test_blank_allowlist_allows_tenant_members(self):
		conf = dict(self.conf, allowed_email_domains=[])
		self.assertEqual(entra.resolve_email({"email": "x@anything.org"}, conf), "x@anything.org")

	def test_blank_allowlist_still_rejects_guests(self):
		conf = dict(self.conf, allowed_email_domains=[])
		with self.assertRaises(entra.SSOError):
			entra.resolve_email({"preferred_username": "g_gmail.com#EXT#@tiberbu.onmicrosoft.com"}, conf)
		with self.assertRaises(entra.SSOError):
			entra.resolve_email({"email": "g@gmail.com", "acct": 1}, conf)

	def test_guest_upn_rejected_by_default(self):
		claims = {
			"email": "guest_person_gmail.com#EXT#@tiberbu.onmicrosoft.com",
			"upn": "guest_person_gmail.com#EXT#@tiberbu.onmicrosoft.com",
		}
		with self.assertRaises(entra.SSOError):
			entra.resolve_email(claims, self.conf)

	def test_guest_allowed_when_configured(self):
		conf = dict(self.conf, allow_guests=True)
		self.assertIn("@tiberbu.com", entra.resolve_email({"email": "guest#EXT#@tiberbu.com"}, conf))

	def test_no_email_claim_rejected(self):
		with self.assertRaises(entra.SSOError):
			entra.resolve_email({}, self.conf)


class TestTenantFromKey(unittest.TestCase):
	def _key(self, authorize_url, access_token_url="", custom_base_url=0, base_url=""):
		return frappe._dict(
			authorize_url=authorize_url,
			access_token_url=access_token_url,
			custom_base_url=custom_base_url,
			base_url=base_url,
		)

	def test_v2_url(self):
		key = self._key(entra.authorize_endpoint(TENANT_ID))
		self.assertEqual(entra._tenant_from_key(key), TENANT_ID)

	def test_v1_url_accepted(self):
		key = self._key(f"https://login.microsoftonline.com/{TENANT_ID.upper()}/oauth2/authorize")
		self.assertEqual(entra._tenant_from_key(key), TENANT_ID)

	def test_relative_url_with_custom_base(self):
		key = self._key(
			f"/{TENANT_ID}/oauth2/v2.0/authorize", custom_base_url=1, base_url="https://login.microsoftonline.com/"
		)
		self.assertEqual(entra._tenant_from_key(key), TENANT_ID)

	def test_core_default_common_rejected_with_guidance(self):
		key = self._key("https://login.microsoftonline.com/common/oauth2/authorize")
		with self.assertRaises(entra.SSOError) as ctx:
			entra._tenant_from_key(key)
		self.assertIn("common", ctx.exception.detail)

	def test_domain_tenant_rejected_with_guidance(self):
		key = self._key("https://login.microsoftonline.com/contoso.onmicrosoft.com/oauth2/v2.0/authorize")
		with self.assertRaises(entra.SSOError) as ctx:
			entra._tenant_from_key(key)
		self.assertIn("GUID", ctx.exception.detail)


class TestExchangeCode(unittest.TestCase):
	conf = {"tenant_id": TENANT_ID, "client_id": CLIENT_ID, "client_secret": "s3cret"}

	@patch("helpdesk.sso.entra.get_redirect_uri", return_value="https://hd.example/cb")
	@patch("helpdesk.sso.entra.requests.post")
	def test_posts_to_v2_token_endpoint(self, mock_post, _):
		mock_post.return_value = MagicMock(status_code=200, json=lambda: {"id_token": "tok"})
		self.assertEqual(entra._exchange_code_for_id_token("code", self.conf), "tok")
		url = mock_post.call_args.args[0]
		data = mock_post.call_args.kwargs["data"]
		self.assertEqual(url, entra.token_endpoint(TENANT_ID))
		self.assertEqual(data["redirect_uri"], "https://hd.example/cb")
		self.assertEqual(data["client_secret"], "s3cret")

	@patch("helpdesk.sso.entra.get_redirect_uri", return_value="https://hd.example/cb")
	@patch("helpdesk.sso.entra.requests.post")
	def test_aadsts_error_surfaced_without_secret(self, mock_post, _):
		body = {"error": "invalid_client", "error_description": "AADSTS7000215: Invalid client secret provided."}
		mock_post.return_value = MagicMock(status_code=401, json=lambda: body)
		with self.assertRaises(entra.SSOError) as ctx:
			entra._exchange_code_for_id_token("code", self.conf)
		self.assertIn("AADSTS7000215", ctx.exception.detail)
		self.assertIn("https://hd.example/cb", ctx.exception.detail)
		self.assertNotIn("s3cret", ctx.exception.detail)

	@patch("helpdesk.sso.entra.get_redirect_uri", return_value="https://hd.example/cb")
	@patch("helpdesk.sso.entra.requests.post", side_effect=requests.ConnectionError("no route"))
	def test_network_error(self, *_):
		with self.assertRaises(entra.SSOError) as ctx:
			entra._exchange_code_for_id_token("code", self.conf)
		self.assertEqual(ctx.exception.http_status, 502)


class TestEnforceIdentityPin(unittest.TestCase):
	TEST_EMAIL = "sso-pin-test@tiberbu.com"

	def setUp(self):
		if not frappe.db.exists("User", self.TEST_EMAIL):
			frappe.get_doc(
				{"doctype": "User", "email": self.TEST_EMAIL, "first_name": "SSO Pin Test", "send_welcome_email": 0}
			).insert(ignore_permissions=True)

	def tearDown(self):
		if frappe.db.exists("User", self.TEST_EMAIL):
			frappe.delete_doc("User", self.TEST_EMAIL, ignore_permissions=True, force=True)
		frappe.db.commit()

	def _bind(self, subject):
		frappe.get_doc(
			{
				"doctype": "User Social Login",
				"parent": self.TEST_EMAIL,
				"parenttype": "User",
				"parentfield": "social_logins",
				"provider": entra.PROVIDER,
				"userid": subject,
			}
		).insert(ignore_permissions=True)

	def test_no_existing_user_passes(self):
		entra.enforce_identity_pin("nonexistent-user@tiberbu.com", "any-subject")

	def test_no_existing_social_login_row_passes(self):
		entra.enforce_identity_pin(self.TEST_EMAIL, "subject-a")

	def test_matching_subject_passes(self):
		self._bind("subject-a")
		entra.enforce_identity_pin(self.TEST_EMAIL, "subject-a")

	def test_mismatched_subject_rejected(self):
		self._bind("subject-a")
		with self.assertRaises(entra.SSOError):
			entra.enforce_identity_pin(self.TEST_EMAIL, "subject-b-different")


class TestSanitizeState(unittest.TestCase):
	HOST = "support.tiberbu.app"

	def _sanitize(self, redirect_to=None):
		payload = {"token": "abc123"}
		if redirect_to is not None:
			payload["redirect_to"] = redirect_to
		return entra.sanitize_state(_state(payload), self.HOST)["redirect_to"]

	def test_relative_path_kept(self):
		self.assertEqual(self._sanitize("/app/tickets"), "/app/tickets")

	def test_same_host_absolute_kept_as_path(self):
		self.assertEqual(self._sanitize(f"https://{self.HOST}/app/home"), "/app/home")

	def test_other_host_rejected(self):
		self.assertIsNone(self._sanitize("https://evil.example/steal"))

	def test_protocol_relative_rejected(self):
		self.assertIsNone(self._sanitize("//evil.example/steal"))

	def test_backslash_rejected(self):
		self.assertIsNone(self._sanitize("/\\evil.example"))

	def test_javascript_scheme_rejected(self):
		self.assertIsNone(self._sanitize("javascript:alert(1)"))

	def test_standard_base64_accepted(self):
		payload = base64.b64encode(json.dumps({"token": "t", "redirect_to": "/a?x=>>>"}).encode()).decode()
		self.assertEqual(entra.sanitize_state(payload, self.HOST)["token"], "t")

	def test_missing_token_rejected(self):
		with self.assertRaises(entra.SSOError):
			entra.sanitize_state(_state({"no_token_here": True}), self.HOST)

	def test_bad_base64_rejected(self):
		with self.assertRaises(entra.SSOError):
			entra.sanitize_state("not-valid-base64!!!", self.HOST)


class TestConf(unittest.TestCase):
	def test_missing_key_is_not_configured(self):
		with (
			patch("helpdesk.sso.entra.frappe.db.exists", return_value=False),
			self.assertRaises(entra.SSOError) as ctx,
		):
			entra._conf()
		self.assertEqual(ctx.exception.http_status, 503)

	def test_allowlist_parsing(self):
		with patch("helpdesk.sso.entra.frappe.db.get_single_value", return_value=" Tiberbu.com,\n@kns.co.ke ,, "):
			self.assertEqual(entra._allowed_email_domains(), ["tiberbu.com", "kns.co.ke"])

	def test_allowlist_is_standard_field(self):
		self.assertTrue(frappe.get_meta("HD Settings").has_field("sso_allowed_email_domains"))


class TestLoginViaEntra(unittest.TestCase):
	@patch("helpdesk.sso.entra._fail")
	def test_provider_error_fails_with_description(self, mock_fail):
		entra.login_via_entra(code=None, state=None, error="invalid_request", error_description="AADSTS50011: x")
		err = mock_fail.call_args.args[0]
		self.assertIn("AADSTS50011", err.detail)

	@patch("helpdesk.sso.entra._fail")
	@patch("helpdesk.sso.entra._conf", side_effect=ValueError("boom"))
	def test_unexpected_exception_is_contained(self, _, mock_fail):
		entra.login_via_entra(code="c", state="s")
		self.assertEqual(mock_fail.call_args.args[0].http_status, 500)


class TestConfigureEntraSso(unittest.TestCase):
	def setUp(self):
		self.restore_key = _stash_social_login_key()
		self.site_conf = {"tenant_id": TENANT_ID, "client_id": CLIENT_ID, "client_secret": "first-secret"}

	def tearDown(self):
		self.restore_key()

	def test_idempotent_and_rotates_secret(self):
		with patch.dict(frappe.local.conf, {"entra_sso": self.site_conf}):
			entra.configure_entra_sso()
			self.site_conf["client_secret"] = "rotated-secret"
			entra.configure_entra_sso()

		self.assertEqual(frappe.db.count("Social Login Key", {"name": entra.PROVIDER}), 1)
		doc = frappe.get_doc("Social Login Key", entra.PROVIDER)
		self.assertEqual(doc.authorize_url, entra.authorize_endpoint(TENANT_ID))
		self.assertEqual(doc.access_token_url, entra.token_endpoint(TENANT_ID))
		self.assertEqual(doc.sign_ups, "Deny")
		self.assertEqual(
			get_decrypted_password("Social Login Key", entra.PROVIDER, "client_secret"), "rotated-secret"
		)


class TestEndToEndFlow(unittest.TestCase):
	"""Drives the real WSGI app: /login -> login -> (mocked Microsoft) -> callback -> session."""

	EMAIL = "sso-e2e@tiberbu.com"
	SUBJECT = "e2e-subject"

	@classmethod
	def setUpClass(cls):
		cls.private_key, cls.public_key = _make_keypair()
		cls.restore_key = _stash_social_login_key()
		frappe.get_doc(
			{
				"doctype": "Social Login Key",
				"provider_name": "Office 365",
				"social_login_provider": "Office 365",
				"enable_social_login": 1,
				"base_url": entra.AUTHORITY,
				"authorize_url": f"{entra.AUTHORITY}/{TENANT_ID}/oauth2/authorize",  # v1 shape on purpose
				"access_token_url": f"{entra.AUTHORITY}/{TENANT_ID}/oauth2/token",
				"redirect_url": entra.CORE_CALLBACK,
				"client_id": CLIENT_ID,
				"client_secret": "e2e-secret",
				"sign_ups": "Deny",
			}
		).insert(ignore_permissions=True)
		if not frappe.db.exists("User", cls.EMAIL):
			frappe.get_doc(
				{"doctype": "User", "email": cls.EMAIL, "first_name": "SSO E2E", "send_welcome_email": 0}
			).insert(ignore_permissions=True)
		cls.domains_before = frappe.db.get_single_value("HD Settings", "sso_allowed_email_domains")
		frappe.db.set_single_value("HD Settings", "sso_allowed_email_domains", "")
		frappe.db.commit()

	@classmethod
	def tearDownClass(cls):
		frappe.delete_doc("User", cls.EMAIL, ignore_permissions=True, force=True)
		cls.restore_key()
		frappe.db.set_single_value("HD Settings", "sso_allowed_email_domains", cls.domains_before)
		frappe.db.commit()

	def _request(self, client, path):
		result = {}
		site = frappe.local.site

		def run():
			with patch("frappe.app.get_site_name", return_value=site):
				result["r"] = client.get(path)

		t = Thread(target=run)
		t.start()
		t.join()
		return result["r"]

	def _start(self, client):
		login_page = self._request(client, "/login?redirect-to=/helpdesk/tickets")
		self.assertEqual(login_page.status_code, 200)
		html = login_page.get_data(as_text=True)
		self.assertIn("Sign in with Microsoft", html)
		self.assertIn("/api/method/helpdesk.sso.entra.login?redirect_to=%2Fhelpdesk%2Ftickets", html)

		start = self._request(client, "/api/method/helpdesk.sso.entra.login?redirect_to=%2Fhelpdesk%2Ftickets")
		self.assertEqual(start.status_code, 302)
		location = urlparse(start.headers["Location"])
		self.assertEqual(f"{location.scheme}://{location.netloc}{location.path}", entra.authorize_endpoint(TENANT_ID))
		params = {k: v[0] for k, v in parse_qs(location.query).items()}
		self.assertIn(entra.STATE_COOKIE, " ".join(start.headers.getlist("Set-Cookie")))
		return params

	def _token_response(self, nonce, **claims):
		token = _make_token(
			self.private_key, email=self.EMAIL, sub=self.SUBJECT, nonce=nonce, given_name="SSO", **claims
		)
		return MagicMock(status_code=200, json=lambda: {"id_token": token, "access_token": "x"})

	def _callback(self, client, params, state=None):
		signing_key = SimpleNamespace(key=self.public_key)
		jwks = MagicMock(get_signing_key_from_jwt=MagicMock(return_value=signing_key))
		with (
			patch("helpdesk.sso.entra.requests.post", return_value=self._token_response(params["nonce"])) as post,
			patch("helpdesk.sso.entra._jwks_client", return_value=jwks),
		):
			response = self._request(
				client,
				f"{entra.CORE_CALLBACK}?code=auth-code&state={state or params['state']}",
			)
		return response, post

	def test_full_login(self):
		client = get_test_client()
		params = self._start(client)
		self.assertEqual(params["scope"], entra.SCOPE)
		self.assertEqual(params["client_id"], CLIENT_ID)

		response, post = self._callback(client, params)
		self.assertEqual(response.status_code, 302, response.get_data(as_text=True)[:2000])
		self.assertTrue(response.headers["Location"].endswith("/helpdesk/tickets"))
		self.assertEqual(post.call_args.args[0], entra.token_endpoint(TENANT_ID))
		self.assertEqual(post.call_args.kwargs["data"]["redirect_uri"], params["redirect_uri"])

		frappe.db.rollback()
		userid = frappe.db.get_value(
			"User Social Login", {"parent": self.EMAIL, "provider": entra.PROVIDER}, "userid"
		)
		self.assertEqual(userid, self.SUBJECT)
		self.assertIn(f"user_id={self.EMAIL.replace('@', '%40')}", " ".join(response.headers.getlist("Set-Cookie")))

	def test_start_bounces_to_callback_host_once(self):
		client = get_test_client()
		other = "https://helpdesk.example.org" + entra.CORE_CALLBACK
		with patch("helpdesk.sso.entra.get_redirect_uri", return_value=other):
			first = self._request(client, "/api/method/helpdesk.sso.entra.login?redirect_to=%2Fhelpdesk")
			second = self._request(client, "/api/method/helpdesk.sso.entra.login?redirect_to=%2Fhelpdesk&hop=1")
		self.assertEqual(first.status_code, 302)
		self.assertTrue(first.headers["Location"].startswith("https://helpdesk.example.org/api/method/helpdesk.sso.entra.login?"))
		self.assertIn("hop=1", first.headers["Location"])
		self.assertNotIn(entra.STATE_COOKIE, " ".join(first.headers.getlist("Set-Cookie")))
		self.assertTrue(second.headers["Location"].startswith(entra.authorize_endpoint(TENANT_ID)))

	def test_callback_without_state_cookie_rejected(self):
		params = self._start(get_test_client())
		response, post = self._callback(get_test_client(), params)  # different browser
		self.assertEqual(response.status_code, 400)
		post.assert_not_called()

	def test_forged_state_rejected(self):
		client = get_test_client()
		params = self._start(client)
		forged = _state({"token": "attacker-token", "redirect_to": "/helpdesk"})
		response, post = self._callback(client, params, state=forged)
		self.assertEqual(response.status_code, 400)
		post.assert_not_called()


if __name__ == "__main__":
	unittest.main()
