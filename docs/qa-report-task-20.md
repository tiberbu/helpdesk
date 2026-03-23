# QA Report: Story 1.4 - Internal Notes on Tickets

**Task:** #20 (Story 1.4: Internal Notes on Tickets)
**QA Task:** #52
**Reviewer Model:** opus (adversarial review)
**Date:** 2026-03-23
**Methodology:** Code-level adversarial review + unit test execution + API verification

---

## Acceptance Criteria Verification

### AC-1: Visually distinct editor with amber styling, lock icon, rich text, file attachments
**Result: PASS (with caveats - see P2-01, P2-05)**

**Evidence:**
- `InternalNote.vue` (line 52-54): `class="rounded bg-amber-50 border-l-4 border-amber-400"` -- correct amber-50 bg and amber-400 left border
- `InternalNoteIcon.vue`: SVG padlock icon -- correct lock icon
- Badge (line 57-63): `"Internal Note"` badge with `bg-amber-100 text-amber-700` -- visually distinct
- `InternalNoteTextEditor.vue`: Uses `TextEditor` with `FileUploader` component -- rich text and file attachment support confirmed
- `CommunicationArea.vue` (line 28-37): "Internal Note" button with amber styling in toolbar

### AC-2: Internal notes NOT visible in customer portal and NOT included in customer emails
**Result: PASS (with caveat - see P1-01)**

**Evidence:**
- `api.py` (line 219-221): `get_comments()` filters `is_internal == 0` for non-agents (server-side)
- `get_one()` (line 118) delegates to `get_comments()` which applies the filter
- Customer portal (`TicketCustomer.vue`) has no reference to `is_internal` -- it relies entirely on backend filtering, which is correct
- `HDTicketComment` doctype permissions restrict read to `System Manager` and `Agent` roles only -- customers can't read comments directly
- No email sending code in `new_internal_note()` -- internal notes don't trigger customer emails

### AC-3: Server-side permission check excludes internal notes from non-agent API calls
**Result: PASS**

**Evidence:**
- 10/10 unit tests passing (verified via `bench run-tests`)
- `new_internal_note()` (hd_ticket.py line 627-642): `is_agent()` check before creation, throws `PermissionError`
- `get_comments()` (api.py line 220-221): `is_agent()` check filters internal notes
- `new_comment()` (hd_ticket.py line 618): Explicitly sets `is_internal = False` -- prevents injection via regular comment path

---

## Adversarial Review Findings

### P1-01: Delete endpoint lacks agent-only authorization (SECURITY)
**Severity: P1 (High)**
**File:** `InternalNote.vue` line 197-208

The delete function uses `frappe.client.delete` which relies on Frappe's standard doctype permissions. While `HD Ticket Comment` has permissions restricted to `Agent` and `System Manager` roles, there is **no explicit server-side check** that only the note's author or an admin can delete internal notes. Any agent can delete any other agent's internal notes.

Additionally, the frontend only shows the delete button when `authStore.userId === commentedBy` (line 26), but this is a **client-side-only guard** -- a determined agent could call `frappe.client.delete` directly via the API to delete another agent's note.

**Expected:** Server-side `before_delete` hook on `HDTicketComment` that verifies the deleting user is either the author or a System Manager.
**Actual:** No server-side ownership check on delete.

### P1-02: Update endpoint lacks agent-only ownership validation (SECURITY)
**Severity: P1 (High)**
**File:** `InternalNote.vue` line 220-235

The update uses `updateRes` (a generic resource wrapper for `frappe.client.set_value`). This relies solely on Frappe doctype permissions. Any agent could update any other agent's internal note content by calling the API directly. The frontend restricts editing to the author (line 26), but this is purely a UI guard.

**Expected:** Server-side `before_save` or `validate` hook on `HDTicketComment` that verifies the editing user is the original author when `is_internal=1`.
**Actual:** No server-side ownership check on update.

### P2-01: `onMounted` sets width to 0px -- broken layout hack
**Severity: P2 (Medium)**
**File:** `InternalNote.vue` line 238-240

```js
onMounted(() => {
  internalNoteRef.value.style.width = "0px";
});
```

This sets the container width to 0px on mount, which is a bizarre layout hack. It will cause the internal note to be invisible or collapsed when first rendered. There's no subsequent code to restore it. This is likely a copy-paste error from another component or an incomplete animation implementation.

