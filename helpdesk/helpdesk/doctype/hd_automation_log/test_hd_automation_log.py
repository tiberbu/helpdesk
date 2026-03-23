# Copyright (c) 2026, Frappe Technologies Pvt. Ltd. and contributors
# For license information, please see license.txt

"""Unit tests for HD Automation Log DocType, cleanup, and execution stats API.

Covers:
    AC#1  - HD Automation Log DocType exists with required fields
    AC#2  - Log created on success/skipped paths
    AC#3  - Log created with status=failure and error_message on failure
    AC#4  - get_execution_stats() returns correct counts, last_fired, failure_rate
    AC#7  - purge_old_logs() deletes records older than retention period
    AC#8  - purge_old_logs() reads log_retention_days from HD Settings
    AC#9  - Unit test coverage for all above
"""

import json
from datetime import timedelta
from unittest.mock import patch

import frappe
from frappe.tests.utils import FrappeTestCase
from frappe.utils import now_datetime, add_days

from helpdesk.helpdesk.doctype.hd_automation_log.cleanup import purge_old_logs
from helpdesk.helpdesk.automation.engine import _create_log


def _make_rule(name_suffix=""):
    """Create a minimal HD Automation Rule for testing."""
    return frappe.get_doc(
        {
            "doctype": "HD Automation Rule",
            "rule_name": f"log-test-{frappe.generate_hash(length=6)}{name_suffix}",
            "trigger_type": "ticket_created",
            "enabled": 1,
            "conditions": "[]",
            "actions": "[]",
            "failure_count": 0,
        }
    ).insert(ignore_permissions=True)


def _insert_log(rule_name, status="success", timestamp=None, ticket=None, error_message=""):
    """Directly insert an HD Automation Log record for testing."""
    return frappe.get_doc(
        {
            "doctype": "HD Automation Log",
            "rule_name": rule_name,
            "ticket": ticket,
            "trigger_event": "ticket_created",
            "conditions_evaluated": "[]",
            "actions_executed": "[]",
            "execution_time_ms": 5,
            "status": status,
            "error_message": error_message,
            "timestamp": timestamp or now_datetime(),
        }
    ).insert(ignore_permissions=True)


class TestHDAutomationLogDocType(FrappeTestCase):
    """Tests for HD Automation Log DocType field structure and creation."""

    def setUp(self):
        frappe.set_user("Administrator")
        self._rules = []
        self._logs = []

    def tearDown(self):
        frappe.set_user("Administrator")
        for log in self._logs:
            if frappe.db.exists("HD Automation Log", log):
                frappe.delete_doc("HD Automation Log", log, ignore_permissions=True)
        for rule in self._rules:
            if frappe.db.exists("HD Automation Rule", rule):
                frappe.delete_doc("HD Automation Rule", rule, ignore_permissions=True)
        frappe.db.commit()  # nosemgrep

    def test_doctype_exists(self):
        """HD Automation Log DocType must exist."""
        self.assertTrue(frappe.db.exists("DocType", "HD Automation Log"))

    def test_required_fields_present(self):
        """All required fields must be present in the DocType definition."""
        meta = frappe.get_meta("HD Automation Log")
        fieldnames = {f.fieldname for f in meta.fields}
        required = {
            "rule_name",
            "ticket",
            "trigger_event",
            "conditions_evaluated",
            "actions_executed",
            "execution_time_ms",
            "status",
            "error_message",
            "timestamp",
        }
        for field in required:
            self.assertIn(field, fieldnames, f"Field '{field}' missing from HD Automation Log")

    def test_insert_success_log(self):
        """A success log record can be inserted programmatically."""
        rule = _make_rule()
        self._rules.append(rule.name)

        log = _insert_log(rule.name, status="success")
        self._logs.append(log.name)

        fetched = frappe.get_doc("HD Automation Log", log.name)
        self.assertEqual(fetched.status, "success")
        self.assertEqual(fetched.rule_name, rule.name)

    def test_insert_failure_log_captures_error(self):
        """A failure log record stores the error_message correctly."""
        rule = _make_rule()
        self._rules.append(rule.name)

        log = _insert_log(rule.name, status="failure", error_message="Action timed out")
        self._logs.append(log.name)

        fetched = frappe.get_doc("HD Automation Log", log.name)
        self.assertEqual(fetched.status, "failure")
        self.assertEqual(fetched.error_message, "Action timed out")

    def test_insert_skipped_log(self):
        """A skipped log record (conditions not matched) can be inserted."""
        rule = _make_rule()
        self._rules.append(rule.name)

        log = _insert_log(rule.name, status="skipped")
        self._logs.append(log.name)

        fetched = frappe.get_doc("HD Automation Log", log.name)
        self.assertEqual(fetched.status, "skipped")


