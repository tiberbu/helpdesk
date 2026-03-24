# -*- coding: utf-8 -*-
# Copyright (c) 2026, Frappe Technologies Pvt. Ltd. and contributors
# See license.txt
"""
Unit tests for Story 4.4: OLA/UC Agreement Type Preparation.
Tests cover:
- agreement_type field default value ("SLA")
- agreement_type Select options (SLA, OLA, UC)
- internal_team and vendor field presence on DocType meta
- Migration patch sets SLA default for NULL records (idempotent)
- Permission enforcement (Guest cannot read)
"""
import frappe
from frappe.tests import IntegrationTestCase


class TestHDSLAAgreementType(IntegrationTestCase):
	def setUp(self):
		# Track inserted test record names for cleanup
		self._inserted_names = []

	def tearDown(self):
		frappe.set_user("Administrator")
		for name in self._inserted_names:
			frappe.db.sql(
				"DELETE FROM `tabHD Service Level Agreement` WHERE name = %s", name
			)
		if self._inserted_names:
			frappe.db.commit()

	# ------------------------------------------------------------------
	# AC #1 / AC #5: agreement_type field with default "SLA"
	# ------------------------------------------------------------------
	def test_agreement_type_default_is_sla(self):
		"""New doc without explicit agreement_type defaults to 'SLA'."""
		doc = frappe.new_doc("HD Service Level Agreement")
		# Default is applied at object creation time via field definition
		self.assertEqual(doc.agreement_type, "SLA")

	# ------------------------------------------------------------------
	# AC #5: Select options contain exactly SLA, OLA, UC
	# ------------------------------------------------------------------
	def test_agreement_type_select_options(self):
		"""agreement_type field has exactly three options: SLA, OLA, UC."""
		meta = frappe.get_meta("HD Service Level Agreement")
		field = meta.get_field("agreement_type")
		self.assertIsNotNone(field, "agreement_type field must exist on DocType meta")
		options = [opt.strip() for opt in field.options.split("\n") if opt.strip()]
		self.assertEqual(sorted(options), sorted(["SLA", "OLA", "UC"]))

	# ------------------------------------------------------------------
	# AC #5: internal_team and vendor fields exist on meta
	# ------------------------------------------------------------------
	def test_internal_team_field_exists(self):
		"""internal_team Link field must exist on HD Service Level Agreement meta."""
		meta = frappe.get_meta("HD Service Level Agreement")
		field = meta.get_field("internal_team")
		self.assertIsNotNone(field, "internal_team field must exist on DocType meta")
		self.assertEqual(field.fieldtype, "Link")
		self.assertEqual(field.options, "HD Team")

	def test_vendor_field_exists(self):
		"""vendor Data field must exist on HD Service Level Agreement meta."""
		meta = frappe.get_meta("HD Service Level Agreement")
		field = meta.get_field("vendor")
		self.assertIsNotNone(field, "vendor field must exist on DocType meta")
		self.assertEqual(field.fieldtype, "Data")

	# ------------------------------------------------------------------
	# AC #6: Migration patch sets 'SLA' default for NULL records
	# ------------------------------------------------------------------
	def test_migration_patch_sets_sla_default(self):
		"""Patch sets agreement_type='SLA' for records with NULL or empty value."""
		# Insert two raw records with NULL agreement_type to simulate pre-migration state
		for i, name in enumerate(["_test_sla_patch_a", "_test_sla_patch_b"]):
			frappe.db.sql(
				"""INSERT INTO `tabHD Service Level Agreement`
				   (name, service_level, agreement_type)
				   VALUES (%s, %s, NULL)
				   ON DUPLICATE KEY UPDATE agreement_type = NULL""",
				(name, f"_Test Patch SLA {i}"),
			)
			self._inserted_names.append(name)
		frappe.db.commit()

		# Run the patch
		from helpdesk.patches.v1_phase1.add_sla_agreement_type import execute

		execute()

		# Verify both records now have agreement_type = 'SLA'
		for name in ["_test_sla_patch_a", "_test_sla_patch_b"]:
			val = frappe.db.get_value(
				"HD Service Level Agreement", name, "agreement_type"
			)
			self.assertEqual(val, "SLA", f"Record {name} should have agreement_type='SLA'")

	def test_migration_patch_is_idempotent(self):
		"""Running the patch twice must not raise errors or corrupt data."""
		# Insert a record with NULL
		frappe.db.sql(
			"""INSERT INTO `tabHD Service Level Agreement`
			   (name, service_level, agreement_type)
			   VALUES ('_test_sla_idem', '_Test Idem SLA', NULL)
			   ON DUPLICATE KEY UPDATE agreement_type = NULL""",
		)
		self._inserted_names.append("_test_sla_idem")
		frappe.db.commit()

		from helpdesk.patches.v1_phase1.add_sla_agreement_type import execute

		# First run
		execute()
		val_after_first = frappe.db.get_value(
			"HD Service Level Agreement", "_test_sla_idem", "agreement_type"
		)
		self.assertEqual(val_after_first, "SLA")

		# Second run — must not raise and value must stay 'SLA'
		execute()
		val_after_second = frappe.db.get_value(
			"HD Service Level Agreement", "_test_sla_idem", "agreement_type"
		)
		self.assertEqual(val_after_second, "SLA")

	def test_migration_patch_skips_existing_values(self):
		"""Patch must not overwrite records already having OLA or UC."""
		# Insert record with OLA
		frappe.db.sql(
			"""INSERT INTO `tabHD Service Level Agreement`
			   (name, service_level, agreement_type)
			   VALUES ('_test_sla_ola', '_Test OLA SLA', 'OLA')
			   ON DUPLICATE KEY UPDATE agreement_type = 'OLA'""",
		)
		self._inserted_names.append("_test_sla_ola")
		frappe.db.commit()

		from helpdesk.patches.v1_phase1.add_sla_agreement_type import execute

		execute()

		val = frappe.db.get_value(
			"HD Service Level Agreement", "_test_sla_ola", "agreement_type"
		)
		self.assertEqual(val, "OLA", "Patch must not overwrite existing non-empty values")

	# ------------------------------------------------------------------
	# AC #5: in_list_view is set on agreement_type
	# ------------------------------------------------------------------
	def test_agreement_type_in_list_view(self):
		"""agreement_type field must have in_list_view=1 to appear in list column."""
		meta = frappe.get_meta("HD Service Level Agreement")
		field = meta.get_field("agreement_type")
		self.assertIsNotNone(field)
		self.assertEqual(field.in_list_view, 1)

	# ------------------------------------------------------------------
	# AC #7: Permission boundary — Guest cannot read
	# ------------------------------------------------------------------
	def test_api_requires_permission(self):
		"""Guest user must not be able to read HD Service Level Agreement."""
		frappe.set_user("Guest")
		try:
			with self.assertRaises(frappe.PermissionError):
				frappe.get_list("HD Service Level Agreement", limit=1)
		finally:
			frappe.set_user("Administrator")
