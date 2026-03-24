import frappe
from bs4 import BeautifulSoup
from frappe import _
from frappe.rate_limiter import rate_limit
from frappe.utils import get_user_info_for_avatar

from helpdesk.utils import is_agent

# Allowed workflow transitions callable from the Vue frontend
_SUBMIT_FOR_REVIEW = "Submit for Review"
_APPROVE = "Approve"
_REQUEST_CHANGES = "Request Changes"
_REJECT = "Reject"
_ARCHIVE = "Archive"


@frappe.whitelist(allow_guest=True)
def get_article(name: str):
    article = frappe.get_doc("HD Article", name).as_dict()

    if not is_agent() and article["status"] != "Published":
        frappe.throw(_("Access denied"), frappe.PermissionError)

    if not is_agent() and article.get("internal_only"):
        frappe.throw(_("Access denied"), frappe.PermissionError)

    author = get_user_info_for_avatar(article["author"])
    feedback = (
        frappe.db.get_value(
            "HD Article Feedback",
            {"article": name, "user": frappe.session.user},
            "feedback",
        )
        or 0
    )

    return {
        "name": article.name,
        "title": article.title,
        "content": article.content,
        "author": author,
        "creation": article.creation,
        "status": article.status,
        "published_on": article.published_on,
        "modified": article.modified,
        "category_name": frappe.db.get_value(
            "HD Article Category", article.category, "category_name"
        ),
        "category_id": article.category,
        "feedback": int(feedback),
        "reviewer_comment": article.reviewer_comment,
        "internal_only": article.get("internal_only", 0),
    }


@frappe.whitelist()
def delete_articles(articles: list[str]):
    for article in articles:
        frappe.delete_doc("HD Article", article)


@frappe.whitelist()
def create_category(title: str):
    category = frappe.new_doc("HD Article Category", category_name=title).insert()
    article = frappe.new_doc(
        "HD Article", title="New Article", category=category.name
    ).insert()
    return {"article": article.name, "category": category.name}


@frappe.whitelist()
def move_to_category(category: str, articles: list[str]):
    frappe.has_permission("HD Article", "write", throw=True)

    for article in articles:
        try:
            article_category = frappe.db.get_value("HD Article", article, "category")
            category_existing_articles = frappe.db.count(
                "HD Article", {"category": article_category}
            )
            if category_existing_articles == 1:
                frappe.throw(_("Category must have atleast one article"))
                return
            else:
                frappe.db.set_value(
                    "HD Article", article, "category", category, update_modified=False
                )
        except Exception as e:
            frappe.db.rollback()
            frappe.throw(_("Error moving article to category"))


@frappe.whitelist()
def get_categories():
    categories = frappe.get_all(
        "HD Article Category",
        fields=["name", "category_name", "modified"],
    )
    for c in categories:
        c["article_count"] = frappe.db.count(
            "HD Article", filters={"category": c.name, "status": "Published", "internal_only": 0}
        )

    categories.sort(key=lambda c: c["article_count"], reverse=True)
    categories = [c for c in categories if c["article_count"] > 0]
    return categories


@frappe.whitelist()
def get_category_articles(category: str):
    articles = frappe.get_all(
        "HD Article",
        filters={"category": category, "status": "Published", "internal_only": 0},
        fields=["name", "title", "published_on", "modified", "author", "content"],
    )
    for article in articles:
        article["author"] = get_user_info_for_avatar(article["author"])
        soup = BeautifulSoup(article["content"], "html.parser")
        article["content"] = str(soup.text)[:100]

    return articles


@frappe.whitelist()
def merge_category(source: str, target: str):
    frappe.has_permission("HD Article Category", "delete", throw=True)

    if source == target:
        frappe.throw(_("Source and target category cannot be same"))
    general_category = get_general_category()
    if source == general_category:
        frappe.throw(_("Cannot merge General category"))
    source_articles = frappe.get_all(
        "HD Article",
        filters={"category": source},
        pluck="name",
    )
    for article in source_articles:
        frappe.db.set_value(
            "HD Article", article, "category", target, update_modified=False
        )

    frappe.delete_doc("HD Article Category", source)