class TestCreateLogHelper(FrappeTestCase):
    """Tests for the engine._create_log() internal helper."""

    def setUp(self):
        frappe.set_user("Administrator")
        self._rules = []
        self._logs_before = set(frappe.db.get_all("HD Automation Log", pluck="name"))

    def tearDown(self):
        frappe.set_user("Administrator")
        new_logs = set(frappe.db.get_all("HD Automation Log", pluck="name")) - self._logs_before
        for log in new_logs:
            frappe.delete_doc("HD Automation Log", log, ignore_permissions=True)
        for rule in self._rules:
            if frappe.db.exists("HD Automation Rule", rule):
                frappe.delete_doc("HD Automation Rule", rule, ignore_permissions=True)
        frappe.db.commit()  # nosemgrep

    def test_create_log_success(self):
        """_create_log() creates a success record in DB."""
        rule = _make_rule()
        self._rules.append(rule.name)

        _create_log(
            rule_name=rule.name,
            ticket=None,
            trigger_event="ticket_created",
            conditions_evaluated="[]",
            actions_executed="[]",
            execution_time_ms=10,
            status="success",
        )

        logs = frappe.db.get_all(
            "HD Automation Log",
            filters={"rule_name": rule.name, "status": "success"},
            fields=["name", "execution_time_ms", "trigger_event"],
        )
        self.assertEqual(len(logs), 1)
        self.assertEqual(logs[0]["execution_time_ms"], 10)
        self.assertEqual(logs[0]["trigger_event"], "ticket_created")

    def test_create_log_failure_stores_error(self):
        """_create_log() with status=failure stores the error_message."""
        rule = _make_rule()
        self._rules.append(rule.name)

        _create_log(
            rule_name=rule.name,
            ticket=None,
            trigger_event="ticket_updated",
            conditions_evaluated="[]",
            actions_executed="[]",
            execution_time_ms=3,
            status="failure",
            error_message="Something broke",
        )

        logs = frappe.db.get_all(
            "HD Automation Log",
            filters={"rule_name": rule.name, "status": "failure"},
            fields=["error_message"],
        )
        self.assertEqual(len(logs), 1)
        self.assertEqual(logs[0]["error_message"], "Something broke")

    def test_create_log_swallows_exceptions(self):
        """_create_log() must not raise even if insert fails (e.g. bad rule_name)."""
        # Passing a non-existent rule_name; should not raise
        try:
            _create_log(
                rule_name="non-existent-rule-xyz",
                ticket=None,
                trigger_event="ticket_created",
                conditions_evaluated="[]",
                actions_executed="[]",
                execution_time_ms=0,
                status="success",
            )
        except Exception as e:
            self.fail(f"_create_log() raised an unexpected exception: {e}")


class TestPurgeOldLogs(FrappeTestCase):
    """Tests for cleanup.purge_old_logs()."""

    def setUp(self):
        frappe.set_user("Administrator")
        self._rules = []
        self._log_names = []

    def tearDown(self):
        frappe.set_user("Administrator")
        for log in self._log_names:
            if frappe.db.exists("HD Automation Log", log):
                frappe.delete_doc("HD Automation Log", log, ignore_permissions=True)
        for rule in self._rules:
            if frappe.db.exists("HD Automation Rule", rule):
                frappe.delete_doc("HD Automation Rule", rule, ignore_permissions=True)
        frappe.db.commit()  # nosemgrep

    def test_purge_deletes_old_logs(self):
        """Records older than retention_days must be deleted."""
        rule = _make_rule()
        self._rules.append(rule.name)

        # Insert one old log (35 days ago) and one recent log (1 day ago)
        old_ts = add_days(now_datetime(), -35)
        recent_ts = add_days(now_datetime(), -1)

        old_log = _insert_log(rule.name, status="success", timestamp=old_ts)
        recent_log = _insert_log(rule.name, status="success", timestamp=recent_ts)
        self._log_names.extend([old_log.name, recent_log.name])

        # Set retention to 30 days
        frappe.db.set_single_value("HD Settings", "log_retention_days", 30)

        purge_old_logs()

        # Old log must be gone
        self.assertFalse(frappe.db.exists("HD Automation Log", old_log.name))
        # Recent log must remain
        self.assertTrue(frappe.db.exists("HD Automation Log", recent_log.name))

    def test_purge_respects_configured_retention(self):
        """purge_old_logs() reads log_retention_days from HD Settings."""
        rule = _make_rule()
        self._rules.append(rule.name)

        # Log from 10 days ago
        ts_10d = add_days(now_datetime(), -10)
        log = _insert_log(rule.name, status="success", timestamp=ts_10d)
        self._log_names.append(log.name)

        # Set retention to 7 days → 10-day-old log should be deleted
        frappe.db.set_single_value("HD Settings", "log_retention_days", 7)

        purge_old_logs()

        self.assertFalse(frappe.db.exists("HD Automation Log", log.name))

    def test_purge_defaults_to_30_days_when_null(self):
        """purge_old_logs() falls back to 30-day retention when setting is null."""
        rule = _make_rule()
        self._rules.append(rule.name)

        # Log from 25 days ago — should survive with default 30-day retention
        ts_25d = add_days(now_datetime(), -25)
        log = _insert_log(rule.name, status="success", timestamp=ts_25d)
        self._log_names.append(log.name)

        # Clear the setting to force fallback
        frappe.db.set_single_value("HD Settings", "log_retention_days", None)

        purge_old_logs()

        # 25 days < 30 days default retention → must still exist
        self.assertTrue(frappe.db.exists("HD Automation Log", log.name))

    def test_purge_does_not_delete_recent_logs(self):
        """Logs within the retention window must not be deleted."""
        rule = _make_rule()
        self._rules.append(rule.name)

        log = _insert_log(rule.name, status="success")  # just now
        self._log_names.append(log.name)

        frappe.db.set_single_value("HD Settings", "log_retention_days", 30)

        purge_old_logs()

        self.assertTrue(frappe.db.exists("HD Automation Log", log.name))


