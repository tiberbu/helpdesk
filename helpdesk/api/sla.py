# Copyright (c) 2026, Frappe Technologies Pvt. Ltd. and contributors
# For license information, please see license.txt
"""SLA Compliance Dashboard API — Story 4.3.

Provides four read-only analytics endpoints:
  - get_compliance_overview   (AC #8)  — overall response/resolution % cards
  - get_compliance_trend      (AC #9)  — time-series trend with prior-period comparison
  - get_compliance_by_dimension (AC #10) — drill-down by team/agent/priority/category
  - get_breach_analysis       (AC #11) — top breach categories + time-of-day distribution

Key facts about HD Ticket SLA fields (verified from hd_ticket.json):
  agreement_status : Select  — "Fulfilled" = on-time, "Failed" = breached
  response_by      : Datetime — SLA deadline for first response
  first_responded_on : Datetime — actual first response timestamp
  resolution_by    : Datetime — SLA deadline for resolution
  resolution_date  : Datetime — actual resolution timestamp
  agent_group      : Link → HD Team
  _assign          : JSON  — assigned agent email(s)
  priority         : Link → HD Ticket Priority
  category         : Link → HD Ticket Category
"""

import json
from datetime import timedelta
from functools import reduce
import operator

import frappe
from frappe import _
from frappe.query_builder import DocType
from frappe.query_builder.functions import Count, Avg, Function
from frappe.utils import getdate, add_days, date_diff, nowdate
from pypika import Case
from pypika.terms import LiteralValue

from helpdesk.utils import agent_only

# ---------------------------------------------------------------------------
# Constants
# ---------------------------------------------------------------------------
_STATUS_FULFILLED = "Fulfilled"
_STATUS_FAILED = "Failed"
_VALID_DIMENSIONS = {"team", "agent", "priority", "category"}
_VALID_GRANULARITIES = {"daily", "weekly", "monthly"}
_MAX_TREND_POINTS = 90
_CACHE_TTL_SECONDS = 300  # 5-minute Redis cache for dashboard responses


# ---------------------------------------------------------------------------
# Public API Endpoints
# ---------------------------------------------------------------------------


@frappe.whitelist()
@agent_only
def get_compliance_overview(
    date_from: str = None,
    date_to: str = None,
    team: str = None,
    agent: str = None,
    priority: str = None,
    category: str = None,
) -> dict:
    """Return overall SLA compliance percentages for the given date range and filters.

    Response compliance : first_responded_on <= response_by (both must be non-null)
    Resolution compliance : agreement_status = "Fulfilled" among tickets with SLA

    AC #8 — all tickets without SLA (response_by IS NULL) are excluded.
    """
    frappe.has_permission("HD Ticket", "read", throw=True)

    date_from, date_to = _resolve_date_range(date_from, date_to)

    cache_key = _cache_key(
        "overview", date_from, date_to, team, agent, priority, category
    )
    cached = frappe.cache().get_value(cache_key)
    if cached:
        return cached

    ticket = DocType("HD Ticket")
    base_conds = _build_base_conditions(
        ticket, date_from, date_to, team, agent, priority, category
    )
    # Only tickets that have an SLA applied (response_by IS NOT NULL)
    sla_cond = ticket.response_by.isnotnull()
    all_conds = base_conds + [sla_cond]

    combined = reduce(operator.and_, all_conds) if all_conds else None

    # --- Response compliance ---
    resp_total_q = frappe.qb.from_(ticket).select(Count("*").as_("total"))
    if combined is not None:
        resp_total_q = resp_total_q.where(combined)
    resp_total = (resp_total_q.run(as_dict=True)[0].total) or 0

    resp_met_cond = ticket.first_responded_on.isnotnull() & (
        ticket.first_responded_on <= ticket.response_by
    )
    full_resp_met_cond = (
        (combined & resp_met_cond) if combined is not None else resp_met_cond
    )
    resp_met_q = (
        frappe.qb.from_(ticket)
        .select(Count("*").as_("met"))
        .where(full_resp_met_cond)
    )
    resp_met = (resp_met_q.run(as_dict=True)[0].met) or 0

    # --- Resolution compliance ---
    res_total = resp_total  # same SLA-tracked ticket pool
    res_met_cond = ticket.agreement_status == _STATUS_FULFILLED
    full_res_met_cond = (
        (combined & res_met_cond) if combined is not None else res_met_cond
    )
    res_met_q = (
        frappe.qb.from_(ticket)
        .select(Count("*").as_("met"))
        .where(full_res_met_cond)
    )
    res_met = (res_met_q.run(as_dict=True)[0].met) or 0

    result = {
        "response_compliance_pct": round(
            (resp_met / resp_total * 100) if resp_total else 0.0, 1
        ),
        "response_met": resp_met,
        "response_total": resp_total,
        "resolution_compliance_pct": round(
            (res_met / res_total * 100) if res_total else 0.0, 1
        ),
        "resolution_met": res_met,
        "resolution_total": res_total,
    }

    frappe.cache().set_value(cache_key, result, expires_in_sec=_CACHE_TTL_SECONDS)
    return result


