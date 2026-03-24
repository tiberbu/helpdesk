# Copyright (c) 2026, Frappe Technologies and contributors
# For license information, please see license.txt
# Story 5.3: Review Dates and Expiry Reminders — daily reminder job (AC #4, #5, #6)

import frappe
from frappe import _
from frappe.utils import get_url, today


def send_review_reminders():
    """Send email reminders to authors of Published articles whose review_date has passed.

    - Skips articles where last_reminder_sent == today (duplicate prevention, AC #6).
    - Skips non-Published articles.
    - Each failing article is logged individually and does not block others (AC #4).
    - Registered in hooks.py scheduler_events["daily"] (AC #5).
    """
    today_str = today()

    overdue_articles = frappe.db.get_all(
        "HD Article",
        filters=[
            ["status", "=", "Published"],
            ["review_date", "is", "set"],
            ["review_date", "<", today_str],
            ["last_reminder_sent", "!=", today_str],
        ],
        fields=["name", "title", "review_date", "author"],
    )

    for article in overdue_articles:
        try:
            _send_reminder_for_article(article, today_str)
        except Exception:
            frappe.log_error(
                title=f"KB Review Reminder failed for article {article.name}",
                message=frappe.get_traceback(),
            )


def _send_reminder_for_article(article: dict, today_str: str):
    """Send one reminder email and stamp last_reminder_sent."""
    if not article.author:
        return

    author_email = frappe.db.get_value("User", article.author, "email") or article.author
    if not author_email:
        return

    article_url = get_url(f"/helpdesk/kb/articles/{article.name}")
    subject = _("KB Article Review Reminder: {0}").format(article.title)
    message = _(
        "This is a reminder that the knowledge base article <b>{0}</b> "
        "was due for review on {1}.<br><br>"
        "Please review and update the article, then mark it as reviewed.<br><br>"
        '<a href="{2}">View Article</a>'
    ).format(article.title, article.review_date, article_url)

    frappe.sendmail(
        recipients=[author_email],
        subject=subject,
        message=message,
        delayed=False,
    )

    # Stamp today so duplicate runs don't re-send (AC #6)
    frappe.db.set_value(
        "HD Article",
        article.name,
        "last_reminder_sent",
        today_str,
        update_modified=False,
    )
