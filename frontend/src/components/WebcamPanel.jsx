import { useEffect, useRef, useState } from 'react'
import { connectSocket, disconnectSocket, getSocket, sendFrame } from '../services/socket'

const FRAME_INTERVAL_MS = 130 // ~7-8 fps upload; backend still infers at 24+ fps on its buffer

export default function WebcamPanel({
  sessionId,
  mode,
  onPrediction,
  isFrozen,
  connectionStatus,
  setConnectionStatus
}) {
  const videoRef = useRef(null)
  const canvasRef = useRef(null)
  const streamRef = useRef(null)
  const intervalRef = useRef(null)
  const modeRef = useRef(mode)
  const [cameraError, setCameraError] = useState(null)
  const [currentLetter, setCurrentLetter] = useState(null)
  const [confidence, setConfidence] = useState(0)
  const [fps, setFps] = useState(0)

  // Keep modeRef in sync so the frame loop never reads a stale mode
  useEffect(() => {
    modeRef.current = mode
  }, [mode])

  // Camera lifecycle
  useEffect(() => {
    async function startCamera() {
      try {
        const stream = await navigator.mediaDevices.getUserMedia({
          video: { width: 640, height: 480, facingMode: 'user' },
          audio: false
        })
        streamRef.current = stream
        if (videoRef.current) {
          videoRef.current.srcObject = stream
        }
      } catch (err) {
        setCameraError('Camera access was denied or is unavailable. Check your browser permissions.')
      }
    }
    startCamera()
    return () => {
      streamRef.current?.getTracks().forEach((t) => t.stop())
    }
  }, [])

  // Socket lifecycle
  useEffect(() => {
    setConnectionStatus('connecting')
    const socket = connectSocket()

    socket.on('connect', () => setConnectionStatus('connected'))
    socket.on('disconnect', () => setConnectionStatus('disconnected'))
    socket.on('connect_error', () => setConnectionStatus('error'))

    socket.on('prediction', (payload) => {
      const { label, confidence: conf, fps: serverFps } = payload || {}
      if (label === undefined) return
      setCurrentLetter(label)
      setConfidence(conf ?? 0)
      if (serverFps) setFps(serverFps)
      onPrediction?.({ label, confidence: conf ?? 0 })
    })

    return () => {
      socket.off('connect')
      socket.off('disconnect')
      socket.off('connect_error')
      socket.off('prediction')
      disconnectSocket()
    }
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, [])

  // Frame streaming loop
  useEffect(() => {
    if (isFrozen) {
      clearInterval(intervalRef.current)
      return
    }
    intervalRef.current = setInterval(() => {
      const video = videoRef.current
      const canvas = canvasRef.current
      if (!video || !canvas || video.readyState < 2) return

      const ctx = canvas.getContext('2d')
      canvas.width = video.videoWidth || 640
      canvas.height = video.videoHeight || 480
      ctx.drawImage(video, 0, 0, canvas.width, canvas.height)

      const dataUrl = canvas.toDataURL('image/jpeg', 0.6)
      console.log("Sending mode:", mode)
      sendFrame(dataUrl, sessionId, mode)
    }, FRAME_INTERVAL_MS)

    return () => clearInterval(intervalRef.current)
  }, [isFrozen, sessionId])

  return (
    <div className="panel p-4 sm:p-5 flex flex-col gap-4">
      <div className="flex items-center justify-between">
        <div>
          <p className="eyebrow">Live Capture</p>
          <h2 className="font-display text-lg font-semibold text-paper">Webcam feed</h2>
        </div>
        <StatusBadge status={connectionStatus} />
      </div>

      <div className="relative aspect-[4/3] w-full overflow-hidden rounded-xl bg-ink-950 border border-white/5">
        {cameraError ? (
          <div className="absolute inset-0 flex items-center justify-center p-6 text-center text-sm text-slate-400">
            {cameraError}
          </div>
        ) : (
          <video
            ref={videoRef}
            autoPlay
            playsInline
            muted
            className="h-full w-full object-cover scale-x-[-1]"
          />
        )}
        <canvas ref={canvasRef} className="hidden" />

        {/* Recording indicator */}
        {!isFrozen && !cameraError && (
          <div className="absolute left-3 top-3 flex items-center gap-2 rounded-full bg-ink-950/70 px-3 py-1 backdrop-blur-sm">
            <span className="relative flex h-2 w-2">
              <span className="absolute inline-flex h-full w-full rounded-full bg-coral opacity-75 animate-ping" />
              <span className="relative inline-flex h-2 w-2 rounded-full bg-coral" />
            </span>
            <span className="font-mono text-[11px] tracking-wide text-slate-300">LIVE</span>
          </div>
        )}

        {isFrozen && (
          <div className="absolute left-3 top-3 rounded-full bg-ink-950/70 px-3 py-1 font-mono text-[11px] tracking-wide text-amber-400 backdrop-blur-sm">
            FROZEN
          </div>
        )}

        {/* FPS readout */}
        <div className="absolute right-3 top-3 rounded-full bg-ink-950/70 px-3 py-1 font-mono text-[11px] text-slate-400 backdrop-blur-sm">
          {fps ? `${fps.toFixed(0)} fps` : '-- fps'}
        </div>

        {/* Big letter overlay, the "signature" reveal moment */}
        <div className="absolute bottom-0 left-0 right-0 flex items-end justify-between gap-4 bg-gradient-to-t from-ink-950/90 to-transparent p-4">
          <div className="flex items-end gap-3">
            <span
              key={currentLetter}
              className="font-display text-5xl font-bold leading-none text-paper animate-rise"
            >
              {currentLetter ?? '—'}
            </span>
            <span className="mb-1 font-mono text-xs text-slate-400">predicted sign</span>
          </div>
          <ConfidenceMeter value={confidence} />
        </div>
      </div>
    </div>
  )
}

function ConfidenceMeter({ value }) {
  const pct = Math.round(value || 0)
  const color = pct >= 80 ? 'bg-teal-400' : pct >= 50 ? 'bg-amber-500' : 'bg-coral'
  return (
    <div className="mb-1 flex w-28 flex-col gap-1">
      <div className="flex justify-between font-mono text-[11px] text-slate-400">
        <span>confidence</span>
        <span>{pct}%</span>
      </div>
      <div className="h-1.5 w-full overflow-hidden rounded-full bg-white/10">
        <div
          className={`h-full rounded-full transition-all duration-200 ${color}`}
          style={{ width: `${pct}%` }}
        />
      </div>
    </div>
  )
}

function StatusBadge({ status }) {
  const config = {
    connected: { text: 'Connected', dot: 'bg-teal-400' },
    connecting: { text: 'Connecting…', dot: 'bg-amber-500 animate-pulse' },
    disconnected: { text: 'Disconnected', dot: 'bg-slate-500' },
    error: { text: 'Connection error', dot: 'bg-coral' }
  }[status] || { text: 'Unknown', dot: 'bg-slate-500' }

  return (
    <div className="flex items-center gap-2 rounded-full border border-white/5 bg-ink-800 px-3 py-1">
      <span className={`h-1.5 w-1.5 rounded-full ${config.dot}`} />
      <span className="font-mono text-[11px] text-slate-300">{config.text}</span>
    </div>
  )
}