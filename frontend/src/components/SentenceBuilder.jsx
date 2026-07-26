export default function SentenceBuilder({ words, onRemoveWord, onAddSpace, onUndo, onClear, onTranslate, isTranslating }) {
  const sentence = words.join(' ')

  return (
    <div className="panel flex flex-col gap-3 p-4">
      <div className="flex items-center justify-between">
        <p className="eyebrow">Sentence in progress</p>
        <div className="flex gap-1.5">
          <button
            onClick={onUndo}
            className="rounded-md bg-white/5 px-2.5 py-1 font-mono text-[11px] text-slate-400 hover:bg-white/10"
          >
            Undo
          </button>
          <button
            onClick={onClear}
            className="rounded-md bg-white/5 px-2.5 py-1 font-mono text-[11px] text-slate-400 hover:bg-white/10"
          >
            Clear
          </button>
        </div>
      </div>

      <div className="flex min-h-[3.5rem] flex-wrap items-center gap-2 rounded-xl border border-white/5 bg-ink-950/60 p-3">
        {words.length === 0 && (
          <span className="font-mono text-xs text-slate-500">
            Tap a suggested word to add it to your sentence…
          </span>
        )}
        {words.map((w, i) => (
          <span
            key={`${w}-${i}`}
            className="group flex items-center gap-1.5 rounded-lg bg-ink-800 px-2.5 py-1 text-sm text-paper animate-rise"
          >
            {w}
            <button
              onClick={() => onRemoveWord(i)}
              className="text-slate-500 opacity-0 transition-opacity group-hover:opacity-100 hover:text-coral"
              aria-label={`Remove ${w}`}
            >
              ×
            </button>
          </span>
        ))}
      </div>

      <div className="flex items-center gap-2">
        <button
          onClick={onAddSpace}
          className="flex-1 rounded-lg border border-white/5 bg-ink-800/60 py-2 font-mono text-xs text-slate-300 hover:bg-ink-800"
        >
          + space / next word
        </button>
        <button
          onClick={() => onTranslate(sentence)}
          disabled={!sentence || isTranslating}
          className="flex-1 rounded-lg bg-teal-500 py-2 font-display text-xs font-semibold text-ink-950 transition-opacity hover:bg-teal-400 disabled:opacity-40"
        >
          {isTranslating ? 'Translating…' : 'Form sentence →'}
        </button>
      </div>
    </div>
  )
}
