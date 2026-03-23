/**
 * Widget.vue integration tests.
 *
 * Tests:
 *  1. FAB button renders at the correct position
 *  2. Clicking FAB toggles the panel open/closed
 *  3. PreChatForm shown when agents are online
 *  4. OfflineForm shown when no agents are available
 *  5. Mobile: panel uses full-screen class; Desktop: panel uses 400px class
 *  6. Session is restored from localStorage on mount
 *  7. BrandingHeader renders inside the open panel
 */
import { describe, it, expect, vi, beforeEach } from 'vitest'
import { mount, flushPromises } from '@vue/test-utils'
import Widget from '../Widget.vue'

// ── Socket.js mock ──────────────────────────────────────────────────────────
vi.mock('../socket.js', () => ({
  connectSocket: vi.fn(() => Promise.resolve({ on: vi.fn(), connected: false })),
  on: vi.fn(),
  disconnectSocket: vi.fn(),
}))

// ── Fetch helpers ───────────────────────────────────────────────────────────
function mockFetch(available) {
  global.fetch = vi.fn().mockResolvedValue({
    ok: true,
    json: async () => ({ message: { available } }),
  })
}

beforeEach(() => {
  vi.restoreAllMocks()
  localStorage.clear()
})

describe('Widget.vue', () => {
  // ── 1. FAB renders ───────────────────────────────────────────────────────
  it('renders the FAB button', async () => {
    mockFetch(false)
    const wrapper = mount(Widget, { props: { siteUrl: '', brand: 'default', position: 'bottom-right' } })
    await flushPromises()
    const fab = wrapper.find('.hd-fab')
    expect(fab.exists()).toBe(true)
  })

  // ── 2. FAB left position ─────────────────────────────────────────────────
  it('applies hd-fab--left class when position is bottom-left', async () => {
    mockFetch(false)
    const wrapper = mount(Widget, { props: { siteUrl: '', brand: 'default', position: 'bottom-left' } })
    await flushPromises()
    expect(wrapper.find('.hd-fab--left').exists()).toBe(true)
  })

  // ── 3. Panel hidden initially, shown on FAB click ────────────────────────
  it('toggles the panel on FAB click', async () => {
    mockFetch(false)
    const wrapper = mount(Widget, { props: { siteUrl: '', brand: 'default', position: 'bottom-right' } })
    await flushPromises()
    expect(wrapper.find('.hd-panel').exists()).toBe(false)
    await wrapper.find('.hd-fab').trigger('click')
    expect(wrapper.find('.hd-panel').exists()).toBe(true)
    await wrapper.find('.hd-fab').trigger('click')
    expect(wrapper.find('.hd-panel').exists()).toBe(false)
  })

  // ── 4. PreChatForm shown when agents online ──────────────────────────────
  it('shows PreChatForm when agents are online', async () => {
    mockFetch(true)
    const wrapper = mount(Widget, { props: { siteUrl: '', brand: 'default', position: 'bottom-right' } })
    await flushPromises()
    await wrapper.find('.hd-fab').trigger('click')
    // PreChatForm has hd-form__title "Start a conversation"
    const title = wrapper.find('.hd-form__title')
    expect(title.exists()).toBe(true)
    expect(title.text()).toContain('Start a conversation')
  })

  // ── 5. OfflineForm shown when no agents ──────────────────────────────────
  it('shows OfflineForm when no agents are available', async () => {
    mockFetch(false)
    const wrapper = mount(Widget, { props: { siteUrl: '', brand: 'default', position: 'bottom-right' } })
    await flushPromises()
    await wrapper.find('.hd-fab').trigger('click')
    // OfflineForm has hd-form__title "Leave a message"
    const title = wrapper.find('.hd-form__title')
    expect(title.exists()).toBe(true)
    expect(title.text()).toContain('Leave a message')
  })

  // ── 6. Mobile: full-screen panel ─────────────────────────────────────────
  it('uses mobile full-screen class when viewport is narrow', async () => {
    mockFetch(false)
    Object.defineProperty(window, 'innerWidth', { writable: true, configurable: true, value: 375 })
    const wrapper = mount(Widget, { props: { siteUrl: '', brand: 'default', position: 'bottom-right' } })
    await flushPromises()
    // Trigger resize to detect mobile
    window.dispatchEvent(new Event('resize'))
    await flushPromises()
    await wrapper.find('.hd-fab').trigger('click')
    expect(wrapper.find('.hd-panel--mobile').exists()).toBe(true)
    // Restore
    Object.defineProperty(window, 'innerWidth', { writable: true, configurable: true, value: 1024 })
  })

  // ── 7. Desktop: 400px panel ───────────────────────────────────────────────
  it('uses desktop class when viewport is wide', async () => {
    mockFetch(false)
    Object.defineProperty(window, 'innerWidth', { writable: true, configurable: true, value: 1200 })
    const wrapper = mount(Widget, { props: { siteUrl: '', brand: 'default', position: 'bottom-right' } })
    await flushPromises()
    await wrapper.find('.hd-fab').trigger('click')
    expect(wrapper.find('.hd-panel--desktop').exists()).toBe(true)
  })

  // ── 8. Session restored from localStorage → ChatView shown ───────────────
  it('restores session from localStorage and shows ChatView', async () => {
    mockFetch(true)
    localStorage.setItem('hd_chat_session', JSON.stringify({
      session_id: 'sess-123',
      token: 'tok-abc',
      status: 'active',
    }))
    // Mock second fetch call for message history (get_messages)
    global.fetch = vi.fn()
      .mockResolvedValueOnce({ ok: true, json: async () => ({ message: { available: true } }) })
      .mockResolvedValueOnce({ ok: true, json: async () => ({ message: [] }) })

    const wrapper = mount(Widget, { props: { siteUrl: '', brand: 'default', position: 'bottom-right' } })
    await flushPromises()
    await wrapper.find('.hd-fab').trigger('click')
    // ChatView renders .hd-chat
    expect(wrapper.find('.hd-chat').exists()).toBe(true)
  })

  // ── 9. Session with status=ended not restored ─────────────────────────────
  it('does not restore ended sessions', async () => {
    mockFetch(false)
    localStorage.setItem('hd_chat_session', JSON.stringify({
      session_id: 'sess-old',
      token: 'tok-old',
      status: 'ended',
    }))
    const wrapper = mount(Widget, { props: { siteUrl: '', brand: 'default', position: 'bottom-right' } })
    await flushPromises()
    await wrapper.find('.hd-fab').trigger('click')
    expect(wrapper.find('.hd-chat').exists()).toBe(false)
    expect(wrapper.find('.hd-form__title').text()).toContain('Leave a message')
  })

  // ── 10. handleSessionCreated saves session to localStorage ───────────────
  it('persists session to localStorage when session is created', async () => {
    mockFetch(true)
    const wrapper = mount(Widget, { props: { siteUrl: '', brand: 'default', position: 'bottom-right' } })
    await flushPromises()
    // Simulate PreChatForm emitting session-created
    await wrapper.vm.handleSessionCreated({ session_id: 'new-sess', token: 'new-tok' })
    const stored = JSON.parse(localStorage.getItem('hd_chat_session'))
    expect(stored.session_id).toBe('new-sess')
    expect(stored.token).toBe('new-tok')
    expect(stored.status).toBe('active')
  })

  // ── 11. handleSessionEnded clears localStorage ────────────────────────────
  it('clears localStorage when session ends', async () => {
    mockFetch(true)
    localStorage.setItem('hd_chat_session', JSON.stringify({ session_id: 'x', token: 'y', status: 'active' }))
    const wrapper = mount(Widget, { props: { siteUrl: '', brand: 'default', position: 'bottom-right' } })
    await flushPromises()
    await wrapper.vm.handleSessionEnded()
    expect(localStorage.getItem('hd_chat_session')).toBeNull()
  })

  // ── 12. fetch error → isOnline stays false ─────────────────────────────────
  it('defaults to offline when availability fetch fails', async () => {
    global.fetch = vi.fn().mockRejectedValue(new Error('network'))
    const wrapper = mount(Widget, { props: { siteUrl: '', brand: 'default', position: 'bottom-right' } })
    await flushPromises()
    await wrapper.find('.hd-fab').trigger('click')
    expect(wrapper.find('.hd-form__title').text()).toContain('Leave a message')
  })
})
