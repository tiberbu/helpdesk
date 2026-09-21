"""Microsoft Entra ID single sign-on for Frappe.

Configures the built-in ``Office 365`` Social Login Key against tenant-specific
v2.0 endpoints and replaces the core callback with one that validates the ID
token (signature, issuer, audience, tenant), enforces a domain allowlist, pins
each Frappe user to one Entra subject, and blocks open redirects.
"""

import base64
import json
import re
import secrets
from urllib.parse import urlencode, urlparse

import frappe
import jwt
from frappe import _
from frappe.utils.oauth import get_oauth2_flow, get_redirect_uri, login_oauth_user

PROVIDER = "office_365"  # frappe.scrub("Office 365"); fixed by core callback name
AUTHORITY = "https://login.microsoftonline.com"
CORE_CALLBACK = "/api/method/frappe.integrations.oauth2_logins.login_via_office365"

_TENANT_RE = re.compile(r"login\.microsoftonline\.com/([0-9a-fA-F-]{36}|common|organizations)/")

_jwks_clients: dict = {}


class SSOError(Exception):
	def __init__(self, reason: str, http_status: int = 401):
		super().__init__(reason)
		self.reason = reason
		self.http_status = http_status


def _conf() -> dict:
	"""Read live SSO config from the Office 365 Social Login Key + HD Settings.

	No site_config.json required: tenant_id is parsed from the key's own
	Authorize URL, client_id/client_secret are native fields on that same
	doctype, and the email-domain allowlist is HD Settings.sso_allowed_email_domains.
	"""
	if not frappe.db.exists("Social Login Key", PROVIDER):
		raise SSOError("not configured", 503)

	key = frappe.get_cached_doc("Social Login Key", PROVIDER)
	if not key.get("client_id") or not key.get("authorize_url"):
		raise SSOError("not configured", 503)

	match = _TENANT_RE.search(key.authorize_url or "")
	tenant_id = match.group(1) if match else None
	if not tenant_id or tenant_id in ("common", "organizations"):
		raise SSOError("not configured", 503)

	client_secret = key.get_password("client_secret", raise_exception=False)
	if not client_secret:
		raise SSOError("not configured", 503)

	domains_raw = frappe.db.get_single_value("HD Settings", "sso_allowed_email_domains") or ""
	allowed_email_domains = [d.strip().lower() for d in domains_raw.split(",") if d.strip()]

	return {
		"tenant_id": tenant_id,
		"client_id": key.client_id,
		"client_secret": client_secret,
		"allowed_email_domains": allowed_email_domains,
		"allow_guests": 0,
	}


def build_authorize_url(redirect_to: str) -> str:
	"""Build the Microsoft authorize URL ourselves, with an explicit state
	format sanitize_state() is guaranteed to understand. Avoids depending on
	however core Frappe's get_oauth2_authorize_url() happens to format
	``state`` on a given Frappe version -- that varied between environments
	and broke UAT while production (a different Frappe build) worked.
	"""
	conf = _conf()
	state_payload = {"token": secrets.token_hex(16), "redirect_to": redirect_to}
	state = base64.b64encode(json.dumps(state_payload).encode("utf-8")).decode("utf-8")
	params = {
		"client_id": conf["client_id"],
		"response_type": "code",
		"redirect_uri": get_redirect_uri(PROVIDER),
		"scope": "openid email profile",
		"state": state,
	}
	return f"{AUTHORITY}/{conf['tenant_id']}/oauth2/v2.0/authorize?{urlencode(params)}"


def configure_entra_sso():
	"""Idempotently create/update the Office 365 Social Login Key from site_config.

	Optional bootstrap helper. A Social Login Key can also be configured
	entirely through the desk UI (Social Login Key list > Office 365 >
	fill in Client ID/Secret and the tenant-specific Authorize/Token URLs),
	in which case _conf() reads everything from that record directly and
	this function is never needed.

	Run: bench --site <site> execute helpdesk.sso.entra.configure_entra_sso
	"""
	conf = frappe.conf.get("entra_sso") or {}
	if not (conf.get("tenant_id") and conf.get("client_id") and conf.get("client_secret")):
		frappe.throw(
			_(
				"Set entra_sso.tenant_id, client_id and client_secret in site_config.json, "
				"or configure the Office 365 Social Login Key directly from the desk UI"
			)
		)

	tenant_id = conf["tenant_id"]
	values = {
		"provider_name": "Office 365",
		"social_login_provider": "Office 365",
		"enable_social_login": 1,
		"custom_base_url": 0,
		"base_url": AUTHORITY,
		"authorize_url": f"{AUTHORITY}/{tenant_id}/oauth2/v2.0/authorize",
		"access_token_url": f"{AUTHORITY}/{tenant_id}/oauth2/v2.0/token",
		"redirect_url": CORE_CALLBACK,
		"api_endpoint": None,
		"api_endpoint_args": None,
		"auth_url_data": json.dumps({"response_type": "code", "scope": "openid email profile"}),
		"user_id_property": "sub",
		"sign_ups": "Deny",
		"client_id": conf["client_id"],
		"client_secret": conf["client_secret"],
	}
	if frappe.db.exists("Social Login Key", PROVIDER):
		doc = frappe.get_doc("Social Login Key", PROVIDER)
		doc.update(values)
		doc.save(ignore_permissions=True)
	else:
		frappe.get_doc({"doctype": "Social Login Key", **values}).insert(ignore_permissions=True)
	frappe.db.commit()
	return {"provider": PROVIDER, "redirect_uri": get_redirect_uri(PROVIDER)}


