# Copyright (c) 2026, Frappe Technologies Pvt. Ltd. and contributors
# For license information, please see license.txt

"""Unit tests for helpdesk.helpdesk.automation.conditions.ConditionEvaluator."""

import frappe
from frappe.tests.utils import FrappeTestCase

from helpdesk.helpdesk.automation.conditions import ConditionEvaluator


def _doc(**kwargs):
    """Return a simple frappe._dict acting as a ticket substitute."""
    return frappe._dict(kwargs)


class TestConditionEvaluator(FrappeTestCase):
    def setUp(self):
        self.ev = ConditionEvaluator()

    # ------------------------------------------------------------------ #
    # equals / not_equals                                                  #
    # ------------------------------------------------------------------ #

    def test_equals_match(self):
        doc = _doc(priority="Urgent")
        self.assertTrue(
            self.ev.evaluate(doc, [{"field": "priority", "operator": "equals", "value": "Urgent"}])
        )

    def test_equals_no_match(self):
        doc = _doc(priority="Low")
        self.assertFalse(
            self.ev.evaluate(doc, [{"field": "priority", "operator": "equals", "value": "Urgent"}])
        )

    def test_not_equals_match(self):
        doc = _doc(priority="Low")
        self.assertTrue(
            self.ev.evaluate(
                doc, [{"field": "priority", "operator": "not_equals", "value": "Urgent"}]
            )
        )

    def test_not_equals_no_match(self):
        doc = _doc(priority="Urgent")
        self.assertFalse(
            self.ev.evaluate(
                doc, [{"field": "priority", "operator": "not_equals", "value": "Urgent"}]
            )
        )

    # ------------------------------------------------------------------ #
    # contains                                                             #
    # ------------------------------------------------------------------ #

    def test_contains_match(self):
        doc = _doc(subject="Server is down")
        self.assertTrue(
            self.ev.evaluate(
                doc, [{"field": "subject", "operator": "contains", "value": "down"}]
            )
        )

    def test_contains_case_insensitive(self):
        doc = _doc(subject="Server is DOWN")
        self.assertTrue(
            self.ev.evaluate(
                doc, [{"field": "subject", "operator": "contains", "value": "down"}]
            )
        )

    def test_contains_no_match(self):
        doc = _doc(subject="All systems operational")
        self.assertFalse(
            self.ev.evaluate(
                doc, [{"field": "subject", "operator": "contains", "value": "down"}]
            )
        )

    # ------------------------------------------------------------------ #
    # greater_than / less_than                                             #
    # ------------------------------------------------------------------ #

    def test_greater_than_match(self):
        doc = _doc(feedback_rating=5)
        self.assertTrue(
            self.ev.evaluate(
                doc, [{"field": "feedback_rating", "operator": "greater_than", "value": 3}]
            )
        )

    def test_greater_than_no_match(self):
        doc = _doc(feedback_rating=2)
        self.assertFalse(
            self.ev.evaluate(
                doc, [{"field": "feedback_rating", "operator": "greater_than", "value": 3}]
            )
        )

    def test_less_than_match(self):
        doc = _doc(feedback_rating=1)
        self.assertTrue(
            self.ev.evaluate(
                doc, [{"field": "feedback_rating", "operator": "less_than", "value": 3}]
            )
        )

    def test_less_than_no_match(self):
        doc = _doc(feedback_rating=5)
        self.assertFalse(
            self.ev.evaluate(
                doc, [{"field": "feedback_rating", "operator": "less_than", "value": 3}]
            )
        )

    # ------------------------------------------------------------------ #
    # is_set / is_not_set                                                  #
    # ------------------------------------------------------------------ #

    def test_is_set_with_value(self):
        doc = _doc(agent_group="Support L1")
        self.assertTrue(
            self.ev.evaluate(doc, [{"field": "agent_group", "operator": "is_set", "value": None}])
        )

    def test_is_set_with_none(self):
        doc = _doc(agent_group=None)
        self.assertFalse(
            self.ev.evaluate(doc, [{"field": "agent_group", "operator": "is_set", "value": None}])
        )

    def test_is_set_with_empty_string(self):
        doc = _doc(agent_group="")
        self.assertFalse(
            self.ev.evaluate(doc, [{"field": "agent_group", "operator": "is_set", "value": None}])
        )

    def test_is_not_set_with_none(self):
        doc = _doc(agent_group=None)
        self.assertTrue(
            self.ev.evaluate(
                doc, [{"field": "agent_group", "operator": "is_not_set", "value": None}]
            )
        )

    def test_is_not_set_with_value(self):
        doc = _doc(agent_group="Support L1")
        self.assertFalse(
            self.ev.evaluate(
                doc, [{"field": "agent_group", "operator": "is_not_set", "value": None}]
            )
        )

    # ------------------------------------------------------------------ #
    # AND / OR grouping                                                    #
    # ------------------------------------------------------------------ #

    def test_and_all_match(self):
        doc = _doc(priority="Urgent", agent_group=None)
        conditions = [
            {"field": "priority", "operator": "equals", "value": "Urgent"},
            {"field": "agent_group", "operator": "is_not_set", "value": None},
        ]
        self.assertTrue(self.ev.evaluate(doc, conditions, logic="AND"))

    def test_and_one_fails(self):
        doc = _doc(priority="Low", agent_group=None)
        conditions = [
            {"field": "priority", "operator": "equals", "value": "Urgent"},
            {"field": "agent_group", "operator": "is_not_set", "value": None},
        ]
        self.assertFalse(self.ev.evaluate(doc, conditions, logic="AND"))

    def test_or_one_matches(self):
        doc = _doc(priority="Low", agent_group=None)
        conditions = [
            {"field": "priority", "operator": "equals", "value": "Urgent"},
            {"field": "agent_group", "operator": "is_not_set", "value": None},
        ]
        self.assertTrue(self.ev.evaluate(doc, conditions, logic="OR"))

    def test_or_none_match(self):
        doc = _doc(priority="Low", agent_group="Support L1")
        conditions = [
            {"field": "priority", "operator": "equals", "value": "Urgent"},
            {"field": "agent_group", "operator": "is_not_set", "value": None},
        ]
        self.assertFalse(self.ev.evaluate(doc, conditions, logic="OR"))

    def test_nested_group(self):
        """Nested condition group with its own logic."""
        doc = _doc(priority="Urgent", agent_group=None)
        conditions = [
            {
                "logic": "OR",
                "conditions": [
                    {"field": "priority", "operator": "equals", "value": "Urgent"},
                    {"field": "priority", "operator": "equals", "value": "High"},
                ],
            },
            {"field": "agent_group", "operator": "is_not_set", "value": None},
        ]
        self.assertTrue(self.ev.evaluate(doc, conditions))

    # ------------------------------------------------------------------ #
    # Edge cases                                                           #
    # ------------------------------------------------------------------ #

    def test_empty_conditions_always_true(self):
        doc = _doc(priority="Low")
        self.assertTrue(self.ev.evaluate(doc, []))

    def test_json_string_input(self):
        import json

        doc = _doc(priority="Urgent")
        conditions_json = json.dumps(
            [{"field": "priority", "operator": "equals", "value": "Urgent"}]
        )
        self.assertTrue(self.ev.evaluate(doc, conditions_json))

    def test_invalid_json_returns_false(self):
        doc = _doc(priority="Urgent")
        self.assertFalse(self.ev.evaluate(doc, "not valid json{{{"))

    def test_missing_field_returns_false_for_equals(self):
        doc = _doc()  # no 'priority' key
        self.assertFalse(
            self.ev.evaluate(doc, [{"field": "priority", "operator": "equals", "value": "Urgent"}])
        )

    def test_unknown_operator_returns_false(self):
        doc = _doc(priority="Urgent")
        self.assertFalse(
            self.ev.evaluate(
                doc, [{"field": "priority", "operator": "regex_match", "value": "Ur.*"}]
            )
        )

    # ------------------------------------------------------------------ #
    # New UI dict format: {"logic": "...", "conditions": [...]}           #
    # ------------------------------------------------------------------ #

    def test_dict_format_or_no_match(self):
        """Dict format with OR logic: no conditions match → False."""
        import json

        doc = _doc(priority="High")
        conditions_json = json.dumps({
            "logic": "OR",
            "conditions": [
                {"field": "priority", "operator": "equals", "value": "Low"},
            ],
        })
        self.assertFalse(self.ev.evaluate(doc, conditions_json))

    def test_dict_format_or_match(self):
        """Dict format with OR logic: one condition matches → True."""
        import json

        doc = _doc(priority="High")
        conditions_json = json.dumps({
            "logic": "OR",
            "conditions": [
                {"field": "priority", "operator": "equals", "value": "Low"},
                {"field": "priority", "operator": "equals", "value": "High"},
            ],
        })
        self.assertTrue(self.ev.evaluate(doc, conditions_json))

    def test_dict_format_and_all_match(self):
        """Dict format with AND logic: all conditions match → True."""
        import json

        doc = _doc(priority="High", status="Open")
        conditions_json = json.dumps({
            "logic": "AND",
            "conditions": [
                {"field": "priority", "operator": "equals", "value": "High"},
                {"field": "status", "operator": "equals", "value": "Open"},
            ],
        })
        self.assertTrue(self.ev.evaluate(doc, conditions_json))

    def test_dict_format_and_one_fails(self):
        """Dict format with AND logic: one condition fails → False."""
        import json

        doc = _doc(priority="High", status="Closed")
        conditions_json = json.dumps({
            "logic": "AND",
            "conditions": [
                {"field": "priority", "operator": "equals", "value": "High"},
                {"field": "status", "operator": "equals", "value": "Open"},
            ],
        })
        self.assertFalse(self.ev.evaluate(doc, conditions_json))

    def test_dict_format_empty_conditions(self):
        """Dict format with empty conditions list → always True."""
        import json

        doc = _doc(priority="High")
        conditions_json = json.dumps({"logic": "AND", "conditions": []})
        self.assertTrue(self.ev.evaluate(doc, conditions_json))
