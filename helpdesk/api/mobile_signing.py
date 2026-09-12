"""CareVerse Ed25519 verification for explicitly configured Helpdesk instances."""

import base64
import hashlib
import inspect
import json
import time
from datetime import datetime, timezone
from functools import wraps
from urllib.parse import parse_qs

import frappe
import requests
from cryptography.exceptions import InvalidSignature
from cryptography.hazmat.primitives import serialization
from cryptography.hazmat.primitives.asymmetric.ed25519 import Ed25519PublicKey

PUBLIC_KEY_PATH = "/api/method/careverse_hq.api.hmis_signing.get_public_key"


def _deny(message):
    frappe.throw(message, frappe.AuthenticationError)


def _unique_object(pairs):
    result = {}
    for key, value in pairs:
        if key in result:
            raise ValueError("Duplicate JSON key")
        result[key] = value
    return result


def signed_arguments(request):
    try:
        raw = request.get_data(cache=True)
        if len(raw) > 9 * 1024 * 1024:
            raise ValueError()
        if request.method == "GET":
            if raw:
                raise ValueError()
            query = parse_qs(
                request.query_string.decode("ascii"), keep_blank_values=True
            )
            if any(len(values) != 1 for values in query.values()):
                raise ValueError()
            args = {key: values[0] for key, values in query.items()}
        elif request.method == "POST" and request.is_json and not request.query_string:
            args = json.loads(raw, object_pairs_hook=_unique_object)
        else:
            raise ValueError()
        if not isinstance(args, dict):
            raise ValueError()
        for key in ("user_id", "instance_id", "request_id"):
            if not isinstance(args.get(key), str) or not args[key]:
                raise ValueError()
        if not 16 <= len(args["request_id"]) <= 128:
            raise ValueError()
        return args
    except (ValueError, TypeError, UnicodeError):
        _deny(
            "Unique signed instance_id, user_id and request_id are required. GET uses query parameters; POST uses JSON only."
        )


def _check_timestamp(request):
    stamp = request.headers.get("X-AC-Timestamp", "")
    try:
        issued = datetime.fromisoformat(stamp.replace("Z", "+00:00"))
        if (
            issued.tzinfo is None
            or abs((datetime.now(timezone.utc) - issued).total_seconds()) > 30
        ):
            raise ValueError()
    except (ValueError, TypeError):
        _deny("Signature timestamp must be within 30 seconds of server time.")
    return stamp


def _fetch_public_key(instance, key_id):
    """Fetch only the administrator-configured HTTPS origin; never a caller URL."""
    cache = frappe.cache()
    identity = hashlib.sha256(
        (instance.name + ":" + instance.base_url).encode()
    ).hexdigest()
    cache_key = "helpdesk:careverse:public-key:" + identity
    cached = cache.get_value(cache_key)
    if cached and cached.get("key_id") == key_id:
        return cached
    # Unknown IDs may trigger at most one refresh per 30 seconds per instance.
    if not cache.set(cache_key + ":refresh", "1", nx=True, ex=30):
        # Share in-flight discovery for simultaneous requests with a cold cache.
        if not cached:
            for _ in range(20):
                time.sleep(0.25)
                published = cache.get_value(cache_key, use_local_cache=False)
                if published:
                    if published.get("key_id") == key_id:
                        return published
                    break
        _deny("Signing key unavailable; retry public-key discovery after 30 seconds.")
    try:
        with requests.get(
            instance.base_url.rstrip("/") + PUBLIC_KEY_PATH,
            timeout=5,
            allow_redirects=False,
            stream=True,
        ) as response:
            if response.status_code != 200:
                raise ValueError("Public-key endpoint did not return HTTP 200")
            body = bytearray()
            for chunk in response.iter_content(4096):
                body.extend(chunk)
                if len(body) > 32768:
                    raise ValueError("Oversized public-key response")
        result = json.loads(body)["message"]
        if result.get("status") != "success":
            raise ValueError("Public-key endpoint reported failure")
        payload = result["data"]
        pem = payload["public_key_pem"]
        public_key = serialization.load_pem_public_key(pem.encode())
        if not isinstance(public_key, Ed25519PublicKey):
            raise ValueError("Expected Ed25519 key")
        if payload["key_id"] != hashlib.sha256(pem.encode()).hexdigest()[:16]:
            raise ValueError("Public key ID does not match PEM")
        cache.set_value(cache_key, payload, expires_in_sec=300)
    except (requests.RequestException, ValueError, KeyError, TypeError, AttributeError):
        _deny(
            "Cannot retrieve a valid CareVerse public key from the configured instance."
        )
    if payload["key_id"] != key_id:
        _deny("Signing key ID is not published by the configured CareVerse instance.")
    return payload