@frappe.whitelist()
def get_general_category():
    return frappe.db.get_value(
        "HD Article Category", {"category_name": "General"}, "name"
    )


@frappe.whitelist()
def get_category_title(category: str):
    return frappe.db.get_value("HD Article Category", category, "category_name")


@frappe.whitelist()
@rate_limit(key="article", seconds=60 * 60)
def increment_views(article: str):
    views = frappe.db.get_value("HD Article", article, "views") or 0
    views += 1
    frappe.db.set_value("HD Article", article, "views", views, update_modified=False)


@frappe.whitelist()
def submit_for_review(article: str) -> dict:
    """Transition article from Draft to In Review. Callable by agents/authors.

    Sends email notification to all configured KB reviewers.
    """
    if not is_agent():
        frappe.throw(_("Not permitted"), frappe.PermissionError)

    doc = frappe.get_doc("HD Article", article)
    if doc.status != "Draft":
        frappe.throw(
            _("Only Draft articles can be submitted for review. Current status: {0}").format(
                doc.status
            )
        )

    doc.status = "In Review"
    doc.reviewer_comment = None
    doc.save(ignore_permissions=True)
    doc.on_workflow_action(_SUBMIT_FOR_REVIEW)
    return {"status": doc.status}


@frappe.whitelist()
def approve_article(article: str) -> dict:
    """Transition article from In Review to Published. Restricted to HD Admin/System Manager."""
    _require_reviewer_role()

    doc = frappe.get_doc("HD Article", article)
    if doc.status != "In Review":
        frappe.throw(
            _("Only In Review articles can be approved. Current status: {0}").format(
                doc.status
            )
        )

    doc.status = "Published"
    doc.save(ignore_permissions=True)
    try:
        doc.on_workflow_action(_APPROVE)
    except Exception:
        frappe.log_error(title="Article workflow notification failed")
    return {"status": doc.status}


@frappe.whitelist()
def request_changes(article: str, comment: str) -> dict:
    """Transition article from In Review back to Draft with a reviewer comment."""
    _require_reviewer_role()

    if not comment or not comment.strip():
        frappe.throw(_("A reviewer comment is required when requesting changes."))

    doc = frappe.get_doc("HD Article", article)
    if doc.status != "In Review":
        frappe.throw(
            _("Only In Review articles can have changes requested. Current status: {0}").format(
                doc.status
            )
        )

    doc.status = "Draft"
    doc.reviewer_comment = comment.strip()
    doc.save(ignore_permissions=True)
    try:
        doc.on_workflow_action(_REQUEST_CHANGES)
    except Exception:
        frappe.log_error(title="Article workflow notification failed")
    return {"status": doc.status}


@frappe.whitelist()
def reject_article(article: str) -> dict:
    """Transition article from In Review to Archived (rejected)."""
    _require_reviewer_role()

    doc = frappe.get_doc("HD Article", article)
    if doc.status != "In Review":
        frappe.throw(
            _("Only In Review articles can be rejected. Current status: {0}").format(
                doc.status
            )
        )

    doc.status = "Archived"
    doc.save(ignore_permissions=True)
    try:
        doc.on_workflow_action(_REJECT)
    except Exception:
        frappe.log_error(title="Article workflow notification failed")
    return {"status": doc.status}


@frappe.whitelist()
def archive_article(article: str) -> dict:
    """Transition article from Published to Archived."""
    _require_reviewer_role()

    doc = frappe.get_doc("HD Article", article)
    if doc.status != "Published":
        frappe.throw(
            _("Only Published articles can be archived. Current status: {0}").format(
                doc.status
            )
        )

    doc.status = "Archived"
    doc.save(ignore_permissions=True)
    try:
        doc.on_workflow_action(_ARCHIVE)
    except Exception:
        frappe.log_error(title="Article workflow notification failed")
    return {"status": doc.status}