@frappe.whitelist()
@agent_only
def get_compliance_trend(
    date_from: str = None,
    date_to: str = None,
    granularity: str = "daily",
    team: str = None,
    agent: str = None,
    priority: str = None,
    category: str = None,
) -> dict:
    """Return compliance time-series for current and prior period.

    AC #9 — returns {"current": [...], "prior": [...]} each with
    {period_label, resolution_compliance_pct, response_compliance_pct, ticket_count}.
    Prior period spans the same duration immediately before date_from.
    Capped at _MAX_TREND_POINTS buckets per period.
    """
    frappe.has_permission("HD Ticket", "read", throw=True)

    if granularity not in _VALID_GRANULARITIES:
        frappe.throw(_("granularity must be one of: daily, weekly, monthly"))

    date_from, date_to = _resolve_date_range(date_from, date_to)

    cache_key = _cache_key(
        "trend", date_from, date_to, team, agent, priority, category, granularity
    )
    cached = frappe.cache().get_value(cache_key)
    if cached:
        return cached

    # Prior period: same duration, ending the day before date_from
    diff_days = date_diff(date_to, date_from)
    prior_date_to = add_days(date_from, -1)
    prior_date_from = add_days(prior_date_to, -diff_days)

    current_buckets = _compute_trend_buckets(
        date_from, date_to, granularity, team, agent, priority, category
    )
    prior_buckets = _compute_trend_buckets(
        prior_date_from, prior_date_to, granularity, team, agent, priority, category
    )

    result = {"current": current_buckets, "prior": prior_buckets}
    frappe.cache().set_value(cache_key, result, expires_in_sec=_CACHE_TTL_SECONDS)
    return result


@frappe.whitelist()
@agent_only
def get_compliance_by_dimension(
    dimension: str,
    date_from: str = None,
    date_to: str = None,
    team: str = None,
    agent: str = None,
    priority: str = None,
    category: str = None,
) -> list:
    """Return compliance metrics grouped by team/agent/priority/category.

    AC #10 — returns list of dicts with:
      dimension_value, total_tickets, response_met, response_total,
      response_compliance_pct, resolution_met, resolution_total,
      resolution_compliance_pct, avg_response_minutes, avg_resolution_minutes,
      breach_count
    """
    frappe.has_permission("HD Ticket", "read", throw=True)

    if dimension not in _VALID_DIMENSIONS:
        frappe.throw(_("dimension must be one of: team, agent, priority, category"))

    date_from, date_to = _resolve_date_range(date_from, date_to)

    cache_key = _cache_key(
        "dimension", date_from, date_to, team, agent, priority, category, dimension
    )
    cached = frappe.cache().get_value(cache_key)
    if cached:
        return cached

    result = _compute_dimension(
        dimension, date_from, date_to, team, agent, priority, category
    )
    frappe.cache().set_value(cache_key, result, expires_in_sec=_CACHE_TTL_SECONDS)
    return result


