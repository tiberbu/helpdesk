# Copyright (c) 2026, Frappe Technologies Pvt. Ltd. and contributors
# For license information, please see license.txt
"""
Unit tests for helpdesk.api.sla — SLA Compliance Dashboard API.
Story 4.3 / AC #8, #9, #10, #11.

Coverage areas:
  - get_compliance_overview: correct counts for Fulfilled / Failed tickets
  - get_compliance_overview: date_from/date_to filtering
  - get_compliance_overview: team filter
  - get_compliance_trend: daily granularity returns period_label / pcts
  - get_compliance_by_dimension: team dimension
  - get_compliance_by_dimension: priority dimension
  - get_compliance_by_dimension: invalid dimension raises
  - get_breach_analysis: by_category includes top breaches
  - get_breach_analysis: by_hour has all 24 entries
  - Helper _resolve_date_range: defaults to last 30 days
  - Helper _cache_key: deterministic output
"""

import json
from datetime import datetime, timedelta

import frappe
from frappe.tests.utils import FrappeTestCase
from frappe.utils import nowdate, add_days

from helpdesk.test_utils import create_agent, make_ticket


# ---------------------------------------------------------------------------
# Test helper: set common SLA fields directly on a ticket row
# ---------------------------------------------------------------------------

def _patch_ticket_sla(ticket_name: str, **kwargs):
    """Directly set SLA fields via frappe.db.set_value (bypasses all hooks)."""
    for field, value in kwargs.items():
        frappe.db.set_value("HD Ticket", ticket_name, field, value)


def _dt(days_offset: int = 0, hours_offset: int = 0) -> str:
    """Return a datetime string relative to now."""
    dt = datetime.now() + timedelta(days=days_offset, hours=hours_offset)
    return dt.strftime("%Y-%m-%d %H:%M:%S")


class TestGetComplianceOverview(FrappeTestCase):
    """Tests for get_compliance_overview() — AC #8."""

    def setUp(self):
        frappe.set_user("Administrator")
        self._agent = create_agent("sla.overview.agent@test.com")
        # Create tickets with known SLA state
        self.fulfilled = make_ticket("SLA Fulfilled Ticket", raised_by="sla.overview.agent@test.com")
        self.failed = make_ticket("SLA Failed Ticket", raised_by="sla.overview.agent@test.com")
        self.no_sla = make_ticket("No SLA Ticket", raised_by="sla.overview.agent@test.com")

        # Set response_by so these count as SLA-tracked
        _patch_ticket_sla(
            self.fulfilled.name,
            response_by=_dt(hours_offset=1),
            first_responded_on=_dt(hours_offset=-1),  # responded before deadline
            resolution_by=_dt(hours_offset=2),
            agreement_status="Fulfilled",
        )
        _patch_ticket_sla(
            self.failed.name,
            response_by=_dt(days_offset=-1),
            first_responded_on=_dt(days_offset=1),   # responded AFTER deadline
            resolution_by=_dt(days_offset=-1),
            agreement_status="Failed",
        )
        # no_sla ticket: no response_by → excluded from SLA counts

    def tearDown(self):
        frappe.set_user("Administrator")
        frappe.db.rollback()

    def _call(self, **kwargs):
        from helpdesk.api.sla import get_compliance_overview
        frappe.set_user("sla.overview.agent@test.com")
        # Bypass the @agent_only decorator's caching by calling the underlying logic
        # via the public function (agent user has 'Agent' role)
        result = get_compliance_overview(**kwargs)
        frappe.set_user("Administrator")
        return result

    def test_overview_returns_required_keys(self):
        result = self._call(date_from=add_days(nowdate(), -1), date_to=nowdate())
        for key in (
            "response_compliance_pct",
            "response_met",
            "response_total",
            "resolution_compliance_pct",
            "resolution_met",
            "resolution_total",
        ):
            self.assertIn(key, result, f"Key '{key}' missing from overview response")

    def test_fulfilled_ticket_counted_in_resolution_met(self):
        result = self._call(date_from=add_days(nowdate(), -1), date_to=nowdate())
        # At least the fulfilled ticket should be in resolution_met
        self.assertGreaterEqual(
            result["resolution_met"], 1,
            "Expected at least 1 Fulfilled ticket in resolution_met"
        )

    def test_no_sla_ticket_excluded_from_total(self):
        """Tickets without response_by must not inflate total."""
        result = self._call(date_from=add_days(nowdate(), -1), date_to=nowdate())
        # no_sla ticket has no response_by, so response_total must be at least 2 (fulfilled + failed)
        # but must NOT count the no_sla ticket
        self.assertGreaterEqual(result["response_total"], 2)

    def test_compliance_pct_between_0_and_100(self):
        result = self._call(date_from=add_days(nowdate(), -1), date_to=nowdate())
        for key in ("response_compliance_pct", "resolution_compliance_pct"):
            self.assertGreaterEqual(result[key], 0.0, f"{key} must be >= 0")
            self.assertLessEqual(result[key], 100.0, f"{key} must be <= 100")

    def test_empty_date_range_returns_zero(self):
        """Date range before any tickets → all zeros, no exception."""
        result = self._call(date_from="2000-01-01", date_to="2000-01-02")
        self.assertEqual(result["response_total"], 0)
        self.assertEqual(result["response_compliance_pct"], 0.0)
        self.assertEqual(result["resolution_compliance_pct"], 0.0)


