# Copyright (c) 2026, Frappe Technologies Pvt. Ltd. and contributors
# For license information, please see license.txt

"""Migration patch: seed business-hours configuration on existing SLAs.

For each HD Service Level Agreement that has no working-hours rows (e.g. SLAs
created before Story 4.1), this patch:

  1. Reloads the DocType so the new ``timezone`` field is present.
  2. Sets ``timezone = "UTC"`` (safe default).
  3. If the SLA has no ``support_and_resolution`` rows, adds Mon-Fri 09:00-18:00
     as a baseline so existing SLAs continue to compute reasonable deadlines.

SLAs that already have working-hours rows are left untouched; only their
``timezone`` field is set if it was previously empty.
"""

import frappe


_DEFAULT_WEEKDAYS = ["Monday", "Tuesday", "Wednesday", "Thursday", "Friday"]
_DEFAULT_START = "09:00:00"
_DEFAULT_END = "18:00:00"


def execute():
    # Reload the DocType so the timezone column is available in the DB
    frappe.reload_doc("Helpdesk", "DocType", "HD Service Level Agreement")

    sla_names = frappe.db.get_all("HD Service Level Agreement", pluck="name")
    if not sla_names:
        return

    for sla_name in sla_names:
        try:
            _migrate_sla(sla_name)
        except Exception:
            frappe.log_error(
                title=f"add_business_hours_to_sla: error migrating {sla_name}",
                message=frappe.get_traceback(),
            )


def _migrate_sla(sla_name: str):
    sla = frappe.get_doc("HD Service Level Agreement", sla_name)

    changed = False

    # 1. Default timezone to UTC if not set
    if not sla.timezone:
        sla.timezone = "UTC"
        changed = True

    # 2. Seed Mon-Fri 09:00-18:00 if no working-hours rows exist
    if not sla.support_and_resolution:
        for day in _DEFAULT_WEEKDAYS:
            sla.append(
                "support_and_resolution",
                {
                    "workday": day,
                    "start_time": _DEFAULT_START,
                    "end_time": _DEFAULT_END,
                },
            )
        changed = True

    if changed:
        # Use db_update() to skip permission checks and avoid firing all hooks
        sla.db_update()
        # Also save child rows if we added them
        for row in sla.support_and_resolution:
            if not row.name:
                row.db_insert()