@frappe.whitelist()
def get_agent_articles(category: str = None) -> list[dict]:
    """Return all non-archived articles visible to agents (includes In Review).

    AC #8: In Review articles are visible to agents for internal reference.
    """
    if not is_agent():
        frappe.throw(_("Not permitted"), frappe.PermissionError)

    filters = {"status": ["!=", "Archived"]}
    if category:
        filters["category"] = category

    articles = frappe.get_all(
        "HD Article",
        filters=filters,
        fields=["name", "title", "status", "author", "modified", "category", "internal_only"],
        order_by="modified desc",
    )
    return articles


@frappe.whitelist()
def get_article_versions(article: str) -> list[dict]:
    """Return all version records for an article, ordered newest-first.

    Restricted to agents only (AC #10).
    """
    if not is_agent():
        frappe.throw(_("Not permitted"), frappe.PermissionError)

    versions = frappe.get_all(
        "HD Article Version",
        filters={"article": article},
        fields=["name", "version_number", "title", "author", "timestamp", "change_summary", "content"],
        order_by="version_number desc",
    )

    for v in versions:
        v["author_full_name"] = (
            frappe.db.get_value("User", v["author"], "full_name") or v["author"]
        )

    return versions


@frappe.whitelist()
def revert_article_to_version(article: str, version_name: str) -> dict:
    """Restore article content from a previous version and create a new version record.

    Restricted to agents only (AC #10). Preserves workflow state (AC #7).
    """
    if not is_agent():
        frappe.throw(_("Not permitted"), frappe.PermissionError)

    version_doc = frappe.get_doc("HD Article Version", version_name)

    if version_doc.article != article:
        frappe.throw(_("Version does not belong to this article"), frappe.ValidationError)

    doc = frappe.get_doc("HD Article", article)
    doc.content = version_doc.content
    doc.title = version_doc.title
    doc.flags.revert_change_summary = _(
        "Reverted to version #{0} by {1}"
    ).format(version_doc.version_number, frappe.session.user)
    doc.save(ignore_permissions=True)

    from helpdesk.helpdesk.doctype.hd_article_version.hd_article_version import (
        HDArticleVersion,
    )
    new_version_number = HDArticleVersion.get_next_version_number(article) - 1

    return {"success": True, "new_version_number": new_version_number}


def _require_reviewer_role():
    """Ensure the calling user has System Manager or HD Admin role."""
    user_roles = set(frappe.get_roles(frappe.session.user))
    if not user_roles & {"System Manager", "HD Admin"}:
        frappe.throw(_("Only reviewers (HD Admin or System Manager) can perform this action."), frappe.PermissionError)


# ---------------------------------------------------------------------------
# Story 5.4: Ticket-Article Linking
# ---------------------------------------------------------------------------

@frappe.whitelist()
def search_articles(query: str = "") -> list:
    """Search published KB articles by title for the link dialog.

    Only Published articles are returned (agents cannot link Draft/In Review
    articles — keeps the KB consistent with portal visibility).
    """
    filters = {"status": "Published"}
    if query:
        filters["title"] = ["like", f"%{query}%"]

    articles = frappe.get_all(
        "HD Article",
        filters=filters,
        fields=["name", "title", "category", "internal_only"],
        order_by="title asc",
        limit=20,
    )

    for art in articles:
        if art.get("category"):
            art["category_name"] = (
                frappe.db.get_value("HD Article Category", art["category"], "category_name")
                or art["category"]
            )
        else:
            art["category_name"] = ""

    return articles