**Expected:** Component should be visible immediately on mount, or have proper show/hide animation.
**Actual:** Width forced to 0px with no mechanism to restore it.

### P2-02: Keyboard shortcut `n` not documented in ShortcutsModal
**Severity: P2 (Medium)**
**File:** `ShortcutsModal.vue` line 100-105

The Communication shortcuts section lists `R` (Reply) and `C` (Comment) but does **not** list `N` (Internal Note). Users have no way to discover this shortcut.

**Expected:** `{ keys: ["N"], description: __("Open internal note box") }` added to the Communication group.
**Actual:** Shortcut is registered but not documented in the shortcuts modal.

### P2-03: `merge_ticket` does not preserve `is_internal` flag awareness
**Severity: P2 (Medium)**
**File:** `api.py` line 332-390 (merge_ticket function)

When tickets are merged via `merge_ticket()`, the `duplicate_list_retain_timestamp` function copies all `HD Ticket Comment` records from source to target using `frappe.copy_doc()`. While `frappe.copy_doc()` should preserve `is_internal`, **there is no explicit test** for this, and the merge-generated comment on the target ticket (line 382-389) does not set `is_internal=0` explicitly -- it relies on the default value.

**Expected:** Explicit test that internal notes survive ticket merge with `is_internal=1` intact.
**Actual:** Implicit reliance on `frappe.copy_doc()` and default values.

### P2-04: `split_ticket` bulk-updates comments without considering internal notes
**Severity: P2 (Medium)**
**File:** `api.py` line 450-482 (split_ticket function)

When tickets are split, comments are moved via bulk `frappe.db.set_value()` (line 473-482) which updates `reference_ticket` for all comments matching a creation timestamp. This correctly moves internal notes along with regular comments. However, like merge, **there is no test** ensuring internal notes survive the split operation with their `is_internal` flag intact.

**Expected:** Test coverage for split preserving internal note flag.
**Actual:** No test.

### P2-05: Mutable default argument anti-pattern
**Severity: P2 (Medium)**
**File:** `hd_ticket.py` lines 609, 627

```python
def new_comment(self, content: str, attachments: list[str] = []):
def new_internal_note(self, content: str, attachments: list[str] = []):
```

Both methods use a mutable default argument (`[]`). This is a classic Python anti-pattern -- if the list is ever mutated, subsequent calls without arguments will see the mutated list. Should use `None` with a `or []` guard inside the function.

**Expected:** `attachments: list[str] | None = None` with `attachments = attachments or []` inside.
**Actual:** Mutable default `[]`.

### P2-06: Toggle functions duplicated between `modalStates.ts` and `CommunicationArea.vue`
**Severity: P2 (Medium)**
**Files:** `modalStates.ts` line 7-33, `CommunicationArea.vue` line 167-185

The toggle logic for `toggleEmailBox`, `toggleCommentBox` is defined in **both** `modalStates.ts` and `CommunicationArea.vue`, with slightly different implementations. `CommunicationArea.vue` defines local `toggleEmailBox` and `toggleCommentBox` functions that shadow the imported `toggleInternalNoteBox` from `modalStates.ts`. Only `toggleInternalNoteBox` is imported from `modalStates.ts`. This is confusing and error-prone -- the mutual exclusion logic could drift between the two copies.

**Expected:** Single source of truth for all toggle functions in `modalStates.ts`.
**Actual:** Duplicated toggle logic for email and comment boxes.

### P3-01: `InternalNoteTextEditor` leaks typing events for private notes
**Severity: P3 (Low)**
**File:** `InternalNoteTextEditor.vue` line 172-186

The component initializes `useTyping(props.ticketId)` and triggers `onUserType()` whenever content changes. This sends typing indicator events via realtime (presumably visible to all users viewing the ticket). Typing indicators for **internal notes** should not be broadcast to non-agent users, as they reveal that an agent is writing something privately.

**Expected:** Typing indicators suppressed for internal notes, or at least filtered to agent-only recipients.
**Actual:** Typing events broadcast without distinction between comment and internal note.

### P3-02: `useStorage` persists internal note content in localStorage
**Severity: P3 (Low)**
**File:** `InternalNoteTextEditor.vue` line 170

```js
const noteContent = useStorage("internalNoteBoxContent" + props.ticketId, null);
```

Internal note drafts are persisted to `localStorage` under a predictable key. If the browser is shared or the storage is accessed by another script/extension, the draft internal note content is exposed. For a feature explicitly designed for confidentiality, this is a minor information leak vector.

