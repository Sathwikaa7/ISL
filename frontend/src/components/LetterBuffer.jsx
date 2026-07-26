export default function LetterBuffer({ buffer, onBackspace, onClear, onFreeze, isFrozen }) {
  return (
    <div className="panel flex flex-col gap-3 p-4">
      <div className="flex items-center justify-between">
        <p className="eyebrow">Letter buffer</p>
        <div className="flex gap-1.5">
          <button
            onClick={onFreeze}
            className={`rounded-md px-2.5 py-1 font-mono text-[11px] transition-colors ${
              isFrozen
                ? 'bg-amber-500/20 text-amber-400'
                : 'bg-white/5 text-slate-400 hover:bg-white/10'
            }`}
          >
            {isFrozen ? 'Resume' : 'Freeze'}
          </button>
          <button
            onClick={onBackspace}
            className="rounded-md bg-white/5 px-2.5 py-1 font-mono text-[11px] text-slate-400 hover:bg-white/10"
          >
            ⌫
          </button>
          <button
            onClick={onClear}
            className="rounded-md bg-white/5 px-2.5 py-1 font-mono text-[11px] text-slate-400 hover:bg-white/10"
          >
            Clear
          </button>
        </div>
      </div>

      <div className="flex min-h-[3rem] flex-wrap items-center gap-1.5 rounded-xl border border-white/5 bg-ink-950/60 p-3">
        {buffer.length === 0 && (
          <span className="font-mono text-xs text-slate-500">Start signing to build a word…</span>
        )}
        {buffer.split('').map((ch, i) => (
          <span
            key={`${ch}-${i}`}
            className="flex h-8 w-8 items-center justify-center rounded-md bg-ink-800 font-display text-sm font-semibold text-paper animate-rise"
          >
            {ch.toUpperCase()}
          </span>
        ))}
      </div>
    </div>
  )
}
