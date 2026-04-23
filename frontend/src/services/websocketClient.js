const RECONNECT_DELAY_MS = 3000
const MAX_RECONNECT_ATTEMPTS = 5

/**
 * createWebSocketClient — factory for a managed WebSocket connection.
 * Handles auth handshake, binary/text messaging, and reconnection.
 */
export function createWebSocketClient(url) {
  let ws = null
  let reconnectAttempts = 0
  let sessionToken = null
  let statusCallback = null
  let messageCallback = null
  let shouldReconnect = true

  function setStatus(status) {
    statusCallback?.(status)
  }

  function connect(token) {
    sessionToken = token
    shouldReconnect = true
    _open()
  }

  function _open() {
    setStatus('connecting')
    ws = new WebSocket(url)
    ws.binaryType = 'arraybuffer'

    ws.onopen = () => {
      reconnectAttempts = 0
      // Send auth handshake as first message
      ws.send(JSON.stringify({ session_token: sessionToken }))
      setStatus('connected')
    }

    ws.onmessage = (event) => {
      messageCallback?.(event.data)
    }

    ws.onerror = () => {
      setStatus('error')
    }

    ws.onclose = (event) => {
      if (event.code === 4001) {
        setStatus('error')
        return  // Auth failure — don't reconnect
      }
      if (event.code === 1000 || !shouldReconnect) {
        setStatus('disconnected')
        return
      }
      if (reconnectAttempts < MAX_RECONNECT_ATTEMPTS) {
        reconnectAttempts++
        setTimeout(_open, RECONNECT_DELAY_MS)
        setStatus('connecting')
      } else {
        setStatus('error')
      }
    }
  }

  function disconnect() {
    shouldReconnect = false
    ws?.close(1000)
  }

  function sendBinary(data) {
    if (ws?.readyState === WebSocket.OPEN) {
      ws.send(data)
    }
  }

  function sendText(text) {
    if (ws?.readyState === WebSocket.OPEN) {
      ws.send(text)
    }
  }

  function onStatusChange(cb) { statusCallback = cb }
  function onMessage(cb) { messageCallback = cb }

  return { connect, disconnect, sendBinary, sendText, onStatusChange, onMessage }
}
