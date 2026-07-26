import { io } from 'socket.io-client'

// Real-time channel: the browser streams webcam frames to Flask
// (Flask-SocketIO), and the server streams back gesture predictions after
// running MediaPipe + MobileNetV3 on each frame.
//
// Client -> server events:
//   'frame'        { image: <base64 jpeg>, session_id }
//
// Server -> client events:
//   'prediction'   { label, confidence, fps }
//   'connect' / 'disconnect'
//
// Adjust event names/payloads to match your Flask-SocketIO handlers.

let socket = null

export function getSocket() {
  if (!socket) {
    socket = io('/', {
      path: '/socket.io',
      transports: ['polling', 'websocket'],
      autoConnect: false
    })
  }
  return socket
}

export function connectSocket() {
  const s = getSocket()
  if (!s.connected) s.connect()
  return s
}

export function disconnectSocket() {
  if (socket && socket.connected) socket.disconnect()
}

export function sendFrame(base64Image, sessionId, mode) {
  const s = getSocket()

  if (s.connected) {
    s.emit("frame", {
      image: base64Image,
      session_id: sessionId,
      mode
    })
  }
}
