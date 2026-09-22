"""Microsoft Entra ID single sign-on for Frappe.

Uses the built-in ``Office 365`` Social Login Key for credentials and tenant, but
drives the OIDC flow itself against tenant-specific v2.0 endpoints: the login
button hits ``login`` (sets a state cookie, redirects to Microsoft) and the core
``login_via_office365`` callback is overridden by ``login_via_entra``, which
checks the state cookie, validates the ID token (signature, issuer, audience,
tenant, nonce), enforces a domain allowlist, pins each Frappe user to one Entra
subject, and blocks open redirects.
"""

import base64
import hmac
import json
import re
import secrets
from urllib.parse import urlencode, urlparse

import frappe
import jwt
import requests
from frappe import _
from frappe.utils import cint, get_url
from frappe.utils.oauth import login_oauth_user

PROVIDER = "office_365"  # frappe.scrub("Office 365"); fixed by core callback name
AUTHORITY = "https://login.microsoftonline.com"
CORE_CALLBACK = "/api/method/frappe.integrations.oauth2_logins.login_via_office365"
LOGIN_ENDPOINT = "/api/method/helpdesk.sso.entra.login"
SCOPE = "openid email profile"
STATE_COOKIE = "hd_entra_state"
STATE_TTL = 600

_GUID = r"[0-9a-fA-F]{8}-[0-9a-fA-F]{4}-[0-9a-fA-F]{4}-[0-9a-fA-F]{4}-[0-9a-fA-F]{12}"
_GUID_RE = re.compile(rf"^{_GUID}$")
_TENANT_SEGMENT_RE = re.compile(r"login\.microsoftonline\.com/([^/?#]+)")

_jwks_clients: dict = {}


class SSOError(Exception):
	def __init__(self, reason: str, http_status: int = 401, detail: str | None = None):
		super().__init__(reason)
		self.reason = reason
		self.http_status = http_status
		self.detail = detail


def authorize_endpoint(tenant_id: str) -> str:
	return f"{AUTHORITY}/{tenant_id}/oauth2/v2.0/authorize"


def token_endpoint(tenant_id: str) -> str:
	return f"{AUTHORITY}/{tenant_id}/oauth2/v2.0/token"


def _tenant_from_key(key) -> str:
	"""Tenant GUID from the key's Authorize/Token URL.

	Accepts both the v1 (``/<tenant>/oauth2/authorize``) and v2 URL shapes and
	relative URLs under a custom Base URL, as Desk may store any of them. Only the
	tenant is taken from the key; endpoints are always rebuilt as v2.0, since a v1
	token endpoint returns tokens with a different issuer that would fail validation.
	"""
	candidates = [key.get("authorize_url"), key.get("access_token_url")]
	if key.get("custom_base_url") and key.get("base_url"):
		base = key.base_url.rstrip("/")
		candidates += [base + "/" + (url or "").lstrip("/") for url in candidates if url]

	found = None
	for url in candidates:
		match = _TENANT_SEGMENT_RE.search(url or "")
		if match:
			found = match.group(1)
			if _GUID_RE.match(found):
				return found.lower()

	if found in ("common", "organizations", "consumers"):
		detail = (
			f"Authorize URL uses the multi-tenant '{found}' endpoint. Replace it with your "
			"Directory (tenant) ID GUID, e.g. "
			f"{authorize_endpoint('<tenant-guid>')} and {token_endpoint('<tenant-guid>')}"
		)
	elif found:
		detail = (
			f"Tenant '{found}' in the Authorize URL is not a GUID. Use the Directory "
			"(tenant) ID from the Entra app registration overview; token issuers are keyed by it."
		)
	else:
		detail = "Authorize URL does not contain a login.microsoftonline.com/<tenant-guid>/ segment."
	raise SSOError("not configured", 503, detail)


def _allowed_email_domains() -> list[str]:
	if not frappe.get_meta("HD Settings").has_field("sso_allowed_email_domains"):
		return []
	raw = frappe.db.get_single_value("HD Settings", "sso_allowed_email_domains") or ""
	return [d.strip().lower().lstrip("@") for d in raw.replace("\n", ",").split(",") if d.strip()]