@frappe.whitelist()
def link_article_to_ticket(ticket: str, article: str) -> dict:
    """Link a published article to a ticket.

    Creates an HD Ticket Article child row on the HD Ticket.
    Raises ValidationError if the article is already linked.
    Requires write permission on HD Ticket (agent-only, AC #9).
    """
    if not is_agent():
        frappe.throw(_("Not permitted"), frappe.PermissionError)

    article_doc = frappe.get_doc("HD Article", article)

    # Duplicate prevention (AC #4)
    existing = frappe.db.exists(
        "HD Ticket Article",
        {
            "parent": ticket,
            "parentfield": "linked_articles",
            "parenttype": "HD Ticket",
            "article": article,
        },
    )
    if existing:
        frappe.throw(
            _("Article '{0}' is already linked to this ticket.").format(article_doc.title),
            frappe.ValidationError,
        )

    ticket_doc = frappe.get_doc("HD Ticket", ticket)
    ticket_doc.append(
        "linked_articles",
        {
            "article": article,
            "article_title": article_doc.title,
        },
    )
    ticket_doc.save(ignore_permissions=True)

    return {"article": article, "article_title": article_doc.title}


@frappe.whitelist()
def remove_article_link(ticket: str, article: str) -> None:
    """Remove an article link from a ticket.

    Deletes the matching HD Ticket Article child row.
    Requires write permission on HD Ticket (AC #9, #10).
    """
    if not is_agent():
        frappe.throw(_("Not permitted"), frappe.PermissionError)

    ticket_doc = frappe.get_doc("HD Ticket", ticket)
    rows_to_keep = [row for row in ticket_doc.linked_articles if row.article != article]

    if len(rows_to_keep) == len(ticket_doc.linked_articles):
        frappe.throw(_("Article link not found on this ticket."), frappe.ValidationError)

    ticket_doc.linked_articles = rows_to_keep
    ticket_doc.save(ignore_permissions=True)


@frappe.whitelist()
def get_linked_tickets(article: str) -> dict:
    """Return tickets that have linked this article.

    Returns count of all linked tickets plus the 10 most recent rows,
    enriched with ticket subject and status (AC #8).
    """
    count = frappe.db.count(
        "HD Ticket Article",
        filters={"article": article, "parenttype": "HD Ticket"},
    )

    rows = frappe.db.get_all(
        "HD Ticket Article",
        filters={"article": article, "parenttype": "HD Ticket"},
        fields=["parent as ticket_name", "linked_on"],
        order_by="linked_on desc",
        limit=10,
    )

    tickets = []
    for row in rows:
        ticket_name = row["ticket_name"]
        subject, status = frappe.db.get_value(
            "HD Ticket", ticket_name, ["subject", "status"]
        ) or ("", "")
        tickets.append(
            {
                "name": ticket_name,
                "subject": subject,
                "status": status,
                "linked_on": row["linked_on"],
            }
        )

    return {"count": count, "tickets": tickets}


@frappe.whitelist()
def prefill_article_from_ticket(ticket: str) -> dict:
    """Return pre-fill data for creating a new article from a ticket.

    Fetches the ticket subject, category, and last agent reply content.
    Does NOT include internal notes (communication_type=Communication only).
    Requires write permission on HD Ticket (agent-only).
    """
    if not is_agent():
        frappe.throw(_("Not permitted"), frappe.PermissionError)

    ticket_doc = frappe.get_doc("HD Ticket", ticket)

    # Fetch last outgoing agent communication (not internal notes)
    last_replies = frappe.db.get_all(
        "Communication",
        filters={
            "reference_doctype": "HD Ticket",
            "reference_name": ticket,
            "sent_or_received": "Sent",
            "communication_type": "Communication",
        },
        fields=["content"],
        order_by="creation desc",
        limit=1,
    )

    last_reply_content = last_replies[0]["content"] if last_replies else ""

    if last_reply_content:
        content = (
            f"<h2>{_('Problem')}</h2>"
            f"<p>{frappe.utils.escape_html(ticket_doc.subject)}</p>"
            f"<h2>{_('Resolution')}</h2>"
            f"{last_reply_content}"
        )
    else:
        content = (
            f"<h2>{_('Problem')}</h2>"
            f"<p>{frappe.utils.escape_html(ticket_doc.subject)}</p>"
        )

    return {
        "title": ticket_doc.subject,
        "content": content,
        "category": ticket_doc.category or "",
        "source_ticket": ticket,
    }
