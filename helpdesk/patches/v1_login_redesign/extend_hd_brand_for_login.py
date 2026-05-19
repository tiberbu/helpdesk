"""
Patch: extend_hd_brand_for_login

Sprint 1 (Login Redesign) — extends HD Brand with the additive fields the
redesigned login page needs (host_patterns, is_default, wordmark, favicon,
bg_image, accent_color, bg_tint_color, headline, supporting_copy) plus the
two new child tables (HD Brand Perk, HD Brand Stat).

This patch is purely a schema reload. The fields are declared in
``hd_brand.json``; ``frappe.reload_doc`` ensures the database is in step.

Existing HD Brand records (Phase 1 / Story 3.8) are NOT mutated. They keep
their ``brand_name`` PK, their ``portal_domain``, and their ``is_active``
flag. The new login resolver consults ``portal_domain`` as a fallback so
those records continue to work without manual edits.
"""

import frappe


def execute():
    # Reload child tables first so the parent's table fields find their target.
    if not frappe.db.exists("DocType", "HD Brand Perk"):
        frappe.reload_doc("Helpdesk", "doctype", "hd_brand_perk", force=True)
    else:
        frappe.reload_doc("Helpdesk", "doctype", "hd_brand_perk", force=True)

    if not frappe.db.exists("DocType", "HD Brand Stat"):
        frappe.reload_doc("Helpdesk", "doctype", "hd_brand_stat", force=True)
    else:
        frappe.reload_doc("Helpdesk", "doctype", "hd_brand_stat", force=True)

    # Reload the parent DocType so the additive fields get persisted.
    frappe.reload_doc("Helpdesk", "doctype", "hd_brand", force=True)

    # Reload HD Settings so the Authentication section + 3 new fields appear.
    frappe.reload_doc("Helpdesk", "doctype", "hd_settings", force=True)
