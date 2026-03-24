# QA Report: Story 5.4 — Ticket-Article Linking (Task #45)

**Date:** 2026-03-24
**QA Depth:** 1/1
**Testing Method:** Backend unit tests (16/16 pass), API endpoint testing via curl, code review
**Note:** Playwright MCP tools were not available in this environment. Testing was conducted via API calls and code review.

---

## Acceptance Criteria Results

### AC1: Link Article in ticket sidebar — search dialog to find and select published articles
**Result: PASS**

**Evidence:**
- `ArticleLinkDialog.vue` implements an Autocomplete-based search dialog that calls `helpdesk.api.knowledge_base.search_articles`
- API tested: `search_articles(query="QA")` returns only Published articles with name, title, and category_name
- API tested: `search_articles(query="Version")` returns empty — correctly excludes Draft article "Version Test Article"
- Debounced search (200ms) prevents excessive API calls
- Dialog has proper Cancel/Link Article buttons with loading state
- Integrated in `LinkedArticles.vue` via "Link" button in ticket sidebar

### AC2: Linked articles shown in ticket sidebar with title and click-through link
**Result: PASS**

**Evidence:**
- `LinkedArticles.vue` renders linked articles as a list with article titles
- Click-through implemented via `router.push(/articles/${link.article})`
- Count badge shown in header: `({{ linkedArticles.data.length }})`
- Empty state: "No linked articles" text
- Unlink (X) button with confirmation dialog (red "Remove" button)
- Component mounted in `TicketDetailsTab.vue` at line 73: `<LinkedArticles v-if="ticket?.doc?.name" :ticket-id="String(ticket.doc.name)" />`
- API tested: `link_article_to_ticket(ticket="12116", article="0059pu09mf")` returns `{"article": "0059pu09mf", "article_title": "QA Review Date Test Article"}`
- API tested: `remove_article_link(ticket="12116", article="0059pu09mf")` returns successfully, verified count drops to 0

### AC3: Create Article from Ticket — pre-fills new article with ticket subject and resolution details
**Result: PASS**

**Evidence:**
- `LinkedArticles.vue` has "Create Article" button that calls `prefill_article_from_ticket` API
- API tested: `prefill_article_from_ticket(ticket="12116")` returns:
  ```json
  {
    "title": "Test Ticket for Incident Model",
    "content": "<h2>Problem</h2><p>Test Ticket for Incident Model</p>",
    "category": "",
    "source_ticket": "12116"
  }
  ```
- Pre-fill data stored in `sessionStorage["hd_article_prefill"]`
- `NewArticle.vue` reads and clears sessionStorage on mount (line 108-122)
- Auto-links article back to source ticket after creation (line 149-151)
- Internal notes excluded: API filters `communication_type="Communication"` only (line 518)

### AC4: Article detail shows list of linked tickets (count and recent 10)
**Result: PASS**

**Evidence:**
- `LinkedTickets.vue` calls `get_linked_tickets(article)` API
- API returns `{count, tickets[]}` — limited to 10 most recent with `order_by="linked_on desc"`
- Shows "...and N more ticket(s)" when count > displayed tickets
- Ticket rows show #name, subject, and status badge with color mapping
- Click-through to ticket via `router.push(/tickets/${t.name})`
- Component gated to agents only in `Article.vue` line 170: `v-if="!isCustomerPortal && article.data?.name"`
- API tested: `get_linked_tickets(article="0059pu09mf")` returned `{count: 1, tickets: [{name: "12116", subject: "...", status: "Open", linked_on: "..."}]}`

---

## Additional Checks

### Duplicate Prevention
**PASS** — `link_article_to_ticket` raises `ValidationError` with message "Article 'X' is already linked to this ticket." when attempting duplicate link.

### Permission Boundary (NFR-SE-01)
**PASS** — All 5 API methods use `is_agent()` check. Unit tests verify:
- `test_link_article_requires_agent` — PermissionError for non-agent
- `test_remove_article_link_requires_agent` — PermissionError for non-agent
- `test_prefill_article_from_ticket_requires_agent` — PermissionError for non-agent

### Unit Tests
**PASS** — All 16 tests pass:
```
Ran 16 tests in 0.684s — OK
```

### Frontend Build
**PASS** — `yarn build` completes in 29s with no errors or warnings.

### DocType Definition
**PASS** — `HD Ticket Article` is correctly defined as `istable=1` with fields: article (Link to HD Article, reqd), article_title (fetch_from), linked_by (default __user), linked_on (default Now). Class name `HDTicketArticle` follows Frappe convention.

### Migration Patch
**PASS** — `helpdesk.patches.v1_phase1.add_linked_articles_to_hd_ticket` registered in `patches.txt`.

---

## Console Errors
No console errors observed during API testing. Frontend build is clean.

## Regressions
No regressions detected. The feature adds new components/APIs without modifying existing logic. The `TicketDetailsTab.vue` and `Article.vue` additions are additive (new sections appended to sidebar/detail views).

---

## Summary

| AC | Description | Result |
|----|-------------|--------|
| AC1 | Link Article search dialog | PASS |
| AC2 | Linked articles in ticket sidebar | PASS |
| AC3 | Create Article from Ticket with pre-fill | PASS |
| AC4 | Linked tickets on article detail | PASS |

**Overall: ALL PASS — No fix task required.**
