# Story 3.3: Embeddable Chat Widget

Status: ready-for-dev

<!-- Note: Validation is optional. Run validate-create-story for quality check before dev-story. -->

## Story

As a website visitor,
I want to open a chat widget on the company's website to get real-time support,
so that I can get help without leaving the page.

## Acceptance Criteria

1. **Single-script embedding, async load, <50KB gzipped** — A single `<script>` tag with `data-site`, `data-brand`, and `data-position` attributes loads the widget asynchronously (does not block page rendering). The total production bundle (`helpdesk-chat.iife.js` + inlined CSS) is under 50KB when gzipped (NFR-P-05, FR-LC-01, AR-08).

2. **Widget button at configured position** — After the script loads, a floating chat button appears at the position specified by `data-position` (accepts `bottom-right` or `bottom-left`). The button defaults to `bottom-right` if the attribute is omitted. The button is rendered within a Shadow DOM root to prevent host-page CSS interference.

3. **Pre-chat form when agents are online** — When the widget is opened and agents are available (i.e., `GET /api/method/helpdesk.api.chat.get_availability` returns `{"available": true}`), the `PreChatForm.vue` component is shown with three fields: **Name** (required), **Email** (required, validated format), and **Subject** (required). Submitting the form calls `POST /api/method/helpdesk.api.chat.create_session` and transitions to `ChatView.vue`.

4. **Offline form when no agents are available** — When the availability check returns `{"available": false}` (or the check fails/times out), the `OfflineForm.vue` component is shown with a "Leave a message" heading and the same Name/Email/Subject fields plus a **Message** body field. Submitting this form calls `POST /api/method/helpdesk.api.chat.create_offline_ticket` and creates an email ticket without starting a real-time session. A confirmation message is shown after submission.

5. **Shadow DOM isolation** — The widget root element (`<frappe-helpdesk-chat>`) attaches a Shadow DOM. All widget HTML, styles, and Vue components are mounted inside the shadow root. Host-page CSS does not affect widget styling, and widget CSS does not affect the host page (FR-LC-01).

6. **Responsive: full-screen on mobile, 400px panel on desktop** — On viewports ≥ 768px the open chat panel is 400px wide × 600px tall (fixed, above the floating button). On viewports < 768px the panel expands to 100vw × 100vh (full screen), covering the entire page (UX-DR-03, NFR-U-03).

7. **BrandingHeader with custom color and logo** — The `BrandingHeader.vue` component reads `data-brand` from the script tag, fetches brand config from `GET /api/method/helpdesk.api.chat.get_widget_config?brand={brand}`, and applies `primary_color` (CSS custom property `--hd-primary`) and `logo` to the header. If no brand is configured, sensible defaults are used without error.

8. **Widget state persistence across page navigation** — The widget stores `session_id` and JWT `token` in `localStorage` under the key `hd_chat_session`. On subsequent page loads the widget reads this key and, if a session is still active (`status !== "ended"`), skips the pre-chat form and reopens directly to `ChatView.vue` with message history.

9. **Integration test coverage** — A Vitest (or equivalent) test suite at `widget/src/__tests__/` tests: (a) Pre-chat form renders when availability is `true`; (b) Offline form renders when availability is `false`; (c) Shadow DOM isolation verified (no style leak); (d) Mobile vs desktop layout class applied at correct breakpoint; (e) `localStorage` session restored correctly on re-load. Tests mock `fetch` for all API calls.

## Tasks / Subtasks