@frappe.whitelist()
@agent_only
def get_breach_analysis(
    date_from: str = None,
    date_to: str = None,
    team: str = None,
    agent: str = None,
    priority: str = None,
    category: str = None,
) -> dict:
    """Return breach analysis: top categories + hourly distribution.

    AC #11 — returns {"by_category": [...], "by_hour": [...]}
      by_category: [{category, breach_count}] top 10 desc
      by_hour: [{hour, breach_count}] for hours 0-23 (all hours included)
    """
    frappe.has_permission("HD Ticket", "read", throw=True)

    date_from, date_to = _resolve_date_range(date_from, date_to)

    cache_key = _cache_key(
        "breach", date_from, date_to, team, agent, priority, category
    )
    cached = frappe.cache().get_value(cache_key)
    if cached:
        return cached

    ticket = DocType("HD Ticket")
    base_conds = _build_base_conditions(
        ticket, date_from, date_to, team, agent, priority, category
    )
    breach_cond = ticket.agreement_status == _STATUS_FAILED
    all_conds = base_conds + [breach_cond]
    combined = reduce(operator.and_, all_conds) if all_conds else None

    # --- By category (top 10) ---
    cat_q = (
        frappe.qb.from_(ticket)
        .select(
            Function("COALESCE", ticket.category, "Uncategorized").as_("category"),
            Count("*").as_("breach_count"),
        )
        .groupby(Function("COALESCE", ticket.category, "Uncategorized"))
        .orderby(Count("*"), order=frappe.qb.desc)
        .limit(10)
    )
    if combined is not None:
        cat_q = cat_q.where(combined)
    by_category = cat_q.run(as_dict=True)

    # --- By hour (0-23) ---
    hour_q = (
        frappe.qb.from_(ticket)
        .select(
            Function("HOUR", ticket.creation).as_("hour"),
            Count("*").as_("breach_count"),
        )
        .groupby(Function("HOUR", ticket.creation))
    )
    if combined is not None:
        hour_q = hour_q.where(combined)
    hour_rows = hour_q.run(as_dict=True)

    # Fill all 24 hours, defaulting missing hours to 0
    hour_map = {int(r["hour"]): int(r["breach_count"]) for r in hour_rows}
    by_hour = [{"hour": h, "breach_count": hour_map.get(h, 0)} for h in range(24)]

    result = {
        "by_category": [
            {"category": r["category"], "breach_count": int(r["breach_count"])}
            for r in by_category
        ],
        "by_hour": by_hour,
    }
    frappe.cache().set_value(cache_key, result, expires_in_sec=_CACHE_TTL_SECONDS)
    return result


# ---------------------------------------------------------------------------
# Internal helpers
# ---------------------------------------------------------------------------


def _resolve_date_range(date_from, date_to):
    """Return (date_from, date_to) strings, defaulting to last 30 days."""
    if not date_to:
        date_to = nowdate()
    if not date_from:
        date_from = add_days(date_to, -30)
    return str(date_from), str(date_to)


def _cache_key(*parts) -> str:
    """Build a deterministic cache key from all filter params."""
    return "sla_compliance:" + ":".join(
        str(p) if p is not None else "" for p in parts
    )


def _build_base_conditions(ticket, date_from, date_to, team, agent, priority, category):
    """Return list of frappe.qb WHERE conditions for the common filters."""
    conds = []

    # Date range: filter on creation date (when ticket entered SLA clock)
    conds.append(ticket.creation >= date_from)
    conds.append(ticket.creation <= date_to + " 23:59:59")

    if team:
        conds.append(ticket.agent_group == team)

    if agent:
        # _assign is JSON like '["agent@example.com"]' — use JSON_SEARCH
        conds.append(
            Function("JSON_SEARCH", ticket._assign, "one", agent).isnotnull()
        )

    if priority:
        conds.append(ticket.priority == priority)

    if category:
        conds.append(ticket.category == category)

    return conds


