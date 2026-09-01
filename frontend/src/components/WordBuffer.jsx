export default function WordBuffer({ word, onAdd, onClear, onCaptureNext, isFrozen }) {
  const displayWord = word.replaceAll('_', ' ')

  return (
    <div className="panel flex flex-col gap-3 p-4">
      <div className="flex items-center justify-between">
        <p className="eyebrow">Word buffer</p>
        <div className="flex gap-1.5">
          <button onClick={onCaptureNext} className="rounded-md bg-amber-500/20 px-2.5 py-1 font-mono text-[11px] text-amber-400 hover:bg-amber-500/30">
            {isFrozen ? 'Capture word' : 'Restart capture'}
          </button>
          <button onClick={onClear} className="rounded-md bg-white/5 px-2.5 py-1 font-mono text-[11px] text-slate-400 hover:bg-white/10">
            Clear
          </button>
        </div>
      </div>
      <div className="flex min-h-[3rem] items-center rounded-xl border border-white/5 bg-ink-950/60 p-3">
        {word ? <span className="rounded-md bg-ink-800 px-3 py-1.5 font-display text-sm font-semibold text-paper animate-rise">{displayWord}</span> : <span className="font-mono text-xs text-slate-500">Press Capture word, then perform one complete sign…</span>}
      </div>
      <button onClick={onAdd} disabled={!word} className="rounded-lg bg-teal-500 py-2 font-display text-xs font-semibold text-ink-950 transition-opacity hover:bg-teal-400 disabled:opacity-40">
        Add confirmed word
      </button>
    </div>
  )
}
