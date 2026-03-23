/**
 * socket.js — Socket.IO client wrapper for the chat widget.
 *
 * Loads socket.io-client lazily from the Frappe server at runtime
 * (the server always exposes it at <siteUrl>/socket.io/socket.io.js).
 * This keeps the widget bundle under 50 KB gzipped (AC #1).
 *
 * Public API:
 *   connectSocket(siteUrl, sessionId, token) → Promise<Socket>
 *   on(socket, event, handler)
 *   disconnectSocket()
 */

let _socket = null
let _ioPromise = null

/**
 * Load socket.io client library from the Frappe server.
 * Caches the promise so the script is only injected once.
 *
 * @param {string} siteUrl
 * @returns {Promise<Function>} Resolves to the global `io` function
 */
function loadSocketIO(siteUrl) {
  if (_ioPromise) return _ioPromise

  _ioPromise = new Promise((resolve, reject) => {
    // If already on the same origin the library may already be loaded
    if (typeof window !== 'undefined' && window.io && typeof window.io === 'function') {
      return resolve(window.io)
    }

    const script = document.createElement('script')
    // Frappe's socket.io server exposes its client bundle at this path
    script.src = `${siteUrl}/socket.io/socket.io.js`
    script.async = true
    script.onload = () => {
      if (window.io) resolve(window.io)
      else reject(new Error('socket.io loaded but window.io not found'))
    }
    script.onerror = () => reject(new Error(`Failed to load socket.io from ${script.src}`))
    document.head.appendChild(script)
  })

  return _ioPromise
}

/**
 * Connect to the Frappe Socket.IO server and join the chat room.
 *
 * @param {string} siteUrl    - Base URL of the Frappe site
 * @param {string} sessionId  - HD Chat Session session_id
 * @param {string} token      - JWT returned by create_session
 * @returns {Promise<Socket>} Resolves to the connected socket instance
 */
export async function connectSocket(siteUrl, sessionId, token) {
  // Reuse existing connected socket
  if (_socket && _socket.connected) return _socket

  // Disconnect any stale socket before reconnecting
  if (_socket) {
    _socket.disconnect()
    _socket = null
  }

  const io = await loadSocketIO(siteUrl)

  _socket = io(siteUrl, {
    auth: { token },
    transports: ['websocket', 'polling'],
    path: '/socket.io',
    reconnectionAttempts: 5,
    reconnectionDelay: 2000,
  })

  _socket.on('connect', () => {
    // Join the session-specific room (AR-07: room naming chat:{session_id})
    _socket.emit('join_room', { room: `chat:${sessionId}` })
  })

  return _socket
}

/**
 * Convenience helper for binding event handlers.
 *
 * @param {Socket} socket
 * @param {string} event
 * @param {Function} handler
 */
export function on(socket, event, handler) {
  if (socket) socket.on(event, handler)
}

/**
 * Disconnect and clear the socket singleton.
 */
export function disconnectSocket() {
  if (_socket) {
    _socket.disconnect()
    _socket = null
  }
  _ioPromise = null
}