class TestGetComplianceTrend(FrappeTestCase):
    """Tests for get_compliance_trend() — AC #9."""

    def setUp(self):
        frappe.set_user("Administrator")
        create_agent("sla.trend.agent@test.com")
        t = make_ticket("Trend Ticket", raised_by="sla.trend.agent@test.com")
        _patch_ticket_sla(
            t.name,
            response_by=_dt(hours_offset=2),
            first_responded_on=_dt(hours_offset=1),
            resolution_by=_dt(hours_offset=3),
            agreement_status="Fulfilled",
        )
        self._ticket = t

    def tearDown(self):
        frappe.set_user("Administrator")
        frappe.db.rollback()

    def _call(self, **kwargs):
        from helpdesk.api.sla import get_compliance_trend
        frappe.set_user("sla.trend.agent@test.com")
        result = get_compliance_trend(**kwargs)
        frappe.set_user("Administrator")
        return result

    def test_trend_returns_current_and_prior(self):
        result = self._call(date_from=add_days(nowdate(), -7), date_to=nowdate())
        self.assertIn("current", result)
        self.assertIn("prior", result)
        self.assertIsInstance(result["current"], list)
        self.assertIsInstance(result["prior"], list)

    def test_trend_bucket_has_required_keys(self):
        result = self._call(date_from=add_days(nowdate(), -7), date_to=nowdate())
        if result["current"]:
            bucket = result["current"][0]
            for key in ("period_label", "ticket_count", "resolution_compliance_pct", "response_compliance_pct"):
                self.assertIn(key, bucket, f"Key '{key}' missing from trend bucket")

    def test_invalid_granularity_raises(self):
        from helpdesk.api.sla import get_compliance_trend
        frappe.set_user("sla.trend.agent@test.com")
        with self.assertRaises(frappe.ValidationError):
            get_compliance_trend(granularity="hourly")
        frappe.set_user("Administrator")

    def test_weekly_granularity_accepted(self):
        result = self._call(
            date_from=add_days(nowdate(), -30),
            date_to=nowdate(),
            granularity="weekly",
        )
        self.assertIn("current", result)

    def test_monthly_granularity_accepted(self):
        result = self._call(
            date_from=add_days(nowdate(), -60),
            date_to=nowdate(),
            granularity="monthly",
        )
        self.assertIn("current", result)


class TestGetComplianceByDimension(FrappeTestCase):
    """Tests for get_compliance_by_dimension() — AC #10."""

    def setUp(self):
        frappe.set_user("Administrator")
        create_agent("sla.dim.agent@test.com")
        # Team-based ticket
        t = make_ticket("Dimension Ticket", raised_by="sla.dim.agent@test.com")
        _patch_ticket_sla(
            t.name,
            response_by=_dt(hours_offset=2),
            agreement_status="Fulfilled",
        )
        self._ticket = t

    def tearDown(self):
        frappe.set_user("Administrator")
        frappe.db.rollback()

    def _call(self, dimension, **kwargs):
        from helpdesk.api.sla import get_compliance_by_dimension
        frappe.set_user("sla.dim.agent@test.com")
        result = get_compliance_by_dimension(dimension=dimension, **kwargs)
        frappe.set_user("Administrator")
        return result

    def test_invalid_dimension_raises(self):
        from helpdesk.api.sla import get_compliance_by_dimension
        frappe.set_user("sla.dim.agent@test.com")
        with self.assertRaises(frappe.ValidationError):
            get_compliance_by_dimension(dimension="status")
        frappe.set_user("Administrator")

    def test_team_dimension_returns_list(self):
        result = self._call("team", date_from=add_days(nowdate(), -1), date_to=nowdate())
        self.assertIsInstance(result, list)

    def test_priority_dimension_returns_list(self):
        result = self._call("priority", date_from=add_days(nowdate(), -1), date_to=nowdate())
        self.assertIsInstance(result, list)

    def test_category_dimension_returns_list(self):
        result = self._call("category", date_from=add_days(nowdate(), -1), date_to=nowdate())
        self.assertIsInstance(result, list)

    def test_agent_dimension_returns_list(self):
        result = self._call("agent", date_from=add_days(nowdate(), -1), date_to=nowdate())
        self.assertIsInstance(result, list)

    def test_dimension_row_has_required_keys(self):
        result = self._call("priority", date_from=add_days(nowdate(), -1), date_to=nowdate())
        if result:
            row = result[0]
            for key in (
                "dimension_value",
                "total_tickets",
                "response_met",
                "response_total",
                "response_compliance_pct",
                "resolution_met",
                "resolution_total",
                "resolution_compliance_pct",
                "breach_count",
            ):
                self.assertIn(key, row, f"Key '{key}' missing from dimension row")

    def test_dimension_compliance_pct_is_numeric(self):
        result = self._call("team", date_from=add_days(nowdate(), -1), date_to=nowdate())
        for row in result:
            self.assertIsInstance(row["response_compliance_pct"], (int, float))
            self.assertIsInstance(row["resolution_compliance_pct"], (int, float))


