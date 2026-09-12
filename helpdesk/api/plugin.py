"""Signed CareVerse plugin contract, preserving native ticket routing and threads."""

import hashlib
import json
from html import escape

import frappe

from helpdesk.api import mobile, plugin_media
from helpdesk.api.mobile_signing import signed_rpc


def _identity():
    identity = getattr(frappe.local, "careverse_identity", None)
    if not identity or frappe.session.user == "Guest":
        frappe.throw(
            "Verified CareVerse identity required.", frappe.AuthenticationError
        )
    return identity


def _email(email=None):
    expected = _identity()["user_id"]
    if email is not None and email != expected:
        frappe.throw(
            "Reporter email must match the authenticated CareVerse user.",
            frappe.PermissionError,
        )
    return expected


def _filters():
    return {
        "plugin_instance": _identity()["instance_id"],
        "plugin_reporter_email": _email(),
        "raised_by": frappe.session.user,
    }


def _ticket(ticket_id):
    doc = mobile._ticket(ticket_id)
    if any(doc.get(key) != value for key, value in _filters().items()):
        frappe.throw(
            "Ticket does not belong to this instance and reporter.",
            frappe.PermissionError,
        )
    return doc


def _summary(doc):
    return {
        "ticket_id": doc.name,
        "status": doc.status,
        "assigned_to": json.loads(doc.get("_assign") or "[]"),
        "assigned_team": doc.agent_group,
        "attachments": [plugin_media.metadata(f) for f in plugin_media.initial(doc)],
    }


def _detail(doc):
    return {
        **{key: doc.get(key) for key in mobile.TICKET_FIELDS},
        **_summary(doc),
        "source": doc.plugin_source,
        "external_reference_id": doc.external_reference_id,
        "category": doc.ticket_type,
        "description_html": doc.description or "",
        "reporter": {
            "name": doc.plugin_reporter_name,
            "email": doc.plugin_reporter_email,
            "facility": doc.plugin_reporter_facility,
        },
    }


def _existing(key):
    rows = frappe.get_list(
        "HD Ticket",
        filters={**_filters(), "plugin_key": key},
        fields=["name"],
        limit_page_length=1,
    )
    return _ticket(rows[0].name) if rows else None


def _check_attachment_retry(doc, attachments, fingerprint):
    original = doc.get("plugin_attachment_fingerprint") or plugin_media.fingerprint([])
    if attachments is not None and fingerprint != original:
        frappe.throw(
            "Attachments differ from the original submission. Send new files in a follow-up message."
        )


@frappe.whitelist(allow_guest=True, methods=["POST"])
@signed_rpc
def create_ticket(
    source,
    external_reference_id,
    reporter,
    category,
    priority,
    description,
    attachments=None,
):
    identity = _identity()
    files = plugin_media.validate(attachments)
    attachment_fingerprint = plugin_media.fingerprint(files)
    source = mobile._text(source, "source", 40)
    external_reference_id = mobile._text(
        external_reference_id, "external_reference_id", 140
    )
    if not isinstance(reporter, dict) or set(reporter) != {"name", "email", "facility"}:
        frappe.throw("reporter must contain name, email and facility.")
    email = _email(mobile._text(reporter["email"], "reporter.email", 140))
    name = mobile._text(reporter["name"], "reporter.name", 140)
    facility = mobile._text(reporter["facility"], "reporter.facility", 140)
    # A persistent unique index arbitrates concurrent creates, including different users.
    key = hashlib.sha256(
        json.dumps(
            [identity["instance_id"], source, external_reference_id],
            separators=(",", ":"),
        ).encode()
    ).hexdigest()
    existing = _existing(key)
    if existing:
        _check_attachment_retry(existing, attachments, attachment_fingerprint)
        return mobile._result({**_summary(existing), "reused": True})
    description = mobile._text(description, "description", 20000)
    mobile._link("HD Ticket Type", category)
    mobile._link("HD Ticket Priority", priority)
    if frappe.db.get_value("HD Ticket Type", category, "disabled"):
        frappe.throw("Category is disabled.")
    # Resolve an existing catalogue entry; free-text facility remains reporter metadata.
    facilities = [
        row
        for row in mobile.location.get_facilities()
        if facility in (row.get("name"), row.get("facility_name"))
    ]
    if len(facilities) > 1:
        frappe.throw(
            "Facility name is ambiguous. Use the facility ID from get_facilities."
        )
    location = facilities[0] if facilities else {}
    doc = frappe.get_doc(
        {
            "doctype": "HD Ticket",
            "subject": description.splitlines()[0][:140],
            "description": escape(description).replace("\n", "<br>"),
            "priority": priority,
            "ticket_type": category,
            "raised_by": frappe.session.user,
            "via_customer_portal": 1,
            "facility": location.get("name"),
            "county": location.get("county"),
            "sub_county": location.get("sub_county"),
            "plugin_key": key,
            "plugin_instance": identity["instance_id"],
            "plugin_source": source,
            "external_reference_id": external_reference_id,
            "plugin_reporter_name": name,
            "plugin_reporter_email": email,
            "plugin_reporter_facility": facility,
            "plugin_attachment_fingerprint": attachment_fingerprint,
        }
    )
    previous_messages = list(frappe.local.message_log or [])
    try:
        doc.insert()
    except (frappe.UniqueValidationError, frappe.DuplicateEntryError):
        # End the losing transaction's snapshot before reading the committed winner.
        frappe.db.rollback()
        existing = _existing(key)
        if existing:
            _check_attachment_retry(existing, attachments, attachment_fingerprint)
            # A resolved uniqueness race is success, not a client error toast.
            frappe.local.message_log = previous_messages
            return mobile._result({**_summary(existing), "reused": True})
        frappe.throw(
            "External reference is already in use or ticket creation conflicted.",
            frappe.PermissionError,
        )
    saved = plugin_media.save(files, "HD Ticket", doc.name)
    doc.db_set(
        "plugin_attachments",
        json.dumps([f["attachment_id"] for f in saved]),
        update_modified=False,
    )
    doc.reload()  # Native assignment rules may update _assign directly during insertion.
    return mobile._result({**_summary(doc), "reused": False})


