/**
 * ChatRealtime.test.js — Story 3.4: Real-Time Chat Communication
 *
 * Covers AC #2 (message status), AC #3 (typing indicator), AC #4 (localStorage).
 *
 * Tests:
 *  1. Typing indicator shows on typing_start event; auto-clears after 10s
 *  2. Typing indicator clears immediately on typing_stop event
 *  3. Message status advances: sent → delivered → read via message_status events
 *  4. message_delivered API called when chat_message received from non-customer
 *  5. mark_messages_read called when chat_message received from non-customer
 *  6. localStorage session restored — ChatView shown without PreChatForm
 *  7. TypingIndicator component renders dots and sender name
 *  8. StatusIcon renders correct aria-label for each status
 *  9. typing_start emitted via REST API on keydown (debounced)
 * 10. typing_stop emitted on message send
 */
import { describe, it, expect, vi, beforeEach, afterEach } from 'vitest'
import { mount, flushPromises } from '@vue/test-utils'
import ChatView from '../components/ChatView.vue'
import TypingIndicator from '../components/TypingIndicator.vue'
import StatusIcon from '../components/StatusIcon.vue'
import Widget from '../Widget.vue'

// ── Socket.js mock ──────────────────────────────────────────────────────────
const mockEmit = vi.fn()
const mockOn = vi.fn()
const mockSocket = { on: mockOn, emit: mockEmit, connected: false, disconnect: vi.fn() }

vi.mock('../socket.js', () => ({
  connectSocket: vi.fn(() => Promise.resolve(mockSocket)),
  on: vi.fn((socket, event, handler) => { socket.on(event, handler) }),
  disconnectSocket: vi.fn(),
}))

// ── Fake timers for auto-clear tests ────────────────────────────────────────
beforeEach(() => {
  vi.useFakeTimers()
  vi.clearAllMocks()
})
afterEach(() => {
  vi.useRealTimers()
})

// ── Helpers ──────────────────────────────────────────────────────────────────

function mountChatView(fetchMock = null) {
  global.fetch = fetchMock ?? vi.fn().mockResolvedValue({
    ok: true,
    json: async () => ({ message: [] }),
  })
  return mount(ChatView, {
    props: { sessionId: 'sess-rt', token: 'tok-rt', siteUrl: '' },
  })
}

/** Fire the named socket event on the mock socket. */
function fireSocketEvent(event, data) {
  const handlers = mockOn.mock.calls
    .filter(([e]) => e === event)
    .map(([, h]) => h)
  handlers.forEach((h) => h(data))
}

// ═══════════════════════════════════════════════════════════════════════════

describe('AC #3: Typing indicator — auto-clear after 10s', () => {
  it('shows typing indicator on typing_start and auto-clears after 10000ms', async () => {
    const wrapper = mountChatView()
    await flushPromises()

    // Fire typing_start
    fireSocketEvent('typing_start', { session_id: 'sess-rt', sender_name: 'Alice' })
    await flushPromises()

    expect(wrapper.find('.hd-typing-indicator').exists()).toBe(true)
    expect(wrapper.find('.hd-typing-indicator__label').text()).toContain('Alice')

    // Advance 10 seconds — indicator must auto-clear (AC #3)
    vi.advanceTimersByTime(10_000)
    await flushPromises()

    expect(wrapper.find('.hd-typing-indicator').exists()).toBe(false)
  })

  it('resets the 10s timer when a new typing_start arrives', async () => {
    const wrapper = mountChatView()
    await flushPromises()

    fireSocketEvent('typing_start', { session_id: 'sess-rt', sender_name: 'Bob' })
    await flushPromises()

    vi.advanceTimersByTime(6_000)
    // Second typing_start arrives at 6s — resets the 10s window
    fireSocketEvent('typing_start', { session_id: 'sess-rt', sender_name: 'Bob' })
    await flushPromises()

    vi.advanceTimersByTime(5_000) // Total: 11s — but only 5s since last start
    await flushPromises()
    expect(wrapper.find('.hd-typing-indicator').exists()).toBe(true)

    vi.advanceTimersByTime(5_000) // 10s since last start — should clear now
    await flushPromises()
    expect(wrapper.find('.hd-typing-indicator').exists()).toBe(false)
  })

  it('ignores typing_start from a different session', async () => {
    const wrapper = mountChatView()
    await flushPromises()

    fireSocketEvent('typing_start', { session_id: 'other-sess', sender_name: 'Eve' })
    await flushPromises()

    expect(wrapper.find('.hd-typing-indicator').exists()).toBe(false)
  })
})

