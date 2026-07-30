const SIGNS = ['0', '1', '2', '3', '4', '5', '6', '7', '8', '9', ...'ABCDEFGHIJKLMNOPQRSTUVWXYZ']

const API_BASE = import.meta.env.VITE_API_URL || 'http://127.0.0.1:5000'

export default function AlphabetReference({ onSelect }) {
  return (
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
            onClick={() => onSelect(sign)}
            className="group overflow-hidden rounded-lg border border-white/10 bg-ink-950/60 text-left transition hover:-translate-y-0.5 hover:border-teal-400/70 hover:bg-ink-900 focus-visible:outline focus-visible:outline-2 focus-visible:outline-offset-2 focus-visible:outline-teal-300"
            aria-label={`Add ${sign} to the letter buffer`}
            title={`Add ${sign}`}
          >
            <img
              src={`${API_BASE}/api/alphabet-reference/${encodeURIComponent(sign)}`}
              alt={`Reference sign ${sign}`}
              className="aspect-square w-full object-cover"
              loading="lazy"
            />
            <span className="block py-1 text-center font-mono text-xs font-semibold text-teal-300">{sign}</span>
          </button>
        ))}
      </div>
    </section>
  )
}