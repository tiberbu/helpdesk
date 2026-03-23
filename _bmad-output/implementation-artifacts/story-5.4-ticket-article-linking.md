# Story 5.4: Ticket-Article Linking

Status: ready-for-dev

## Story

As a support agent,
I want to link KB articles to tickets and create articles from tickets,
so that resolution knowledge is connected to the incidents it addresses.

## Acceptance Criteria

1. **[HD Ticket Article Child DocType — Schema]** Given the `HD Ticket Article` child DocType exists, when a developer inspects its schema, then it has the following fields:
   - `article` (Link → HD Article, reqd: 1, in_list_view: 1, label: "Article")
   - `article_title` (Data, read_only: 1, fetch_from: `article.title`, label: "Article Title")
   - `linked_on` (Datetime, default: `now`, label: "Linked On")
   - `linked_by` (Link → User, default: `__user`, label: "Linked By")
   The parent DocType is `HD Ticket` and it follows the standard `HD ` prefix naming convention (AR-02).

2. **[HD Ticket — linked_articles Child Table Field]** Given the `hd_ticket.json` DocType is inspected, when a developer reviews the fields, then a `Table` field named `linked_articles` (label: "Linked Articles", options: "HD Ticket Article") exists on HD Ticket. This field is added directly to the DocType JSON (not via Custom Fields, per AR-04).

3. **[Link Article Action — Sidebar Search Dialog]** Given an agent is viewing a ticket in the agent workspace, when they click the "Link Article" button in the KB section of the ticket sidebar, then `ArticleLinkDialog.vue` opens as a modal dialog with:
   - A search input field (auto-focused) that queries published HD Articles by title and content
   - A results list showing matching article titles with category labels
   - A "Link" button on each result row to confirm the selection
   - Only `Published` articles are returned by the search (non-published articles are excluded)
   - The dialog closes after a successful link and the sidebar refreshes to show the newly linked article

4. **[Link Article — Duplicate Prevention]** Given an agent attempts to link an article that is already linked to the ticket, when the link request is submitted to the API, then the server returns a validation error `"Article '{title}' is already linked to this ticket."` and no duplicate child row is created. The frontend shows this message as a toast/error notification.

5. **[Linked Articles Display — Ticket Sidebar]** Given a ticket has one or more linked articles, when an agent views the ticket sidebar, then the "Linked Articles" panel shows:
   - Each linked article's title as a clickable link navigating to the article detail in the agent KB (`/helpdesk/knowledge-base/{article_name}`)
   - A "Remove" icon (x) next to each article that, when clicked, removes the link (with a confirmation prompt: "Remove link to '[article title]'?")
   - An article count badge on the panel header (e.g., "Linked Articles (2)")
   - If no articles are linked, the panel shows an empty state: "No articles linked. Click 'Link Article' to connect relevant KB content."

6. **[Create Article from Ticket — Action]** Given an agent is viewing a ticket in the agent workspace, when they click "Create Article from Ticket" (available in the ticket action menu or sidebar KB section), then the agent is navigated to the New Article form (`/helpdesk/knowledge-base/new-article`) with the following fields pre-filled:
   - `title` pre-filled with the ticket's `subject`
   - `content` pre-filled with a structured template:
     ```
     ## Problem
     {ticket subject}

     ## Resolution
     {last agent reply content, if available; otherwise empty}
     ```
   - `category` pre-filled with the ticket's `category` (if set on the ticket)
   - After the new article is saved, the system automatically creates a link between the new article and the originating ticket (the ticket name is passed as a URL parameter or session state so the link is created on article save)

7. **[Create Article from Ticket — Auto-Link on Save]** Given an agent created a new article from a ticket via the "Create Article from Ticket" action, when they save the new article (in Draft state), then a `HD Ticket Article` child row is automatically added to the originating ticket's `linked_articles` table linking it to the new article. The agent is shown a toast: "Article created and linked to ticket [ticket ID]."