describe('AC #3: Typing indicator — clears on typing_stop', () => {
  it('clears immediately on typing_stop event', async () => {
    const wrapper = mountChatView()
    await flushPromises()

    fireSocketEvent('typing_start', { session_id: 'sess-rt', sender_name: 'Carol' })
    await flushPromises()
    expect(wrapper.find('.hd-typing-indicator').exists()).toBe(true)

    fireSocketEvent('typing_stop', { session_id: 'sess-rt' })
    await flushPromises()
    expect(wrapper.find('.hd-typing-indicator').exists()).toBe(false)
  })

  it('ignores typing_stop from a different session', async () => {
    const wrapper = mountChatView()
    await flushPromises()

    fireSocketEvent('typing_start', { session_id: 'sess-rt', sender_name: 'Dave' })
    await flushPromises()
    expect(wrapper.find('.hd-typing-indicator').exists()).toBe(true)

    fireSocketEvent('typing_stop', { session_id: 'other-sess' })
    await flushPromises()
    // Still visible — wrong session
    expect(wrapper.find('.hd-typing-indicator').exists()).toBe(true)
  })
})

describe('AC #2: Message status icons', () => {
  it('shows status icon after optimistic message send (status=sent)', async () => {
    global.fetch = vi.fn()
      .mockResolvedValueOnce({ ok: true, json: async () => ({ message: [] }) }) // history
      .mockResolvedValue({
        ok: true,
        json: async () => ({ message: { message_id: 'real-msg-1', status: 'sent' } }),
      })

    const wrapper = mountChatView(global.fetch)
    await flushPromises()

    await wrapper.find('.hd-chat__input').setValue('Hello')
    await wrapper.find('.hd-chat__send').trigger('click')
    await flushPromises()

    // Customer message should have StatusIcon rendered
    const customerMsgs = wrapper.findAll('.hd-message--customer')
    expect(customerMsgs.length).toBeGreaterThanOrEqual(1)
    // StatusIcon should be present in the message meta
    expect(wrapper.find('.hd-status-icon').exists()).toBe(true)
  })

  it('advances status from sent → delivered → read via message_status events', async () => {
    global.fetch = vi.fn()
      .mockResolvedValueOnce({ ok: true, json: async () => ({ message: [] }) })
      .mockResolvedValue({
        ok: true,
        json: async () => ({ message: { message_id: 'track-msg-1', status: 'sent' } }),
      })

    const wrapper = mountChatView(global.fetch)
    await flushPromises()

    await wrapper.find('.hd-chat__input').setValue('Track me')
    await wrapper.find('.hd-chat__send').trigger('click')
    await flushPromises()

    // Initial status: sent
    expect(wrapper.find('.hd-status-icon--sent').exists()).toBe(true)

    // Simulate delivered event
    fireSocketEvent('message_status', { session_id: 'sess-rt', message_id: 'track-msg-1', status: 'delivered' })
    await flushPromises()
    expect(wrapper.find('.hd-status-icon--delivered').exists()).toBe(true)

    // Simulate read event
    fireSocketEvent('message_status', { session_id: 'sess-rt', message_id: 'track-msg-1', status: 'read' })
    await flushPromises()
    expect(wrapper.find('.hd-status-icon--read').exists()).toBe(true)
  })

  it('status does not revert from read back to delivered', async () => {
    global.fetch = vi.fn()
      .mockResolvedValueOnce({ ok: true, json: async () => ({ message: [] }) })
      .mockResolvedValue({
        ok: true,
        json: async () => ({ message: { message_id: 'rev-msg', status: 'sent' } }),
      })

    const wrapper = mountChatView(global.fetch)
    await flushPromises()

    await wrapper.find('.hd-chat__input').setValue('No revert')
    await wrapper.find('.hd-chat__send').trigger('click')
    await flushPromises()

    fireSocketEvent('message_status', { session_id: 'sess-rt', message_id: 'rev-msg', status: 'read' })
    await flushPromises()
    expect(wrapper.find('.hd-status-icon--read').exists()).toBe(true)

    // Attempt to revert to delivered — should be ignored
    fireSocketEvent('message_status', { session_id: 'sess-rt', message_id: 'rev-msg', status: 'delivered' })
    await flushPromises()
    expect(wrapper.find('.hd-status-icon--read').exists()).toBe(true)
    expect(wrapper.find('.hd-status-icon--delivered').exists()).toBe(false)
  })
})

