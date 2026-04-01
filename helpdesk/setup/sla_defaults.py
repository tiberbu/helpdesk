"""
Shared SLA defaults seed module.

Creates the 4 default HD Service Level Agreement entries for each support
level in the Kenya administrative hierarchy.  Consumed by both the
after_install hook and migration patches.

Safe to call multiple times (idempotent).
"""

import frappe

# Durations stored in seconds (Frappe Duration fieldtype)
_MIN = 60
_HR = 3600

SLA_DEFINITIONS = [
    {
        "service_level": "L0 Sub-County SLA",
        "description": "Sub-county first-line support — 30 min first response, 4 hr resolution",
        "response_time": 30 * _MIN,   # 1800
        "resolution_time": 4 * _HR,   # 14400
        "agreement_type": "OLA",
        "support_level_tag": "L0 - Sub-County",
    },
    {
        "service_level": "L1 County SLA",
        "description": "County support — 1 hr first response, 8 hr resolution",
        "response_time": 1 * _HR,     # 3600
        "resolution_time": 8 * _HR,   # 28800
        "agreement_type": "SLA",
        "support_level_tag": "L1 - County",
    },
    {
        "service_level": "L2 National SLA",
        "description": "National support — 2 hr first response, 24 hr resolution",
        "response_time": 2 * _HR,     # 7200
        "resolution_time": 24 * _HR,  # 86400
        "agreement_type": "SLA",
        "support_level_tag": "L2 - National",
    },
    {
        "service_level": "L3 Engineering SLA",
        "description": "Engineering escalation — 4 hr first response, 72 hr resolution",
        "response_time": 4 * _HR,     # 14400
        "resolution_time": 72 * _HR,  # 259200
        "agreement_type": "SLA",
        "support_level_tag": "L3 - Engineering",
    },
]

# 24/7 working hours: all 7 days, 00:00 – 23:59
_ALL_DAYS = [
    "Monday",
    "Tuesday",
    "Wednesday",
    "Thursday",
    "Friday",
    "Saturday",
    "Sunday",
]


def _ensure_holiday_list() -> str:
    """Return the name of a usable HD Service Holiday List, creating one if needed."""
    existing = frappe.db.get_value("HD Service Holiday List", {}, "name")
    if existing:
        return existing

    hl = frappe.get_doc(
        {
            "doctype": "HD Service Holiday List",
            "holiday_list_name": "Kenya Default Holiday List",
            "from_date": "2024-01-01",
            "to_date": "2030-12-31",
            "holidays": [
                {"description": "New Year's Day", "holiday_date": "2024-01-01"},
                {"description": "Good Friday", "holiday_date": "2024-03-29"},
                {"description": "Easter Monday", "holiday_date": "2024-04-01"},
                {"description": "Labour Day", "holiday_date": "2024-05-01"},
                {"description": "Madaraka Day", "holiday_date": "2024-06-01"},
                {"description": "Utamaduni Day", "holiday_date": "2024-10-10"},
                {"description": "Mashujaa Day", "holiday_date": "2024-10-20"},
                {"description": "Jamhuri Day", "holiday_date": "2024-12-12"},
                {"description": "Christmas Day", "holiday_date": "2024-12-25"},
                {"description": "Boxing Day", "holiday_date": "2024-12-26"},
            ],
        }
    )
    hl.insert(ignore_permissions=True)
    return hl.name


def _get_or_create_priority() -> str:
    """Return the name of the first HD Ticket Priority, creating 'Medium' if none exists."""
    existing = frappe.db.get_value("HD Ticket Priority", {}, "name")
    if existing:
        return existing

    prio = frappe.get_doc(
        {
            "doctype": "HD Ticket Priority",
            "name": "Medium",
            "integer_value": 2,
        }
    )
    prio.insert(ignore_permissions=True)
    return "Medium"


def seed_sla_configs() -> None:
    """
    Create HD Service Level Agreement entries for each Kenya support level.

    Creates:
      - L0 Sub-County SLA  (30 min response, 4 hr resolution)
      - L1 County SLA      (1 hr response, 8 hr resolution)
      - L2 National SLA    (2 hr response, 24 hr resolution)
      - L3 Engineering SLA (4 hr response, 72 hr resolution)

    Idempotent — safe to call multiple times.
    """
    holiday_list = _ensure_holiday_list()
    priority = _get_or_create_priority()

    # Build 24/7 working hours rows
    working_hours = [
        {
            "workday": day,
            "start_time": "00:00:00",
            "end_time": "23:59:00",
        }
        for day in _ALL_DAYS
    ]

    for sla_def in SLA_DEFINITIONS:
        if frappe.db.exists("HD Service Level Agreement", sla_def["service_level"]):
            continue

        doc = frappe.get_doc(
            {
                "doctype": "HD Service Level Agreement",
                "service_level": sla_def["service_level"],
                "description": sla_def["description"],
                "enabled": 1,
                "apply_sla_for_resolution": 1,
                "agreement_type": sla_def["agreement_type"],
                "holiday_list": holiday_list,
                "timezone": "Africa/Nairobi",
                "support_and_resolution": working_hours,
                "priorities": [
                    {
                        "priority": priority,
                        "default_priority": 1,
                        "response_time": sla_def["response_time"],
                        "resolution_time": sla_def["resolution_time"],
                    }
                ],
            }
        )
        doc.insert(ignore_permissions=True)

    frappe.db.commit()  # nosemgrep