def _jwks_client(tenant_id: str):
	if tenant_id not in _jwks_clients:
		_jwks_clients[tenant_id] = jwt.PyJWKClient(f"{AUTHORITY}/{tenant_id}/discovery/v2.0/keys")
	return _jwks_clients[tenant_id]


def _decoder(raw):
	return json.loads(bytes(raw).decode("utf-8"))


def _exchange_code_for_id_token(code: str):
	flow = get_oauth2_flow(PROVIDER)
	try:
		session = flow.get_auth_session(
			data={
				"code": code,
				"redirect_uri": get_redirect_uri(PROVIDER),
				"grant_type": "authorization_code",
				"scope": "openid email profile",
			},
			decoder=_decoder,
		)
		return json.loads(session.access_token_response.text)["id_token"], flow.client_id
	except Exception:
		frappe.log_error(title="Entra SSO: token exchange failed", message=frappe.get_traceback())
		raise SSOError("token exchange failed")


def validate_id_token(raw_token: str, tenant_id: str, client_id: str, signing_key=None) -> dict:
	"""Verify signature, iss, aud, exp/iat and tid. ``signing_key`` is injectable for tests."""
	try:
		key = signing_key or _jwks_client(tenant_id).get_signing_key_from_jwt(raw_token).key
		claims = jwt.decode(
			raw_token,
			key,
			algorithms=["RS256"],
			audience=client_id,
			issuer=f"{AUTHORITY}/{tenant_id}/v2.0",
			leeway=60,
			options={"require": ["exp", "iat", "aud", "iss", "sub", "tid"]},
		)
	except Exception:
		raise SSOError("token validation failed")
	if claims.get("tid") != tenant_id:
		raise SSOError("token validation failed")
	return claims


def resolve_email(claims: dict, conf: dict) -> str:
	email = (claims.get("email") or claims.get("upn") or claims.get("preferred_username") or "").strip().lower()
	if not email or "@" not in email:
		raise SSOError("no email claim", 403)
	upn = (claims.get("upn") or "").lower()
	if not conf.get("allow_guests") and ("#ext#" in upn or "#ext#" in email):
		raise SSOError("domain not allowed", 403)
	allowed = {d.strip().lower() for d in conf.get("allowed_email_domains") or []}
	if email.rsplit("@", 1)[1] not in allowed:
		raise SSOError("domain not allowed", 403)
	return email


def enforce_identity_pin(email: str, subject: str):
	"""Reject if this Frappe user is already bound to a different Entra subject."""
	if not frappe.db.exists("User", email):
		return  # core applies sign_ups policy
	stored = frappe.db.get_value(
		"User Social Login", {"parent": email, "parenttype": "User", "provider": PROVIDER}, "userid"
	)
	if stored and stored != subject:
		raise SSOError("identity mismatch", 403)


def sanitize_state(state, request_host) -> dict:
	try:
		payload = json.loads(base64.b64decode(state or "").decode("utf-8"))
	except Exception:
		raise SSOError("invalid state", 400)
	if not isinstance(payload, dict) or not payload.get("token"):
		raise SSOError("invalid state", 400)

	target = payload.get("redirect_to") or ""
	parsed = urlparse(target)
	safe = None
	if target and "\\" not in target and not target.startswith("//"):
		if not parsed.scheme and not parsed.netloc and target.startswith("/"):
			safe = target
		elif parsed.scheme in ("http", "https") and request_host and parsed.netloc == request_host:
			safe = parsed.path or "/"
			if parsed.query:
				safe += "?" + parsed.query
	payload["redirect_to"] = safe
	return payload


def _fail(err: SSOError):
	frappe.log_error(title=f"Entra SSO: {err.reason}", message=frappe.get_traceback() or err.reason)
	frappe.respond_as_web_page(
		_("Sign-in failed"),
		_("We could not sign you in with Microsoft. Please try again or contact your administrator.")
		+ '<br><br><a href="/login">' + _("Back to login") + "</a>",
		http_status_code=err.http_status,
		indicator_color="red",
	)


@frappe.whitelist(allow_guest=True, methods=["GET"])
def login_via_entra(code: str = None, state: str = None, error: str = None, **kwargs):
	try:
		if error or not code:
			raise SSOError("provider error")
		conf = _conf()
		safe_state = sanitize_state(state, frappe.local.request.host)
		raw_token, client_id = _exchange_code_for_id_token(code)
		claims = validate_id_token(raw_token, conf["tenant_id"], client_id)
		email = resolve_email(claims, conf)
		enforce_identity_pin(email, claims["sub"])
	except SSOError as err:
		return _fail(err)

	data = {
		"email": email,
		"sub": claims["sub"],
		"given_name": claims.get("given_name"),
		"family_name": claims.get("family_name"),
		"name": claims.get("name"),
	}
	login_oauth_user(data, provider=PROVIDER, state=safe_state)