describe('AC #2: message_delivered called when receiving agent message', () => {
  it('calls message_delivered API for non-customer chat_message events', async () => {
    const fetchMock = vi.fn()
      .mockResolvedValueOnce({ ok: true, json: async () => ({ message: [] }) }) // history
      .mockResolvedValue({ ok: true, json: async () => ({ message: { ok: true } }) })

    const wrapper = mountChatView(fetchMock)
    await flushPromises()

    fireSocketEvent('chat_message', {
      session_id: 'sess-rt',
      message_id: 'agent-msg-1',
      sender_type: 'agent',
      content: 'Hi there',
      sent_at: new Date().toISOString(),
    })
    await flushPromises()

    // fetch should have been called for message_delivered and mark_messages_read
    const calls = fetchMock.mock.calls.map(([url]) => url)
    expect(calls.some((u) => u.includes('message_delivered'))).toBe(true)
    expect(calls.some((u) => u.includes('mark_messages_read'))).toBe(true)
  })
})

describe('AC #3: typing_start emitted on keydown (debounced)', () => {
  it('calls typing_start API on keydown', async () => {
    const fetchMock = vi.fn()
      .mockResolvedValueOnce({ ok: true, json: async () => ({ message: [] }) })
      .mockResolvedValue({ ok: true, json: async () => ({}) })

    const wrapper = mountChatView(fetchMock)
    await flushPromises()

    const input = wrapper.find('.hd-chat__input')
    await input.trigger('keydown', { key: 'a' })
    await flushPromises()

    const typingStartCalls = fetchMock.mock.calls.filter(([url]) => url.includes('typing_start'))
    expect(typingStartCalls.length).toBeGreaterThanOrEqual(1)
  })

  it('debounces typing_start — emits only once within 2s window', async () => {
    const fetchMock = vi.fn()
      .mockResolvedValueOnce({ ok: true, json: async () => ({ message: [] }) })
      .mockResolvedValue({ ok: true, json: async () => ({}) })

    const wrapper = mountChatView(fetchMock)
    await flushPromises()

    const input = wrapper.find('.hd-chat__input')
    // Rapid keystrokes
    await input.trigger('keydown', { key: 'a' })
    await input.trigger('keydown', { key: 'b' })
    await input.trigger('keydown', { key: 'c' })
    await flushPromises()

    const typingStartCalls = fetchMock.mock.calls.filter(([url]) => url.includes('typing_start'))
    // Only 1 call within the debounce window
    expect(typingStartCalls.length).toBe(1)
  })
})

describe('AC #3: typing_stop emitted on message send', () => {
  it('calls typing_stop API when a message is sent', async () => {
    const fetchMock = vi.fn()
      .mockResolvedValueOnce({ ok: true, json: async () => ({ message: [] }) })
      .mockResolvedValue({
        ok: true,
        json: async () => ({ message: { message_id: 'stop-test', status: 'sent' } }),
      })

    const wrapper = mountChatView(fetchMock)
    await flushPromises()

    await wrapper.find('.hd-chat__input').setValue('Send me')
    await wrapper.find('.hd-chat__send').trigger('click')
    await flushPromises()

    const typingStopCalls = fetchMock.mock.calls.filter(([url]) => url.includes('typing_stop'))
    expect(typingStopCalls.length).toBeGreaterThanOrEqual(1)
  })
})

