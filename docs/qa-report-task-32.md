# QA Report: Task #32 — Story 3.3: Embeddable Chat Widget

**QA Date**: 2026-03-24
**QA Depth**: 1/1 (final)
**Story File**: `_bmad-output/implementation-artifacts/story-32-story-3-3-embeddable-chat-widget.md`
**Overall Result**: FAIL (1 P0 blocker + 1 P1)

---

## Acceptance Criteria Results

### AC1: Single script tag with data attributes loads widget, async, <50KB gzipped
**Result**: FAIL (P0 — bundle crashes on load)

- **Bundle size**: PASS — 127,777 bytes raw, **42.9 KB gzipped** (under 50KB limit)
- **Script tag structure**: PASS — `main.js` registers `<frappe-helpdesk-chat>` custom element, auto-injects it, reads `data-site`/`data-brand`/`data-position`
- **Bundle execution**: FAIL — Widget JS crashes immediately with `ReferenceError: process is not defined`
- **Root cause**: `widget/vite.config.js` does not include `define: { 'process.env.NODE_ENV': JSON.stringify('production') }`. Vue 3 runtime references `process.env.NODE_ENV` for dev/prod mode detection. In browser IIFE context, `process` is undefined. 4 occurrences of `process.env` found in the built bundle.
- **Previous P0s (wrong API paths, Guest permission) from prior QA cycle were fixed** — API paths now use correct `helpdesk.api.chat.*`, and `create_offline_ticket` properly elevates to Administrator.

**Browser evidence**: Loaded `http://help.frappe.local/assets/helpdesk/widget-test.html` in Playwright. Console shows:
```
ReferenceError: process is not defined
    at helpdesk-chat.iife.js:28:748
```
No FAB button or panel rendered. Screenshot: `task-32-widget-test-page-no-fab.png`

### AC2: Agents available shows "Support is online" with pre-chat form (name, email, subject)
**Result**: BLOCKED (by P0) — code review PASS

- **API verification (curl)**: `get_availability` returns `{"available": true}` — PASS
- **API verification (curl)**: `get_widget_config` returns correct defaults — PASS
- **API verification (curl)**: `create_session` returns `{session_id, token, status: "waiting"}` — PASS
- **Code review**: Widget.vue correctly routes to PreChatForm when `isOnline === true`. PreChatForm has Name, Email, Subject fields with validation, loading spinner, error banner. Calls `create_session` which returns JWT.

### AC3: No agents shows "Leave a message" form creating email ticket
**Result**: BLOCKED (by P0) — code review PASS

- **API verification (curl)**: `create_offline_ticket` returns `{"ticket_id": 140}` as Guest — PASS (previously was P0, now fixed)
- **Code review**: OfflineForm.vue has Name, Email, Subject, Message fields with validation. Calls `create_offline_ticket` API (now correctly elevates to Administrator). Shows confirmation with submitted email on success.

### AC4: Shadow DOM isolation prevents host CSS conflicts
**Result**: BLOCKED (by P0) — code review PASS

- **Code review**: `main.js` uses `attachShadow({ mode: 'open' })`. CSS injected into shadow root via `?inline` import. `:host` selector with `all: initial` provides full isolation.
- **Test page**: Created aggressive CSS overrides (red buttons, pink inputs) to validate — cannot verify visually due to P0 crash.

### AC5: Mobile full-screen instead of 400px desktop panel
**Result**: BLOCKED (by P0) — code review PASS

- **Code review**: `Widget.vue:59-61` checks `window.innerWidth < 768`. Desktop: `hd-panel--desktop` (400px x 600px). Mobile: `hd-panel--mobile` (100vw x 100vh). Resize listener properly added/removed.

---

## Browser Testing (Playwright MCP)

### Agent-Side Live Chat Page
- **URL**: `http://help.frappe.local/helpdesk/chat`
- **Result**: PASS — Page loads correctly with "Live Chat" heading, agent status "Online", active chats count, and "Select a chat to get started" empty state.
- **Screenshot**: `task-32-live-chat-agent-page.png`

### Widget Test Page
- **URL**: `http://help.frappe.local/assets/helpdesk/widget-test.html`
- **Result**: FAIL — Widget script crashes on load with `process is not defined`. No custom element, no FAB button, no chat panel rendered.
- **Screenshot**: `task-32-widget-test-page-no-fab.png`

---

## Test Results

- **Widget unit tests**: **58 passed, 4 failed** (6 test files)
  - socket.test.js (6/6 pass), OfflineForm.test.js (8/8 pass), ChatRealtime.test.js (20/20 pass)
  - PreChatForm.test.js: 7/8 pass, 1 fail — `emits session-created` assertion fails
  - ChatView.test.js: 7/8 pass, 1 fail — `emits session-ended` assertion fails (`.hd-ended button` not found)
  - Widget.test.js: 10/12 pass, 2 fail — `handleSessionCreated`/`handleSessionEnded` not exposed on `wrapper.vm` (Vue 3 `<script setup>` issue)
- **Note**: The 4 test failures are caused by Story 3.4 changes that modified component internals without updating the original Story 3.3 tests.
- **Note**: Unit tests run in jsdom which defines `process.env.NODE_ENV`, so they cannot catch the production bundle P0 issue.

---

## Console Errors

| Error | Severity | Source |
|-------|----------|--------|
| `ReferenceError: process is not defined` | P0 | `helpdesk-chat.iife.js:28:748` |
| `ERR_CONNECTION_REFUSED /socket.io/` (repeated) | Pre-existing | Socket.IO server not running in test env |

---

## Issues Found

| # | Severity | Issue | File(s) |
|---|----------|-------|---------|
| 1 | **P0** | Widget bundle crashes — `process.env.NODE_ENV` not replaced by Vite in IIFE library build | `widget/vite.config.js` |
| 2 | **P1** | 4 unit tests fail due to Story 3.4 changes breaking Story 3.3 test assumptions | `widget/src/__tests__/Widget.test.js`, `PreChatForm.test.js`, `ChatView.test.js` |
| 3 | P2 | `applyPrimaryColor` DOM query fails inside Shadow DOM | `widget/src/components/BrandingHeader.vue:55` |
| 4 | P2 | StatusIcon.vue/TypingIndicator.vue CSS classes have no styles in `styles.css` | `widget/src/styles.css` |
| 5 | P3 | `document.currentScript` null in async context (mitigated by fallback) | `widget/src/main.js:38` |

---

## Backend API Verification (curl)

| Endpoint | Status | Evidence |
|----------|--------|----------|
| `get_availability` | PASS | `{"available": true}` |
| `get_widget_config` | PASS | Returns defaults (primary_color, logo, greeting, name) |
| `create_session` | PASS | Returns `{session_id, token, status: "waiting"}` |
| `send_message` | PASS | Returns `{message_id, sent_at}` with valid JWT |
| `get_messages` | PASS | Returns message array for session |
| `create_offline_ticket` | PASS | Returns `{ticket_id: 140}` as Guest (fixed from prior QA) |

---

## Screenshots

- `task-32-widget-test-page-no-fab.png` — Widget test page showing no FAB (P0 crash)
- `task-32-live-chat-agent-page.png` — Agent-side Live Chat page working correctly
