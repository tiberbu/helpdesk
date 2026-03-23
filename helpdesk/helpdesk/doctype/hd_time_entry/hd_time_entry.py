# Copyright (c) 2026, Frappe Technologies Pvt. Ltd. and contributors
# For license information, please see license.txt

import frappe
from frappe import _
from frappe.model.document import Document

MAX_DESCRIPTION_LENGTH = 500  # Issue #11: single source of truth for description limit
MAX_DURATION_MINUTES = 1440  # Issue #13: 24-hour upper bound

# Single source of truth for roles that may delete any time entry (not just their own).
# Mirrors the delete:1 grant in the HD Time Entry DocType JSON.
# Note: System Manager is intentionally excluded — bare System Manager users are not
# agents and must not be granted delete authority over time entries.
PRIVILEGED_ROLES = frozenset({"HD Admin", "Agent Manager"})


def _check_delete_permission(entry, user, user_roles=None):
	"""
	Shared permission check for deleting an HD Time Entry (Issue #9).

	Agents may only delete their own entries; HD Admin and Agent Manager
	(privileged agent roles) may delete any entry.

	Administrator is always permitted (explicit short-circuit before role lookup).

	Note: This function is called from on_trash() (all deletion paths) and from
	delete_entry() (whitelisted API). Callers are responsible for enforcing any
	additional pre-gate checks (e.g. is_agent()) before delegating here.
	System Manager is intentionally NOT in PRIVILEGED_ROLES — bare System Manager
	users must be blocked by the caller's pre-gate before this function is reached.

	Args:
	    entry: The HD Time Entry document.
	    user: The user performing the delete.
	    user_roles: Pre-fetched set of role names (optional). If None, roles are
	        fetched via frappe.get_roles(). Pass a pre-fetched set to avoid a
	        redundant DB/cache hit when the caller already holds the roles.

	Uses frappe.get_roles() (Issue #12) instead of direct Has Role table query.
	Includes Agent Manager (Issue #1) which holds delete:1 in the DocType JSON.

	Raises frappe.PermissionError if the user is not permitted.
	"""
	# Administrator can always delete any entry — explicit short-circuit so we do not
	# depend on Administrator incidentally holding one of the PRIVILEGED_ROLES.
	if user == "Administrator":
		return
	if user_roles is None:
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

	def on_trash(self):
		"""
		Enforce ownership on all delete paths including direct REST DELETE
		(e.g. DELETE /api/resource/HD Time Entry/{name}).

		Frappe calls on_trash (not before_delete) from frappe.delete_doc() /
		doc.delete(), so this is the correct hook to intercept all deletion paths.

		Delegates to the shared _check_delete_permission helper (Issue #9) so the
		logic is defined in exactly one place and cannot drift.
		"""
		_check_delete_permission(self, frappe.session.user)
