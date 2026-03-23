"""JWT helper for chat session authentication (ADR-05).

Provides token generation and validation for stateless chat session auth.
Tokens are signed with the Frappe site secret so they are verifiable
server-side without storing them in the database.

Token payload:
    sub         — SHA-256 hash of the customer email
    session_id  — the HD Chat Session name / session_id
    iat         — issued-at (UTC)
    exp         — expiry (UTC, default 24 hours)
"""

import hashlib
from datetime import UTC, datetime, timedelta

import jwt

import frappe


_TOKEN_EXPIRY_HOURS = 24


def _get_signing_secret() -> str:
    """Return a stable per-site secret for JWT signing.

    Uses the Frappe site encryption key, which is generated once per site
    and persisted in site_config.json. Falls back to the site name for
    testing environments where encryption key may not be set.
    """
    from frappe.utils.password import get_encryption_key
    return get_encryption_key()


def generate_chat_token(session_id: str, customer_email: str) -> str:
    """Generate a signed JWT for a chat session.

    Parameters
    ----------
    session_id : str
        The HD Chat Session ``session_id`` field value.
    customer_email : str
        The customer's email address (stored as a hash in the token).

    Returns
    -------
    str
        Signed JWT string.
    """
    secret = _get_signing_secret()
    email_hash = hashlib.sha256(customer_email.lower().encode()).hexdigest()
    now = datetime.now(UTC)
    payload = {
        "sub": email_hash,
        "session_id": session_id,
        "iat": now,
        "exp": now + timedelta(hours=_TOKEN_EXPIRY_HOURS),
    }
    return jwt.encode(payload, secret, algorithm="HS256")


def validate_chat_token(token: str, session_id: str) -> bool:
    """Validate a chat JWT token.

    Parameters
    ----------
    token : str
        JWT string to validate.
    session_id : str
        Expected session_id — must match the token payload.

    Returns
    -------
    bool
        True if the token is valid and matches the session.

    Raises
    ------
    frappe.AuthenticationError
        If the token is invalid, expired, or does not match the session.
    """
    secret = _get_signing_secret()
    try:
        payload = jwt.decode(token, secret, algorithms=["HS256"])
    except jwt.ExpiredSignatureError:
        frappe.throw(
            frappe._("Chat session token has expired. Please start a new chat."),
            frappe.AuthenticationError,
        )
    except jwt.InvalidTokenError as exc:
        frappe.throw(
            frappe._("Invalid chat session token: {0}").format(str(exc)),
            frappe.AuthenticationError,
        )

    if payload.get("session_id") != session_id:
        frappe.throw(
            frappe._("Chat token does not match the requested session."),
            frappe.AuthenticationError,
        )

    return True
