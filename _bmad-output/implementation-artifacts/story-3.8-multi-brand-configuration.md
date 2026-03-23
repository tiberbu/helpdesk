# Story 3.8: Multi-Brand Configuration

Status: ready-for-dev

## Story

As an administrator managing multiple brands,
I want to configure separate brand identities from a single Helpdesk instance,
so that each brand has its own portal appearance, email address, and support team.

## Acceptance Criteria

1. **HD Brand DocType** — The `HD Brand` DocType exists with fields: `name` (Data, unique), `logo` (Attach Image), `primary_color` (Color), `support_email` (Data, email format), `portal_domain` (Data), `default_team` (Link → HD Team), `default_sla` (Link → HD Service Level Agreement); only System Manager / HD Admin role can create, edit, or delete brands.

2. **Email-to-brand auto-tagging** — When a ticket is created via email, the inbound `to` address is matched against all active HD Brand `support_email` values; if a match is found, the ticket's `brand` field is set to that brand automatically (before-insert hook); no match leaves `brand` blank (default behavior preserved).

3. **Brand-based portal theming** — When a customer accesses the customer portal from a URL that matches an HD Brand's `portal_domain`, the portal renders the brand-specific logo, primary color (CSS variable override), and only shows KB articles associated with that brand; a default (no-brand) view is used when no domain match occurs.

4. **Brand filter on ticket list** — The agent ticket list view exposes a "Brand" filter that, when selected, restricts the list to tickets whose `brand` field matches the selected value; the filter appears alongside existing Priority, Status, and Team filters.

5. **Brand-specific CSAT templates and chat widget** — `HD CSAT Survey Template` records can be linked to an HD Brand (via `brand` Link field already defined in Story 3.7); when generating a CSAT survey for a ticket with a brand, the brand-specific template is used (falling back to default if none set); the embeddable chat widget script tag accepts a `data-brand` attribute that loads brand-specific colors, logo, and greeting.

## Tasks / Subtasks

