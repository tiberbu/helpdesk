# Copyright (c) 2026, Frappe Technologies and Contributors
# See license.txt

import frappe
from frappe import _
from frappe.model.document import Document


class HDFacilityMapping(Document):
	def validate(self):
		self._auto_resolve_parent_teams()

	def _auto_resolve_parent_teams(self):
		"""Auto-resolve l1_team from l0_team.parent_team if not explicitly set."""
		if self.l0_team and not self.l1_team:
			l0_parent = frappe.db.get_value("HD Team", self.l0_team, "parent_team")
			if l0_parent:
				self.l1_team = l0_parent

		if self.l1_team and not self.l2_team:
			l1_parent = frappe.db.get_value("HD Team", self.l1_team, "parent_team")
			if l1_parent:
				self.l2_team = l1_parent
