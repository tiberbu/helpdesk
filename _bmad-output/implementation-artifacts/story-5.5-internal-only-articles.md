# Story 5.5: Internal-Only Articles

Status: ready-for-dev

## Story

As a KB author,
I want to mark articles as internal-only,
so that sensitive procedures are available to agents but hidden from customers.

## Acceptance Criteria

1. **[HD Article — `internal_only` Field Schema]** Given the `hd_article.json` DocType is inspected, when a developer reviews the fields, then a `Check` field named `internal_only` (label: "Internal Only", default: 0, description: "When checked, this article is hidden from the customer portal and public knowledge base") exists on HD Article. This field is added directly to the DocType JSON (not via Custom Fields, per AR-04).

2. **[Customer Portal — Exclude Internal Articles]** Given an article has `internal_only = 1`, when any customer-facing endpoint returns KB articles (customer portal list, public KB search, portal article detail), then the article is NOT included in the response. The server-side filter `{"internal_only": 0}` (or equivalent) must be applied at the API/query level before data is returned — never relying solely on frontend hiding.

3. **[Customer Portal — Direct URL Access Blocked]** Given an article has `internal_only = 1`, when a customer (unauthenticated user or user without Agent role) attempts to access the article detail page via its direct URL (`/helpdesk/kb/{article_name}` or `/knowledge-base/{article_name}`), then the server returns a 404 or "Not Found" response — the article content is never served.

4. **[Agent Workspace KB Search — Internal Articles Visible]** Given an article has `internal_only = 1` and `status = "Published"`, when an agent searches the KB from the agent workspace, then the article appears in search results alongside public articles. Internal articles are not hidden from agents.

5. **[Agent Workspace — "Internal" Badge on Article List]** Given an agent views the KB article list in the agent workspace, when an article has `internal_only = 1`, then the article row displays a visual "Internal" badge (using `frappe-ui` `Badge` component with a warning/amber color) and a lock icon (Lucide `Lock` icon, 14px) adjacent to the article title. Public articles show no such badge.

6. **[Agent Workspace — "Internal" Badge on Article Detail]** Given an agent opens an internal article's detail page in the agent workspace, when the article has `internal_only = 1`, then a prominent "Internal" badge with lock icon is displayed near the article title/header (not in the body). This badge is never shown in customer-facing views.

7. **[Agent Workspace — "Internal" Badge on KB Search Results]** Given an agent is searching the KB from within the agent workspace (e.g., the KB search panel, or the `ArticleLinkDialog` from Story 5.4), when the search returns an article with `internal_only = 1`, then the result row shows the "Internal" badge with lock icon. This distinguishes internal articles from public ones at a glance.

8. **[API — `get_articles` / `list_articles` Server-Side Filter]** Given any whitelisted API method that returns a list of articles for customer-facing consumption (e.g., `helpdesk.api.knowledge_base.get_articles`, portal-side `get_kb_articles`, or equivalent), when the caller does not have the Agent role, then `{"internal_only": 0}` is included in the query filters so internal articles are never returned. Agent-role callers receive all articles (including internal ones).

9. **[Migration Patch]** Given a pre-existing Frappe Helpdesk installation with HD Article records, when the Phase 1 migration patch `add_internal_only_to_hd_article.py` runs, then the `internal_only` field is available on all HD Article records with a default value of `0` (false). No existing articles are retroactively marked as internal. No data loss occurs.

10. **[Unit Tests — Visibility Filtering]** Given the implementation is complete, when the test suite runs, then unit tests in `test_hd_article.py` (or a new `test_internal_only_articles.py`) pass covering:
    - (a) An article with `internal_only = 1` is excluded from customer-facing article list API responses
    - (b) An article with `internal_only = 0` is included in customer-facing article list API responses
    - (c) An article with `internal_only = 1` IS included when the caller has Agent role
    - (d) A customer (no Agent role) cannot retrieve an internal article by direct name/ID via the public article API
    - (e) An agent CAN retrieve an internal article by direct name/ID via the agent article API
    Minimum 80% coverage on all new/modified API methods (NFR-M-01).

## Tasks / Subtasks