def _conf() -> dict:
	"""Read live SSO config from the Office 365 Social Login Key + HD Settings.

	Credentials come only from the Social Login Key. Core's ``office_365_login``
	site_config override is deliberately ignored so the key edited in Desk is the
	single source of truth and a stale site_config entry cannot silently win.
	"""
	if not frappe.db.exists("Social Login Key", PROVIDER):
		raise SSOError("not configured", 503, "Social Login Key 'office_365' does not exist.")

	key = frappe.get_cached_doc("Social Login Key", PROVIDER)
	if not key.enable_social_login:
		raise SSOError("not configured", 503, "Social Login Key 'office_365' is disabled.")

	tenant_id = _tenant_from_key(key)

	client_id = (key.client_id or "").strip()
	client_secret = (key.get_password("client_secret", raise_exception=False) or "").strip()
	if not client_id:
		raise SSOError("not configured", 503, "Client ID is not set on Social Login Key 'office_365'.")
	if not client_secret:
		raise SSOError("not configured", 503, "Client Secret is not set on Social Login Key 'office_365'.")

	return {
		"tenant_id": tenant_id,
		"client_id": client_id,
		"client_secret": client_secret,
		"allowed_email_domains": _allowed_email_domains(),
		"allow_guests": 0,
	}


def is_configured() -> bool:
	"""For the login page: whether to show the Microsoft button.

	Misconfiguration is logged at most once an hour so a broken setup is visible
	in Error Log without flooding it on every login page view.
	"""
	try:
		_conf()
		return True
	except SSOError as err:
		cache_key = "helpdesk:entra_sso:config_error_logged"
		if not frappe.cache.get_value(cache_key):
			frappe.cache.set_value(cache_key, 1, expires_in_sec=3600)
			frappe.log_error(title="Entra SSO: not configured", message=err.detail or err.reason)
		return False


def get_redirect_uri() -> str:
	"""Absolute callback URL from the key's Redirect URL (core default if blank).

	Unlike core's helper, never reads ``office_365_login.redirect_uri`` from site_config.
	"""
	path = frappe.db.get_value("Social Login Key", PROVIDER, "redirect_url") or CORE_CALLBACK
	return path if path.startswith(("http://", "https://")) else get_url(path)


def _encode_state(token: str, redirect_to: str | None) -> str:
	payload = {"token": token, "redirect_to": redirect_to}
	return base64.urlsafe_b64encode(json.dumps(payload).encode("utf-8")).decode("utf-8")


def build_authorize_url(redirect_to: str | None, token: str, conf: dict | None = None) -> str:
	conf = conf or _conf()
	params = {
		"client_id": conf["client_id"],
		"response_type": "code",
		"response_mode": "query",
		"redirect_uri": get_redirect_uri(),
		"scope": SCOPE,
		"state": _encode_state(token, redirect_to),
		"nonce": token,
	}
	return f"{authorize_endpoint(conf['tenant_id'])}?{urlencode(params)}"


def login_url(redirect_to: str | None = None) -> str:
	"""Relative URL for the "Sign in with Microsoft" button."""
	return LOGIN_ENDPOINT + ("?" + urlencode({"redirect_to": redirect_to}) if redirect_to else "")


@frappe.whitelist(allow_guest=True, methods=["GET"])
def login(redirect_to: str | None = None, hop: int = 0):
	"""Start the flow: bind a one-time token to this browser, then go to Microsoft.

	The state is generated here rather than when the login page renders so each
	click gets a fresh token that matches the cookie set in the same response.
	"""
	try:
		conf = _conf()
	except SSOError as err:
		return _fail(err)

	# The state cookie must be set on the host Microsoft redirects back to, which
	# follows host_name in site_config and can differ from the host serving /login.
	# Cookies ignore scheme and port, and request.scheme is unreliable behind a TLS
	# proxy, so compare hostnames only; ``hop`` stops a loop if a proxy rewrites Host.
	callback = urlparse(get_redirect_uri())
	request_hostname = (frappe.local.request.host or "").split(":")[0].lower()
	if not cint(hop) and callback.hostname and callback.hostname.lower() != request_hostname:
		frappe.local.response["type"] = "redirect"
		frappe.local.response["location"] = (
			f"{callback.scheme}://{callback.netloc}{LOGIN_ENDPOINT}?"
			+ urlencode({"redirect_to": redirect_to or "", "hop": 1})
		)
		return

	token = secrets.token_urlsafe(32)
	frappe.local.cookie_manager.set_cookie(
		STATE_COOKIE, token, max_age=STATE_TTL, httponly=True, samesite="Lax"
	)
	frappe.local.response["type"] = "redirect"
	frappe.local.response["location"] = build_authorize_url(_safe_redirect(redirect_to), token, conf)


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

	tenant_id = conf["tenant_id"].strip()
	if not _GUID_RE.match(tenant_id):
		frappe.throw(_("entra_sso.tenant_id must be the Directory (tenant) ID GUID"))

	values = {
		"provider_name": "Office 365",
		"social_login_provider": "Office 365",
		"enable_social_login": 1,
		"custom_base_url": 0,
		"base_url": AUTHORITY,
		"authorize_url": authorize_endpoint(tenant_id),
		"access_token_url": token_endpoint(tenant_id),
		"redirect_url": CORE_CALLBACK,
		"api_endpoint": None,
		"api_endpoint_args": None,
		"auth_url_data": json.dumps({"response_type": "code", "scope": SCOPE}),
		"user_id_property": "sub",
		"sign_ups": "Deny",
		"client_id": conf["client_id"].strip(),
		"client_secret": conf["client_secret"].strip(),
	}
	if frappe.db.exists("Social Login Key", PROVIDER):
		# Save through the document, not db.set_value: client_secret is a Password
		# field and set_value would bypass encryption, leaving the old secret in
		# __Auth. provider_name/social_login_provider are set_only_once in core.
		doc = frappe.get_doc("Social Login Key", PROVIDER)
		for fieldname in ("provider_name", "social_login_provider"):
			values.pop(fieldname)
		doc.update(values)
		doc.save(ignore_permissions=True)
	else:
		frappe.get_doc({"doctype": "Social Login Key", **values}).insert(ignore_permissions=True)
	frappe.db.commit()
	return {"provider": PROVIDER, "redirect_uri": get_redirect_uri()}


