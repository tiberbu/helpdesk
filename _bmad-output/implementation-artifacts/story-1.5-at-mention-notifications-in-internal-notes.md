# Story 1.5: @Mention Notifications in Internal Notes

Status: ready-for-dev

## Story

As a support agent,
I want to @mention other agents in internal notes,
so that they are notified and can quickly find the relevant ticket.

## Acceptance Criteria

1. **[@Mention Autocomplete Trigger]** Given an agent has the internal note composer open (Story 1.4 prerequisite), when they type the `@` character followed by one or more characters, then an autocomplete dropdown appears overlaid on the editor showing a filtered list of agent names matching the typed characters (case-insensitive prefix/substring match). The dropdown is dismissed when the agent presses `Escape`, clicks outside the dropdown, or completes a selection.

2. **[Autocomplete Dropdown — Agent List Population]** Given the autocomplete dropdown is shown, when it renders, then it lists only users with the "HD Agent" or "System Manager" role (not all system users). Each entry shows the agent's full name and optionally their avatar/initials. The list is ordered alphabetically by full name and is limited to the 10 best matches to avoid overwhelming the UI.

3. **[Autocomplete Dropdown — Keyboard Navigation]** Given the autocomplete dropdown is visible, when the agent uses the keyboard, then:
   - Arrow Up / Arrow Down moves selection through the list
   - `Enter` or `Tab` confirms the selected agent and inserts the mention
   - `Escape` dismisses the dropdown without inserting anything
   - The dropdown must not block form submission or conflict with other shortcuts

4. **[Mention Insertion — Markup in Note Content]** Given an agent selects an agent name from the autocomplete dropdown, when the selection is confirmed, then:
   - The typed `@partial` text in the editor is replaced with `@{full_name}` (e.g., `@Rajesh Kumar`)
   - The inserted mention is visually distinct in the editor (e.g., rendered as a chip or highlighted span)
   - The raw content stored in the communication record includes the mention markup: `<span data-mention="user@email.com">@Rajesh Kumar</span>` to preserve the email reference for backend parsing

5. **[Mention Detection on Note Save — Backend Parsing]** Given a submitted internal note contains one or more `<span data-mention="...">` elements, when the `add_internal_note` API handler processes the note, then:
   - All mentioned agent emails are extracted from `data-mention` attributes in the HTML content
   - For each extracted agent email, a notification job is enqueued
   - Duplicate mentions of the same agent (multiple `@Rajesh Kumar` in one note) result in only one notification per agent per note
   - Mentions of non-existent users or non-Agent users are silently ignored (no error raised)

6. **[In-App Notification — Delivery]** Given an agent is mentioned in an internal note that has been saved, when the notification job runs, then:
   - A Frappe notification record is created for the mentioned agent using `frappe.get_doc("Notification Log", ...)` or `frappe.publish_realtime` via the `notifications.ts` Pinia store pipeline
   - The notification is delivered to the mentioned agent's notification bell (in-app toast + unread badge increment) via Socket.IO on room `agent:{agent_email}` (per ADR-12 room naming)
   - The notification job runs on the `short` queue (high priority, per ADR-12 queue strategy)

7. **[In-App Notification — Content]** Given the notification is delivered to the mentioned agent, when they view the notification, then:
   - The notification title is: `"You were mentioned in a note on [Ticket Subject]"` (e.g., `"You were mentioned in a note on Password Reset Issue"`)
   - The notification body shows a preview of the note content (first 200 characters of plain-text content, stripped of HTML tags)
   - The notification includes a direct link to the ticket: `/helpdesk/tickets/{ticket_id}`
   - Clicking the notification navigates the agent directly to the relevant ticket

8. **[Self-Mention — No Notification]** Given an agent types `@` and selects their own name in the autocomplete, when the note is saved, then no notification is dispatched for the author's own mention (an agent mentioning themselves generates no notification).

9. **[Notification Not Sent for Non-Internal Notes]** Given a non-internal (customer-facing) communication is submitted with `@name` text in the body, when it is processed, then the mention detection and notification logic does NOT fire. Mention parsing and notification dispatch is scoped exclusively to records where `is_internal = 1`.

10. **[Mentioned Agent Not Online — Notification Persists]** Given a mentioned agent is currently offline or not actively using the desk when the note is saved, when the notification job runs, then the Frappe Notification Log record is still created so the agent sees it when they next log in (persistent notification, not ephemeral socket-only).