8. **[Article Detail — Linked Tickets Display]** Given an article has been linked to one or more tickets, when an agent views the article detail page in the agent workspace, then a "Linked Tickets" section is displayed showing:
   - Total count of tickets linked to this article (e.g., "Linked Tickets (5)")
   - A list of the most recent 10 linked tickets, each showing: ticket ID (as a clickable link to the ticket detail), subject, status badge, and the date linked
   - If more than 10 tickets are linked, a "View all [n] tickets" link navigates to the ticket list pre-filtered to `linked_articles.article = {article_name}`
   - This data is fetched via a new whitelisted API endpoint `helpdesk.api.knowledge_base.get_linked_tickets(article)`

9. **[Link Article API — Permission Check]** Given a user without the Agent role (e.g., a guest or customer) attempts to call `helpdesk.api.knowledge_base.link_article_to_ticket` or `helpdesk.api.knowledge_base.remove_article_link`, when the API is invoked, then `frappe.PermissionError` is raised (enforced via `frappe.has_permission("HD Ticket", "write", throw=True)` check inside the method).

10. **[Remove Article Link — API]** Given an agent clicks the remove icon next to a linked article in the ticket sidebar, when they confirm the removal, then the `helpdesk.api.knowledge_base.remove_article_link(ticket, article)` API is called, the corresponding `HD Ticket Article` child row is deleted from the ticket, and the sidebar refreshes. The API enforces the same Agent-role permission check (AC #9).

11. **[Unit Tests — Bidirectional Linking]** Given the implementation is complete, when the test suite runs, then unit tests in `test_hd_article.py` and/or a new `test_ticket_article_linking.py` pass covering:
    - (a) Linking an article to a ticket creates an `HD Ticket Article` child row on the ticket
    - (b) Linking the same article twice to the same ticket raises a `frappe.ValidationError`
    - (c) `get_linked_tickets(article)` returns tickets with the article in their `linked_articles` table, limited to 10, sorted by `linked_on` DESC
    - (d) `get_linked_tickets` returns count of all linked tickets (not just the 10 shown)
    - (e) Removing a link deletes the child row from `linked_articles`
    - (f) Only `Published` articles appear in the `ArticleLinkDialog` search results (non-agents cannot access Draft/In Review articles)
    - (g) Guest user calling `link_article_to_ticket` API raises `frappe.PermissionError`
    Minimum 80% coverage on all new controller methods (NFR-M-01).

12. **[Migration Patch — HD Ticket linked_articles Field]** Given a pre-existing Frappe Helpdesk installation with HD Ticket records, when the Phase 1 migration patch `add_linked_articles_to_hd_ticket.py` runs, then the `linked_articles` Table field and the `HD Ticket Article` child DocType are available without altering any existing ticket records. No back-fill is performed (existing tickets start with an empty `linked_articles` table).

## Tasks / Subtasks

- [ ] Task 1 — Create `HD Ticket Article` child DocType (AC: #1, #12)
  - [ ] 1.1 Create directory `helpdesk/helpdesk/doctype/hd_ticket_article/`
  - [ ] 1.2 Create `__init__.py` (empty)
  - [ ] 1.3 Create `hd_ticket_article.json` with fields: `article` (Link → HD Article, reqd: 1, in_list_view: 1), `article_title` (Data, fetch_from: `article.title`, read_only: 1), `linked_on` (Datetime, default: `now`), `linked_by` (Link → User, default: `__user`); set `istable: 1`, `parent_doctype: "HD Ticket"`
  - [ ] 1.4 Create `hd_ticket_article.py` with empty controller class `HdTicketArticle(Document): pass`
  - [ ] 1.5 Create migration patch `helpdesk/patches/v1_phase1/add_linked_articles_to_hd_ticket.py` with `execute()` that is a no-op (DocType auto-creates via `bench migrate`; patch exists for ordering in `patches.txt`)
  - [ ] 1.6 Register the patch in `helpdesk/patches.txt`

- [ ] Task 2 — Add `linked_articles` Table field to HD Ticket DocType (AC: #2, #12)
  - [ ] 2.1 Open `helpdesk/helpdesk/doctype/hd_ticket/hd_ticket.json`
  - [ ] 2.2 Add a `Section Break` field (label: "Knowledge Base", collapsible: 1, collapsible_depends_on: `eval:doc.linked_articles && doc.linked_articles.length`) before the new table field
  - [ ] 2.3 Add `Table` field `linked_articles` (label: "Linked Articles", options: "HD Ticket Article") directly in the DocType JSON (not via Custom Fields per AR-04)
  - [ ] 2.4 Verify via `bench migrate` that the new child table is created without errors and existing ticket records are unaffected

- [ ] Task 3 — Implement backend API for linking, searching, and removing (AC: #3, #4, #9, #10)
  - [ ] 3.1 Open (or create) `helpdesk/api/knowledge_base.py`
  - [ ] 3.2 Add `@frappe.whitelist()` method `search_articles(query: str) -> list` — queries HD Article where `status = "Published"` and title contains `query` (case-insensitive); returns list of `{name, title, category}` dicts; limited to 20 results
  - [ ] 3.3 Add `@frappe.whitelist()` method `link_article_to_ticket(ticket: str, article: str) -> dict` — validates agent role with `frappe.has_permission("HD Ticket", "write", throw=True)`, checks for existing link (raises `frappe.ValidationError` on duplicate), appends child row to `ticket.linked_articles`, calls `ticket.save()`, returns `{article, article_title}`
  - [ ] 3.4 Add `@frappe.whitelist()` method `remove_article_link(ticket: str, article: str) -> None` — validates agent role, finds and deletes the matching `HD Ticket Article` child row from the ticket, calls `ticket.save()`
  - [ ] 3.5 Add `@frappe.whitelist()` method `get_linked_tickets(article: str) -> dict` — queries `HD Ticket Article` child table for rows where `article = article`, joins with `HD Ticket` for `name, subject, status`, returns `{count: int, tickets: list[{name, subject, status, linked_on}]}` limited to most recent 10, sorted by `linked_on DESC`
  - [ ] 3.6 Add `@frappe.whitelist()` method `prefill_article_from_ticket(ticket: str) -> dict` — validates agent role, fetches the ticket's `subject`, `category`, and last agent reply (`content` of the most recent `HD Ticket Communication` where `sent_or_received = "Sent"` and `communication_type = "Communication"`); returns `{title: ticket.subject, content: "<h2>Problem</h2>...", category: ticket.category}`
  - [ ] 3.7 Ensure all user-facing error messages use `frappe._()` for i18n (Architecture Enforcement Guideline #7)

- [ ] Task 4 — Create `ArticleLinkDialog.vue` search and select component (AC: #3, #4)
  - [ ] 4.1 Create `desk/src/components/kb/ArticleLinkDialog.vue`
  - [ ] 4.2 Implement as a `frappe-ui` Dialog component with a search input (auto-focus via `onMounted`)
  - [ ] 4.3 Wire up `createResource` to call `helpdesk.api.knowledge_base.search_articles` with a debounced (300ms) query on input change
  - [ ] 4.4 Render search results as a list — each row shows article title + category badge + "Link" button
  - [ ] 4.5 Show loading skeleton while search is in progress (frappe-ui `LoadingText` or skeleton rows)
  - [ ] 4.6 Emit `linked(article)` event when user clicks "Link" on a result row; parent component calls the link API and handles the response
  - [ ] 4.7 Show an error toast if the API returns a duplicate validation error (AC #4)
  - [ ] 4.8 Show empty state "No published articles found for '[query]'" when results list is empty
  - [ ] 4.9 Follow `frappe-ui` Dialog conventions and WCAG 2.1 AA accessibility (NFR-U-04): keyboard navigation through results (arrow keys), Enter to select, Escape to close

- [ ] Task 5 — Add Linked Articles panel to ticket sidebar (AC: #5)
  - [ ] 5.1 Identify the ticket sidebar component: `desk/src/pages/ticket/TicketSidebarContent.vue` or equivalent (check `desk/src/pages/ticket/` for sidebar composition)
  - [ ] 5.2 Create `desk/src/components/ticket/LinkedArticles.vue` panel component with:
    - Props: `ticketId` (String)
    - A "Linked Articles (n)" header with count badge, using `frappe-ui` `Badge`
    - "Link Article" button that opens `ArticleLinkDialog.vue`
    - List of linked articles, each with title as a `<router-link>` to `/helpdesk/knowledge-base/{article_name}` and a remove icon (Lucide `X`)
    - Confirmation dialog before removal: "Remove link to '[article title]'?" using `frappe-ui` Dialog
    - Empty state when no articles linked
  - [ ] 5.3 Integrate `LinkedArticles.vue` into the ticket sidebar — import and place it within the KB section of the sidebar
  - [ ] 5.4 Wire `link_article_to_ticket` API call (called when `ArticleLinkDialog` emits `linked` event); refresh linked articles list on success
  - [ ] 5.5 Wire `remove_article_link` API call on remove confirm; refresh list on success
  - [ ] 5.6 Use `createResource` / `createListResource` for data fetching; respect the existing SWR-like caching pattern
  - [ ] 5.7 Follow frappe-ui patterns and WCAG 2.1 AA (NFR-U-04): all buttons have aria-labels, remove button has descriptive aria-label `"Remove link to [article title]"`

- [ ] Task 6 — Implement "Create Article from Ticket" action (AC: #6, #7)
  - [ ] 6.1 Add "Create Article from Ticket" button to the ticket sidebar KB section (inside `LinkedArticles.vue` or as a separate action button near it)
  - [ ] 6.2 On click, call `prefill_article_from_ticket(ticket)` API to fetch pre-fill data
  - [ ] 6.3 Navigate to `/helpdesk/knowledge-base/new-article` via Vue Router with the pre-fill data passed as route state (`router.push({ path: '/helpdesk/knowledge-base/new-article', state: { prefill: {...}, sourceTicket: ticketId } })`) or as query params if state is not supported
  - [ ] 6.4 In the New Article form component (`desk/src/pages/knowledge-base/Article.vue` or new article page), check for `prefill` route state on `onMounted` and populate `title`, `content`, and `category` fields if present
  - [ ] 6.5 After article save succeeds and route state includes `sourceTicket`, automatically call `link_article_to_ticket(sourceTicket, newArticle.name)` to create the bidirectional link
  - [ ] 6.6 Show success toast after auto-link: `"Article created and linked to ticket [sourceTicket]."` (AC #7)
  - [ ] 6.7 Handle edge cases: if the ticket has no last agent reply, the `content` template pre-fills with only the "## Problem" section; if `category` is not set on the ticket, the category field is left blank

- [ ] Task 7 — Add Linked Tickets section to article detail view (AC: #8)
  - [ ] 7.1 Identify the article detail component: `desk/src/pages/knowledge-base/Article.vue` or equivalent
  - [ ] 7.2 Create `desk/src/components/kb/LinkedTickets.vue` component with:
    - Props: `articleName` (String)
    - Uses `createResource` to call `helpdesk.api.knowledge_base.get_linked_tickets(article)`
    - Shows "Linked Tickets (n)" header with total count
    - Renders a list of up to 10 tickets, each row showing: ticket ID as `<router-link>` to `/helpdesk/tickets/{ticket_name}`, subject, and status badge using the existing ticket status badge pattern
    - "View all [n] tickets" link (shown only when count > 10) pointing to ticket list filtered by `linked_articles.article = articleName`
    - Empty state: "No tickets have linked this article yet."
    - Performance: API query must use indexed `article` field on `HD Ticket Article` and limit to 10 results (NFR-P-07 < 1s)
  - [ ] 7.3 Import and integrate `LinkedTickets.vue` into the article detail view, placed below the article content section
  - [ ] 7.4 Component is only visible to agents (not rendered in customer-facing portal)

- [ ] Task 8 — Write unit tests for bidirectional linking (AC: #11)
  - [ ] 8.1 Create (or open) `helpdesk/helpdesk/doctype/hd_article/test_ticket_article_linking.py` (or add to `test_hd_article.py`)
  - [ ] 8.2 Write `test_link_article_to_ticket_creates_child_row` — create test ticket and article, call `link_article_to_ticket`, assert child row exists in ticket's `linked_articles`
  - [ ] 8.3 Write `test_duplicate_link_raises_validation_error` — link the same article twice, assert second call raises `frappe.ValidationError`
  - [ ] 8.4 Write `test_get_linked_tickets_returns_count_and_recent_10` — create an article, link it to 12 test tickets, call `get_linked_tickets`, assert `count == 12` and `len(tickets) == 10` and results sorted by `linked_on DESC`
  - [ ] 8.5 Write `test_remove_article_link_deletes_child_row` — link an article, remove it, assert child row is gone from `linked_articles`
  - [ ] 8.6 Write `test_search_articles_returns_only_published` — create Draft, In Review, Published, Archived articles, call `search_articles`, assert only Published article in results
  - [ ] 8.7 Write `test_link_article_requires_agent_role` — impersonate a guest user, call `link_article_to_ticket`, assert `frappe.PermissionError`
  - [ ] 8.8 Write `test_prefill_article_from_ticket_returns_subject_and_content` — create a ticket with a subject and a sent agent reply, call `prefill_article_from_ticket`, assert returned `title == ticket.subject` and `content` contains the reply content
  - [ ] 8.9 Run tests: `bench --site <site> run-tests --module helpdesk.helpdesk.doctype.hd_article.test_ticket_article_linking`

## Dev Notes

### Architecture Patterns

- **Child Table on HD Ticket (not separate mapping table):** The link is stored as `HD Ticket Article` child table rows on the HD Ticket DocType. This is consistent with the `HD Related Ticket` child table pattern used for ticket-to-ticket linking (ADR-02, `HD Related Ticket`). The article detail view queries the reverse relationship via `frappe.db.get_all("HD Ticket Article", filters={"article": article_name}, ...)` — no separate bidirectional table needed, as Frappe child tables are queryable by their Link fields.

- **`frappe.db.get_all` for Reverse Lookup:** The `get_linked_tickets` API uses:
  ```python
  rows = frappe.db.get_all(
      "HD Ticket Article",
      filters={"article": article},
      fields=["parent as ticket_name", "linked_on"],
      order_by="linked_on desc",
      limit=10
  )
  count = frappe.db.count("HD Ticket Article", filters={"article": article})
  ```
  Then enriches each row with ticket `subject` and `status` via a follow-up `frappe.db.get_value` call or a JOIN query using `frappe.qb`. Never use raw SQL (Architecture Enforcement Guideline #6).

- **Duplicate Prevention Logic:**
  ```python
  existing = frappe.db.exists(
      "HD Ticket Article",
      {"parent": ticket, "parentfield": "linked_articles", "article": article}
  )
  if existing:
      frappe.throw(frappe._("Article '{0}' is already linked to this ticket.").format(article_title))
  ```

- **`prefill_article_from_ticket` — Fetching Last Agent Reply:**
  ```python
  last_reply = frappe.db.get_all(
      "HD Ticket Communication",  # or "Communication" — check existing DocType name
      filters={
          "reference_doctype": "HD Ticket",
          "reference_name": ticket,
          "sent_or_received": "Sent",
          "communication_type": "Communication"
      },
      fields=["content"],
      order_by="creation desc",
      limit=1
  )
  ```
  If no reply found, `content` template uses only the "## Problem" section.

- **ArticleLinkDialog.vue — createResource Pattern:**
  ```vue
  const searchResult = createResource({
    url: "helpdesk.api.knowledge_base.search_articles",
    params: { query: searchQuery.value },
    auto: false,
  })
  // Debounced watcher triggers searchResult.fetch()
  ```

- **"Create Article from Ticket" — Route State vs Query Params:** Vue Router's `state` option (passed via `router.push({ ..., state: {...} })`) is available in `history.state` on the destination page, but is lost on browser refresh. For the pre-fill use case this is acceptable — the agent creates the article immediately. If state is not accessible in the target component, use `sessionStorage` as a fallback to pass the pre-fill data before navigating.

- **Auto-Link After Article Save:** In the new article form component, detect the source ticket via route state in an `onMounted` hook:
  ```javascript
  const sourceTicket = history.state?.sourceTicket
  // After save succeeds:
  if (sourceTicket && savedArticle.name) {
    await linkArticleToTicket.submit({ ticket: sourceTicket, article: savedArticle.name })
  }
  ```

- **Permission Model (ADR-04):** All new API methods must call `frappe.has_permission("HD Ticket", "write", throw=True)` to enforce Agent-only access. Guest and customer users must never be able to create or remove ticket-article links.

- **Only Published Articles in Search:** The `search_articles` API must always include `{"status": "Published"}` in the `frappe.db.get_all` filters. This prevents agents from accidentally linking Draft or In Review articles to tickets, and ensures consistency with the KB visibility model from Story 5.1.

### Files to Create / Modify

| Action | Path | Notes |
|--------|------|-------|
| Create | `helpdesk/helpdesk/doctype/hd_ticket_article/__init__.py` | Empty file |
| Create | `helpdesk/helpdesk/doctype/hd_ticket_article/hd_ticket_article.json` | Child DocType schema definition |
| Create | `helpdesk/helpdesk/doctype/hd_ticket_article/hd_ticket_article.py` | Empty controller |
| Modify | `helpdesk/helpdesk/doctype/hd_ticket/hd_ticket.json` | Add `linked_articles` Table field + KB Section Break |
| Modify | `helpdesk/api/knowledge_base.py` | Add `search_articles`, `link_article_to_ticket`, `remove_article_link`, `get_linked_tickets`, `prefill_article_from_ticket` methods |
| Create | `desk/src/components/kb/ArticleLinkDialog.vue` | Search + select modal dialog |
| Create | `desk/src/components/ticket/LinkedArticles.vue` | Ticket sidebar linked articles panel |
| Create | `desk/src/components/kb/LinkedTickets.vue` | Article detail linked tickets section |
| Modify | `desk/src/pages/ticket/TicketSidebarContent.vue` (or equiv.) | Integrate `LinkedArticles.vue` |
| Modify | `desk/src/pages/knowledge-base/Article.vue` (or equiv.) | Integrate `LinkedTickets.vue`; handle pre-fill route state |
| Create | `helpdesk/patches/v1_phase1/add_linked_articles_to_hd_ticket.py` | Migration patch (ordering only) |
| Modify | `helpdesk/patches.txt` | Register new patch |
| Create | `helpdesk/helpdesk/doctype/hd_article/test_ticket_article_linking.py` | Unit tests for linking |

### Testing Standards

- Minimum 80% unit test coverage on all new API methods (NFR-M-01).
- Use `frappe.tests.utils.FrappeTestCase` as base class for all test cases.
- Create test fixtures (ticket, article) in `setUp` and clean up via `addCleanup` or `tearDown`.
- Mock `frappe.session.user` to test guest vs. agent permission scenarios.
- Use `frappe.set_user("test_agent@example.com")` to impersonate agent role in tests.
- Run full test module: `bench --site <site> run-tests --module helpdesk.helpdesk.doctype.hd_article.test_ticket_article_linking`

### Constraints

- **AR-04 (Modify DocType JSON directly, not Custom Fields):** The `linked_articles` field on HD Ticket and all `HD Ticket Article` fields must be defined in source JSON files.
- **AR-05 (Patches in `helpdesk/patches/v1_phase1/`):** Migration patch must be placed in this directory and registered in `patches.txt`.
- **NFR-SE-01 (Never expose internal notes):** No API in this story returns internal note content. The `prefill_article_from_ticket` method must fetch only communications with `communication_type = "Communication"` (not internal notes).
- **NFR-M-02 (REST API coverage):** The `HD Ticket Article` DocType auto-generates REST API via Frappe (`/api/resource/HD Ticket Article`). No additional REST setup needed.
- **Backward compatibility:** Adding the `linked_articles` Table field to HD Ticket is additive (NULL-equivalent for existing records) and does not break any existing ticket workflows, SLA rules, or assignments.
- **Customer portal isolation:** `get_linked_tickets` and article search APIs are agent-only. The customer portal must never expose the `linked_articles` table or ticket-article link data.

### Project Structure Notes

- **Child DocType naming convention:** `HD Ticket Article` follows the `HD ` prefix convention (AR-02); folder is `hd_ticket_article/` [Source: architecture.md#Naming Patterns]
- **API module location:** New methods are added to `helpdesk/api/knowledge_base.py` (which already exists for article search functions) [Source: architecture.md#ADR-08; existing `helpdesk/api/article.py` and `knowledge_base.py`]
- **Frontend component placement:**
  - `ArticleLinkDialog.vue` → `desk/src/components/kb/` (KB-related dialog) [Source: architecture.md#ADR-09 — `desk/src/components/kb/ArticleLinkDialog.vue` explicitly listed]
  - `LinkedArticles.vue` → `desk/src/components/ticket/` (ticket sidebar panel) [Source: architecture.md#ADR-09 — `desk/src/components/ticket/` for ticket enhancements]
  - `LinkedTickets.vue` → `desk/src/components/kb/` (KB article enhancement) [Source: architecture.md#ADR-09 — `desk/src/components/kb/`]
- **Dependency on Story 5.1:** The `search_articles` API filters by `status = "Published"` which requires the `In Review` status from Story 5.1 to be present in the schema. If Story 5.1 is not yet deployed, the filter still works (Published articles still exist). Story 5.4 is independent enough to proceed before 5.1 is done.
- **No new Pinia store needed:** Linked article state is local to the `LinkedArticles.vue` component and uses `createResource` directly — no global store required for this feature.

### References

- FR-KB-04 (Ticket-article linking): [Source: _bmad-output/planning-artifacts/epics.md#Story 5.4]
- FR-KB-04 (PRD): [Source: _bmad-output/planning-artifacts/prd.md#FR-KB-04]
- ADR-02 (New DocTypes — `HD Ticket Article` follows `HD Related Ticket` pattern): [Source: _bmad-output/planning-artifacts/architecture.md#ADR-02]
- ADR-08 (API design — whitelisted methods in `helpdesk/api/`): [Source: _bmad-output/planning-artifacts/architecture.md#ADR-08]
- ADR-09 (Frontend component organization — `desk/src/components/kb/`, `desk/src/components/ticket/`): [Source: _bmad-output/planning-artifacts/architecture.md#ADR-09; `ArticleLinkDialog.vue` explicitly listed]
- ADR-04 (Permission model — `frappe.has_permission` checks): [Source: _bmad-output/planning-artifacts/architecture.md#ADR-04]
- AR-02 (HD prefix naming convention): [Source: _bmad-output/planning-artifacts/epics.md#Additional Requirements]
- AR-04 (Modify DocType JSON directly): [Source: _bmad-output/planning-artifacts/epics.md#Additional Requirements]
- AR-05 (Migration patches in `helpdesk/patches/v1_phase1/`): [Source: _bmad-output/planning-artifacts/epics.md#Additional Requirements]
- NFR-M-01 (80% unit test coverage): [Source: _bmad-output/planning-artifacts/epics.md#Non-Functional Requirements]
- NFR-P-07 (Dashboard widget load < 1s): [Source: _bmad-output/planning-artifacts/epics.md#Non-Functional Requirements]
- NFR-U-04 (WCAG 2.1 AA accessibility): [Source: _bmad-output/planning-artifacts/epics.md#Non-Functional Requirements]
- UX user journey UJ-05 (KB author workflow — "Create KB Article from Ticket"): [Source: _bmad-output/planning-artifacts/prd.md#UJ-05]
- Existing HD Article DocType: `helpdesk/helpdesk/doctype/hd_article/hd_article.{json|py}`
- Existing KB API: `helpdesk/api/knowledge_base.py`, `helpdesk/api/article.py`
- Existing HD Ticket DocType: `helpdesk/helpdesk/doctype/hd_ticket/hd_ticket.json`
- Related story pattern (child table linking): Story 1.6 Related Ticket Linking (`HD Related Ticket` child DocType)

## Dev Agent Record

### Agent Model Used

Claude Sonnet 4.5 (create-story workflow)

### Debug Log References

_None — story creation phase_

### Completion Notes List

_To be filled by implementing dev agent_

### File List

_To be filled by implementing dev agent upon completion_
