import { useRef, useState } from 'react'
import { synthesizeSpeech } from '../services/api'

export default function BilingualOutput({ english, telugu }) {
  return (
    <div className="panel flex flex-col gap-3 p-4">
      <p className="eyebrow">Bilingual output</p>
      <div className="grid grid-cols-1 gap-3 sm:grid-cols-2">
        <LanguageCard label="English" lang="en" text={english} accent="teal" />
        <LanguageCard label="తెలుగు" lang="te" text={telugu} accent="amber" />
      </div>
    </div>
  )
}

function LanguageCard({ label, lang, text, accent }) {
  const [status, setStatus] = useState('idle') // idle | loading | playing | error
  const audioRef = useRef(null)

  const accentClasses =
    accent === 'teal'
      ? 'border-teal-400/20 text-teal-400'
      : 'border-amber-500/20 text-amber-400'

  async function handleSpeak() {
    if (!text) return
    if (status === 'loading') return

    setStatus('loading')
    try {
      const data = await synthesizeSpeech(text, lang)
      const src = data.audio_url || (data.audio_base64 ? `data:audio/mp3;base64,${data.audio_base64}` : null)
      if (!src) throw new Error('No audio returned')

      if (!audioRef.current) audioRef.current = new Audio()
      audioRef.current.src = src
      audioRef.current.onended = () => setStatus('idle')
      audioRef.current.onerror = () => setStatus('error')
      await audioRef.current.play()
      setStatus('playing')
    } catch {
      setStatus('error')
    }
  }

  return (
    <div className={`flex flex-col gap-3 rounded-xl border bg-ink-950/50 p-4 ${accentClasses}`}>
      <div className="flex items-center justify-between">
        <span className="font-mono text-[11px] uppercase tracking-wide">{label}</span>
        <button
          onClick={handleSpeak}
          disabled={!text}
          className="flex items-center gap-1.5 rounded-full bg-white/5 px-3 py-1 font-mono text-[11px] text-paper transition-colors hover:bg-white/10 disabled:opacity-30"
        >
          <SpeakerIcon status={status} />
          {status === 'loading' ? 'Loading…' : status === 'playing' ? 'Playing' : 'Speak'}
        </button>
      </div>
      <p className="min-h-[2.5rem] font-body text-lg leading-snug text-paper">
        {text || <span className="text-slate-500">Awaiting a completed sentence…</span>}
      </p>
      {status === 'error' && (
        <p className="font-mono text-[11px] text-coral">Couldn't play audio — check the /api/speak endpoint.</p>
      )}
    </div>
  )
}

function SpeakerIcon({ status }) {
  return (
    <svg
      width="12"
      height="12"
      viewBox="0 0 24 24"
      fill="none"
      className={status === 'playing' ? 'animate-pulse' : ''}
    >
      <path
        d="M4 9v6h4l5 5V4L8 9H4z"
        fill="currentColor"
      />
      <path
        d="M17.5 8.5a5 5 0 010 7"
        stroke="currentColor"
        strokeWidth="1.6"
        strokeLinecap="round"
      />
    </svg>
  )
}
