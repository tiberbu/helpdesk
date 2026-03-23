# Copyright (c) 2026, Frappe Technologies Pvt. Ltd. and contributors
# For license information, please see license.txt
#
# Tests for helpdesk/utils.py — co-located with the module under test.
# Moved here from test_hd_time_entry.py (story-130 P1 fix).

import frappe
from frappe.tests.utils import FrappeTestCase

from helpdesk.test_utils import create_agent


class TestIsAgentExplicitUser(FrappeTestCase):
	"""
	Dedicated tests for is_agent(user=...) explicit user parameter.

	P1-2 fix: is_admin(user) parameter was silently added to is_agent() without tests.
	The change has global scope — all callers that pass user= must check THAT user,
	not frappe.session.user.
	"""

	def setUp(self):
		frappe.set_user("Administrator")
		# Create an agent user for is_agent() checks
		create_agent("is.agent.check@test.com", "IsAgent", "Check")
		# Create a non-agent (customer) user
		if not frappe.db.exists("User", "not.an.agent@test.com"):
			frappe.get_doc({
				"doctype": "User",
				"email": "not.an.agent@test.com",
				"first_name": "NotAgent",
				"last_name": "User",
				"send_welcome_email": 0,
			}).insert(ignore_permissions=True)

	def tearDown(self):
		frappe.set_user("Administrator")
		frappe.db.rollback()

	def test_is_agent_with_explicit_agent_user(self):
		"""
		is_agent(user='is.agent.check@test.com') must return True even when the
		current session user is someone else (e.g. the customer). This verifies the
		user parameter is actually used, not frappe.session.user.
		"""
		from helpdesk.utils import is_agent

		# Session user is NOT an agent
		frappe.set_user("not.an.agent@test.com")
		# But checking the explicit agent user must still return True
		result = is_agent(user="is.agent.check@test.com")
		self.assertTrue(
			result,
			"is_agent(user='is.agent.check@test.com') must return True regardless of session user",
		)

	def test_is_agent_with_explicit_non_agent_user(self):
		"""
		is_agent(user='not.an.agent@test.com') must return False even when the
		current session user IS an agent. Verifies the parameter is not ignored.
		"""
		from helpdesk.utils import is_agent

		# Session user IS an agent
		frappe.set_user("is.agent.check@test.com")
		# But checking the non-agent user must return False
		result = is_agent(user="not.an.agent@test.com")
		self.assertFalse(
			result,
			"is_agent(user='not.an.agent@test.com') must return False regardless of session user",
		)

	def test_is_agent_defaults_to_session_user_when_no_param(self):
		"""
		is_agent() with no arguments must check frappe.session.user, not a cached value.
		"""
		from helpdesk.utils import is_agent

		# Session is the agent — should return True
		frappe.set_user("is.agent.check@test.com")
		self.assertTrue(is_agent(), "is_agent() must return True when session user is an agent")

		# Session is the customer — should return False
		frappe.set_user("not.an.agent@test.com")
		self.assertFalse(is_agent(), "is_agent() must return False when session user is not an agent")

	def test_is_agent_administrator_always_returns_true(self):
		"""
		is_agent(user='Administrator') must always return True.
		Administrator is handled via is_admin() inside is_agent().
		"""
		from helpdesk.utils import is_agent

		frappe.set_user("not.an.agent@test.com")
		self.assertTrue(
			is_agent(user="Administrator"),
			"is_agent(user='Administrator') must always return True",
		)

	def test_is_agent_raises_valueerror_for_mismatched_user_with_roles(self):
		"""
		ValueError must be raised when user_roles are pre-fetched for the current
		session user but is_agent() is called with a *different* user.

		This enforces the identity contract: pre-fetched roles are only valid for
		frappe.session.user.  Passing them for a different user would silently
		produce incorrect permission decisions (privilege escalation or denial).
		"""
		from helpdesk.utils import is_agent

		# Session user is the agent
		frappe.set_user("is.agent.check@test.com")
		# user_roles fetched for the current session user (is.agent.check@test.com)
		session_user_roles = set(frappe.get_roles(frappe.session.user))

		# Calling is_agent() for a *different* user with these mismatched roles
		# must raise ValueError — not silently return a wrong answer.
		with self.assertRaises(ValueError):
			is_agent(user="not.an.agent@test.com", user_roles=session_user_roles)

	def test_is_agent_no_valueerror_when_user_matches_session(self):
		"""
		No ValueError must be raised when user equals the current session user
		and user_roles are provided — this is the valid, intended calling pattern.
		"""
		from helpdesk.utils import is_agent

		frappe.set_user("is.agent.check@test.com")
		user_roles = set(frappe.get_roles(frappe.session.user))

		# Same user as session — must succeed and return True (is an agent)
		result = is_agent(user=frappe.session.user, user_roles=user_roles)
		self.assertTrue(
			result,
			"is_agent(user=session_user, user_roles=...) must not raise and must return True for an agent",
		)