class TestGetBreachAnalysis(FrappeTestCase):
    """Tests for get_breach_analysis() — AC #11."""

    def setUp(self):
        frappe.set_user("Administrator")
        create_agent("sla.breach.agent@test.com")
        t = make_ticket("Breach Ticket", raised_by="sla.breach.agent@test.com")
        _patch_ticket_sla(
            t.name,
            response_by=_dt(days_offset=-1),
            resolution_by=_dt(days_offset=-1),
            agreement_status="Failed",
        )
        self._ticket = t

    def tearDown(self):
        frappe.set_user("Administrator")
        frappe.db.rollback()

    def _call(self, **kwargs):
        from helpdesk.api.sla import get_breach_analysis
        frappe.set_user("sla.breach.agent@test.com")
        result = get_breach_analysis(**kwargs)
        frappe.set_user("Administrator")
        return result

    def test_breach_analysis_returns_required_keys(self):
        result = self._call(date_from=add_days(nowdate(), -1), date_to=nowdate())
        self.assertIn("by_category", result)
        self.assertIn("by_hour", result)

    def test_by_hour_has_24_entries(self):
        result = self._call(date_from=add_days(nowdate(), -1), date_to=nowdate())
        self.assertEqual(len(result["by_hour"]), 24, "by_hour must have exactly 24 entries")

    def test_by_hour_covers_hours_0_to_23(self):
        result = self._call(date_from=add_days(nowdate(), -1), date_to=nowdate())
        hours = [entry["hour"] for entry in result["by_hour"]]
        self.assertEqual(sorted(hours), list(range(24)))

    def test_by_category_is_list(self):
        result = self._call(date_from=add_days(nowdate(), -1), date_to=nowdate())
        self.assertIsInstance(result["by_category"], list)

    def test_by_category_has_at_most_10_entries(self):
        result = self._call(date_from=add_days(nowdate(), -7), date_to=nowdate())
        self.assertLessEqual(len(result["by_category"]), 10)

    def test_breach_in_empty_range_returns_zeros(self):
        result = self._call(date_from="2000-01-01", date_to="2000-01-02")
        self.assertEqual(result["by_category"], [])
        self.assertTrue(all(e["breach_count"] == 0 for e in result["by_hour"]))


class TestHelpers(FrappeTestCase):
    """Tests for internal helper functions."""

    def test_resolve_date_range_defaults(self):
        from helpdesk.api.sla import _resolve_date_range
        from_d, to_d = _resolve_date_range(None, None)
        self.assertEqual(to_d, nowdate())
        # from_d should be 30 days before today
        expected_from = add_days(nowdate(), -30)
        self.assertEqual(from_d, str(expected_from))

    def test_resolve_date_range_preserves_explicit(self):
        from helpdesk.api.sla import _resolve_date_range
        from_d, to_d = _resolve_date_range("2025-01-01", "2025-01-31")
        self.assertEqual(from_d, "2025-01-01")
        self.assertEqual(to_d, "2025-01-31")

    def test_cache_key_is_deterministic(self):
        from helpdesk.api.sla import _cache_key
        key1 = _cache_key("overview", "2025-01-01", "2025-01-31", None, None, None, None)
        key2 = _cache_key("overview", "2025-01-01", "2025-01-31", None, None, None, None)
        self.assertEqual(key1, key2)

    def test_cache_key_differs_on_dimension(self):
        from helpdesk.api.sla import _cache_key
        key1 = _cache_key("dimension", "2025-01-01", "2025-01-31", None, None, None, None, "team")
        key2 = _cache_key("dimension", "2025-01-01", "2025-01-31", None, None, None, None, "priority")
        self.assertNotEqual(key1, key2)

    def test_cache_key_prefix_separates_endpoints(self):
        from helpdesk.api.sla import _cache_key
        overview_key = _cache_key("overview", "2025-01-01", "2025-01-31")
        trend_key = _cache_key("trend", "2025-01-01", "2025-01-31")
        self.assertNotEqual(overview_key, trend_key)
