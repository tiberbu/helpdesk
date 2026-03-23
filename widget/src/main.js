/**
 * Helpdesk Chat Widget — entry point.
 *
 * Registers a <frappe-helpdesk-chat> custom element that mounts the Vue widget
 * into a Shadow DOM, providing full CSS isolation from the host page (AC #5).
 *
 * Embedding (AC #1):
 *   <script src=".../helpdesk-chat.iife.js"
 *           data-site="https://helpdesk.example.com"
 *           data-brand="acme"
 *           data-position="bottom-right"
 *           async></script>
 */
import { createApp } from 'vue'
import Widget from './Widget.vue'
import widgetStyles from './styles.css?inline'

class HelpdeskChatElement extends HTMLElement {
  connectedCallback() {
    // Prevent double-mount if element is moved in DOM
    if (this._mounted) return
    this._mounted = true

    // Create Shadow DOM root (AC #5 — isolation)
    const shadow = this.attachShadow({ mode: 'open' })

    // Inject widget CSS into shadow root so it cannot leak to the host page
    const styleEl = document.createElement('style')
    styleEl.textContent = widgetStyles
    shadow.appendChild(styleEl)

    // App container inside the shadow root
    const container = document.createElement('div')
    container.id = 'hd-widget-root'
    shadow.appendChild(container)

    // Read configuration from the embedding <script> tag (AC #1, #2, #7)
    const scriptTag =
      document.currentScript || document.querySelector('script[data-site]')

    const props = {
      siteUrl: scriptTag?.dataset?.site || window.location.origin,
      brand: scriptTag?.dataset?.brand || 'default',
      position: scriptTag?.dataset?.position || 'bottom-right',
    }

    const app = createApp(Widget, props)
    app.mount(container)
  }
}

// Register custom element
if (!customElements.get('frappe-helpdesk-chat')) {
  customElements.define('frappe-helpdesk-chat', HelpdeskChatElement)
}

// Auto-inject the custom element into <body> (AC #1 — single script tag loads widget)
if (typeof document !== 'undefined') {
  const existing = document.querySelector('frappe-helpdesk-chat')
  if (!existing) {
    const el = document.createElement('frappe-helpdesk-chat')
    if (document.body) {
      document.body.appendChild(el)
    } else {
      document.addEventListener('DOMContentLoaded', () => {
        document.body.appendChild(el)
      })
    }
  }
}
