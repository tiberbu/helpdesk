# Copyright (c) 2026, Frappe Technologies and contributors
# For license information, please see license.txt

import frappe
from frappe.tests.utils import FrappeTestCase


class TestHDSupportLevel(FrappeTestCase):
	def test_seed_data_exists(self):
		"""Verify the four seed support levels exist after patch."""
		expected = [
			("L0 - Sub-County", 0, "Sub-County Support", 1, 1, 60),
			("L1 - County", 1, "County Support", 1, 1, 120),
			("L2 - National", 2, "National Support", 1, 0, None),
			("L3 - Engineering", 3, "Engineering", 0, 0, None),
		]
		for level_name, order, display, allow_esc, auto_esc, minutes in expected:
			doc = frappe.get_doc("HD Support Level", level_name)
			self.assertEqual(doc.level_order, order)
			self.assertEqual(doc.display_name, display)
			self.assertEqual(doc.allow_escalation_to_next, allow_esc)
			self.assertEqual(doc.auto_escalate_on_breach, auto_esc)
			if minutes is not None:
				self.assertEqual(doc.auto_escalate_minutes, minutes)

	def test_level_name_required(self):
		"""level_name is required and unique."""
		doc = frappe.new_doc("HD Support Level")
		doc.level_order = 99
		self.assertRaises(frappe.ValidationError, doc.insert)

	def test_unique_level_name(self):
		"""Duplicate level_name should raise."""
		self.assertRaises(
			Exception,
			frappe.get_doc,
			{
				"doctype": "HD Support Level",
				"level_name": "L0 - Sub-County",
				"level_order": 99,
			},
		)
