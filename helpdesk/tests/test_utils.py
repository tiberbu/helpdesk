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
