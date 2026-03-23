# Copyright (c) 2026, Frappe Technologies Pvt. Ltd. and contributors
# For license information, please see license.txt
"""
CSAT Survey API endpoints.
Story 3.7 -- CSAT Survey Infrastructure and Delivery
"""
import json

import frappe
from frappe import _
from frappe.utils import now_datetime

from helpdesk.utils import generate_csat_token, validate_csat_token


# ---------------------------------------------------------------------------
# Guest endpoints (customers click from email)
# ---------------------------------------------------------------------------

@frappe.whitelist(allow_guest=True)
def submit_rating(token: str, rating: str) -> None:
	"""Submit a CSAT star rating via one-click link from survey email.

	Validates token, records rating, marks token used, then renders the
	thank-you page so the customer can optionally add a comment.

	AC #3, #7, #8 — single-click submission + HMAC token + single-use.
	"""
	try:
		rating_int = int(rating)
	except (ValueError, TypeError):
		frappe.throw(_("Invalid rating value."), frappe.ValidationError)

	if not (1 <= rating_int <= 5):
		frappe.throw(_("Rating must be between 1 and 5."), frappe.ValidationError)

	# Locate the pending CSAT Response record for this token
	response_name = frappe.db.get_value(
		"HD CSAT Response", {"token": token, "token_used": 0}, "name"
	)
	if not response_name:
		# Token already used or not found — render graceful error
		_render_error_page(
			_("This survey link has already been used or is invalid."),
			token=token,
		)
		return

	response_doc = frappe.get_doc("HD CSAT Response", response_name)

	# Validate token HMAC + expiry
	result = validate_csat_token(token, response_doc.ticket, response_doc.customer_email)
	if result["expired"]:
		_render_error_page(
			_("This survey link has expired."),
			token=token,
		)
		return
	if not result["valid"]:
		_render_error_page(
			_("This survey link is invalid."),
			token=token,
		)
		return

	# Record rating and mark token used (single-use enforcement — NFR-SE-03)
	frappe.db.set_value(
		"HD CSAT Response",
		response_name,
		{
			"rating": rating_int,
			"token_used": 1,
			"responded_at": now_datetime(),
		},
		update_modified=True,
	)
	frappe.db.commit()  # nosemgrep

	_render_thankyou_page(token=token, rating=rating_int)


@frappe.whitelist(allow_guest=True)
def submit_comment(token: str, comment: str) -> dict:
	"""Save optional free-text comment on an already-rated CSAT response.

	Idempotent — can be called multiple times; last comment wins.
	AC #4.
	"""
	comment = (comment or "").strip()[:2000]  # cap comment length

	response_name = frappe.db.get_value(
		"HD CSAT Response", {"token": token}, "name"
	)
	if not response_name:
		frappe.throw(_("Survey response not found."), frappe.DoesNotExistError)

	frappe.db.set_value(
		"HD CSAT Response",
		response_name,
		{"comment": comment},
		update_modified=True,
	)
	frappe.db.commit()  # nosemgrep

	return {"message": _("Thank you for your feedback!")}


@frappe.whitelist(allow_guest=True)
def unsubscribe(token: str) -> None:
	"""Unsubscribe a customer from future CSAT surveys.

	Adds their email to the ``csat_unsubscribed_emails`` JSON list in
	HD Settings and renders a confirmation page.
	AC #6.
	"""
	response_name = frappe.db.get_value(
		"HD CSAT Response", {"token": token}, "name"
	)
	if not response_name:
		_render_error_page(_("Invalid unsubscribe link."), token=token)
		return

	customer_email = frappe.db.get_value("HD CSAT Response", response_name, "customer_email")
	if not customer_email:
		_render_error_page(_("Invalid unsubscribe link."), token=token)
		return

	_mark_unsubscribed(customer_email)

	frappe.db.commit()  # nosemgrep
	_render_unsubscribe_confirmation_page(customer_email)


# ---------------------------------------------------------------------------
# Agent / authenticated endpoints
# ---------------------------------------------------------------------------