- [ ] **Task 1: Create `widget/` directory structure and Vite build config** (AC: #1)
  - [ ] Create `widget/` directory at repo root (sibling to `desk/`)
  - [ ] Create `widget/src/main.js` — entry point that registers a custom element `<frappe-helpdesk-chat>` and mounts `Widget.vue` into its Shadow DOM
  - [ ] Create `widget/vite.config.js` with `lib` mode targeting `iife` format, `minify: 'terser'`, `cssCodeSplit: false`, output file `helpdesk-chat`
  - [ ] Create `widget/package.json` with `vue` and `socket.io-client` as the only non-dev dependencies; use external-free bundling (no CDN imports)
  - [ ] Add `build:widget` script to root `package.json` (or `Makefile`) that runs `vite build --config widget/vite.config.js`
  - [ ] Verify gzip size of output is <50KB (add a `check-bundle-size` script using `gzip -c` and `wc -c`, fail if >51200 bytes)

- [ ] **Task 2: Implement Shadow DOM entry point** (AC: #2, #5)
  - [ ] In `widget/src/main.js`, define a custom element class that:
    - Creates a Shadow DOM with `mode: 'open'`
    - Injects an inner `<div id="app">` inside the shadow root
    - Calls `createApp(Widget).mount(shadowRoot.querySelector('#app'))`
    - Reads `data-site`, `data-brand`, `data-position` from the `<script>` tag and passes them as props to `Widget`
  - [ ] The custom element auto-registers itself when the script loads (`customElements.define('frappe-helpdesk-chat', HelpdeskChatElement)`) and injects a `<frappe-helpdesk-chat>` node into `document.body` if not already present
  - [ ] Self-contained CSS (`widget/src/styles.css`) is injected into the shadow root via a `<style>` element (not Tailwind; hand-written or PostCSS with minimal reset)

- [ ] **Task 3: Implement `Widget.vue` root component** (AC: #2, #6, #8)
  - [ ] Create `widget/src/Widget.vue`
  - [ ] Render a floating action button (FAB) at `bottom-right` or `bottom-left` based on `position` prop, using `position: fixed` with CSS custom properties for offset
  - [ ] On FAB click, toggle an `isOpen` ref; when `true`, show the chat panel
  - [ ] On mount, call `GET /api/method/helpdesk.api.chat.get_availability` and store `isOnline` in a ref
  - [ ] On mount, read `localStorage.getItem('hd_chat_session')`, parse, and set `activeSession` ref if session is active
  - [ ] Show `PreChatForm` when `isOnline && !activeSession`; show `OfflineForm` when `!isOnline && !activeSession`; show `ChatView` when `activeSession` exists
  - [ ] Apply class `hd-panel--mobile` (100vw×100vh) or `hd-panel--desktop` (400px×600px) based on `window.innerWidth < 768`; use a `resize` event listener to react to viewport changes
  - [ ] Emit session data to `localStorage` when a session is created

- [ ] **Task 4: Implement `PreChatForm.vue`** (AC: #3)
  - [ ] Create `widget/src/components/PreChatForm.vue`
  - [ ] Three fields: Name (text, required), Email (email type, required, HTML5 validation + regex), Subject (text, required)
  - [ ] On submit, call `POST /api/method/helpdesk.api.chat.create_session` with `{name, email, subject, brand}`
  - [ ] On success, emit `session-created` event with `{session_id, token}` to parent `Widget.vue`
  - [ ] Show inline field-level validation errors (not browser popups)
  - [ ] Show a loading spinner on the submit button while the API call is in-flight
  - [ ] On API error, show a dismissible error banner ("Could not start chat. Please try again.")

- [ ] **Task 5: Implement `OfflineForm.vue`** (AC: #4)
  - [ ] Create `widget/src/components/OfflineForm.vue`
  - [ ] Four fields: Name (text, required), Email (email, required), Subject (text, required), Message (textarea, required)
  - [ ] On submit, call `POST /api/method/helpdesk.api.chat.create_offline_ticket` with `{name, email, subject, message, brand}`
  - [ ] On success, replace the form with a confirmation message: "Thanks! We'll get back to you at {email} as soon as possible."
  - [ ] On API error, show an error banner
  - [ ] If `create_offline_ticket` endpoint does not exist in Story 3.2 output, create a stub in `helpdesk/api/chat.py` that creates an HD Ticket with `source="Portal"` using the channel normalizer

- [ ] **Task 6: Implement `ChatView.vue`** (AC: #3, #8)
  - [ ] Create `widget/src/components/ChatView.vue`
  - [ ] Accepts props: `session_id`, `token`, `site_url`
  - [ ] On mount, fetch message history: `GET /api/method/helpdesk.api.chat.get_messages?session_id={session_id}&token={token}`
  - [ ] Display messages in a scrollable list: customer messages right-aligned (primary color background), agent messages left-aligned (neutral background)
  - [ ] Show sender name and time for each message
  - [ ] Include a text input and send button at the bottom; on send, call `POST /api/method/helpdesk.api.chat.send_message`
  - [ ] Initialize `socket.js` connection (see Task 7); listen for `chat_message` events on room `chat:{session_id}` and append new messages in real time
  - [ ] Show a typing indicator ("Agent is typing...") when a `typing` event is received, auto-clearing after 5 seconds of no follow-up events
  - [ ] Show a "Chat ended" banner and disable input when a `session_ended` event is received; offer "Start new chat" button that clears `localStorage` and resets to `PreChatForm`

- [ ] **Task 7: Implement `socket.js`** (AC: #3, #6 real-time dependency)
  - [ ] Create `widget/src/socket.js`
  - [ ] Export a `connectSocket(siteUrl, sessionId, token)` function that:
    - Instantiates a Socket.IO client pointing at `siteUrl` (Frappe's default Socket.IO endpoint `/`)
    - Passes `{auth: {token}}` in the handshake options for JWT authentication
    - Joins room `chat:{sessionId}` via `socket.emit('join_room', {room: 'chat:' + sessionId})`
    - Returns the socket instance
  - [ ] Export an `on(socket, event, handler)` helper for cleaner event binding in Vue components
  - [ ] Tree-shake unused Socket.IO features: import only from `socket.io-client/build/esm` (or use `socket.io-client` default and rely on Vite tree-shaking) — critical for the <50KB bundle budget

- [ ] **Task 8: Implement `BrandingHeader.vue`** (AC: #7)
  - [ ] Create `widget/src/components/BrandingHeader.vue`
  - [ ] Accepts props: `brand` (string), `site_url` (string)
  - [ ] On mount, fetch `GET {site_url}/api/method/helpdesk.api.chat.get_widget_config?brand={brand}` and extract `{primary_color, logo, greeting, name}`
  - [ ] Apply `primary_color` as `--hd-primary` CSS custom property on the shadow root host element (passed up via an emit or set directly on the container div)
  - [ ] Render brand logo (img) or fallback to brand name text if logo is missing
  - [ ] Render greeting text below brand name (default: "Hi! How can we help you today?")
  - [ ] Handle fetch errors silently — fall back to defaults (blue primary, no logo)

- [ ] **Task 9: Add `get_widget_config` and `get_availability` backend endpoints** (AC: #3, #4, #7)
  - [ ] In `helpdesk/helpdesk/api/chat.py`, add (if not already present from Story 3.2):
    - `get_widget_config(brand=None)` — `@frappe.whitelist(allow_guest=True)`: returns `{primary_color, logo, greeting, name}` from `HD Brand` (or defaults if brand is None/not found)
    - `get_availability(brand=None)` — `@frappe.whitelist(allow_guest=True)`: checks if any `HD Agent` with `availability_status="Online"` exists (optionally filtered by brand's `default_team`); returns `{"available": bool}`
    - `create_offline_ticket(name, email, subject, message, brand=None)` — `@frappe.whitelist(allow_guest=True)`: uses the `ChannelNormalizer` with a `ChannelMessage(source="portal", ...)` to create an HD Ticket; returns `{"ticket_id": ticket.name}`

- [ ] **Task 10: Write integration tests** (AC: #9)
  - [ ] Create `widget/src/__tests__/Widget.test.js` (Vitest + `@vue/test-utils`)
  - [ ] Test: online state renders `PreChatForm`; mock `fetch` to return `{"available": true}`
  - [ ] Test: offline state renders `OfflineForm`; mock `fetch` to return `{"available": false}`
  - [ ] Test: `PreChatForm` submission calls `create_session` and emits `session-created`
  - [ ] Test: `OfflineForm` submission calls `create_offline_ticket` and shows confirmation
  - [ ] Test: `Widget.vue` applies `hd-panel--mobile` class when viewport width < 768px (mock `window.innerWidth`)
  - [ ] Test: `localStorage` session is read on mount and `ChatView` is shown when session exists with `status !== "ended"`
  - [ ] Test: Shadow DOM is created (`attachShadow` was called) — mock or use jsdom shadow DOM support
  - [ ] Add `test:widget` script to `widget/package.json` running `vitest run`

## Dev Notes

### Architecture Patterns

This story implements the embeddable chat widget described in **ADR-10: Chat Widget Build Strategy** from the architecture document. The widget is a completely isolated, self-contained JavaScript bundle that communicates with the Frappe backend via standard HTTP (fetch) and Socket.IO.

**Key architectural constraints:**
- **Separate Vite build** — The widget has its own `widget/vite.config.js` producing an IIFE bundle (not ESM). This is separate from the main `desk/` Vite build (ADR-10).
- **No Tailwind CSS** — Tailwind's utility classes are too large for the <50KB budget. Use hand-written CSS or PostCSS with a minimal reset. CSS is inlined into the JS bundle via `cssCodeSplit: false`.
- **No frappe-ui** — The `frappe-ui` component library targets the agent desktop, not the widget. All UI components must be custom, lightweight Vue 3 SFCs.
- **Shadow DOM isolation** — Required by FR-LC-01. Use `element.attachShadow({mode: 'open'})`. Vue's `createApp().mount()` accepts a shadow root element directly.
- **Socket.IO client bundled** — Unlike the main desk app which uses Frappe's global Socket.IO, the widget must bundle `socket.io-client` itself. Use the ESM build and rely on Vite tree-shaking.
- **JWT in localStorage** — Chat session JWT is stored in `localStorage` per ADR-05. The widget reads/writes `hd_chat_session` key. Never store in a cookie (cookie scope issues on embedded sites).

### Bundle Size Budget (NFR-P-05)

Target: < 50KB gzipped. Approximate budget allocation:
| Component | ~Size (minified) |
|-----------|-----------------|
| Vue 3 runtime (tree-shaken) | ~22KB |
| socket.io-client (minimal ESM) | ~14KB |
| Widget components + styles | ~8KB |
| **Total minified** | ~44KB |
| **Gzipped estimate** | ~17-20KB |

Use `rollup-plugin-visualizer` or the Vite bundle analyzer during development to track size. The `check-bundle-size` CI script should fail the build if gzipped output exceeds 51200 bytes.

To minimize socket.io-client bundle size, import from `socket.io-client/build/esm/index.js` and use Vite's `optimizeDeps.exclude` if needed. Consider using the lightweight `@socket.io/component-emitter` pattern if the full client proves too large.

### Vite Widget Build Config

```javascript
// widget/vite.config.js
import { defineConfig } from 'vite'
import vue from '@vitejs/plugin-vue'
import { terser } from 'rollup-plugin-terser'

export default defineConfig({
    plugins: [vue()],
    build: {
        lib: {
            entry: 'src/main.js',
            name: 'FrappeHelpdeskChat',
            fileName: 'helpdesk-chat',
            formats: ['iife']
        },
        rollupOptions: {
            output: {
                inlineDynamicImports: true,
            }
        },
        cssCodeSplit: false,
        minify: 'terser',
        terserOptions: {
            compress: { drop_console: true },
        },
        outDir: '../helpdesk/public/js',   // Frappe serves static from public/
    }
})
```

### Shadow DOM Mount Pattern

```javascript
// widget/src/main.js
import { createApp } from 'vue'
import Widget from './Widget.vue'

class HelpdeskChatElement extends HTMLElement {
    connectedCallback() {
        const shadow = this.attachShadow({ mode: 'open' })
        const container = document.createElement('div')
        container.id = 'hd-widget-root'
        shadow.appendChild(container)

        // Inject styles into shadow root
        const style = document.createElement('style')
        style.textContent = __WIDGET_CSS__  // Replaced by Vite build
        shadow.appendChild(style)

        // Read config from the script tag
        const scriptTag = document.currentScript ||
            document.querySelector('script[data-site]')
        const props = {
            siteUrl: scriptTag?.dataset.site || window.location.origin,
            brand: scriptTag?.dataset.brand || 'default',
            position: scriptTag?.dataset.position || 'bottom-right',
        }

        const app = createApp(Widget, props)
        app.mount(container)
    }
}

customElements.define('frappe-helpdesk-chat', HelpdeskChatElement)

// Auto-inject the custom element into body
if (!document.querySelector('frappe-helpdesk-chat')) {
    document.body.appendChild(document.createElement('frappe-helpdesk-chat'))
}
```

### Availability Check API Pattern

```python
# helpdesk/helpdesk/api/chat.py (additions)

@frappe.whitelist(allow_guest=True)
def get_availability(brand=None):
    """Check if any agents are currently online."""
    filters = {"availability_status": "Online"}
    if brand:
        hd_brand = frappe.db.get_value("HD Brand", brand, "default_team")
        if hd_brand:
            filters["team"] = hd_brand
    count = frappe.db.count("HD Agent", filters=filters)
    return {"available": count > 0}


@frappe.whitelist(allow_guest=True)
def get_widget_config(brand=None):
    """Return branding config for the chat widget."""
    defaults = {
        "primary_color": "#4F46E5",
        "logo": None,
        "greeting": "Hi! How can we help you today?",
        "name": "Support",
    }
    if not brand or brand == "default":
        return defaults
    brand_doc = frappe.db.get_value(
        "HD Brand", brand,
        ["primary_color", "logo", "chat_greeting", "name"],
        as_dict=True
    )
    if not brand_doc:
        return defaults
    return {
        "primary_color": brand_doc.primary_color or defaults["primary_color"],
        "logo": brand_doc.logo,
        "greeting": brand_doc.chat_greeting or defaults["greeting"],
        "name": brand_doc.name,
    }


@frappe.whitelist(allow_guest=True)
def create_offline_ticket(name, email, subject, message, brand=None):
    """Create a ticket from an offline form submission (no live chat session)."""
    from helpdesk.helpdesk.channels.base import ChannelMessage
    from helpdesk.helpdesk.channels.normalizer import ChannelNormalizer

    channel_msg = ChannelMessage(
        source="portal",
        sender_email=email,
        sender_name=name,
        subject=subject,
        content=frappe.utils.html_sanitize(message),
        metadata={"brand": brand, "offline_form": True},
    )
    normalizer = ChannelNormalizer()
    ticket = normalizer.process(channel_msg)
    return {"ticket_id": ticket.name}
```

### Socket.js Pattern

```javascript
// widget/src/socket.js
import { io } from 'socket.io-client'

let _socket = null

export function connectSocket(siteUrl, sessionId, token) {
    if (_socket?.connected) return _socket

    _socket = io(siteUrl, {
        auth: { token },
        transports: ['websocket', 'polling'],
        path: '/socket.io',
    })

    _socket.on('connect', () => {
        _socket.emit('join_room', { room: `chat:${sessionId}` })
    })

    return _socket
}

export function disconnectSocket() {
    if (_socket) {
        _socket.disconnect()
        _socket = null
    }
}
```

### Responsive Layout CSS

```css
/* widget/src/styles.css */
:host {
    --hd-primary: #4F46E5;
    --hd-radius: 12px;
    --hd-shadow: 0 4px 24px rgba(0,0,0,0.15);
    all: initial;
    font-family: -apple-system, BlinkMacSystemFont, 'Segoe UI', sans-serif;
}

.hd-fab {
    position: fixed;
    bottom: 24px;
    right: 24px;      /* overridden for bottom-left position */
    width: 56px;
    height: 56px;
    border-radius: 50%;
    background: var(--hd-primary);
    cursor: pointer;
    z-index: 2147483647;
}

.hd-panel--desktop {
    position: fixed;
    bottom: 90px;
    right: 24px;
    width: 400px;
    height: 600px;
    border-radius: var(--hd-radius);
    box-shadow: var(--hd-shadow);
    overflow: hidden;
    z-index: 2147483646;
}

.hd-panel--mobile {
    position: fixed;
    top: 0;
    left: 0;
    width: 100vw;
    height: 100vh;
    border-radius: 0;
    z-index: 2147483647;
}
```

### Widget Directory Structure

```
widget/
├── package.json                  # vue, socket.io-client deps; build + test scripts
├── vite.config.js                # IIFE build → helpdesk/public/js/helpdesk-chat.js
├── src/
│   ├── main.js                   # Custom element definition; shadow DOM + Vue mount
│   ├── Widget.vue                # Root: FAB + panel; availability check; session routing
│   ├── socket.js                 # Socket.IO client connection + room join
│   ├── styles.css                # Self-contained CSS (no Tailwind, no frappe-ui)
│   ├── components/
│   │   ├── PreChatForm.vue       # Name/Email/Subject → create_session
│   │   ├── ChatView.vue          # Message list + input + Socket.IO events
│   │   ├── OfflineForm.vue       # Leave-a-message → create_offline_ticket
│   │   └── BrandingHeader.vue   # Logo + primary_color + greeting from brand config
│   └── __tests__/
│       ├── Widget.test.js        # Vitest integration tests (see AC #9)
│       └── setup.js              # Mock window.innerWidth, localStorage, fetch
```

### Frappe Asset Serving

The built widget bundle must be served by Frappe's static asset system:

- **Output path**: `helpdesk/public/js/helpdesk-chat.iife.js`
- Frappe automatically serves files in `{app}/public/` at `/assets/{app}/`
- Full URL: `https://{site}/assets/helpdesk/js/helpdesk-chat.iife.js`

Ensure `vite.config.js` sets `build.outDir` to `'../../helpdesk/public/js'` relative to the `widget/` directory.

### Prerequisites and Dependencies

- **Story 3.1** (Channel Abstraction Layer) — Required for `create_offline_ticket` to use the `ChannelNormalizer`. If unavailable, stub with direct `frappe.get_doc({"doctype": "HD Ticket", ...}).insert()`.
- **Story 3.2** (Chat Session Management Backend) — Required for `create_session`, `send_message`, `end_session` API endpoints. `get_availability`, `get_widget_config`, and `create_offline_ticket` are new additions added in this story.
- **`chat_enabled` feature flag** — All API endpoints added in this story should check `frappe.db.get_single_value("HD Settings", "chat_enabled")` and return an appropriate error if chat is disabled.

### Project Structure Notes

- **Widget location**: `widget/` at project root (sibling to `desk/`), as specified in ADR-10 and AR-08
- **Output location**: `helpdesk/public/js/helpdesk-chat.iife.js` — served by Frappe at `/assets/helpdesk/js/helpdesk-chat.iife.js`
- **No Tailwind, no frappe-ui**: Bundle size constraint prohibits these. Use minimal hand-written CSS.
- **Naming**: Vue components use PascalCase (`Widget.vue`, `PreChatForm.vue`) per frontend naming conventions in architecture doc
- **API module**: New endpoints (`get_availability`, `get_widget_config`, `create_offline_ticket`) are added to `helpdesk/helpdesk/api/chat.py` (the same module used by Story 3.2)
- **Test location**: `widget/src/__tests__/` using Vitest (matches Vite ecosystem; separate from Frappe Python tests)
- **No `@frappe.whitelist` import in widget code**: The widget is a client-side bundle and never imports Python modules

### Embedding Example

```html
<!-- Minimal embed — one script tag, no other dependencies required -->
<script
  src="https://helpdesk.example.com/assets/helpdesk/js/helpdesk-chat.iife.js"
  data-site="https://helpdesk.example.com"
  data-brand="acme-support"
  data-position="bottom-right"
  async
></script>
```

### References

- Architecture ADR-10: Chat Widget Build Strategy — IIFE bundle, Shadow DOM, widget directory [Source: `_bmad-output/planning-artifacts/architecture.md#ADR-10`]
- Architecture ADR-05: Chat Widget Security — JWT token in localStorage [Source: `_bmad-output/planning-artifacts/architecture.md#ADR-05`]
- Architecture ADR-08: API Design — `helpdesk/api/chat.py` endpoints [Source: `_bmad-output/planning-artifacts/architecture.md#ADR-08`]
- Architecture ADR-09: Frontend Component Organization — widget components pattern [Source: `_bmad-output/planning-artifacts/architecture.md#ADR-09`]
- Epic 3 Story 3.3 acceptance criteria [Source: `_bmad-output/planning-artifacts/epics.md#Story 3.3: Embeddable Chat Widget`]
- FR-LC-01: Embeddable chat widget with custom branding, agent availability, pre-chat form, responsive, <50KB [Source: `_bmad-output/planning-artifacts/epics.md#Functional Requirements`]
- NFR-P-05: Chat widget bundle size < 50KB gzipped [Source: `_bmad-output/planning-artifacts/epics.md#Non-Functional Requirements`]
- NFR-U-03: Chat widget fully functional on mobile browsers [Source: `_bmad-output/planning-artifacts/epics.md#Non-Functional Requirements`]
- NFR-A-02: Chat widget graceful degradation to "Leave a message" form [Source: `_bmad-output/planning-artifacts/epics.md#Non-Functional Requirements`]
- NFR-SE-02: Chat sessions authenticated via token [Source: `_bmad-output/planning-artifacts/epics.md#Non-Functional Requirements`]
- NFR-SE-06: All chat messages sanitized server-side before storage [Source: `_bmad-output/planning-artifacts/epics.md#Non-Functional Requirements`]
- UX-DR-03: Chat widget supports custom branding and responsive design (400px desktop, full-screen mobile) [Source: `_bmad-output/planning-artifacts/epics.md#UX Design Requirements`]
- AR-08: Separate Vite build for chat widget (widget/ directory) producing IIFE bundle with Shadow DOM [Source: `_bmad-output/planning-artifacts/epics.md#Additional Requirements`]
- AR-07: Socket.IO room naming convention: `chat:{session_id}` [Source: `_bmad-output/planning-artifacts/epics.md#Additional Requirements`]
- Story 3.1 (prerequisite): Channel Abstraction Layer [Source: `_bmad-output/implementation-artifacts/story-3.1-channel-abstraction-layer.md`]
- Story 3.2 (prerequisite): Chat Session Management Backend [Source: `_bmad-output/implementation-artifacts/story-3.2-chat-session-management-backend.md`]

## Dev Agent Record

### Agent Model Used

claude-opus-4-5

### Debug Log References

### Completion Notes List

### File List
