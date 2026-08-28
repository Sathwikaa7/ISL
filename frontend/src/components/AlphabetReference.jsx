import { useEffect, useRef, useState } from 'react'

const SIGNS = ['0', '1', '2', '3', '4', '5', '6', '7', '8', '9', ...'ABCDEFGHIJKLMNOPQRSTUVWXYZ']

const API_BASE = import.meta.env.VITE_API_URL || 'http://127.0.0.1:5000'

export default function AlphabetReference({ onSelect }) {
  const [previewSign, setPreviewSign] = useState(null)
  const previewTimerRef = useRef(null)

  useEffect(() => {
    function handleKeyDown(event) {
      if (event.key === 'Escape') setPreviewSign(null)
    }
    window.addEventListener('keydown', handleKeyDown)
    return () => {
      window.removeEventListener('keydown', handleKeyDown)
      clearTimeout(previewTimerRef.current)
    }
  }, [])

  const imageUrl = (sign) => `${API_BASE}/api/alphabet-reference/${encodeURIComponent(sign)}`

  return (
    <>
      <section className="panel p-4 sm:p-5">
      <div className="mb-3 flex items-baseline justify-between gap-3">
        <div>
          <p className="eyebrow">Reference</p>
          <h2 className="font-display text-base font-semibold text-paper">Alphabet & digits</h2>
        </div>
        <span className="font-mono text-[10px] text-slate-500">36 signs</span>
      </div>

      <div className="grid max-h-[27rem] grid-cols-4 gap-2 overflow-y-auto pr-1 sm:grid-cols-6">
        {SIGNS.map((sign) => (
          <button
            key={sign}
            type="button"
            onClick={() => {
              // Delay the preview briefly so a double-click can be treated
              // as an add action without opening the modal first.
              clearTimeout(previewTimerRef.current)
              previewTimerRef.current = setTimeout(() => setPreviewSign(sign), 220)
            }}
            onDoubleClick={() => {
              clearTimeout(previewTimerRef.current)
              onSelect(sign)
            }}
            className="group overflow-hidden rounded-lg border border-white/10 bg-ink-950/60 text-left transition hover:-translate-y-0.5 hover:border-teal-400/70 hover:bg-ink-900 focus-visible:outline focus-visible:outline-2 focus-visible:outline-offset-2 focus-visible:outline-teal-300"
            aria-label={`Preview sign ${sign}; double-click to add it to the letter buffer`}
            title={`Click to preview ${sign}; double-click to add it`}
          >
            <img
              src={imageUrl(sign)}
              alt={`Reference sign ${sign}`}
              className="aspect-square w-full object-cover"
              loading="lazy"
            />
            <span className="block py-1 text-center font-mono text-xs font-semibold text-teal-300">{sign}</span>
          </button>
        ))}
      </div>
      </section>

      {previewSign && (
        <div
          className="fixed inset-0 z-50 flex items-center justify-center bg-ink-950/90 p-4 backdrop-blur-sm"
          role="dialog"
          aria-modal="true"
          aria-label={`Preview sign ${previewSign}`}
          onClick={() => setPreviewSign(null)}
        >
          <div
            className="relative w-full max-w-lg overflow-hidden rounded-2xl border border-teal-300/40 bg-ink-900 p-4 shadow-2xl"
            onClick={(event) => event.stopPropagation()}
          >
            <button
              type="button"
              onClick={() => setPreviewSign(null)}
              className="absolute right-6 top-6 rounded-md bg-ink-950/80 px-3 py-1.5 font-mono text-xs text-slate-200 hover:bg-ink-800"
              aria-label="Close preview"
            >
              Close
            </button>
            <img src={imageUrl(previewSign)} alt={`Reference sign ${previewSign}`} className="aspect-square w-full rounded-xl object-contain" />
            <div className="mt-3 flex items-center justify-between gap-3">
              <span className="font-display text-3xl font-bold text-teal-300">{previewSign}</span>
              <button
                type="button"
                onClick={() => {
                  onSelect(previewSign)
                  setPreviewSign(null)
                }}
                className="rounded-lg bg-teal-400 px-4 py-2 text-sm font-semibold text-ink-950 hover:bg-teal-300"
              >
                Add to buffer
              </button>
            </div>
            <p className="mt-2 text-xs text-slate-400">Double-click a reference tile to add it directly, or use this button.</p>
          </div>
        </div>
      )}
    </>
  )
}
