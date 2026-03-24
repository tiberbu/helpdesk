# Copyright (c) 2026, Frappe Technologies and contributors
# For license information, please see license.txt
# Story 5.3: Review Dates and Expiry Reminders — backend API (AC #7, #8, #9)

import frappe
from frappe import _
from frappe.utils import add_days, getdate, today

from helpdesk.utils import is_agent


@frappe.whitelist()
def get_articles_due_for_review() -> dict:
    """Return Published articles whose review_date is within 7 days or already overdue.

    Response shape:
      {
        "overdue":  [article, ...],   # review_date < today
        "upcoming": [article, ...],   # today <= review_date <= today + 7
      }

    Each article dict includes: name, title, review_date, author, reviewed_by,
    days_overdue (positive = overdue, negative = days remaining).

    Permission: agents only (AC #9 security note).
    """
    if not is_agent():
        frappe.throw(_("Not permitted"), frappe.PermissionError)

    today_str = today()
    cutoff_date = add_days(today_str, 7)

    articles = frappe.db.get_all(
        "HD Article",
        filters=[
            ["status", "=", "Published"],
            ["review_date", "is", "set"],
            ["review_date", "<=", cutoff_date],
        ],
        fields=["name", "title", "review_date", "author", "reviewed_by"],
        order_by="review_date asc",
    )

    today_date = getdate(today_str)
    overdue = []
    upcoming = []

    for art in articles:
        rd = getdate(art.review_date)
        delta = (today_date - rd).days  # positive = overdue
        art["days_overdue"] = delta
        if rd < today_date:
            overdue.append(art)
        else:
            upcoming.append(art)

    return {"overdue": overdue, "upcoming": upcoming}


@frappe.whitelist()
def mark_article_reviewed(article_name: str) -> dict:
    """Reset review_date, set reviewed_by to current user, clear last_reminder_sent.

    AC #8: mark_article_reviewed action.
    """
    if not is_agent():
        frappe.throw(_("Not permitted"), frappe.PermissionError)

    if not frappe.db.exists("HD Article", article_name):
        frappe.throw(_("Article {0} not found").format(article_name), frappe.DoesNotExistError)

    frappe.has_permission("HD Article", "write", doc=article_name, throw=True)

    settings = frappe.get_single("HD Settings")
    period = settings.get_kb_review_period_days()
    new_review_date = add_days(today(), period)

    frappe.db.set_value(
        "HD Article",
        article_name,
        {
            "review_date": new_review_date,
            "reviewed_by": frappe.session.user,
            "last_reminder_sent": None,
        },
        update_modified=False,
    )

    return {
        "name": article_name,
        "review_date": new_review_date,
        "reviewed_by": frappe.session.user,
    }


@frappe.whitelist()
def archive_article_from_widget(article_name: str) -> dict:
    """Trigger Published → Archived workflow transition from the dashboard widget.

    AC #7: "Archive" quick action on the widget.
    Uses the knowledge_base.archive_article whitelisted helper which enforces
    System Manager / HD Admin roles.
    """
    from helpdesk.api.knowledge_base import archive_article

    result = archive_article(article_name)
    return {"success": True, "status": result.get("status")}