- [ ] **Task 1 — HD Brand DocType** (AC: #1)
  - [ ] 1.1 Create `helpdesk/helpdesk/doctype/hd_brand/` directory with `__init__.py`
  - [ ] 1.2 Create `hd_brand.json` DocType schema with fields: `name` (Data, reqd, unique), `logo` (Attach Image), `primary_color` (Color), `support_email` (Data, options="Email"), `portal_domain` (Data), `default_team` (Link → HD Team), `default_sla` (Link → HD Service Level Agreement), `csat_template` (Link → HD CSAT Survey Template), `is_active` (Check, default 1)
  - [ ] 1.3 Create `hd_brand.py` controller with `validate()` — ensure `support_email` is valid email format if set, ensure `portal_domain` is unique across brands if set
  - [ ] 1.4 Set DocType permissions: System Manager and HD Admin can Create/Read/Write/Delete; HD Agent can Read only
  - [ ] 1.5 Write migration patch `helpdesk/patches/v1_phase1/add_hd_brand_doctype.py` (no-op migration — DocType JSON install is sufficient, patch records the migration)

- [ ] **Task 2 — Brand field on HD Ticket** (AC: #2, #4)
  - [ ] 2.1 Add `brand` (Link → HD Brand, optional) field to `helpdesk/helpdesk/doctype/hd_ticket/hd_ticket.json`
  - [ ] 2.2 Position `brand` field in the ticket form after `team` field (or in a new "Channel & Brand" section)
  - [ ] 2.3 Write migration patch `helpdesk/patches/v1_phase1/add_brand_field_to_hd_ticket.py`
  - [ ] 2.4 Add `brand` to the HD Ticket list view columns (optional, lower priority)

- [ ] **Task 3 — Email-to-brand matching** (AC: #2)
  - [ ] 3.1 Create `helpdesk/helpdesk/overrides/hd_ticket_brand.py` with function `assign_brand_from_email(doc, method)`:
    - Fetch all active HD Brand records with `support_email` set (cache in Redis with 5-min TTL)
    - Compare `doc.via_customer_portal` inbound address or parse email headers for `to` address against brand support emails (case-insensitive)
    - If match found: set `doc.brand` to matched brand name
    - Also set `doc.team` to `brand.default_team` and `doc.sla` to `brand.default_sla` if those fields are not already set
  - [ ] 3.2 Register the hook in `hooks.py`:
    ```python
    doc_events = {
        "HD Ticket": {
            "before_insert": "helpdesk.helpdesk.overrides.hd_ticket_brand.assign_brand_from_email",
        }
    }
    ```
  - [ ] 3.3 Merge with existing `doc_events` dict in `hooks.py` (additive; do not overwrite existing ticket hooks)

- [ ] **Task 4 — Brand-based portal theming** (AC: #3)
  - [ ] 4.1 Create `helpdesk/api/brand.py` with:
    - `get_brand_config(portal_domain: str) -> dict` — `@frappe.whitelist(allow_guest=True)` — looks up HD Brand by `portal_domain`, returns `{name, logo_url, primary_color, portal_domain}` or default config if not found
    - `get_brand_articles(brand: str, filters: dict) -> list` — `@frappe.whitelist(allow_guest=True)` — returns KB articles filtered by brand (assumes HD Article gains a `brand` optional Link field)
  - [ ] 4.2 Add `brand` (Link → HD Brand, optional) field to `hd_article.json` (HD Article DocType) to support brand-scoped KB articles
  - [ ] 4.3 Create `desk/src/composables/useBrandTheme.ts`:
    - On portal load, call `get_brand_config` with current `window.location.hostname`
    - Apply `--primary-color` CSS variable to `:root` if `primary_color` returned
    - Set portal logo `src` to returned `logo_url` if present
    - Export `{ brandConfig, applyTheme }` for use in portal layout
  - [ ] 4.4 Inject `useBrandTheme` into the portal root layout component (`portal/src/App.vue` or equivalent) so theming applies on first load

- [ ] **Task 5 — Brand filter on ticket list** (AC: #4)
  - [ ] 5.1 Add `brand` filter option to the agent ticket list filter configuration in `desk/src/pages/tickets/` (identify the filter config file or component — likely `TicketList.vue` or a filters composable)
  - [ ] 5.2 Filter should use a `Select` or `Link` field input populated by `frappe.db.get_all("HD Brand", fields=["name"])` via a `createListResource`
  - [ ] 5.3 Ensure the filter passes `{brand: selectedBrand}` as a frappe filter in the ticket list query
  - [ ] 5.4 Add "Brand" column to the ticket list view (optional: toggle-able via column chooser)

- [ ] **Task 6 — Brands settings page** (AC: #1, #5)
  - [ ] 6.1 Create `desk/src/pages/settings/Brands.vue`:
    - List view: show all HD Brand records with name, logo thumbnail, support_email, portal_domain, active status
    - "New Brand" button opens a create form
    - Edit/delete actions per row
    - Uses `createListResource` and `createResource` patterns (frappe-ui)
  - [ ] 6.2 Register route `/helpdesk/settings/brands` in the Vue Router config (likely `desk/src/router.ts` or `desk/src/router/index.ts`)
  - [ ] 6.3 Add "Brands" link to the Settings sidebar / navigation menu (identify the settings nav component and add the entry)
  - [ ] 6.4 Guard the route to System Manager / HD Admin roles (check existing auth guard pattern in router)

- [ ] **Task 7 — Chat widget brand integration** (AC: #5)
  - [ ] 7.1 Update `widget/src/main.js` to read `data-brand` attribute from the script tag and pass it to the root `Widget.vue` as a prop
  - [ ] 7.2 Update `widget/src/components/BrandingHeader.vue` to accept `brandConfig` prop (logo URL, primary color, greeting override from HD Brand)
  - [ ] 7.3 In `widget/src/main.js` or `Widget.vue`, on mount call `get_brand_config(portal_domain)` (or use `data-brand` name directly) to fetch brand styles; apply to Shadow DOM styles
  - [ ] 7.4 Pass `brand` name to `create_session` API so the HD Chat Session (and resulting HD Ticket) is tagged with the brand

- [ ] **Task 8 — Unit tests** (AC: #1, #2)
  - [ ] 8.1 Create `helpdesk/helpdesk/doctype/hd_brand/test_hd_brand.py`:
    - Test: brand creation with valid fields succeeds
    - Test: duplicate `support_email` or `portal_domain` raises validation error
    - Test: only System Manager / HD Admin can create/edit (permission test)
  - [ ] 8.2 Create `helpdesk/helpdesk/overrides/test_hd_ticket_brand.py`:
    - Test: ticket created with email matching `brand.support_email` is tagged with brand
    - Test: ticket created with unmatched email has no brand set
    - Test: ticket inherits `default_team` and `default_sla` from brand when not set
    - Test: case-insensitive email matching works correctly
  - [ ] 8.3 Run with `bench run-tests --app helpdesk --module helpdesk.helpdesk.doctype.hd_brand.test_hd_brand`

## Dev Notes

### Architecture Patterns

- **HD Brand DocType (ADR-02):** `HD Brand` is one of the 10 new DocTypes defined in the architecture. It follows the same DocType structure pattern: `helpdesk/helpdesk/doctype/hd_brand/{hd_brand.json, hd_brand.py, __init__.py, test_hd_brand.py}`. Naming follows `HD ` prefix convention (AR-02).
- **Permission Model (ADR-04):** Brand management is restricted to System Manager / HD Admin role — use `frappe.only_for(["System Manager", "HD Admin"])` in the controller or set permissions in the DocType JSON. All agents can read brand records (needed for ticket form brand field display).
- **Brand field on HD Ticket (ADR-01):** Adding `brand` field to HD Ticket follows the "Extend HD Ticket rather than separate DocTypes" decision. Field addition is additive (NULL default for legacy records).
- **Email-to-brand hook (ADR-01):** Register in `hooks.py` `doc_events["HD Ticket"]["before_insert"]`. The existing `doc_events` in `hooks.py` must be merged additively — check for existing entries before adding. See `helpdesk/hooks.py` for current `doc_events` structure.
- **Brand caching:** Brand support_email lookups happen on every inbound email. Cache the brand list in Redis (use `frappe.cache().get_value("hd_brand_list")` with a 5-min TTL) to avoid per-ticket DB queries.
- **Portal theming (Vue composable):** The portal frontend likely lives in `portal/` directory. The `useBrandTheme` composable should check `window.location.hostname` against the brand's `portal_domain`. Use `document.documentElement.style.setProperty("--primary-color", color)` to apply the CSS variable.
- **Guest API endpoints (ADR-04):** `get_brand_config` must use `@frappe.whitelist(allow_guest=True)` since customers access the portal without authentication. Sanitize all returned data — no internal fields.
- **Chat widget (ADR-10):** The widget is a separate IIFE bundle at `widget/src/`. Brand data flows in via `data-brand` script attribute. The Shadow DOM hosts brand-specific CSS variable overrides so the widget doesn't inherit host page styles.
- **DocType JSON patching (AR-04):** Adding `brand` to `hd_ticket.json` is done directly in the DocType JSON file (not Custom Fields), per AR-04. Write a migration patch in `helpdesk/patches/v1_phase1/` to document the schema change.
- **CSAT template per brand:** The `brand` field on `HD CSAT Survey Template` was already defined in Story 3.7 (Task 3, step 3.2). This story does NOT re-create that field — it relies on Story 3.7's output. The `HD Brand.csat_template` Link field established in this story's HD Brand DocType closes the loop.

### Existing Code Reference

- `hooks.py`: `helpdesk/hooks.py` — add `before_insert` hook to `doc_events["HD Ticket"]`
- HD Ticket DocType JSON: `helpdesk/helpdesk/doctype/hd_ticket/hd_ticket.json` — add `brand` field
- HD Article DocType JSON: `helpdesk/helpdesk/doctype/hd_article/hd_article.json` — add `brand` field
- Existing DocType pattern: See `helpdesk/helpdesk/doctype/hd_team/` for a simple DocType structure example
- Existing override pattern: See `helpdesk/helpdesk/overrides/hd_ticket.py` for ticket override functions
- Frontend settings pages: Check `desk/src/pages/settings/` for existing settings page pattern (e.g., `Teams.vue` if present)
- Vue Router: `desk/src/router.ts` or `desk/src/router/index.ts` — add `/helpdesk/settings/brands` route
- Portal frontend: `portal/` directory — locate `App.vue` or layout component for brand theme injection
- Widget entry: `widget/src/main.js` — read `data-brand` attribute

### Project Structure Notes

**New files to create:**
```
helpdesk/
├── helpdesk/
│   ├── api/
│   │   └── brand.py                                    # NEW: Brand API endpoints
│   ├── helpdesk/
│   │   └── doctype/
│   │       └── hd_brand/
│   │           ├── __init__.py                         # NEW
│   │           ├── hd_brand.json                       # NEW: DocType schema
│   │           ├── hd_brand.py                         # NEW: Controller
│   │           └── test_hd_brand.py                    # NEW: Unit tests
│   └── overrides/
│       ├── hd_ticket_brand.py                          # NEW: Email-to-brand matching
│       └── test_hd_ticket_brand.py                     # NEW: Unit tests
└── patches/
    └── v1_phase1/
        ├── add_hd_brand_doctype.py                     # NEW: Migration patch (no-op marker)
        └── add_brand_field_to_hd_ticket.py             # NEW: Migration patch

desk/
└── src/
    ├── composables/
    │   └── useBrandTheme.ts                            # NEW: Portal brand theming composable
    └── pages/
        └── settings/
            └── Brands.vue                              # NEW: Brand management settings page

widget/
└── src/
    ├── main.js                                         # MODIFIED: read data-brand attribute
    └── components/
        └── BrandingHeader.vue                          # MODIFIED: accept brandConfig prop
```

**Modified files:**
```
helpdesk/
├── hooks.py                                            # MODIFIED: add before_insert brand hook
└── helpdesk/
    └── doctype/
        ├── hd_ticket/
        │   └── hd_ticket.json                          # MODIFIED: add brand Link field
        └── hd_article/
            └── hd_article.json                         # MODIFIED: add brand Link field

desk/
└── src/
    ├── router.ts (or router/index.ts)                  # MODIFIED: add /settings/brands route
    └── pages/
        └── tickets/
            └── TicketList.vue (or filters composable)  # MODIFIED: add Brand filter
```

**Alignment with architecture:**
- DocType naming follows `HD ` prefix convention (AR-02)
- DocType folder: `hd_brand/` (snake_case, AR-02)
- API module at `helpdesk/api/brand.py` (matches ADR-08 API Design pattern)
- Settings page at `desk/src/pages/settings/Brands.vue` (matches ADR-09 component table)
- Migration patches in `helpdesk/patches/v1_phase1/` (AR-05)
- Guest API endpoints use `@frappe.whitelist(allow_guest=True)` (ADR-04)
- Feature is brand management; no separate feature flag needed (always available to admins)

### References

- [Source: _bmad-output/planning-artifacts/architecture.md#ADR-02: New DocType Schema for Phase 1]
- [Source: _bmad-output/planning-artifacts/architecture.md#ADR-04: Permission Model Extensions]
- [Source: _bmad-output/planning-artifacts/architecture.md#ADR-08: API Design for New Features]
- [Source: _bmad-output/planning-artifacts/architecture.md#ADR-09: Frontend Component Organization]
- [Source: _bmad-output/planning-artifacts/architecture.md#ADR-10: Chat Widget Build Strategy]
- [Source: _bmad-output/planning-artifacts/architecture.md#ADR-01: Extend HD Ticket Rather Than Separate DocTypes]
- [Source: _bmad-output/planning-artifacts/architecture.md#Implementation Patterns & Consistency Rules]
- [Source: _bmad-output/planning-artifacts/epics.md#Story 3.8: Multi-Brand Configuration]
- [Source: _bmad-output/planning-artifacts/epics.md#FR-MB-01: Multi-brand support with separate portals]
- [Source: _bmad-output/planning-artifacts/epics.md#AR-02: All new DocTypes follow HD prefix naming convention]
- [Source: _bmad-output/planning-artifacts/epics.md#AR-04: All new fields added via DocType JSON modification]
- [Source: _bmad-output/planning-artifacts/epics.md#AR-05: Migration patches in helpdesk/patches/v1_phase1/]
- [Source: _bmad-output/planning-artifacts/epics.md#NFR-M-01: Minimum 80% unit test coverage on all new backend code]
- [Source: _bmad-output/planning-artifacts/prd.md#FR-MB: Multi-Brand Support / FR-MB-01: Branded Portals]

## Dev Agent Record

### Agent Model Used

claude-opus-4-5

### Debug Log References

### Completion Notes List

### File List