@frappe.whitelist()
def get_dashboard_data(filters: str = "{}") -> dict:
	"""Return aggregated CSAT data for Story 6.3 CSAT Analytics Dashboard.

	:param filters: JSON string with optional keys:
	    ``from_date``, ``to_date``, ``agent`` (User), ``team`` (HD Team name).
	:returns: Dict with overall_score, response_count, rating_distribution,
	    responses list.
	"""
	frappe.has_permission("HD CSAT Response", "read", throw=True)

	try:
		f = json.loads(filters) if isinstance(filters, str) else filters
	except (ValueError, TypeError):
		f = {}

	qb_filters: dict = {"rating": ["!=", None]}

	if f.get("from_date"):
		qb_filters["survey_sent_at"] = [">=", f["from_date"]]
	if f.get("to_date"):
		existing = qb_filters.get("survey_sent_at")
		if existing:
			# Already have from_date — use list-of-conditions form
			qb_filters["survey_sent_at"] = ["between", [f["from_date"], f["to_date"]]]
		else:
			qb_filters["survey_sent_at"] = ["<=", f["to_date"]]

	responses = frappe.db.get_all(
		"HD CSAT Response",
		filters=qb_filters,
		fields=["name", "ticket", "customer_email", "rating", "comment", "responded_at"],
		order_by="responded_at desc",
		limit=500,
	)

	if not responses:
		return {
			"overall_score": None,
			"response_count": 0,
			"rating_distribution": {str(i): 0 for i in range(1, 6)},
			"responses": [],
		}

	total = len(responses)
	score_sum = sum(r.rating for r in responses if r.rating)
	distribution = {str(i): 0 for i in range(1, 6)}
	for r in responses:
		if r.rating:
			distribution[str(r.rating)] += 1

	return {
		"overall_score": round(score_sum / total, 2) if total else None,
		"response_count": total,
		"rating_distribution": distribution,
		"responses": responses,
	}


# ---------------------------------------------------------------------------
# Internal helpers (not whitelisted)
# ---------------------------------------------------------------------------

def _mark_unsubscribed(email: str) -> None:
	"""Add *email* to the HD Settings ``csat_unsubscribed_emails`` JSON list."""
	raw = frappe.db.get_single_value("HD Settings", "csat_unsubscribed_emails")
	try:
		unsubscribed: list = json.loads(raw) if raw else []
	except (ValueError, TypeError):
		unsubscribed = []

	if email not in unsubscribed:
		unsubscribed.append(email)
		frappe.db.set_single_value(
			"HD Settings",
			"csat_unsubscribed_emails",
			json.dumps(unsubscribed),
		)


def is_unsubscribed(email: str) -> bool:
	"""Return True if *email* has unsubscribed from CSAT surveys."""
	raw = frappe.db.get_single_value("HD Settings", "csat_unsubscribed_emails")
	try:
		unsubscribed: list = json.loads(raw) if raw else []
	except (ValueError, TypeError):
		unsubscribed = []
	return email in unsubscribed


def _get_base_url() -> str:
	return frappe.utils.get_url()