- [ ] Task 1 — Add `internal_only` Check field to HD Article DocType (AC: #1, #9)
  - [ ] 1.1 Open `helpdesk/helpdesk/doctype/hd_article/hd_article.json`
  - [ ] 1.2 Add a `Check` field `internal_only` (label: "Internal Only", default: 0, description: "When checked, this article is hidden from the customer portal and public knowledge base") directly in the fields array (per AR-04, not via Custom Fields)
  - [ ] 1.3 Place the field in a logical position — after the `status` / `workflow_state` fields, or in a dedicated "Visibility" section break
  - [ ] 1.4 Create migration patch file `helpdesk/patches/v1_phase1/add_internal_only_to_hd_article.py` with an `execute()` function that is a no-op (field addition is handled by `bench migrate`; patch provides ordering guarantee)
  - [ ] 1.5 Register the patch in `helpdesk/patches.txt`

- [ ] Task 2 — Add server-side filter to all customer-facing article APIs (AC: #2, #3, #8)
  - [ ] 2.1 Identify all API methods and portal routes that return HD Article records to non-agent callers — check `helpdesk/api/knowledge_base.py`, `helpdesk/api/article.py`, and any portal-facing templates or controllers (e.g., `helpdesk/www/` or portal page Python controllers)
  - [ ] 2.2 In each identified customer-facing query, add `{"internal_only": 0}` to the `frappe.db.get_all()` / `frappe.db.get_value()` / `frappe.qb` filters so internal articles are excluded at the database layer
  - [ ] 2.3 For article detail retrieval by name/slug (single article fetch), add a guard: after fetching the article, check `if article.internal_only and not frappe.has_permission("HD Article", "read", user=frappe.session.user, ptype="write")` (or Agent role check) — if the caller lacks agent access, raise `frappe.DoesNotExistError` or call `frappe.throw(_("Not found"), frappe.DoesNotExistError)` (returns 404)
  - [ ] 2.4 Ensure the agent-workspace article APIs (called from `desk/` frontend) do NOT apply the `internal_only` filter — agents should see all articles
  - [ ] 2.5 Add `frappe._(...)` to all new user-facing error strings for i18n compliance (Architecture Enforcement Guideline #7)

- [ ] Task 3 — Add "Internal" badge and lock icon to agent workspace article list (AC: #5)
  - [ ] 3.1 Identify the agent-workspace article list component — likely `desk/src/pages/knowledge-base/KnowledgeBase.vue` or `desk/src/pages/knowledge-base/Articles.vue` (inspect `desk/src/pages/knowledge-base/` to confirm)
  - [ ] 3.2 Ensure `internal_only` field is included in the `fields` array of the `createListResource` call that fetches articles for the agent KB list
  - [ ] 3.3 In the article list row template, conditionally render a `frappe-ui` `Badge` (label: "Internal", theme: "orange" or "yellow") plus a Lucide `Lock` icon (size: 14) adjacent to the article title when `article.internal_only === 1`
  - [ ] 3.4 The badge must only appear in the agent workspace list — confirm the same component is not reused for the customer portal view (if shared, gate the badge rendering with an agent-context check)
  - [ ] 3.5 Follow WCAG 2.1 AA (NFR-U-04): the lock icon must have `aria-label="Internal article"` or be accompanied by the visible "Internal" text badge so screen readers convey the meaning

- [ ] Task 4 — Add "Internal" badge and lock icon to agent workspace article detail view (AC: #6)
  - [ ] 4.1 Identify the article detail page component — likely `desk/src/pages/knowledge-base/Article.vue`
  - [ ] 4.2 Ensure `internal_only` is fetched with the article resource
  - [ ] 4.3 In the article header / title area, conditionally render the "Internal" badge (same `frappe-ui` Badge + Lucide Lock pattern as Task 3) when `article.internal_only === 1`
  - [ ] 4.4 The badge must NOT appear when the article is viewed through any customer portal route

- [ ] Task 5 — Add "Internal" badge to KB search results in agent workspace (AC: #7)
  - [ ] 5.1 Identify the KB search component(s) used by agents — could be a search panel in the ticket sidebar, the `ArticleLinkDialog.vue` (from Story 5.4), or a standalone search page
  - [ ] 5.2 Ensure `internal_only` is included in the fields returned by `search_articles` API (or equivalent search endpoint used by the agent)
  - [ ] 5.3 In each search result row, conditionally render the "Internal" badge + lock icon when `result.internal_only === 1`
  - [ ] 5.4 The badge rendering should use a shared Vue component or utility so the look-and-feel is consistent across list, detail, and search (consider extracting an `InternalArticleBadge.vue` shared component under `desk/src/components/kb/`)

- [ ] Task 6 — Write unit tests for visibility filtering (AC: #10)
  - [ ] 6.1 Create (or open) `helpdesk/helpdesk/doctype/hd_article/test_internal_only_articles.py`
  - [ ] 6.2 Write `test_internal_article_excluded_from_customer_api` — create a Published article with `internal_only = 1`, call the customer-facing list API as a guest/customer user, assert the article is NOT in the response
  - [ ] 6.3 Write `test_public_article_included_in_customer_api` — create a Published article with `internal_only = 0`, call the customer-facing list API, assert the article IS in the response
  - [ ] 6.4 Write `test_internal_article_visible_to_agent` — create a Published article with `internal_only = 1`, call the agent-workspace list/search API as an Agent role user, assert the article IS in the response
  - [ ] 6.5 Write `test_customer_cannot_fetch_internal_article_by_name` — create a Published article with `internal_only = 1`, attempt to fetch it by name via the public article detail API as a guest user, assert a 404 / `DoesNotExistError` / permission error is raised
  - [ ] 6.6 Write `test_agent_can_fetch_internal_article_by_name` — create a Published article with `internal_only = 1`, fetch it by name via the agent detail API as an Agent role user, assert the article data is returned successfully
  - [ ] 6.7 Run tests: `bench --site <site> run-tests --module helpdesk.helpdesk.doctype.hd_article.test_internal_only_articles`

## Dev Notes

### Architecture Patterns

- **Field added directly to DocType JSON (AR-04):** The `internal_only` `Check` field must be added to `hd_article.json` in the source code — not via Frappe's Custom Fields mechanism. This is consistent with all Phase 1 field additions to existing DocTypes (same pattern as `review_date`, `reviewed_by`, and `version_count` added to HD Article in Stories 5.2/5.3).

- **Server-side filter is mandatory (NFR-SE-01 analog for KB):** Filtering internal articles must happen at the database query layer — never as a frontend-only filter. The pattern mirrors how internal notes on tickets are protected:
  ```python
  # Customer-facing query — always exclude internal articles
  articles = frappe.db.get_all(
      "HD Article",
      filters={"status": "Published", "internal_only": 0},
      fields=["name", "title", "category", "modified"],
  )
  ```
  ```python
  # Agent workspace query — no internal_only filter applied
  articles = frappe.db.get_all(
      "HD Article",
      filters={"status": "Published"},
      fields=["name", "title", "category", "internal_only", "modified"],
  )
  ```

- **Role-based access check for single article detail:**
  ```python
  @frappe.whitelist(allow_guest=True)
  def get_article(article_name: str):
      article = frappe.get_doc("HD Article", article_name)
      if article.internal_only:
          # Check if caller is an agent
          if not frappe.db.exists("HD Agent", {"user": frappe.session.user}):
              frappe.throw(frappe._("Not found"), frappe.DoesNotExistError)
      return article
  ```
  Alternatively, use `frappe.has_permission` with a custom permission check. The key requirement is that the article content is **never returned** to a non-agent caller when `internal_only = 1`.

- **Agent role check pattern (ADR-04):**
  ```python
  # Check if the current user is a helpdesk agent
  is_agent = frappe.db.exists("HD Agent", {"user": frappe.session.user})
  # OR use Frappe role check:
  is_agent = "HD Agent" in frappe.get_roles(frappe.session.user)
  ```
  Use whichever pattern is already established in the existing codebase (check `helpdesk/api/knowledge_base.py` for the current convention).

- **Shared `InternalArticleBadge` Vue component (optional but recommended):** To ensure visual consistency across the article list, detail, search results, and `ArticleLinkDialog`, consider creating a small shared component:
  ```vue
  <!-- desk/src/components/kb/InternalArticleBadge.vue -->
  <template>
    <span v-if="show" class="inline-flex items-center gap-1">
      <Badge label="Internal" theme="orange" size="sm" />
      <Lock :size="14" aria-label="Internal article" />
    </span>
  </template>
  <script setup lang="ts">
  import { Badge } from "frappe-ui"
  import { Lock } from "lucide-vue-next"
  defineProps<{ show: boolean }>()
  </script>
  ```
  This avoids duplicating the badge markup in four places and makes future styling changes trivial.

- **`createListResource` fields array — include `internal_only`:** When the agent workspace fetches article lists, the `fields` array in `createListResource` must include `"internal_only"` so the frontend receives the flag. Example:
  ```javascript
  const articles = createListResource({
    doctype: "HD Article",
    fields: ["name", "title", "category", "status", "internal_only", "modified"],
    // ... filters, etc.
  })
  ```

- **Customer portal routes to audit:** The customer-facing KB is served from portal pages or a public Vue frontend. Audit all of the following for `internal_only` filtering:
  - Any `helpdesk/api/knowledge_base.py` methods called from the customer portal
  - Any `helpdesk/api/article.py` public methods
  - Any Frappe portal page Python controllers under `helpdesk/www/` that query HD Article
  - The customer portal Vue frontend (if it exists as a separate app under `helpdesk/portal/` or similar)

### Files to Create / Modify

| Action | Path | Notes |
|--------|------|-------|
| Modify | `helpdesk/helpdesk/doctype/hd_article/hd_article.json` | Add `internal_only` Check field (default: 0) |
| Create | `helpdesk/patches/v1_phase1/add_internal_only_to_hd_article.py` | Migration patch (no-op execute, ordering only) |
| Modify | `helpdesk/patches.txt` | Register new patch |
| Modify | `helpdesk/api/knowledge_base.py` | Add `internal_only: 0` filter to customer-facing queries; guard on article detail fetch |
| Modify | `helpdesk/api/article.py` (if exists) | Same filtering as above for any public article methods |
| Create | `desk/src/components/kb/InternalArticleBadge.vue` | Shared badge + lock icon component (recommended) |
| Modify | `desk/src/pages/knowledge-base/Articles.vue` (or equiv.) | Include `internal_only` in fields; render badge conditionally |
| Modify | `desk/src/pages/knowledge-base/Article.vue` (or equiv.) | Include `internal_only` in fields; render badge in header |
| Modify | `desk/src/components/kb/ArticleLinkDialog.vue` (or equiv.) | Include `internal_only` in search results; render badge |
| Create | `helpdesk/helpdesk/doctype/hd_article/test_internal_only_articles.py` | Unit tests for visibility filtering |

### Testing Standards

- Minimum 80% unit test coverage on all new/modified API methods (NFR-M-01).
- Use `frappe.tests.utils.FrappeTestCase` as base class for all test cases.
- Create test HD Article fixtures in `setUp`; clean up with `tearDown` or `addCleanup`.
- Use `frappe.set_user("Administrator")` for agent-context tests and `frappe.set_user("Guest")` or an unprivileged user for customer-context tests.
- Run full test module: `bench --site <site> run-tests --module helpdesk.helpdesk.doctype.hd_article.test_internal_only_articles`

### Constraints

- **AR-04 (Modify DocType JSON directly):** `internal_only` field must be in `hd_article.json`, not a Custom Field.
- **AR-05 (Patches in `helpdesk/patches/v1_phase1/`):** Migration patch must be placed in this exact directory and registered in `patches.txt`.
- **Backward compatibility:** Adding `internal_only` (Check, default: 0) to HD Article is additive and non-destructive. All existing articles default to `internal_only = 0` (public), preserving existing behavior for all customers.
- **NFR-SE-01 (data isolation):** By analogy with internal notes on tickets, internal articles must NEVER be returned to customer-facing API callers regardless of direct URL access attempts. Server-side enforcement is mandatory.
- **NFR-M-02 (REST API):** The `internal_only` field is automatically exposed on the HD Article REST endpoint (`/api/resource/HD Article`) via Frappe's auto-generated CRUD. No additional REST setup needed. However, the standard Frappe REST API does not apply custom visibility filters — ensure all custom article list/fetch endpoints apply the `internal_only: 0` filter for non-agent callers.
- **No customer portal source modification without verification:** Before modifying customer portal article queries, verify the exact file paths by inspecting `helpdesk/www/` and any portal Vue app directories. The architecture doc references `desk/src/` for the agent workspace and a separate portal frontend. Do not blindly assume file paths.

### Project Structure Notes

- **HD Article DocType location:** `helpdesk/helpdesk/doctype/hd_article/hd_article.json` — the existing DocType to modify [Source: architecture.md#Complete Project Directory Structure]
- **Patches directory:** `helpdesk/patches/v1_phase1/` — all Phase 1 schema migration patches [Source: architecture.md#ADR-02 and epics.md#AR-05]
- **API module location:** `helpdesk/api/knowledge_base.py` — existing module for KB-related API methods [Source: architecture.md#ADR-08; consistent with Story 5.4 approach]
- **Agent workspace frontend:** `desk/src/pages/knowledge-base/` — existing KB pages; `desk/src/components/kb/` — KB components [Source: architecture.md#ADR-09]
- **Shared badge component:** `desk/src/components/kb/InternalArticleBadge.vue` — follows the `desk/src/components/kb/` convention for KB-related shared components [Source: architecture.md#ADR-09 — `desk/src/components/kb/` explicitly listed]
- **Dependency on Story 5.1:** Story 5.1 adds the article review workflow and `status` field values (Draft/In Review/Published/Archived). Story 5.5 relies on `status = "Published"` being present for the customer portal visibility filter to function correctly. However, Story 5.5 can be implemented independently — the `internal_only` filter works alongside whatever `status` values exist. If Story 5.1 is not deployed, the `status` filter should still use the existing published/visibility convention in the codebase.
- **No new Pinia store needed:** The `internal_only` flag is a simple field on the article document; no global state is required. Local `createResource` / `createListResource` with the `internal_only` field included is sufficient.

### References

- FR-KB-05 (Internal-only articles — PRD): [Source: _bmad-output/planning-artifacts/prd.md#FR-KB-05]
- FR-KB-05 (Internal-only articles — Epics Story 5.5): [Source: _bmad-output/planning-artifacts/epics.md#Story 5.5]
- ADR-02 (Existing DocType modifications — HD Article field additions): [Source: _bmad-output/planning-artifacts/architecture.md#ADR-02]
- ADR-04 (Permission model — role-based access checks): [Source: _bmad-output/planning-artifacts/architecture.md#ADR-04]
- ADR-08 (API design — whitelisted methods in `helpdesk/api/`): [Source: _bmad-output/planning-artifacts/architecture.md#ADR-08]
- ADR-09 (Frontend component organization — `desk/src/components/kb/`): [Source: _bmad-output/planning-artifacts/architecture.md#ADR-09]
- AR-02 (HD prefix naming convention): [Source: _bmad-output/planning-artifacts/epics.md#Additional Requirements]
- AR-04 (Modify DocType JSON directly, not Custom Fields): [Source: _bmad-output/planning-artifacts/epics.md#Additional Requirements]
- AR-05 (Migration patches in `helpdesk/patches/v1_phase1/`): [Source: _bmad-output/planning-artifacts/epics.md#Additional Requirements]
- NFR-M-01 (80% unit test coverage): [Source: _bmad-output/planning-artifacts/epics.md#Non-Functional Requirements]
- NFR-M-02 (All new DocTypes / fields accessible via REST API): [Source: _bmad-output/planning-artifacts/epics.md#Non-Functional Requirements]
- NFR-SE-01 (Sensitive data isolation — never expose to non-agents): [Source: _bmad-output/planning-artifacts/epics.md#Non-Functional Requirements]
- NFR-U-04 (WCAG 2.1 AA accessibility for all new UI components): [Source: _bmad-output/planning-artifacts/epics.md#Non-Functional Requirements]
- UX-DR-10 (Article lifecycle badges — color-coded status indicators): [Source: _bmad-output/planning-artifacts/epics.md#UX Design Requirements]
- Existing HD Article DocType: `helpdesk/helpdesk/doctype/hd_article/hd_article.{json|py}`
- Existing KB API: `helpdesk/api/knowledge_base.py`, `helpdesk/api/article.py`
- Related story pattern (field addition to existing DocType): Story 5.2/5.3 (review_date, reviewed_by on HD Article); Story 5.4 (ArticleLinkDialog.vue, knowledge_base.py pattern)
- Related security pattern (server-side isolation): Story 1.4 Internal Notes (NFR-SE-01 — internal notes never exposed via customer portal)

## Dev Agent Record

### Agent Model Used

Claude Sonnet 4.5 (create-story workflow)

### Debug Log References

_None — story creation phase_

### Completion Notes List

_To be filled by implementing dev agent_

### File List

_To be filled by implementing dev agent upon completion_
