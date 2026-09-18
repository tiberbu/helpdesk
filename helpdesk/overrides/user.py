"""
User override: send the password reset email immediately via SES,
before Frappe's default handler redacts the message in the Email Queue.
"""

import frappe
from frappe.core.doctype.user.user import User


class HelpdeskUser(User):
    def validate(self):
        # If the user is setting their own new_password (e.g. via the forced
        # password-change screen or a normal voluntary change), always clear
        # the flag — they should never remain flagged after choosing their
        # own password.
        #
        # If someone else (an admin) is setting this user's password, we no
        # longer force force_password_change to 1 automatically — it's a
        # real, visible checkbox on the User form now, and whatever value
        # was explicitly submitted (checked or unchecked) is respected as-is.
        # Scripts/console usage that want enforcement must set
        # doc.force_password_change = 1 explicitly before saving.
        if self.get("new_password") and frappe.session.user == self.name:
            self.force_password_change = 0
        super().validate()

    def password_reset_mail(self, link):
        from helpdesk.email.aws_ses_config import get_ses_config

        config = get_ses_config()
        if not config.enabled:
            return super().password_reset_mail(link)

        # Build and send the email immediately so SES delivers the full content
        # before Frappe overwrites the Email Queue message with the redacted version.
        reset_password_template = frappe.db.get_system_setting("reset_password_template")

        q = self.send_login_mail(
            frappe._("Password Reset"),
            "password_reset",
            {"link": link},
            now=True,
            custom_template=reset_password_template,
        )

        if q:
            from helpdesk.email.email_queue_override import SesAwareEmailQueue

            # Force-send immediately using the in-memory queue doc (full content).
            # This must happen before Frappe's after_commit callback, which runs
            # after the DB set_value below overwrites the message with a redaction.
            queue_doc = frappe.get_doc("Email Queue", q.name)
            # Preserve the original in-memory message so the send uses full content
            queue_doc.message = q.message
            queue_doc.__class__ = SesAwareEmailQueue
            queue_doc._send_with_ses()
            frappe.db.commit()

            # Now let Frappe do its redaction — the email is already sent
            import re
            raw_message = q.message
            parts = re.split(r"(?i)Dear", raw_message, maxsplit=1)
            if len(parts) > 1:
                redacted = parts[0] + "[THE FOLLOWING CONTENT HAS BEEN REDACTED FOR SECURITY REASONS]"
                frappe.db.set_value("Email Queue", q.name, "message", redacted, update_modified=False)

            # Remove the after_commit send that Frappe registered (email already sent)
            try:
                frappe.db.after_commit.callbacks.remove(q.send)
            except (ValueError, AttributeError):
                pass
