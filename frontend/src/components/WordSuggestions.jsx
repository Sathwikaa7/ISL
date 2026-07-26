import { useEffect, useState } from 'react'
import { fetchWordSuggestions } from '../services/api'
import { debounce } from '../services/utils'

const debouncedFetch = debounce((prefix, cb) => {
  fetchWordSuggestions(prefix)
    .then((data) => cb(data.suggestions || []))
    .catch(() => cb([]))
}, 200)

export default function WordSuggestions({ letterBuffer, onSelect }) {
  const [suggestions, setSuggestions] = useState([])
  const [loading, setLoading] = useState(false)

  useEffect(() => {
    if (!letterBuffer) {
      setSuggestions([])
      return
    }
    setLoading(true)
    debouncedFetch(letterBuffer, (results) => {
      setSuggestions(results)
      setLoading(false)
    })
  }, [letterBuffer])

  return (
    <div className="panel flex flex-col gap-3 p-4">
      <div className="flex items-center justify-between">
        <p className="eyebrow">Suggested words</p>
        <span className="font-mono text-[10px] text-slate-500">RapidFuzz</span>
      </div>

      <div className="flex flex-wrap gap-2">
        {loading && <span className="font-mono text-xs text-slate-500">Matching…</span>}

        {!loading && suggestions.length === 0 && (
          <span className="font-mono text-xs text-slate-500">
            Suggestions appear as letters are signed.
          </span>
        )}

        {!loading &&
          suggestions.map((s, idx) => (
            <button
              key={`${s.word}-${idx}`}
              onClick={() => onSelect(s.word)}
              className="group flex items-center gap-2 rounded-full border border-white/5 bg-ink-800/70 px-3.5 py-1.5 transition-colors hover:border-teal-400/40 hover:bg-teal-400/10"
            >
              <span className="font-body text-sm text-paper">{s.word}</span>
              <span className="font-mono text-[10px] text-slate-500 group-hover:text-teal-400">
                {Math.round((s.score ?? 0) * 100)}%
              </span>
            </button>
          ))}
      </div>
    </div>
  )
}
