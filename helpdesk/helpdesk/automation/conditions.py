# Copyright (c) 2026, Frappe Technologies Pvt. Ltd. and contributors
# For license information, please see license.txt

"""Condition evaluator for HD Automation Rules.

Supports AND/OR logical grouping and the following per-condition operators:
    equals, not_equals, contains, greater_than, less_than, is_set, is_not_set
"""

import json
from typing import Any

import frappe
from frappe import _


# Set of valid operators
VALID_OPERATORS = frozenset(
    {
        "equals",
        "not_equals",
        "contains",
        "greater_than",
        "less_than",
        "is_set",
        "is_not_set",
    }
)


class ConditionEvaluator:
    """Evaluates a list of conditions against an HD Ticket document.

    Condition JSON format (single condition)::

        {"field": "priority", "operator": "equals", "value": "Urgent"}

    Condition group with OR logic::

        {"logic": "OR", "conditions": [
            {"field": "priority", "operator": "equals", "value": "Urgent"},
            {"field": "priority", "operator": "equals", "value": "High"}
        ]}

    Top-level list uses AND by default (all conditions must match).
    Pass ``logic="OR"`` as keyword argument to use OR at top level.
    """

    def evaluate(self, ticket, conditions_raw: list | str, logic: str = "AND") -> bool:
        """Evaluate conditions against a ticket document.

        Args:
            ticket: HD Ticket frappe.Document or frappe._dict.
            conditions_raw: List of condition dicts, or a JSON string.
            logic: Top-level logical operator — "AND" (default) or "OR".

        Returns:
            True if conditions match the ticket, False otherwise.
        """
        if isinstance(conditions_raw, str):
            try:
                conditions = json.loads(conditions_raw)
            except (json.JSONDecodeError, TypeError):
                frappe.log_error(
                    title="AutomationRule: invalid conditions JSON",
                    message=str(conditions_raw),
                )
                return False
        else:
            conditions = conditions_raw

        # Unwrap the new UI format: {"logic": "OR", "conditions": [...]}
        if isinstance(conditions, dict):
            logic = conditions.get("logic", logic).upper()
            conditions = conditions.get("conditions", [])

        if not conditions:
            # Empty conditions → always match (unconditional rule)
            return True

        results = []
        for cond in conditions:
            if not isinstance(cond, dict):
                continue
            # Nested condition group
            if "conditions" in cond:
                group_logic = cond.get("logic", "AND").upper()
                group_result = self.evaluate(ticket, cond["conditions"], logic=group_logic)
                results.append(group_result)
            else:
                results.append(self._evaluate_single(ticket, cond))

        if not results:
            return True

        if logic.upper() == "OR":
            return any(results)
        return all(results)

    def _evaluate_single(self, ticket, condition: dict) -> bool:
        """Evaluate a single condition dict against the ticket."""
        field = condition.get("field", "")
        operator = condition.get("operator", "")
        expected = condition.get("value")

        if operator not in VALID_OPERATORS:
            frappe.log_error(
                title="AutomationRule: unknown operator",
                message=f"Operator '{operator}' is not supported.",
            )
            return False

        # Fetch actual value from ticket; use getattr for Document objects
        # and dict-style access for frappe._dict / plain dicts.
        if hasattr(ticket, field):
            actual = getattr(ticket, field)
        elif isinstance(ticket, dict):
            actual = ticket.get(field)
        else:
            actual = None

        return self._apply_operator(operator, actual, expected)

    def _apply_operator(self, operator: str, actual: Any, expected: Any) -> bool:
        """Apply the comparison operator and return True/False."""
        if operator == "is_set":
            return actual is not None and actual != "" and actual != 0

        if operator == "is_not_set":
            return actual is None or actual == "" or actual == 0

        if operator == "equals":
            return str(actual) == str(expected) if actual is not None else expected is None

        if operator == "not_equals":
            return str(actual) != str(expected) if actual is not None else expected is not None

        if operator == "contains":
            if actual is None:
                return False
            return str(expected).lower() in str(actual).lower()

        if operator == "greater_than":
            try:
                return float(actual) > float(expected)
            except (TypeError, ValueError):
                return str(actual) > str(expected)

        if operator == "less_than":
            try:
                return float(actual) < float(expected)
            except (TypeError, ValueError):
                return str(actual) < str(expected)

        return False
