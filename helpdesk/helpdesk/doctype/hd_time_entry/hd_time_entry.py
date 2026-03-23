# Copyright (c) 2026, Frappe Technologies Pvt. Ltd. and contributors
# For license information, please see license.txt

import frappe
from frappe import _
from frappe.model.document import Document
from helpdesk.utils import is_agent

MAX_DESCRIPTION_LENGTH = 500  # Issue #11: single source of truth for description limit
MAX_DURATION_MINUTES = 1440  # Issue #13: 24-hour upper bound

# Explicitly enumerate privileged roles rather than deriving from AGENT_ROLES.
# Derivation via AGENT_ROLES - {"Agent"} is a privilege escalation risk: any new
# role added to AGENT_ROLES would silently auto-become privileged and gain the
# ability to delete any agent's time entry — without an intentional review.
# Only HD Admin and Agent Manager hold delete:1 in the HD Time Entry DocType JSON;
# that explicit list is the source of truth, not set arithmetic.
# See QA report task-155 Finding #4.
PRIVILEGED_ROLES: frozenset = frozenset({"HD Admin", "Agent Manager"})


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

	        **Identity contract** — ``user_roles`` is only valid for the current
	        session user (``frappe.session.user``).  Passing ``user_roles`` for a
	        *different* user raises ``ValueError`` immediately to prevent silent
	        identity mismatches that would produce incorrect permission decisions.
	        This mirrors the same contract enforced by ``is_agent()``.

	Uses frappe.get_roles() (Issue #12) instead of direct Has Role table query.
	Includes Agent Manager (Issue #1) which holds delete:1 in the DocType JSON.

	Raises frappe.PermissionError if the user is not permitted.
	Raises ValueError if user_roles is provided for a non-session user.
	"""
	# Administrator can always delete any entry — explicit short-circuit so we do not
	# depend on Administrator incidentally holding one of the PRIVILEGED_ROLES.
	if user == "Administrator":
		return
	# Identity-contract enforcement: pre-fetched roles are only valid for the
	# current session user.  Catching this at runtime prevents silent mismatches
	# where a caller passes user="X" with roles fetched for user "Y".
	# Mirrors the same contract in is_agent() (helpdesk/utils.py).
	if user_roles is not None and user != frappe.session.user:
		raise ValueError(
			f"_check_delete_permission(): pre-fetched user_roles are only valid for the "
			f"current session user ({frappe.session.user!r}). Received user={user!r}. "
			"To check a different user, omit user_roles and let _check_delete_permission() "
			"fetch roles via frappe.get_roles(user)."
		)
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
		Enforce agent-only access and ownership on all delete paths including
		direct REST DELETE (e.g. DELETE /api/resource/HD Time Entry/{name}).

		Frappe calls on_trash (not before_delete) from frappe.delete_doc() /
		doc.delete(), so this is the correct hook to intercept all deletion paths.

		Pre-gate: only agents may delete time entries at all.  This blocks bare
		System Manager users who own their own entries (created via direct REST POST)
		from deleting them — the ownership check in _check_delete_permission would
		allow that case because entry.agent == user passes, so the is_agent() guard
		here is the only layer that catches it.

		Delegates to the shared _check_delete_permission helper (Issue #9) so the
		ownership logic is defined in exactly one place and cannot drift.
		"""
		user = frappe.session.user
		# Administrator short-circuit: skip the role lookup entirely.
		# is_agent() and _check_delete_permission() both short-circuit for
		# Administrator, but get_roles() would still be called unconditionally
		# before reaching those checks — wasteful for a highly-frequent caller.
		# See QA report task-155 Finding #3.
		if user == "Administrator":
			return
		# Pre-fetch roles ONCE and forward to both callers to avoid a redundant
		# frappe.get_roles() DB/cache hit.
		user_roles = set(frappe.get_roles(user))
		if not is_agent(user=user, user_roles=user_roles):
			frappe.throw(_("Not permitted"), frappe.PermissionError)
		_check_delete_permission(self, user, user_roles=user_roles)