class TestGetExecutionStats(FrappeTestCase):
    """Tests for helpdesk.api.automation.get_execution_stats()."""

    def setUp(self):
        frappe.set_user("Administrator")
        self._rules = []
        self._log_names = []

    def tearDown(self):
        frappe.set_user("Administrator")
        for log in self._log_names:
            if frappe.db.exists("HD Automation Log", log):
                frappe.delete_doc("HD Automation Log", log, ignore_permissions=True)
        for rule in self._rules:
            if frappe.db.exists("HD Automation Rule", rule):
                frappe.delete_doc("HD Automation Rule", rule, ignore_permissions=True)
        frappe.db.commit()  # nosemgrep

    def _get_stats_for(self, rule_name):
        """Helper: call get_execution_stats and return stats entry for a specific rule."""
        from helpdesk.api.automation import get_execution_stats
        results = get_execution_stats()
        for r in results:
            if r["name"] == rule_name:
                return r
        return None

    def test_stats_zero_for_rule_with_no_logs(self):
        """A rule with no log entries must return execution_count=0, failure_rate=0."""
        rule = _make_rule()
        self._rules.append(rule.name)

        stat = self._get_stats_for(rule.name)
        self.assertIsNotNone(stat)
        self.assertEqual(stat["execution_count"], 0)
        self.assertIsNone(stat["last_fired"])
        self.assertEqual(stat["failure_rate"], 0.0)

    def test_stats_execution_count(self):
        """execution_count must match total log entries for the rule."""
        rule = _make_rule()
        self._rules.append(rule.name)

        for _ in range(5):
            log = _insert_log(rule.name, status="success")
            self._log_names.append(log.name)

        stat = self._get_stats_for(rule.name)
        self.assertEqual(stat["execution_count"], 5)

    def test_stats_failure_rate_calculation(self):
        """failure_rate = (failures / total) * 100, rounded to 1 decimal."""
        rule = _make_rule()
        self._rules.append(rule.name)

        # 3 failures, 7 successes → 30.0%
        for _ in range(3):
            log = _insert_log(rule.name, status="failure")
            self._log_names.append(log.name)
        for _ in range(7):
            log = _insert_log(rule.name, status="success")
            self._log_names.append(log.name)

        stat = self._get_stats_for(rule.name)
        self.assertEqual(stat["execution_count"], 10)
        self.assertEqual(stat["failure_rate"], 30.0)

    def test_stats_last_fired_is_most_recent(self):
        """last_fired must be the timestamp of the most recent log entry."""
        rule = _make_rule()
        self._rules.append(rule.name)

        old_ts = add_days(now_datetime(), -5)
        recent_ts = add_days(now_datetime(), -1)

        log_old = _insert_log(rule.name, status="success", timestamp=old_ts)
        log_recent = _insert_log(rule.name, status="success", timestamp=recent_ts)
        self._log_names.extend([log_old.name, log_recent.name])

        stat = self._get_stats_for(rule.name)
        self.assertIsNotNone(stat["last_fired"])
        # last_fired should be close to recent_ts (within a few seconds)
        from datetime import datetime
        last_fired_dt = datetime.fromisoformat(str(stat["last_fired"]).replace(" ", "T"))
        diff = abs((last_fired_dt - recent_ts.replace(tzinfo=None)).total_seconds())
        self.assertLess(diff, 5, "last_fired should match the most recent log timestamp")

    def test_stats_100_percent_failure_rate(self):
        """A rule with all failures must return failure_rate=100.0."""
        rule = _make_rule()
        self._rules.append(rule.name)

        for _ in range(4):
            log = _insert_log(rule.name, status="failure")
            self._log_names.append(log.name)

        stat = self._get_stats_for(rule.name)
        self.assertEqual(stat["failure_rate"], 100.0)