def _compute_trend_buckets(date_from, date_to, granularity, team, agent, priority, category):
    """Compute compliance trend buckets for a given date range.

    Returns a list of dicts with:
      period_label, resolution_compliance_pct, response_compliance_pct, ticket_count
    """
    ticket = DocType("HD Ticket")
    base_conds = _build_base_conditions(
        ticket, date_from, date_to, team, agent, priority, category
    )
    sla_cond = ticket.response_by.isnotnull()
    all_conds = base_conds + [sla_cond]
    combined = reduce(operator.and_, all_conds) if all_conds else None

    if granularity == "daily":
        group_expr = Function("DATE", ticket.creation).as_("period_label")
        group_by_expr = Function("DATE", ticket.creation)
    elif granularity == "weekly":
        # YEARWEEK returns YYYYWW — readable enough for the frontend label
        group_expr = Function("YEARWEEK", ticket.creation, 1).as_("period_label")
        group_by_expr = Function("YEARWEEK", ticket.creation, 1)
    else:  # monthly
        group_expr = Function(
            "DATE_FORMAT", ticket.creation, "%Y-%m"
        ).as_("period_label")
        group_by_expr = Function("DATE_FORMAT", ticket.creation, "%Y-%m")

    q = (
        frappe.qb.from_(ticket)
        .select(
            group_expr,
            Count("*").as_("ticket_count"),
            Count(
                Case()
                .when(ticket.agreement_status == _STATUS_FULFILLED, ticket.name)
                .else_(None)
            ).as_("resolution_met"),
            Count(
                Case()
                .when(
                    ticket.first_responded_on.isnotnull()
                    & (ticket.first_responded_on <= ticket.response_by),
                    ticket.name,
                )
                .else_(None)
            ).as_("response_met"),
        )
        .groupby(group_by_expr)
        .orderby(group_by_expr)
        .limit(_MAX_TREND_POINTS)
    )
    if combined is not None:
        q = q.where(combined)

    rows = q.run(as_dict=True)

    result = []
    for r in rows:
        total = int(r.get("ticket_count") or 0)
        res_met = int(r.get("resolution_met") or 0)
        resp_met = int(r.get("response_met") or 0)
        result.append(
            {
                "period_label": str(r.get("period_label", "")),
                "ticket_count": total,
                "resolution_compliance_pct": round(
                    (res_met / total * 100) if total else 0.0, 1
                ),
                "response_compliance_pct": round(
                    (resp_met / total * 100) if total else 0.0, 1
                ),
            }
        )
    return result


def _compute_dimension(dimension, date_from, date_to, team, agent, priority, category):
    """Compute compliance metrics grouped by the requested dimension.

    For "agent" dimension, uses Python-level grouping since _assign is JSON.
    For other dimensions, uses frappe.qb GROUP BY.
    """
    if dimension == "agent":
        return _compute_agent_dimension(
            date_from, date_to, team, agent, priority, category
        )

    ticket = DocType("HD Ticket")
    base_conds = _build_base_conditions(
        ticket, date_from, date_to, team, agent, priority, category
    )
    sla_cond = ticket.response_by.isnotnull()
    all_conds = base_conds + [sla_cond]
    combined = reduce(operator.and_, all_conds) if all_conds else None

    dim_field_map = {
        "team": ticket.agent_group,
        "priority": ticket.priority,
        "category": ticket.category,
    }
    dim_field = dim_field_map[dimension]

    q = (
        frappe.qb.from_(ticket)
        .select(
            dim_field.as_("dimension_value"),
            Count("*").as_("total_tickets"),
            Count(
                Case()
                .when(ticket.agreement_status == _STATUS_FULFILLED, ticket.name)
                .else_(None)
            ).as_("resolution_met"),
            Count(
                Case()
                .when(ticket.agreement_status == _STATUS_FAILED, ticket.name)
                .else_(None)
            ).as_("breach_count"),
            Count(
                Case()
                .when(
                    ticket.first_responded_on.isnotnull()
                    & (ticket.first_responded_on <= ticket.response_by),
                    ticket.name,
                )
                .else_(None)
            ).as_("response_met"),
            # avg_response_minutes: calendar minutes from creation to first response
            Avg(
                Case()
                .when(
                    ticket.first_responded_on.isnotnull(),
                    Function(
                        "TIMESTAMPDIFF",
                        LiteralValue("MINUTE"),
                        ticket.creation,
                        ticket.first_responded_on,
                    ),
                )
                .else_(None)
            ).as_("avg_response_minutes"),
            # avg_resolution_minutes: calendar minutes from creation to resolution
            Avg(
                Case()
                .when(
                    ticket.resolution_date.isnotnull(),
                    Function(
                        "TIMESTAMPDIFF",
                        LiteralValue("MINUTE"),
                        ticket.creation,
                        ticket.resolution_date,
                    ),
                )
                .else_(None)
            ).as_("avg_resolution_minutes"),
        )
        .groupby(dim_field)
        .orderby(Count("*"), order=frappe.qb.desc)
    )
    if combined is not None:
        q = q.where(combined)

    rows = q.run(as_dict=True)
    return [_format_dimension_row(r) for r in rows]


