# Copyright (c) 2026, Frappe Technologies Pvt. Ltd. and contributors
# For license information, please see license.txt

import json

import frappe
from frappe import _
from frappe.model.document import Document

# Roles allowed to create/edit/delete automation rules (NFR-SE-04)
AUTOMATION_ADMIN_ROLES = frozenset({"System Manager", "HD Admin"})


class HDAutomationRule(Document):
	def validate(self):
		self._validate_conditions()
		self._validate_actions()
		self._check_write_permission()

	def _check_write_permission(self):
		"""Restrict create/edit to System Manager and HD Admin (NFR-SE-04)."""
		user = frappe.session.user
		if user == "Administrator":
			return
		roles = set(frappe.get_roles(user))
		if not (roles & AUTOMATION_ADMIN_ROLES):
			frappe.throw(
				_("Only System Manager or HD Admin can manage Automation Rules."),
				frappe.PermissionError,
			)

	# Maximum nesting depth for condition groups
	_MAX_CONDITION_DEPTH = 5

	def _validate_conditions(self):
		"""Ensure conditions field is a valid JSON array."""
		if not self.conditions:
			self.conditions = "[]"
			return
		try:
			data = json.loads(self.conditions)
		except (json.JSONDecodeError, TypeError):
			frappe.throw(
				_("Conditions must be a valid JSON array."),
				frappe.ValidationError,
			)
			return
		if not isinstance(data, list):
			frappe.throw(
				_("Conditions must be a JSON array, not an object."),
				frappe.ValidationError,
			)
		self._validate_condition_list(data, depth=0)

	def _validate_condition_list(self, data, depth=0):
		"""Recursively validate a condition list, supporting arbitrarily nested groups."""
		if depth > self._MAX_CONDITION_DEPTH:
			frappe.throw(
				_("Conditions are nested too deeply (maximum depth is {0}).").format(
					self._MAX_CONDITION_DEPTH
				),
				frappe.ValidationError,
			)
		for i, cond in enumerate(data):
			if not isinstance(cond, dict):
				frappe.throw(
					_("Condition #{0} must be a JSON object.").format(i + 1),
					frappe.ValidationError,
				)
			if "conditions" in cond:
				# Nested condition group — validate recursively
				nested = cond["conditions"]
				if not isinstance(nested, list):
					frappe.throw(
						_("Condition #{0} nested 'conditions' must be a list.").format(i + 1),
						frappe.ValidationError,
					)
				self._validate_condition_list(nested, depth=depth + 1)
			elif "field" not in cond or "operator" not in cond:
				frappe.throw(
					_("Condition #{0} must have 'field' and 'operator' keys.").format(i + 1),
					frappe.ValidationError,
				)

	def _validate_actions(self):
		"""Ensure actions field is a valid JSON array."""
		if not self.actions:
			self.actions = "[]"
			return
		try:
			data = json.loads(self.actions)
		except (json.JSONDecodeError, TypeError):
			frappe.throw(
				_("Actions must be a valid JSON array."),
				frappe.ValidationError,
			)
			return
		if not isinstance(data, list):
			frappe.throw(
				_("Actions must be a JSON array, not an object."),
				frappe.ValidationError,
			)
		for i, action in enumerate(data):
			if not isinstance(action, dict):
				frappe.throw(
					_("Action #{0} must be a JSON object.").format(i + 1),
					frappe.ValidationError,
				)
			if "type" not in action:
				frappe.throw(
					_("Action #{0} must have a 'type' key.").format(i + 1),
					frappe.ValidationError,
				)