def _render_thankyou_page(token: str, rating: int) -> None:
	"""Render and return a thank-you HTML response to the browser."""
	stars = "⭐" * rating
	html = f"""<!DOCTYPE html>
<html lang="en">
<head>
  <meta charset="UTF-8">
  <meta name="viewport" content="width=device-width, initial-scale=1.0">
  <title>Thank You!</title>
  <style>
    body {{ font-family: -apple-system, BlinkMacSystemFont, 'Segoe UI', Roboto, sans-serif;
            background: #f9fafb; display: flex; align-items: center; justify-content: center;
            min-height: 100vh; margin: 0; }}
    .card {{ background: #fff; border-radius: 12px; padding: 40px 48px; text-align: center;
             box-shadow: 0 4px 16px rgba(0,0,0,0.08); max-width: 480px; width: 100%; }}
    h1 {{ color: #111827; font-size: 24px; margin: 0 0 8px; }}
    p {{ color: #6b7280; font-size: 15px; line-height: 1.6; margin: 0 0 20px; }}
    .stars {{ font-size: 32px; margin: 16px 0; }}
    textarea {{ width: 100%; box-sizing: border-box; border: 1px solid #e5e7eb;
               border-radius: 8px; padding: 10px 12px; font-size: 14px;
               resize: vertical; min-height: 80px; }}
    button {{ background: #4F46E5; color: #fff; border: none; border-radius: 8px;
             padding: 10px 24px; font-size: 15px; cursor: pointer; margin-top: 12px; }}
    button:hover {{ background: #4338CA; }}
    .sent {{ color: #059669; font-size: 14px; margin-top: 12px; display: none; }}
  </style>
</head>
<body>
  <div class="card">
    <div class="stars">{stars}</div>
    <h1>Thank you!</h1>
    <p>We appreciate your feedback. Would you like to share more details?</p>
    <textarea id="comment" placeholder="Your comment (optional)…"></textarea>
    <br>
    <button onclick="sendComment()">Submit Comment</button>
    <p class="sent" id="sent-msg">✅ Comment saved!</p>
  </div>
  <script>
    async function sendComment() {{
      const comment = document.getElementById('comment').value.trim();
      if (!comment) return;
      const res = await fetch('/api/method/helpdesk.api.csat.submit_comment', {{
        method: 'POST',
        headers: {{'Content-Type': 'application/json', 'X-Frappe-CSRF-Token': 'fetch'}},
        body: JSON.stringify({{ token: '{token}', comment }})
      }});
      if (res.ok) {{
        document.getElementById('sent-msg').style.display = 'block';
      }}
    }}
  </script>
</body>
</html>"""
	frappe.respond_as_web_page(title="Thank You!", html=html, http_status_code=200)


def _render_error_page(message: str, token: str = "") -> None:
	"""Render a graceful error page for invalid/expired tokens."""
	html = f"""<!DOCTYPE html>
<html lang="en">
<head>
  <meta charset="UTF-8">
  <title>Survey Link Issue</title>
  <style>
    body {{ font-family: -apple-system, BlinkMacSystemFont, 'Segoe UI', Roboto, sans-serif;
            background: #f9fafb; display: flex; align-items: center; justify-content: center;
            min-height: 100vh; margin: 0; }}
    .card {{ background: #fff; border-radius: 12px; padding: 40px 48px; text-align: center;
             box-shadow: 0 4px 16px rgba(0,0,0,0.08); max-width: 420px; width: 100%; }}
    h1 {{ color: #111827; font-size: 22px; margin: 0 0 8px; }}
    p {{ color: #6b7280; font-size: 15px; line-height: 1.6; margin: 0; }}
  </style>
</head>
<body>
  <div class="card">
    <h1>⚠️ Survey Link Issue</h1>
    <p>{frappe.utils.escape_html(message)}</p>
  </div>
</body>
</html>"""
	frappe.respond_as_web_page(
		title="Survey Link Issue",
		html=html,
		http_status_code=400,
	)


def _render_unsubscribe_confirmation_page(email: str) -> None:
	"""Render unsubscribe confirmation page."""
	safe_email = frappe.utils.escape_html(email)
	html = f"""<!DOCTYPE html>
<html lang="en">
<head>
  <meta charset="UTF-8">
  <title>Unsubscribed</title>
  <style>
    body {{ font-family: -apple-system, BlinkMacSystemFont, 'Segoe UI', Roboto, sans-serif;
            background: #f9fafb; display: flex; align-items: center; justify-content: center;
            min-height: 100vh; margin: 0; }}
    .card {{ background: #fff; border-radius: 12px; padding: 40px 48px; text-align: center;
             box-shadow: 0 4px 16px rgba(0,0,0,0.08); max-width: 420px; width: 100%; }}
    h1 {{ color: #111827; font-size: 22px; margin: 0 0 8px; }}
    p {{ color: #6b7280; font-size: 15px; line-height: 1.6; margin: 0; }}
  </style>
</head>
<body>
  <div class="card">
    <h1>✅ Unsubscribed</h1>
    <p><strong>{safe_email}</strong> has been unsubscribed from future CSAT surveys.</p>
  </div>
</body>
</html>"""
	frappe.respond_as_web_page(title="Unsubscribed", html=html, http_status_code=200)