def _compute_agent_dimension(date_from, date_to, team, agent, priority, category):
    """Compute agent-level compliance using Python-level grouping.

    Since _assign is a JSON array, GROUP BY in SQL is impractical.
    We fetch all tickets and aggregate per unique agent email.
    """
    ticket = DocType("HD Ticket")
    base_conds = _build_base_conditions(
        ticket, date_from, date_to, team, agent, priority, category
    )
    sla_cond = ticket.response_by.isnotnull()
    all_conds = base_conds + [sla_cond]
    combined = reduce(operator.and_, all_conds) if all_conds else None

    q = (
        frappe.qb.from_(ticket)
        .select(
            ticket._assign,
            ticket.agreement_status,
            ticket.first_responded_on,
            ticket.response_by,
            ticket.creation,
            ticket.resolution_date,
        )
    )
    if combined is not None:
        q = q.where(combined)

    rows = q.run(as_dict=True)

    # Aggregate per agent email
    agents: dict = {}
    for r in rows:
        assign_val = r.get("_assign") or "[]"
        try:
            assign_list = json.loads(assign_val) if isinstance(assign_val, str) else (assign_val or [])
        except (json.JSONDecodeError, TypeError):
            assign_list = []

        if not assign_list:
            assign_list = ["Unassigned"]

        for email in assign_list:
            if email not in agents:
                agents[email] = {
                    "dimension_value": email,
                    "total_tickets": 0,
                    "resolution_met": 0,
                    "response_met": 0,
                    "breach_count": 0,
                    "response_minutes_sum": 0.0,
                    "response_minutes_count": 0,
                    "resolution_minutes_sum": 0.0,
                    "resolution_minutes_count": 0,
                }
            a = agents[email]
            a["total_tickets"] += 1

            if r.get("agreement_status") == _STATUS_FULFILLED:
                a["resolution_met"] += 1
            if r.get("agreement_status") == _STATUS_FAILED:
                a["breach_count"] += 1

            if r.get("first_responded_on") and r.get("response_by"):
                if r["first_responded_on"] <= r["response_by"]:
                    a["response_met"] += 1
                # Avg response minutes
                from frappe.utils import get_datetime
                try:
                    delta = get_datetime(r["first_responded_on"]) - get_datetime(r["creation"])
                    a["response_minutes_sum"] += delta.total_seconds() / 60
                    a["response_minutes_count"] += 1
                except Exception:
                    pass

            if r.get("resolution_date") and r.get("creation"):
                from frappe.utils import get_datetime
                try:
                    delta = get_datetime(r["resolution_date"]) - get_datetime(r["creation"])
                    a["resolution_minutes_sum"] += delta.total_seconds() / 60
                    a["resolution_minutes_count"] += 1
                except Exception:
                    pass

    result = []
    for email, a in sorted(agents.items(), key=lambda x: -x[1]["total_tickets"]):
        total = a["total_tickets"]
        result.append(
            _format_dimension_row(
                {
                    "dimension_value": email,
                    "total_tickets": total,
                    "resolution_met": a["resolution_met"],
                    "response_met": a["response_met"],
                    "breach_count": a["breach_count"],
                    "avg_response_minutes": (
                        a["response_minutes_sum"] / a["response_minutes_count"]
                        if a["response_minutes_count"]
                        else None
                    ),
                    "avg_resolution_minutes": (
                        a["resolution_minutes_sum"] / a["resolution_minutes_count"]
                        if a["resolution_minutes_count"]
                        else None
                    ),
                }
            )
        )
    return result


def _format_dimension_row(r: dict) -> dict:
    """Normalize a raw query row into the standard dimension response format."""
    total = int(r.get("total_tickets") or 0)
    res_met = int(r.get("resolution_met") or 0)
    resp_met = int(r.get("response_met") or 0)
    breach = int(r.get("breach_count") or 0)

    avg_resp = r.get("avg_response_minutes")
    avg_res = r.get("avg_resolution_minutes")

    return {
        "dimension_value": r.get("dimension_value") or _("Unassigned"),
        "total_tickets": total,
        "response_met": resp_met,
        "response_total": total,
        "response_compliance_pct": round(
            (resp_met / total * 100) if total else 0.0, 1
        ),
        "resolution_met": res_met,
        "resolution_total": total,
        "resolution_compliance_pct": round(
            (res_met / total * 100) if total else 0.0, 1
        ),
        "avg_response_minutes": round(float(avg_resp), 1) if avg_resp is not None else None,
        "avg_resolution_minutes": round(float(avg_res), 1) if avg_res is not None else None,
        "breach_count": breach,
    }
