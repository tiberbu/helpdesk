import frappe
from frappe.model.document import Document


class HDNotification(Document):
    def format_message(self):
        user_from = self.get_from()
        if self.notification_type == "Mention":
            if self.reference_comment:
                return f"{user_from} mentioned you in a comment"
            return f"{user_from} mentioned you"
        return ""

    def get_from(self):
        return frappe.db.get_value(
            "User", {"name": self.user_from}, fieldname="full_name"
        )

    def get_button_label(self):
        if self.reference_comment:
            return "See Comment"
        return "Visit"

    def get_url(self):
        if self.notification_type in ("Ticket Reply", "Ticket Status Change"):
            res = "/helpdesk/my-tickets"
        else:
            res = "/helpdesk"
        if self.reference_ticket:
            res += "/" + str(self.reference_ticket)
        if self.reference_comment:
            res += "#" + self.reference_comment
        return frappe.utils.get_url(res)

    def parse_html(self):
        from bs4 import BeautifulSoup

        soup = BeautifulSoup(self.message, "html.parser")
        if soup.find("img"):
            img = soup.find("img")
            img["src"] = ("").join([frappe.utils.get_url(), img["src"]])
            return str(soup)
        return str(soup)

    def get_args(self):
        if self.notification_type == "Mention":
            return {
                "title": self.format_message(),
                "button_label": self.get_button_label(),
                "callback_url": self.get_url(),
                "comment": self.parse_html(),
            }

    def format_assignment_message(self):
        user_from = self.get_from()
        subject = ""
        if self.reference_ticket:
            subject = frappe.db.get_value("HD Ticket", self.reference_ticket, "subject") or ""
        if subject:
            return f"{user_from} assigned you ticket: {subject}"
        return f"{user_from} assigned you a ticket"

    def after_insert(self):
        # Emit real-time event for all notification types so the bell updates
        # and the frontend can play a sound / show a browser popup.
        REALTIME_TYPES = ("Mention", "Assignment", "Reaction", "Escalation", "SLA Warning", "SLA Breach", "Ticket Reply", "Ticket Status Change")
        if self.notification_type in REALTIME_TYPES:
            ticket_subject = ""
            if self.reference_ticket:
                ticket_subject = frappe.db.get_value(
                    "HD Ticket", self.reference_ticket, "subject"
                ) or ""

            frappe.publish_realtime(
                "helpdesk:new-notification",
                {
                    "notification_type": self.notification_type,
                    "reference_ticket": self.reference_ticket,
                    "ticket_subject": ticket_subject,
                    "user_from": self.get_from(),
                    "message": self.message,
                },
                user=self.user_to,
                after_commit=True,
            )

        if self.notification_type == "Assignment":
            skip_email_workflow = frappe.db.get_single_value(
                "HD Settings", "skip_email_workflow"
            )

            if skip_email_workflow:
                return

            # Deduplicate: only send one assignment email per agent per ticket
            dedup_key = f"hd:assign_email:{self.reference_ticket}:{self.user_to}"
            if frappe.cache.get_value(dedup_key):
                return
            frappe.cache.set_value(dedup_key, 1, expires_in_sec=86400)

            msg = self.format_assignment_message()
            ticket_url = self.get_url()
            frappe.sendmail(
                recipients=self.user_to,
                subject=msg,
                message=f"{msg}<br><a href='{ticket_url}'>View Ticket</a>",
                now=True,
            )
