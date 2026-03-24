# Copyright (c) 2026, Frappe Technologies and contributors
# For license information, please see license.txt

import frappe
from frappe.model.document import Document


class HDArticleVersion(Document):
    @staticmethod
    def get_next_version_number(article_name: str) -> int:
        """Return the next version number for the given article.

        Queries MAX(version_number) for the article and returns max + 1.
        Returns 1 if no versions exist yet.
        """
        result = frappe.db.sql(
            "SELECT MAX(version_number) FROM `tabHD Article Version` WHERE article = %s",
            article_name,
        )
        current_max = result[0][0] if result and result[0][0] is not None else 0
        return current_max + 1
