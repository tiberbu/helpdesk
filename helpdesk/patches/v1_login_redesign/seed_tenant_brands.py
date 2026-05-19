"""
Patch: seed_tenant_brands

Sprint 5 (Login Redesign) — seeds the Tiberbu and DHA HD Brand records so
the redesigned login page resolves them from incoming Host headers.

This patch is idempotent. It uses brand_name (the PK) to detect existing
records and only inserts when missing. Re-running on a site that already has
Tiberbu / DHA brands is a no-op.

Per G0.3 reconciliation (2026-05-14), Sprint 5 ships records with colours +
copy + host_patterns only — logo / wordmark / favicon attach later via the
admin form when artwork is delivered. The first-party-asset validator is
already in place (Sprint 1).
"""

import frappe

_BRAND_DEFINITIONS = [
    {
        "brand_name": "Tiberbu",
        "is_active": 1,
        "is_default": 0,
        "host_patterns": "\n".join(["*.tiberbu.health", "*.tiberbu.app"]),
        "primary_color": "#5551FF",
        "accent_color": "#7B78FF",
        "bg_tint_color": "#F5F5FF",
        "headline": "Welcome back",
        "supporting_copy": "Sign in to Tiberbu Helpdesk",
    },
    {
        "brand_name": "DHA",
        "is_active": 1,
        "is_default": 0,
        "host_patterns": "*.dha.gov.ae",
        "primary_color": "#1A8755",
        "accent_color": "#54B98A",
        "bg_tint_color": "#F2FAF6",
        "headline": "Welcome to DHA Helpdesk",
        "supporting_copy": "Sign in to manage your tickets and access knowledge base articles.",
    },
]


def execute():
    # Reload the schema in case this patch runs ahead of extend_hd_brand_for_login
    # on a fresh site (defensive — patches.txt order guarantees we run after).
    frappe.reload_doc("Helpdesk", "doctype", "hd_brand", force=True)

    for definition in _BRAND_DEFINITIONS:
        if frappe.db.exists("HD Brand", definition["brand_name"]):
            continue

        doc = frappe.get_doc({"doctype": "HD Brand", **definition})
        doc.insert(ignore_permissions=True)

    frappe.db.commit()  # nosemgrep
