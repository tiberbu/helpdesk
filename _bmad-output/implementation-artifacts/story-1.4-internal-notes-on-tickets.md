# Story 1.4: Internal Notes on Tickets

Status: ready-for-dev

## Story

As a support agent,
I want to add private notes on a ticket that are visible only to other agents,
so that I can collaborate internally without exposing information to customers.

## Acceptance Criteria

1. **[is_internal Field on HD Communication]** Given the HD Ticket communication mechanism (the DocType used to store ticket replies and comments), when the schema is updated, then an `is_internal` boolean field (Check, default 0, label "Internal Note") is present on the communication record. This field persists to the database and is always stored server-side — it cannot be overridden by a non-Agent API caller.

2. **[Add Internal Note via Agent UI — Editor Opens]** Given an agent is viewing a ticket in the agent desk (`/helpdesk/tickets/:id`), when they click the "Add Internal Note" button (or press the keyboard shortcut `Ctrl+Shift+N` / `Cmd+Shift+N` on macOS), then a note composer opens that is visually distinct from the standard reply composer:
   - Background: `bg-amber-50`
   - Left border: `border-l-4 border-amber-400`
   - Header badge: "Internal Note" label with a lock icon (Lucide `Lock` icon)
   - The composer is clearly separated from the customer-reply composer so agents cannot accidentally send an internal note as a customer reply.

3. **[Rich Text Editor in Internal Note Composer]** Given the internal note composer is open, when the agent interacts with it, then the editor supports full rich-text formatting: bold, italic, underline, links, inline code, code blocks, and ordered/unordered lists — using the existing frappe-ui `TextEditor` component (or equivalent Tiptap-based editor already used in ticket replies). File attachment upload (drag-and-drop and click-to-upload, up to 10 MB per file, any MIME type) is also supported via the existing Frappe file attachment mechanism.

4. **[Submitting an Internal Note — Saved with is_internal = True]** Given the agent fills in the internal note composer and clicks "Submit Note" (or presses `Ctrl+Enter` / `Cmd+Enter`), when the note is submitted, then:
   - A communication record is created with `is_internal = 1`
   - The note appears immediately in the ticket's communication thread
   - It is rendered using the `InternalNote.vue` component (amber-50 background, amber-400 left border, lock icon, "Internal Note" badge)
   - Any attached files are linked to the communication record

5. **[InternalNote.vue — Visual Distinction]** Given internal note communications exist on a ticket, when the ticket thread is rendered in the agent desk, then each internal note communication is rendered by the `InternalNote.vue` component with all of the following visual cues:
   - `bg-amber-50` background (distinct from white customer reply background)
   - `border-l-4 border-amber-400` left border accent
   - A "Internal Note" badge (frappe-ui `Badge` component, amber/yellow variant)
   - A Lucide `Lock` icon adjacent to the badge
   - Author name, timestamp, and content rendered the same as a regular reply
   - Attached files shown as downloadable links