@frappe.whitelist(allow_guest=True, methods=["GET"])
@signed_rpc
def get_ticket(ticket_id):
    doc = _ticket(ticket_id)
    return mobile._result(_detail(doc))


@frappe.whitelist(allow_guest=True, methods=["GET"])
@signed_rpc
def list_tickets(email=None, status=None, offset=0, limit=20):
    _email(email)
    offset, limit = mobile._page(offset, limit)
    filters = _filters()
    if status:
        filters["status"] = status
    rows = frappe.get_list(
        "HD Ticket",
        filters=filters,
        fields=["name"],
        order_by="creation desc, name desc",
        limit_start=offset,
        limit_page_length=limit + 1,
    )
    return mobile._result(
        {
            "items": [_detail(_ticket(row.name)) for row in rows[:limit]],
            "has_more": len(rows) > limit,
            "next_offset": offset + limit if len(rows) > limit else None,
        }
    )


@frappe.whitelist(allow_guest=True, methods=["GET"])
@signed_rpc
def get_bootstrap():
    result = mobile.get_bootstrap()
    result["data"]["categories"] = result["data"].pop("ticket_types")
    result["data"]["reporter_email"] = _email()
    result["data"]["capabilities"]["attachments"] = True
    result["data"]["attachment_limits"] = plugin_media.LIMITS
    return result


@frappe.whitelist(allow_guest=True, methods=["GET"])
@signed_rpc
def get_counties():
    return mobile.get_counties()


@frappe.whitelist(allow_guest=True, methods=["GET"])
@signed_rpc
def get_subcounties(county):
    return mobile.get_subcounties(county)


@frappe.whitelist(allow_guest=True, methods=["GET"])
@signed_rpc
def get_facilities(county=None, sub_county=None, offset=0, limit=50):
    return mobile.get_facilities(county, sub_county, offset, limit)


@frappe.whitelist(allow_guest=True, methods=["GET"])
@signed_rpc
def get_thread(ticket_id, offset=0, limit=50):
    doc = _ticket(ticket_id)
    result = mobile.get_thread(ticket_id, offset, limit)
    grouped = {}
    for file, event_id in plugin_media.public_files(doc):
        grouped.setdefault(event_id, []).append(plugin_media.metadata(file))
    for event in result["data"]["items"]:
        event["attachments"] = grouped.get(event["id"], [])
    result["data"]["initial_attachments"] = grouped.get(None, [])
    return result


@frappe.whitelist(allow_guest=True, methods=["POST"])
@signed_rpc
def send_message(ticket_id, content="", attachments=None):
    doc = _ticket(ticket_id)
    files = plugin_media.validate(attachments)
    if (
        not isinstance(content, str)
        or len(content) > 10000
        or (not content.strip() and not files)
    ):
        frappe.throw("Provide a message of at most 10000 characters or an attachment.")
    comment_id = doc.new_comment(
        escape(content.strip()).replace("\n", "<br>") or "Attachments"
    )
    saved = plugin_media.save(files, "HD Ticket Comment", comment_id)
    return mobile._result(
        {
            "ticket_id": doc.name,
            "accepted": True,
            "message_id": "comment:" + comment_id,
            "attachments": saved,
        }
    )


@frappe.whitelist(allow_guest=True, methods=["GET"])
@signed_rpc
def list_attachments(ticket_id, offset=0, limit=50):
    doc = _ticket(ticket_id)
    offset, limit = mobile._page(offset, limit)
    files = plugin_media.public_files(doc)
    return mobile._result(
        {
            "items": [
                {**plugin_media.metadata(f), "event_id": event}
                for f, event in files[offset : offset + limit]
            ],
            "has_more": len(files) > offset + limit,
            "next_offset": offset + limit if len(files) > offset + limit else None,
        }
    )


@frappe.whitelist(allow_guest=True, methods=["GET"])
@signed_rpc
def download_attachment(ticket_id, attachment_id):
    return mobile._result(plugin_media.download(_ticket(ticket_id), attachment_id))
