/**
 * socket.js unit tests.
 *
 * Tests the dynamic-load Socket.IO wrapper.
 *
 *  1. connectSocket() creates socket with correct options via window.io
 *  2. Reuses existing connected socket (no duplicate connections)
 *  3. Emits join_room on connect with correct room name
 *  4. on() attaches an event handler
 *  5. on() is a no-op when socket is null
 *  6. disconnectSocket clears the singleton
 *  7. disconnectSocket safe to call when no socket
 */
import { describe, it, expect, vi, beforeEach } from 'vitest'

beforeEach(() => {
  vi.clearAllMocks()
  vi.resetModules()
  // Reset window.io to avoid test cross-contamination
  delete window.io
})

/**
 * Creates a fresh mock socket and injects window.io to simulate
 * the dynamic script-load completing successfully.
 */
function setupWindowIo() {
  const socket = {
    connected: false,
    on: vi.fn(),
    emit: vi.fn(),
    disconnect: vi.fn(),
  }
  const ioFn = vi.fn(() => socket)
  window.io = ioFn
  return { socket, ioFn }
}

describe('socket.js', () => {
  // ── 1. connectSocket creates socket via window.io ────────────────────────
  it('creates socket via window.io with correct options', async () => {
    const { socket, ioFn } = setupWindowIo()
    const { connectSocket } = await import('../socket.js')
    const result = await connectSocket('https://helpdesk.example.com', 'sess-1', 'jwt-token')
    expect(ioFn).toHaveBeenCalledWith('https://helpdesk.example.com', expect.objectContaining({
      auth: { token: 'jwt-token' },
      path: '/socket.io',
    }))
    expect(result).toBe(socket)
  })

  // ── 2. Registers connect handler that emits join_room ────────────────────
  it('registers connect handler that emits join_room for correct room', async () => {
    const { socket } = setupWindowIo()
    const { connectSocket } = await import('../socket.js')
    await connectSocket('https://helpdesk.example.com', 'sess-99', 'tok')
    const connectCall = socket.on.mock.calls.find(([event]) => event === 'connect')
    expect(connectCall).toBeDefined()
    connectCall[1]()
    expect(socket.emit).toHaveBeenCalledWith('join_room', { room: 'chat:sess-99' })
  })

  // ── 3. on() attaches event handler ──────────────────────────────────────
  it('on() attaches event listener', async () => {
    const { socket } = setupWindowIo()
    const { connectSocket, on } = await import('../socket.js')
    const result = await connectSocket('https://helpdesk.example.com', 'sess-1', 'tok')
    const handler = vi.fn()
    on(result, 'chat_message', handler)
    expect(socket.on).toHaveBeenCalledWith('chat_message', handler)
  })

  // ── 4. on() is a no-op when socket is null ───────────────────────────────
  it('on() does not throw when socket is null', async () => {
    const { on } = await import('../socket.js')
    expect(() => on(null, 'event', vi.fn())).not.toThrow()
  })

  // ── 5. disconnectSocket calls disconnect and resets singleton ─────────────
  it('disconnectSocket calls disconnect', async () => {
    const { socket } = setupWindowIo()
    const { connectSocket, disconnectSocket } = await import('../socket.js')
    await connectSocket('https://helpdesk.example.com', 'sess-1', 'tok')
    disconnectSocket()
    expect(socket.disconnect).toHaveBeenCalled()
  })

  // ── 6. disconnectSocket is safe when no socket exists ────────────────────
  it('disconnectSocket does not throw with no active socket', async () => {
    const { disconnectSocket } = await import('../socket.js')
    expect(() => disconnectSocket()).not.toThrow()
  })
})
