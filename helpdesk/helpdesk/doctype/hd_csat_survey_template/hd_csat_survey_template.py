# Copyright (c) 2026, Frappe Technologies Pvt. Ltd. and contributors
# For license information, please see license.txt

import frappe
from frappe.model.document import Document


class HDCSATSurveyTemplate(Document):
	pass


def get_default_template() -> dict:
	"""Return the default CSAT survey template as a plain dict.

	Looks for a template with ``is_default=1``; if none found, returns
	built-in defaults so the caller always has something to render.
	"""
	default_doc = frappe.db.get_value(
		"HD CSAT Survey Template",
		{"is_default": 1},
		["template_name", "subject", "intro_text", "logo_url", "primary_color"],
		as_dict=True,
	)
	if default_doc:
		return default_doc

	return frappe._dict(
		template_name="Default",
		subject="How would you rate your support experience?",
		intro_text="We'd love to hear about your recent support experience. Please take a moment to rate it.",
		logo_url="",
		primary_color="#4F46E5",
	)
