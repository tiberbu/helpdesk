/**
 * ChatView.vue integration tests.
 *
 * Tests:
 *  1. Fetches message history on mount and renders messages
 *  2. Renders customer and agent messages with correct CSS classes
 *  3. Sends a message via the API on button click
 *  4. Sends a message via Enter key (not Shift+Enter)
 *  5. Shift+Enter does not submit
 *  6. Typing indicator appears on 'typing' socket event
 *  7. Hides input area and shows "Chat ended" on session_ended event
 *  8. Emits 'session-ended' when "Start new chat" is clicked
 */
import { describe, it, expect, vi, beforeEach } from 'vitest'
import { mount, flushPromises } from '@vue/test-utils'
import ChatView from '../components/ChatView.vue'

// ── Socket.js mock ──────────────────────────────────────────────────────────
const mockOn = vi.fn()
const mockEmit = vi.fn()
const mockSocket = { on: mockOn, emit: mockEmit, connected: false, disconnect: vi.fn() }

vi.mock('../socket.js', () => ({
  connectSocket: vi.fn(() => Promise.resolve(mockSocket)),
  on: vi.fn((socket, event, handler) => {
    socket.on(event, handler)
  }),
  disconnectSocket: vi.fn(),
}))

beforeEach(() => {
  vi.clearAllMocks()
})

// Helper to mount ChatView with default fetch returning empty message list
function mountChatView(fetchImpl = null) {
  global.fetch = fetchImpl ?? vi.fn().mockResolvedValue({
    ok: true,
    json: async () => ({ message: [] }),
  })
  return mount(ChatView, {
    props: { sessionId: 'sess-123', token: 'tok-abc', siteUrl: '' },
  })
}

describe('ChatView.vue', () => {
  // ── 1. Renders message history fetched on mount ──────────────────────────
  it('renders messages fetched on mount', async () => {
    global.fetch = vi.fn().mockResolvedValue({
      ok: true,
      json: async () => ({
        message: [
          { message_id: 'm1', sender_type: 'agent', content: 'Hello!', sent_at: '2024-01-01T10:00:00Z' },
          { message_id: 'm2', sender_type: 'customer', content: 'Hi there', sent_at: '2024-01-01T10:01:00Z' },
        ],
      }),
    })
    const wrapper = mount(ChatView, { props: { sessionId: 'sess-1', token: 'tok', siteUrl: '' } })
    await flushPromises()
    const msgs = wrapper.findAll('.hd-message')
    expect(msgs).toHaveLength(2)
    expect(msgs[0].classes()).toContain('hd-message--agent')
    expect(msgs[1].classes()).toContain('hd-message--customer')
  })

  // ── 2. Send message via button click ────────────────────────────────────
  it('sends message via send button click', async () => {
    global.fetch = vi.fn()
      .mockResolvedValueOnce({ ok: true, json: async () => ({ message: [] }) }) // history
      .mockResolvedValueOnce({ ok: true, json: async () => ({ message: { message_id: 'new-1' } }) }) // send
    const wrapper = mount(ChatView, { props: { sessionId: 'sess-2', token: 'tok', siteUrl: '' } })
    await flushPromises()
    await wrapper.find('.hd-chat__input').setValue('Test message')
    await wrapper.find('.hd-chat__send').trigger('click')
    await flushPromises()
    // 3 calls: history + typing_stop (Story 3.4) + send_message
    expect(global.fetch).toHaveBeenCalledTimes(3)
    // Check optimistic message was rendered
    const msgs = wrapper.findAll('.hd-message')
    expect(msgs.length).toBeGreaterThanOrEqual(1)
    expect(msgs[msgs.length - 1].find('.hd-message__bubble').html()).toContain('Test message')
  })

  // ── 3. Enter key submits message, Shift+Enter does not ──────────────────
  it('submits on Enter but not Shift+Enter', async () => {
    global.fetch = vi.fn()
      .mockResolvedValueOnce({ ok: true, json: async () => ({ message: [] }) })
      .mockResolvedValue({ ok: true, json: async () => ({ message: { message_id: 'x' } }) })
    const wrapper = mount(ChatView, { props: { sessionId: 'sess-3', token: 'tok', siteUrl: '' } })
    await flushPromises()
    const input = wrapper.find('.hd-chat__input')
    await input.setValue('Hello')
    // Shift+Enter should NOT submit (but does emit typing_start — Story 3.4)
    await input.trigger('keydown', { key: 'Enter', shiftKey: true })
    await flushPromises()
    expect(global.fetch).toHaveBeenCalledTimes(2) // history + typing_start

    // Regular Enter should submit (typing_stop + send_message)
    await input.trigger('keydown', { key: 'Enter', shiftKey: false })
    await flushPromises()
    expect(global.fetch).toHaveBeenCalledTimes(4) // + typing_stop + send_message
  })

  // ── 4. Send button disabled when input is empty ─────────────────────────
  it('disables send button when input is empty', async () => {
    const wrapper = mountChatView()
    await flushPromises()
    expect(wrapper.find('.hd-chat__send').attributes('disabled')).toBeDefined()
  })

  // ── 5. Session ended via socket event — hides input, shows banner ─────────
  it('shows chat-ended banner and hides input on session_ended socket event', async () => {
    const wrapper = mountChatView()
    await flushPromises()
    // Find the session_ended handler registered via mockOn
    const sessionEndedCall = mockOn.mock.calls.find(([event]) => event === 'session_ended')
    expect(sessionEndedCall).toBeDefined()
    const handler = sessionEndedCall[1]
    handler({ session_id: 'sess-123' })
    await flushPromises()
    expect(wrapper.find('.hd-ended').exists()).toBe(true)
    expect(wrapper.find('.hd-chat__footer').exists()).toBe(false)
  })

  // ── 6. Emits 'session-ended' when "Start new chat" clicked ───────────────
  it('emits session-ended when start new chat button clicked', async () => {
    const wrapper = mountChatView()
    await flushPromises()
    // Trigger session end
    const sessionEndedCall = mockOn.mock.calls.find(([event]) => event === 'session_ended')
    sessionEndedCall[1]({ session_id: 'sess-123' })
    await flushPromises()
    await wrapper.find('.hd-ended button').trigger('click')
    expect(wrapper.emitted('session-ended')).toBeTruthy()
  })

  // ── 7. Typing indicator appears on typing_start event from agent ─────────
  it('shows typing indicator when typing_start event received', async () => {
    const wrapper = mountChatView()
    await flushPromises()
    const typingCall = mockOn.mock.calls.find(([event]) => event === 'typing_start')
    expect(typingCall).toBeDefined()
    typingCall[1]({ session_id: 'sess-123', sender_name: 'Alice' })
    await flushPromises()
    expect(wrapper.find('.hd-typing-indicator').exists()).toBe(true)
  })

  // ── 8. Ignores typing events from different sessions ─────────────────────
  it('ignores typing events from different session', async () => {
    const wrapper = mountChatView()
    await flushPromises()
    const typingCall = mockOn.mock.calls.find(([event]) => event === 'typing_start')
    typingCall[1]({ session_id: 'other-sess', sender_name: 'Bob' })
    await flushPromises()
    expect(wrapper.find('.hd-typing-indicator').exists()).toBe(false)
  })
})
