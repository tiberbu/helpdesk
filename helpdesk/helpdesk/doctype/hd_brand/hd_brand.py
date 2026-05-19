# Copyright (c) 2026, Frappe Technologies Pvt. Ltd. and contributors
# For license information, please see license.txt

import re

import frappe
from frappe import _
from frappe.model.document import Document

# Pattern grammar (see sprint-1-plan.md §Host-Pattern Grammar):
#   exact:    label("." label)+
#   wildcard: "*" "." label("." label)+
#   label:    [a-z0-9] ([a-z0-9-]* [a-z0-9])?
_HOST_LABEL = r"[a-z0-9]([a-z0-9-]*[a-z0-9])?"
_HOST_EXACT_RE = re.compile(rf"^{_HOST_LABEL}(\.{_HOST_LABEL})+$")
_HOST_WILDCARD_RE = re.compile(rf"^\*\.{_HOST_LABEL}(\.{_HOST_LABEL})+$")

_FIRST_PARTY_PREFIXES = ("/files/", "/private/files/", "/assets/")


class HDBrand(Document):
    def validate(self):
        self._validate_support_email()
        self._validate_portal_domain_unique()
        self._validate_default_uniqueness()
        self._validate_host_patterns()
        self._validate_first_party_assets()

    def _validate_support_email(self):
        if self.support_email and not frappe.utils.validate_email_address(
            self.support_email
        ):
            frappe.throw(
                _("Support Email {0} is not a valid email address").format(
                    self.support_email
                ),
                frappe.ValidationError,
            )

    def _validate_portal_domain_unique(self):
        if not self.portal_domain:
            return
        existing = frappe.db.get_value(
            "HD Brand",
            {"portal_domain": self.portal_domain, "name": ["!=", self.name]},
            "name",
        )
        if existing:
            frappe.throw(
                _("Portal domain {0} is already used by brand {1}").format(
                    self.portal_domain, existing
                ),
                frappe.ValidationError,
            )

    def _validate_default_uniqueness(self):
        if not self.is_default or not self.is_active:
            return
        existing = frappe.db.get_value(
            "HD Brand",
            {
                "is_default": 1,
                "is_active": 1,
                "name": ["!=", self.name],
            },
            "name",
        )
        if existing:
            frappe.throw(
                _(
                    "Brand {0} is already marked as default. Only one active brand may be the default."
                ).format(existing),
                frappe.ValidationError,
            )

    def _validate_host_patterns(self):
        if not self.host_patterns:
            return
        normalized_lines = []
        for raw in (self.host_patterns or "").splitlines():
            line = raw.strip().lower()
            if not line:
                continue
            if line.count("*") > 1:
                frappe.throw(
                    _("Host pattern {0} contains more than one wildcard").format(line),
                    frappe.ValidationError,
                )
            if "*" in line:
                if not _HOST_WILDCARD_RE.match(line):
                    frappe.throw(
                        _(
                            "Host pattern {0} is invalid. Wildcards must be at the leftmost label only (e.g., *.tiberbu.health)."
                        ).format(line),
                        frappe.ValidationError,
                    )
            else:
                if not _HOST_EXACT_RE.match(line):
                    frappe.throw(
                        _(
                            "Host pattern {0} is invalid. Allowed characters: lowercase letters, digits, dot, hyphen."
                        ).format(line),
                        frappe.ValidationError,
                    )
            normalized_lines.append(line)
        # Persist normalized form so the resolver can do straight string compares.
        self.host_patterns = "\n".join(normalized_lines)

    def _validate_first_party_assets(self):
        for fieldname in ("logo", "wordmark", "favicon", "bg_image"):
            value = self.get(fieldname)
            if not value:
                continue
            if not value.startswith(_FIRST_PARTY_PREFIXES):
                frappe.throw(
                    _(
                        "Brand assets must be uploaded files or bundled app assets. External URLs are not allowed for {0}: {1}"
                    ).format(fieldname, value),
                    frappe.ValidationError,
                )
