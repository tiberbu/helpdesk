# Copyright (c) 2026, Frappe Technologies Pvt. Ltd. and contributors
# For license information, please see license.txt

"""Unit tests for the HD Automation Rule DocType and its controller."""

import json

import frappe
from frappe.tests.utils import FrappeTestCase

from helpdesk.test_utils import create_agent


class TestHDAutomationRule(FrappeTestCase):
    """Basic CRUD and validation tests for HD Automation Rule DocType."""

    def setUp(self):
        frappe.set_user("Administrator")
        self._created = []

    def tearDown(self):
        frappe.set_user("Administrator")
        for name in self._created:
            if frappe.db.exists("HD Automation Rule", name):
                frappe.delete_doc("HD Automation Rule", name, ignore_permissions=True)
        frappe.db.commit()  # nosemgrep
        frappe.db.rollback()

    def _new_rule(self, **kwargs):
        defaults = dict(
            trigger_type="ticket_created",
            enabled=1,
            conditions="[]",
            actions="[]",
            priority_order=10,
        )
        defaults.update(kwargs)
        if "rule_name" not in defaults:
            defaults["rule_name"] = f"test-rule-{frappe.generate_hash(length=8)}"
        doc = frappe.get_doc({"doctype": "HD Automation Rule", **defaults})
        doc.insert(ignore_permissions=True)
        self._created.append(doc.name)
        return doc

    # ------------------------------------------------------------------ #
    # CRUD                                                                  #
    # ------------------------------------------------------------------ #

    def test_create_rule_with_all_fields(self):
        rule = self._new_rule(
            rule_name=f"full-rule-{frappe.generate_hash(length=6)}",
            description="A complete test rule",
            trigger_type="ticket_updated",
            priority_order=5,
            conditions=json.dumps(
                [{"field": "priority", "operator": "equals", "value": "Urgent"}]
            ),
            actions=json.dumps([{"type": "set_priority", "value": "High"}]),
        )
        self.assertEqual(rule.trigger_type, "ticket_updated")
        self.assertEqual(rule.priority_order, 5)
        self.assertEqual(rule.enabled, 1)

    def test_rule_defaults(self):
        rule = self._new_rule()
        self.assertEqual(rule.enabled, 1)
        self.assertEqual(rule.priority_order, 10)
        self.assertEqual(rule.failure_count, 0)

    def test_rule_accessible_via_frappe_get_all(self):
        rule = self._new_rule()
        results = frappe.get_all(
            "HD Automation Rule", filters={"name": rule.name}, fields=["name", "enabled"]
        )
        self.assertEqual(len(results), 1)
        self.assertEqual(results[0]["name"], rule.name)

    # ------------------------------------------------------------------ #
    # Validation: conditions JSON                                           #
    # ------------------------------------------------------------------ #

    def test_invalid_conditions_json_raises(self):
        with self.assertRaises(frappe.ValidationError):
            self._new_rule(conditions="not-json{{{")

    def test_conditions_object_instead_of_array_raises(self):
        with self.assertRaises(frappe.ValidationError):
            self._new_rule(conditions=json.dumps({"field": "priority"}))

    def test_condition_missing_field_key_raises(self):
        with self.assertRaises(frappe.ValidationError):
            self._new_rule(
                conditions=json.dumps([{"operator": "equals", "value": "Urgent"}])
            )

    def test_empty_conditions_is_valid(self):
        rule = self._new_rule(conditions="[]")
        self.assertEqual(rule.conditions, "[]")

    # ------------------------------------------------------------------ #
    # Validation: actions JSON                                              #
    # ------------------------------------------------------------------ #

    def test_invalid_actions_json_raises(self):
        with self.assertRaises(frappe.ValidationError):
            self._new_rule(actions="bad json")

    def test_actions_object_instead_of_array_raises(self):
        with self.assertRaises(frappe.ValidationError):
            self._new_rule(actions=json.dumps({"type": "set_priority"}))

    def test_action_missing_type_key_raises(self):
        with self.assertRaises(frappe.ValidationError):
            self._new_rule(actions=json.dumps([{"value": "Urgent"}]))

    def test_empty_actions_is_valid(self):
        rule = self._new_rule(actions="[]")
        self.assertEqual(rule.actions, "[]")

    # ------------------------------------------------------------------ #
    # Security: non-admin cannot create rules (NFR-SE-04)                  #
    # ------------------------------------------------------------------ #

    def test_agent_cannot_create_rule(self):
        create_agent("rule.agent@test.com", "Rule", "Agent")
        frappe.set_user("rule.agent@test.com")
        with self.assertRaises(frappe.PermissionError):
            self._new_rule()

    def test_administrator_can_create_rule(self):
        frappe.set_user("Administrator")
        rule = self._new_rule()
        self.assertIsNotNone(rule.name)