6. **[Server-Side Permission Check — Customer Portal API]** Given an internal note (`is_internal = 1`) exists on a ticket, when the ticket detail is fetched via any customer-facing API endpoint (e.g. `/api/method/helpdesk.api.ticket.*` or the portal's resource endpoint for HD Communication), then:
   - The internal note record is completely excluded from the API response
   - No `is_internal = 1` communications appear anywhere in the serialized ticket data returned to a non-Agent session
   - The check is enforced server-side in Python; client-side filtering alone is NOT sufficient (per NFR-SE-01)

7. **[Server-Side Permission Check — REST API Without Agent Role]** Given a user without the "HD Agent" or "System Manager" role makes a GET request to `/api/resource/HD Communication?filters=[["ticket","=","TICKET-001"]]` (or any REST list/document endpoint that could expose communications), when the request is processed, then communications with `is_internal = 1` are filtered out from the results before they are returned. This is implemented via a `has_permission` or `get_list_filters` hook on the communication DocType, or via a server-side `get_list` override — not via any UI-only guard.

8. **[Internal Notes Excluded from Customer Emails]** Given an internal note is created on a ticket, when the Frappe email notification system processes outgoing emails for this ticket (e.g., new-reply notifications to the customer), then the internal note content is NEVER included in any email sent to the customer's email address. This is enforced by checking `is_internal` before queuing any outbound notification email related to a communication record.

9. **[Internal Notes Visible to Agents in Ticket Thread]** Given an agent with the "HD Agent" or "System Manager" role is viewing the ticket, when they load the ticket thread, then all internal notes (`is_internal = 1`) for that ticket ARE visible, interleaved chronologically with other communications. This confirms agents can see their own and each other's notes.

10. **[Keyboard Shortcut — Add Internal Note]** Given an agent has a ticket open in the agent desk, when they press `Ctrl+Shift+N` (Windows/Linux) or `Cmd+Shift+N` (macOS), then the internal note composer opens (same effect as clicking "Add Internal Note" button). The shortcut is registered using the existing keyboard shortcut infrastructure in the desk (the same system used for existing shortcuts T, P, A, S, R, C, Ctrl+K per PRD). The shortcut must not conflict with existing registered shortcuts.

11. **[Internal Notes NOT Visible in Customer Portal]** Given a customer is authenticated in the customer portal (`/helpdesk/my-tickets/:id`) and views their ticket, when the portal loads the ticket thread, then no internal notes are present in the rendered thread — they are absent from the API response (enforced by AC #6) and therefore cannot be displayed, regardless of frontend filtering.

12. **[Migration Patch — add is_internal Field]** Given a pre-existing helpdesk installation with existing communication records, when the Phase 1 migration patch for Story 1.4 runs, then:
   - The `is_internal` column is present on the underlying communications table
   - All existing communication records have `is_internal = 0` (defaulted, non-destructive)
   - No existing data is lost or altered

13. **[Unit Tests — Permission Boundary (NFR-SE-01)]** Given the internal notes implementation, when the test suite runs, then unit tests exist that cover:
   - Creating a communication with `is_internal = 1` and verifying it is saved correctly
   - Fetching ticket communications as an Agent — internal notes ARE returned
   - Fetching ticket communications as a non-Agent (e.g., Guest or Customer role) — internal notes are NOT returned
   - Creating an internal note and verifying no outbound email notification is triggered for the customer
   - The migration patch is idempotent (safe to run twice)
   - Minimum 80% line coverage on all new backend Python code (NFR-M-01)

## Tasks / Subtasks

- [ ] Task 1 — Add `is_internal` field to the ticket communication DocType (AC: #1, #12)
  - [ ] 1.1 Identify the DocType used for ticket communications. In Frappe Helpdesk, communications are stored in the Frappe-built-in `Communication` DocType (or a custom `HD Communication` DocType — verify by inspecting `helpdesk/helpdesk/doctype/` and `hooks.py`). If a custom DocType exists, modify its JSON. If the standard Frappe `Communication` DocType is used, add `is_internal` as a Custom Field via the DocType JSON override pattern (AR-04: prefer DocType JSON modification where the app owns the schema).
  - [ ] 1.2 Add `is_internal` field to the identified DocType JSON:
    ```json
    {
      "fieldname": "is_internal",
      "fieldtype": "Check",
      "label": "Internal Note",
      "default": "0",
      "in_list_view": 0,
      "search_index": 1
    }
    ```
  - [ ] 1.3 Create migration patch `helpdesk/patches/v1_phase1/add_is_internal_to_communication.py`:
    ```python
    def execute():
        """Add is_internal field to communication table (Story 1.4)."""
        import frappe
        table = "tabCommunication"  # or tabHD Communication — confirm
        if not frappe.db.has_column(table.replace("tab", ""), "is_internal"):
            frappe.db.add_column(table.replace("tab", ""), "is_internal", "int(1) default 0")
        frappe.db.commit()
    ```
  - [ ] 1.4 Register the patch in `helpdesk/patches.txt` after Story 1.3 entries:
    ```
    helpdesk.patches.v1_phase1.add_is_internal_to_communication
    ```

- [ ] Task 2 — Implement server-side permission filter for internal notes (AC: #6, #7, #8)
  - [ ] 2.1 Locate (or create) `helpdesk/helpdesk/overrides/hd_ticket.py` — the existing override file referenced in the architecture.
  - [ ] 2.2 Implement a `filter_internal_notes(doc, method=None)` helper or use Frappe's `has_permission` / `get_list_filters` hook to exclude `is_internal = 1` records for non-Agent callers:
    ```python
    def get_communication_list_filters(user=None):
        """Called by Frappe's get_list to append filters.
        Excludes internal notes for non-agent users.
        """
        if not user:
            user = frappe.session.user
        if frappe.has_permission("HD Ticket", "write", user=user):
            # Agent or System Manager — no filter, see all
            return []
        # Customer / guest — exclude internal notes
        return [["is_internal", "=", 0]]
    ```
  - [ ] 2.3 Register the filter hook in `hooks.py` under `has_permission` or `get_list` override for the relevant DocType.
  - [ ] 2.4 Also add an explicit guard in any whitelisted API method that returns ticket communications (search for methods in `helpdesk/api/ticket.py`, `helpdesk/api/agent.py`, etc. that serialize communications). For each such method, append `filters={"is_internal": 0}` when the caller does not have Agent role:
    ```python
    def _get_communications(ticket_id: str) -> list:
        is_agent = frappe.has_permission("HD Ticket", "write")
        filters = {"reference_name": ticket_id}
        if not is_agent:
            filters["is_internal"] = 0
        return frappe.get_all(
            "Communication",
            filters=filters,
            fields=["name", "content", "sender", "creation", "is_internal", ...],
        )
    ```
  - [ ] 2.5 Locate the email notification logic for ticket communications (likely in `hooks.py` `doc_events` for `Communication` `after_insert`, or in a notification template). Add a guard:
    ```python
    def on_communication_insert(doc, method=None):
        if doc.is_internal:
            return  # Never send customer emails for internal notes
        # Existing email dispatch logic continues here
    ```
  - [ ] 2.6 Register the `on_communication_insert` guard in `hooks.py` under `doc_events` for the communication DocType's `after_insert` event (prepend — do not replace existing hooks).

- [ ] Task 3 — Create `InternalNote.vue` component (AC: #5)
  - [ ] 3.1 Create `desk/src/components/ticket/InternalNote.vue`:
    ```vue
    <template>
      <div class="border-l-4 border-amber-400 bg-amber-50 rounded-r p-4 my-2">
        <div class="flex items-center gap-2 mb-2">
          <Lock class="h-4 w-4 text-amber-600" />
          <Badge variant="warning" label="Internal Note" />
          <span class="text-sm text-gray-500">{{ authorName }}</span>
          <span class="text-sm text-gray-400">{{ formattedTime }}</span>
        </div>
        <div class="prose prose-sm" v-html="sanitizedContent" />
        <AttachmentList v-if="attachments.length" :attachments="attachments" />
      </div>
    </template>

    <script setup lang="ts">
    import { computed } from 'vue'
    import { Lock } from 'lucide-vue-next'
    import { Badge } from '@frappe-ui/vue'
    // Props, computed, sanitization
    </script>
    ```
  - [ ] 3.2 Component accepts props:
    - `content: string` — HTML content of the note (rendered with `v-html`, must be server-sanitized before storage per NFR-SE-06)
    - `author: string` — agent full name or email
    - `timestamp: string` — ISO 8601 datetime string
    - `attachments: Array<{name: string, file_url: string, file_name: string}>` — attached files
  - [ ] 3.3 Use Lucide `Lock` icon (already a project dependency per architecture) for the lock icon.
  - [ ] 3.4 Use frappe-ui `Badge` component with amber/warning variant for the "Internal Note" label.
  - [ ] 3.5 Format timestamp using existing `dayjs` utility (consistent with other ticket timestamps).
  - [ ] 3.6 Render `AttachmentList` (reuse or create simple sub-component) for any attached files.
  - [ ] 3.7 Ensure the component is accessible: the lock icon has `aria-label="Internal note — not visible to customer"`, the amber background achieves WCAG 2.1 AA contrast ratio for text.

- [ ] Task 4 — Integrate `InternalNote.vue` into the ticket thread (AC: #5, #9, #11)
  - [ ] 4.1 Locate the ticket thread/communication list component (likely `desk/src/pages/ticket/` or `desk/src/components/ticket/` — look for the component rendering the ticket's reply/comment history).
  - [ ] 4.2 Update the thread rendering logic to check each communication record's `is_internal` flag:
    ```vue
    <template v-for="comm in communications" :key="comm.name">
      <InternalNote v-if="comm.is_internal" v-bind="mapCommToNote(comm)" />
      <TicketReply v-else v-bind="mapCommToReply(comm)" />
    </template>
    ```
  - [ ] 4.3 Ensure the `createListResource` or `createResource` call fetching communications includes `is_internal` in the `fields` list.
  - [ ] 4.4 Since the server already filters internal notes for non-Agent callers (AC #6, #7), the frontend simply renders whatever is returned — no additional client-side permission filtering needed (defense in depth only).

- [ ] Task 5 — Create the "Add Internal Note" composer UI (AC: #2, #3, #4)
  - [ ] 5.1 Locate the ticket reply composer component (the area where agents type replies). Add an "Add Internal Note" toggle button or tab alongside the existing reply actions.
  - [ ] 5.2 The note composer UI must be visually distinct from the reply composer: apply `bg-amber-50`, `border-l-4 border-amber-400` to the composer container, display the `Lock` icon and "Internal Note" badge in the composer header.
  - [ ] 5.3 Reuse the existing `TextEditor` (frappe-ui Tiptap-based rich text editor) for the note body — the same editor used for ticket replies. Do not create a new editor implementation.
  - [ ] 5.4 Add file attachment support: reuse the existing file upload component/mechanism already present in the reply composer.
  - [ ] 5.5 The submit button is labeled "Submit Note" (distinct from the reply composer's "Send Reply" label).
  - [ ] 5.6 On submit, call the API to create the communication with `is_internal: 1`:
    ```typescript
    await createResource({
      url: 'helpdesk.api.ticket.add_internal_note',  // or equivalent
      params: {
        ticket_id: props.ticketId,
        content: noteContent.value,
        attachments: attachedFiles.value,
      },
    }).submit()
    ```
  - [ ] 5.7 After successful submission, clear the composer and trigger a refresh of the ticket thread.

- [ ] Task 6 — Expose a whitelisted API method for adding internal notes (AC: #4, #6)
  - [ ] 6.1 In `helpdesk/api/ticket.py` (or the appropriate API module), add a whitelisted method:
    ```python
    @frappe.whitelist()
    def add_internal_note(ticket_id: str, content: str, attachments: list = None):
        """Create an internal note on a ticket. Agent role required."""
        frappe.has_permission("HD Ticket", "write", throw=True)
        comm = frappe.get_doc({
            "doctype": "Communication",   # or HD Communication
            "communication_type": "Comment",
            "reference_doctype": "HD Ticket",
            "reference_name": ticket_id,
            "content": frappe.utils.sanitize_html(content),
            "is_internal": 1,
            "sent_or_received": "Sent",
            "sender": frappe.session.user,
        })
        comm.insert(ignore_permissions=False)
        if attachments:
            _attach_files_to_communication(comm.name, attachments)
        return {"name": comm.name, "creation": str(comm.creation)}
    ```
  - [ ] 6.2 Apply `frappe.utils.sanitize_html(content)` before storing the note content — prevents XSS (NFR-SE-06).
  - [ ] 6.3 The `frappe.has_permission("HD Ticket", "write", throw=True)` call ensures only Agents (who have write access on HD Ticket) can create internal notes.

- [ ] Task 7 — Register keyboard shortcut for "Add Internal Note" (AC: #10)
  - [ ] 7.1 Locate the keyboard shortcut registration in the desk frontend (look for existing shortcut definitions — likely in a composable or router guard, e.g., `useKeyboardShortcuts.ts` or similar, matching the existing T, P, A, S, R, C shortcuts).
  - [ ] 7.2 Register `Ctrl+Shift+N` / `Cmd+Shift+N` to trigger opening the internal note composer:
    ```typescript
    useKeyboardShortcut('ctrl+shift+n', () => openInternalNoteComposer(), {
      description: 'Add internal note',
    })
    ```
  - [ ] 7.3 Verify the shortcut does not conflict with any existing registered shortcut (check all existing registrations in the shortcut registry before registering).
  - [ ] 7.4 The shortcut should only be active when a ticket detail page is in focus (scope it to the ticket view context, not globally).

- [ ] Task 8 — Write unit tests for permission boundary (AC: #13, NFR-SE-01)
  - [ ] 8.1 Create or extend `helpdesk/helpdesk/doctype/hd_ticket/test_hd_ticket.py` (or the communication DocType test file) with the following tests:
    - `test_internal_note_is_stored_with_is_internal_true` — create a communication with `is_internal=1`; assert `frappe.db.get_value` returns `is_internal=1`
    - `test_agent_can_read_internal_notes` — as a user with HD Agent role, fetch communications for a ticket; assert the internal note IS in the result set
    - `test_non_agent_cannot_read_internal_notes` — as a user without HD Agent role (e.g., a portal customer), fetch communications for a ticket via the API or list endpoint; assert internal notes are NOT in the result
    - `test_internal_note_does_not_trigger_customer_email` — create an internal note; assert no outbound email notification is queued for the customer (mock or spy on the email dispatch function)
    - `test_migration_patch_is_idempotent` — run the patch twice; assert no error and column exists after both runs
    - `test_add_internal_note_api_requires_agent_role` — call `add_internal_note` as a non-Agent; assert `frappe.PermissionError` is raised
  - [ ] 8.2 Use `frappe.tests.utils.FrappeTestCase` as the base class.
  - [ ] 8.3 All tests must be self-contained: create test fixtures (test ticket, test user with/without HD Agent role) in `setUp` and clean up in `tearDown` / `addCleanup`.
  - [ ] 8.4 Run tests with:
    ```bash
    bench --site <site> run-tests --module helpdesk.helpdesk.doctype.hd_ticket.test_hd_ticket
    ```

## Dev Notes

### Architecture Patterns

- **Communication Type Extension (ADR-01):** Internal notes are implemented as a new `communication_type` or via an `is_internal` boolean flag on the existing ticket communication mechanism — NOT as a separate DocType. The architecture document states: "New communication type on HD Ticket; permission-gated visibility." This keeps all ticket communications in a unified timeline while allowing a single permission-based filter to exclude internal records. [Source: architecture.md — Requirements Overview, FR-IN-01]

- **ChannelMessage is_internal Flag (ADR-07):** The Channel Abstraction Layer's `ChannelMessage` dataclass includes `is_internal: bool`. When the channel normalizer processes an internal note submission, it sets `is_internal = True` before creating the communication record. This design means ALL communication creation — whether from email, chat, or the agent UI — passes through the normalizer and respects the same `is_internal` flag. [Source: architecture.md#ADR-07]

- **InternalNote.vue Component (ADR-09):** The architecture explicitly defines this component:
  ```
  desk/src/components/ticket/
  └── InternalNote.vue    # Visually distinct internal note
  ```
  Styling MUST use amber-50 background and amber-400 left border per UX-DR-02. Use Lucide `Lock` icon (already in the dependency tree per architecture). Follow the existing frappe-ui component composition pattern (`<script setup lang="ts">`, Composition API). [Source: architecture.md#ADR-09, epics.md#UX-DR-02]

- **Permission Model (ADR-04):** The architecture's permission mapping for internal notes:
  | Feature | Read | Write | Condition |
  |---------|------|-------|-----------|
  | Internal Notes | Agent role | Agent role | `note.is_internal` check on ALL customer-facing APIs |

  The server-side check must be applied in EVERY API path that returns communications. Audit ALL `frappe.whitelist()` methods in `helpdesk/api/` that could return communication data. [Source: architecture.md#ADR-04]

- **NFR-SE-01 — Hard Security Boundary:** The requirement is absolute — internal notes must NEVER be exposed via customer portal, API, or email. Implement the filter at multiple layers (defense in depth):
  1. DocType `get_list` filter hook — excludes from all REST list responses
  2. Explicit filter in all whitelisted API methods that return communications
  3. Email notification guard — skips email dispatch when `is_internal = 1`
  Unit tests MUST prove the boundary holds (AC #13). [Source: epics.md#NFR-SE-01]

- **Keyboard Shortcuts (Existing Infrastructure):** The PRD confirms the codebase already has a keyboard shortcut system (T, P, A, S, R, C, Ctrl+K). The new shortcut `Ctrl+Shift+N` must be registered through the same mechanism — do not introduce a parallel event listener. Check `desk/src/composables/` or `desk/src/pages/ticket/` for the shortcut registration pattern. [Source: prd.md — What Already Exists]

- **Rich Text Editor:** The desk already uses a Tiptap-based `TextEditor` component from frappe-ui for ticket replies. Reuse this component for the internal note composer — same props/config. Do NOT introduce a second rich text editor library. [Source: architecture.md — Vue 3 + frappe-ui, existing codebase]

- **HTML Sanitization (NFR-SE-06):** All note content must be sanitized server-side before storage using `frappe.utils.sanitize_html()` (which uses Python `bleach`). Client-side sanitization alone is insufficient. This is critical since notes can contain arbitrary HTML from the rich text editor. [Source: architecture.md#NFR-SE-06]

- **@Mention Support:** Story 1.4 requires the note composer to support `@mention` syntax (per FR-IN-01: "@mention support: typing '@' shows agent list"). However, the notification dispatch logic for @mentions is scoped to **Story 1.5** (which builds on this foundation). For Story 1.4: implement the `@` trigger in the editor UI to show an agent dropdown (autocomplete overlay), but the actual in-app notification sending is deferred to Story 1.5. The `@mention` parsing in the composer can be a stub that stores the mention markup in the note content without dispatching notifications.

- **Identifying the Communication DocType:** Frappe Helpdesk may use the built-in Frappe `Communication` DocType or a custom `HD Communication` DocType. Before implementing Task 1, inspect:
  - `helpdesk/helpdesk/doctype/` for any `hd_communication` directory
  - `hooks.py` for any `Communication` doc_events overrides
  - Existing ticket reply/comment code to see which DocType it inserts into
  This determines whether to modify `Communication.json` (core Frappe — use a custom field approach) or `HD Communication.json` (app-owned — modify directly per AR-04).

### Files to Create / Modify

| Action | Path | Notes |
|--------|------|-------|
| Modify | `helpdesk/helpdesk/doctype/{communication_doctype}/{name}.json` | Add `is_internal` Check field |
| Create | `helpdesk/patches/v1_phase1/add_is_internal_to_communication.py` | Migration patch |
| Modify | `helpdesk/patches.txt` | Register new patch after Story 1.3 entries |
| Modify | `helpdesk/helpdesk/overrides/hd_ticket.py` | Add communication list filter helper |
| Modify | `helpdesk/hooks.py` | Register `get_list` filter and email notification guard for communications |
| Modify | `helpdesk/api/ticket.py` | Add `add_internal_note` whitelisted method; filter `is_internal` in existing communication fetch methods |
| Create | `desk/src/components/ticket/InternalNote.vue` | Amber-styled internal note display component |
| Modify | `desk/src/pages/ticket/{TicketDetail}.vue` (or equivalent) | Render `InternalNote.vue` for `is_internal` communications in thread |
| Modify | `desk/src/pages/ticket/{TicketReplyComposer}.vue` (or equivalent) | Add "Add Internal Note" button/tab, amber-styled composer, `Ctrl+Shift+N` shortcut |
| Modify | `desk/src/composables/useKeyboardShortcuts.ts` (or equivalent) | Register `Ctrl+Shift+N` shortcut for internal note composer |
| Create/Modify | `helpdesk/helpdesk/doctype/hd_ticket/test_hd_ticket.py` | Unit tests for permission boundary |

### Testing Standards

- Minimum **80% line coverage** on all new backend Python code (NFR-M-01).
- Use `frappe.tests.utils.FrappeTestCase` as base class.
- Security tests (AC #13) are NON-NEGOTIABLE — the permission boundary must be proven by automated tests, not just manual verification.
- To simulate a non-Agent user in tests, use `frappe.set_user("test_customer@example.com")` (with a test user that has only Guest/Customer role) and restore with `frappe.set_user("Administrator")` in cleanup.
- Mock or inspect email queuing (check `frappe.sendmail` calls or `frappe.db.get_all("Email Queue")` after note creation) to verify no email is queued for internal notes.
- Patch tests must use `frappe.db.has_column()` assertions before and after to confirm idempotency.

### Constraints

- Do NOT use Custom Fields if the app owns the communication DocType (AR-04). If using Frappe's built-in `Communication`, follow the Custom Field approach via `fixtures/` or a migration patch rather than modifying core Frappe files.
- `is_internal` must be enforced server-side — client-side filtering is a display convenience only, not a security control (NFR-SE-01).
- The internal note editor must reuse the existing `TextEditor` from frappe-ui — do not introduce a new rich text library.
- All user-facing strings ("Internal Note", "Submit Note", validation messages) must use `frappe._()` in Python and `__()` in JavaScript/Vue for i18n.
- The `Ctrl+Shift+N` shortcut must be scoped to the ticket detail view — not registered globally — to avoid conflicts on other pages.
- Do NOT implement @mention notification dispatch in this story — that is Story 1.5. The UI can render `@name` markup in the autocomplete but must not fire notifications.

### Project Structure Notes

- **Standalone Story:** Story 1.4 has no hard dependencies on Stories 1.1, 1.2, or 1.3 (per epics.md dependency table: "FR-IN-01: Dependencies: None"). However, the `doc_events["HD Ticket"]["validate"]` hook list may already exist from Stories 1.1–1.3 — extend the list rather than replacing it.
- **Story 1.5 Dependency:** Story 1.5 (@Mention Notifications) depends on Story 1.4 being complete. The `is_internal` flag and the `InternalNote.vue` component are prerequisites for mention notifications.
- **Channel Normalizer Integration:** The `helpdesk/helpdesk/channels/normalizer.py` (new in Phase 1, per ADR-07) must handle `is_internal = True` on `ChannelMessage` objects when creating communications from the agent note UI path. Coordinate with the channel abstraction work if it has already started.
- **Email Guard Placement:** The email notification guard (Task 2, step 2.5) must run BEFORE any existing email dispatch logic for communications. Use `before_insert` hook if possible, or prepend to the `after_insert` hook list to ensure early return.

### References

- Story 1.4 acceptance criteria: [Source: _bmad-output/planning-artifacts/epics.md#Story 1.4]
- FR-IN-01 (Private Agent Notes — full requirement): [Source: _bmad-output/planning-artifacts/epics.md#FR-IN-01, prd.md#FR-IN-01]
- NFR-SE-01 (Internal notes NEVER exposed): [Source: _bmad-output/planning-artifacts/epics.md#Non-Functional Requirements]
- UX-DR-02 (amber-50 bg, amber-400 border, badge, lock icon): [Source: _bmad-output/planning-artifacts/epics.md#UX Design Requirements]
- NFR-U-05 (Keyboard navigation for all new features): [Source: _bmad-output/planning-artifacts/epics.md#Non-Functional Requirements]
- NFR-U-04 (WCAG 2.1 AA compliance): [Source: _bmad-output/planning-artifacts/epics.md#Non-Functional Requirements]
- NFR-SE-06 (Server-side HTML sanitization): [Source: _bmad-output/planning-artifacts/epics.md#Non-Functional Requirements]
- NFR-M-01 (80% unit test coverage): [Source: _bmad-output/planning-artifacts/epics.md#Non-Functional Requirements]
- AR-04 (Modify DocType JSON, not Custom Fields when app owns DocType): [Source: _bmad-output/planning-artifacts/epics.md#Additional Requirements]
- AR-05 (Migration patches in `helpdesk/patches/v1_phase1/`): [Source: _bmad-output/planning-artifacts/epics.md#Additional Requirements]
- ADR-01 (Extend HD Ticket rather than separate DocTypes): [Source: _bmad-output/planning-artifacts/architecture.md#ADR-01]
- ADR-04 (Permission model extensions — internal notes): [Source: _bmad-output/planning-artifacts/architecture.md#ADR-04]
- ADR-07 (Channel abstraction — ChannelMessage.is_internal): [Source: _bmad-output/planning-artifacts/architecture.md#ADR-07]
- ADR-09 (Frontend component — InternalNote.vue): [Source: _bmad-output/planning-artifacts/architecture.md#ADR-09]
- Existing keyboard shortcuts (T, P, A, S, R, C, Ctrl+K): [Source: _bmad-output/planning-artifacts/prd.md#What Already Exists]
- Story 1.5 (dependent — @Mention Notifications): [Source: _bmad-output/implementation-artifacts/story-1.5 when created]

## Dev Agent Record

### Agent Model Used

Claude Sonnet 4.5 (create-story workflow)

### Debug Log References

_None — story creation phase_

### Completion Notes List

_To be filled by implementing dev agent_

### File List

_To be filled by implementing dev agent upon completion_