describe('AC #4: localStorage session persistence', () => {
  it('restores session and renders ChatView when localStorage has active session', async () => {
    const session = { session_id: 'stored-sess', token: 'stored-tok', status: 'active' }
    vi.stubGlobal('localStorage', {
      getItem: vi.fn((key) => key === 'hd_chat_session' ? JSON.stringify(session) : null),
      setItem: vi.fn(),
      removeItem: vi.fn(),
    })

    global.fetch = vi.fn()
      .mockResolvedValueOnce({ ok: true, json: async () => ({ available: true }) }) // availability
      .mockResolvedValue({ ok: true, json: async () => ({ message: [] }) })

    const wrapper = mount(Widget, {
      props: { siteUrl: '', brand: 'default', position: 'bottom-right' },
    })
    await flushPromises()

    // Manually open the panel (simulate clicking the FAB)
    await wrapper.find('.hd-fab').trigger('click')
    await flushPromises()

    // ChatView should be shown (not PreChatForm) because session was restored
    expect(wrapper.findComponent({ name: 'ChatView' }).exists() ||
           wrapper.find('.hd-chat').exists()).toBe(true)

    vi.unstubAllGlobals()
  })

  it('shows PreChatForm when localStorage session status is ended', async () => {
    const session = { session_id: 'old-sess', token: 'old-tok', status: 'ended' }
    vi.stubGlobal('localStorage', {
      getItem: vi.fn((key) => key === 'hd_chat_session' ? JSON.stringify(session) : null),
      setItem: vi.fn(),
      removeItem: vi.fn(),
    })

    global.fetch = vi.fn().mockResolvedValue({
      ok: true,
      json: async () => ({ message: { available: true } }),
    })

    const wrapper = mount(Widget, {
      props: { siteUrl: '', brand: 'default', position: 'bottom-right' },
    })
    await flushPromises()

    await wrapper.find('.hd-fab').trigger('click')
    await flushPromises()

    // PreChatForm should be shown (session ended)
    expect(wrapper.findComponent({ name: 'PreChatForm' }).exists() ||
           wrapper.find('.hd-pre-chat').exists()).toBe(true)

    vi.unstubAllGlobals()
  })
})

// ═══════════════════════════════════════════════════════════════════════════
// Component unit tests
// ═══════════════════════════════════════════════════════════════════════════

describe('TypingIndicator component', () => {
  it('renders animated dots when visible=true', () => {
    const wrapper = mount(TypingIndicator, {
      props: { senderName: 'Aria', visible: true },
    })
    expect(wrapper.find('.hd-typing-indicator').exists()).toBe(true)
    expect(wrapper.findAll('.hd-typing-indicator__dot')).toHaveLength(3)
    expect(wrapper.find('.hd-typing-indicator__label').text()).toContain('Aria')
  })

  it('is hidden when visible=false', () => {
    const wrapper = mount(TypingIndicator, {
      props: { senderName: 'Bob', visible: false },
    })
    expect(wrapper.find('.hd-typing-indicator').exists()).toBe(false)
  })

  it('has role=status and aria-live=polite for accessibility (NFR-U-04)', () => {
    const wrapper = mount(TypingIndicator, {
      props: { senderName: 'Test', visible: true },
    })
    const el = wrapper.find('.hd-typing-indicator')
    expect(el.attributes('role')).toBe('status')
    expect(el.attributes('aria-live')).toBe('polite')
  })
})

describe('StatusIcon component', () => {
  it('renders sent icon with aria-label="Sent"', () => {
    const wrapper = mount(StatusIcon, { props: { status: 'sent' } })
    expect(wrapper.find('.hd-status-icon--sent').exists()).toBe(true)
    expect(wrapper.find('[aria-label="Sent"]').exists()).toBe(true)
  })

  it('renders delivered icon with aria-label="Delivered"', () => {
    const wrapper = mount(StatusIcon, { props: { status: 'delivered' } })
    expect(wrapper.find('.hd-status-icon--delivered').exists()).toBe(true)
    expect(wrapper.find('[aria-label="Delivered"]').exists()).toBe(true)
  })

  it('renders read icon with aria-label="Read"', () => {
    const wrapper = mount(StatusIcon, { props: { status: 'read' } })
    expect(wrapper.find('.hd-status-icon--read').exists()).toBe(true)
    expect(wrapper.find('[aria-label="Read"]').exists()).toBe(true)
  })
})