def _jwks_client(tenant_id: str):
	if tenant_id not in _jwks_clients:
		_jwks_clients[tenant_id] = jwt.PyJWKClient(
			f"{AUTHORITY}/{tenant_id}/discovery/v2.0/keys", cache_keys=True, timeout=15
		)
	return _jwks_clients[tenant_id]


def _exchange_code_for_id_token(code: str, conf: dict) -> str:
	redirect_uri = get_redirect_uri()
	try:
		response = requests.post(
			token_endpoint(conf["tenant_id"]),
			data={
				"client_id": conf["client_id"],
				"client_secret": conf["client_secret"],
				"code": code,
				"redirect_uri": redirect_uri,
				"grant_type": "authorization_code",
				"scope": SCOPE,
			},
			timeout=15,
		)
	except requests.RequestException as e:
		raise SSOError("token exchange failed", 502, f"Could not reach {AUTHORITY}: {e}") from e

	try:
		body = response.json()
	except ValueError:
		body = {}

	if response.status_code != 200 or not body.get("id_token"):
		# error/error_description carry the AADSTS code (e.g. AADSTS7000215 for a
		# secret ID pasted instead of the secret value); never log the tokens.
		raise SSOError(
			"token exchange failed",
			401,
			f"HTTP {response.status_code} from token endpoint. "
			f"error={body.get('error')!r} description={body.get('error_description')!r} "
			f"redirect_uri={redirect_uri!r} client_id={conf['client_id']!r}",
		)
	return body["id_token"]


def validate_id_token(
	raw_token: str, tenant_id: str, client_id: str, nonce: str | None = None, signing_key=None
) -> dict:
	"""Verify signature, iss, aud, exp/iat, tid and nonce. ``signing_key`` is injectable for tests."""
	try:
		key = signing_key or _jwks_client(tenant_id).get_signing_key_from_jwt(raw_token).key
		claims = jwt.decode(
			raw_token,
			key,
			algorithms=["RS256"],
			audience=client_id,
			issuer=f"{AUTHORITY}/{tenant_id}/v2.0",
			leeway=120,
			options={"require": ["exp", "iat", "aud", "iss", "sub", "tid"]},
		)
	except Exception as e:
		raise SSOError("token validation failed", 401, f"{type(e).__name__}: {e}") from e
	if (claims.get("tid") or "").lower() != tenant_id.lower():
		raise SSOError("token validation failed", 401, f"tid {claims.get('tid')!r} != {tenant_id!r}")
	if nonce is not None and not hmac.compare_digest(str(claims.get("nonce") or ""), nonce):
		raise SSOError("token validation failed", 401, "nonce mismatch")
	return claims


def resolve_email(claims: dict, conf: dict) -> str:
	"""Pick the user's email; a blank allowlist admits any member of the tenant.

	The tenant is already pinned by ``validate_id_token``, and guests (the only way
	outside identities appear in a tenant) are rejected here.
	"""
	email = (claims.get("email") or claims.get("upn") or claims.get("preferred_username") or "").strip().lower()
	if not email or "@" not in email:
		raise SSOError("no email claim", 403, f"claims present: {sorted(claims)}")
	upn = (claims.get("upn") or "").lower()
	preferred = (claims.get("preferred_username") or "").lower()
	is_guest = "#ext#" in upn or "#ext#" in email or "#ext#" in preferred or claims.get("acct") == 1
	if not conf.get("allow_guests") and is_guest:
		raise SSOError("domain not allowed", 403, f"guest account {email}")
	allowed = {d.strip().lower() for d in conf.get("allowed_email_domains") or [] if d.strip()}
	if allowed and email.rsplit("@", 1)[1] not in allowed:
		raise SSOError("domain not allowed", 403, f"{email} not in {sorted(allowed)}")
	return email