def verify_request(request, trusted_keys, endpoint, namespace="helpdesk.api.plugin"):
    """Verify canonical bytes and signed identity; return external user and replay key."""
    if request.path != "/api/method/" + namespace + "." + endpoint:
        _deny("Use the canonical signed RPC URL.")
    stamp = _check_timestamp(request)
    args = signed_arguments(request)
    key_id = request.headers.get("X-AC-Key-Id", "")
    trust = trusted_keys.get(key_id)
    if not trust:
        _deny("Unknown signing key ID.")
    raw = request.get_data(cache=True)
    query = request.query_string.decode("ascii")
    target = request.path + ("?" + query if query else "")
    canonical = "\n".join(
        [request.method.upper(), target, stamp, hashlib.sha256(raw).hexdigest()]
    )
    try:
        key = serialization.load_pem_public_key(trust["public_key_pem"].encode())
        if not isinstance(key, Ed25519PublicKey):
            raise ValueError()
        key.verify(
            base64.b64decode(request.headers.get("X-AC-Signature", ""), validate=True),
            canonical.encode(),
        )
    except (ValueError, KeyError, TypeError, InvalidSignature):
        _deny("Invalid request signature.")
    user = args["user_id"]
    if user in ("Guest", "Administrator") or user not in trust.get("allowed_users", []):
        _deny("CareVerse instance is not authorized for this user.")
    replay_key = (
        "helpdesk:mobile:replay:"
        + hashlib.sha256(
            (args["instance_id"] + ":" + args["request_id"]).encode()
        ).hexdigest()
    )
    return user, replay_key


def signed_rpc(fn):
    @wraps(fn)
    def wrapped(*args, **kwargs):
        request = frappe.request
        _check_timestamp(request)
        values = signed_arguments(request)
        try:
            instance = frappe.get_doc("HD CareVerse Instance", values["instance_id"])
        except frappe.DoesNotExistError:
            _deny("Unknown CareVerse instance.")
        if not instance.enabled:
            _deny("CareVerse instance is disabled.")
        mappings = {
            row.careverse_user: row.helpdesk_user
            for row in instance.users
            if row.enabled
        }
        if values["user_id"] not in mappings:
            _deny("No enabled user mapping for this CareVerse instance.")
        key_id = request.headers.get("X-AC-Key-Id", "")
        public = _fetch_public_key(instance, key_id)
        user, replay_key = verify_request(
            request,
            {key_id: {**public, "allowed_users": list(mappings)}},
            fn.__name__,
            fn.__module__,
        )
        target_user = mappings[user]
        if target_user in ("Guest", "Administrator") or not frappe.db.get_value(
            "User", target_user, "enabled"
        ):
            _deny("Mapped Helpdesk user is unavailable or disabled.")
        # Dispatch only the verified bytes, never an unsigned form/keyword override.
        business = {
            key: value
            for key, value in values.items()
            if key not in ("instance_id", "user_id", "request_id")
        }
        try:
            inspect.signature(fn).bind(**business)
        except TypeError:
            frappe.throw("Missing or unexpected RPC arguments.")
        if not frappe.cache().set(replay_key, "1", nx=True, ex=90):
            _deny("Request already received. Use a new request_id.")
        previous = frappe.session.user
        previous_context = getattr(frappe.local, "careverse_identity", None)
        try:
            frappe.set_user(target_user)
            frappe.local.careverse_identity = {
                "instance_id": instance.name,
                "user_id": user,
            }
            return fn(**business)
        finally:
            frappe.set_user(previous)
            frappe.local.careverse_identity = previous_context

    return wrapped
