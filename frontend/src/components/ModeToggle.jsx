const MODES = [
  { id: 'alphabet', label: 'Alphabet', hint: 'Spell letter by letter — best for names & new words' },
  { id: 'phrase', label: 'Word / Phrase', hint: 'One sign per word — faster for everyday conversation' }
]

export default function ModeToggle({ mode, setMode }) {
  return (
    <div className="panel flex flex-col gap-3 p-4">
      <p className="eyebrow">Recognition mode</p>
      <div className="grid grid-cols-2 gap-2">
        {MODES.map((m) => {
          const active = mode === m.id
          return (
            <button
              key={m.id}
              onClick={() => {
    console.log("Selected:", m.id)
    setMode(m.id)
}}
              className={`rounded-xl border px-3 py-2.5 text-left transition-colors ${
                active
                  ? 'border-teal-400/40 bg-teal-400/10 text-paper'
                  : 'border-white/5 bg-ink-800/60 text-slate-400 hover:border-white/10 hover:text-slate-300'
              }`}
            >
              <span className="block font-display text-sm font-semibold">{m.label}</span>
              <span className="mt-0.5 block text-[11px] leading-snug text-slate-500">{m.hint}</span>
            </button>
          )
        })}
      </div>
    </div>
  )
}