11. **[Autocomplete API — Agent List Endpoint]** Given the frontend needs to populate the autocomplete dropdown, when the agent types `@{partial}`, then a debounced API call is made to a whitelisted endpoint `helpdesk.api.ticket.get_mentionable_agents(query)` that returns agents matching the query. The endpoint enforces Agent role on the caller (only agents can retrieve the agent list) and returns `[{name, full_name, email, user_image}]`.

12. **[Unit Tests — Mention Detection and Notification]** Given the @mention implementation, when the test suite runs, then unit tests exist that cover:
    - Parsing `<span data-mention="user@email.com">` from note HTML and extracting the correct email
    - Enqueuing exactly one notification per unique mentioned agent
    - No notification enqueued when the author mentions themselves
    - No mention parsing when `is_internal = 0`
    - Notification job creates a Frappe Notification Log entry with correct title, preview, and ticket link
    - `get_mentionable_agents` returns only HD Agent / System Manager role users
    - Minimum 80% line coverage on all new backend Python code (NFR-M-01)

## Tasks / Subtasks

- [ ] Task 1 — Implement `get_mentionable_agents` API endpoint (AC: #11, #2)
  - [ ] 1.1 In `helpdesk/api/ticket.py`, add a whitelisted method:
    ```python
    @frappe.whitelist()
    def get_mentionable_agents(query: str = "") -> list:
        """Return agents matching query for @mention autocomplete.
        Only callable by HD Agent or System Manager roles.
        """
        frappe.has_permission("HD Ticket", "write", throw=True)
        agents = frappe.get_all(
            "User",
            filters=[
                ["Has Role", "role", "in", ["HD Agent", "System Manager"]],
                ["full_name", "like", f"%{query}%"],
                ["enabled", "=", 1],
                ["name", "!=", frappe.session.user],  # Optional: exclude self or include for self-mention UI
            ],
            fields=["name as email", "full_name", "user_image"],
            limit=10,
            order_by="full_name asc",
        )
        return agents
    ```
  - [ ] 1.2 Apply input sanitisation: strip special characters from `query` before building the LIKE filter to prevent SQL injection via the ORM. Maximum query length: 100 characters.
  - [ ] 1.3 Cache results for the same `query` for 30 seconds using Frappe's cache (`frappe.cache().get_value` / `set_value`) to reduce DB hits during rapid typing.

- [ ] Task 2 — Implement @mention autocomplete in the internal note editor (AC: #1, #2, #3, #4)
  - [ ] 2.1 In the internal note composer component (created in Story 1.4, likely `desk/src/pages/ticket/` or `desk/src/components/ticket/`), add `@` trigger detection to the `TextEditor` (frappe-ui Tiptap-based editor). Use Tiptap's `Mention` extension (already available in the frappe-ui Tiptap build, or install `@tiptap/extension-mention`) for the `@` trigger handling.
  - [ ] 2.2 Configure the Mention extension:
    ```typescript
    import Mention from '@tiptap/extension-mention'
    import { buildMentionSuggestion } from '@/composables/useMentionSuggestion'

    // In editor setup:
    extensions: [
      // ...existing extensions...
      Mention.configure({
        HTMLAttributes: { class: 'mention' },
        renderLabel({ node }) { return `@${node.attrs.label}` },
        suggestion: buildMentionSuggestion(),
      }),
    ]
    ```
  - [ ] 2.3 Create `desk/src/composables/useMentionSuggestion.ts` that implements the Tiptap suggestion config:
    - `items({ query })`: debounced (200ms) call to `helpdesk.api.ticket.get_mentionable_agents` with the partial query; returns `[{id: email, label: full_name, image: user_image}]`
    - `render()`: returns a Vue popup component reference (`MentionDropdown.vue`) using Tiptap's `tippy.js` positioning (already used in frappe-ui)
  - [ ] 2.4 Create `desk/src/components/ticket/MentionDropdown.vue` — the autocomplete popup component:
    - Renders a list of agent names with avatar/initials
    - Highlights the currently selected item
    - Handles Arrow Up / Arrow Down / Enter / Tab / Escape keyboard events (delegated from Tiptap's suggestion `onKeyDown` callback)
    - Styled with Tailwind (white bg, border, shadow, rounded, max-height with scroll)
    - WCAG 2.1 AA compliant: `role="listbox"`, `aria-selected` on highlighted item, `aria-label="Mention an agent"` on container (NFR-U-04)
  - [ ] 2.5 Verify the Mention extension serialises to HTML as `<span data-mention="{agent_email}" data-label="{full_name}">@{full_name}</span>` when the editor content is saved, so the backend parser can reliably extract mentioned emails.
  - [ ] 2.6 Style inserted mentions with `@/components/ticket/MentionChip.vue` inline — or rely on Tiptap's Mention node rendering — using Tailwind class `bg-blue-100 text-blue-700 rounded px-1 py-0.5 text-sm font-medium` to make `@names` visually distinct from surrounding text.

- [ ] Task 3 — Implement backend mention detection and notification dispatch (AC: #5, #6, #7, #8, #9, #10)
  - [ ] 3.1 Create `helpdesk/helpdesk/notifications/mention_handler.py`:
    ```python
    import frappe
    import re
    from html.parser import HTMLParser

    def extract_mentions(html_content: str) -> list[str]:
        """Extract agent emails from <span data-mention="..."> in HTML content.
        Returns a deduplicated list of email addresses.
        """
        emails = re.findall(r'data-mention="([^"]+)"', html_content or "")
        return list(set(emails))  # deduplicate

    def dispatch_mention_notifications(
        note_content: str,
        ticket_id: str,
        ticket_subject: str,
        author_email: str,
    ) -> None:
        """Extract @mentions from note_content and enqueue notification jobs."""
        mentioned_emails = extract_mentions(note_content)
        for email in mentioned_emails:
            if email == author_email:
                continue  # Skip self-mentions (AC #8)
            if not frappe.db.exists("User", {"name": email, "enabled": 1}):
                continue  # Skip non-existent users (AC #5)
            frappe.enqueue(
                "helpdesk.helpdesk.notifications.mention_handler.send_mention_notification",
                queue="short",
                timeout=30,
                email=email,
                ticket_id=ticket_id,
                ticket_subject=ticket_subject,
                note_preview=_get_note_preview(note_content),
                author=frappe.get_value("User", author_email, "full_name") or author_email,
            )

    def _get_note_preview(html_content: str, max_length: int = 200) -> str:
        """Strip HTML tags and return first max_length characters as plain text preview."""
        import bleach
        plain = bleach.clean(html_content or "", tags=[], strip=True).strip()
        return plain[:max_length] + ("..." if len(plain) > max_length else "")

    def send_mention_notification(
        email: str,
        ticket_id: str,
        ticket_subject: str,
        note_preview: str,
        author: str,
    ) -> None:
        """Create Frappe Notification Log and publish real-time event for @mention."""
        # Create persistent notification log entry
        notif = frappe.get_doc({
            "doctype": "Notification Log",
            "subject": f"You were mentioned in a note on {ticket_subject}",
            "email_content": note_preview,
            "document_type": "HD Ticket",
            "document_name": ticket_id,
            "from_user": frappe.session.user,
            "for_user": email,
            "type": "Mention",
            "read": 0,
        })
        notif.insert(ignore_permissions=True)
        frappe.db.commit()

        # Publish real-time event to the agent's private Socket.IO room (ADR-12)
        frappe.publish_realtime(
            event="mention_notification",
            message={
                "ticket_id": ticket_id,
                "ticket_subject": ticket_subject,
                "preview": note_preview,
                "author": author,
                "link": f"/helpdesk/tickets/{ticket_id}",
                "notification_name": notif.name,
            },
            user=email,
        )
    ```
  - [ ] 3.2 Create `helpdesk/helpdesk/notifications/__init__.py` (empty or with package imports).
  - [ ] 3.3 Integrate `dispatch_mention_notifications` into the `add_internal_note` API method (from Story 1.4):
    ```python
    # In helpdesk/api/ticket.py — add_internal_note function, after comm.insert(...)
    from helpdesk.helpdesk.notifications.mention_handler import dispatch_mention_notifications

    if comm.is_internal:  # Only for internal notes (AC #9)
        dispatch_mention_notifications(
            note_content=content,
            ticket_id=ticket_id,
            ticket_subject=frappe.db.get_value("HD Ticket", ticket_id, "subject"),
            author_email=frappe.session.user,
        )
    ```
  - [ ] 3.4 Also hook into `HD Ticket`'s `doc_events` for the communication `after_insert` event as a belt-and-suspenders fallback. Add to `hooks.py`:
    ```python
    doc_events = {
        # ...existing events...
        "Communication": {
            "after_insert": "helpdesk.helpdesk.notifications.mention_handler.on_communication_insert",
        }
    }
    ```
    And create `on_communication_insert(doc, method=None)` that calls `dispatch_mention_notifications` if `doc.is_internal == 1` and `doc.reference_doctype == "HD Ticket"`.

- [ ] Task 4 — Frontend notification handling (AC: #6, #7)
  - [ ] 4.1 In `desk/src/stores/notifications.ts` (new Pinia store per ADR-11), add a handler for the `mention_notification` Socket.IO real-time event:
    ```typescript
    // In notifications store setup
    frappe.realtime.on('mention_notification', (data) => {
      store.addNotification({
        type: 'mention',
        title: `You were mentioned in a note on ${data.ticket_subject}`,
        body: data.preview,
        link: data.link,
        ticketId: data.ticket_id,
        notificationName: data.notification_name,
      })
      store.incrementUnreadCount()
      showToast(data)  // Display toast notification
    })
    ```
  - [ ] 4.2 If `notifications.ts` Pinia store does not yet exist (it's new in Phase 1 per ADR-11), create it with state: `notifications: []`, `unreadCount: number`; actions: `addNotification`, `markRead`, `markAllRead`, `incrementUnreadCount`.
  - [ ] 4.3 Ensure the notification bell / badge component in the desk header subscribes to `unreadCount` from the store and increments the badge visually when new mentions arrive.
  - [ ] 4.4 Clicking a mention notification navigates to `/helpdesk/tickets/{ticket_id}` via Vue Router's `router.push()` and calls `markRead(notificationName)` which makes a backend call to mark the Notification Log entry as read.

- [ ] Task 5 — Write unit tests for mention detection and notification delivery (AC: #12)
  - [ ] 5.1 Create `helpdesk/helpdesk/notifications/test_mention_handler.py`:
    ```python
    import frappe
    from frappe.tests.utils import FrappeTestCase
    from helpdesk.helpdesk.notifications.mention_handler import (
        extract_mentions,
        dispatch_mention_notifications,
        _get_note_preview,
    )

    class TestMentionHandler(FrappeTestCase):
        def setUp(self):
            # Create test ticket
            self.ticket = frappe.get_doc({
                "doctype": "HD Ticket",
                "subject": "Test Ticket for Mentions",
                "raised_by": "customer@test.com",
            }).insert(ignore_permissions=True)
            # Create test agent users
            self._create_test_user("agent.one@test.com", "Agent One", "HD Agent")
            self._create_test_user("agent.two@test.com", "Agent Two", "HD Agent")

        def test_extract_mentions_single(self):
            html = '<p>Hey <span data-mention="agent.one@test.com">@Agent One</span></p>'
            result = extract_mentions(html)
            self.assertIn("agent.one@test.com", result)
            self.assertEqual(len(result), 1)

        def test_extract_mentions_multiple(self):
            html = ('<p><span data-mention="agent.one@test.com">@Agent One</span> '
                    'and <span data-mention="agent.two@test.com">@Agent Two</span></p>')
            result = extract_mentions(html)
            self.assertEqual(set(result), {"agent.one@test.com", "agent.two@test.com"})

        def test_extract_mentions_deduplicated(self):
            html = ('<p><span data-mention="agent.one@test.com">@Agent One</span> '
                    '<span data-mention="agent.one@test.com">@Agent One</span></p>')
            result = extract_mentions(html)
            self.assertEqual(len(result), 1)

        def test_no_notification_for_self_mention(self):
            frappe.set_user("agent.one@test.com")
            html = '<p><span data-mention="agent.one@test.com">@Agent One</span></p>'
            # Enqueue spy: check no job enqueued for agent.one
            with self.assertRaises(Exception) if False else self.subTest():
                dispatch_mention_notifications(
                    note_content=html,
                    ticket_id=self.ticket.name,
                    ticket_subject=self.ticket.subject,
                    author_email="agent.one@test.com",
                )
            # Verify no notification log created for agent.one as recipient
            logs = frappe.get_all("Notification Log",
                                   filters={"for_user": "agent.one@test.com",
                                            "document_name": self.ticket.name})
            self.assertEqual(len(logs), 0)
            frappe.set_user("Administrator")

        def test_notification_log_created_for_mentioned_agent(self):
            frappe.set_user("agent.two@test.com")
            html = '<p><span data-mention="agent.one@test.com">@Agent One</span></p>'
            # Call synchronously for test (bypass queue)
            from helpdesk.helpdesk.notifications.mention_handler import send_mention_notification
            send_mention_notification(
                email="agent.one@test.com",
                ticket_id=self.ticket.name,
                ticket_subject=self.ticket.subject,
                note_preview="Test preview",
                author="Agent Two",
            )
            log = frappe.get_all("Notification Log",
                                  filters={"for_user": "agent.one@test.com",
                                           "document_name": self.ticket.name})
            self.assertEqual(len(log), 1)
            frappe.set_user("Administrator")

        def test_note_preview_strips_html(self):
            html = '<p><b>Important</b> issue with <a href="#">system</a></p>'
            preview = _get_note_preview(html, max_length=50)
            self.assertNotIn('<b>', preview)
            self.assertNotIn('<a', preview)
            self.assertIn('Important', preview)

        def test_note_preview_truncates(self):
            long_text = '<p>' + 'x' * 300 + '</p>'
            preview = _get_note_preview(long_text, max_length=200)
            self.assertTrue(len(preview) <= 203)  # 200 + "..."
            self.assertTrue(preview.endswith('...'))

        def test_get_mentionable_agents_returns_only_agents(self):
            frappe.set_user("agent.one@test.com")
            from helpdesk.api.ticket import get_mentionable_agents
            result = get_mentionable_agents(query="")
            emails = [r['email'] for r in result]
            # Non-agent users should not appear
            self.assertNotIn("customer@test.com", emails)
            frappe.set_user("Administrator")

        def _create_test_user(self, email, full_name, role):
            if not frappe.db.exists("User", email):
                user = frappe.get_doc({
                    "doctype": "User",
                    "email": email,
                    "full_name": full_name,
                    "first_name": full_name.split()[0],
                    "send_welcome_email": 0,
                    "roles": [{"role": role}],
                }).insert(ignore_permissions=True)

        def tearDown(self):
            frappe.db.rollback()
    ```
  - [ ] 5.2 Use `frappe.tests.utils.FrappeTestCase` as base class (consistent with Story 1.4 testing pattern).
  - [ ] 5.3 Run tests with:
    ```bash
    bench --site <site> run-tests --module helpdesk.helpdesk.notifications.test_mention_handler
    ```
  - [ ] 5.4 Ensure test coverage meets NFR-M-01 (minimum 80% line coverage on all new backend Python code).

## Dev Notes

### Architecture Patterns

- **Direct Dependency on Story 1.4:** Story 1.5 builds entirely on the internal note infrastructure created in Story 1.4. The `is_internal` flag, `add_internal_note` API method, `InternalNote.vue` component, and the Tiptap-based `TextEditor` are all prerequisites. Confirm Story 1.4 is merged before starting this story. [Source: _bmad-output/implementation-artifacts/story-1.4-internal-notes-on-tickets.md#Constraints]

- **@Mention Notification Queue (ADR-12):** Notification jobs for @mentions are classified as `short` queue (high priority, real-time) in the architecture. Do NOT enqueue to `default` or `long`. [Source: architecture.md#ADR-12]
  ```
  Queue    | Jobs                                      | Priority | Frequency
  short    | @mention notifications, SLA breach notif  | High     | Real-time / scheduled
  ```

- **Socket.IO Room for Agent Notifications (ADR-12):** Per the room naming convention, private agent notifications use the room `agent:{agent_email}`. Use `frappe.publish_realtime(event, message, user=email)` — Frappe maps the `user` param to the `agent:{email}` room automatically. Do NOT use a broadcast or team room for private @mention delivery. [Source: architecture.md#Communication Patterns]

- **Frappe Notification Log DocType:** Use Frappe's built-in `Notification Log` DocType for persistent notifications. This integrates with Frappe's existing notification bell UI in the toolbar without requiring a custom notification store from scratch. The `notifications.ts` Pinia store (ADR-11) should sync with the Notification Log and layer real-time delivery on top. [Source: architecture.md#ADR-11]

- **Tiptap Mention Extension:** The frappe-ui TextEditor is Tiptap-based. The `@tiptap/extension-mention` package provides the `@` trigger, dropdown positioning (via tippy.js, already a Tiptap dependency), and serialization hooks. Check the existing `package.json` / `yarn.lock` in `desk/` to confirm if `@tiptap/extension-mention` is already present before adding a new dependency. [Source: architecture.md#ADR-09, Vue 3 + frappe-ui tech stack]

- **HTML Mention Attribute Convention:** The data attribute `data-mention="{agent_email}"` is the agreed interface between frontend and backend. The frontend Tiptap Mention node serializes to this format; the backend `extract_mentions()` parser reads it. This contract must be maintained consistently. If the Tiptap extension uses a different default attribute (e.g., `data-id`), configure it explicitly to use `data-mention`.

- **Self-Mention Prevention (AC #8):** Agents can visually type and insert `@TheirOwnName` in the UI — this is not blocked at the UI layer (it would be confusing UX). The prevention is server-side only: `dispatch_mention_notifications` skips `email == author_email`. The UI should include the author in the autocomplete dropdown (they may be typing their own name to reference themselves in prose), but the notification is simply not sent.

- **Scope to Internal Notes Only (AC #9):** The mention parsing and notification dispatch is ONLY for `is_internal = 1` communications. Never parse `@mentions` in customer-facing replies. This is enforced in the `on_communication_insert` hook and in the `add_internal_note` API method. [Source: FR-IN-01, NFR-SE-01]

- **Performance — Debounced Autocomplete (AC #11):** The autocomplete API call is debounced 200ms to avoid spamming the server while the agent types. Use Vue's `watchEffect` with a debounce utility or Tiptap's built-in suggestion debounce to implement this. The `get_mentionable_agents` endpoint uses a LIKE query which benefits from a `full_name` index — confirm the index exists or add one.

- **Notification Bell Integration:** The Frappe desk already has a notification bell component driven by `Notification Log`. The `notifications.ts` Pinia store should subscribe to the `notification_alert` and `mention_notification` real-time events and reflect the count in the bell. Inspect the existing desk header component to find the notification bell and its data source before creating a parallel implementation.

### Files to Create / Modify

| Action | Path | Notes |
|--------|------|-------|
| Create | `helpdesk/helpdesk/notifications/__init__.py` | Package init |
| Create | `helpdesk/helpdesk/notifications/mention_handler.py` | Mention parsing + notification dispatch |
| Create | `helpdesk/helpdesk/notifications/test_mention_handler.py` | Unit tests |
| Modify | `helpdesk/api/ticket.py` | Add `get_mentionable_agents` endpoint; integrate mention dispatch in `add_internal_note` |
| Modify | `helpdesk/hooks.py` | Register `doc_events["Communication"]["after_insert"]` for mention detection fallback |
| Create | `desk/src/composables/useMentionSuggestion.ts` | Tiptap mention suggestion config + API wiring |
| Create | `desk/src/components/ticket/MentionDropdown.vue` | Autocomplete popup component |
| Modify | `desk/src/components/ticket/InternalNote.vue` (Story 1.4) | Ensure `@name` spans render with chip styling in the displayed note |
| Modify | `desk/src/pages/ticket/{InternalNoteComposer}.vue` (Story 1.4) | Wire Tiptap Mention extension into the TextEditor |
| Create/Modify | `desk/src/stores/notifications.ts` | Pinia store for real-time mention notifications (new per ADR-11) |
| Modify | `desk/src/components/{NotificationBell}.vue` | Subscribe to `unreadCount` from notifications store |

### Testing Standards

- Minimum **80% line coverage** on all new backend Python code (NFR-M-01).
- Use `frappe.tests.utils.FrappeTestCase` as base class (consistent with project patterns).
- Test users must be created in `setUp` with appropriate roles and cleaned up in `tearDown` using `frappe.db.rollback()`.
- For socket/realtime assertions, spy on `frappe.publish_realtime` (mock it) and assert it is called with the correct `user` and `event` arguments.
- Test the `get_mentionable_agents` endpoint under a non-Agent caller to confirm `frappe.PermissionError` is raised.
- All backend test fixtures (test ticket, test users) must use unique email addresses / subjects to avoid collision with parallel test runs.

### Constraints

- Do NOT parse plain-text `@name` mentions — only `<span data-mention="email">` HTML attributes. Plain-text `@mentions` in older notes or in customer replies must never trigger notifications.
- Do NOT introduce a new rich-text editor library. The Tiptap `@tiptap/extension-mention` package is an official Tiptap extension compatible with the existing frappe-ui editor setup.
- The autocomplete must only surface agents (HD Agent + System Manager role) — never customers, guest users, or disabled users (AC #2, #11).
- Notification delivery must be both real-time (Socket.IO for online agents) AND persistent (Notification Log for offline agents) — AC #10.
- All user-facing strings in Python must use `frappe._()` and in Vue/TypeScript must use `__()` for i18n compatibility.
- The mention notification job timeout is 30 seconds (short operation); do not set a long timeout.

### Project Structure Notes

- **Prerequisite — Story 1.4:** This story cannot be implemented without Story 1.4 (Internal Notes on Tickets). The `is_internal` field, `add_internal_note` API, and the Tiptap TextEditor in the note composer are all foundations that Story 1.5 extends. Confirm Story 1.4 is `done` in sprint-status.yaml before beginning.
- **`notifications/` Package:** The `helpdesk/helpdesk/notifications/` directory is new in Phase 1. Ensure `__init__.py` is created so Python treats it as a package. Future notification types (SLA warnings, major incident alerts) should be added here as additional modules.
- **`notifications.ts` Pinia Store (ADR-11):** The architecture defines this as a new store for SLA alerts, @mentions, and chat assignments. Story 1.5 creates the initial version. Design it generically so future notification types (from SLA, chat) can be added without refactoring — use a `type` discriminator field on notification objects.
- **`hooks.py` Extension:** The `doc_events` key for `"Communication"` may already exist from Story 1.4 (email guard). Use list append, not replacement:
  ```python
  doc_events = {
      "Communication": {
          "after_insert": [
              "helpdesk.helpdesk.overrides.hd_ticket.on_communication_insert",  # Story 1.4 email guard
              "helpdesk.helpdesk.notifications.mention_handler.on_communication_insert",  # Story 1.5 mention detection
          ]
      }
  }
  ```
- **No New DocTypes:** This story does not introduce any new DocTypes. It uses the existing Frappe built-in `Notification Log` DocType and the `Communication` DocType extended in Story 1.4.

### References

- Story 1.4 (prerequisite — Internal Notes): [Source: _bmad-output/implementation-artifacts/story-1.4-internal-notes-on-tickets.md]
- FR-IN-01 (Private agent notes, @mention support): [Source: _bmad-output/planning-artifacts/epics.md#FR-IN-01]
- NFR-SE-01 (Internal notes NEVER exposed): [Source: _bmad-output/planning-artifacts/epics.md#Non-Functional Requirements]
- NFR-M-01 (80% unit test coverage): [Source: _bmad-output/planning-artifacts/epics.md#Non-Functional Requirements]
- NFR-U-04 (WCAG 2.1 AA compliance for new UI components): [Source: _bmad-output/planning-artifacts/epics.md#Non-Functional Requirements]
- ADR-09 (Frontend component organisation — `desk/src/components/ticket/`): [Source: _bmad-output/planning-artifacts/architecture.md#ADR-09]
- ADR-11 (Pinia stores — `notifications.ts` for @mentions): [Source: _bmad-output/planning-artifacts/architecture.md#ADR-11]
- ADR-12 (Background job queues — `short` for @mention notifications): [Source: _bmad-output/planning-artifacts/architecture.md#ADR-12]
- ADR-12 (Socket.IO room `agent:{agent_email}` for private notifications): [Source: _bmad-output/planning-artifacts/architecture.md#Communication Patterns]
- ADR-08 (API design — `get_mentionable_agents` in `helpdesk/api/ticket.py`): [Source: _bmad-output/planning-artifacts/architecture.md#ADR-08]
- UX-DR-02 (Visual distinction for internal notes — amber styling): [Source: _bmad-output/planning-artifacts/epics.md#UX Design Requirements]
- Epic 1 Story 1.5 AC: [Source: _bmad-output/planning-artifacts/epics.md#Story 1.5]

## Dev Agent Record

### Agent Model Used

Claude Sonnet 4.5 (create-story workflow)

### Debug Log References

_None — story creation phase_

### Completion Notes List

_To be filled by implementing dev agent_

### File List

_To be filled by implementing dev agent upon completion_
