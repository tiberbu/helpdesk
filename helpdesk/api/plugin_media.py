"""Bounded private image/PDF attachments for the signed ticket contract."""

import base64
import binascii
import hashlib
import io
import json
import re
import warnings
from pathlib import Path

import frappe
from PIL import Image
from pypdf import PdfReader

from helpdesk.helpdesk.doctype.hd_ticket import api as ticket_api

MAX_FILES = 5
MAX_FILE_BYTES = 2 * 1024 * 1024
MAX_TOTAL_BYTES = 6 * 1024 * 1024
TYPES = {
    ".png": "image/png",
    ".jpg": "image/jpeg",
    ".jpeg": "image/jpeg",
    ".webp": "image/webp",
    ".pdf": "application/pdf",
}
FORMATS = {"image/png": "PNG", "image/jpeg": "JPEG", "image/webp": "WEBP"}
LIMITS = {
    "max_files": MAX_FILES,
    "max_file_bytes": MAX_FILE_BYTES,
    "max_total_bytes": MAX_TOTAL_BYTES,
    "content_types": sorted(set(TYPES.values())),
    "encoding": "base64",
    "max_image_pixels": 20000000,
    "max_pdf_pages": 100,
}


def validate(attachments):
    if attachments is None:
        return []
    if not isinstance(attachments, list) or len(attachments) > MAX_FILES:
        frappe.throw("attachments must be an array containing at most five files.")
    result = []
    total = 0
    for item in attachments:
        if not isinstance(item, dict) or set(item) != {
            "file_name",
            "content_type",
            "content_base64",
        }:
            frappe.throw(
                "Each attachment requires file_name, content_type and content_base64 only."
            )
        name, mime, encoded = (
            item[key] for key in ("file_name", "content_type", "content_base64")
        )
        if (
            not isinstance(name, str)
            or not re.fullmatch(r"[A-Za-z0-9][A-Za-z0-9 ._-]{0,119}", name)
            or ".." in name
        ):
            frappe.throw(
                "Use a simple file name of 1-120 ASCII characters, without paths."
            )
        if TYPES.get(Path(name).suffix.lower()) != mime or mime not in TYPES.values():
            frappe.throw("Only PNG, JPEG, WebP and PDF attachments are supported.")
        if not isinstance(encoded, str) or len(encoded) > 4 * (
            (MAX_FILE_BYTES + 2) // 3
        ):
            frappe.throw("Each attachment must be at most 2 MiB.")
        try:
            content = base64.b64decode(encoded, validate=True)
        except (binascii.Error, ValueError):
            frappe.throw(
                "Attachment content must be plain standard Base64, without a data URL prefix."
            )
        total += len(content)
        if not content or len(content) > MAX_FILE_BYTES or total > MAX_TOTAL_BYTES:
            frappe.throw(
                "Files must be nonempty, at most 2 MiB each and 6 MiB in total."
            )
        try:
            if mime == "application/pdf":
                if not content.startswith(b"%PDF-"):
                    raise ValueError()
                pdf = PdfReader(io.BytesIO(content), strict=True)
                if pdf.is_encrypted or not 1 <= len(pdf.pages) <= 100:
                    raise ValueError()
            else:
                with warnings.catch_warnings():
                    warnings.simplefilter("error", Image.DecompressionBombWarning)
                    with Image.open(io.BytesIO(content)) as image:
                        if (
                            image.format != FORMATS[mime]
                            or image.width * image.height > 20000000
                            or getattr(image, "n_frames", 1) != 1
                        ):
                            raise ValueError()
                        image.verify()
        except Exception:
            frappe.throw(
                "Attachment content is invalid or does not match its declared type; encrypted PDFs and animated images are unsupported."
            )
        result.append(
            {
                "file_name": name,
                "content_type": mime,
                "content": content,
                "sha256": hashlib.sha256(content).hexdigest(),
            }
        )
    return result


def fingerprint(files):
    manifest = [
        {k: f[k] for k in ("file_name", "content_type", "sha256")} for f in files
    ]
    return hashlib.sha256(json.dumps(manifest, sort_keys=True).encode()).hexdigest()


def metadata(file):
    return {
        "attachment_id": file.name,
        "file_name": file.file_name,
        "content_type": TYPES.get(Path(file.file_name or "").suffix.lower()),
        "size_bytes": file.file_size,
        "is_private": True,
    }


def save(files, doctype, name):
    result = []
    for item in files:
        file = frappe.get_doc(
            {
                "doctype": "File",
                "file_name": item["file_name"],
                "content": item["content"],
                "is_private": 1,
                "attached_to_doctype": doctype,
                "attached_to_name": name,
            }
        ).insert()
        result.append(metadata(file))
    return result


def _read(file):
    # Stored metadata is not a reliable allocation limit if a file changes on disk.
    with open(file.get_full_path(), "rb") as stream:
        content = stream.read(MAX_FILE_BYTES + 1)
    if not content or len(content) > MAX_FILE_BYTES:
        frappe.throw("Attachment exceeds the download limit or is empty.")
    return content


def _matches_header(content, mime):
    if mime == "image/png":
        return content.startswith(b"\x89PNG\r\n\x1a\n")
    if mime == "image/jpeg":
        return content.startswith(b"\xff\xd8\xff")
    if mime == "image/webp":
        return content.startswith(b"RIFF") and content[8:12] == b"WEBP"
    return mime == "application/pdf" and content.startswith(b"%PDF-")


def _files(ids, doctype, name):
    result = []
    for file_id in ids:
        try:
            file = frappe.get_doc("File", file_id)
        except frappe.DoesNotExistError:
            frappe.clear_last_message()
            continue
        if (
            file.attached_to_doctype != doctype
            or file.attached_to_name != name
            or not file.is_private
            or file.is_remote_file
            or file.is_folder
            or Path(file.file_name or "").suffix.lower() not in TYPES
            or not file.file_size
            or file.file_size > MAX_FILE_BYTES
        ):
            continue
        file.check_permission("read")
        try:
            with open(file.get_full_path(), "rb") as stream:
                header = stream.read(16)
        except FileNotFoundError:
            continue
        if not _matches_header(header, metadata(file)["content_type"]):
            continue
        result.append(file)
    return result


def initial(doc):
    ids = json.loads(doc.get("plugin_attachments") or "[]")
    return _files(ids, "HD Ticket", doc.name)


def public_files(doc):
    result = [(file, None) for file in initial(doc)]
    for comment in ticket_api.get_comments(doc.name):
        if not comment.is_internal:
            result.extend(
                (file, "comment:" + comment.name)
                for file in _files(
                    [a.name for a in comment.attachments],
                    "HD Ticket Comment",
                    comment.name,
                )
            )
    for communication in ticket_api.get_communications(doc.name):
        result.extend(
            (file, "communication:" + communication.name)
            for file in _files(
                [a.name for a in communication.attachments],
                "Communication",
                communication.name,
            )
        )
    return result


def download(doc, attachment_id):
    for file, event_id in public_files(doc):
        if file.name == attachment_id:
            content = _read(file)
            encoded = base64.b64encode(content).decode("ascii")
            # Native agent uploads share this path and receive the same validation.
            validate(
                [
                    {
                        "file_name": file.file_name,
                        "content_type": metadata(file)["content_type"],
                        "content_base64": encoded,
                    }
                ]
            )
            return {
                **metadata(file),
                "event_id": event_id,
                "content_base64": encoded,
                "sha256": hashlib.sha256(content).hexdigest(),
            }
    frappe.throw("Attachment is unavailable for this ticket.", frappe.PermissionError)
