# Copyright (c) 2026, Frappe Technologies Pvt. Ltd. and contributors
# For license information, please see license.txt

import frappe
from frappe import _
from frappe.model.document import Document

MAX_DESCRIPTION_LENGTH = 500  # Issue #11: single source of truth for description limit
MAX_DURATION_MINUTES = 1440  # Issue #13: 24-hour upper bound

# Single source of truth for roles that may delete any time entry (not just their own).
# Mirrors the delete:1 grant in the HD Time Entry DocType JSON.
PRIVILEGED_ROLES = {"HD Admin", "Agent Manager", "System Manager"}


def _check_delete_permission(entry, user):
	"""
	Shared permission check for deleting an HD Time Entry (Issue #9).

	Agents may only delete their own entries; HD Admin, Agent Manager, and
	System Manager may delete any entry.

	Uses frappe.get_roles() (Issue #12) instead of direct Has Role table query.
	Includes Agent Manager (Issue #1) which holds delete:1 in the DocType JSON.

	Raises frappe.PermissionError if the user is not permitted.
	"""
	user_roles = set(frappe.get_roles(user))
	is_privileged = bool(user_roles & PRIVILEGED_ROLES)
	if entry.agent != user and not is_privileged:
		frappe.throw(_("You can only delete your own time entries."), frappe.PermissionError)


class HDTimeEntry(Document):
	def validate(self):
		if self.duration_minutes < 1:
			frappe.throw(
				_("Duration must be at least 1 minute."),
				frappe.ValidationError,
			)
		# Issue #13: upper bound prevents nonsensical values (>24 h in a single entry)
		if self.duration_minutes > MAX_DURATION_MINUTES:
			frappe.throw(
				_("Duration must not exceed {0} minutes (24 hours).").format(MAX_DURATION_MINUTES),
				frappe.ValidationError,
			)
		# Issue #3/#4: enforce limit at model layer so direct REST POST /api/resource/…
		# cannot bypass the 500-char cap that previously existed only in the API layer.
		if len(self.description or "") > MAX_DESCRIPTION_LENGTH:
			frappe.throw(
				_("Description must not exceed {0} characters.").format(MAX_DESCRIPTION_LENGTH),
				frappe.ValidationError,
			)

	def before_delete(self):
		"""
		Enforce ownership on direct REST DELETE calls
		(e.g. DELETE /api/resource/HD Time Entry/{name}).

		Delegates to the shared _check_delete_permission helper (Issue #9) so the
		logic is defined in exactly one place and cannot drift.
		"""
		_check_delete_permission(self, frappe.session.user)
