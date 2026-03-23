# Copyright (c) 2026, Frappe Technologies and Contributors
# See license.txt
# Story 1.5: @Mention Notifications in Internal Notes

import frappe
from frappe.tests.utils import FrappeTestCase

from helpdesk.test_utils import create_agent, make_ticket
from helpdesk.utils import extract_mentions


MENTION_CONTENT = lambda email, name: (
    f'<p>Hey <span class="mention" data-type="mention" '
    f'data-id="{email}" data-label="{name}">@{name}</span>, please look at this.</p>'
)

MULTI_MENTION_CONTENT = lambda agents: (
    "<p>"
    + " ".join(
        f'<span class="mention" data-type="mention" data-id="{e}" data-label="{n}">@{n}</span>'
        for e, n in agents
    )
    + "</p>"
)


class TestMentionNotificationsInInternalNotes(FrappeTestCase):
    """
    Story 1.5: Verify @mention notifications are created and delivered
    when agents are mentioned in internal notes (is_internal=1 comments).
    """

    def setUp(self):
        frappe.set_user("Administrator")
        frappe.db.set_single_value("HD Settings", "skip_email_workflow", 1)

        self.author_email = "mention_author@example.com"
        self.mentioned_email = "mention_target@example.com"
        self.second_mentioned_email = "mention_target2@example.com"

        create_agent(self.author_email)
        create_agent(self.mentioned_email)
        create_agent(self.second_mentioned_email)

        self.ticket = make_ticket(
            subject="Mention Notification Test Ticket",
            raised_by=self.author_email,
        )

    def tearDown(self):
        frappe.set_user("Administrator")
        frappe.db.set_single_value("HD Settings", "skip_email_workflow", 0)

        # Clean up notifications
        for notif in frappe.get_all(
            "HD Notification",
            filters={"reference_ticket": self.ticket.name},
            pluck="name",
        ):
            frappe.delete_doc("HD Notification", notif, force=True)

        # Clean up comments
        for comment in frappe.get_all(
            "HD Ticket Comment",
            filters={"reference_ticket": self.ticket.name},
            pluck="name",
        ):
            frappe.delete_doc("HD Ticket Comment", comment, force=True)

        if frappe.db.exists("HD Ticket", self.ticket.name):
            frappe.delete_doc("HD Ticket", self.ticket.name, force=True)

        for email in [
            self.author_email,
            self.mentioned_email,
            self.second_mentioned_email,
        ]:
            if frappe.db.exists("User", email):
                frappe.delete_doc("User", email, force=True)

    # ------------------------------------------------------------------ #
    # extract_mentions() utility                                            #
    # ------------------------------------------------------------------ #

    def test_extract_mentions_returns_mentioned_email(self):
        """extract_mentions() must parse data-id from mention spans."""
        html = MENTION_CONTENT(self.mentioned_email, "Target Agent")
        mentions = extract_mentions(html)
        self.assertEqual(len(mentions), 1)
        self.assertEqual(mentions[0].email, self.mentioned_email)
        self.assertEqual(mentions[0].full_name, "Target Agent")

    def test_extract_mentions_empty_content(self):
        """extract_mentions() must return an empty list for None/empty HTML."""
        self.assertEqual(extract_mentions(None), [])
        self.assertEqual(extract_mentions(""), [])
        self.assertEqual(extract_mentions("<p>No mentions here</p>"), [])

    def test_extract_mentions_multiple(self):
        """extract_mentions() must return all mentioned agents."""
        html = MULTI_MENTION_CONTENT([
            (self.mentioned_email, "Target Agent"),
            (self.second_mentioned_email, "Second Agent"),
        ])
        mentions = extract_mentions(html)
        emails = {m.email for m in mentions}
        self.assertIn(self.mentioned_email, emails)
        self.assertIn(self.second_mentioned_email, emails)

    # ------------------------------------------------------------------ #
    # Notification creation for internal notes                             #
    # ------------------------------------------------------------------ #

    def test_mention_in_internal_note_creates_hd_notification(self):
        """
        Story 1.5 core: Saving an internal note with @mention must create
        an HD Notification of type 'Mention' for the mentioned agent.
        """
        frappe.set_user(self.author_email)
        content = MENTION_CONTENT(self.mentioned_email, "Target Agent")

        comment = frappe.get_doc({
            "doctype": "HD Ticket Comment",
            "reference_ticket": self.ticket.name,
            "content": content,
            "commented_by": self.author_email,
            "owner": self.author_email,
            "is_internal": 1,
        }).insert(ignore_permissions=True)

        notifications = frappe.get_all(
            "HD Notification",
            filters={
                "reference_comment": comment.name,
                "notification_type": "Mention",
                "user_to": self.mentioned_email,
            },
            fields=["name", "user_from", "user_to", "reference_ticket"],
        )

        self.assertEqual(
            len(notifications), 1,
            "Exactly one Mention notification must be created for the mentioned agent",
        )
        notif = notifications[0]
        self.assertEqual(notif.user_from, self.author_email)
        self.assertEqual(notif.user_to, self.mentioned_email)
        self.assertEqual(str(notif.reference_ticket), str(self.ticket.name))

    def test_mention_notification_includes_ticket_link(self):
        """
        The notification's get_url() must return a URL containing the ticket ID,
        satisfying the 'link to the ticket' AC requirement.
        """
        frappe.set_user(self.author_email)
        content = MENTION_CONTENT(self.mentioned_email, "Target Agent")

        comment = frappe.get_doc({
            "doctype": "HD Ticket Comment",
            "reference_ticket": self.ticket.name,
            "content": content,
            "commented_by": self.author_email,
            "owner": self.author_email,
            "is_internal": 1,
        }).insert(ignore_permissions=True)

        notif_name = frappe.get_value(
            "HD Notification",
            {"reference_comment": comment.name, "notification_type": "Mention"},
            "name",
        )
        self.assertIsNotNone(notif_name, "Notification must exist")

        notif = frappe.get_doc("HD Notification", notif_name)
        url = notif.get_url()
        self.assertIn(str(self.ticket.name), url)
        self.assertIn("/helpdesk/tickets/", url)

    def test_mention_notification_content_preview(self):
        """
        The notification message field must contain the note's HTML content
        as a preview (stored by HasMentions.notify_mentions).
        """
        frappe.set_user(self.author_email)
        content = MENTION_CONTENT(self.mentioned_email, "Target Agent")

        comment = frappe.get_doc({
            "doctype": "HD Ticket Comment",
            "reference_ticket": self.ticket.name,
            "content": content,
            "commented_by": self.author_email,
            "owner": self.author_email,
            "is_internal": 1,
        }).insert(ignore_permissions=True)

        notif_name = frappe.get_value(
            "HD Notification",
            {"reference_comment": comment.name, "notification_type": "Mention"},
            "name",
        )
        notif = frappe.get_doc("HD Notification", notif_name)
        # The message field stores the full comment content
        self.assertIsNotNone(notif.message)
        self.assertTrue(len(notif.message) > 0)

    # ------------------------------------------------------------------ #
    # Self-mention prevention                                              #
    # ------------------------------------------------------------------ #

    def test_no_notification_for_self_mention_in_internal_note(self):
        """
        Story 1.5 AC #8: An agent mentioning themselves must NOT receive
        a notification.
        """
        frappe.set_user(self.author_email)
        content = MENTION_CONTENT(self.author_email, "Author Agent")

        comment = frappe.get_doc({
            "doctype": "HD Ticket Comment",
            "reference_ticket": self.ticket.name,
            "content": content,
            "commented_by": self.author_email,
            "owner": self.author_email,
            "is_internal": 1,
        }).insert(ignore_permissions=True)

        notifications = frappe.get_all(
            "HD Notification",
            filters={
                "reference_comment": comment.name,
                "notification_type": "Mention",
                "user_to": self.author_email,
            },
        )
        self.assertEqual(
            len(notifications), 0,
            "Self-mentions must NOT generate a notification",
        )

    # ------------------------------------------------------------------ #
    # Duplicate mention deduplication                                      #
    # ------------------------------------------------------------------ #

    def test_duplicate_mention_creates_only_one_notification(self):
        """
        Mentioning the same agent twice in one note must produce only one
        notification (deduplication in HasMentions.notify_mentions).
        """
        frappe.set_user(self.author_email)
        content = (
            f'<p>'
            f'<span class="mention" data-type="mention" data-id="{self.mentioned_email}" '
            f'data-label="Target Agent">@Target Agent</span> and again '
            f'<span class="mention" data-type="mention" data-id="{self.mentioned_email}" '
            f'data-label="Target Agent">@Target Agent</span>'
            f'</p>'
        )

        comment = frappe.get_doc({
            "doctype": "HD Ticket Comment",
            "reference_ticket": self.ticket.name,
            "content": content,
            "commented_by": self.author_email,
            "owner": self.author_email,
            "is_internal": 1,
        }).insert(ignore_permissions=True)

        notifications = frappe.get_all(
            "HD Notification",
            filters={
                "reference_comment": comment.name,
                "notification_type": "Mention",
                "user_to": self.mentioned_email,
            },
        )
        self.assertEqual(
            len(notifications), 1,
            "Duplicate mentions of the same agent must yield exactly one notification",
        )

    # ------------------------------------------------------------------ #
    # Multiple distinct agents mentioned                                    #
    # ------------------------------------------------------------------ #

    def test_multiple_agents_each_get_notification(self):
        """
        Mentioning two different agents must produce one notification per agent.
        """
        frappe.set_user(self.author_email)
        content = MULTI_MENTION_CONTENT([
            (self.mentioned_email, "Target Agent"),
            (self.second_mentioned_email, "Second Agent"),
        ])

        comment = frappe.get_doc({
            "doctype": "HD Ticket Comment",
            "reference_ticket": self.ticket.name,
            "content": content,
            "commented_by": self.author_email,
            "owner": self.author_email,
            "is_internal": 1,
        }).insert(ignore_permissions=True)

        for email in [self.mentioned_email, self.second_mentioned_email]:
            notifications = frappe.get_all(
                "HD Notification",
                filters={
                    "reference_comment": comment.name,
                    "notification_type": "Mention",
                    "user_to": email,
                },
            )
            self.assertEqual(
                len(notifications), 1,
                f"Agent {email} must receive exactly one notification",
            )

    # ------------------------------------------------------------------ #
    # Edit: only NEW mentions trigger notifications                        #
    # ------------------------------------------------------------------ #

    def test_editing_note_notifies_only_new_mentions(self):
        """
        Editing an internal note to add a second mention must notify only the
        newly-added agent, not re-notify the already-mentioned agent.
        """
        frappe.set_user(self.author_email)
        initial_content = MENTION_CONTENT(self.mentioned_email, "Target Agent")

        comment = frappe.get_doc({
            "doctype": "HD Ticket Comment",
            "reference_ticket": self.ticket.name,
            "content": initial_content,
            "commented_by": self.author_email,
            "owner": self.author_email,
            "is_internal": 1,
        }).insert(ignore_permissions=True)

        # Verify first mention notification exists
        first_notifications = frappe.get_all(
            "HD Notification",
            filters={
                "reference_comment": comment.name,
                "notification_type": "Mention",
            },
            fields=["user_to"],
        )
        self.assertEqual(len(first_notifications), 1)
        self.assertEqual(first_notifications[0].user_to, self.mentioned_email)

        # Edit to add a second mention
        updated_content = MULTI_MENTION_CONTENT([
            (self.mentioned_email, "Target Agent"),
            (self.second_mentioned_email, "Second Agent"),
        ])
        comment.content = updated_content
        comment.save(ignore_permissions=True)
        comment.reload()

        # Total notifications: 2 total (one per unique agent)
        all_notifications = frappe.get_all(
            "HD Notification",
            filters={
                "reference_comment": comment.name,
                "notification_type": "Mention",
            },
            fields=["user_to"],
        )
        notified_users = {n.user_to for n in all_notifications}
        self.assertIn(self.mentioned_email, notified_users)
        self.assertIn(self.second_mentioned_email, notified_users)

        # The first agent must NOT have a second notification (dedup)
        first_agent_notifs = [
            n for n in all_notifications if n.user_to == self.mentioned_email
        ]
        self.assertEqual(
            len(first_agent_notifs), 1,
            "Already-mentioned agent must not receive a second notification on edit",
        )

    # ------------------------------------------------------------------ #
    # Internal note via new_internal_note() API                            #
    # ------------------------------------------------------------------ #

    def test_new_internal_note_method_triggers_mention_notification(self):
        """
        Using the new_internal_note() whitelist method (the API called by the UI)
        must also trigger mention notifications.
        """
        frappe.set_user(self.author_email)
        content = MENTION_CONTENT(self.mentioned_email, "Target Agent")

        ticket_doc = frappe.get_doc("HD Ticket", self.ticket.name)
        ticket_doc.new_internal_note(content=content)

        comment = frappe.get_last_doc(
            "HD Ticket Comment",
            filters={
                "reference_ticket": self.ticket.name,
                "is_internal": 1,
            },
        )

        notifications = frappe.get_all(
            "HD Notification",
            filters={
                "reference_comment": comment.name,
                "notification_type": "Mention",
                "user_to": self.mentioned_email,
            },
        )
        self.assertEqual(
            len(notifications), 1,
            "new_internal_note() must trigger a mention notification",
        )

        # Cleanup the created comment
        frappe.set_user("Administrator")
        frappe.delete_doc("HD Ticket Comment", comment.name, force=True)
        for n in notifications:
            frappe.delete_doc("HD Notification", n.name, force=True)

    # ------------------------------------------------------------------ #
    # HDNotification.format_message and get_url                           #
    # ------------------------------------------------------------------ #

    def test_notification_format_message_for_mention(self):
        """
        HDNotification.format_message() must return a human-readable string
        for Mention notifications.
        """
        frappe.set_user(self.author_email)
        content = MENTION_CONTENT(self.mentioned_email, "Target Agent")

        comment = frappe.get_doc({
            "doctype": "HD Ticket Comment",
            "reference_ticket": self.ticket.name,
            "content": content,
            "commented_by": self.author_email,
            "owner": self.author_email,
            "is_internal": 1,
        }).insert(ignore_permissions=True)

        notif_name = frappe.get_value(
            "HD Notification",
            {"reference_comment": comment.name, "notification_type": "Mention"},
            "name",
        )
        notif = frappe.get_doc("HD Notification", notif_name)

        msg = notif.format_message()
        self.assertIn("mentioned", msg.lower())
        self.assertIsNotNone(msg)
        self.assertTrue(len(msg) > 0)
