# Copyright (c) 2021, Frappe Technologies and contributors
# For license information, please see license.txt

import frappe
from frappe import _
from frappe.model.document import Document
from frappe.utils import add_days, cint, get_url, now_datetime, today

from helpdesk.utils import capture_event

# Workflow action name constants
_ACTION_SUBMIT_FOR_REVIEW = "Submit for Review"
_ACTION_APPROVE = "Approve"
_ACTION_REQUEST_CHANGES = "Request Changes"
_ACTION_REJECT = "Reject"
_ACTION_ARCHIVE = "Archive"


class HDArticle(Document):
    def validate(self):
        self.validate_article_category()
        self.validate_published_content()

    def validate_article_category(self):
        if self.has_value_changed("category") and not self.is_new():
            old_category = self.get_doc_before_save().get("category")
            self.check_category_length(old_category)

    def validate_published_content(self):
        if self.status == "Published" and not self.content:
            frappe.throw(_("Published articles must have content."))

    def before_insert(self):
        self.author = frappe.session.user

    def before_save(self):
        # set published date of the hd_article
        if self.status == "Published" and not self.published_on:
            self.published_on = frappe.utils.now()
        elif self.status == "Draft" and self.published_on:
            self.published_on = None

        # index is only set if its not set already, this allows defining index
        # at the time of creation itself if not set the index is set to the
        # last index + 1, i.e. the hd_article is added at the end
        if self.status == "Published" and self.idx == -1:
            self.idx = cint(
                frappe.db.count(
                    "HD Article",
                    {"category": self.category, "status": "Published"},
                )
            )

    def on_update(self):
        """Create a version snapshot when content, title, or category changes."""
        if self.flags.get("skip_version_creation"):
            return

        before = self.get_doc_before_save()
        if before is None:
            # First-ever save — always create version
            self._create_version()
            return

        if (
            self.content != before.get("content")
            or self.title != before.get("title")
            or self.category != before.get("category")
        ):
            self._create_version()

    def _create_version(self):
        """Insert an HD Article Version record capturing the current state."""
        from helpdesk.helpdesk.doctype.hd_article_version.hd_article_version import (
            HDArticleVersion,
        )

        change_summary = self.flags.get("revert_change_summary") or ""
        if not change_summary:
            ts = now_datetime().strftime("%Y-%m-%d %H:%M")
            change_summary = _("Updated by {0} on {1}").format(
                frappe.session.user, ts
            )

        version_number = HDArticleVersion.get_next_version_number(self.name)

        version_doc = frappe.new_doc("HD Article Version")
        version_doc.article = self.name
        version_doc.version_number = version_number
        version_doc.content = self.content or ""
        version_doc.title = self.title or ""
        version_doc.author = frappe.session.user
        version_doc.timestamp = now_datetime()
        version_doc.change_summary = change_summary
        version_doc.insert(ignore_permissions=True)

    def after_insert(self):
        count = frappe.db.count("HD Article")
        if count == 1:
            return
        capture_event("article_created")

    def on_trash(self):
        self.check_category_length()

    def check_category_length(self, category=None):
        category = category or self.get("category")
        if not category:
            return
        category_articles = frappe.db.count("HD Article", {"category": category})
        if category_articles == 1:
            frappe.throw(_("Category must have atleast one article"))

    def on_workflow_action(self, action: str):
        """Called by Frappe workflow engine after a workflow transition.

        Routes to the appropriate notification helper based on the action name.
        """
        if action == _ACTION_SUBMIT_FOR_REVIEW:
            self._notify_reviewers_for_review()
        elif action == _ACTION_APPROVE:
            self._notify_author_approved()
            self._set_review_date()
        elif action == _ACTION_REQUEST_CHANGES:
            self._notify_author_changes_requested()
        elif action == _ACTION_REJECT:
            self._notify_author_rejected()

    def _get_article_url(self) -> str:
        """Return agent workspace URL for this article."""
        return get_url(f"/helpdesk/kb/articles/{self.name}")

    def _set_review_date(self):
        """Set review_date to today + kb_review_period_days days (AC #2, Story 5.3).

        on_workflow_action is called after the document is already saved, so we must
        persist the value directly to the DB rather than just setting self.review_date.
        """
        settings = frappe.get_single("HD Settings")
        period = settings.get_kb_review_period_days()
        new_review_date = add_days(today(), period)
        frappe.db.set_value(
            "HD Article", self.name, "review_date", new_review_date, update_modified=False
        )
        self.review_date = new_review_date  # keep in-memory in sync

    def _notify_reviewers_for_review(self):
        """Send email to all configured KB reviewers when article is submitted for review."""
        settings = frappe.get_single("HD Settings")
        reviewer_emails = settings.get_kb_reviewer_emails()
        if not reviewer_emails:
            return

        author_name = frappe.db.get_value("User", self.author, "full_name") or self.author
        article_url = self._get_article_url()
        subject = _("Article submitted for review: {0}").format(self.title)
        message = _(
            "The article <b>{0}</b> has been submitted for review by {1}.<br><br>"
            '<a href="{2}">Review Article</a>'
        ).format(self.title, author_name, article_url)

        frappe.sendmail(
            recipients=reviewer_emails,
            subject=subject,
            message=message,
            delayed=True,
        )

    def _notify_author_approved(self):
        """Send email to article author when article is approved (Published)."""
        if not self.author:
            return
        author_email = frappe.db.get_value("User", self.author, "email") or self.author
        article_url = self._get_article_url()
        subject = _("Your article '{0}' has been published").format(self.title)
        message = _(
            "Your article <b>{0}</b> has been reviewed and published.<br><br>"
            '<a href="{1}">View Article</a>'
        ).format(self.title, article_url)

        frappe.sendmail(
            recipients=[author_email],
            subject=subject,
            message=message,
            delayed=True,
        )

    def _notify_author_changes_requested(self):
        """Send email to article author when changes are requested."""
        if not self.author:
            return
        author_email = frappe.db.get_value("User", self.author, "email") or self.author
        article_url = self._get_article_url()
        comment = self.reviewer_comment or ""
        subject = _("Changes requested for '{0}'").format(self.title)
        message = _(
            "Changes have been requested for your article <b>{0}</b>.<br><br>"
            "{1}<br><br>"
            '<a href="{2}">View Article</a>'
        ).format(self.title, comment, article_url)

        frappe.sendmail(
            recipients=[author_email],
            subject=subject,
            message=message,
            delayed=True,
        )

    def _notify_author_rejected(self):
        """Send email to article author when article is rejected (Archived)."""
        if not self.author:
            return
        author_email = frappe.db.get_value("User", self.author, "email") or self.author
        subject = _("Your article '{0}' has been archived (rejected)").format(self.title)
        message = _(
            "Your article <b>{0}</b> has been reviewed and rejected (archived)."
        ).format(self.title)

        frappe.sendmail(
            recipients=[author_email],
            subject=subject,
            message=message,
            delayed=True,
        )

    @staticmethod
    def default_list_data():
        columns = [
            {
                "label": "Title",
                "type": "Data",
                "key": "title",
                "width": "20rem",
            },
            {
                "label": "Status",
                "type": "status",
                "key": "status",
                "width": "10rem",
            },
            {
                "label": "Author",
                "type": "Link",
                "key": "author",
                "width": "17rem",
            },
            {
                "label": "Last Modified",
                "type": "Datetime",
                "key": "modified",
                "width": "8rem",
            },
        ]
        return {"columns": columns}

    @frappe.whitelist()
    def set_feedback(self, value: int):
        # 0 empty, 1 like, 2 dislike
        user = frappe.session.user
        feedback = frappe.db.exists(
            "HD Article Feedback", {"user": user, "article": self.name}
        )
        if feedback:
            frappe.db.set_value("HD Article Feedback", feedback, "feedback", value)
            return

        frappe.new_doc(
            "HD Article Feedback", user=user, article=self.name, feedback=value
        ).insert()

    @property
    def title_slug(self) -> str:
        """
        Generate slug from article title.
        Example: "Introduction to Frappe Helpdesk" -> "introduction-to-frappe-helpdesk"

        :return: Generated slug
        """
        return self.title.lower().replace(" ", "-")