**Expected:** Either don't persist internal note drafts, or use sessionStorage, or encrypt the content.
**Actual:** Plaintext draft persisted in localStorage.

### P3-03: No activity log entry when internal note is created
**Severity: P3 (Low)**
**File:** `hd_ticket.py` line 627-642

When `new_comment()` is called, a `HD Ticket Comment` is created and a realtime event is fired by `HDTicketComment.after_insert()`. However, there is no `log_ticket_activity()` call in `new_internal_note()` (nor in `new_comment()` for that matter). Internal note creation is not tracked in the ticket's activity history, so there's no audit trail showing when an internal note was added or by whom (beyond the comment record itself).

**Expected:** `log_ticket_activity(self.name, "added an internal note")` in `new_internal_note()`.
**Actual:** No activity log entry.

### P3-04: `HDTicketComment.after_insert()` broadcasts to ALL room subscribers including customers
**Severity: P3 (Low)**
**File:** `hd_ticket_comment.py` line 26-37

When an internal note is inserted, `after_insert()` fires `helpdesk:ticket-comment` event to the ticket's room. This event is broadcast to **all subscribers** of the room, including any customer who might have the ticket page open. While the customer won't see the note content (it's filtered by `get_comments()`), the realtime event itself leaks the fact that a comment/note was added. A customer seeing a "new comment" notification but not seeing any new comment would be confusing at best and a minor information leak at worst.

**Expected:** `after_insert()` should check `is_internal` and either suppress the event or use an agent-only channel.
**Actual:** All comment events broadcast indiscriminately.

### P3-05: No XSS sanitization specific to internal notes
**Severity: P3 (Low)**
**File:** `InternalNote.vue` line 65-78

The `TextEditor` component renders `_content` which comes from the database. While Frappe's TextEditor likely handles basic sanitization, there's no explicit mention of HTML sanitization for internal note content. If a malicious agent injects script tags via the API (bypassing the frontend editor), other agents viewing the note could be affected.

**Expected:** Explicit sanitization on content display, or documented reliance on Frappe's built-in sanitization.
**Actual:** Implicit reliance on TextEditor component sanitization.

---

## Test Execution Results

| Test | Result |
|------|--------|
| `test_internal_note_hidden_from_non_agent_get_comments` | PASS |
| `test_no_comments_returned_to_non_agent_without_doctype_perm` | PASS |
| `test_internal_note_visible_to_agent_get_comments` | PASS |
| `test_internal_note_hidden_in_get_one_for_non_agent` | PASS |
| `test_internal_note_visible_in_get_one_for_agent` | PASS |
| `test_internal_note_content_not_leaked_to_non_agent` | PASS |
| `test_non_agent_cannot_create_internal_note` | PASS |
| `test_agent_can_create_internal_note` | PASS |
| `test_new_comment_is_not_internal` | PASS |
| `test_new_internal_note_sets_is_internal_flag` | PASS |

**10/10 tests passing.**

---

## Console Errors

Browser testing via Playwright MCP was not available. Console errors could not be captured. API-level testing showed no server errors.

---

## Summary

| Severity | Count | Items |
|----------|-------|-------|
| P0 (Critical) | 0 | -- |
| P1 (High) | 2 | Delete/update lack server-side ownership checks |
| P2 (Medium) | 6 | Layout hack, shortcut docs, merge/split tests, mutable defaults, code duplication |
| P3 (Low) | 5 | Typing leak, localStorage exposure, no activity log, broadcast leak, XSS reliance |

### Acceptance Criteria Summary

| AC | Status | Notes |
|----|--------|-------|
| AC-1: Visually distinct editor | PASS | Amber styling, lock icon, rich text, attachments all present. P2-01 (width=0 hack) is a concern. |
| AC-2: Not visible to customers | PASS | Server-side filtering confirmed. No email triggering. |
| AC-3: Server-side permission check | PASS | 10/10 tests pass. `is_agent()` guard on creation and retrieval. |

**Overall Assessment:** The core security boundary (NFR-SE-01) is well-implemented -- internal notes are properly filtered from non-agent API responses, and creation is agent-gated. However, there are notable gaps in **ownership enforcement** (P1-01, P1-02) where any agent can delete/modify any other agent's notes, a **broken layout hack** (P2-01), and several missing test/documentation items. The P1 issues should be addressed before this feature is considered production-ready.