def enforce_identity_pin(email: str, subject: str):
	"""Reject if this Frappe user is already bound to a different Entra subject."""
	if not frappe.db.exists("User", email):
		return  # core applies sign_ups policy
	stored = frappe.db.get_value(
		"User Social Login", {"parent": email, "parenttype": "User", "provider": PROVIDER}, "userid"
	)
	if stored and stored != subject:
		raise SSOError("identity mismatch", 403, f"{email} is bound to a different Entra subject")


def _safe_redirect(target: str | None, request_host: str | None = None) -> str | None:
	target = target or ""
	if not target or "\\" in target or target.startswith("//"):
		return None
	parsed = urlparse(target)
	if not parsed.scheme and not parsed.netloc and target.startswith("/"):
		return target
	if request_host is None and getattr(frappe.local, "request", None):
		request_host = frappe.local.request.host
	if parsed.scheme in ("http", "https") and request_host and parsed.netloc == request_host:
		return (parsed.path or "/") + ("?" + parsed.query if parsed.query else "")
	return None


def sanitize_state(state, request_host) -> dict:
	try:
		padded = (state or "") + "=" * (-len(state or "") % 4)
		payload = json.loads(base64.urlsafe_b64decode(padded.replace("+", "-").replace("/", "_")))
	except Exception as e:
		raise SSOError("invalid state", 400) from e
	if not isinstance(payload, dict) or not payload.get("token"):
		raise SSOError("invalid state", 400)
	payload["redirect_to"] = _safe_redirect(payload.get("redirect_to"), request_host or "")
	return payload


def _check_state_cookie(token: str):
	cookie = frappe.request.cookies.get(STATE_COOKIE) if getattr(frappe, "request", None) else None
	frappe.local.cookie_manager.delete_cookie(STATE_COOKIE)
	if not cookie:
		raise SSOError(
			"invalid state",
			400,
			"State cookie missing: sign-in was not started from this browser, took longer than "
			f"{STATE_TTL}s, or the redirect URI host differs from the host the login page was served on.",
		)
	if not hmac.compare_digest(cookie, token):
		raise SSOError("invalid state", 400, "State does not match the cookie set for this browser.")


def _core_login_state(redirect_to: str | None):
	"""State in the form this Frappe build's ``login_oauth_user`` accepts.

	Our own state was already verified against the browser cookie; this only
	satisfies core's check. Frappe v15 builds from mid-2026 (e.g. 15.121) take an
	opaque single-use token registered via ``create_oauth_state`` and reject
	anything else with "Your login attempt is invalid or has expired" (417);
	older builds take a dict with a truthy ``token`` and read ``redirect_to`` from it.
	"""
	try:
		from frappe.utils.oauth import create_oauth_state
	except ImportError:
		return {"token": secrets.token_urlsafe(16), "redirect_to": redirect_to}
	return create_oauth_state(redirect_to)


def _fail(err: SSOError):
	frappe.log_error(
		title=f"Entra SSO: {err.reason}",
		message="\n\n".join(filter(None, [err.detail, frappe.get_traceback()])) or err.reason,
	)
	frappe.respond_as_web_page(
		_("Sign-in failed"),
		_("We could not sign you in with Microsoft ({0}). Please try again or contact your administrator.").format(
			_(err.reason)
		)
		+ '<br><br><a href="/login">'
		+ _("Back to login")
		+ "</a>",
		http_status_code=err.http_status,
		indicator_color="red",
	)


@frappe.whitelist(allow_guest=True, methods=["GET"])
def login_via_entra(
	code: str | None = None,
	state: str | None = None,
	error: str | None = None,
	error_description: str | None = None,
	**kwargs,
):
	try:
		if error:
			raise SSOError("provider error", 401, f"{error}: {error_description}")
		if not code:
			raise SSOError("provider error", 400, "Callback received without an authorization code.")
		conf = _conf()
		safe_state = sanitize_state(state, frappe.local.request.host)
		_check_state_cookie(safe_state["token"])
		raw_token = _exchange_code_for_id_token(code, conf)
		claims = validate_id_token(raw_token, conf["tenant_id"], conf["client_id"], nonce=safe_state["token"])
		email = resolve_email(claims, conf)
		enforce_identity_pin(email, claims["sub"])
	except SSOError as err:
		return _fail(err)
	except Exception:
		return _fail(SSOError("internal error", 500))

	data = {
		"email": email,
		"sub": claims["sub"],
		"given_name": claims.get("given_name"),
		"family_name": claims.get("family_name"),
		"name": claims.get("name"),
	}
	login_oauth_user(data, provider=PROVIDER, state=_core_login_state(safe_state["redirect_to"]))
