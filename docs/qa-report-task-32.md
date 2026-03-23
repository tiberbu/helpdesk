# QA Report: Task #32 — Story 3.3: Embeddable Chat Widget

**QA Date**: 2026-03-23
**QA Depth**: 1/1 (final)
**Story File**: `_bmad-output/implementation-artifacts/story-32-story-3-3-embeddable-chat-widget.md`
**Overall Result**: FAIL (2 P0 issues found)

---

## Acceptance Criteria Results

### AC1: Single script tag with data attributes loads widget, async, <50KB gzipped
**Result**: FAIL (P0 — wrong API path)

- **Bundle size**: PASS — 43.12 KB gzipped (under 50KB limit)
- **Script tag loading**: PASS — `main.js` registers `<frappe-helpdesk-chat>` custom element and auto-injects it
- **Data attributes**: PASS — reads `data-site`, `data-brand`, `data-position` from script tag
- **API paths**: FAIL — All 6 API calls in the widget use `helpdesk.helpdesk.api.chat.*` but the correct Frappe module path is `helpdesk.api.chat.*`. The directory `helpdesk/helpdesk/api/` does not exist in the deployed bench app. Every API call will return a 404/ValidationError when the widget runs in production.

**Evidence**:
```
# Wrong path (used by widget):
curl "http://helpdesk.localhost:8004/api/method/helpdesk.helpdesk.api.chat.get_availability"
→ "No module named 'helpdesk.helpdesk.api'"

# Correct path:
curl "http://helpdesk.localhost:8004/api/method/helpdesk.api.chat.get_availability"
→ {"message": {"available": true}}
```

**Affected files**:
- `widget/src/Widget.vue:78` — `helpdesk.helpdesk.api.chat.get_availability`
- `widget/src/components/BrandingHeader.vue:31` — `helpdesk.helpdesk.api.chat.get_widget_config`
- `widget/src/components/PreChatForm.vue:48` — `helpdesk.helpdesk.api.chat.create_session`
- `widget/src/components/OfflineForm.vue:50` — `helpdesk.helpdesk.api.chat.create_offline_ticket`
- `widget/src/components/ChatView.vue:46` — `helpdesk.helpdesk.api.chat.get_messages`
- `widget/src/components/ChatView.vue:112` — `helpdesk.helpdesk.api.chat.send_message`

### AC2: Agents available shows "Support is online" with pre-chat form (name, email, subject)
**Result**: PASS (code-level, contingent on AC1 fix)

- `get_availability` API returns `{"available": true}` when active agents exist
- Widget.vue correctly routes to PreChatForm when `isOnline === true`
- PreChatForm.vue has Name, Email, Subject fields with validation
- Form validation works (required checks, email regex)

### AC3: No agents shows "Leave a message" form creating email ticket
**Result**: FAIL (P0 — permission error for Guest)

- OfflineForm.vue correctly shows "Leave a message" title and has Name, Email, Subject, Message fields
- **Backend bug**: `create_offline_ticket` fails for Guest users with PermissionError. The function doesn't elevate to Administrator before calling the channel normalizer (unlike `_create_ticket_for_session` which does).

**Evidence**:
```
curl -X POST "http://helpdesk.localhost:8004/api/method/helpdesk.api.chat.create_offline_ticket" \
  -H "Content-Type: application/json" -H "X-Frappe-CSRF-Token: test" \
  -d '{"name":"Test","email":"test@example.com","subject":"Help","message":"Please help"}'
→ {"exc_type": "PermissionError", ... "No permission for HD Ticket"}
```

**Root cause**: `helpdesk/api/chat.py:438-452` — the normalizer runs as Guest. Compare with `_create_ticket_for_session` (line 511-540) which correctly does `frappe.set_user("Administrator")`.

### AC4: Shadow DOM isolation prevents host CSS conflicts
**Result**: PASS

- `main.js` correctly uses `this.attachShadow({ mode: 'open' })` to create Shadow DOM
- Styles are injected into shadow root via `?inline` CSS import
- `styles.css` uses `:host` selector for isolation
- `all: initial` resets inherited styles

### AC5: Mobile full-screen instead of 400px desktop panel
**Result**: PASS

- `Widget.vue:59-61`: `isMobile` is set when `window.innerWidth < 768`
- `styles.css:93-100`: `.hd-panel--mobile` uses `width: 100vw; height: 100vh`
- `styles.css:79-86`: `.hd-panel--desktop` uses `width: 400px; height: 600px`
- Window resize listener is properly added/removed

---

## Test Results

- **Widget unit tests**: 42/42 passing (5 test files)
- **Build**: Succeeds, 43.12 KB gzipped output

---

## Additional Findings

### P2: v-html XSS risk in ChatView.vue
- **File**: `widget/src/components/ChatView.vue:170`
- `v-html="msg.content"` renders message HTML directly. Backend sanitizes via `_sanitize()` but Socket.IO messages bypass this if they come from a compromised source.
- **Mitigation**: Backend sanitization exists. Low risk for MVP.

### P2: applyPrimaryColor won't work inside Shadow DOM
- **File**: `widget/src/components/BrandingHeader.vue:55`
- `document.querySelector('#hd-widget-root')` cannot find elements inside Shadow DOM from the document context.
- **Impact**: CSS variable `--hd-primary` won't propagate to child components. Header still works via inline style.

### P3: document.currentScript is null for async scripts
- **File**: `widget/src/main.js:38`
- `document.currentScript` is always `null` inside `connectedCallback` (runs after script load). Fallback `document.querySelector('script[data-site]')` works, so no functional impact.

---

## Summary of Issues

| # | Severity | Issue | File(s) |
|---|----------|-------|---------|
| 1 | **P0** | All widget API paths use wrong module `helpdesk.helpdesk.api.chat` instead of `helpdesk.api.chat` — widget completely broken | 6 files in `widget/src/` |
| 2 | **P0** | `create_offline_ticket` fails for Guest — missing permission elevation | `helpdesk/api/chat.py:438-452` |
| 3 | P2 | `v-html` XSS risk in ChatView | `widget/src/components/ChatView.vue:170` |
| 4 | P2 | `applyPrimaryColor` DOM query fails in Shadow DOM | `widget/src/components/BrandingHeader.vue:55` |
| 5 | P3 | `document.currentScript` null in async context (mitigated by fallback) | `widget/src/main.js:38` |
